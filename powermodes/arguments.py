# -------------------------------------------- LICENSE --------------------------------------------
#
# Copyright 2023 Humberto Gomes
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# -------------------------------------------------------------------------------------------------

"""
powermodes.arguments
====================

Parsing and validation of command-line arguments.
"""

from __future__ import annotations
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import version, PackageNotFoundError
from sys import argv
from textwrap import dedent
from typing import NoReturn, Optional

from .error import Error, ErrorType, handle_error_append

class _ArgumentError(Exception):
    """The type of exception raised by :class:`_CustomParser`."""

class _CustomParser(ArgumentParser):
    """Custom ``argparse.ArgumentParser`` to avoid printing errors before
    :func:`~powermodes.error.handle_error` is called.
    """
    def error(self: _CustomParser, message: str) -> NoReturn:
        """Function overridden not to print errors. An :class:`_ArgumentError` is raised
        instead.
        """
        raise _ArgumentError(message)

class Action(Enum):
    """
    The action the user wants to perform, specified in the command-line arguments.
    """

    SHOW_HELP = 0
    """Show powermodes' help message."""

    SHOW_VERSION = 1
    """Show the version of powermodes and of the installed plugins"""

    INTERACTIVE = 2
    """Interactively choose what powermode from the configuration file to apply."""
    APPLY_MODE = 3
    """Apply powermode specified in the command-line arguments."""

    VALIDATE = 4
    """Validate configuration file."""

    def to_key(self) -> list[str]:
        """Get the command-line arguments associatied with an action. This is used for more
        understandable error messages.

        :return: The list of arguments associated with the action.

        Example:

            >>> Action.SHOW_HELP.to_key
            ['-h', '--help']
        """

        match self:
            case Action.SHOW_HELP:    return [ '-h', '--help' ]
            case Action.SHOW_VERSION: return [       '--version' ]
            case Action.INTERACTIVE:  return [ '-i', '--interactive' ]
            case Action.APPLY_MODE:   return [ '-m', '--mode' ]
            case Action.VALIDATE:     return [ '-v', '--validate' ]

@dataclass
class Arguments:
    """Parsed and validated command-line arguments, whose data has been carefully placed in this
    dataclass. See :func:`validate_arguments`.
    """

    action: Action
    """Action to be performed."""

    config: Optional[str]
    """Path to the configuration file, if specified."""

    mode: Optional[str]
    """Powermode to be applied for :attr:`Action.APPLY_MODE`."""

def __create_parser() -> ArgumentParser:
    """Creates an ``ArgumentParser`` for parsing powermodes' arguments."""

    parser = _CustomParser(prog='powermodes',
                           description='Linux power consumption manager',
                           add_help=False,
                           allow_abbrev=False
                          )

    parser.add_argument('-h', '--help', dest='actions', action='append_const',
        const=Action.SHOW_HELP)
    parser.add_argument('--version', dest='actions', action='append_const',
        const=Action.SHOW_VERSION)
    parser.add_argument('-i', '--interactive', dest='actions', action='append_const',
        const=Action.INTERACTIVE)
    parser.add_argument('-v', '--validate', dest='actions', action='append_const',
        const=Action.VALIDATE)

    parser.add_argument('-c', '--config', action='append')
    parser.add_argument('-m', '--mode', action='append')

    return parser

def parse_arguments(args: Optional[list[str]] = None) -> \
    tuple[Optional[Namespace], Optional[Error]]:
    """Parses command-line arguments.

    :param args: Command-line arguments to parse. Defaults to ``sys.argv``. Note that, when
                 providing a list of custom arguments, the first one will be ignored (name of the
                 program).

    :return: An ``argparse.Namespace`` with the following variables:
             - ``action: Optional[list[Action]]`` - List of actions the user wants to perform
                                                    (includes repetition of actions and excludes
                                                    :attr:`Action.APPLY_MODE`).
             - ``config: Optional[str]`` - path to configuration file, if specified.
             - ``mode: Optional[str]`` - powermode to apply, if specified.

            In case of parsing error, :data:`None` will be returned with an error.
    """

    try:
        if args is None:
            args = argv

        parser = __create_parser()
        return (parser.parse_args(args[1:]), None)
    except _ArgumentError as ex:
        return (None, Error(ErrorType.ERROR, str(ex)))

def __get_action(parsed_args: Namespace) -> tuple[Optional[Action], Optional[Error]]:
    """Gets the action the user wants to perform, from the command-line arguments they specified.

    :param parsed_args: Parsed command-line arguments (see :func:`parse_arguments`).
    :return: The action the user wants to perform (with a possible warning, in case the user
             included its command-line option multiple times), or `None` with an error, if multiple
             distinct actions were specified.
    """

    if parsed_args.mode is not None:
        if parsed_args.actions is None:
            parsed_args.actions = [ Action.APPLY_MODE ]
        else:
            parsed_args.actions.append(Action.APPLY_MODE)

    if parsed_args.actions is None:
        return (Action.SHOW_HELP, None)

    match len(parsed_args.actions):
        case 1:
            return (parsed_args.actions[0], None)
        case _:
            unique_actions = list(set(parsed_args.actions))

            # Different warning if the user specifies the same action more than once.
            if len(unique_actions) == 1:
                option_string = ' / '.join(unique_actions[0].to_key())
                return (unique_actions[0], \
                        Error(ErrorType.WARNING, f'Multiple instances of {option_string} option.'))

            # Error if multiple actions are specified
            options = map(Action.to_key, unique_actions)
            options_strings = map(' / '.join, options)
            options_strings_lines = '\n'.join(options_strings)
            return (None, Error(ErrorType.ERROR, \
                'Multiple actions specified in command-line arguments:\n' + options_strings_lines))

def __get_config(action: Optional[Action], parsed_args: Namespace) -> \
    tuple[Optional[Namespace], list[Error]]:
    """Gets the configuration file (``-c`` / ``--config``) from ``parsed_args`` (if specified).

    :param action: Target action from the parsed arguments (see :func:`__get_action`).
    :param parsed_args: Parsed command-line arguments (see :func:`parse_arguments`).

    :return: If a configuration file is specified, its file path; otherwise, :data:`None`. Possible
             returned errors include an error for no configuration file specified for ``action``, a
             warning for an unnecessary config specified for ``action``, or a warning for multiple
             specified configuration files.
    """

    errors = []
    config = None

    if not parsed_args.config:
        if action not in [ None, Action.SHOW_HELP, Action.SHOW_VERSION ]:
            errors.append(Error(ErrorType.ERROR, 'No config file specified.'))
    else:
        match len(parsed_args.config):
            case 1:
                config = parsed_args.config[0]
            case _:
                errors.append(Error(ErrorType.WARNING, 'Multiple config files specified. ' \
                    'Choosing the last one.'))
                config = parsed_args.config[-1]

    if config is not None and action in [ Action.SHOW_HELP, Action.SHOW_VERSION ]:
        errors.append(Error(ErrorType.WARNING, 'Unnecessarily specified config file.'))

    return (config, errors)

def __get_mode(parsed_args: Namespace) -> tuple[Optional[str], Optional[Error]]:
    """Gets the powermode (``-m`` / ``--mode``) specified in ``parsed_args``.

    :param parsed_args: Parsed command-line arguments (see :func:`parse_arguments`).
    :return: If a powermode was specified in ``parsed_args``, that powermode (along with a
             possible warning, if multiple powermodes were specified). Otherwise :data:`None` is
             returned along with no errors.
    """

    if parsed_args.mode is None:
        return (None, None)
    elif len(parsed_args.mode) == 1:
        return (parsed_args.mode[0], None)
    else:
        error = Error(ErrorType.WARNING, 'Multiple power modes specified. ' \
                      'Choosing the last one.')
        return (parsed_args.mode[-1], error)

def validate_arguments(parsed_args: Namespace) -> tuple[Optional[Arguments], list[Error]]:
    """Validates parsed command-line arguments, creating an organized data structure containing
    them in the process.

    :param parsed_args: Parsed command-line arguments (see :func:`parse_arguments`).
    :return: Organized command-line argument information, along with possible errors and warnings.
    """

    errors: list[Error] = []
    action = handle_error_append(errors, __get_action(parsed_args))
    config = handle_error_append(errors, __get_config(action, parsed_args))
    mode   = handle_error_append(errors, __get_mode(parsed_args))

    if action is None:
        return (None, errors)
    else:
        return (Arguments(action, config, mode), errors)

def get_help_message() -> str:
    """Gets the help message to be shown to the user.

    :return: A custom help message string with examples.
    """

    # Custom help message, due to lack of control from argparse
    return dedent('''
                     usage: powermodes [options]

                     options:
                       -h, --help                 show this help message
                       --version                  show powermode\'s version

                       -c CONFIG, --config CONFIG use CONFIG file

                       -i, --interactive          interactively choose power mode
                       -v, --validate             validate CONFIG file
                       -m MODE, --mode MODE       apply power MODE from CONFIG

                     examples:

                     Interactive mode:       # powermodes -ic config.toml
                     Validate configuration: # powermodes -vc config.toml
                     Apply power mode:       # powermodes -c config.toml -m performance
                  '''[1:-1])

def get_version_string() -> tuple[Optional[str], Optional[Error]]:
    """Gets the version string of powermodes, for example, ``'powermodes 1.0'``.

    :return: The version of powermodes along with an empty error list, or :data:`None` and an
             error.
    """

    try:
        return ('powermodes ' + version('powermodes'), None)
    except PackageNotFoundError:
        return (None, Error(ErrorType.WARNING, 'Failed to get powermodes\' version.'))
