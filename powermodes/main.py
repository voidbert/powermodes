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
# @file main.py
# @package powermodes.main
# @brief Entry point to the program.
##


from os import getuid
import sys
from typing import Any, Union

from .arguments import Action, parse_arguments, validate_arguments, get_help_message, \
    get_version_string
from .config import load_config, validate, apply_mode
from .error import Error, ErrorType, handle_error, handle_error_append
from .plugin import Plugin, load_plugins

##
# @brief Returns an error if the user hasn't root priveleges.
##
def __assert_root() -> tuple[None, Union[Error, None]]:
    return (None,
         Error(ErrorType.ERROR, 'powermodes must be run as root!') if getuid() != 0 else None)

##
# @brief Formats the program's and plugins' versions.
# @details Auxiliary method for [main](@ref powermodes.main.main).
# @returns The formatted version message, along with possible warnings that may happen while
#          getting powermodes' version or loading plugins.
##
def __format_version() -> tuple[str, list[Error]]:
    errors: list[Error] = []
    version = handle_error_append(errors, get_version_string())
    plugins = handle_error_append(errors, load_plugins())

    message = ''

    if version is not None:
        message += f'\n{version}\n'

    if len(plugins) != 0:
        message += '\nVersions of installed plugins:\n'
        for plugin in plugins.values():
            message += f'{plugin.name} {plugin.version}\n'

    return (message, errors)

##
# @brief Loads a configuration file and plugins.
# @details Auxiliary method for [main](@ref powermodes.main.main).
# @param path Path to the configuration file.
# @returns A tuple containing a parsed configuration (or `None`) and the a dictionary associating
#          plugin names to loaded plugins (or `None`), along with errors / warnings that may have
#          happened.
##
def __load_config_plugins(path: str) -> \
    tuple[tuple[Union[dict[str, Any], None], Union[dict[str, Plugin], None]], list[Error]]:

    errors: list[Error] = []
    config = handle_error_append(errors, load_config(path))
    plugins = handle_error_append(errors, load_plugins())

    return ((config, plugins), errors)

##
# @brief The entry point to powermodes.
##
def main() -> None:
    parsed_args = handle_error(parse_arguments())
    args = handle_error(validate_arguments(parsed_args))

    match args.action:
        case Action.SHOW_HELP:
            print(get_help_message())

        case Action.SHOW_VERSION:
            print(handle_error(__format_version()))

        case _:
            handle_error(__assert_root())

            (config, plugins), errors = __load_config_plugins(args.config)
            handle_error((None, errors)) # Print errors
            if config is None or plugins is None:
                sys.exit(1)

            success, errors = validate(config, plugins)
            handle_error((True if success else None, errors))

            match args.action:
                case Action.VALIDATE:
                    sys.exit(0)

                case Action.APPLY_MODE:
                    success, errors = apply_mode(args.mode, config, plugins)
                    handle_error((True if success else None, errors))

                case _:
                    raise NotImplementedError('I\'m not that fast of a developer!')
