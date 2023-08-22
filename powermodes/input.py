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
powermodes.input
================

Methods to read and parse user input. Useful for powermodes' interactive mode
(:attr:`powermodes.arguments.Action.INTERACTIVE`) and for any plugin's interactive features.

Module contents
^^^^^^^^^^^^^^^
"""

from collections.abc import Iterable
from typing import Any
from sys import maxsize, stderr

def input_integer(bottom: int = -maxsize - 1, top: int = maxsize,
                  prompt: str ='{bottom} - {top} > ', \
                  error: str = 'Input must be an integer between {bottom} and {top}!') \
                -> int:
    """Queries the user to input an integer, then reads it from ``stdin``. In case the text
    inputted does not read as an integer in the desired range, an error message is printed to
    ``stdout`` and this method tries to get an integer from the user again and again, until valid
    input is obtained.

    :param bottom: Lowest number the user is allowed to input. Defaults to the smallest integer
                   for the user's system (``- sys.maxsize - 1``).
    :param top: Highest number the user is allowed to input (**inclusive range**). Defaults to the
                largest integer for the user's system (``sys.maxsize``).
    :param prompt: Prompt provided to Python's ``input`` method. The string will be formatted with
               the values of arguments ``bottom`` and ``top``.
    :param error: Error message for when the user's input isn't an integer between ``bottom`` and
                  ``top``. The string will be formatted with the values of arguments ``bottom`` and
                  ``top``.

    :return: The integer inputted by the user.

    Example:

    .. code:: python

        >>> input_integer(0, 10, 'Integer from {bottom} to {top} > ', \\
                'Come on, that\\\'s not what I asked for!')

        # Integer from 0 to 10 > 11
        # Come on, that\'s not what I asked for!
        # Integer from 0 to 10 > 7
        # 7
    """

    while True:
        string_input = input(prompt.format(bottom=bottom, top=top))
        try:
            int_input = int(string_input)
            if bottom <= int_input <= top:
                return int_input
            else:
                raise ValueError()
        except ValueError:
            print(error.format(bottom=bottom, top=top), file=stderr)

def print_options(options: Iterable[str],
                  message: str ='Choose an option:', line_format: str ='  ({n}) - {opt}') -> None:
    """Prints a list of strings as options for the user to choose. No input reading is actually
    performed; for that, see :func:`choose_option`.

    :param options: Iterable of options to be printed.
    :param message: Message to be printed before the options, asking the user to choose an option.
                    you can replace the generic ``'Choose an option:'`` message, with something
                    like ``'Choose a powermode:'``, etc.
    :param line_format: The string used to format each line containing an option. It will be
                        formatted variables with ``n``, the number of the option, and ``opt``, the
                        text content of the option in ``options``.

    Example:

    .. code:: python

        >>> print_options(['Alice', 'Bob', 'Charlie'], 'Choose who to hack:')
        Choose who to hack:
          (1) - Alice
          (2) - Bob
          (3) - Charlie
    """

    print(message, end='\n')
    count = 1
    for option in options:
        print(line_format.format(n=count, opt=option))
        count += 1

def choose_option(options: list[tuple[Any, str]], \
                  message: str ='Choose an option:', line_format: str ='  ({n}) - {opt}', \
                  prompt: str ='{bottom} - {top} > ', \
                  error: str = 'Input must be an integer between {bottom} and {top}!') -> Any:
    """Asks the user to choose an item from a list of options, by inputting a number. Like
    :func:`input_integer`, this function will keep trying to read input until a valid integer is
    read.

    :param options: A list of tuples, the options the user will choose from. The first tuple
                    element is the object that will be returned if the user chooses that option.
                    The second is the name of the object that should be presented to the user.
    :param message: Argument provided to :func:`print_options`: Message to be printed before the
                    options, asking the user to choose an option. you can replace the generic
                    ``'Choose an option:'`` message, with something like ``'Choose a powermode:'``,
                    etc.
    :param line_format: Argument provided to :func:`print_options`: The string used to format each
                        line containing an option. It will be formatted with variables ``n``, the
                        number of the option, and ``opt``, the text content of the option in
                        ``options``.
    :param prompt: Argument provided to :func:`input_integer`: Prompt provided to Python's
                   ``input`` method. The string will be formatted with the values of
                   ``bottom`` (1) and ``top`` (``1 + len(options)``).
    :param error: Argument provided to :func:`input_integer`. Error message for when the user's
                  input isn't an integer between ``bottom`` and ``top``. The string will be
                  formatted with the values of arguments ``bottom`` and ``top``.

    :return: The first element of one of the tuples in ``options``.

    Example:

    .. code::  python

        >>> choose_option([('192.168.1.2', 'Alice'), ('192.168.1.3', 'Bob')], \\
                'Choose who to hack:')
        # Choose who to hack:
        #  (1) - Alice
        #  (2) - Bob
        # 1 - 2 > 8
        # Input must be an integer between 1 and 2!
        # 1 - 2 > 1
        # '192.168.1.2'
    """

    print_options(map(lambda t: t[1], options), message, line_format)
    index = input_integer(1, len(options), prompt) - 1
    return options[index][0]
