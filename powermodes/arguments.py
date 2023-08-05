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

from argparse import ArgumentParser, Namespace
from enum import Enum
from importlib.metadata import version
from sys import argv
from textwrap import dedent

##
# @brief Type of exception raised when a error happens while parsing arguments.
##
class ArgumentException(Exception):
    pass

##
# @brief Exception that may be raised when getting powermodes' version.
##
class VersionException(Exception):
    pass

##
# @brief Custom `argparse.ArgumentParser` implementation to avoid printing errors.
##
class __CustomParser(ArgumentParser):
    def error(self, message):
        raise ArgumentException(message)

##
# @brief Action triggered by command-line arguments.
# @details Examples include showing the program's version, interactively choosing a power mode, ...
##
class Action(Enum):
    SHOW_HELP = 0    ##< @brief Show powermodes' help message
    SHOW_VERSION = 1 ##< @brief Show powermodes' version

    ##
    # @brief Gets the command-line options associated with the current action.
    # @details Used for the error message when multiple actions are specified.
    # #### Example
    # ```
    # >>> Action.SHOW_HELP.to_key()
    # ['-h', '--help']
    # ```
    ##
    def to_key(self) -> list[str]:
        match self:
            case Action.SHOW_HELP: return [ '-h', '--help' ]
            case Action.SHOW_VERSION: return [ '--version' ]

##
# @brief Creates an `ArgumentParser` for powermode's arguments.
# @returns An `ArgumentParser`.
##
def __create_parser() -> ArgumentParser:
    parser = __CustomParser(prog='powermodes',
                            description='Linux power consumption manager',
                            add_help=False,
                            allow_abbrev=False
                           )

    parser.add_argument('-h', '--help', dest='actions', action='append_const',
        const=Action.SHOW_HELP)
    parser.add_argument('--version', dest='actions', action='append_const',
        const=Action.SHOW_VERSION)

    return parser

##
# @brief Parses command-line arguments.
# @details On parsing error, an [ArgumentException](@ref powermodes.arguments.ArgumentException) is
#          raised.
# @param args Command-line arguments to parse. Defaults to `sys.argv`.
#             Note that, when providing a custom list of arguments, the first one will be excluded
#             (considered to be the name of the program).
# @returns A `argparse.Namespace` containing the following variables:
#           - `action: list[Action]` - List of [Action](@ref powermodes.arguments.Action)s the user
#                                      wants to perform.
##
def parse_arguments(args: list[str] = argv) -> Namespace:
    parser = __create_parser()
    return parser.parse_args(args[1:])

##
# @brief Gets the [Action](@ref powermodes.arguments.Action) the user wants to perform from parsed
#        command-line arguments.
# @details Raises an [ArgumentException](@ref powermodes.arguments.ArgumentException) if the user
#          specifies multiple actions.
# @param parsed_args Parsed (from [parse_arguments](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns The [Action](@ref powermodes.arguments.Action) the user wants to perform.
##
def get_action(parsed_args: Namespace) -> Action:
    if parsed_args.actions is None:
        return Action.SHOW_HELP

    match len(parsed_args.actions):
        case 1:
            return parsed_args.actions[0]
        case _:
            options = map(Action.to_key, parsed_args.actions)
            options_strings = map(lambda opts: ' / '.join(opts), options)
            raise ArgumentException('Multiple actions specified in command-line arguments:\n' + \
                                    '\n'.join(options_strings))

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
                  '''[1:-1])

##
# @brief Gets the version of powermodes.
# @details May throw a [VersionException](@ref powermodes.arguments.VersionException).
# @returns A string of powermodes' version.
##
def get_version_string() -> str:
    try:
        return 'powermodes ' + version('powermodes')
    except:
        raise VersionException('Failed to get powermodes\' version')

