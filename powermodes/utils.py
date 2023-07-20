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
# @file utils.py
# @package powermodes.utils
# @brief Utilities for powermodes
##

from sys import exit, stderr

##
# @brief Prints a message to stderr and exits the program with code 1.
##
def fatal(msg: any) -> ():
    print_str = f'fatal: {msg}'
    if stderr.isatty():
        print_str = f'\033[91m{print_str}\033[39m'

    print(print_str, file=stderr)
    exit(1)

##
# @brief Prints a warning message to stderr.
##
def warning(msg: any) -> ():
    print_str = f'warning: {msg}'
    if stderr.isatty():
        print_str = f'\033[93m{print_str}\033[39m'

    print(print_str, file=stderr)

