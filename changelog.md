## 0.2.0

- Breaking: CLI options now use GNU-style `--long-name` flags (e.g.
  `--exclude-name` replaces `-exclude_name`); run `autodox --help` for the
  updated usage
- Added `-v`/`--version`; CLI output now ends with a footer showing the autodox
  and Python versions (`dox_footer()`, suppressed with `--no-footer`)
- `--debug` now logs to stderr via `logging`, so debug output no longer
  contaminates markdown redirected from stdout
- Names, types, and signatures now render as inline code by default (module
  headers included); `backtick_names`, `backtick_types`, and
  `backtick_signatures` default to True and can be disabled with
  `--no-backtick-*`, or all at once with `backticks`/`--no-backticks`
- Annotation, type alias, and default rendering now canonicalize to PEP 604
  unions and builtin generics on all supported versions (e.g.
  `Optional[List[int]]` → `list[int] | None`); module qualifiers in type
  aliases are stripped by default (`clean_type_aliases: False` /
  `--no-clean-type-aliases` keeps them), and `dox_a_value` accepts a
  `module_name` option to control this
- Python 3.14 and 3.15 are now supported
- Module-level type aliases (including PEP 695 `type` aliases) and `NewType`
  values now render their definitions (`Name = Type`,
  `Name = NewType('Name', Supertype)`) in the Values section
- Enum subclasses now document their members in a `Members` section, including
  aliases (`CRIMSON = RED`) and `Flag`/`IntFlag` composites
  (`READ_WRITE = READ | WRITE = 3`)
- Functions, methods, and classes wrapped by decorators exposing `__wrapped__`
  (e.g. `functools.cache`) now render with their real signatures and
  docstrings (classes as classes) instead of appearing as values; cached
  methods are no longer omitted. Async static methods now show `async`, and
  wrapped `classmethod`s keep `@classmethod` without an implicit `cls`
- Complex defaults now render as `...` instead of unstable `repr` output that
  leaked function pointers and memory addresses; `verbose_defaults` /
  `--verbose-defaults` renders stable callable, object, and container forms
  instead
- Added `sort_classes`/`--sort-classes` and
  `sort_default_dicts`/`--sort-default-dicts` (both off by default)
- Large `bytes`/`bytearray` defaults are now elided like other large containers
- Bug fixes:
  - PEP 585 aliases such as `list[int]` were documented as classes on 3.10
  - `typing.Any` and enum/`Flag` defaults rendered inconsistently across
    Python versions
  - Private, name-mangled, and dunder methods omitted decorator markers
  - Implicitly static `__new__` showed `{unknown/unnamed}` and the wrong
    docstring
  - List-format output ignored `line_length`

## 0.1.17

- Bug fixes:
  - Class, function, and method aliases are now detected automatically and
    documented as `Alias = Target` instead of appearing as duplicates of the
    target
  - Function and method signatures now render the full parameter list in
    declaration order with correct defaults, `*args`/`**kwargs` markers,
    properly placed `/` and `*` separators, and preserved `None`/subscripted
    (e.g. `dict[str, str]`) annotations
  - Class annotations now respect `include_private`, `include_dunder`, and
    `exclude_names` instead of always being documented
  - Annotation types render as `int`/`dict[str, str]` instead of
    `<class 'int'>`, matching function signatures
  - Name-mangled private annotations and properties are displayed under their
    source names (e.g. `__hidden` instead of `_Class__hidden`), and
    `exclude_names` accepts either form
  - The `dox_a_*` functions' `options` parameter now defaults to `None`
    instead of a shared mutable `{}`, preventing a `BEFORE_` handler that
    mutates `options` in place from leaking state into later calls

## 0.1.16

- Fixed a crash when documenting functions or classes that lack a `__name__`
  attribute

## 0.1.15

- Fixed an extra space in signatures that combine a decorator prepend with
  `async`

## 0.1.14

- Async functions are now denoted with an `async` prefix in signatures
- Added `line_length` option to configure the paragraph wrap width

## 0.1.13

- Ignore the empty `_no_init_or_replace_init` method that Python 3.10
  `Protocol` classes use to override `__init__`

## 0.1.12

- Dunder methods are now documented before public and private methods
- `__init__` is now documented even when `include_dunder` is not enabled

## 0.1.11

- Fixed a variable shadowing bug that produced incorrect class names in headers
- Moved debug statements below function docstrings

## 0.1.10

- Fixed paragraph wrapping so a token longer than the line length gets its own
  line

## 0.1.9

- Class exclusion is now evaluated before member collection

## 0.1.8

- Added debug tracing and the `-debug` CLI flag (repeated use increases
  verbosity)
- Fixed collection of annotations inherited from parent classes

## 0.1.7

- Value names are now formatted as inline code

## 0.1.6

- Class properties are now formatted as `name: docstring` with a blank line
  after the section

## 0.1.5

- Added class docstring handling

## 0.1.4

- Lowered the minimum supported Python version to 3.10

## 0.1.3

- Fixed rendering of type-valued defaults in function signatures
- Split the CLI entry point into `invoke_cli(args)` and a `main_cli()` wrapper

## 0.1.2

- Fixed class member filtering when `include_dunder` is enabled without
  `include_private`

## 0.1.1

- Fixed documentation of classmethods
- `object` no longer appears as the parent of top-level classes
- Removed a trailing space from function signatures in header format

## 0.1.0

- Renumbered from 0.0.4.6 to 0.1.0
- Function signatures now include keyword-only parameters and their defaults
- String defaults are now quoted in signatures
