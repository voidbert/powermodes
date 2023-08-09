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
# @file error.py
# @package powermodes.error
# @brief Powermodes' error system.
##

from enum import Enum
from sys import stderr
from typing import Union

##
# @brief Type of an [Error](@ref powermodes.error.Error).
##
class ErrorType(Enum):
    WARNING = 0
    ERROR = 1

##
# @brief An error / warning that can be reported by powermodes.
# @details Used so that a powermodes' function can report multiple errors, instead of just raising
#          an exception and exiting.
##
class Error:
    error_type: ErrorType
    message: str
    origin: str | None

    def __init__(self, error_type, message, origin = None):
        self.error_type = error_type
        self.message = message
        self.origin = origin

##
# @brief Prints a powermodes' error to `sys.stderr`.
# @details The message will be formatted and, if `sys.stderr` is a terminal, it'll be printed in
#          color.
##
def print_error(err: Error) -> None:
    print_str = ''
    if err.origin is not None:
        print_str = err.origin + ' '

    print_str += 'warning: ' if err.error_type == ErrorType.WARNING else 'error: '
    print_str += err.message

    if stderr.isatty():
        color = '\033[33m' if err.error_type == ErrorType.WARNING else '\033[31m'
        print_str = color + print_str + '\033[39m'

    print(print_str, file=stderr)

##
# @brief Handle errors from functions that may return them.
# @details
# Prints errors and leaves the program on fatal errors.
#
# Used for functions with one of the following type signatures:
#  - `fn() -> tuple[Union[any, None], Union[Error, None]]`
#  - `fn() -> tuple[Union[any, None], list[Error]]`
#
# If the error isn't `None`, it will be printed. If there are non-warning errors and the
# returned object is `None`, the program is left fatally.
#
# @param output Return value from the function that may return an error.
# @returns The value returned by the function whose result is placed in @p output.
##
def handle_error(output: tuple[Union[any, None], Union[Error, list[Error], None]]) -> any:
    obj, err = output
    has_errors = False
    if type(err) == Error:
        print_error(err)
        has_errors = err.error_type == ErrorType.ERROR
    elif type(err) == list:
        for e in err:
            print_error(e)
        has_errors = any(map(lambda e: e.error_type == ErrorType.ERROR, err))
    else:
        has_errors = False

    if obj is None and has_errors:
        exit(1)

    return obj

##
# @brief Handles errors by appending them to a list.
# @details
# Used for functions with one of the following type signatures:
#  - `fn() -> tuple[Union[any, None], Union[Error, None]]`
#  - `fn() -> tuple[Union[any, None], list[Error]]`
#
# Any error will be appended @p lst and no error will be printed.
#
# @param lst List of errors to which to append new errors.
# @param output Return value from the function that may return an error.
# @returns The value returned by the function whose result is placed in @p output.
##
def handle_error_append(lst: list[Error], \
                        output: tuple[Union[any, None], Union[Error, list[Error], None]]) -> any:
    obj, err = output
    if type(err) == Error:
        lst.append(err)
    elif type(err) == list:
        lst.extend(err)

    return obj
