# Library Development

This is a library intended to be used in other projects. All major decisions MUST
be confirmed by a human. Any changes to the core data model MUST be confirmed by
a human.

# Forbidden Commands

- NEVER, under ANY CIRCUMSTANCES, run `pip install` on ANYTHING. NEVER.
- NEVER, under ANY CIRCUMSTANCES, run `npm install` on ANYTHING. NEVER.
- NEVER, under ANY CIRCUMSTANCES, run `git checkout` on a file. NEVER.
- NEVER, under ANY CIRCUMSTANCES, run `git stash`. NEVER.
- NEVER, under ANY CIRCUMSTANCES, run `git reset` or `git reset --hard`. NEVER.

# Build agent guidelines

- Use a todo list for any non-trivial or long-running task.
  - If you have access to BOTH the todoread and todowrite tools, use them.
  - If you lack access to one of those tools, use a todo.md file.
  - ALWAYS check both todoread and the todo.md file when continuing after compaction.
- When refactoring, verify that it works with one case before copying throughout.
- Prefer a TDD approach:
  1. Write a test that fails.
  2. Prove it fails by running the test.
  3. Fix the code.
  4. Prove it is fixed by running the test.
- Code style guidelines are in docs/code_style.md. Read them before editing or
  reviewing code.
- Use stdlib unittest, not pytest or any other test framework.
- Except for `with self.assertRaises(...)`, use bare `assert condition, context`

# Memory

Major architectural decisions, best practices, and other things worth remembering
long-term are stored in docs/memory.md.

# Changelog

Do NOT record changes to intermediate states in the change log. ONLY record things
that ACTUALLY CHANGE BETWEEN RELEASES in the changelog.

# Discovery of Development Practices

If you encounter a substantial issue that bogged down development, in particular
something that is likely to cause problems in the future, and you discovered a
solution, create an entry in docs/memory.md concisely explaining the problem and
solution for future development efforts, and alert your human that you did. Such
entries must be concise and contain actionable information.
