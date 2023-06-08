"""Autodox is a package for generating documentation from code
    annotations, types, and docstrings.
"""


from sys import argv
from .functions import (
    dox_a_class,
    dox_a_function,
    dox_a_module,
    dox_a_value
)


if __name__ == '__main__':
    from importlib import import_module
    _settings = {}
    _module = ''

    for arg in argv[1:]:
        if arg[:14] == '-exclude_name=':
            if 'exclude_name' not in _settings:
                _settings['exclude_names'] = []
            _settings['exclude_names'].append(arg[14:])
        elif arg[:14] == '-exclude_type=':
            if 'exclude_types' not in _settings:
                _settings['exclude_types'] = []
            _settings['exclude_types'].append(arg[14:])
        elif arg[:14] == '-header_level=':
            _settings['header_level'] = int(arg[14:])
        elif arg[:9] == '-package=':
            _settings['package'] = arg[9:]
        elif arg == '-include_private':
            _settings['include_private'] = True
        elif arg == '-include_dunder':
            _settings['include_dunder'] = True
        elif arg == '-include_submodules':
            _settings['include_submodules'] = True
        elif arg == '-document_submodules':
            _settings['document_submodules'] = True
        else:
            _module = arg

    if 'package' in _settings:
        _module = import_module(_module, _settings['package'])
    else:
        _module = import_module(_module)

    print(dox_a_module, _settings)
