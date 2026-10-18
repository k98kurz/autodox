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
handler.

Detection is limited to the same namespace and does NOT walk the MRO. Aliases
of inherited methods (e.g. `bar = Base.foo` in a subclass), builtins, renamed
imports, and name-mangled targets (`bar = __foo`: key `_C__foo` vs `__name__`
`__foo`) are not detected even via `cls.__dict__.get(target)`; document these
as caveats instead of trying to detect them, since broader detection risks the
false positives described above.
