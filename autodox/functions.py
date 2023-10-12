from enum import Enum, auto
from types import ModuleType, MethodType, FunctionType
from typing import Any, Callable



class Event(Enum):
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
_debug_level = 0


def _debug(level = 1, *args):
    """Print a debug statement if enabled."""
    if _debug_level >= level:
        print(*args)


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


def set_before_handler(event: Event, function: Callable[[Any, dict], tuple[Any, dict]]) -> None:
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


def _invoke_handler(event: Event, *args) -> None:
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


def _paragraph(docstring: str) -> str:
    """Takes a docstring, tokenizes it, and returns a str formatted to
        72 chars or fewer per line without splitting tokens.
    """
    _debug(2, '_paragraph(', docstring, ')')
    def make_line(tokens: list[str]) -> tuple[str, list[str]]:
        _debug(2, 'make_line(', tokens, ')')
        line = ''
        while len(tokens) and (
            len(line) + len(tokens[0]) <= 80 or line.count('`') == 1
        ) or (len(line) == 0 and len(tokens[0]) > 80):
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


def _list(line: str) -> str:
    """Takes a line and returns a formatted list item."""
    _debug(2, '_list(', line, ')')
    doc = _paragraph(f'- {line}')[:-1]
    return _invoke_handler(Event.AFTER_LIST, doc)


def dox_a_module(module: ModuleType, options: dict = {}) -> str:
    """Iterates over a module, collects information about its parts, and
        returns a str containing markdown documentation generated from
        types, annotations, and docstrings.
    """
    _debug(1, 'dox_a_module(', module.__name__, options, ')')
    module, options = _invoke_handler(Event.BEFORE_MODULE, module, options)
    exclude_names = options['exclude_names'] if 'exclude_names' in options else []
    exclude_types = options['exclude_types'] if 'exclude_types' in options else []
    header_level = options['header_level'] if 'header_level' in options else 0
    function_format = options['function_format'] if 'function_format' in options else 'header'
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
            doc = dox_a_class(item, suboptions)
            if doc:
                classes.append(doc)
            continue

        if type(item) is type(dox_a_module):
            doc = dox_a_function(item, {**suboptions, 'format': function_format})
            functions.append(doc)
            continue

        doc = dox_a_value(item, {**suboptions, 'name': name, 'format': value_format})
        values.append(doc)

    doc = _header(module.__name__, header_level)

    if hasattr(module, '__doc__') and module.__doc__:
        doc += _paragraph(module.__doc__)

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


def dox_a_value(value: Any, options: dict = {}) -> str:
    """Collects some information about a value and returns it formatted
        as specified in the options or as a list.
    """
    _debug(1, 'dox_a_value(', value, options, ')')
    value, options = _invoke_handler(Event.BEFORE_VALUE, value, options)
    header_level = options['header_level'] if 'header_level' in options else 0
    format = options['format'] if 'format' in options else 'list'

    name = value.__name__ if hasattr(value, '__name__') else '{unknown/unnamed}'
    if 'name' in options:
        name = options['name']
    type_str = type(value).__name__
    doc = ''

    match format:
        case 'header':
            doc = _header(f'`{name}`: {type_str}', header_level)
        case 'paragraph':
            doc = _paragraph(f'`{name}`: {type_str}')
        case _:
            doc = _list(f'`{name}`: {type_str}')

    return _invoke_handler(Event.AFTER_VALUE, doc)


def dox_a_function(function: Callable, options: dict = {}) -> str:
    """Collects some information about a function and returns it
        formatted as specified in the options or as a list.
    """
    _debug(1, 'dox_a_function(', function.__name__, options, ')')
    function, options = _invoke_handler(Event.BEFORE_FUNCTION, function, options)
    header_level = options['header_level'] if 'header_level' in options else 0
    format = options['format'] if 'format' in options else 'list'
    prepend = options['prepend'] if 'prepend' in options else ''

    name = function.__name__ if hasattr(function, '__name__') else '{unknown/unnamed}'
    annotations = function.__annotations__ if hasattr(function, '__annotations__') else {}
    return_annotation = annotations['return'] if 'return' in annotations else None
    annotations = [
        f'{key}: {value.__name__ if hasattr(value, "__name__") else str(value)}'
        for key, value in annotations.items()
        if key != 'return'
    ]

    if hasattr(function, '__defaults__') and function.__defaults__:
        defaults = [*function.__defaults__]
    else:
        defaults = []

    if hasattr(function, '__kwdefaults__') and function.__kwdefaults__:
        kwdefaults = {**function.__kwdefaults__}
    else:
        kwdefaults = {}

    offset = len(annotations) - len(defaults) - len(kwdefaults)
    if offset < 0:
        offset = 0

    if annotations and defaults:
        for i in range(len(defaults)):
            if type(defaults[i]) is str:
                annotations[i+offset] += f" = '{defaults[i]}'"
            elif type(defaults[i]) is type:
                annotations[i+offset] += f' = {defaults[i].__name__}'
            else:
                annotations[i+offset] += f' = {defaults[i]}'

    kwannotations, indices = [], []
    if annotations and kwdefaults:
        for k, v in kwdefaults.items():
            if k in [a.split(':')[0] for a in annotations]:
                i = [a.split(':')[0] for a in annotations].index(k)
                indices.append(i)
                if type(v) is str:
                    kwannotations.append(annotations[i] + f" = '{v}'")
                elif type(v) is type:
                    kwannotations.append(annotations[i] + f" = {v.__name__}")
                else:
                    kwannotations.append(annotations[i] + f" = {v}")

    indices.sort()
    while len(indices):
        i = indices.pop()
        del annotations[i]

    if len(kwannotations):
        annotations.append('/, *')
        while len(kwannotations):
            annotations.append(kwannotations.pop())

    annotations = ', '.join(annotations) or ''
    docstring = function.__doc__ if hasattr(function, '__doc__') else None

    signature = f'`{prepend}{name}({annotations})'
    if return_annotation:
        if '[' in str(return_annotation):
            return_annotation = str(return_annotation)
        elif hasattr(return_annotation, '__name__'):
            return_annotation = return_annotation.__name__
        signature += f' -> {return_annotation}'
    signature += ':` ' if format != 'header' else ':`'

    doc = ''

    match format:
        case 'header':
            doc = _header(signature, header_level)
            if docstring:
                doc += _paragraph(docstring)
        case 'paragraph':
            doc = _paragraph(signature)
            if docstring:
                doc += _paragraph(docstring)
        case _:
            doc = signature
            if docstring:
                doc += docstring
            doc = _list(doc)

    return _invoke_handler(Event.AFTER_FUNCTION, doc)


def _dox_properties(properties: dict, header_level: int = 0) -> str:
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
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{name}: {value.__doc__}')
            else:
                doc += _list(name)

    if privates:
        for name, value in privates.items():
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{name}: {value.__doc__}')
            else:
                doc += _list(name)

    if dunders:
        for name, value in dunders.items():
            if hasattr(value, '__doc__') and value.__doc__:
                doc += _list(f'{name}: {value.__doc__}')
            else:
                doc += _list(name)

    return doc


def _dox_methods(cls: type, methods: dict, options: dict = {}) -> str:
    """Format a collection of methods/functions."""
    _debug(1, '_dox_methods(', cls.__name__, methods, options, ')')
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
        for _, value in dunders.items():
            doc += dox_a_function(value, {**suboptions, 'format': format})

    if publics:
        for name, value in publics.items():
            if isinstance(value, classmethod):
                doc += dox_a_function(getattr(cls, name), {**suboptions, 'format': format, 'prepend': '@classmethod '})
            elif isinstance(cls.__dict__[name], staticmethod):
                doc += dox_a_function(value, {**suboptions, 'format': format, 'prepend': '@staticmethod '})
            else:
                doc += dox_a_function(value, {**suboptions, 'format': format})

    if privates:
        for _, value in privates.items():
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


def dox_a_class(cls: type, options: dict = {}) -> str:
    """Collects some information about a class and returns a formatted
        str. Any names specified in options['exclude_names'] and any
        types specified in options['exclude_types'] will be excluded.
        Private and dunder methods/properties will be included if
        options['include_private'] or options['include_dunder'] are
        specified, respectively.
    """
    _debug(1, 'dox_a_class(', cls.__name__, options, ')')
    cls, options = _invoke_handler(Event.BEFORE_CLASS, cls, options)
    exclude_names = options['exclude_names'] if 'exclude_names' in options else []
    header_level = options['header_level'] if 'header_level' in options else 0
    include_private = 'include_private' in options
    include_dunder = 'include_dunder' in options
    suboptions = {**options, 'header_level': header_level + 1}

    classname = cls.__name__ if hasattr(cls, '__name__') else '{unknown/unnamed class}'
    if classname in exclude_names:
        return ''

    parent = cls.__base__ if hasattr(cls, '__base__') else None

    properties = {}
    methods = {}
    annotations = _get_all_annotations(cls)

    if parent:
        parent = parent.__name__ if hasattr(parent, '__name__') else str(parent)
    parent = None if parent == 'object' else parent

    for name, item in cls.__dict__.items():
        if name[:1] == '_' and not (include_private or include_dunder) and name != '__init__':
            continue
        if name[:1] == '_' and include_dunder and not include_private and name[:2] != '__':
            continue
        if name[:2] == '__' and not include_dunder and name != '__init__':
            continue
        if name in exclude_names:
            continue

        if type(item) in (MethodType, FunctionType, staticmethod, classmethod):
            methods[name] = item

        if type(item) is property:
            properties[name] = item

    doc = _header(f'`{classname}({parent})`', header_level) if parent else _header(f'`{classname}`', header_level)

    docstring = cls.__doc__ if hasattr(cls, '__doc__') else None
    if docstring:
        doc += _paragraph(docstring)

    if annotations:
        doc += _header('Annotations', header_level + 1)
        for name, value in annotations.items():
            doc += _list(f'{name}: {str(value)}')
        doc += '\n'

    if properties:
        doc += _header('Properties', header_level + 1)
        doc += _dox_properties(properties, header_level) + '\n'

    if methods:
        doc += _header('Methods', header_level + 1)
        doc += _dox_methods(cls, methods, suboptions)

    return _invoke_handler(Event.AFTER_CLASS, doc)


def _cli_help(name: str) -> int:
    print(f'Usage: {name} [package[.module]] [options] ')
    print('\t-exclude_name=str: exclude the given name (or csv of names)')
    print('\t-exclude_type=str: exclude the given type (or csv of types)')
    print('\t-header_level=int: number of hashtags to prepend to headers')
    print('\t-package=str: name of package if not using the . notation')
    print('\t-function_format=str: choose one of "header", "paragraph", or "list"')
    print('\t-method_format=type: choose one of "header", "paragraph", or "list"')
    print('\t-value_format=type: choose one of "header", "paragraph", or "list"')
    print('\t-include_private: includes things prefaced with "_"')
    print('\t-include_dunder: includes things prefaced with "__"')
    print('\t-include_submodules: includes submodules')
    print('\t-document_submodules: runs module documentation for submodules')
    print('\t-debug: increases level of debug statements printed; starts at 0')
    print('\t\tand increases once for each time this flag is passed; level 1')
    print('\t\tprints out the trace for dox_{thing} calls; level 2 includes')
    print('\t\tformatting functions; level 3 includes hooks functions')
    return 0


def invoke_cli(args: list[str]) -> int:
    """Entry point for pip installed wrapper function to invoke via CLI."""
    from importlib import import_module
    _settings = {}
    _module = ''

    for arg in args[1:]:
        if arg in ('--help', '-help', '-?', '-h', '?'):
            return _cli_help(args[0])

        if arg[:14] == '-exclude_name=':
            if 'exclude_names' not in _settings:
                _settings['exclude_names'] = []
            _settings['exclude_names'].extend(arg[14:].split(','))
        elif arg[:14] == '-exclude_type=':
            if 'exclude_types' not in _settings:
                _settings['exclude_types'] = []
            _settings['exclude_types'].extend(arg[14:].split(','))
        elif arg[:14] == '-header_level=':
            _settings['header_level'] = int(arg[14:])
        elif arg[:9] == '-package=':
            _settings['package'] = arg[9:]
        elif arg[:17] == '-function_format=':
            _settings['function_format'] = arg[17:]
        elif arg[:15] == '-method_format=':
            _settings['method_format'] = arg[15:]
        elif arg[:14] == '-value_format=':
            _settings['value_format'] = arg[14:]
        elif arg == '-include_private':
            _settings['include_private'] = True
        elif arg == '-include_dunder':
            _settings['include_dunder'] = True
        elif arg == '-include_submodules':
            _settings['include_submodules'] = True
        elif arg == '-document_submodules':
            _settings['document_submodules'] = True
        elif arg == '-debug':
            global _debug_level
            _debug_level += 1
        elif arg[0] == '-':
            print(f'unrecognized option: {arg}')
            return 1
        else:
            _module = arg

    try:
        if 'package' in _settings:
            _module = import_module(_module, _settings['package'])
        else:
            _module = import_module(_module)
    except ModuleNotFoundError as e:
        print(f'ModuleNotFoundError: {str(e)}')
        return 1

    print(dox_a_module(_module, _settings))
    return 0


def main_cli() -> int:
    from sys import argv
    return invoke_cli(argv)
