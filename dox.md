# `autodox`

Autodox is a package for generating documentation from code annotations, types,
and docstrings.

## Classes

### `Event(Enum)`

Valid events for the hook system.

## Functions

### `dox_a_class(cls: type, options: dict | None = None) -> str:`

Collects some information about a class and returns a formatted str. Any names
specified in options['exclude_names'] will be excluded. Private and dunder
members will be included if options['include_private'] or
options['include_dunder'] are specified, respectively.

### `dox_a_function(function: Callable, options: dict | None = None) -> str:`

Collects some information about a function and returns it formatted as specified
in the options or as a list.

### `dox_a_module(module: ModuleType, options: dict | None = None) -> str:`

Iterates over a module, collects information about its parts, and returns a str
containing markdown documentation generated from types, annotations, and
docstrings.

### `dox_a_value(value: Any, options: dict | None = None) -> str:`

Collects some information about a value and returns it formatted as specified in
the options or as a list.

### `set_before_handler(event: Event, function: Callable[[Any, dict], tuple[Any, dict]]) -> None:`

Sets a handler for a BEFORE_ event.

### `set_after_handler(event: Event, function: Callable[[str], str]) -> None:`

Sets a handler for an AFTER_ event.

### `unset_handler(event: Event) -> None:`

Unset an event handling handler.

### `version() -> str:`

Returns the current version of this package.


