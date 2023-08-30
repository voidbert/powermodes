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
powermodes.plugins.command
==========================

Plugin to run commands. See how to configure it `here <../../../powermodes/plugins/command.md>`_.
"""

from dataclasses import dataclass
from subprocess import run, DEVNULL, PIPE
from typing import Any, Optional, Union

from ..config import iterate_config
from ..error import Error, ErrorType, handle_error_append

NAME = 'command'
VERSION = '1.0'

@dataclass
class _Command:

    command: Union[str, list[str]]
    """The command to be executed, through a shell (``str``), or directly (``list[str]``)."""

    allow_stdin: bool
    """Whether the program can read from standard input."""

    show_stdout: bool
    """Whether the program's standard output should be shown to the user (not captured)."""

    show_stderr: bool
    """Whether the program's standard error should be shown to the user (not captured)."""

    warning_on_failure: bool
    """Whether a warning should be reported if the program exits with a non-zero exit code."""

def __command_validate_command(command: dict[str, Any], powermode: str, number: int) \
    -> tuple[Union[str, list[str], None], Optional[Error]]:
    """Gets the ``command`` attribute in a command (the actual executable and arguments). Some
    checks are performed to assess its type validity.

    :param command: Element of a command list.
    :param powermode: Name of the powermode the command is in. Used for error messages, if needed.
    :param number: Index of the command in the list (starting at 1). Used for error messages, if
                   needed.
    :return: A string (shell command) or list of strings (executable and arguments) to be executed,
             or :data:`None` and a warning in case of poor configuration.
    """

    if 'command' not in command:
        return (None, Error(ErrorType.WARNING, f'Command number {number} in powermode ' \
                                               f'{powermode} must have a value for "command" in ' \
                                                'the TOML table. Ignoring this powermode.'))
    else:
        if isinstance(command['command'], str):
            return (command['command'], None)
        elif isinstance(command['command'], list) and \
             all(map(lambda e: isinstance(e, str), command['command'])):

            return (command['command'], None)
        else:
            return (None, Error(ErrorType.WARNING, f'Command number {number} in powermode ' \
                                                   f'{powermode}: "command" (in the TOML table),' \
                                                    ' must be a string or list of strings. ' \
                                                    'Ignoring this powermode.'))

def __command_validate_boolean(command: dict[str, Any], bool_name: str, default: bool,
                               powermode: str, number: int) -> tuple[bool, Optional[Error]]:
    """Returns the value of a boolean in a command (``show-stdout``, ``show-stderr`` and
    ``warning-on-failure``), reporting a warning if the value provided isn't a boolean. Auxiliary
    function for :func:`__command_validate`.

    :param command: Element of a command list.
    :param bool_name: Name of the boolean to get from ``command``.
    :param default: Default value of the boolean, used if it's not (or wrongly) specified.
    :param powermode: Name of the powermode the command is in. Used for error messages, if needed.
    :param number: Index of the command in the list (starting at 1). Used for error messages, if
                   needed.
    :return: The boolean value, along with a possible warning if an invalid value was provided for
             the boolean.
    """

    if bool_name not in command:
        return (default, None)
    elif isinstance(command[bool_name], bool):
        return (command[bool_name], None)
    else:
        return (default, Error(ErrorType.WARNING, f'Command number {number} in powermode ' \
                                                  f'{powermode}: "{bool_name}" must be a ' \
                                                  f'boolean. Choosing default: {default}.'))

def __command_validate_unknowns(command: dict[str, Any], powermode: str, number: int) \
    -> tuple[None, Optional[Error]]:
    """Reports a warning for unrecognized properties in the command dictionary.

    :param command: Element of a command list.
    :param powermode: Name of the powermode the command is in. Used for error messages, if needed.
    :param number: Index of the command in the list (starting at 1). Used for error messages, if
                   needed.
    :return: A possible reported warning.
    """

    unknown = list(filter(lambda p: p not in [ 'command', 'allow-stdin', 'show-stdout',
        'show-stderr', 'warning-on-failure' ], command.keys()))
    if len(unknown) != 0:
        unknown_csv = ', '.join(unknown)
        return (None, Error(ErrorType.WARNING, f'Command number {number} in powermode ' \
                                               f'{powermode} has the following unknown ' \
                                               f'properties: {unknown_csv}.'))
    else:
        return (None, None)

# pylint: disable=too-many-locals
def __command_validate(command: Any, powermode: str, number: int) \
    -> tuple[Optional[_Command], list[Error]]:
    """Validates an element of a list of commands. Reports any warnings about the configuration,
    and returns a :class:`_Command`, command information organized in a data structure.

    :param command: Element of a command list.
    :param powermode: Name of the powermode the command is in. Used for error messages, if needed.
    :param number: Index of the command in the list (starting at 1). Used for error messages, if
                   needed.
    :return: Organized command data (:data:`None`, along with warnings, on failure).
    """

    if not isinstance(command, dict):
        return (None, [ Error(ErrorType.WARNING, f'Command number {number} in powermode ' \
                                                 f'{powermode} must be a TOML table.') ])

    errors: list[Error] = []
    to_run = handle_error_append(errors, __command_validate_command(command, powermode, number))

    allow_stdin = handle_error_append(errors, __command_validate_boolean(
        command, 'allow-stdin', False, powermode, number))
    show_stdout = handle_error_append(errors, __command_validate_boolean(
        command, 'show-stdout', False, powermode, number))
    show_stderr = handle_error_append(errors, __command_validate_boolean(
        command, 'show-stderr', True, powermode, number))
    warning_on_failure = handle_error_append(errors, __command_validate_boolean(
        command, 'warning-on-failure', True, powermode, number))

    handle_error_append(errors, __command_validate_unknowns(command, powermode, number))

    if to_run is None:
        return (None, errors)
    else:
        return (_Command(to_run, allow_stdin, show_stdout, show_stderr, warning_on_failure),
                errors)

def validate(config: dict[str, dict[str, Any]]) -> tuple[list[str], list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.validate`."""

    errors: list[Error] = []
    successful: list[str] = []

    for powermode, config_obj in iterate_config(config, NAME):
        # Config object must be a list containing commands. All of them must be valid.
        if isinstance(config_obj, list):

            powermode_success = True
            for i, command_dict in enumerate(config_obj):
                command = handle_error_append(errors, \
                    __command_validate(command_dict, powermode, i + 1))

                if command is None:
                    powermode_success = False

            if powermode_success:
                successful.append(powermode)

        else:
            errors.append(Error(ErrorType.WARNING, f'config in powermode {powermode} must ' \
                                                    'be a list of commands.'))

    return (successful, errors)

def configure(config: list[dict[str, Any]]) -> tuple[bool, list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.configure`."""

    errors: list[Error] = []
    all_failed = True

    for i, _ in enumerate(config):
        # Error handling has been done in validate()
        command: _Command = __command_validate(config[i], '', i)[0] # type: ignore

        result = run(command.command, check=False,
                     shell=isinstance(command.command, str),
                     stdin=None if command.allow_stdin else DEVNULL,
                     stdout=None if command.show_stdout else PIPE,
                     stderr=None if command.show_stderr else PIPE
                    )

        if command.warning_on_failure and result.returncode != 0:
            msg = f'Command {i + 1} left with error code {result.returncode}.'
            if not command.show_stderr: # stderr has been piped and can be shown

                decoded_stderr = result.stderr.decode('utf-8')
                if decoded_stderr[-1] == '\n':
                    decoded_stderr = decoded_stderr[0:-1]

                msg += ' Here\'s the program\'s stderr:\n' + decoded_stderr
            errors.append(Error(ErrorType.WARNING, msg))
        else:
            all_failed = False

    return (not all_failed, errors)
