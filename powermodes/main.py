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

from .arguments import Action, parse_arguments, validate_arguments, get_help_message, \
    get_version_string
from .error import handle_error
from .plugin import load_plugins

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
            # Non-fatal errors should be raised, so the program continues
            version = handle_error(get_version_string())
            plugins = handle_error(load_plugins())

            if version is not None:
                print(version)

            if len(plugins) != 0:
                print('Versions of installed plugins:')
                for plugin in plugins:
                    print(f'{plugin.name} {plugin.version}')

        case _:
            raise NotImplementedError('I\'m not that fast of a developer!')
