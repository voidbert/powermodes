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
powermodes.plugins.intelepb
===========================

Plugin to control the `Intel Performance and Energy Bias Hint
<https://docs.kernel.org/admin-guide/pm/intel_epb.html>`_. See how to configure it
`here <../../../powermodes/plugins/intelepb.md>`_.
"""

from pathlib import Path
from typing import Any, Optional, Union

from ..config import plugin_is_in_all_powermodes
from ..error import Error, ErrorType, handle_error_append
from ..pluginutils import write_text_file

NAME = 'intel-epb'
VERSION = '1.0'

__epb_files: list[Path] = []
"""Files used to control Intel EPB. See :func:`__list_epb_files`"""

def __list_cpus() -> tuple[list[Path], Optional[Error]]:
    """Creates the list of sysfs directories related to CPUs. One of these directories may look
    like ``/sys/devices/system/cpu/cpuN``, where ``N`` is a non-negative integer.

    :returns: A list of paths, all sysfs CPU directories, along with a possible error about failing
              to detect CPUs.
    """

    try:
        children = Path('/sys/devices/system/cpu').iterdir()
    except OSError:
        return ([], Error(ErrorType.WARNING, 'No CPUs detected.'))

    cpus = []
    for path in children:
        if path.stem.startswith('cpu') and path.stem[3:].isdigit():
            cpus.append(path)

    if len(cpus) == 0:
        return ([], Error(ErrorType.WARNING, 'No CPUs detected.'))

    return (cpus, None)

def __list_epb_files() -> tuple[list[Path], list[Error]]:
    """Lists all files used to control Intel EPB. A warning is raised for all CPUs that don't
    support it. A path to one of these files may look like
    ``/sys/devices/system/cpu/cpuN/power/energy_perf_bias``, where ``N`` is a non-negative integer.

    :return: A list of paths to Intel EPB sysfs files, along with possible warnings for CPUs that
             don't support it, or about a failure to get information about CPUs.
    """

    errors: list[Error] = []
    cpus = handle_error_append(errors, __list_cpus())
    if len(cpus) == 0:
        return ([], cpus)

    epb_files = map(lambda p: p.joinpath('power', 'energy_perf_bias'), cpus)

    existing: list[Path] = []
    non_existing: list[Path] = []
    for file in epb_files:
        (non_existing, existing)[file.is_file()].append(file)

    if len(existing) == 0:
        errors.append(Error(ErrorType.WARNING, 'EPB is not supported in this system.'))
    elif len(non_existing) != 0:
        non_existing_cpus = map(lambda p: p.parent.parent.stem, non_existing)
        non_existing_cpus_str = ', '.join(non_existing_cpus)
        errors.append(Error(ErrorType.WARNING,
            f'The following CPUs don\'t support EPB: {non_existing_cpus_str}'))

    return (existing, errors)

def __interpret_config_object(obj: Any, powermode: str) -> tuple[Optional[int], Optional[Error]]:
    """Interprets a configuration provided to this plugin.

    :param obj: Object used to configure this plugin.
    :param powermode: Name of the powermode where this configuration object is, for error message
                      purposes.

    :return: The number between 0 and 15 to write to
             ``sys/devices/system/cpu/cpuN/power/energy_perf_bias``, or, on failure, :data:`None`
             along with a warning.
    """

    string_map = {
                   'performance': 0, \
                   'balance-performace': 4, \
                   'normal': 6, 'default': 6, \
                   'normal-powersave': 7, \
                   'balance-power': 8, \
                   'power': 15 \
                 }

    if isinstance(obj, int) and 0 <= obj <= 15:
        return (obj, None)
    elif isinstance(obj, str) and obj in string_map:
        return (string_map[obj], None)
    else:
        accepted_strings = ', '.join(map(lambda s: f'"{s}"', string_map.keys()))
        return (None, Error(ErrorType.WARNING, f'{NAME}, in powermode {powermode}, must be ' \
                                                'configured with an integer between 0 and 15, ' \
                                                'or one of the following strings: ' \
                                               f'{accepted_strings}.'))

def validate(config: dict[str, dict[str, Any]]) -> tuple[list[str], list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.validate`."""

    global __epb_files
    errors: list[Error] = []

    __epb_files = handle_error_append(errors, __list_epb_files())
    handle_error_append(errors, plugin_is_in_all_powermodes(config, NAME))

    successful: list[str] = []
    for powermode, powermode_config in config.items():
        if NAME in powermode_config:
            if handle_error_append(errors, \
                                   __interpret_config_object(powermode_config[NAME], powermode)) \
               is not None:
                successful.append(powermode)

    return (successful, errors)

def configure(config: Union[int, str]) -> tuple[bool, list[Error]]:
    """See :attr:`powermodes.plugin.Plugin.configure`."""

    errors: list[Error] = []

    # Errors can safely be ignored (removed in validate)
    value = str(__interpret_config_object(config, '')[0]) + '\n'
    all_failed = True
    for file in __epb_files:
        path_str = str(file)
        cpu = file.parent.parent.stem

        success = \
            handle_error_append(errors, write_text_file(path_str, value, Error(ErrorType.WARNING, \
                f'Failed to set Intel EPB state for {cpu}.')))
        if success:
            all_failed = False

    return (not all_failed, errors)
