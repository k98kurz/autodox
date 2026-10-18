"""
Build hook that blocks distribution builds while the package version
is a development version. Only editable installs (`pip install -e .`)
are allowed until the version is bumped to a release version.
"""

from __future__ import annotations
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        """Allow editable installs and release versions; block dev builds."""
        if version == 'editable':
            return
        project_version = self.metadata.version
        if 'dev' not in project_version.lower():
            return
        raise RuntimeError(
            f'Refusing to build distribution {project_version!r}; only '
            f'`pip install -e .` is allowed during development. Bump the '
            f'version to a release version to enable `python -m build`.'
        )
