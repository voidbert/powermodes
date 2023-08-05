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

