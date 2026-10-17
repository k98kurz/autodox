"""
Check line lengths in Python files according to project conventions.
"""

from pathlib import Path
import argparse
import io
import sys
import tokenize


MULTILINE_DOCSTRING_LIMIT = 72

SINGLE_LINE_DOCSTRING_LIMIT = 80

DEFAULT_EXCLUDES = {
    "venv", ".git", "__pycache__", "temp", "references", ".old",
}


def get_docstring_limits(source: str) -> dict[int, int]:
    """Map docstring line numbers to their length limit.
        Single-line docstrings get the relaxed limit; lines spanned by
        multi-line docstrings get the stricter one.
    """
    docstring_limits: dict[int, int] = {}
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as e:
        print(f"Warning: could not tokenize source ({e}); "
              f"treating all lines as code", file=sys.stderr)
        return docstring_limits

    def significant_type(
            tokens: list, idx: int, *,
            reverse: bool = False
        ) -> int | None:
        """Return the type of the nearest significant token to
            `tokens[idx]`.
        """
        step = -1 if reverse else 1
        skip = {
            tokenize.NL, tokenize.COMMENT, tokenize.INDENT,
            tokenize.DEDENT, tokenize.ENCODING
        }
        j = idx + step
        while 0 <= j < len(tokens):
            if tokens[j].type not in skip:
                return tokens[j].type
            j += step
        return None

    for i, tok in enumerate(tokens):
        if tok.type != tokenize.STRING:
            continue
        prev_type = significant_type(tokens, i, reverse=True)
        next_type = significant_type(tokens, i)
        if  (   prev_type in (
                    None, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT
                )
                and next_type in (tokenize.NEWLINE, tokenize.ENDMARKER)
            ):
            if tok.start[0] == tok.end[0]:
                docstring_limits[tok.start[0]] = SINGLE_LINE_DOCSTRING_LIMIT
            else:
                for line_num in range(tok.start[0], tok.end[0] + 1):
                    docstring_limits[line_num] = MULTILINE_DOCSTRING_LIMIT
    return docstring_limits


def analyze_source(
        source: str, hardmax: int = 85, softmax: int | None = None,
    ) -> tuple[list, list, list]:
    """Analyze source text for length and whitespace issues.
        Returns (hard_violation_lines, soft_warning_lines,
        whitespace_lines).
    """
    hard_violation_lines: list[tuple[int, int, str]] = []
    soft_warning_lines: list[tuple[int, int, str]] = []
    whitespace_lines: list[int] = []

    lines = source.splitlines()
    docstring_limits = get_docstring_limits(source)

    for line_num, line in enumerate(lines, start=1):
        line_len = len(line.rstrip("\n\r"))

        if line.rstrip("\n\r \t") != line.rstrip("\n\r"):
            whitespace_lines.append(line_num)

        limit = docstring_limits.get(line_num, hardmax)

        if line_len > limit:
            preview = line[: min(line_len, 60)].rstrip("\n\r")
            hard_violation_lines.append((line_num, line_len, preview))

        if  (   line_num not in docstring_limits
                and softmax is not None
                and line_len > softmax
                and line_len <= hardmax
            ):
            preview = line[: min(line_len, 60)].rstrip("\n\r")
            soft_warning_lines.append((line_num, line_len, preview))

    return hard_violation_lines, soft_warning_lines, whitespace_lines


def check_source(
        source: str, hardmax: int = 85, softmax: int | None = None,
    ) -> tuple[int, int, int]:
    """Check source text for violations. Returns counts of hard
        violations, soft warnings, and whitespace issues without
        printing a report.
    """
    hard_lines, soft_lines, whitespace_lines = analyze_source(
        source, hardmax, softmax
    )
    return len(hard_lines), len(soft_lines), len(whitespace_lines)


def collect_files(
        path: str, recursive: bool = False, excludes: list[str] | None = None,
    ) -> list[Path]:
    """Return the Python files to check for the given path.
        A file is returned as-is; a directory is traversed for `.py`
        files, recursively only if `recursive` is set. Directories in
        `DEFAULT_EXCLUDES` and `excludes` are skipped.
    """
    p = Path(path)
    if not p.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        sys.exit(1)
    if p.is_file():
        return [p]

    ignore = DEFAULT_EXCLUDES | set(excludes or [])
    pattern = "**/*.py" if recursive else "*.py"
    files: list[Path] = []
    for f in sorted(p.glob(pattern), key=str):
        if any(part in ignore for part in f.relative_to(p).parts[:-1]):
            continue
        files.append(f)
    return files


def print_report(
        hard_violation_lines: list[tuple[int, int, str]],
        soft_warning_lines: list[tuple[int, int, str]],
        whitespace_lines: list[int],
        softmax: int | None,
    ) -> None:
    """Print the report sections and a summary line."""
    if hard_violation_lines:
        print("HARD VIOLATIONS:")
        for line_num, line_len, preview in hard_violation_lines:
            print(f"  Line {line_num} ({line_len} chars): {preview}...")
        print()

    if soft_warning_lines and softmax is not None:
        print(f"SOFT WARNINGS (--softmax={softmax}):")
        for line_num, line_len, preview in soft_warning_lines:
            print(f"  Line {line_num} ({line_len} chars): {preview}...")
        print()

    if whitespace_lines:
        print("WHITESPACE ISSUES:")
        for line_num in whitespace_lines:
            print(f"  Line {line_num}: trailing whitespace detected")
        print()

    summary_parts = []
    if hard_violation_lines:
        summary_parts.append(
            f"{len(hard_violation_lines)} hard violation(s)"
        )
    if soft_warning_lines:
        summary_parts.append(f"{len(soft_warning_lines)} soft warning(s)")
    if whitespace_lines:
        summary_parts.append(
            f"{len(whitespace_lines)} whitespace issue(s)"
        )

    if summary_parts:
        print(f"SUMMARY: {', '.join(summary_parts)}")
    else:
        print("SUMMARY: No issues found")


def print_aggregate_summary(
        checked: int, with_issues: int, total_hard: int, total_soft: int,
        total_whitespace: int, skipped: int,
    ) -> None:
    """Print the aggregate summary for a multi-file run."""
    print()
    print(f"Checked {checked} file(s), {with_issues} with issues "
          f"({skipped} skipped)")
    parts = []
    if total_hard:
        parts.append(f"{total_hard} hard violation(s)")
    if total_soft:
        parts.append(f"{total_soft} soft warning(s)")
    if total_whitespace:
        parts.append(f"{total_whitespace} whitespace issue(s)")
    if parts:
        print(f"TOTAL: {', '.join(parts)}")
    else:
        print("TOTAL: No issues found")


def run(
        path: str, recursive: bool = False, excludes: list[str] | None = None,
        hardmax: int = 85, softmax: int | None = None,
    ) -> tuple[int, int, int, int]:
    """Check all collected files, printing reports. Returns aggregate
        (hard_violations, soft_warnings, whitespace_issues, skipped).
    """
    files = collect_files(path, recursive, excludes)
    multi = len(files) > 1

    total_hard = 0
    total_soft = 0
    total_whitespace = 0
    with_issues = 0
    skipped = 0

    for f in files:
        try:
            source = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: could not read {f} ({e}); skipping",
                  file=sys.stderr)
            skipped += 1
            continue

        hard_lines, soft_lines, whitespace_lines = analyze_source(
            source, hardmax, softmax
        )
        if hard_lines or soft_lines or whitespace_lines:
            with_issues += 1
        if not multi or hard_lines or soft_lines or whitespace_lines:
            print(f"File: {f}\n")
            print_report(hard_lines, soft_lines, whitespace_lines, softmax)

        total_hard += len(hard_lines)
        total_soft += len(soft_lines)
        total_whitespace += len(whitespace_lines)

    if multi:
        print_aggregate_summary(
            len(files) - skipped, with_issues, total_hard, total_soft,
            total_whitespace, skipped,
        )
    return total_hard, total_soft, total_whitespace, skipped


def main() -> None:
    """Parse arguments and run line length checker."""
    parser = argparse.ArgumentParser(
        description="Check line lengths in Python files"
    )
    parser.add_argument(
        "path",
        help="File or directory to check"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="recursively check .py files under a directory"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="additional directory name(s) to skip when recursing "
             "(repeatable)"
    )
    parser.add_argument(
        "--hardmax",
        type=int,
        default=85,
        help="Hard maximum line length for code (default: 85)"
    )
    parser.add_argument(
        "--softmax",
        type=int,
        default=None,
        help="Soft maximum line length for code (optional, "
             "default: no soft warnings)"
    )

    args = parser.parse_args()

    hard_violations, soft_warnings, whitespace_issues, skipped = run(
        args.path,
        args.recursive,
        args.exclude,
        args.hardmax,
        args.softmax
    )

    if skipped > 0:
        print(f"Error: {skipped} file(s) could not be read", file=sys.stderr)
        sys.exit(1)

    if hard_violations > 0 or whitespace_issues > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
