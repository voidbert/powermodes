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
# @file config.py
# @package powermodes.config
# @brief Loading of configuration files.
##

from tomllib import TOMLDecodeError, load
from typing import Any, Union

from .error import Error, ErrorType, handle_error_append
from .plugin import LoadedPlugins, Plugin, wrapped_validate, wrapped_configure

##
# @brief Parsed configuration file.
# @details There's no certainty there aren't any non-table (dictionary) objects posing as
#          powermodes. See [load_config](@ref powermodes.config.load_config).
##
ParsedConfig = dict[str, Any]

##
# @brief Validated configuration file.
# @details The top-level dictionary lists powermodes (name -> content association) and each
#          powermode associates plugin names to their configuration objects. See
#          [validate](@ref powermodes.config.validate).
##
ValidatedConfig = dict[str, dict[str, Any]]

##
# @brief Loads a configuration file.
# @details [`tomllib`](https://docs.python.org/3/library/tomllib.html) is used.
# @param path Path to the configuration file.
# @return A dictionary representing the TOML configuration.
##
def load_config(path: str) -> tuple[Union[ParsedConfig, None], Union[Error, None]]:
    try:
        with open(path, 'rb') as file:
            return (load(file), None)
    except OSError:
        return (None, Error(ErrorType.ERROR, f'Failed to read config from "{path}".'))
    except TOMLDecodeError as ex:
        return (None, Error(ErrorType.ERROR, f'Failed to parse config in "{path}".' \
                                             f'Here\'s the error message:\n{str(ex)}'))

##
# @brief Removes references to a plugin in a configuration file.
# @details Used for when a plugin's configuration validation misbehaves.
# @param config Partially validated configuration (it must be certain that all powermodes are
#               dicitonaries).
# @param plugin_name Name of the plugin to consider.
# @param blacklist List of validly configured powermodes not to be removed, or `None` (default) for
#                  an empty blacklist.
##
def __remove_plugin_references(config: ValidatedConfig, plugin_name: str, \
                               blacklist: Union[list[str], None] = None) -> None:

    if blacklist is None:
        blacklist = []

    for mode, mode_config in config.items():
        for name_key in list(mode_config):
            if name_key == plugin_name and mode not in blacklist:
                del mode_config[name_key]

##
# @brief Removes all non-`dict`s from @p config.
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @param config Parsed configuration file. After calling this function, the config is transformed
#               into a [ValidatedConfig](@ref powermodes.config.ValidatedConfig).
# @returns All errors reporting non-dictionaries.
##
def __validate_remove_non_dicts(config: ParsedConfig) -> tuple[None, list[Error]]:
    errors: list[Error] = []

    for mode in list(config):
        if not isinstance(config[mode], dict):
            errors.append(Error(ErrorType.WARNING, 'Config specified invalid powermode ' \
                                                  f'"{mode}". Must be a TOML table. Ignoring it.'))
            del config[mode]

    return (None, errors)

##
# @brief Removes all empty dictionaries (power modes) from @p config.
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @param config Partially validated configuration (it must be certain that all powermodes are
#               dicitonaries).
# @param results_from_removal If any empty dicitonary may result from the removal of invalid
#                             configuration parts. Will affect the error message.
# @returns All errors reporting empty dictionaries.
##
def __validate_remove_empty_dicts(config: ValidatedConfig, results_from_removal: bool) \
    -> tuple[None, list[Error]]:

    errors: list[Error] = []

    for mode in list(config):
        if not config[mode]:
            if results_from_removal:
                errors.append(Error(ErrorType.WARNING, f'Empty powermode "{mode}", resulting ' \
                                                        'the removal of invalid configuration ' \
                                                        'parts. Ignoring it.'))
            else:
                errors.append(Error(ErrorType.WARNING, 'Config specified empty powermode ' \
                                                      f'"{mode}". Ignoring it.'))

            del config[mode]

    return (None, errors)

##
# @brief Removes all configurations for unknown plugins from @p config.
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @param config Partially validated configuration (it must be certain that all powermodes are
#               dicitonaries).
# @param plugins Loaded plugins.
# @returns A set of plugin names used in the config file, along with errors reporting unknown
#          plugins.
##
# pylint: disable=too-many-locals
def __validate_remove_unknown_plugins(config: ValidatedConfig, plugins: LoadedPlugins) \
    -> tuple[set[str], list[Error]]:

    errors: list[Error] = []
    known: set[str] = set()
    unknown: dict[str, list[str]] = {} # plugin -> list of powermodes where its defined

    for mode in config.keys():
        for plugin in config[mode].keys():
            if plugin in plugins:
                known.add(plugin)
            else:
                if plugin in unknown:
                    unknown[plugin].append(mode)
                else:
                    unknown[plugin] = [ mode ]

    for plugin, modes in unknown.items():
        modes_text = ', '.join(modes)
        errors.append(Error(ErrorType.WARNING, f'Unknown plugin {plugin} will be ignored in the ' \
                                               f'following powermodes: {modes_text}'))
        __remove_plugin_references(config, plugin)

    return (known, errors)

##
# @brief Asks plugins to validate their configs.
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @param config Partially validated configuration (it must be certain that all powermodes are
#               dicitonaries).
# @param plugins Plugins mentioned in the configuration file.
# @returns All errors reported by plugins.
##
def __validate_plugins(config: ValidatedConfig, plugins: set[Plugin]) -> \
    tuple[None, list[Error]]:

    errors: list[Error] = []

    for plugin in plugins:
        successful = handle_error_append(errors, wrapped_validate(plugin, config))


        error_modes: list[str] = \
        list(filter(lambda mode, suc=successful: mode not in suc, # type: ignore
                    # pylint: disable=line-too-long
                    filter(lambda key, name=plugin.name, cfg=config: name in cfg[key], # type: ignore
                           config.keys())))

        if len(error_modes) != 0:
            errors.append(Error(ErrorType.WARNING, f'Removing plugin {plugin.name} from the ' \
                                                    'following powermodes: ' + \
                                                    ', '.join(error_modes) + '. Plugin\'s ' \
                                                    'validate method failed.',
                                plugin.name))

        __remove_plugin_references(config, plugin.name, successful)

    return (None, errors)

##
# @brief Checks if a configuration file is valid. Modifies @p config to remove invalid parts.
# @param config Parsed configuration.
# @param plugins Loaded plugins.
# @returns Whether the configuration file is valid or not, along with configuration warnings /
#          errors.
##
def validate(config: ParsedConfig, plugins: LoadedPlugins) -> tuple[bool, list[Error]]:
    errors: list[Error] = []

    handle_error_append(errors, __validate_remove_non_dicts(config))
    handle_error_append(errors, __validate_remove_empty_dicts(config, False))
    known_plugin_names = \
        handle_error_append(errors, __validate_remove_unknown_plugins(config, plugins))
    known_plugins = set(map(plugins.__getitem__, known_plugin_names))
    handle_error_append(errors, __validate_plugins(config, known_plugins))
    handle_error_append(errors, __validate_remove_empty_dicts(config, True))

    if not config:
        errors.append(Error(ErrorType.ERROR, 'Empty configuration (this may be the result ' \
                                             'of the removal of invalid config parts).'))
        return (False, errors)
    else:
        return (True, errors)

##
# @brief Applies a power mode from a validated configuration file.
# @param mode Name of the mode to be applied
# @param config Validated configuration file.
# @param plugins Loaded plugins.
# @returns Whether the mode application was sucessful, along with reported errors.
##
def apply_mode(mode: str, config: ValidatedConfig, plugins: LoadedPlugins) -> \
    tuple[bool, list[Error]]:

    errors: list[Error] = []

    if mode not in config:
        return (False, [ Error(ErrorType.ERROR, f'Powermode {mode} not in configuration file') ])

    all_failed = True
    for plugin_name, config_obj in config[mode].items():
        successful = handle_error_append(errors,
                                         wrapped_configure(plugins[plugin_name], config_obj))

        if successful is False:
            errors.append(Error(ErrorType.WARNING, 'configure reported insuccess. You may have ' \
                                                   'ended up with a partially configured ' \
                                                   'system.', \
                                plugin_name))
        else:
            all_failed = False


    if all_failed:
        errors.append(Error(ErrorType.ERROR, f'All plugins failed to apply mode {mode}'))
        return (False, errors)
    else:
        return (True, errors)
