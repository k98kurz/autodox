from __future__ import annotations
from context import functions
from dataclasses import dataclass
from typing import Any, Hashable
import unittest


@dataclass
class ExampleClass:
    clock_uuid: bytes
    ts: Any
    data: Hashable

    def pack(self) -> bytes:
        """Serialize to bytes."""
        ...

    @classmethod
    def unpack(cls, data: bytes, /, *, inject: dict = {}) -> ExampleClass:
        """Deserialize an ExampleClass."""
        ...


def diff(str1: str, str2: str) -> dict[str, list[str]]:
    min_len = min([len(str1), len(str2)])
    max_len = max([len(str1), len(str2)])
    diffs = {}
    start, end = None, None
    for i in range(min_len):
        if str1[i] == str2[i]:
            if end is not None:
                end = i-1
                start = None
                diffs[f"{start}-{end}"] = [str1[start:end], str2[start:end]]
            continue
        if start is None:
            start = i
    if start is not None:
        diffs[f"{start}-{max_len}"] = [str1[start:], str2[start:]]
    return diffs


class TestDoxAFunction(unittest.TestCase):
    def test_annotations_with_defaults(self):
        def fn_with_defaults(arg1: int, arg2: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, arg2: str = 'okay') -> bool:`"+\
            " Does a thing,\nreturns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

        def fn_with_defaults(arg1: int, arg2: bytes = b'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, arg2: bytes = b'okay') -> bool:`"+\
            " Does a thing,\nreturns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

    def test_annotations_with_kwdefaults(self):
        def fn_with_defaults(arg1: int, /, *, arg2: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, /, *, arg2: str = 'okay') -> bool:`"+\
            " Does a thing,\nreturns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

    def test_annotations_with_defaults_and_kwdefaults(self):
        def fn_with_defaults(arg1: int, arg2: bytes = b'not', /, *, arg3: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, arg2: bytes = b'not', /, *, arg3: str = 'okay') -> bool:`"+\
            "\nDoes a thing, returns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"


class TestDoxAClass(unittest.TestCase):
    def test_dox_a_class(self):
        doc = functions.dox_a_class(ExampleClass)
        expected = """# `ExampleClass`

## Annotations

- clock_uuid: bytes
- ts: Any
- data: Hashable

## Methods

### `pack() -> bytes:`

Serialize to bytes.

### `@classmethod unpack(data: bytes, /, *, inject: dict = {}) -> ExampleClass:`

Deserialize an ExampleClass.

"""

        assert doc == expected, \
            f"expected {{\n{expected}}} but got {{\n{doc}}} diff {{{diff(expected, doc)}}}"


if __name__ == '__main__':
    unittest.main()
