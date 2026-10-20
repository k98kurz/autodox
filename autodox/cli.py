from __future__ import annotations
from . import functions
from .version import version
from argparse import ArgumentParser, Namespace
from importlib import import_module
from logging import Formatter, getLogger, StreamHandler
from os.path import basename
import sys


def _build_parser(prog: str) -> ArgumentParser:
    """Builds the argparse parser for the autodox CLI."""
    parser = ArgumentParser(
        prog=prog,
        description=(
            'Generate markdown documentation from a module using its code '
            'annotations, types, and docstrings.'
        )
    )
    parser.add_argument(
        'module',
        help='dotted module path to document (e.g. `package.module`)'
    )
    parser.add_argument(
        '--exclude-name', action='extend', default=None,
        metavar='NAME[,NAME...]',
        type=lambda value: [v for v in value.split(',') if v],
        help='exclude the given name (or comma-separated names); repeatable'
    )
    parser.add_argument(
        '--exclude-type', action='extend', default=None,
        metavar='TYPE[,TYPE...]',
        type=lambda value: [v for v in value.split(',') if v],
        help='exclude the given type (or comma-separated types); repeatable'
    )
    parser.add_argument(
        '--header-level', type=int, metavar='INT',
        help='number of hashtags to prepend to headers'
    )
    parser.add_argument(
        '--package', metavar='PACKAGE',
        help='name of package if not using the . notation'
    )
    parser.add_argument(
        '--function-format', choices=('header', 'paragraph', 'list'),
        help='format used for functions'
    )
    parser.add_argument(
        '--method-format', choices=('header', 'paragraph', 'list'),
        help='format used for methods'
    )
    parser.add_argument(
        '--value-format', choices=('header', 'paragraph', 'list'),
        help='format used for values'
    )
    parser.add_argument(
        '--line-length', type=int, metavar='INT',
        help='number of chars per line in paragraphs'
    )
    parser.add_argument(
        '--include-private', action='store_true',
        help='includes things prefaced with "_"'
    )
    parser.add_argument(
        '--include-dunder', action='store_true',
        help='includes things prefaced with "__"'
    )
    parser.add_argument(
        '--include-submodules', action='store_true',
        help='includes submodules'
    )
    parser.add_argument(
        '--document-submodules', action='store_true',
        help='runs module documentation for submodules'
    )
    parser.add_argument(
        '--no-backtick-names', dest='backtick_names', action='store_false',
        default=None,
        help=(
            'do not wrap names (annotations, values, classes, modules, and '
            'aliases) in backticks'
        )
    )
    parser.add_argument(
        '--no-backtick-types', dest='backtick_types', action='store_false',
        default=None,
        help='do not wrap annotation and value types in backticks'
    )
    parser.add_argument(
        '--no-backtick-signatures', dest='backtick_signatures',
        action='store_false', default=None,
        help='do not wrap function and method signatures in backticks'
    )
    parser.add_argument(
        '--no-backticks', dest='backticks', action='store_false',
        default=None,
        help='do not wrap anything in backticks'
    )
    parser.add_argument(
        '--no-clean-type-aliases', dest='clean_type_aliases',
        action='store_false', default=None,
        help='keep module qualifiers in type alias definitions'
    )
    parser.add_argument(
        '--debug', action='count', default=0,
        help=(
            'increases level of debug statements printed to stderr; starts at '
            '0 and increases once for each time this flag is passed; level 1 '
            'prints the trace for dox_{thing} calls; level 2 includes '
            'formatting functions; level 3 includes hooks functions'
        )
    )
    parser.add_argument(
        '-v', '--version', action='version', version=version(),
        help="show program's version number and exit"
    )
    return parser


def _settings_from(options: Namespace) -> dict:
    """Translates parsed CLI options into `dox_a_module` settings."""
    settings = {}
    if options.exclude_name:
        settings['exclude_names'] = options.exclude_name
    if options.exclude_type:
        settings['exclude_types'] = options.exclude_type
    if options.header_level is not None:
        settings['header_level'] = options.header_level
    if options.function_format is not None:
        settings['function_format'] = options.function_format
    if options.method_format is not None:
        settings['method_format'] = options.method_format
    if options.value_format is not None:
        settings['value_format'] = options.value_format
    if options.line_length is not None:
        settings['line_length'] = options.line_length
    if options.include_private:
        settings['include_private'] = True
    if options.include_dunder:
        settings['include_dunder'] = True
    if options.include_submodules:
        settings['include_submodules'] = True
    if options.document_submodules:
        settings['document_submodules'] = True
    if options.backtick_names is not None:
        settings['backtick_names'] = options.backtick_names
    if options.backtick_types is not None:
        settings['backtick_types'] = options.backtick_types
    if options.backtick_signatures is not None:
        settings['backtick_signatures'] = options.backtick_signatures
    if options.backticks is not None:
        settings['backticks'] = options.backticks
    if options.clean_type_aliases is not None:
        settings['clean_type_aliases'] = options.clean_type_aliases
    return settings


def _configure_logging(debug: int) -> tuple[StreamHandler | None, int, bool]:
    """Configures the package logger for a CLI invocation."""
    logger = getLogger('autodox')
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.setLevel(functions._logging_level_for(debug))
    handler = None
    if debug > 0:
        handler = StreamHandler(sys.stderr)
        handler.setFormatter(Formatter('%(message)s'))
        handler._autodox_cli_handler = True
        logger.addHandler(handler)
        logger.propagate = False
    return handler, previous_level, previous_propagate


def invoke_cli(args: list[str]) -> int:
    """Entry point for pip installed wrapper function to invoke via CLI."""
    prog = basename(args[0]) if args and args[0] else ''
    parser = _build_parser(prog or 'autodox')
    options = parser.parse_args(args[1:])
    handler, previous_level, previous_propagate = _configure_logging(
        options.debug
    )
    settings = _settings_from(options)

    try:
        if options.package:
            module = import_module(options.module, options.package)
        else:
            module = import_module(options.module)
        print(functions.dox_a_module(module, settings))
        return 0
    except ImportError as e:
        print(f'{type(e).__name__}: {str(e)}', file=sys.stderr)
        return 1
    except ValueError as e:
        if options.module:
            raise
        print(f'{type(e).__name__}: {str(e)}', file=sys.stderr)
        return 1
    finally:
        logger = getLogger('autodox')
        if handler is not None:
            logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


def main_cli() -> int:
    return invoke_cli(sys.argv)
