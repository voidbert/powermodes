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


import sys
from typing import Any, Union

from .arguments import Action, parse_arguments, validate_arguments, get_help_message, \
    get_version_string
from .config import load_config, validate
from .error import Error, handle_error, handle_error_append
from .plugin import Plugin, load_plugins

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
        for plugin in plugins:
            message += f'{plugin.name} {plugin.version}\n'

    return (message, errors)

##
# @brief Loads a configuration file and plugins.
# @details Auxiliary method for [main](@ref powermodes.main.main).
# @param path Path to the configuration file.
# @returns A tuple containing a parsed configuration (or `None`) and the list of loaded plugins
#          (or `None`), along with errors / warnings that may have happened.
##
def __load_config_plugins(path: str) -> \
    tuple[tuple[Union[dict[str, Any], None], Union[list[Plugin], None]], list[Error]]:

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
            (config, plugins), errors = __load_config_plugins(args.config)
            handle_error((None, errors)) # Print errors
            if config is None or plugins is None:
                sys.exit(1)

            match args.action:
                case Action.VALIDATE:
                    if not handle_error(validate(config, plugins)):
                        sys.exit(1)

                case _:
                    raise NotImplementedError('I\'m not that fast of a developer!')
