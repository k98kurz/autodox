from context import functions
from enum import Enum
import unittest


class TestHooks(unittest.TestCase):
    def tearDown(self) -> None:
        for event in functions.Event:
            functions.unset_handler(event)
        return super().tearDown()

    def test_functions_contains_handlers_dict_and_Event_enum(self):
        assert hasattr(functions, '_handlers')
        assert type(functions._handlers) is dict
        assert hasattr(functions, 'Event')
        assert issubclass(functions.Event, Enum)

    def test_functions_contains_handler_set_and_unset_functions(self):
        assert hasattr(functions, '_set_handler')
        assert callable(functions._set_handler)
        assert hasattr(functions, 'set_before_handler')
        assert callable(functions.set_before_handler)
        assert hasattr(functions, 'set_after_handler')
        assert callable(functions.set_after_handler)
        assert hasattr(functions, 'unset_handler')
        assert callable(functions.unset_handler)

    def test_AFTER_HEADER_event(self):
        before = functions._header('hello')
        assert before == '# hello\n\n'
        functions.set_after_handler(
            functions.Event.AFTER_HEADER,
            lambda doc: doc + 'world'
        )
        after = functions._header('hello')
        assert after == '# hello\n\nworld'

    def test_AFTER_PARAGRAPH_event(self):
        before = functions._paragraph('hello')
        assert before == 'hello\n\n'
        functions.set_after_handler(
            functions.Event.AFTER_PARAGRAPH,
            lambda doc: doc + 'world'
        )
        after = functions._paragraph('hello')
        assert after == 'hello\n\nworld'

    def test_AFTER_LIST_event(self):
        before = functions._list('hello')
        assert before == '- hello\n'
        functions.set_after_handler(
            functions.Event.AFTER_LIST,
            lambda doc: doc + 'world'
        )
        after = functions._list('hello')
        assert after == '- hello\nworld'

    def test_BEFORE_VALUE_event(self):
        signal = False
        def handle(*args):
            nonlocal signal
            signal = True
            return args
        _ = functions.dox_a_value(signal)
        assert not signal
        functions.set_before_handler(
            functions.Event.BEFORE_VALUE,
            handle
        )
        _ = functions.dox_a_value(signal)
        assert signal

    def test_AFTER_VALUE_event(self):
        val = 'some str'
        before = functions.dox_a_value(val)
        functions.set_after_handler(
            functions.Event.AFTER_VALUE,
            lambda doc: doc + 'AFTER'
        )
        after = functions.dox_a_value(val)
        assert after == before + 'AFTER'

    def test_BEFORE_FUNCTION_event(self):
        signal = False
        def handle(*args):
            nonlocal signal
            signal = True
            return args
        _ = functions.dox_a_function(handle)
        assert not signal
        functions.set_before_handler(
            functions.Event.BEFORE_FUNCTION,
            handle
        )
        _ = functions.dox_a_function(handle)
        assert signal

    def test_AFTER_FUNCTION_event(self):
        handler = lambda doc: doc + 'AFTER'
        before = functions.dox_a_function(handler)
        functions.set_after_handler(
            functions.Event.AFTER_FUNCTION,
            handler
        )
        after = functions.dox_a_function(handler)
        assert after == before + 'AFTER'

    def test_BEFORE_CLASS_event(self):
        signal = False
        def handle(*args):
            nonlocal signal
            signal = True
            return args
        _ = functions.dox_a_class(TestHooks)
        assert not signal
        functions.set_before_handler(
            functions.Event.BEFORE_CLASS,
            handle
        )
        _ = functions.dox_a_class(TestHooks)
        assert signal

    def test_AFTER_CLASS_event(self):
        before = functions.dox_a_class(TestHooks)
        functions.set_after_handler(
            functions.Event.AFTER_CLASS,
            lambda doc: doc + 'AFTER'
        )
        after = functions.dox_a_class(TestHooks)
        assert after == before + 'AFTER'

    def test_BEFORE_MODULE_event(self):
        signal = False
        def handle(*args):
            nonlocal signal
            signal = True
            return args
        _ = functions.dox_a_module(functions)
        assert not signal
        functions.set_before_handler(
            functions.Event.BEFORE_MODULE,
            handle
        )
        _ = functions.dox_a_module(functions)
        assert signal

    def test_AFTER_MODULE_event(self):
        before = functions.dox_a_module(functions)
        functions.set_after_handler(
            functions.Event.AFTER_MODULE,
            lambda doc: doc + 'AFTER'
        )
        after = functions.dox_a_module(functions)
        assert after == before + 'AFTER'

    def test_event_handler_chaining(self):
        val = 'some str'
        before = functions.dox_a_value(val)
        functions.set_after_handler(
            functions.Event.AFTER_VALUE,
            lambda doc: doc + 'AFTER1 '
        )
        functions.set_after_handler(
            functions.Event.AFTER_VALUE,
            lambda doc: doc + 'AFTER2'
        )
        after = functions.dox_a_value(val)
        assert after == before + 'AFTER1 AFTER2'
        functions.set_after_handler(
            functions.Event.AFTER_VALUE,
            lambda doc: doc + ' AFTER3'
        )
        after = functions.dox_a_value(val)
        assert after == before + 'AFTER1 AFTER2 AFTER3'


if __name__ == '__main__':
    unittest.main()
