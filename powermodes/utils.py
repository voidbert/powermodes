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
# @details The message will have the folowing format: `"error: [your message]"`. If `stderr` is a
#          terminal, this will be printed in red.
# @param msg Message to be printed.
##
def fatal(msg: any) -> ():
    print_str = f'fatal: {msg}'
    if stderr.isatty():
        print_str = f'\033[91m{print_str}\033[39m'

    print(print_str, file=stderr)
    exit(1)

##
# @brief Prints a warning message to stderr.
# @details The message will have the folowing format: `"warning: [your message]"`. If `stderr` is a
#          terminal, this will be printed in yellow.
# @param msg Message to be printed.
##
def warning(msg: any) -> ():
    print_str = f'warning: {msg}'
    if stderr.isatty():
        print_str = f'\033[93m{print_str}\033[39m'

    print(print_str, file=stderr)

##
# @brief Allows the user to choose an element from the list by inputting a number.
# @details If the user's input is invalid, this method keeps trying to get valid input from the
#          user.
# @param values List of values to choose from. It must have the same length and @p names and not be
#               empty.
# @param names  Presented names of the values. It must have the same length and @p values and not
#               be empty.
# @returns The value chosen (from @p values).
##
def choose_from(values: list[any], names: list[str]) -> any:
    # Print items
    for i in range(0, len(names)):
        print(f'  ({i + 1}) - {names[i]}')

    # Get input until it's valid.
    while True:
        try:
            string_input = input('> ')
            number_input = int(string_input)
            if number_input not in range(1, len(names) + 1):
                raise ValueError()

            print('') # For spacing
            return values[number_input - 1]
        except KeyboardInterrupt:
            exit(0)
        except:
            print(f'Input must be a number from 1 to {len(names)}')

##
# @brief Reads a text file and returns its contents.
# @details Exceptions are automatically handled with a fatal error.
#          This method exists to be used as a one-liner.
# @param path The path to the file.
# @returns The text contents of the file.
##
def read_file(path: str) -> str:
    try:
        with open(path, 'r') as file:
            return file.read()
    except:
        fatal(f'failed to read file "{path}"!')

##
# @brief Writes text to a file.
# @details Exceptions are automatically handled with a fatal error.
#          This method exists to be used as a one-liner.
# @param path The path to the file.
# @param contents The text contents to be written.
##
def write_file(path: str, contents: str) -> ():
    try:
        with open(path, 'w') as file:
            file.write(contents)
    except:
        fatal(f'failed to write to file "{path}"!')

