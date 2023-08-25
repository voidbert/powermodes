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

from typing import Any
from ..config import plugin_is_in_all_powermodes
from ..error import Error, ErrorType, handle_error_append
from ..pluginutils import write_text_file

NAME = 'nmi-watchdog'
VERSION = '1.0'

def validate(config: dict[str, dict[str, Any]]) -> tuple[list[str], list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.validate`."""

    errors: list[Error] = []
    handle_error_append(errors, plugin_is_in_all_powermodes(config, NAME))

    successful: list[str] = []
    for powermode, powermode_config in config.items():
        if NAME in powermode_config:
            if isinstance(powermode_config[NAME], bool):
                successful.append(powermode)
            else:
                errors.append(Error(ErrorType.WARNING, f'config in powermode {powermode} must be' \
                                                        'a boolean.'))
    return (successful, errors)

def configure(config: bool) -> tuple[bool, list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.configure`."""

    errors: list[Error] = []
    write_string = { False: '0\n', True: '1\n' }[config]
    enable_disable = { False: 'disable', True: 'enable' }[config]

    success = handle_error_append(errors, write_text_file('/proc/sys/kernel/nmi_watchdog',
        write_string, Error(ErrorType.WARNING, f'Failed to {enable_disable} NMI watchdog.')))

    return (success, errors)
