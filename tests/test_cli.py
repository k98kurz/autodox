from __future__ import annotations
from autodox import cli, functions
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from logging import CRITICAL, DEBUG, getLogger, Handler, INFO
from types import ModuleType
from unittest.mock import patch
import unittest


class TestCli(unittest.TestCase):
    def tearDown(self) -> None:
        logger = getLogger('autodox')
        logger.setLevel(CRITICAL + 1)
        logger.propagate = True
        for handler in list(logger.handlers):
            if getattr(handler, '_autodox_cli_handler', False):
                logger.removeHandler(handler)
        return super().tearDown()

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.invoke_cli(['autodox', *argv])
        return rc, out.getvalue(), err.getvalue()

    def test_defaults_return_zero_with_empty_settings(self):
        fake = ModuleType('fakemod')
        captured = {}

        def fake_dox(module, options=None):
            functions._debug(1, 'trace-one')
            captured['module'] = module
            captured['options'] = options
            return 'DOC'

        with patch.object(cli, 'import_module', return_value=fake), \
                patch.object(functions, 'dox_a_module', fake_dox):
            rc, out, err = self._run(['fakemod'])

        assert rc == 0, f'expected 0, got {rc}'
        assert out == 'DOC\n', f'expected DOC output, got {out!r}'
        assert err == '', f'expected no debug output, got {err!r}'
        assert captured['module'] is fake
        assert captured['options'] == {}, captured['options']

    def test_debug_output_is_not_propagated_to_root(self):
        fake = ModuleType('fakemod')
        captured = []

        def fake_dox(module, options=None):
            functions._debug(1, 'unique-marker')
            return 'DOC'

        class RecordingHandler(Handler):
            def emit(self, record):
                captured.append(record.getMessage())

        root = getLogger()
        root_handler = RecordingHandler()
        root.addHandler(root_handler)
        try:
            with patch.object(cli, 'import_module', return_value=fake), \
                    patch.object(functions, 'dox_a_module', fake_dox):
                rc, out, err = self._run(['fakemod', '--debug'])
        finally:
            root.removeHandler(root_handler)

        assert rc == 0, f'expected 0, got {rc}'
        assert out == 'DOC\n', f'expected only DOC, got {out!r}'
        assert err.count('unique-marker') == 1, err
        assert captured == [], captured

    def test_all_options_map_to_settings_and_debug(self):
        fake = ModuleType('fakemod')
        captured = {}

        def fake_dox(module, options=None):
            functions._debug(1, 'depth-one')
            functions._debug(2, 'depth-two')
            functions._debug(3, 'depth-three')
            captured['options'] = options
            return ''

        argv = [
            'fakemod',
            '--exclude-name=a,b', '--exclude-name=c',
            '--exclude-type=int,str',
            '--header-level=2',
            '--package=foo',
            '--function-format=paragraph',
            '--method-format=list',
            '--value-format=header',
            '--line-length=100',
            '--include-private',
            '--include-dunder',
            '--include-submodules',
            '--document-submodules',
            '--debug', '--debug',
        ]

        with patch.object(cli, 'import_module', return_value=fake) as m, \
                patch.object(functions, 'dox_a_module', fake_dox):
            rc, out, err = self._run(argv)

        assert rc == 0, f'expected 0, got {rc}'
        assert m.call_args.args == ('fakemod', 'foo'), m.call_args
        assert captured['options'] == {
            'exclude_names': ['a', 'b', 'c'],
            'exclude_types': ['int', 'str'],
            'header_level': 2,
            'function_format': 'paragraph',
            'method_format': 'list',
            'value_format': 'header',
            'line_length': 100,
            'include_private': True,
            'include_dunder': True,
            'include_submodules': True,
            'document_submodules': True,
        }, captured['options']
        assert 'depth-one' in err, err
        assert 'depth-two' in err, err
        assert 'depth-three' not in err, err
        assert 'depth-one' not in out, out

    def test_debug_levels_show_progressively_more_tiers(self):
        fake = ModuleType('fakemod')
        expected = {
            1: {'depth-one'},
            2: {'depth-one', 'depth-two'},
            3: {'depth-one', 'depth-two', 'depth-three'},
        }

        def fake_dox(module, options=None):
            functions._debug(1, 'depth-one')
            functions._debug(2, 'depth-two')
            functions._debug(3, 'depth-three')
            return 'DOC'

        for debug_count, visible in expected.items():
            with self.subTest(debug_count=debug_count), \
                    patch.object(cli, 'import_module', return_value=fake), \
                    patch.object(functions, 'dox_a_module', fake_dox):
                rc, out, err = self._run(
                    ['fakemod', *(['--debug'] * debug_count)]
                )

            assert rc == 0, f'expected 0, got {rc}'
            assert out == 'DOC\n', f'expected only DOC, got {out!r}'
            for tier in ('depth-one', 'depth-two', 'depth-three'):
                if tier in visible:
                    assert tier in err, (debug_count, tier, err)
                else:
                    assert tier not in err, (debug_count, tier, err)

    def test_debug_shim_preserves_print_spacing(self):
        with self.assertLogs('autodox', level=INFO) as logs:
            functions._debug(1, 'value:', 42, ['a', 'b'])

        assert logs.output == [
            "INFO:autodox.functions:value: 42 ['a', 'b']"
        ], logs.output

    def test_debug_shim_filters_depths_by_logging_level(self):
        with self.assertLogs('autodox', level=DEBUG) as logs:
            functions._debug(1, 'depth-one')
            functions._debug(2, 'depth-two')
            functions._debug(3, 'depth-three')

        assert logs.output == [
            'INFO:autodox.functions:depth-one',
            'DEBUG:autodox.functions:depth-two',
        ], logs.output

        with self.assertLogs('autodox', level=functions.TRACE) as logs:
            functions._debug(1, 'depth-one')
            functions._debug(2, 'depth-two')
            functions._debug(3, 'depth-three')

        assert logs.output == [
            'INFO:autodox.functions:depth-one',
            'DEBUG:autodox.functions:depth-two',
            'TRACE:autodox.functions:depth-three',
        ], logs.output

    def test_import_without_package_uses_single_argument(self):
        fake = ModuleType('fakemod')

        with patch.object(cli, 'import_module', return_value=fake) as m, \
                patch.object(functions, 'dox_a_module', return_value=''):
            rc, out, err = self._run(['fakemod'])

        assert rc == 0, f'expected 0, got {rc}'
        assert m.call_args.args == ('fakemod',), m.call_args

    def test_module_not_found_returns_one(self):
        def boom(name, package=None):
            raise ModuleNotFoundError(f"No module named '{name}'")

        with patch.object(cli, 'import_module', side_effect=boom):
            rc, out, err = self._run(['nope'])

        assert rc == 1, f'expected 1, got {rc}'
        assert 'ModuleNotFoundError' in err, err

    def test_import_error_returns_one(self):
        def boom(name, package=None):
            raise ImportError('bad import')

        with patch.object(cli, 'import_module', side_effect=boom):
            rc, out, err = self._run(['fakemod'])

        assert rc == 1, f'expected 1, got {rc}'
        assert 'ImportError: bad import' in err, err

    def test_empty_module_returns_one(self):
        def boom(name, package=None):
            raise ValueError('Empty module name')

        with patch.object(cli, 'import_module', side_effect=boom):
            rc, out, err = self._run([''])

        assert rc == 1, f'expected 1, got {rc}'
        assert 'ValueError: Empty module name' in err, err

    def test_value_error_from_module_propagates(self):
        def boom(name, package=None):
            raise ValueError('bug in module body')

        with patch.object(cli, 'import_module', side_effect=boom), \
                self.assertRaises(ValueError):
            self._run(['fakemod'])

    def test_main_cli_reads_sys_argv(self):
        fake = ModuleType('fakemod')

        with patch('sys.argv', ['autodox', 'fakemod']), \
                patch.object(cli, 'import_module', return_value=fake), \
                patch.object(functions, 'dox_a_module', return_value=''), \
                redirect_stdout(StringIO()):
            rc = cli.main_cli()

        assert rc == 0, f'expected 0, got {rc}'

    def test_help_exits_zero(self):
        out = StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stdout(out):
            cli.invoke_cli(['autodox', '--help'])
        assert cm.exception.code == 0, cm.exception.code
        assert 'usage' in out.getvalue().lower(), out.getvalue()

    def test_unknown_option_exits_two(self):
        with self.assertRaises(SystemExit) as cm, redirect_stderr(StringIO()):
            cli.invoke_cli(['autodox', '--nope'])
        assert cm.exception.code == 2, cm.exception.code

    def test_missing_module_exits_two(self):
        with self.assertRaises(SystemExit) as cm, redirect_stderr(StringIO()):
            cli.invoke_cli(['autodox'])
        assert cm.exception.code == 2, cm.exception.code


if __name__ == '__main__':
    unittest.main()
