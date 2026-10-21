# Memory

## Render signatures from `inspect.signature`, not annotation metadata

`dox_a_function` must build signatures from `inspect.signature` /
`inspect.Parameter` (`kind`, `annotation`, `default`, `Parameter.empty`), not
from `__annotations__`, `__defaults__`, or `__kwdefaults__`:

- `__annotations__` is not in declaration order when positional-only parameters
  exist (e.g. `def f(arg1, /, arg2)` yields `{'arg2': ..., 'arg1': ...}`), and
  parameter kinds (positional-only, keyword-only, variadic) are not encoded in
  it at all, so order and `/` placement cannot be recovered
- variadic parameters (`*args`/`**kwargs`) appear in `__annotations__` but never
  in `__defaults__`/`__kwdefaults__`, so offset-based default alignment
  misattaches defaults to later parameters

The only legitimate use of `__annotations__` is the `return` fallback in
`_signature_parts`, taken when `signature()` raises `TypeError`/`ValueError`.

Pitfalls verified on 3.10-3.12:

- `signature()` raises `TypeError` on raw `classmethod` descriptors; unwrap
  `__func__` first (see `_signature_parts`). Raw `staticmethod` descriptors and
  bound methods inspect fine, and bound methods already exclude the bound
  parameter
- with `from __future__ import annotations` (PEP 563), annotations come back as
  strings and render verbatim; without it, `dict[str, str].__name__` is `'dict'`,
  so prefer `str(annotation)` whenever it contains `[` (see `_annotation_str`)

## Alias detection is namespace-scoped

Aliases (e.g. `UsageError = DependencyError` at module scope, or `bar = foo` in a
class body) can only be detected where a binding name is available. `dox_a_class`
and `dox_a_function` receive an object, and an object does not know the names it
is bound to, so those functions must NOT attempt alias detection and must NOT
accept a `name`/`binding` option for that purpose.

Detect aliases in `dox_a_module` (module `__dict__` bindings) and `_dox_methods`
(class `__dict__` bindings). A binding is an alias only when a *different*
binding to the SAME object exists under the target's `__name__`, i.e.
`target != name and namespace.get(target) is item`. Do NOT treat any binding
whose name differs from `__name__` as an alias: re-exported objects such as
`from types import ModuleType` (whose `__name__` is `module`) would become false
positives like `ModuleType = module`. Render detected aliases with `_dox_alias`,
which honors the section format and fires no `AFTER_CLASS`/`AFTER_FUNCTION`
handler; forward `options` into `_paragraph`/`_list` so alias entries honor
`line_length` like every other renderer.

Detection is limited to the same namespace and does NOT walk the MRO. Aliases
of inherited methods (e.g. `bar = Base.foo` in a subclass), builtins, renamed
imports, and name-mangled targets (`bar = __foo`: key `_C__foo` vs `__name__`
`__foo`) are not detected even via `cls.__dict__.get(target)`; document these
as caveats instead of trying to detect them, since broader detection risks the
false positives described above.

## Filter class annotations on stored keys, display unmangled names

Python mangles a class-body `__name` (at most one trailing underscore) to
`_ClassName__name`; annotations and properties are keyed by the mangled name.
Filter and display them as follows, or the two paths silently diverge:

- classify with `_is_visible(name, include_private, include_dunder)` on the
  stored key; classifying an unmangled `__name` would treat it as a dunder and
  require `include_dunder` instead of `include_private`
- display with `_unmangle_name(name, owner)`. For annotations, resolve `owner`
  with `_annotation_owner(cls, name)`, which walks the MRO, because
  `_get_all_annotations` merges inherited mangled keys (`_Base__name`)
- `exclude_names` must match the stored key and the unmangled source name
- a genuine single-underscore name `_ClassName__name` is indistinguishable from
  a mangled `__name`; prefer the unmangled display
- dedupe annotation display names after unmangling, since a base and child can
  each define `__name` under different stored keys

## Backtick umbrella option is disable-only

Keep the one-directional semantics of `_backtick_enabled`: `backticks=False`
forces every category off, but `backticks=True` does NOT re-enable a granular
category set to False (documentation and changelog must say "disables", not
"overrides"; a bidirectional override would require distinguishing an absent
key from the default). All render sites (`_dox_alias`, the `dox_a_module`
header, `dox_a_value`, `dox_a_function`, `dox_a_class`) must route through
`_backtick`.

## Build hook: `version` is the builder version, not the project version

In a hatchling build hook (`scripts/hatch_build.py`, plugin `custom`),
`initialize(version, build_data)` receives the **builder version** —
`'standard'` for sdist/wheel builds, `'editable'` for PEP 660 editable
installs — not the project version. Gating on it silently fails
(`'dev' not in 'standard'`). Read `self.metadata.version` instead (the
normalized version, e.g. `0.2.0.dev0` for a `0.2.0-dev` source;
`original_version` keeps the raw string) and gate on the `dev` substring,
not the literal `-dev`.

The sdist always includes `pyproject.toml` even with `only-include`, but not
the hook script. Since `python -m build` rebuilds the wheel from the sdist,
`scripts/hatch_build.py` MUST be in `[tool.hatch.build.targets.sdist]
only-include` or release builds fail with a missing-hook error. Registering
the hook globally makes the sdist step itself fail, rather than leaving a
stray sdist before the wheel step fails.

## Debug output uses logging; only the CLI configures handlers

Library modules must not configure handlers or use `print` for diagnostics,
nor touch logger level or `propagate`; diagnostics go through
`getLogger(__name__)` via the `_debug(level, *args)` shim so call sites stay
unchanged. Only `autodox/cli.py` may attach a handler, and it must isolate
propagation while doing so: without that isolation, debug records reach the
root logger, so a documented module that configures logging on import (e.g.
`logging.basicConfig()`) emits every debug line twice. This keeps redirected
markdown on stdout clean and leaves programmatic users' logging
configuration untouched. Regression coverage:
`tests/test_cli.py::TestCli::test_debug_output_is_not_propagated_to_root`.

## Detect type aliases before class routing

On Python 3.10, `isinstance(list[int], type)` is True (`list[int].__class__` is
`type`), so `dox_a_module` would otherwise route PEP 585 aliases into
`dox_a_class` and document `list`. Detect runtime type aliases before the
`isinstance(item, type)` branch using `types.GenericAlias`, `types.UnionType`,
`typing.get_origin(...) is not None` with non-empty `get_args`, and a
feature-detected `typing.TypeAliasType` (3.12+). Guard the latter with
`getattr(typing, 'TypeAliasType', ())`; `isinstance(x, ())` is safely False on
older versions.

For PEP 695 aliases render `_annotation_str(value.__value__)`, not
`str(value.__value__)`, which yields `<class 'X'>` for a bare-class alias.
Guard `__value__` access with `try/except` because lazy evaluation can raise
`NameError`; fall back to `...`. Strip `typing.`, `builtins.`,
`collections.abc.`, and the documented module's qualifier with a regex whose
left boundary is neither an identifier char nor a dot, so longer dotted names
such as `mytyping.X` are not corrupted. Apply that regex only to spans outside
single/double-quoted string literals, since alias definitions can contain them
(e.g. `Literal['typing.Foo']`); a quote-blind pass corrupts the string
contents. `clean_type_aliases=False` disables cleanup. Render aliases as
`Name = Type` (one pair of backticks, governed by `backtick_names`), leaving
ordinary values in the `Name: type` form.

Detect `typing.NewType` values with `callable(value) and hasattr(value,
'__supertype__')` rather than `isinstance(value, type)`: NewType has been a
class since 3.10, so its instances are not types. Render them as
`Name = NewType('Name', Supertype)` using `_annotation_str(value.__supertype__)`
so the supertype is cleaned like any other alias definition.

## Recognize wrappers via `__wrapped__`, not the concrete wrapper type

`functools.lru_cache`/`cache` return a `functools._lru_cache_wrapper`, not a
`FunctionType`, so exact-type checks silently classify them as values and omit
cached class methods entirely. Detect function-likeness with
`_is_function_like`: `FunctionType`, `MethodType`, `classmethod`,
`staticmethod`, or any callable exposing `__wrapped__`, but not types or
wrapped classes. Use it at BOTH classification sites (`dox_a_module`'s function
branch and `dox_a_class`'s method collection); do not classify all callables,
because `functools.partial`, builtins, and `typing.NewType` must stay values.
Route wrapped classes through `_wrapped_class` BEFORE `_is_function_like`;
otherwise `@lru_cache` on a class documents the wrapper as a function and
loses the class's methods.

Unwrap wrappers with these helpers; each exists because a different unwrap
strategy breaks a different case:

- `_unwrap_function` follows `__wrapped__` and stops at
  `classmethod`/`staticmethod` descriptors and on cycles
- coroutine detection must use `_unwrap_for_inspection`, which continues
  through descriptors: `iscoroutinefunction()` does not follow `__wrapped__`,
  and descriptor-stopping hides async methods behind `staticmethod`
- `_has_implicit_receiver` must keep its `MethodType` early return (bound
  methods are already receiver-free), then unwrap with `_unwrap_function` and
  branch on the descriptor kind: `classmethod` means omit the receiver,
  `staticmethod` means do not. Not unwrapping at all documents `cls` on a
  wrapped classmethod; unwrapping through descriptors instead makes a wrapped
  staticmethod's underlying function look like a class-body function and drop
  a `self`/`cls`-named first parameter
- `_dox_methods` must classify the class binding with `_is_classmethod` /
  `_is_staticmethod` (via `_unwrap_function`) instead of
  `isinstance(..., classmethod/staticmethod)`: an outer wrapper is not the
  descriptor itself, so `isinstance` loses the `@classmethod`/`@staticmethod`
  marker; for `@lru_cache` outside `@staticmethod` the binding is the wrapper,
  not a `staticmethod` descriptor

## Render defaults deterministically; never `str`/`repr` arbitrary values

Parameter defaults are rendered by `_default_str`, which must not fall back to
`f'{value}'` or `repr(value)`: function and object reprs embed memory addresses,
so regenerated docs differ between runs. The final `repr` in
`_simple_default_str` is safe because only deterministic builtin scalar types
reach it. Inline only builtin scalars, enum members, type aliases, `NewType`
values, classes, and exact containers with at most `_INLINE_CONTAINER_LIMIT`
items and no nesting; elide `bytes`/`bytearray` values longer than
`_INLINE_BYTES_LIMIT`, including inside containers; render everything else as
`...` unless `verbose_defaults` is set.

Verbose callables and callable instances render as
`Callable[..., ReturnType]` (argument types are intentionally omitted; a missing
return annotation becomes `Any`), non-callable object instances as
`TypeName(...)`, and containers recursively. Check
`_is_new_type`/`_is_type_alias` before `callable` so aliases are not rendered
as callables. They must also be checked before `isinstance(value, type)` in
`_simple_default_str`: on Python 3.10, `isinstance(list[int], type)` is True,
so the class branch would render `list` instead of `list[int]`; keep the
`not _is_type_alias` guard on that class branch as a defense against
reordering. Likewise, `typing.Any` is a class on Python 3.11+ but a special
form on 3.10; identity-check it and treat it as a simple scalar on both, and
special-case it in `_simple_default_str` so 3.10 does not fall through to
`repr` and render `typing.Any`. Sort set/frozenset renderings unconditionally,
but sort dict items only when `sort_default_dicts` is set; preserving dict
insertion order is intentional otherwise. Track container ids in a seen set
(add before rendering children, discard after, in `finally`) so cycles become
`...` while repeated non-cyclic references still render.

Combined `Flag`/`IntFlag` values have `name is None` on Python 3.10, so
decompose them into nonzero members and render fully qualified unions such as
`Mode.READ | Mode.WRITE`. Regression coverage:
`tests/test_doxing.py::TestDoxAFunction::test_verbose_defaults_are_deterministic`.
