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
from enum import Enum
from importlib.metadata import version
from sys import argv

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
# @details Examples include showing the program's version, interactively configuring a plugin, ...
##
class Action(Enum):
    SHOW_HELP = 0    # @brief Show powermodes' help message
    SHOW_VERSION = 1 # @brief Show powermodes' version

    ##
    # @brief Creates an [Action](@ref powermodes.arguments.Action) from a command-line argument
    #        key.
    # @brief key Key from the return value of `parse_arguments`, when converted to a dictionary
    #            using built-in `vars`.
    # @returns An [Action](@ref powermodes.arguments.Action). Returns `None` if @p key isn't
    #          recognized.
    ##
    @staticmethod
    def from_key(key: str) -> Action | NoneType:
        match key:
            case 'help': return Action.SHOW_HELP
            case 'version': return Action.SHOW_VERSION

    ##
    # @brief Gets the command-line options associated with the current action.
    # @details
    # #### Example
    # ```
    # >>> Action.SHOW_HELP.to_key()
    # ['-h', '--help']
    # ```
    ##
    def to_key(self) -> list[str]:
        match self:
            case Action.SHOW_HELP: return [ '-h', '--help' ]
            case Action.SHOW_VERSION: return [ '-v', '--version' ]

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

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')

    return parser

##
# @brief Parses command-line arguments.
# @details On parsing error, an [ArgumentException](@ref powermodes.arguments.ArgumentException) is
#          raised.
# @param args Command-line arguments to parse. Defaults to `sys.argv`.
#             Note that, when providing a custom list of arguments, the first one will be excluded
#             (considered to be the name of the program).
# @returns A `argparse.Namespace`.
##
def parse_arguments(args: list[str] = argv) -> Namespace:
    parser = __create_parser()
    return parser.parse_args(args[1:])

##
# @brief Gets the list of [Action](@ref powermodes.arguments.Action)s from parsed command-line
#        arguments.
# @param parsed_args Parsed (from [parse_argument](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns Lists of actions the user wants to perform.
##
def __get_actions(parsed_args: Namespace) -> list[Action]:
    args_dict = vars(parsed_args)
    actions = []

    for key, value in args_dict.items():
        action: Action = Action.from_key(key)
        if action is not None and value == True:
            actions.append(action)

    if len(actions) == 0:
        actions = [ Action.SHOW_HELP ]

    return actions

##
# @brief Gets the [Action](@ref powermodes.arguments.Action) from parsed command-line arguments.
# @details Raises an [ArgumentException](@ref powermodes.arguments.ArgumentException) if the user
#          specifies multiple actions.
# @param parsed_args Parsed (from [parse_argument](@ref powermodes.arguments.parse_arguments))
#                    command-line arguments.
# @returns The [Action](@ref powermodes.arguments.Action) the user want to perform.
##
def get_action(parsed_args: Namespace) -> Action:
    actions = __get_actions(parsed_args)
    if len(actions) == 1:
        return actions[0]
    else:
        # Used for error message formatting. Works like Haskell's Data.List.intercalate.
        def intercalate(strings: list[str], separator: str):
            res = ''
            for s in strings:
                res += s + separator
            return res[: - len(separator)]

        options = list(map(Action.to_key, actions))
        options_strings = map(lambda opts: intercalate(opts, ' / '), options)
        raise ArgumentException('Multiple actions specified in command-line arguments:\n' + \
                                intercalate(options_strings, '\n'))

##
# @brief Gets the help message to be shown to the user.
##
def get_help_message() -> str:
    parser = __create_parser()
    return parser.format_help()

##
# @brief Gets the version of powermodes.
# @details May throw a [VersionException](@ref powermodes.arguments.VersionException).
##
def get_version_string() -> str:
    try:
        return 'powermodes ' + version('powermodes')
    except:
        raise VersionException('Failed to get powermodes\' version')

