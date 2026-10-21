from __future__ import annotations
from enum import Enum, Flag, auto
from inspect import Parameter, iscoroutinefunction, signature
from logging import addLevelName, CRITICAL, DEBUG, getLogger, INFO
from types import FunctionType, GenericAlias, MethodType, ModuleType, UnionType
from typing import Any, Callable, get_args, get_origin
import re
import typing


class Event(Enum):
    """Valid events for the hook system."""
    AFTER_HEADER = auto()
    AFTER_PARAGRAPH = auto()
    AFTER_LIST = auto()
    BEFORE_VALUE = auto()
    AFTER_VALUE = auto()
    BEFORE_FUNCTION = auto()
    AFTER_FUNCTION = auto()
    BEFORE_CLASS = auto()
    AFTER_CLASS = auto()
    BEFORE_MODULE = auto()
    AFTER_MODULE = auto()


_handlers = {}
logger = getLogger(__name__)
TRACE = 5
addLevelName(TRACE, 'TRACE')
_DEPTH_LEVELS = {1: INFO, 2: DEBUG, 3: TRACE}
_TYPE_ALIAS_TYPE = getattr(typing, 'TypeAliasType', ())


def _logging_level_for(debug: int) -> int:
    """Returns the logging threshold for a CLI debug count."""
    if debug <= 0:
        return CRITICAL + 1
    return _DEPTH_LEVELS.get(debug, TRACE)


def _debug(level: int = 1, *args):
    """Log a debug statement if enabled."""
    log_level = _DEPTH_LEVELS.get(level, TRACE)
    if logger.isEnabledFor(log_level):
        logger.log(log_level, ' '.join(str(arg) for arg in args))


def _set_handler(event: Event, function: Callable) -> None:
    """Set a handler for a specific event."""
    _debug(3, '_set_handler(', event, function, ')')
    if not callable(function):
        raise TypeError('function must be callable')

    if event.name in _handlers:
        first = _handlers[event.name]
        second = function
        _handlers[event.name] = lambda *args: second(first(*args))
    else:
        _handlers[event.name] = function


def set_before_handler(
        event: Event, function: Callable[[Any, dict], tuple[Any, dict]]
    ) -> None:
    """Sets a handler for a BEFORE_ event."""
    _debug(3, 'set_before_handler(', event, function, ')')
    if type(event) is not Event:
        raise TypeError('event must be Event')
    if 'BEFORE_' not in event.name:
        raise ValueError('event must be a BEFORE_ event')

    _set_handler(event, function)


def set_after_handler(event: Event, function: Callable[[str], str]) -> None:
    """Sets a handler for an AFTER_ event."""
    _debug(3, 'set_after_handler(', event, ')')
    if type(event) is not Event:
        raise TypeError('event must be Event')
    if 'AFTER_' not in event.name:
        raise ValueError('event must be an AFTER_ event')

    _set_handler(event, function)


def unset_handler(event: Event) -> None:
    """Unset an event handling handler."""
    _debug(3, 'unset_handler(', event, ')')
    if type(event) is not Event:
        raise TypeError('event must be Event')
    if event.name in _handlers:
        del _handlers[event.name]


def _invoke_handler(event: Event, *args) -> Any:
    """Invokes the handler for the event if set, otherwise return the
        parameters.
    """
    _debug(3, '_invoke_handler(', event, ')')
    if event.name in _handlers:
        val = _handlers[event.name](*args)
        return val[0] if len(val) == 1 else val
    return args[0] if len(args) == 1 else args


def _header(line: str, header_level: int = 0) -> str:
    """Takes a line and returns it formatted as a header with the proper
        number of hashtags for the given header_level.
    """
    _debug(2, '_header(', line, header_level, ')')
    doc = ''.join(['#' for _ in range(header_level+1)]) + f' {line}\n\n'
    return _invoke_handler(Event.AFTER_HEADER, doc)


def _paragraph(docstring: str, options: dict | None = None) -> str:
    """Takes a docstring, tokenizes it, and returns a str formatted to
        80 chars (default, or `options['line_length']`) or fewer per
        line without splitting tokens; tokens that stretch beyond the
        char limit are preserved on their own lines.
    """
    _debug(2, '_paragraph(', docstring, ')')
    options = options or {}
    line_length = options.get('line_length', 80)
    def make_line(tokens: list[str]) -> tuple[str, list[str]]:
        _debug(2, 'make_line(', tokens, ')')
        line = ''
        while len(tokens) and (
                len(line) + len(tokens[0]) <= line_length
                or line.count('`') == 1
            ) or (
                len(line) == 0 and len(tokens[0]) > line_length
            ):
            line += tokens[0] + ' '
            tokens = tokens[1:]
        return (line[:-1], tokens)

    tokens = docstring.split()
    lines = []

    while len(tokens):
        line, tokens = make_line(tokens)
        lines.append(line)

    doc = '\n'.join(lines) + '\n\n'
    return _invoke_handler(Event.AFTER_PARAGRAPH, doc)


def _list(line: str, options: dict | None = None) -> str:
    """Takes a line and returns a formatted list item."""
    _debug(2, '_list(', line, ')')
    doc = _paragraph(f'- {line}', options)[:-1]
    return _invoke_handler(Event.AFTER_LIST, doc)


def _unwrap_function(function: Callable) -> Callable:
    """Follows a `__wrapped__` chain to the underlying callable. Stops
        at `classmethod`/`staticmethod` descriptors and at cycles so
        wrapped functions can be inspected safely.
    """
    seen = set()
    while True:
        if isinstance(function, (classmethod, staticmethod)):
            return function
        wrapped = getattr(function, '__wrapped__', None)
        if wrapped is None or id(function) in seen:
            return function
        seen.add(id(function))
        function = wrapped


def _unwrap_for_inspection(function: Callable) -> Any:
    """Follows `__wrapped__` and descriptor `__func__` links to the
        underlying callable so properties such as coroutine status can
        be inspected. Unlike `_unwrap_function`, this does not stop at
        `classmethod`/`staticmethod` descriptors, but it does stop at
        cycles.
    """
    seen = set()
    function = _unwrap_function(function)
    while isinstance(function, (classmethod, staticmethod)):
        if id(function) in seen:
            return function
        seen.add(id(function))
        function = _unwrap_function(function.__func__)
    return function


def _is_function_like(item: Any) -> bool:
    """Returns whether `item` should be documented as a function or
        method. Plain functions, methods, and their raw descriptors
        qualify, as do callables exposing `__wrapped__`, such as
        `functools.lru_cache` wrappers. Classes, including wrapped
        classes, do not qualify.
    """
    if isinstance(item, type):
        return False
    if isinstance(item, (FunctionType, MethodType, classmethod, staticmethod)):
        return True
    if not callable(item) or not hasattr(item, '__wrapped__'):
        return False
    return not isinstance(_unwrap_function(item), type)


def _is_classmethod(descriptor: Any) -> bool:
    """Returns whether a class binding is a `classmethod` descriptor,
        including one wrapped by another decorator.
    """
    return isinstance(_unwrap_function(descriptor), classmethod)


def _is_staticmethod(descriptor: Any) -> bool:
    """Returns whether a class binding is a `staticmethod` descriptor,
        including one wrapped by another decorator.
    """
    return isinstance(_unwrap_function(descriptor), staticmethod)


def _wrapped_class(item: Any) -> type | None:
    """Returns the class wrapped by `item`, or `item` itself when it is
        already a class. Returns `None` for non-classes.
    """
    if isinstance(item, type):
        return item
    if not callable(item) or not hasattr(item, '__wrapped__'):
        return None
    unwrapped = _unwrap_function(item)
    return unwrapped if isinstance(unwrapped, type) else None


def _name_of(item: Any, fallback: str) -> str:
    """Returns the `__name__` of an item, unwrapping `__func__` so that
        raw `classmethod`/`staticmethod` objects resolve to the name of
        the wrapped function. Falls back to the given name when no
        `__name__` is available.
    """
    func = getattr(item, '__func__', item)
    name = getattr(func, '__name__', None)
    if name is None:
        name = getattr(_unwrap_function(func), '__name__', None)
    return name if name is not None else fallback


def _dox_alias(
        binding: str, target: str, header_level: int = 0,
        format: str = 'header', options: dict | None = None
    ) -> str:
    """Renders an alias binding, e.g. `UsageError = DependencyError`,
        using the specified format. Alias entries do not fire the
        `AFTER_CLASS` or `AFTER_FUNCTION` handlers.
    """
    _debug(1, '_dox_alias(', binding, target, header_level, format, options, ')')
    options = options or {}
    alias = _backtick(
        f'{binding} = {target}', _backtick_enabled(options, 'backtick_names')
    )
    match format:
        case 'header':
            return _header(alias, header_level)
        case 'paragraph':
            return _paragraph(alias, options)
        case _:
            return _list(alias, options)


def dox_a_module(module: ModuleType, options: dict | None = None) -> str:
    """Iterates over a module, collects information about its parts, and
        returns a str containing markdown documentation generated from
        types, annotations, and docstrings.
    """
    _debug(
        1, 'dox_a_module(',
        getattr(module, '__name__', '[unnamed]'), options, ')'
    )
    options = options or {}
    module, options = _invoke_handler(Event.BEFORE_MODULE, module, options)
    exclude_names = options['exclude_names'] if 'exclude_names' in options else []
    exclude_types = options['exclude_types'] if 'exclude_types' in options else []
    header_level = options['header_level'] if 'header_level' in options else 0
    function_format = (
        options['function_format'] if 'function_format' in options else 'header'
    )
    value_format = options['value_format'] if 'value_format' in options else 'list'
    include_private = 'include_private' in options
    include_dunder = 'include_dunder' in options
    include_submodules = 'include_submodules' in options
    document_submodules = 'document_submodules' in options
    suboptions = {**options, 'header_level': header_level + 2}

    values = []
    functions = []
    classes = []
    submodules = []

    for name, item in module.__dict__.items():
        item_type = type(item)

        if name[:1] == '_' and not (include_private or include_dunder):
            continue
        if name[:2] == '__' and not include_dunder:
            continue
        if name in exclude_names:
            continue
        if hasattr(item_type, '__name__') and item_type.__name__ in exclude_types:
            continue

        if isinstance(item, ModuleType):
            if include_submodules and not document_submodules:
                submodules.append(f'- {name}')
            elif document_submodules:
                doc = dox_a_module(item, suboptions)
                submodules.append(doc)
            continue

        value_options = {
            **suboptions, 'name': name, 'format': value_format,
            'module_name': getattr(module, '__name__', ''),
        }

        if _is_type_alias(item):
            values.append(dox_a_value(item, value_options))
            continue

        cls = _wrapped_class(item)
        if cls is not None:
            target = _name_of(item, name)
            if target != name and module.__dict__.get(target) is item:
                doc = _dox_alias(name, target, header_level + 2, options=options)
            else:
                doc = dox_a_class(cls, suboptions)
            if doc:
                classes.append(doc)
            continue

        if _is_function_like(item):
            target = _name_of(item, name)
            if target != name and module.__dict__.get(target) is item:
                doc = _dox_alias(
                    name, target, header_level + 2, function_format, options
                )
            else:
                doc = dox_a_function(
                    item, {**suboptions, 'format': function_format}
                )
            functions.append(doc)
            continue

        doc = dox_a_value(item, value_options)
        values.append(doc)

    doc = _header(
        _backtick(module.__name__, _backtick_enabled(options, 'backtick_names')),
        header_level,
    )

    if hasattr(module, '__doc__') and module.__doc__:
        doc += _paragraph(module.__doc__, options)

    if len(classes):
        doc += _header('Classes', header_level + 1)
        for cls in classes:
            doc += cls

    if len(functions):
        doc += _header('Functions', header_level + 1)
        for func in functions:
            doc += func
        if function_format == 'list':
            doc += '\n'

    if len(values):
        doc += _header('Values', header_level + 1)
        for val in values:
            doc += val

    if len(submodules):
        doc += _header('Submodules', header_level + 1)
        for sub in submodules:
            doc += sub

    return _invoke_handler(Event.AFTER_MODULE, doc)


def dox_a_value(value: Any, options: dict | None = None) -> str:
    """Collects some information about a value and returns it formatted
        as specified in the options or as a list. Runtime type aliases
        and `NewType` values render as `name = definition` instead of
        their runtime class name.
    """
    _debug(1, 'dox_a_value(', value, options, ')')
    options = options or {}
    value, options = _invoke_handler(Event.BEFORE_VALUE, value, options)
    header_level = options['header_level'] if 'header_level' in options else 0
    format = options['format'] if 'format' in options else 'list'
    backtick_names = _backtick_enabled(options, 'backtick_names')
    backtick_types = _backtick_enabled(options, 'backtick_types')

    name = value.__name__ if hasattr(value, '__name__') else '{unknown/unnamed}'
    if 'name' in options:
        name = options['name']

    definition = _value_definition(value)
    if definition is not None:
        clean = (
            options['clean_type_aliases']
            if 'clean_type_aliases' in options else True
        )
        if clean:
            module_name = (
                options['module_name'] if 'module_name' in options else ''
            )
            definition = _clean_type_alias_text(definition, module_name)
        entry = _backtick(f'{name} = {definition}', backtick_names)
    else:
        name = _backtick(name, backtick_names)
        type_str = _backtick(type(value).__name__, backtick_types)
        entry = f'{name}: {type_str}'

    doc = ''

    match format:
        case 'header':
            doc = _header(entry, header_level)
        case 'paragraph':
            doc = _paragraph(entry, options)
        case _:
            doc = _list(entry)

    return _invoke_handler(Event.AFTER_VALUE, doc)


def _annotation_str(annotation: Any) -> str:
    """Renders an annotation as a str, keeping subscripts such as
        `dict[str, str]` verbatim.
    """
    text = str(annotation)
    if '[' in text:
        return text
    return annotation.__name__ if hasattr(annotation, '__name__') else text


def _is_type_alias(value: Any) -> bool:
    """Returns whether `value` is a runtime type alias construct, e.g.
        `Callable[[int], str]`, `int | str`, or a PEP 695 `type` alias.
    """
    if _TYPE_ALIAS_TYPE and isinstance(value, _TYPE_ALIAS_TYPE):
        return True
    if isinstance(value, (GenericAlias, UnionType)):
        return True
    return get_origin(value) is not None and bool(get_args(value))


def _type_alias_text(value: Any) -> str:
    """Returns a readable definition for a runtime type alias. PEP 695
        aliases are evaluated lazily, so failures fall back to `...`.
    """
    if _TYPE_ALIAS_TYPE and isinstance(value, _TYPE_ALIAS_TYPE):
        try:
            return _annotation_str(value.__value__)
        except Exception:
            return '...'
    return str(value)


def _is_new_type(value: Any) -> bool:
    """Returns whether `value` is a `typing.NewType` instance. NewType
        has been a class since 3.10, so its instances are never `type`s;
        `__supertype__` is the stable way to detect them.
    """
    return callable(value) and hasattr(value, '__supertype__')


def _value_definition(value: Any) -> str | None:
    """Returns the right-hand side used to render a type alias or a
        `NewType` as `Name = definition`, or `None` for ordinary values.
    """
    if _is_new_type(value):
        supertype = _annotation_str(value.__supertype__)
        return f"NewType('{value.__name__}', {supertype})"
    if _is_type_alias(value):
        return _type_alias_text(value)
    return None


def _strip_type_qualifiers(text: str, module_name: str = '') -> str:
    """Strips stdlib and documented-module qualifiers from rendered type
        text without touching longer dotted identifiers.
    """
    text = re.sub(
        r'(?<![\w.])(?:typing|builtins|collections\.abc)\.', '', text
    )
    if module_name:
        text = re.sub(
            r'(?<![\w.])' + re.escape(module_name) + r'\.', '', text
        )
    return text


def _clean_type_alias_text(text: str, module_name: str = '') -> str:
    """Strips stdlib and documented-module qualifiers from rendered type
        alias text. String literals, such as the arguments of
        `Literal['typing.Foo']`, are copied verbatim, so their
        contents are never rewritten.
    """
    out = []
    start = 0
    index = 0
    quote = None
    while index < len(text):
        char = text[index]
        if quote is None:
            if char in ("'", '"'):
                out.append(
                    _strip_type_qualifiers(text[start:index], module_name)
                )
                quote = char
                start = index
            index += 1
        else:
            if char == '\\':
                index += 2
                continue
            if char == quote:
                out.append(text[start:index + 1])
                quote = None
                start = index + 1
            index += 1
    out.append(_strip_type_qualifiers(text[start:], module_name))
    return ''.join(out)


def _backtick(text: str, enabled: bool) -> str:
    """Wraps `text` in backticks when `enabled` is True."""
    return f'`{text}`' if enabled else text


def _backtick_enabled(options: dict, key: str) -> bool:
    """Returns whether backticks are enabled for the given option key.
        The `backticks` umbrella option, when False, disables backticks
        for every category; it never re-enables a category disabled by a
        granular option.
    """
    master = options['backticks'] if 'backticks' in options else True
    granular = options[key] if key in options else True
    return master and granular


_INLINE_CONTAINER_LIMIT = 3
_INLINE_BYTES_LIMIT = 40
_SIMPLE_SCALAR_TYPES = (
    type(None), bool, int, float, complex, str, bytes, bytearray, range,
    type(Ellipsis),
)


def _is_simple_scalar(value: Any) -> bool:
    """Returns whether `value` can be rendered inline as a scalar
        default: a builtin scalar, an enum member, `typing.Any`, a
        type alias, a `NewType`, or a class.
    """
    return (
        type(value) in _SIMPLE_SCALAR_TYPES
        or isinstance(value, Enum)
        or value is typing.Any
        or _is_new_type(value)
        or _is_type_alias(value)
        or isinstance(value, type)
    )


def _is_inline_scalar(value: Any) -> bool:
    """Returns whether `value` is a simple scalar that fits inline.
        Applies `_INLINE_BYTES_LIMIT` to bytes-like values, including
        when they are nested in a container.
    """
    if type(value) in (bytes, bytearray):
        return len(value) <= _INLINE_BYTES_LIMIT
    return _is_simple_scalar(value)


def _is_simple_default(value: Any) -> bool:
    """Returns whether `value` can be rendered inline without the
        verbose option. Containers qualify only when they are very
        small (at most `_INLINE_CONTAINER_LIMIT` items), not nested,
        and contain only simple scalars. Bytes-like values qualify
        only up to `_INLINE_BYTES_LIMIT` bytes, including when nested
        in a container.
    """
    if _is_inline_scalar(value):
        return True
    if type(value) not in (tuple, list, set, frozenset, dict):
        return False
    if len(value) > _INLINE_CONTAINER_LIMIT:
        return False
    if type(value) is dict:
        return all(
            _is_inline_scalar(key) and _is_inline_scalar(item)
            for key, item in value.items()
        )
    return all(_is_inline_scalar(item) for item in value)


def _enum_default_str(value: Enum) -> str:
    """Renders an enum member. Combined flags are rendered as a
        union of fully qualified member names.
    """
    class_name = type(value).__name__
    names = []
    if isinstance(value, Flag):
        if value.name:
            names = value.name.split('|')
        else:
            names = [
                member.name for member in type(value)
                if  (   member.value != 0
                        and member & value == member
                    )
            ]
    elif value.name is not None:
        names = [value.name]

    if names:
        return ' | '.join(
            f'{class_name}.{name}' for name in names
        )
    return f'{class_name}({value.value!r})'


def _simple_default_str(
        value: Any, options: dict | None = None
    ) -> str:
    """Renders a simple default inline. Enum members use
        `Enum.MEMBER`; type aliases and `NewType` values render as their
        annotation text; containers preserve their literal syntax. Dict
        keys are sorted only when `sort_default_dicts` is set.
    """
    options = options or {}
    if value is Ellipsis:
        return '...'
    if value is typing.Any:
        return 'Any'
    if _is_new_type(value) or _is_type_alias(value):
        return _annotation_str(value)
    if isinstance(value, Enum):
        return _enum_default_str(value)
    if isinstance(value, type):
        return value.__name__
    if type(value) is dict:
        items = [
            (
                _simple_default_str(key, options),
                _simple_default_str(item, options),
            )
            for key, item in value.items()
        ]
        if options.get('sort_default_dicts', False):
            items.sort()
        rendered = ', '.join(f'{key}: {item}' for key, item in items)
        return '{' + rendered + '}'
    if type(value) is list:
        return '[' + ', '.join(
            _simple_default_str(item, options) for item in value
        ) + ']'
    if type(value) is tuple:
        items = ', '.join(_simple_default_str(item, options) for item in value)
        return f'({items},)' if len(value) == 1 else f'({items})'
    if type(value) is set:
        if not value:
            return 'set()'
        items = sorted(_simple_default_str(item, options) for item in value)
        return '{' + ', '.join(items) + '}'
    if type(value) is frozenset:
        if not value:
            return 'frozenset()'
        items = sorted(_simple_default_str(item, options) for item in value)
        return 'frozenset({' + ', '.join(items) + '})'
    return repr(value)


def _callable_default_str(value: Callable) -> str:
    """Renders a callable default as `Callable[..., ReturnType]`.
        Argument types are intentionally omitted, and a missing or
        uninspectable return annotation becomes `Any`.
    """
    try:
        _, return_annotation = _signature_parts(value)
    except Exception:
        return 'Callable[..., Any]'
    if return_annotation is Parameter.empty:
        return 'Callable[..., Any]'
    return f'Callable[..., {_annotation_str(return_annotation)}]'


def _verbose_default_str(
        value: Any, options: dict | None = None,
        seen: set[int] | None = None
    ) -> str:
    """Renders a complex default deterministically. Cycles are
        rendered as `...`; non-callable object instances use a stable
        `TypeName(...)` placeholder instead of their memory address,
        and callable instances render as `Callable[..., ReturnType]`.
        Dict keys are sorted only when `sort_default_dicts` is set.
    """
    options = options or {}
    seen = seen if seen is not None else set()
    if _is_simple_scalar(value):
        return _simple_default_str(value, options)
    if callable(value):
        return _callable_default_str(value)

    value_id = id(value)
    if value_id in seen:
        return '...'

    if type(value) is dict:
        seen.add(value_id)
        try:
            items = [
                (
                    _verbose_default_str(key, options, seen),
                    _verbose_default_str(item, options, seen),
                )
                for key, item in value.items()
            ]
        finally:
            seen.discard(value_id)
        if options.get('sort_default_dicts', False):
            items.sort()
        rendered = ', '.join(f'{key}: {item}' for key, item in items)
        return '{' + rendered + '}'

    if type(value) in (list, tuple, set, frozenset):
        seen.add(value_id)
        try:
            rendered = [
                _verbose_default_str(item, options, seen)
                for item in value
            ]
        finally:
            seen.discard(value_id)
        if type(value) is list:
            return '[' + ', '.join(rendered) + ']'
        if type(value) is tuple:
            body = ', '.join(rendered)
            return f'({body},)' if len(rendered) == 1 else f'({body})'
        rendered.sort()
        if type(value) is set:
            if not rendered:
                return 'set()'
            return '{' + ', '.join(rendered) + '}'
        if not rendered:
            return 'frozenset()'
        return 'frozenset({' + ', '.join(rendered) + '})'

    return f'{type(value).__name__}(...)'


def _default_str(
        value: Any, options: dict | None = None,
        seen: set[int] | None = None
    ) -> str:
    """Renders a parameter default. Simple values are shown inline;
        complex values are abbreviated to `...` unless
        `options['verbose_defaults']` is set.
    """
    options = options or {}
    if _is_simple_default(value):
        return _simple_default_str(value, options)
    if options.get('verbose_defaults', False):
        return _verbose_default_str(value, options, seen)
    return '...'


def _param_str(
        param: Parameter, options: dict | None = None,
        seen: set[int] | None = None
    ) -> str:
    """Renders a parameter with its variadic marker, annotation, and
        default when present. Complex defaults are abbreviated unless
        `options['verbose_defaults']` is set.
    """
    match param.kind:
        case Parameter.VAR_POSITIONAL:
            text = f'*{param.name}'
        case Parameter.VAR_KEYWORD:
            text = f'**{param.name}'
        case _:
            text = param.name

    if param.annotation is not Parameter.empty:
        text += f': {_annotation_str(param.annotation)}'

    if param.default is not Parameter.empty:
        text += f' = {_default_str(param.default, options, seen)}'

    return text


def _has_implicit_receiver(function: Callable) -> bool:
    """Returns whether the parameters include an implicit receiver
        (`self`/`cls`) to omit. Raw `classmethod` descriptors, even
        when reached through a wrapper, and functions defined in a
        class body qualify; raw `staticmethod` descriptors, bound
        methods, module-level functions, and functions in `<locals>`
        or comprehension scopes do not. A `staticmethod` reached
        through its class looks like an unbound method, so pass the raw
        descriptor from the class `__dict__` for an accurate result.
    """
    if isinstance(function, MethodType):
        return False
    function = _unwrap_function(function)
    if isinstance(function, classmethod):
        return True
    if isinstance(function, staticmethod):
        return False
    if not isinstance(function, FunctionType):
        return False
    qualname = getattr(function, '__qualname__', '')
    scope, _, _ = qualname.rpartition('.')
    return bool(scope) and not scope.rpartition('.')[2].startswith('<')


def _signature_parts(function: Callable) -> tuple[list[Parameter], Any]:
    """Extracts the parameters and return annotation from the signature
        of a function. Raw `classmethod` descriptors, which cannot be
        inspected, are unwrapped first. Falls back to an empty list and
        the `__annotations__` return annotation when it fails.
    """
    if isinstance(function, classmethod):
        function = function.__func__
    try:
        sig = signature(function)
        return [*sig.parameters.values()], sig.return_annotation
    except (TypeError, ValueError):
        annotations = getattr(function, '__annotations__', None) or {}
        return [], annotations.get('return', Parameter.empty)


def dox_a_function(function: Callable, options: dict | None = None) -> str:
    """Collects some information about a function and returns it
        formatted as specified in the options or as a list.
    """
    _debug(
        1, 'dox_a_function(',
        getattr(function, '__name__', '[unnamed function]'), options, ')'
    )
    options = options or {}
    function, options = _invoke_handler(Event.BEFORE_FUNCTION, function, options)
    header_level = options['header_level'] if 'header_level' in options else 0
    format = options['format'] if 'format' in options else 'list'
    prepend = options['prepend'] if 'prepend' in options else ''
    backtick_signatures = _backtick_enabled(options, 'backtick_signatures')

    if iscoroutinefunction(_unwrap_for_inspection(function)):
        prepend = f'{prepend}async '

    name = (
        function.__name__ if hasattr(function, '__name__') else '{unknown/unnamed}'
    )
    params, return_annotation = _signature_parts(function)
    has_receiver = _has_implicit_receiver(function)

    parts = []
    pos_only_rendered, slash_emitted = False, False
    star_emitted, varargs_rendered = False, False
    seen = set()

    for position, param in enumerate(params):
        if  (   position == 0
                and has_receiver
                and param.name in ('self', 'cls')
            ):
            continue

        if  (   param.kind is not Parameter.POSITIONAL_ONLY
                and pos_only_rendered
                and not slash_emitted
            ):
            parts.append('/')
            slash_emitted = True

        if  (   param.kind is Parameter.KEYWORD_ONLY
                and not varargs_rendered
                and not star_emitted
            ):
            parts.append('*')
            star_emitted = True

        if param.kind is Parameter.VAR_POSITIONAL:
            varargs_rendered = True

        parts.append(_param_str(param, options, seen))

        if param.kind is Parameter.POSITIONAL_ONLY:
            pos_only_rendered = True

    if pos_only_rendered and not slash_emitted:
        parts.append('/')

    annotations = ', '.join(parts)
    docstring = function.__doc__ if hasattr(function, '__doc__') else None

    tick = '`' if backtick_signatures else ''
    sig_str = f'{tick}{prepend}{name}({annotations})'
    if return_annotation is not Parameter.empty:
        sig_str += f' -> {_annotation_str(return_annotation)}'
    sig_str += f':{tick}' + ('' if format == 'header' else ' ')

    doc = ''

    match format:
        case 'header':
            doc = _header(sig_str, header_level)
            if docstring:
                doc += _paragraph(docstring, options)
        case 'paragraph':
            doc = _paragraph(sig_str, options)
            if docstring:
                doc += _paragraph(docstring, options)
        case _:
            doc = sig_str
            if docstring:
                doc += docstring
            doc = _list(doc)

    return _invoke_handler(Event.AFTER_FUNCTION, doc)


def _is_visible(
        name: str, include_private: bool, include_dunder: bool,
        always_visible: tuple[str, ...] = ()
    ) -> bool:
    """Returns whether a class member or annotation name should be
        documented given the privacy options. Names in `always_visible`
        are documented regardless of the other options.
    """
    if name in always_visible:
        return True
    if name[:2] == '__':
        return include_dunder
    if name[:1] == '_':
        return include_private
    return True


def _unmangle_name(name: str, owner: str = '') -> str:
    """Returns the source name of a name-mangled class member. Python
        stores a class-body `__name` (at most one trailing underscore)
        as `_ClassName__name`; this reverses that transformation.
    """
    if not owner:
        return name
    prefix = '_' + owner.lstrip('_')
    if name.startswith(prefix + '__'):
        return name[len(prefix):]
    return name


def _annotation_owner(cls: type, name: str) -> str:
    """Returns the name of the first class in the MRO that defines the
        given annotation, defaulting to the name of `cls`.
    """
    fallback = cls.__name__ if hasattr(cls, '__name__') else ''
    for klass in getattr(cls, '__mro__', ()):
        if name in vars(klass).get('__annotations__', {}):
            if hasattr(klass, '__name__'):
                return klass.__name__
            return fallback
    return fallback


def _dox_properties(
        properties: dict, header_level: int = 0, classname: str = ''
    ) -> str:
    """Format properties for a class."""
    _debug(1, '_dox_properties(', properties, header_level, ')')
    doc = ''
    dunders = {
        name: value
        for name, value in properties.items()
        if name[:2] == '__'
    }
    privates = {
        name: value
        for name, value in properties.items()
        if name[:1] == '_' and name not in dunders
    }
    publics = {
        name: value
        for name, value in properties.items()
        if name not in dunders and name not in privates
    }

    if publics:
        for name, value in publics.items():
            display = _unmangle_name(name, classname)
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{display}: {value.__doc__}')
            else:
                doc += _list(display)

    if privates:
        for name, value in privates.items():
            display = _unmangle_name(name, classname)
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{display}: {value.__doc__}')
            else:
                doc += _list(display)

    if dunders:
        for name, value in dunders.items():
            display = _unmangle_name(name, classname)
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{display}: {value.__doc__}')
            else:
                doc += _list(display)

    return doc


def _dox_methods(cls: type, methods: dict, options: dict | None = None) -> str:
    """Format a collection of methods/functions."""
    _debug(
        1, '_dox_methods(',
        getattr(cls, '__name__', '[unnamed class]'), methods, options, ')'
    )
    options = options or {}
    header_level = options['header_level'] if 'header_level' in options else 0
    header_level += 1
    suboptions = {**options, 'header_level': header_level}
    format = options['method_format'] if 'method_format' in options else 'header'
    doc = ''

    dunders = {
        name: value
        for name, value in methods.items()
        if name[:2] == '__'
    }
    privates = {
        name: value
        for name, value in methods.items()
        if name[:1] == '_' and name not in dunders
    }
    publics = {
        name: value
        for name, value in methods.items()
        if name not in dunders and name not in privates
    }

    if dunders:
        for name, value in dunders.items():
            target = _name_of(value, name)
            if target != name and cls.__dict__.get(target) is value:
                doc += _dox_alias(name, target, header_level, format, options)
            else:
                doc += dox_a_function(value, {**suboptions, 'format': format})

    if publics:
        for name, value in publics.items():
            target = _name_of(value, name)
            if target != name and cls.__dict__.get(target) is value:
                doc += _dox_alias(name, target, header_level, format, options)
            elif _is_classmethod(value):
                doc += dox_a_function(
                    getattr(cls, name),
                    {**suboptions, 'format': format, 'prepend': '@classmethod '}
                )
            elif _is_staticmethod(value):
                doc += dox_a_function(
                    value,
                    {**suboptions, 'format': format, 'prepend': '@staticmethod '}
                )
            else:
                doc += dox_a_function(value, {**suboptions, 'format': format})

    if privates:
        for name, value in privates.items():
            target = _name_of(value, name)
            if target != name and cls.__dict__.get(target) is value:
                doc += _dox_alias(name, target, header_level, format, options)
            else:
                doc += dox_a_function(value, {**suboptions, 'format': format})

    return doc


def _get_all_annotations(cls: type) -> dict:
    """Collects all annotations from a class hierarchy."""
    _debug(1, '_get_all_annotations(', cls, ')')
    annotations = cls.__annotations__ if hasattr(cls, '__annotations__') else {}
    parent = cls.__base__ if hasattr(cls, '__base__') else None
    if parent and hasattr(parent, '__annotations__'):
        annotations = {**_get_all_annotations(parent), **annotations}
    return annotations


def dox_a_class(cls: type, options: dict | None = None) -> str:
    """Collects some information about a class and returns a formatted
        str. Any names specified in options['exclude_names'] will be
        excluded. Private and dunder members will be included if
        options['include_private'] or options['include_dunder'] are
        specified, respectively.
    """
    _debug(
        1, 'dox_a_class(',
        getattr(cls, '__name__', '[unnamed class]'), options, ')'
    )
    options = options or {}
    cls, options = _invoke_handler(Event.BEFORE_CLASS, cls, options)
    exclude_names = options['exclude_names'] if 'exclude_names' in options else []
    header_level = options['header_level'] if 'header_level' in options else 0
    include_private = 'include_private' in options
    include_dunder = 'include_dunder' in options
    backtick_names = _backtick_enabled(options, 'backtick_names')
    backtick_types = _backtick_enabled(options, 'backtick_types')
    suboptions = {**options, 'header_level': header_level + 1}

    classname = (
        cls.__name__ if hasattr(cls, '__name__') else '{unknown/unnamed class}'
    )
    if classname in exclude_names:
        return ''

    parent = cls.__base__ if hasattr(cls, '__base__') else None

    properties = {}
    methods = {}
    annotations = {}
    for name, value in _get_all_annotations(cls).items():
        owner = _annotation_owner(cls, name)
        display = _unmangle_name(name, owner)
        if  (   name in exclude_names
                or display in exclude_names
            ):
            continue
        if not _is_visible(name, include_private, include_dunder):
            continue
        annotations[display] = value

    if parent:
        parent = parent.__name__ if hasattr(parent, '__name__') else str(parent)
    parent = None if parent == 'object' else parent

    for name, item in cls.__dict__.items():
        if not _is_visible(
                name, include_private, include_dunder, ('__init__',)
            ):
            continue
        if  (   name in exclude_names
                or _unmangle_name(name, classname) in exclude_names
            ):
            continue

        if _is_function_like(item):
            # ignoring Protocol __init__ method overridden with an empty method
            # https://github.com/python/cpython/issues/110788
            if  (   name == '__init__'
                    and getattr(item, '__name__', '')
                        == "_no_init_or_replace_init"
                ):
                continue
            methods[name] = item

        if type(item) is property:
            properties[name] = item

    header_name = f'{classname}({parent})' if parent else classname
    doc = _header(_backtick(header_name, backtick_names), header_level)

    docstring = cls.__doc__ if hasattr(cls, '__doc__') else None
    if docstring:
        doc += _paragraph(docstring, options)

    if annotations:
        doc += _header('Annotations', header_level + 1)
        for name, value in annotations.items():
            name_str = _backtick(name, backtick_names)
            type_str = _backtick(_annotation_str(value), backtick_types)
            doc += _list(f'{name_str}: {type_str}')
        doc += '\n'

    if properties:
        doc += _header('Properties', header_level + 1)
        doc += _dox_properties(properties, header_level, classname) + '\n'

    if methods:
        doc += _header('Methods', header_level + 1)
        doc += _dox_methods(cls, methods, suboptions)

    return _invoke_handler(Event.AFTER_CLASS, doc)
