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
# @file input.py
# @package powermodes.input
# @brief Methods for getting user input.
##

from collections.abc import Iterable
from typing import Any
from sys import maxsize, stderr

##
# @brief Gets an integer from `stdin`.
# @details On parsing / range failure, this method tries to read input again, until a valid integer
#          is found.
# @param bottom Minimum number accepted. Defaults to the smallest integer.
# @param top    Maximum number accepted. Default to the largest integer.
# @param prompt Prompt given to Python's `input`. Will be formatted and with the arguments @p top
#               and @p bottom. Defaults to `{bottom} - {top} > `.
# @returns The inputted integer.
##
def input_integer(bottom: int = -maxsize - 1, top: int = maxsize,
                  prompt: str ='{bottom} - {top} > ') -> int:

    while True:
        string_input = input(prompt.format(bottom=bottom, top=top))
        try:
            int_input = int(string_input)
            if bottom <= int_input <= top:
                return int_input
            else:
                raise ValueError()
        except ValueError:
            print(f'Input must be an integer between {bottom} and {top}.', file=stderr)

##
# @brief Prints a list of strings as options for the user to choose, along with a message.
# @param options Options to be printed
# @param message Message printed before the options.
# @param line_format Format for each option. Will be formatted with the variables `n` (option
#               number) and `msg` (message). Defaults to `({n}) - {msg}`.
##
def print_options(options: Iterable[str],
                  message: str ='Choose an option:', line_format: str ='{n} - {msg}') -> None:

    print(message, end='\n')
    count = 1
    for option in options:
        print(line_format.format(n=count, msg=option))
        count += 1

##
# @brief Asks the user to choose an item from a list by inputting a number.
# @details On parsing / range failure, this method tries to read input again, until a valid integer
#          is found.
# @param options List of values and their human-readable counterparts. The latter will be printed,
#                while one of the former will be returned if the user chooses it.
# @param message Message asking the user to choose the option.
# @param line_format Format for option lines. See
#                    [print_options](@ref powermodes.input.print_options).
# @param prompt Prompt for [input_integer](@ref powermodes.input.input_integer).
##
def choose_option(options: list[tuple[Any, str]], \
                  message: str ='Choose an option:', line_format: str ='{n} - {msg}', \
                  prompt: str ='{bottom} - {top} > ') -> Any:

    print_options(map(lambda t: t[1], options), message, line_format)
    index = input_integer(1, len(options), prompt) - 1
    return options[index][0]
