from __future__ import annotations
from autodox import functions
from difflib import SequenceMatcher
from types import ModuleType, FunctionType, MethodType
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

    @classmethod
    async def some_async_class_method(cls, data: str) -> bool:
        """Example async class method."""
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
    """Returns each non-matching region between `str1` and `str2` using
        `difflib`, keyed by the offsets in each string and mapping to
        the two differing slices.
    """
    matcher = SequenceMatcher(None, str1, str2, autojunk=False)
    return {
        f"exp[{i1}:{i2}] obs[{j1}:{j2}]": [str1[i1:i2], str2[j1:j2]]
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    }


class TestDoxAFunction(unittest.TestCase):
    def test_annotations_with_defaults(self):
        def fn_with_defaults(arg1: int, arg2: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, arg2: str = 'okay') -> bool:`"
            " Does a thing,\nreturns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

        def fn_with_defaults(arg1: int, arg2: bytes = b'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, arg2: bytes = b'okay') -> bool:`"
            " Does a thing,\nreturns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_empty_str_default(self):
        def fn_with_defaults(arg1: int, arg2: str = '') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, arg2: str = '') -> bool:`"
            " Does a thing, returns\nsome stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_type_default(self):
        def fn_with_defaults(arg1: int, arg2: type = ExampleClass) -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, "
            "arg2: type = ExampleClass) -> bool:`"
            " Does a\nthing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_kwdefaults(self):
        def fn_with_defaults(arg1: int, /, *, arg2: str = 'okay') -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, /, *, "
            "arg2: str = 'okay') -> bool:`"
            " Does a thing,\nreturns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_type_kwdefault(self):
        def fn_with_defaults(
                arg1: int, /, *, arg2: type = ExampleClass
            ) -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, /, *, "
            "arg2: type = ExampleClass) -> bool:`"
            " Does a\nthing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_defaults_and_kwdefaults(self):
        def fn_with_defaults(
                arg1: int, arg2: bytes = b'not', /, *,
                arg3: str = 'okay'
            ) -> bool:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_defaults)
        expected = (
            "- `fn_with_defaults(arg1: int, arg2: bytes = b'not', /, *, "
            "arg3: str = 'okay') -> bool:`"
            "\nDoes a thing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_kwargs_and_defaults(self):
        class SqlQueryBuilder:
            """A query builder."""

            def order_by(
                    self, column: str = None, direction: str = 'desc',
                    **conditions: dict[str, str]
                ) -> SqlQueryBuilder:
                """Sets query order."""
                ...

        doc = functions.dox_a_function(SqlQueryBuilder.order_by)
        expected = (
            "- `order_by(column: str = None, direction: str = 'desc', "
            "**conditions: dict[str, str]) -> SqlQueryBuilder:`"
            "\nSets query order.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

        doc = functions.dox_a_function(
            SqlQueryBuilder.order_by, {'format': 'header'}
        )
        expected = (
            "# `order_by(column: str = None, direction: str = 'desc', "
            "**conditions: dict[str, str]) -> SqlQueryBuilder:`\n\n"
            "Sets query order.\n\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_varargs_and_defaults(self):
        def fn_with_varargs(arg1: int, arg2: str = 'x', *args: int) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_varargs)
        expected = (
            "- `fn_with_varargs(arg1: int, arg2: str = 'x', *args: int)"
            " -> None:` Does a\nthing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_varargs_kwargs_and_kwonly(self):
        def fn_with_varargs_kwargs_and_kwonly(
                arg1: int, *args: int, arg2: str = 'x', **kw: int
            ) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_varargs_kwargs_and_kwonly)
        expected = (
            "- `fn_with_varargs_kwargs_and_kwonly(arg1: int, *args: int, "
            "arg2: str = 'x', **kw: int) -> None:`"
            "\nDoes a thing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_positional_only(self):
        def fn_with_positional_only(arg1: int, /, arg2: str = 'x') -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_positional_only)
        expected = (
            "- `fn_with_positional_only(arg1: int, /, arg2: str = 'x')"
            " -> None:` Does a\nthing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_kwonly_without_default(self):
        def fn_with_kwonly(arg1: int, *, arg2: str) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_kwonly)
        expected = (
            "- `fn_with_kwonly(arg1: int, *, arg2: str) -> None:`"
            " Does a thing, returns some\nstuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_unannotated_params(self):
        def fn_with_unannotated(arg1, arg2: int = 1) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_unannotated)
        expected = (
            "- `fn_with_unannotated(arg1, arg2: int = 1) -> None:`"
            " Does a thing, returns some\nstuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_unannotated_variadic(self):
        def fn_with_unannotated_variadic(arg1, *args, **kwargs) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_unannotated_variadic)
        expected = (
            "- `fn_with_unannotated_variadic(arg1, *args, **kwargs)"
            " -> None:` Does a thing,\nreturns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_trailing_positional_only(self):
        def fn_with_trailing_positional_only(arg1: int, /) -> None:
            """Does a thing, returns some stuff."""
            ...

        doc = functions.dox_a_function(fn_with_trailing_positional_only)
        expected = (
            "- `fn_with_trailing_positional_only(arg1: int, /) -> None:`"
            " Does a thing,\nreturns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )

    def test_annotations_with_annotated_self(self):
        class WithAnnotatedSelf:
            """An example class."""

            def method(self: WithAnnotatedSelf, x: int) -> None:
                """Does a thing, returns some stuff."""
                ...

        doc = functions.dox_a_function(WithAnnotatedSelf.method)
        expected = (
            "- `method(x: int) -> None:` Does a thing, returns some stuff.\n"
        )

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}}"
        )


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

### `@classmethod async some_async_class_method(data: str) -> bool:`

Example async class method.

"""

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}} "
            f"diff {{{diff(expected, doc)}}}"
        )

    def test_with_private(self):
        doc = functions.dox_a_class(
            ExampleClass, options={'include_private': True}
        )
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

### `@classmethod async some_async_class_method(data: str) -> bool:`

Example async class method.

### `_private() -> None:`

Gets mangled by runtime.

"""

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}} "
            f"diff {{{diff(expected, doc)}}}"
        )

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

### `@classmethod async some_async_class_method(data: str) -> bool:`

Example async class method.

### `_private() -> None:`

Gets mangled by runtime.

"""

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}} "
            f"diff {{{diff(expected, doc)}}}"
        )

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

### `@classmethod async some_async_class_method(data: str) -> bool:`

Example async class method.

"""

        assert doc == expected, (
            f"expected {{\n{expected}}} but got {{\n{doc}}} "
            f"diff {{{diff(expected, doc)}}}"
        )


class TestDoxAProtocol(unittest.TestCase):
    def test_dox_a_protocol(self):
        # discovered that the Protocol is designed to prevent documenting
        # the init interface
        # https://github.com/python/cpython/issues/110788
        observed = functions.dox_a_class(ExampleInterface)
        expected = """# `ExampleInterface(Protocol)`

## Methods

### `@classmethod init(name: str = 'foobar') -> ExampleInterface:`

Should initialize.

### `get_some_str() -> str:`

Should return a str.

"""

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

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

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

        observed = functions.dox_a_class(
            LongParagraphInterface, {'line_length': 100}
        )
        expected = """# `LongParagraphInterface(Protocol)`

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.

"""

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

        observed = functions.dox_a_class(
            LongParagraphInterface, {'line_length': 72}
        )
        expected = """# `LongParagraphInterface(Protocol)`

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum.

"""

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )


class TestAliases(unittest.TestCase):
    def test_module_aliases_are_not_duplicated(self):
        class DependencyError(Exception):
            """Raised when a dependency cannot be resolved."""
            ...

        def resolve(name: str):
            """Resolve a dependency."""
            ...

        module = ModuleType('repro_mod')
        module.DependencyError = DependencyError
        module.UsageError = DependencyError
        module.resolve = resolve
        module.resolve_alias = resolve

        observed = functions.dox_a_module(module)
        expected = """# repro_mod

## Classes

### `DependencyError(Exception)`

Raised when a dependency cannot be resolved.

### `UsageError = DependencyError`

## Functions

### `resolve(name: str):`

Resolve a dependency.

### `resolve_alias = resolve`

"""

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed} "
            f"diff {{{diff(expected, observed)}}}"
        )

    def test_dox_alias_paragraph_format(self):
        observed = functions._dox_alias('AliasFn', 'resolve', 0, 'paragraph')
        expected = '`AliasFn = resolve`\n\n'

        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

    def test_imported_types_are_not_treated_as_aliases(self):
        module = ModuleType('types_mod')
        module.ModuleType = ModuleType
        module.FunctionType = FunctionType
        module.MethodType = MethodType

        observed = functions.dox_a_module(module)
        alias_lines = [
            line for line in observed.splitlines()
            if line.startswith('### `') and ' = ' in line
        ]

        assert alias_lines == [], observed

    def test_method_aliases_are_not_duplicated(self):
        class AliasedMethods:
            """A class with method aliases."""

            def foo(self) -> None:
                """Do foo."""
                ...

            bar = foo

            @classmethod
            def cm(cls) -> None:
                """Do cm."""
                ...

            cm_alias = cm

            @staticmethod
            def sm() -> None:
                """Do sm."""
                ...

            sm_alias = sm

        observed = functions.dox_a_class(AliasedMethods)

        assert observed.count('### `foo() -> None:`') == 1, observed
        assert '### `bar = foo`' in observed, observed
        assert observed.count('### `@classmethod cm() -> None:`') == 1, observed
        assert '### `cm_alias = cm`' in observed, observed
        assert observed.count('### `@staticmethod sm() -> None:`') == 1, observed
        assert '### `sm_alias = sm`' in observed, observed

    def test_method_alias_to_private_target(self):
        class C:
            """C."""

            def _foo(self) -> None:
                """private foo."""
                ...

            bar = _foo

        observed = functions.dox_a_class(C)
        expected = """# `C`

C.

## Methods

### `bar = _foo`

"""
        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

        observed = functions.dox_a_class(C, {'include_private': True})
        assert '### `bar = _foo`' in observed, observed
        assert '### `_foo() -> None:`' in observed, observed

    def test_method_alias_to_private_descriptor_target(self):
        class C:
            """C."""

            @classmethod
            def _cm(cls) -> None:
                """private cm."""
                ...

            cm_alias = _cm

            @staticmethod
            def _sm() -> None:
                """private sm."""
                ...

            sm_alias = _sm

        observed = functions.dox_a_class(C)
        expected = """# `C`

C.

## Methods

### `cm_alias = _cm`

### `sm_alias = _sm`

"""
        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )

    def test_method_alias_to_excluded_target(self):
        class C:
            """C."""

            def foo(self) -> None:
                """foo."""
                ...

            bar = foo

        observed = functions.dox_a_class(C, {'exclude_names': ['foo']})
        expected = """# `C`

C.

## Methods

### `bar = foo`

"""
        assert observed == expected, (
            f"expected\n{expected}\nbut observed\n{observed}"
        )


if __name__ == '__main__':
    unittest.main()
