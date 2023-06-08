from types import ModuleType
from typing import Any, Callable


def dox_a_module(module: ModuleType, options: dict = None) -> str:
    ...

def dox_a_value(value: Any, options: dict = None) -> str:
    ...

def dox_a_function(function: Callable, options: dict = None) -> str:
    ...

def dox_a_class(cls: type, options: dict = None) -> str:
    ...
