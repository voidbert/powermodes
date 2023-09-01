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
powermodes.pluginutils
======================

This module contains utilities for tasks often performed by plugins. As of now, the following are
implemented:

- Reading and writing to text files;
- Listing, loading and unloading of Linux kernel modules.
"""

from typing import Any, Optional
from subprocess import DEVNULL, PIPE, run

from .error import Error, ErrorType

def read_text_file(path: str, error: Error) -> tuple[Optional[str], Optional[Error]]:
    """Tries to read a string from a text file.

    :param path: Path of the file to be read.
    :param error: Error to be reported in case of failure.
    :return: The contents of the file (on success), or ``error``.
    """

    try:
        with open(path, 'r', encoding='utf-8') as file:
            contents = file.read()
        return (contents, None)
    except OSError:
        return (None, error)

def write_text_file(path: str, contents: str, error: Error) -> tuple[bool, Optional[Error]]:
    """Tries to write a string to a text file.

    :param path: Path to the file to write to.
    :param contents: String contents to write to the file.
    :param error: Error to be reported in case of failure.
    :return: Whether writing to the file was successful, along with, possibly, ``error``.
    """

    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(contents)
        return (True, None)
    except OSError:
        return (False, error)
def list_modules() -> tuple[Optional[list[str]], Optional[Error]]:
    """Lists all modules loaded onto the Linux kernel (by parsing ``/proc/modules``).

    :return: A list of names of the loaded modules, (or :data:`None`, along with a warning,
             on failure).
    """

    proc_modules, error = read_text_file('/proc/modules', Error(ErrorType.WARNING,
        'failed to list kernel modules: failure reading /proc/modules.'))

    if proc_modules is None:
        return (None, error)

    lines = proc_modules.split('\n')[:-1] # Remove POSIX end-of-line
    try:
        return (list(map(lambda line: line.split()[0], lines)), None)
    except IndexError:
        return (None, Error(ErrorType.WARNING, 'failed to list kernel modules: failure parsing ' \
                                               '/proc/modules'))

def load_module(name: str, params: dict[str, Any], force_modversion: bool = False, \
                force_vermagic: bool = False) -> tuple[bool, Optional[Error]]:
    """Loads a Linux kernel module using ``modprobe``. Note that ``modprobe`` is called with
    ``--first-time``, meaning that an error will occur if you try to load a module that's already
    loaded.

    :param name: Name of the kernel module provided to ``modprobe``.
    :param params: Parameters used to configure the kernel module. Each parameter will create an
                   argument for modprobe, formatted like ``f'{key}="{value}"'``. If ``value`` is a
                   string containing quotes, this method will fail.
    :param force_modversion: See ``--force-modversion`` in ``man 8 modprobe``. Use :data:`False`
                             unless you know what you're doing. Requires a kernel built with
                             ``CONFIG_MODULE_FORCE_LOAD``.
    :param force_vermagic: See ``--force-vermagic`` in ``man 8 modprobe``. Use :data:`False`
                           unless you know what you're doing. Requires a kernel built with
                           ``CONFIG_MODULE_FORCE_LOAD``.
    :return: Whether the module was successfully loaded, along with a possible warning in case of
             failure.
    """

    if any(map(lambda value: isinstance(value, str) and '"' in value, params.values())):
        return (False, Error(ErrorType.WARNING, 'at least a parameter for the kernel module '
                                               f'{name} is a string containing quotes. Those ' \
                                                'can\'t always be correctly escaped, so ' \
                                                'they\'re not accepted.'))

    param_list = list(map(lambda kv: f'{kv[0]}="{kv[1]}"', params.items()))
    result = run(['modprobe'] + (['--force-modversion'] if force_modversion else []) + \
                                (['--force-vermagic']   if force_vermagic   else []) + \
                                ['--first-time', name] + param_list,
                 stdin=DEVNULL, stdout=PIPE, stderr=PIPE, check=False)

    if result.returncode == 0:
        return (True, None)
    else:
        string_stderr = result.stderr.decode('utf-8')[:-1] # Remove POSIX end-of-line
        return (False, Error(ErrorType.WARNING, f'failed to load kernel module "{name}". ' \
                                                f'Here\'s modprobe\'s output:\n{string_stderr}'))

def unload_module(name: str, force: bool) -> tuple[bool, Optional[Error]]:
    """Unloads a Linux kernel module using ``rmmod``.

    :param name: Name of the module to be unloaded.
    :param force: If the module should be force-removed (``rmmod -f``). For this to work, your
                  kernel needs to be compiled with ``CONFIG_MODULE_FORCE_UNLOAD`` (the default).
    :return: Whether the module was successfully unloaded, along with a warning if failure
             occurred.
    """

    result = run(['rmmod'] + (['-f'] if force else []) + [name],
                 stdin=DEVNULL, stdout=PIPE, stderr=PIPE, check=False)

    if result.returncode == 0:
        return (True, None)
    else:
        string_stderr = result.stderr.decode('utf-8')[:-1] # Remove POSIX end-of-line
        return (False, Error(ErrorType.WARNING, f'failed to unload kernel module "{name}". ' \
                                                f'Here\'s rmmod\'s output:\n{string_stderr}'))
