from __future__ import annotations
from enum import Enum, auto
from inspect import Parameter, iscoroutinefunction, signature
from logging import addLevelName, CRITICAL, DEBUG, getLogger, INFO
from types import ModuleType, MethodType, FunctionType
from typing import Any, Callable


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


def _name_of(item: Any, fallback: str) -> str:
    """Returns the `__name__` of an item, unwrapping `__func__` so that
        raw `classmethod`/`staticmethod` objects resolve to the name of
        the wrapped function. Falls back to the given name when no
        `__name__` is available.
    """
    func = getattr(item, '__func__', item)
    return getattr(func, '__name__', fallback)


def _dox_alias(
        binding: str, target: str, header_level: int = 0,
        format: str = 'header'
    ) -> str:
    """Renders an alias binding, e.g. `UsageError = DependencyError`,
        using the specified format. Alias entries do not fire the
        `AFTER_CLASS` or `AFTER_FUNCTION` handlers.
    """
    _debug(1, '_dox_alias(', binding, target, header_level, format, ')')
    alias = f'`{binding} = {target}`'
    match format:
        case 'header':
            return _header(alias, header_level)
        case 'paragraph':
            return _paragraph(alias)
        case _:
            return _list(alias)


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

        if isinstance(item, type):
            target = _name_of(item, name)
            if target != name and module.__dict__.get(target) is item:
                doc = _dox_alias(name, target, header_level + 2)
            else:
                doc = dox_a_class(item, suboptions)
            if doc:
                classes.append(doc)
            continue

        if type(item) is type(dox_a_module):
            target = _name_of(item, name)
            if target != name and module.__dict__.get(target) is item:
                doc = _dox_alias(name, target, header_level + 2, function_format)
            else:
                doc = dox_a_function(
                    item, {**suboptions, 'format': function_format}
                )
            functions.append(doc)
            continue

        doc = dox_a_value(item, {**suboptions, 'name': name, 'format': value_format})
        values.append(doc)

    doc = _header(module.__name__, header_level)

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
        as specified in the options or as a list.
    """
    _debug(1, 'dox_a_value(', value, options, ')')
    options = options or {}
    value, options = _invoke_handler(Event.BEFORE_VALUE, value, options)
    header_level = options['header_level'] if 'header_level' in options else 0
    format = options['format'] if 'format' in options else 'list'
    backtick_names = (
        options['backtick_names'] if 'backtick_names' in options else True
    )
    backtick_types = (
        options['backtick_types'] if 'backtick_types' in options else True
    )

    name = value.__name__ if hasattr(value, '__name__') else '{unknown/unnamed}'
    if 'name' in options:
        name = options['name']
    name = _backtick(name, backtick_names)
    type_str = _backtick(type(value).__name__, backtick_types)
    doc = ''

    match format:
        case 'header':
            doc = _header(f'{name}: {type_str}', header_level)
        case 'paragraph':
            doc = _paragraph(f'{name}: {type_str}', options)
        case _:
            doc = _list(f'{name}: {type_str}')

    return _invoke_handler(Event.AFTER_VALUE, doc)


def _annotation_str(annotation: Any) -> str:
    """Renders an annotation as a str, keeping subscripts such as
        `dict[str, str]` verbatim.
    """
    text = str(annotation)
    if '[' in text:
        return text
    return annotation.__name__ if hasattr(annotation, '__name__') else text


def _backtick(text: str, enabled: bool) -> str:
    """Wraps `text` in backticks when `enabled` is True."""
    return f'`{text}`' if enabled else text


def _param_str(param: Parameter) -> str:
    """Renders a parameter with its variadic marker, annotation, and
        default when present.
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
        if type(param.default) is str:
            text += f" = '{param.default}'"
        elif type(param.default) is type:
            text += f' = {param.default.__name__}'
        else:
            text += f' = {param.default}'

    return text


def _has_implicit_receiver(function: Callable) -> bool:
    """Returns whether the parameters include an implicit receiver
        (`self`/`cls`) to omit. Raw `classmethod` descriptors and
        functions defined in a class body qualify; bound methods,
        module-level functions, and functions in `<locals>` or
        comprehension scopes do not. A `staticmethod` reached through
        its class looks like an unbound method, so pass the raw
        descriptor from the class `__dict__` for an accurate result.
    """
    if isinstance(function, classmethod):
        return True
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

    if iscoroutinefunction(function):
        prepend = f'{prepend}async '

    name = (
        function.__name__ if hasattr(function, '__name__') else '{unknown/unnamed}'
    )
    params, return_annotation = _signature_parts(function)
    has_receiver = _has_implicit_receiver(function)

    parts = []
    pos_only_rendered, slash_emitted = False, False
    star_emitted, varargs_rendered = False, False

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

        parts.append(_param_str(param))

        if param.kind is Parameter.POSITIONAL_ONLY:
            pos_only_rendered = True

    if pos_only_rendered and not slash_emitted:
        parts.append('/')

    annotations = ', '.join(parts)
    docstring = function.__doc__ if hasattr(function, '__doc__') else None

    sig_str = f'`{prepend}{name}({annotations})'
    if return_annotation is not Parameter.empty:
        sig_str += f' -> {_annotation_str(return_annotation)}'
    sig_str += ':` ' if format != 'header' else ':`'

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
                doc += _dox_alias(name, target, header_level, format)
            else:
                doc += dox_a_function(value, {**suboptions, 'format': format})

    if publics:
        for name, value in publics.items():
            target = _name_of(value, name)
            if target != name and cls.__dict__.get(target) is value:
                doc += _dox_alias(name, target, header_level, format)
            elif isinstance(value, classmethod):
                doc += dox_a_function(
                    getattr(cls, name),
                    {**suboptions, 'format': format, 'prepend': '@classmethod '}
                )
            elif isinstance(cls.__dict__[name], staticmethod):
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
                doc += _dox_alias(name, target, header_level, format)
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
    backtick_names = (
        options['backtick_names'] if 'backtick_names' in options else True
    )
    backtick_types = (
        options['backtick_types'] if 'backtick_types' in options else True
    )
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

        if type(item) in (MethodType, FunctionType, staticmethod, classmethod):
            # ignoring Protocol __init__ method overridden with an empty method
            # https://github.com/python/cpython/issues/110788
            if name == '__init__' and item.__name__ == "_no_init_or_replace_init":
                continue
            methods[name] = item

        if type(item) is property:
            properties[name] = item

    doc = _header(
        f'`{classname}({parent})`', header_level
    ) if parent else _header(f'`{classname}`', header_level)

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
