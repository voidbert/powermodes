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
# @file plugin.py
# @package powermodes.plugin
# @brief Plugin loading and tooling.
##

from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from inspect import signature
from pathlib import Path
from traceback import format_exception
from typing import Any, Callable, Union

from .error import Error, ErrorType, handle_error_append, set_unspecified_origins

##
# @brief See [config.ValidatedConfig](@ref powermodes.config.ValidatedConfig).
# @details Needed to avoid cyclical imports.
##
ValidatedConfig = dict[str, dict[str, Any]]

##
# @brief Path to directory that contains the plugins.
##
__plugins_dir = Path(__file__).parent.joinpath('plugins')

##
# @brief They type of a plugin.
##
@dataclass(frozen=True)
class Plugin:
    file: str    = '' ##< @brief The Python file containing the plugin (excludes directory).

    name: str    = '' ##< @brief Name of the plugin.
    version: str = '' ##< @brief Version of the plugin.

    ##
    # @brief Method called to validate the configuration file.
    # @details Takes in the parsed configuration file (filtered to only show configurations for the
    #          plugin), and returns the list of validly configured powermodes, along with all
    #          errors reported.
    ##
    validate: Callable[[dict[str, Any]], tuple[list[str], list[Error]]] = lambda _: ([], [])

    ##
    # @brief Method called to apply a configuration.
    # @details Takes in the configuration object for the plugin, for the powermode to be applied.
    #          Returns whether the application was successful, along with reported errors and
    #          warnings.
    ##
    configure: Callable[[Any], tuple[bool, list[Error]]] = lambda _: (False, [])

##
# @brief Dictionary associating plugin names (self-reported `NAME`s) with plugins.
# @details See [load_plugins](@reg powermodes.plugins.load_plugins).
##
LoadedPlugins = dict[str, Plugin]

##
# @brief Checks if the value returned by a plugin's `validate` method is valid.
# @param Value returned by the `validate` method.
# @returns Whether the value returned by a plugin's `validate` method is valid.
##
def __valid_plugin_validate_return(obj: Any) -> bool:
    if not isinstance(obj, tuple):
        return False
    if len(obj) != 2:
        return False

    if not isinstance(obj[0], list) or not isinstance(obj[1], list):
        return False

    if not all(map(lambda e: isinstance(e, str), obj[0])):
        return False
    if not all(map(lambda e: isinstance(e, Error), obj[1])):
        return False

    return True

##
# @brief Checks if the value returned by a plugin's `configure` method is valid.
# @param Value returned by the `configre` method.
# @returns Whether the value returned by a plugin's `configure` method is valid.
##
def __valid_plugin_configure_return(obj: Any) -> bool:
    if not isinstance(obj, tuple):
        return False
    if len(obj) != 2:
        return False

    if not isinstance(obj[0], bool):
        return False

    if not isinstance(obj[1], list):
        return False
    if not all(map(lambda e: isinstance(e, Error), obj[1])):
        return False

    return True

##
# @brief Removes configuration objects that do not belong to the specified plugin.
# @details The configuration is deep-copied, so that plugins can't mess it up.
# @param config Partially validated configuration (it must be certain that all powermodes are
#               dicitonaries).
# @param plugin_name Name of the plugin to consider.
# @returns The filtered and copied configuration.
##
def __filter_config_for_plugin(config: ValidatedConfig, plugin_name: str) -> ValidatedConfig:
    copy = deepcopy(config)

    for mode in list(config):
        for name_key in list(config[mode]):
            if name_key != plugin_name:
                del copy[mode][name_key]

    return copy

##
# @brief Wrapper around a plugin's `validate`.
# @details
# Calls the plugin's `validate`, but makes sure of the following:
# - @p config is copied and filtered to contain information only about this plugin, before
#   being used as an argument of `validate`;
# - Any exception coming from the plugin is handled and transformed into an error;
# - If the plugin returns an object of an unexpected type, an error is reported;
# - Plugin's errors without a specified origin have it set to the plugin's name.
# @param plugin Plugin to validate @p config with.
# @param config Validated configuration file.
# @returns The same as the `validate` method, or `[]` if errors happened.
##
def wrapped_validate(plugin: Plugin, config: ValidatedConfig) -> tuple[list[str], list[Error]]:
    filtered = __filter_config_for_plugin(config, plugin.name)

    try:
        plugin_return = plugin.validate(filtered)
        if __valid_plugin_validate_return(plugin_return):
            successful, plugin_errors = plugin_return
            set_unspecified_origins(plugin_errors, plugin.name)

            return (successful, plugin_errors)
        else:
            return ([], [ Error(ErrorType.WARNING, 'validate returned an invalid value: ' \
                                                  f'{plugin_return}. Unable to report any error ' \
                                                   '/ warning from this plugin. Ignoring it.',
                              plugin.name) ])

    # Needed pylint suppression because a module can throw any type of error
    # pylint: disable=broad-exception-caught
    except BaseException as ex:
        exception_text = ''.join(format_exception(ex))
        return ([], [ Error(ErrorType.WARNING, f'Calling validate resulted in an exception. ' \
                                                'Ignoring that plugin. Unable to report any ' \
                                                'other error / warning from this plugin. ' \
                                               f'Here\'s the exception:\n{exception_text}',
                          plugin.name) ])

##
# @brief Wrapper around a plugin's `configure`.
# @details
# Calls the plugin's `configure`, but makes sure of the following:
# - Any exception coming from the plugin is handled and transformed into an error;
# - If the plugin returns an object of an unexpected type, an error is reported;
# - Plugin's errors without a specified origin have it set to the plugin's name.
# @param plugin Plugin to validate @p config with.
# @param obj Configuration object plugin for the plugin.
# @returns The same as the `configure` method, or `None` if errors happened.
##
def wrapped_configure(plugin: Plugin, obj: Any) -> tuple[Union[bool, None], list[Error]]:
    try:
        plugin_return = plugin.configure(obj)
        if __valid_plugin_configure_return(plugin_return):
            success, plugin_errors = plugin_return
            set_unspecified_origins(plugin_errors, plugin.name)
            return (success, plugin_errors)
        else:
            return (None, [ Error(ErrorType.WARNING, 'configure returned an invalid value: ' \
                                                    f'{plugin_return}. Unable to report any ' \
                                                     'error / warning from this plugin. You ' \
                                                     'may have ended up with a partially ' \
                                                     'configured system.', plugin.name) ])

    # Needed pylint suppression because a module can throw any type of error
    # pylint: disable=broad-exception-caught
    except BaseException as ex:
        exception_text = ''.join(format_exception(ex))
        return (None, [ Error(ErrorType.WARNING, f'Calling configure resulted in an ' \
                                                  'exception. You may have ended up with a ' \
                                                  'partially configured system. Unable to ' \
                                                  'report any other error / warning from this ' \
                                                  'plugin. Here\'s the exception:\n' \
                                                 f'{exception_text}', \
                             plugin.name) ])

##
# @brief Gets a list of all the names of plugin Python modules.
# @returns A list of all names of plugin Python modules (`None` on failure). Errors and warnings
#          can also be returned.
##
def list_plugin_module_names() -> tuple[Union[list[str], None], list[Error]]:

    def is_plugin(path: Path) -> bool:
        return path.suffix == '.py' and not path.stem.startswith('__')

    try:
        file_paths = Path(__plugins_dir).iterdir()
        plugin_paths = filter(is_plugin, file_paths)
        names = map(lambda p: p.stem, plugin_paths)
    except OSError:
        return (None, [ Error(ErrorType.ERROR, 'Failed to list plugins.') ])

    warnings = []
    valid_names = []
    for name in names:
        if name.isidentifier():
            valid_names.append(name)
        else:
            warnings.append(Error(ErrorType.WARNING, f'Plugin in "{name}.py" has an invalid ' \
                                                      'module name (must be a Python ' \
                                                      'identifier). Ignoring it.'))

    return (valid_names, warnings)

##
# @brief Loads a plugin from its module name.
# @param module_name Name of the Python module of the plugin.
# @returns The loaded [Plugin](@ref powermodes.plugin.Plugin), or `None` when an error happens.
##
def load_plugin(module_name: str) -> tuple[Union[Plugin, None], list[Error]]:
    try:
        module = import_module('.plugins.' + module_name, package='powermodes')
    # Needed pylint suppression because a module can throw any type of error
    # pylint: disable=broad-exception-caught
    except BaseException as ex:
        exception_text = ''.join(format_exception(ex))
        return (None, [ Error(ErrorType.WARNING, f'Failed to load plugin in "{module_name}.py". ' \
                                                 f'Here\'s the cause:\n{exception_text}' )])

    # Module validity verification

    errors = []
    if not hasattr(module, 'NAME') or not isinstance(module.NAME, str):
        errors.append(Error(ErrorType.WARNING, f'Plugin in "{module_name}.py" reported no NAME ' \
                                                '/ non-string NAME. Defaulting to ' \
                                               f'"{module_name}".'))

        module.NAME = module_name # type: ignore

    if not hasattr(module, 'VERSION') or not isinstance(module.VERSION, str):
        errors.append(Error(ErrorType.WARNING, 'No VERSION specified / non-string VERSION. ' \
                                               'Defaulting to "unknown".', module.NAME))

        module.VERSION = 'unknown' # type: ignore

    if not hasattr(module, 'validate'):
        errors.append(Error(ErrorType.WARNING, 'No validate method specified. Ignoring this ' \
                                               'plugin.', module.NAME))
        return (None, errors)

    elif not callable(module.validate) or len(signature(module.validate).parameters) != 1:

        errors.append(Error(ErrorType.WARNING, 'validate must be a method that takes in a ' \
                                               'single argument. Considering all config files ' \
                                               'to be invalid.', \
                            module.NAME))

    if not hasattr(module, 'configure'):
        errors.append(Error(ErrorType.WARNING, 'No configure method specified. Skipping ' \
                                               'invalid plugin.', module.NAME))
        return (None, errors)

    elif not callable(module.configure) or len(signature(module.configure).parameters) != 1:
        errors.append(Error(ErrorType.WARNING, 'configure must be a method that takes in a ' \
                                               'single argument. Ignoring this plugin.', \
                            module.NAME))


        return (None, errors)

    return (Plugin(module_name + '.py',
                   module.NAME, module.VERSION, module.validate, module.configure), errors)

##
# @brief Loads all plugins.
# @returns See [LoadedPlugins](@ref powermodes.plugin.LoadedPlugins).
##
def load_plugins() -> tuple[Union[LoadedPlugins, None], list[Error]]:
    plugin_module_names, errors = list_plugin_module_names()
    if plugin_module_names is None:
        return (None, errors)

    plugins: dict[str, Plugin] = {}
    for name in plugin_module_names:
        plug = handle_error_append(errors, load_plugin(name))
        if plug is not None:
            if plug.name not in plugins:
                plugins[plug.name] = plug
            else:
                errors.append(Error(ErrorType.WARNING, f'Plugins in "{plugins[plug.name].file}" ' \
                                                       f'and "{plug.file}" have reported the ' \
                                                       f'same name, "{plug.name}". Ignoring ' \
                                                       f'"{plug.file}"'))

    return (plugins, errors)
