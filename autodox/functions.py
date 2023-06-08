from types import ModuleType
from typing import Any, Callable


def dox_a_module(module: ModuleType, options: dict = None) -> str:
    """Iterates over a module, collects information about its parts, and
        returns a str containing markdown documentation generated from
        types, annotations, and docstrings.
    """
    exclude_names = options['exclude_names'] if 'exclude_names' in options else []
    exclude_types = options['exclude_types'] if 'exclude_types' in options else []
    header_level = options['header_level'] if 'header_level' in options else 0
    include_private = 'include_private' in options
    include_dunder = 'include_dunder' in options
    include_submodules = 'include_submodules' in options
    document_submodules = 'document_submodules' in options
    suboptions = {**options, 'header_level': header_level + 1}

    values = []
    functions = []
    classes = []
    submodules = []

    for name, item in module.__dict__.items():
        item_type = type(item)

        if name[:1] == '_' and not include_private:
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
            classes.append(doc)
            continue

        if type(item) is type(dox_a_module):
            doc = dox_a_function(item, suboptions)
            functions.append(doc)
            continue

        doc = dox_a_value(item, suboptions)
        values.append(doc)

    ...


def dox_a_value(value: Any, options: dict = None) -> str:
    ...

def dox_a_function(function: Callable, options: dict = None) -> str:
    ...

def dox_a_class(cls: type, options: dict = None) -> str:
    ...
