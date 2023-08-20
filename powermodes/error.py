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
powermodes.error
================

Error handling for powermodes isn't done with exceptions, to allow methods to report multiple
errors, and also report warnings without having to be exited.

Raising errors
^^^^^^^^^^^^^^

You can create an error the following way:

.. code:: python

    from .error import Error, ErrorType # Use ..error if this is plugin code

    error   = Error(ErrorType.ERROR,   'sample error')
    warning = Error(ErrorType.WARNING, 'sample warning')

You should write your code to be resilient to errors, adapting to errors and emitting warnings when
needed. Only use :attr:`ErrorType.ERROR` when your code finds a fatal error it can't recover from.
For example, if a plugin you're developing is configured invalidly, report a warning and modify
the configuration, to remove or change invalid options.

Errors are raised by functions that have one of the following type signatures:

- ``fn(...) -> tuple[Optional[Any], Optional[Error]]`` - single or no error
- ``fn(...) -> tuple[Optional[Any], list[Error]]`` - arbitrary number of errors

Along with the return value, these methods may return a possible error or a list of errors. Here's
an example:

.. code:: python

    def read_text_file(path: str) -> tuple[Optional[str], Optional[Error]]:
        try:
            with open(path) as f:
	            return (f.read(), None)
        except OSError:
            return (None, Error(ErrorType.ERROR, f'failed to read text file "{path}"'))

Handling errors
^^^^^^^^^^^^^^^

If you aren't modifying powermodes' :func:`~powermodes.main` or developing an entry point for an
interactive version of a plugin, you're likely looking for :func:`handle_error_append`. Otherwise,
see :func:`handle_error`. :func:`handle_error_append` just adds the errors reported by a function to
a list. Here's an example:

.. code:: python

    def error_handling_example() -> tuple[None, list[Error]]:
        errors = []
        i_may_fail_42_return     = handle_error_append(errors, i_may_fail(42))
        i_may_fail_0xbeef_return = handle_error_append(errors, i_may_fail(0xbeef))
        return (None, errors)

In this example, ``i_may_fail`` is a hypothetical function that returns an error. If you need the
result from ``i_may_fail`` to continue running your function, just use a simple if statement:

.. code:: python

    def error_handling_example2() -> tuple[int, list[Error]]:
        errors = []
        val = handle_error_append(errors, i_may_fail(0))
        if val is None:
            return (None, errors)
        else:
            return (val + 1, errors) # We also return errors because i_may_fail may also report
                                     # warnings, for example.

Keep in mind that powermodes' errors aren't the only type of error that needs to be handled.
**Don't forget to handle Python exceptions!**

Module documentation
^^^^^^^^^^^^^^^^^^^^
"""

from __future__ import annotations
from enum import Enum
import sys
from typing import Any, NoReturn, Optional, Union

class ErrorType(Enum):
    """The type of an :class:`Error`."""

    WARNING = 0 #: A non-fatal error.
    ERROR = 1   #: A fatal (although, possibly not immediately fatal) error.

class Error:
    """An error / warning that can be reported by powermodes."""

    def __init__(self: Error, error_type: ErrorType, message: str, \
                 origin: Optional[str] = None) -> None:
        """Constructor method"""

        self.error_type: ErrorType = error_type
        """Whether the error is fatal (:attr:`ErrorType.ERROR`) or non-fatal
        (:attr:`ErrorType.WARNING`)."""

        self.message: str = message
        """String of the error message."""

        self.origin: Optional[str] = origin
        """The origin of an error can be `None`, meaning it originates from powermodes itself, or
        the name of the plugin the error originated from. **You don't need to manually specify your
        errors' origins**, as origins of errors originating from plugins are automatically set
        before printing the errors.
        """

def print_error(err: Error) -> None:
    """Prints a powermodes' error to ``sys.stderr``. The message will be formated and, if
    ``sys.stderr`` is a terminal (the output isn't being piped), the message will be outputted in
    an adequate color (red for :attr:`ErrorType.ERROR` and yellow for :attr:`ErrorType.WARNING`).

    :param err: Error to be printed.
    """

    print_str = ''
    if err.origin is not None:
        print_str = err.origin + ' '

    print_str += 'warning: ' if err.error_type == ErrorType.WARNING else 'error: '
    print_str += err.message

    if sys.stderr.isatty():
        color = '\033[33m' if err.error_type == ErrorType.WARNING else '\033[31m'
        print_str = color + print_str + '\033[39m'

    print(print_str, file=sys.stderr)

def handle_error(output: tuple[Optional[Any], Union[Error, list[Error], None]]) -> \
    Union[Any, NoReturn]:
    """Handles errors by printing them and exiting the program on failure.

    This method **shouldn't be used in plugins** and methods other than
    :func:`~powermodes.main.main`, as the program shouldn't just exit when any error occurs
    (for control flow reasons).

    Functions that return errors have one of the following type signatures:

    - ``fn(...) -> tuple[Optional[Any], Optional[Error]]`` - single or no error
    - ``fn(...) -> tuple[Optional[Any], list[Error]]`` - arbitrary number of errors

    To handle errors with this method, use: ``val = handle_error(i_may_fail())``, where ``val`` is
    the return value (with errors removed) of ``i_may_fail``, a method that may return errors.

    This function will print the errors present in the return value of the function that raises
    errors (second element of ``output``). If the first element of ``output`` is :data:`None`, and
    fatal errors (:attr:`ErrorType.ERROR`) have been returned, that is considered to be a failure
    and the program is exited with code 1.

    :param output: The return value of a function that may return errors.
    :return: The first element of ``output``, if the program isn't left fatally.
    """

    obj, err = output
    has_errors = False
    if isinstance(err, Error):
        print_error(err)
        has_errors = err.error_type == ErrorType.ERROR
    elif isinstance(err, list):
        for error in err:
            print_error(error)
        has_errors = any(map(lambda e: e.error_type == ErrorType.ERROR, err))
    else:
        has_errors = False

    if obj is None and has_errors:
        sys.exit(1)

    return obj

def handle_error_append(lst: list[Error], \
                        output: tuple[Optional[Any], Union[Error, list[Error], None]]) -> Any:
    """Handles errors by appending them to a list.

    Functions that return errors have one of the following type signatures:

    - ``fn(...) -> tuple[Optional[Any], Optional[Error]]`` - single or no error
    - ``fn(...) -> tuple[Optional[Any], list[Error]]`` - arbitrary number of errors

    To handle errors with this method, use: ``val = handle_error_append(errors, i_may_fail())``,
    where ``val`` is the return value (with errors removed) of ``i_may_fail``, a method that may
    return errors, and ``errors`` is a list of errors.

    All errors in ``output`` will be appended to ``lst``, and none of them will be printed.

    :param lst: The list of errors to be modified.
    :param output: The return value of a function that may return errors.
    :return: The first element of ``output``.
    """

    obj, err = output
    if isinstance(err, Error):
        lst.append(err)
    elif isinstance(err, list):
        lst.extend(err)

    return obj

def set_unspecified_origins(errors: list[Error], origin: str) -> None:
    """Sets the origins of errors whose :attr:`Error.origin` is :data:`None`. Used to set the
    origin of errors coming from plguins. Errors with set origins won't be changed.

    :param errors: List of errors that will be modified to have new origins.
    :param origin: New origin of the errors of unspecified origin.

    :return: :data:`None`. **Keep in mind that** ``errors`` **is modified**.
    """

    for err in errors:
        if err.origin is None:
            err.origin = origin
