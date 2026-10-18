"""
Autodox is a package for generating documentation from code annotations,
types, and docstrings.
"""


from .functions import (
    dox_a_class,
    dox_a_function,
    dox_a_module,
    dox_a_value,
    Event,
    set_before_handler,
    set_after_handler,
    unset_handler
)
from .version import version
from logging import getLogger, NullHandler


getLogger(__name__).addHandler(NullHandler())
del getLogger, NullHandler
