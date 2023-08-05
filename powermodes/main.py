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

from .arguments import ArgumentException, VersionException, Action, parse_arguments, \
    get_action, get_help_message, get_version_string

##
# @brief The entry point to powermodes.
##
def main() -> None:
    try:
        args = parse_arguments()
        action = get_action(args)
    except ArgumentException as err:
        print(str(err))
        exit(1)

    match action:
        case Action.SHOW_HELP:
            print(get_help_message())

        case Action.SHOW_VERSION:
            try:
                print(get_version_string())
            except VersionException as err:
                print(str(err))
                exit(1)

