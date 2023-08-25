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

- Reading and writing to text files.
"""

from typing import Optional

from .error import Error

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
