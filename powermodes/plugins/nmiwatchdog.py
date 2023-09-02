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
powermodes.plugins.nmiwatchdog
==============================

Plugin to enable / disable the NMI (non-maskable interrupt) watchdog. See how to configure it
`here <../../../powermodes/plugins/nmiwatchdog.md>`_.
"""

from typing import Any, Union

from ..config import iterate_config, plugin_is_in_all_powermodes
from ..error import Error, ErrorType, handle_error_append
from ..pluginutils import write_text_file

NAME = 'nmi-watchdog'
VERSION = '1.1'

def validate(config: dict[str, dict[str, Any]]) -> tuple[list[str], list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.validate`."""

    errors: list[Error] = []
    handle_error_append(errors, plugin_is_in_all_powermodes(config, NAME))

    successful: list[str] = []
    for powermode, config_obj in iterate_config(config, NAME):
        if isinstance(config_obj, bool) or config_obj == 'skip':
            successful.append(powermode)
        else:
            errors.append(Error(ErrorType.WARNING, f'config, in powermode "{powermode}" must ' \
                                                    'be a boolean or the string "skip".'))
    return (successful, errors)

def configure(config: Union[bool, str]) -> tuple[bool, list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.configure`."""

    if isinstance(config, str): # "skip"
        return (True, [])

    errors: list[Error] = []
    write_string = { False: '0\n', True: '1\n' }[config]
    enable_disable = { False: 'disable', True: 'enable' }[config]

    success = handle_error_append(errors, write_text_file('/proc/sys/kernel/nmi_watchdog',
        write_string, Error(ErrorType.WARNING, f'Failed to {enable_disable} NMI watchdog.')))

    return (success, errors)
