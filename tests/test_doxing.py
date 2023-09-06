from context import functions
import unittest


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


if __name__ == '__main__':
    unittest.main()
