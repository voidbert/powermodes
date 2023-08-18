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
powermodes.main
===============

Module that contains powermode's entry point, :func:`main`.
"""

from os import getuid
import sys
from typing import Optional

from .arguments import Action, parse_arguments, validate_arguments, get_help_message, \
    get_version_string
from .config import ValidatedConfig, load_config, validate, apply_mode
from .error import Error, ErrorType, handle_error, handle_error_append
from .input import choose_option
from .plugin import LoadedPlugins,  load_plugins

def __assert_root() -> tuple[None, Optional[Error]]:
    """Checks if the user running powermodes has root priveleges. This is a hard requirement for a
    majority of plugins.

    :return: ``None``, along with a possible error, if the current user isn't root.
    """

    return (None,
        Error(ErrorType.ERROR, 'powermodes must be run as root!') if getuid() != 0 else None)

def __format_version() -> tuple[str, list[Error]]:
    """Formats a string with the version of both powermodes and the installed plugins. Parts of
    this message may be omitted if an error occurs while getting either powermodes' or one of the
    plugins' version.

    This function is responsible for loading all installed plugins, to later get their versions.

    :return: The formatted message string, along with possible warnings from failing to get
             powermodes' version, or from loading plugins.
    """

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

def __load_config_plugins(path: str) -> \
    tuple[Optional[tuple[ValidatedConfig, LoadedPlugins]], list[Error]]:
    """Loads installed plugins and a configuration file, that is also validated.

    :param path: Path to the configuration file

    :return: A tuple containing a validated configuration file and the loaded plugins (or ``None``,
             on failure of any of these steps), along with any errors / warnings that may have
             happened.
    """

    errors: list[Error] = []
    config = handle_error_append(errors, load_config(path))
    plugins = handle_error_append(errors, load_plugins())

    if config is None or plugins is None:
        return (None, errors)

    validate_success = handle_error_append(errors, validate(config, plugins))
    if not validate_success:
        return (None, errors)

    return ((config, plugins), errors)

def main() -> None:
    """The entry point to powermodes"""

    parsed_args = handle_error(parse_arguments())
    args = handle_error(validate_arguments(parsed_args))

    match args.action:
        case Action.SHOW_HELP:
            print(get_help_message())

        case Action.SHOW_VERSION:
            print(handle_error(__format_version()))

        case _:
            handle_error(__assert_root())
            config, plugins = handle_error(__load_config_plugins(args.config))

            match args.action:
                case Action.VALIDATE:
                    sys.exit(0)

                case Action.APPLY_MODE:
                    success, errors = apply_mode(args.mode, config, plugins)
                    handle_error((True if success else None, errors))

                case Action.INTERACTIVE:
                    options = list(zip(config.keys(), config.keys()))
                    mode = choose_option(options, 'Choose a powermode:')

                    success, errors = apply_mode(mode, config, plugins)
                    handle_error((True if success else None, errors))
