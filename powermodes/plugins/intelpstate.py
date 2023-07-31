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
# @brief Manage pstates on Intel processors.
##

from dataclasses import dataclass
from enum import Enum
from os.path import join, isfile, isdir
from re import search

from ..utils import fatal, warning, read_file, write_file, input_int_range, input_yesno

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
#          Unless told otherwise, member variables can be `None`, meaning that those settings won't
#          be applied.
##
@dataclass
class PstateConfig:
    ##
    # @brief Minimum frequency (as percentage of CPU spec).
    # @details Available in both active and passive modes. Cannot be `None`.
    ##
    min_percentage: int = None

    ##
    # @brief Maximum frequency (as percentage of CPU spec).
    # @details Available in both active and passive modes. Cannot be `None`.
    ##
    max_percentage: int = None

    ##
    # @brief Enable / disable turbo.
    # @details Available in both active and passive modes.
    ##
    turbo: bool = None

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
# @details Will assume no turbo support (with a warning message) in case of failure.
# @returns Whether the CPU supports Intel Dynamic Acceleration (Turbo Boost).
##
def can_turbo() -> bool:
    cpuinfo = None
    try:
        with open('/proc/cpuinfo') as file:
            cpuinfo = file.read()
    except:
        warning('failed to read /proc/cpuinfo! Assuming CPU can\'t turbo.')
        return False

    flag_match = search(r'\nflags[\s]*:', cpuinfo)
    if not flag_match:
        warning('failed to parse /proc/cpuinfo! Assuming CPU can\'t turbo.')
        return False

    flags_string_start = flag_match.span()[1]
    try:
        flags_string_end = cpuinfo.index('\n', flags_string_start)
    except:
        warning('failed to parse /proc/cpuinfo! Assuming CPU can\'t turbo.')
        return False

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
    if not isdir(pstate_file('')):
        fatal('Linux intel_pstate driver not found!')

    # Get status
    status = read_file(pstate_file('status'))
    match status:
        case 'active\n':
            return DriverStatus.ACTIVE
        case 'passive\n':
            return DriverStatus.PASSIVE
        case 'off\n':
            fatal('intel_pstate Linux driver is off!')
        case _:
            # After reading the driver's source code, this doesn't seem to be a possibility as of
            # now, but may be if more modes are added in the future.
            fatal(f'intel_pstate Linux driver reported an unknown status: "{status}"!')

    # Check if intel_pstate=per_cpu_perf_limits is enabled. This makes using this plugin
    # impossible, because needed sysfs files aren't exposed.
    if not isfile(pstate_file('min_perf_pct')) or not isfile(pstate_file('max_perf_pct')):
        fatal('Your kernel is configured with intel_pstate=per_cpu_perf_limits. '
              'The intelpstate plugin doesn\'t work under these conditions!')

##
# @brief Gets the lowest performance percentage the CPU can operate in.
# @details The program is exited with a message in case of IO errors.
# @returns The lowest performance percentage.
##
def get_lowest_performance_percent() -> int:
    file = pstate_file('min_perf_pct')

    old_min_pct = read_file(file) # Read current percentage for later.

    # Try to set percentage to 0 and see what value it gets clamped to.
    write_file(file, '0\n')
    minimum_pct = read_file(file)

    # Restore old percentage.
    write_file(file, old_min_pct)

    try:
        return int(minimum_pct)
    except:
        fatal('can\'t convert sysfs value to integer!')

##
# @brief Gets the set of options that must be present on the configuration.
# @param status The status of the driver influences what needs to be configured.
# @param turbo  If the CPU supports turbo boosting, that also needs to be configured.
##
def get_needed_config_options(status: DriverStatus, turbo: bool) -> set[str]:
    needed_options = { 'min-percentage', 'max-percentage' }

    if turbo:
        needed_options.add('turbo')
    if status == DriverStatus.ACTIVE:
        needed_options = needed_options.union({ 'energy-efficient', 'dynamic-boost' })

    return needed_options

##
# @brief Exits the program with error messages if the user configuration has missing or unknown
#        options.
# @param config TOML configuration table (Python dictionary).
# @param status The status of the driver influences what needs to be configured.
# @param turbo  If the CPU supports turbo boosting, that also needs to be configured.
##
def validate_config_keys(config: dict[str, any], status: DriverStatus, turbo: bool) -> ():
    needed_options = get_needed_config_options(status, turbo)

    config_options = set(config.keys())
    if config_options != needed_options:
        unknown = config_options.difference(needed_options)
        for option in unknown:
            warning(f'unknown option: {option}')

        missing = needed_options.difference(config_options)
        for option in missing:
            warning(f'missing option: {option}')

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
        fatal(f'invalid config value for {variable}. Must be an integer from 0 to 100!')

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
        fatal(f'invalid config value for {variable}. Must be a boolean!')

##
# @brief Validates a configuration and, in the process, generates a
#        [PstateConfig](@ref powermodes.plugins.intelpstate.PstateConfig).
##
def generate_config(input_config: any) -> PstateConfig:
    if type(input_config) != dict:
        fatal('configuration must be a TOML table!')

    status = get_driver_status()
    turbo_support = can_turbo()
    validate_config_keys(input_config, status, turbo_support)

    min_pct = interpret_percentage('min-percentage', input_config['min-percentage'])
    max_pct = interpret_percentage('min-percentage', input_config['max-percentage'])
    if min_pct > max_pct:
        fatal('min-percentage can\'t be larger than max-percentage!')

    turbo = interpret_boolean('turbo', input_config['turbo']) if turbo_support else None
    energy_efficient = None
    dynamic_boost = None

    if status == DriverStatus.ACTIVE:
        energy_efficient = interpret_boolean('energy-efficent', input_config['energy-efficient'])
        dynamic_boost = interpret_boolean('dynamic-boost', input_config['dynamic-boost'])

    return PstateConfig(min_pct, max_pct, turbo, energy_efficient, dynamic_boost)

##
# @brief Applies new performance percentages to the intel_pstate driver.
# @details This method may exit with a fatal error in case of IO errors.
# @param min Minimum performance percentage.
# @param max Maximum performance percentage.
##
def apply_percentages(min: int, max: int) -> ():
    # The intel_pstate driver clamps new performance percentages according to the old ones.
    # See https://elixir.bootlin.com/linux/latest/source/drivers/cpufreq/intel_pstate.c#L1351 and
    # https://elixir.bootlin.com/linux/latest/source/drivers/cpufreq/intel_pstate.c#L1384
    # This may make the new values be applied incorrectly (for example, when the new max
    # percentage is lower than the old min percentage). To avoid that, temporarily set the minimum
    # and maximum percentages to their minimum and maximum values.

    min_file = pstate_file('min_perf_pct')
    max_file = pstate_file('max_perf_pct')

    write_file(min_file, '0\n')
    write_file(max_file, '100\n')

    write_file(min_file, str(min) + '\n')
    write_file(max_file, str(max) + '\n')

    # Read back files to confirm if percentages were correctly applied.
    achieved_min = read_file(min_file)[:-1]
    achieved_max = read_file(max_file)[:-1]

    if achieved_min != str(min):
        warning(f'failed to apply min-percentage: clamped to {achieved_min}!')
    if achieved_max != str(max):
        warning(f'failed to apply max-percentage: clamped to {achieved_max}!')

##
# @brief Applies boolean values to the intel_pstate driver.
# @details This method may exit with a fatal error in case of IO errors.
# @param file The file to write to in the intel_pstate sysfs directory (for example, `'turbo'`).
# @param value The value to be written to file. May be `None` for no writes to happen.
##
def apply_boolean(file: str, value: bool) -> ():
    if value is not None:
        write_file(pstate_file(file), str(int(value)) + '\n')

##
# @brief Applies a configuration.
# @param config The configuration to apply.
##
def apply_config(config: PstateConfig) -> ():
    apply_percentages(config.min_percentage, config.max_percentage)
    apply_boolean('no_turbo', not config.turbo if config.turbo is not None else None)
    apply_boolean('energy_efficiency', config.energy_efficient)
    apply_boolean('hwp_dynamic_boost', config.dynamic_boost)

##
# @brief Function that gets called to apply a configuration to the plugin.
# @param config Parsed TOML configuration.
##
def configure(config: any) -> ():
    processed_config = generate_config(config)
    apply_config(processed_config)

def interact() -> ():
    status = get_driver_status()
    turbo_support = can_turbo()
    lowest_pct = get_lowest_performance_percent()

    # Print configuration helper
    needed_options = list(get_needed_config_options(status, turbo_support))
    print('When configuring the intelpstate plugin, you need the following options:')

    needed_options_str = ""
    for i in range(0, len(needed_options)):
        if i == len(needed_options) - 1:
            needed_options_str += needed_options[i] + '\n'
        else:
            needed_options_str += needed_options[i] + ', '
    print(needed_options_str)

    # Get user options
    print(f'Minimum performance percentage ({lowest_pct} - 100):')
    min_pct = input_int_range(range(lowest_pct, 101))
    print(f'Maximum performance percentage ({min_pct} - 100):')
    max_pct = input_int_range(range(min_pct, 101))

    turbo = None
    energy_efficient = None
    dynamic_boost = None

    if turbo_support:
        print('Enable turbo?')
        turbo = input_yesno()
    if status == DriverStatus.ACTIVE:
        print('Enable energy efficient optimizations?')
        energy_efficient = input_yesno()
        print('Enable dynamic boost (increase frequency when IO is happening)?')
        dynamic_boost = input_yesno()

    config = PstateConfig(min_pct, max_pct, turbo, energy_efficient, dynamic_boost)
    apply_config(config)


