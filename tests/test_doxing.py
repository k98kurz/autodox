from __future__ import annotations
from context import functions
from typing import Any, Hashable, Protocol, runtime_checkable
import unittest


class ExampleClass:
    """An example class to document."""
    clock_uuid: bytes
    ts: Any
    data: Hashable

    def __init__(self, clock_uuid: bytes, ts: Any, data: Hashable) -> None:
        """The init method."""
        ...

    @property
    def thing(self) -> Any:
        """Some property."""
        ...

    def pack(self) -> bytes:
        """Serialize to bytes."""
        ...

    def __repr__(self) -> str:
        """Used for calls to repr."""
        ...

    def _private(self) -> None:
        """Gets mangled by runtime."""
        ...

    @classmethod
    def unpack(cls, data: bytes, /, *, inject: dict = {}) -> ExampleClass:
        """Deserialize an ExampleClass."""
        ...

    async def some_async_method(self, data: str) -> bool:
        """Example async method."""
        ...


@runtime_checkable
class ExampleInterface(Protocol):
    @classmethod
    def init(cls, name: str = 'foobar') -> ExampleInterface:
        """Should initialize."""
        ...
    def get_some_str(self) -> str:
        """Should return a str."""
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

    def test_annotations_with_empty_str_default(self):
        def fn_with_defaults(arg1: int, arg2: str = '') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, arg2: str = '') -> bool:`"+\
            " Does a thing, returns\nsome stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

    def test_annotations_with_type_default(self):
        def fn_with_defaults(arg1: int, arg2: type = ExampleClass) -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, arg2: type = ExampleClass) -> bool:`"+\
            " Does a\nthing, returns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

    def test_annotations_with_kwdefaults(self):
        def fn_with_defaults(arg1: int, /, *, arg2: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, /, *, arg2: str = 'okay') -> bool:`"+\
            " Does a thing,\nreturns some stuff.\n"
        assert doc == expected, f"expected {{\n{expected}}} but got {{\n{doc}}}"

    def test_annotations_with_type_kwdefault(self):
        def fn_with_defaults(arg1: int, /, *, arg2: type = ExampleClass) -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = "- `fn_with_defaults(arg1: int, /, *, arg2: type = ExampleClass) -> bool:`"+\
            " Does a\nthing, returns some stuff.\n"
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

An example class to document.

## Annotations

- clock_uuid: bytes
- ts: Any
- data: Hashable

## Properties

- thing: Some property.

## Methods

### `__init__(clock_uuid: bytes, ts: Any, data: Hashable) -> None:`

The init method.

### `pack() -> bytes:`

Serialize to bytes.

### `@classmethod unpack(data: bytes, /, *, inject: dict = {}) -> ExampleClass:`

Deserialize an ExampleClass.

### `async some_async_method(data: str) -> bool:`

Example async method.

"""

        assert doc == expected, \
            f"expected {{\n{expected}}} but got {{\n{doc}}} diff {{{diff(expected, doc)}}}"

    def test_with_private(self):
        doc = functions.dox_a_class(ExampleClass, options={'include_private': True})
        expected = """# `ExampleClass`

An example class to document.

## Annotations

- clock_uuid: bytes
- ts: Any
- data: Hashable

## Properties

- thing: Some property.

## Methods

### `__init__(clock_uuid: bytes, ts: Any, data: Hashable) -> None:`

The init method.

### `pack() -> bytes:`

Serialize to bytes.

### `@classmethod unpack(data: bytes, /, *, inject: dict = {}) -> ExampleClass:`

Deserialize an ExampleClass.

### `async some_async_method(data: str) -> bool:`

Example async method.

### `_private() -> None:`

Gets mangled by runtime.

"""

        assert doc == expected, \
            f"expected {{\n{expected}}} but got {{\n{doc}}} diff {{{diff(expected, doc)}}}"

    def test_with_private_and_dunder(self):
        options = {'include_private': True, 'include_dunder': True}
        doc = functions.dox_a_class(ExampleClass, options)
        expected = """# `ExampleClass`

An example class to document.

## Annotations

- clock_uuid: bytes
- ts: Any
- data: Hashable

## Properties

- thing: Some property.

## Methods

### `__init__(clock_uuid: bytes, ts: Any, data: Hashable) -> None:`

The init method.

### `__repr__() -> str:`

Used for calls to repr.

### `pack() -> bytes:`

Serialize to bytes.

### `@classmethod unpack(data: bytes, /, *, inject: dict = {}) -> ExampleClass:`

Deserialize an ExampleClass.

### `async some_async_method(data: str) -> bool:`

Example async method.

### `_private() -> None:`

Gets mangled by runtime.

"""

        assert doc == expected, \
            f"expected {{\n{expected}}} but got {{\n{doc}}} diff {{{diff(expected, doc)}}}"

    def test_with_dunder_and_without_private(self):
        options = {'include_dunder': True}
        doc = functions.dox_a_class(ExampleClass, options)
        expected = """# `ExampleClass`

An example class to document.

## Annotations

- clock_uuid: bytes
- ts: Any
- data: Hashable

## Properties

- thing: Some property.

## Methods

### `__init__(clock_uuid: bytes, ts: Any, data: Hashable) -> None:`

The init method.

### `__repr__() -> str:`

Used for calls to repr.

### `pack() -> bytes:`

Serialize to bytes.

### `@classmethod unpack(data: bytes, /, *, inject: dict = {}) -> ExampleClass:`

Deserialize an ExampleClass.

### `async some_async_method(data: str) -> bool:`

Example async method.

"""

        assert doc == expected, \
            f"expected {{\n{expected}}} but got {{\n{doc}}} diff {{{diff(expected, doc)}}}"


class TestDoxAProtocol(unittest.TestCase):
    def test_dox_a_protocol(self):
        # discovered that the Protocol is designed to prevent documenting the init interface
        # https://github.com/python/cpython/issues/110788
        observed = functions.dox_a_class(ExampleInterface)
        expected = """# `ExampleInterface(Protocol)`

## Methods

### `@classmethod init(name: str = 'foobar') -> ExampleInterface:`

Should initialize.

### `get_some_str() -> str:`

Should return a str.

"""
        assert observed == expected, f"expected\n{expected}\nbut observed\n{observed}"

    def test_dox_a_protocol_with_long_line_length(self):
        @runtime_checkable
        class LongParagraphInterface(Protocol):
            """Lorem ipsum dolor sit amet, consectetur adipiscing elit,
                sed do eiusmod tempor incididunt ut labore et dolore
                magna aliqua. Ut enim ad minim veniam, quis nostrud
                exercitation ullamco laboris nisi ut aliquip ex ea
                commodo consequat. Duis aute irure dolor in
                reprehenderit in voluptate velit esse cillum dolore eu
                fugiat nulla pariatur. Excepteur sint occaecat cupidatat
                non proident, sunt in culpa qui officia deserunt mollit
                anim id est laborum.
            """
            ...

        observed = functions.dox_a_class(LongParagraphInterface)
        expected = """# `LongParagraphInterface(Protocol)`

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.

"""
        assert observed == expected, f"expected\n{expected}\nbut observed\n{observed}"

        observed = functions.dox_a_class(LongParagraphInterface, {'line_length': 100})
        expected = """# `LongParagraphInterface(Protocol)`

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.

"""
        assert observed == expected, f"expected\n{expected}\nbut observed\n{observed}"

        observed = functions.dox_a_class(LongParagraphInterface, {'line_length': 72})
        expected = """# `LongParagraphInterface(Protocol)`

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum.

"""
        assert observed == expected, f"expected\n{expected}\nbut observed\n{observed}"


if __name__ == '__main__':
    unittest.main()
