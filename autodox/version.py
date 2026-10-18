from __future__ import annotations
import importlib.metadata


__version__ = importlib.metadata.version('autodox')


def version() -> str:
    """Returns the current version of this package."""
    return __version__
