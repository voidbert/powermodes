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

##
# @file arguments.py
# @package powermodes.arguments
# @brief Parsing and verification of command-line arguments.
##

from __future__ import annotations
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import version, PackageNotFoundError
from sys import argv
from textwrap import dedent
from typing import Union, NoReturn

from .error import Error, ErrorType, handle_error_append

##
# @brief The type of exception raised by
#        [_CustomParser](@ref powermodes.arguments._CustomParser).
##
class _ArgumentError(Exception):
    pass

##
# @brief Custom `argparse.ArgumentParser` implementation to avoid printing errors.
##
class _CustomParser(ArgumentParser):
    def error(self: _CustomParser, message: str) -> NoReturn:
        raise _ArgumentError(message)

##
# @brief Action triggered by command-line arguments.
# @details Examples include showing the program's version, interactively choosing a power mode, ...
##
class Action(Enum):
    SHOW_HELP = 0    ##< @brief Show powermodes' help message.
    SHOW_VERSION = 1 ##< @brief Show powermodes' version.

    INTERACTIVE = 2  ##< @brief Interactively choose mode from config file.
    APPLY_MODE = 3   ##< @brief Apply power mode from config file.
    VALIDATE = 4     ##< @brief Validate configuration file.

    ##
    # @brief Gets the command-line options associated with an action.
    # @details Used for the error message when multiple actions are specified.
    # #### Example
    # ```
    # >>> Action.SHOW_HELP.to_key()
    # ['-h', '--help']
    # ```
    ##
    def to_key(self) -> list[str]:
        match self:
            case Action.SHOW_HELP:    return [ '-h', '--help' ]
            case Action.SHOW_VERSION: return [       '--version' ]
            case Action.INTERACTIVE:  return [ '-i', '--interactive' ]
            case Action.APPLY_MODE:   return [ '-m', '--mode' ]
            case Action.VALIDATE:     return [ '-v', '--validate' ]

##
# @brief Data in parsed and verified command-line arguments.
##
@dataclass
class Arguments:
    action: Action = Action.SHOW_HELP ##< @brief Action to be executed.
    config: Union[str, None] = None  ##< @brief Path to configuration file.

    ##
    # @brief Power mode to be applied (for
    #        [Action.APPLY_MODE](@ref powermodes.arguments.Action.APPLY_MODE)).
    ##
    mode: Union[str, None] = None

##
# @brief Creates an `ArgumentParser` for powermode's arguments.
# @returns An `ArgumentParser`.
##
def __create_parser() -> ArgumentParser:
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

##
# @brief Parses command-line arguments.
# @param args Command-line arguments to parse. Defaults to `sys.argv`.
#             Note that, when providing a custom list of arguments, the first one will be excluded
#             (considered to be the name of the program).
# @returns
# A `argparse.Namespace` that contains the following variables:
#
#  - `action: Union[list[Action], None]` - List of [Action](@ref powermodes.arguments.Action)s the
#                                          user wants to perform (excluding setting a mode).
#  - `config: Union[str, None]`          - Path to configuration file.
#  - `mode: Union[str, None]`            - Mode to be applied.
#
#  In case of error, the `Namespace` will be `None`, and the [Error](@ref powermodes.error.Error)
#  will be non-`None`.
##
def parse_arguments(args: Union[list[str], None] = None) -> \
    tuple[Union[Namespace, None], Union[Error, None]]:

    try:
        if args is None:
            args = argv

        parser = __create_parser()
        return (parser.parse_args(args[1:]), None)
    except _ArgumentError as ex:
        return (None, Error(ErrorType.ERROR, str(ex)))

##
# @brief Gets the [Action](@ref powermodes.arguments.Action) the user wants to perform, from parsed
#        command-line arguments.
# @param parsed_args Parsed (from [parse_arguments](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns The [Action](@ref powermodes.arguments.Action) the user wants to perform (or `None`, if
#          multiple actions are specified), along with a possible error / warning.
##
def __get_action(parsed_args: Namespace) -> tuple[Union[Action, None], Union[Error, None]]:
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

##
# @brief Gets the path to the configuration file from parsed command-line arguments.
# @param action Result from [__get_action](@ref powermodes.arguments.__get_action).
# @param parsed_args Parsed (from [parse_arguments](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns The path to the configuration file, if specified. Errors and warnings can be returned.
##
def __get_config(action: Union[Action, None], parsed_args: Namespace) -> \
    tuple[Union[Namespace, None], list[Error]]:

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

##
# @brief Gets the power mode the user wants to apply from parsed command-line arguments.
# @param parsed_args Parsed (from [parse_arguments](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns The power mode to be applied, if specified. A warning may accompany it.
##
def __get_mode(parsed_args: Namespace) -> tuple[Union[str, None], Union[Error, None]]:
    if parsed_args.mode is None:
        return (None, None)
    elif len(parsed_args.mode) == 1:
        return (parsed_args.mode[0], None)
    else:
        error = Error(ErrorType.WARNING, 'Multiple power modes specified. ' \
                      'Choosing the last one.')
        return (parsed_args.mode[-1], error)

##
# @brief Validates parsed arguments, generating an organized data structure with them.
# @param parsed_args Parsed (from [parse_arguments](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns An object containing argument information.
##
def validate_arguments(parsed_args: Namespace) -> tuple[Union[Arguments, None], list[Error]]:
    errors: list[Error] = []
    action = handle_error_append(errors, __get_action(parsed_args))
    config = handle_error_append(errors, __get_config(action, parsed_args))
    mode   = handle_error_append(errors, __get_mode(parsed_args))

    if action is None:
        return (None, errors)
    else:
        return (Arguments(action, config, mode), errors)

##
# @brief Gets the help message to be shown to the user.
# @returns A string of the help message.
##
def get_help_message() -> str:
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

##
# @brief Gets the version of powermodes.
# @returns A string of powermodes' version. If an error happens, the string will be `None` and the
#          error will be returned.
##
def get_version_string() -> tuple[Union[str, None], Union[Error, None]]:
    try:
        return ('powermodes ' + version('powermodes'), None)
    except PackageNotFoundError:
        return (None, Error(ErrorType.WARNING, 'Failed to get powermodes\' version.'))
