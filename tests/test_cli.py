from __future__ import annotations
from autodox import cli, functions
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import ModuleType
from unittest.mock import patch
import unittest


class TestCli(unittest.TestCase):
    def tearDown(self) -> None:
        functions._debug_level = 0
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
            captured['module'] = module
            captured['options'] = options
            return 'DOC'

        with patch.object(cli, 'import_module', return_value=fake), \
                patch.object(functions, 'dox_a_module', fake_dox):
            rc, out, err = self._run(['fakemod'])

        assert rc == 0, f'expected 0, got {rc}'
        assert functions._debug_level == 0, functions._debug_level
        assert out == 'DOC\n', f'expected DOC output, got {out!r}'
        assert captured['module'] is fake
        assert captured['options'] == {}, captured['options']

    def test_all_options_map_to_settings_and_debug(self):
        fake = ModuleType('fakemod')
        captured = {}

        def fake_dox(module, options=None):
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
        assert functions._debug_level == 2, functions._debug_level

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
