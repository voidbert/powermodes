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
# @file intelpstate.py
# @package powermodes.plugins.intelpstate
# @brief Manage pstates on Intel processors
##

from dataclasses import dataclass
from enum import Enum
from os.path import join
from re import search

from utils import fatal, warning, read_file

##
# @brief Generates the file path for a file in the intel_pstate directory.
##
def pstate_file(file: str) -> str:
    return join('/sys/devices/system/cpu/intel_pstate', file)

##
# @brief Status of the intel_pstate driver.
# @details The status of the driver may imply more or less configuration from the user.
##
class DriverStatus(Enum):
    ACTIVE  = 0 ##< @brief Only for newer CPUs
    PASSIVE = 1 ##< @brief Available for every Intel CPU since Sandy Bridge

##
# @brief Internal configuration format.
# @details For more information, see
#          [intel_pstate driver documentation](https://www.kernel.org/doc/html/v6.3/admin-guide/pm/intel_pstate.html).
#          Any member variable can be `None`, meaning that that setting won't be applied.
##
@dataclass
class PstateConfig:
    ##
    # @brief Minimum frequency (as percentage of CPU spec).
    # @details Available in both active and passive modes.
    ##
    min_percentage: int = None

    ##
    # @brief Maximum frequency (as percentage of CPU spec).
    # @details Available in both active and passive modes.
    ##
    max_percentage: int = None

    ##
    # @brief Enable / disable turbo.
    # @details Available in both active and passive modes.
    ##
    turbo : bool = None

    ##
    # @brief Enable / disable energy efficient optimizations.
    # @details Only available in active mode.
    ##
    energy_efficient: bool = None

    ##
    # @brief Enable / disable dynamic boost.
    # @details Only available in active mode.
    ##
    dynamic_boost: bool = None

##
# @brief Determines if the CPU supports Intel Dynamic Acceleration.
# @details Will exit the program with an error message in case of failure.
# @returns Whether the CPU supports Intel Dynamic Acceleration (Turbo Boost).
##
def can_turbo() -> bool:
    cpuinfo = read_file('/proc/cpuinfo')

    flag_match = search(r'\nflags[\s]*:', cpuinfo)
    if not flag_match:
        fatal('intelpstate cannot read flags from /proc/cpuinfo!')

    flags_string_start = flag_match.span()[1]
    try:
        flags_string_end = cpuinfo.index('\n', flags_string_start)
    except:
        fatal('intelpstate failed to parse /proc/cpuinfo!')

    flags_string = cpuinfo[flags_string_start:flags_string_end]
    flags = flags_string.split()
    return 'ida' in flags

##
# @brief Gets the status the driver is running in.
# @details This method exits the program with an error message if the driver is off or the status
#          is unrecognizable.
# @returns The status of the driver.
##
def get_driver_status() -> DriverStatus:
    status = read_file(pstate_file('status'))
    match status:
        case 'active\n':
            return DriverStatus.ACTIVE
        case 'passive\n':
            return DriverStatus.PASSIVE
        case 'off\n':
            fatal('intel_pstate driver is off!')
        case _:
            fatal(f'intel_pstate reported an unknown status: "{status}"!')

##
# @brief Exits the program with error messages if the user configuration has missing or unknown
#        options.
# @param config TOML configuration table (Python dictionary).
# @param status The status of the driver influences what needs to be configured.
# @param turbo  If the CPU supports turbo boosting, that also needs to be configured.
##
def validate_config_keys(config: dict[str, any], status: DriverStatus, turbo: bool) -> ():
    needed_options = { 'min-percentage', 'max-percentage' }

    if turbo:
        needed.add('turbo')
    if status == DriverStatus.ACTIVE:
        needed_options = needed_options.union({ 'energy-efficient', 'dynamic-boost' })

    config_options = set(config.keys())
    if config_options != needed_options:
        unknown = config_options.difference(needed_options)
        for option in unknown:
            warning(f'intelpstate unknown option: {option}')

        missing = needed_options.difference(config_options)
        for option in missing:
            warning(f'intelpstate missing option: {option}')

        fatal('incorrect options for intelpstate!')

##
# @brief Interprets the value of the `min-percentage` of `max-percentage` options.
# @details Exits the program with a message if the value is invalid.
# @param variable Name of the configuration variable (for a descriptive error message, if needed).
# @param pct The object in the TOML config.
# @returns The percentage value.
##
def interpret_percentage(variable: str, pct: any) -> int:
    if type(pct) == int and 0 <= pct and pct <= 100:
        return pct
    else:
        fatal(f'invalid intelpstate value {variable}. Must be an integer from 0 to 100!')

##
# @brief Interprets any config value that's supposed to be a boolean.
# @details Exits the program with a message if the value is invalid.
# @param variable Name of the configuration variable (for a descriptive error message, if needed).
# @param value The object in the TOML config.
# @returns The boolean value.
##
def interpret_boolean(variable: str, value: any) -> bool:
    if type(value) == bool:
        return value
    else:
        fatal(f'invalid intelpstate value for {variable}. Must be a boolean!')

##
# @brief Validates a configuration and, in the process, generates a
#        [PstateConfig](@ref powermodes.plugins.intelpstate.PstateConfig).
##
def generate_config(input_config: any) -> PstateConfig:
    if type(input_config) != dict:
        fatal('configuration of the intelpstate plugin must be a TOML table!')

    status = get_driver_status()
    turbo_support = can_turbo()
    validate_config_keys(input_config, status, turbo_support)

    min_pct = interpret_percentage('min-percentage', input_config['min-percentage'])
    max_pct = interpret_percentage('min-percentage', input_config['max-percentage'])
    if min_pct > max_pct:
        fatal('intelpstate\'s min-percentage can\'t be larger than max-percentage!')

    turbo = interpret_boolean('turbo', input_config['turbo']) if turbo_support else None
    energy_efficient = None
    dynamic_boost = None

    if status == DriverStatus.ACTIVE:
        energy_efficient = interpret_boolean('energy-efficent', input_config['energy-efficient'])
        dynamic_boost = interpret_boolean('dynamic-boost', input_config['dynamic-boost'])

    return PstateConfig(min_pct, max_pct, turbo, energy_efficient, dynamic_boost)


def configure(config: any) -> ():
    processed_config = generate_config(config)
    print(processed_config)

def interact() -> ():
    print('Say something and I\'ll say it louder!')
    print(input().upper())
    warning('I do nothing as of now')

