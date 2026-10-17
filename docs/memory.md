# Memory

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
