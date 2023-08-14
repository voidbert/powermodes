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

from copy import deepcopy
from tomllib import TOMLDecodeError, load
from traceback import format_exception
from typing import Any, Union

from .error import Error, ErrorType, handle_error_append, set_unspecified_origins
from .plugin import Plugin, valid_plugin_validate_return, valid_plugin_configure_return

##
# @brief Loads a configuration file.
# @details [`tomllib`](https://docs.python.org/3/library/tomllib.html) is used.
# @param path Path to the configuration file.
# @return A dictionary representing the TOML configuration.
##
def load_config(path: str) -> tuple[Union[dict[str, Any], None], Union[Error, None]]:
    try:
        with open(path, 'rb') as file:
            return (load(file), None)
    except OSError:
        return (None, Error(ErrorType.ERROR, f'Failed to read config from "{path}".'))
    except TOMLDecodeError as ex:
        return (None, Error(ErrorType.ERROR, f'Failed to parse config in "{path}".' \
                                             f'Here\'s the error message:\n{str(ex)}'))

##
# @brief Removes configuration elements that do not belong to the specified plugin.
# @details The configuration is deep-copied, so that plugins can't mess it up.
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)).
# @param plugin_name Name of the plugin to consider.
# @returns The filtered and copied configuration.
##
def __filter_config_for_plugin(config: dict[str, Any], plugin_name: str) -> dict[str, Any]:
    copy = deepcopy(config)

    for mode in list(config):
        for name_key in list(config[mode]):
            if name_key != plugin_name:
                del copy[mode][name_key]

    return copy

##
# @brief Removes references to a plugin in a configuration file.
# @details Auxiliary function for [validate](@ref powermodes.config.validate). Used for when a
#          plugin's configuration validation misbehaves.
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)).
# @param plugin_name Name of the plugin to consider.
# @param blacklist List of validly configured powermodes not to be removed.
##
def __remove_plugin_references(config: dict[str, Any], plugin_name: str, \
                               blacklist: Union[list[str], None] = None) -> None:

    if blacklist is None:
        blacklist = []

    for mode, mode_config in config.items():
        for name_key in list(mode_config):
            if name_key == plugin_name and mode not in blacklist:
                del mode_config[name_key]

##
# @brief Checks if a configuration file is empty (no plugin configurations).
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @returns Whether a configuration file is empty (no plugin configurations).
##
def __is_config_empty(config: dict[str, Any]) -> bool:
    if not config:
        return True
    else:
        return all(map(lambda dict: not bool(dict), config.values()))

##
# @brief Removes all non-`dict`s from @p config.
# @details Auxiliary function for [validate](@ref powermodes.config.validate).
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)). Will
#               be modified.
# @returns All errors reporting non-dictionaries.
##
def __validate_remove_non_dicts(config: dict[str, Any]) -> tuple[None, list[Error]]:
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
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)). Will
#               be modified.
# @param results_from_removal If any empty dicitonary may result from the removal of invalid
#                             configuration parts. Will affect the error message.
# @returns All errors reporting empty dictionaries.
##
def __validate_remove_empty_dicts(config: dict[str, Any], results_from_removal: bool) \
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
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)). Will
#               be modified.
# @param plugins List of loaded plugins (see [load_plugins](@reg powermodes.plugins.load_plugins)).
# @returns A set of plugins used in the config file, along with errors reporting unknown plugins.
##
# pylint: disable=too-many-locals
def __validate_remove_unknown_plugins(config: dict[str, Any], plugins: list[Plugin]) \
    -> tuple[set[str], list[Error]]:

    errors: list[Error] = []
    known: set[str] = set()
    unknown: dict[str, list[str]] = {} # plugin -> list of powermodes where its defined

    for mode in config.keys():
        for plugin in config[mode].keys():
            if plugin in map(lambda p: p.name, plugins):
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
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)). Will
#               be modified.
# @param plugins List of loaded plugins (see [load_plugins](@reg powermodes.plugins.load_plugins)).
# @returns All errors reported by plugins.
##
# pylint: disable=too-many-locals
def __validate_plugins(config: dict[str, Any], plugins: set[Plugin]) -> tuple[None, list[Error]]:
    errors: list[Error] = []

    # Plugin verification
    for plugin in plugins:
        filtered = __filter_config_for_plugin(config, plugin.name)
        try:
            plugin_return = plugin.validate(filtered)
            if valid_plugin_validate_return(plugin_return):
                successful, plugin_errors = plugin_return
                set_unspecified_origins(plugin_errors, plugin.name)
                errors.extend(plugin_errors)

                __remove_plugin_references(config, plugin.name, successful)
            else:
                errors.append(Error(ErrorType.WARNING, 'validate returned an invalid value: ' \
                                                      f'{plugin_return}. Ignoring this plugin.',
                                    plugin.name))
                __remove_plugin_references(config, plugin.name)

        # Needed pylint suppression because a module can throw any type of error
        # pylint: disable=broad-exception-caught
        except BaseException as ex:
            exception_text = ''.join(format_exception(ex))
            errors.append(Error(ErrorType.WARNING, f'Calling validate resulted in an exception. ' \
                                                    'Ignoring that plugin. Here\'s the ' \
                                                   f'exception:\n{exception_text}',
                                plugin.name))

            __remove_plugin_references(config, plugin.name)

    return (None, errors)

##
# @brief Checks if a configuration file is valid. Modifies @p config to remove invalid parts.
# @param config Loaded configuration (see [load_config](@ref powermodes.config.load_config)).
# @param plugins List of loaded plugins (see [load_plugins](@reg powermodes.plugins.load_plugins)).
# @returns Whether the configuration file is valid or not, along with configuration warnings /
#          errors.
##
def validate(config: dict[str, Any], plugins: list[Plugin]) -> tuple[bool, list[Error]]:
    errors: list[Error] = []

    handle_error_append(errors, __validate_remove_non_dicts(config))
    handle_error_append(errors, __validate_remove_empty_dicts(config, False))
    known_plugin_names = \
        handle_error_append(errors, __validate_remove_unknown_plugins(config, plugins))
    known_plugins = set(filter(lambda plug: plug.name in known_plugin_names, plugins))
    handle_error_append(errors, __validate_plugins(config, known_plugins))
    handle_error_append(errors, __validate_remove_empty_dicts(config, True))

    if __is_config_empty(config):
        errors.append(Error(ErrorType.ERROR, 'Empty configuration (this may be the result ' \
                                             'of the removal of invalid config parts).'))
        return (False, errors)
    else:
        return (True, errors)

##
# @brief Applies a power mode from a validated configuration file.
# @param mode Name of the mode to be applied
# @param config Validated (see [validate](@ref powermodes.config.validate)) configuration file.
# @param plugins List of loaded plugins (see [load_plugins](@reg powermodes.plugins.load_plugins)).
# @returns Whether the mode application was sucessful, along with reported errors.
##
# pylint: disable=too-many-branches
def apply_mode(mode: str, config: dict[str, dict[str, Any]], plugins: list[Plugin]) -> \
    tuple[bool, list[Error]]:

    errors: list[Error] = []

    if mode not in config:
        return (False, [ Error(ErrorType.ERROR, f'Powermode {mode} not in configuration file') ])

    all_failed = True
    for plugin_name in config[mode]: # Unknown plugins should already have been removed
        plugin = next(filter(lambda p, name=plugin_name: p.name == name, plugins)) # type: ignore
        try:
            plugin_return = plugin.configure(config[mode][plugin_name])
            if valid_plugin_configure_return(plugin_return):
                successful, plugin_errors = plugin_return
                set_unspecified_origins(plugin_errors, plugin.name)
                errors.extend(plugin_errors)

                if not successful:
                    errors.append(Error(ErrorType.WARNING, 'configure reported insuccess. ' \
                                                           'You may have ended up with a ' \
                                                           'partially configured system.', \
                                        plugin.name))
                else:
                    all_failed = False
            else:
                errors.append(Error(ErrorType.WARNING, 'configure returned an invalid value: ' \
                                                      f'{plugin_return}. Unable to report any ' \
                                                       'error / warning from this plugin. You ' \
                                                       'may have ended up with a partially ' \
                                                       'configured system.', plugin.name))

        # Needed pylint suppression because a module can throw any type of error
        # pylint: disable=broad-exception-caught
        except BaseException as ex:
            exception_text = ''.join(format_exception(ex))
            errors.append(Error(ErrorType.WARNING, f'Calling configure resulted in an ' \
                                                    'exception. You may have ended up with a ' \
                                                    'partially configured system. Here\'s the ' \
                                                   f'exception:\n{exception_text}',
                                plugin.name))

    if all_failed:
        errors.append(Error(ErrorType.ERROR, f'All plugins failed to apply mode {mode}'))
        return (False, errors)
    else:
        return (True, errors)
