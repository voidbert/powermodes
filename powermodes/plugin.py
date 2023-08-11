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

from dataclasses import dataclass
from importlib import import_module
from inspect import signature
from pathlib import Path
from traceback import format_exception
from typing import Any, Callable, Union

from .error import Error, ErrorType, handle_error_append

##
# @brief Path to directory that contains the plugins.
##
__plugins_dir = Path(__file__).parent.joinpath('plugins')

##
# @brief They type of a plugin.
##
@dataclass
class Plugin:
    name: str    = '' ##< @brief Name of the plugin.
    version: str = '' ##< @brief Version of the plugin.

    ##
    # @brief Method called to validate the configuration file.
    # @details Takes in the whole configuration file and returns whether the configuration is
    #          valid, along with reported errors and warnings.
    ##
    validate: Callable[[dict[str, Any]], tuple[bool, list[Error]]] = lambda _: (True, [])

    ##
    # @brief Method called to apply a configuration.
    # @details Takes in the configuration object for the plugin, for the powermode to be applied.
    #          Returns whether the application was successful, along with reported errors and
    #          warnings.
    ##
    configure: Callable[[Any], tuple[bool, list[Error]]] = lambda _: (False, [])

##
# @brief Gets a list of all the names of plugin Python modules.
# @returns A list of all names of plugin Python modules (`None` on failure). Errors and warnings
#          can also be returned.
##
def list_plugin_module_names() -> tuple[Union[list[str] | None], list[Error]]:

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
            warnings.append(Error(ErrorType.WARNING, f'Plugin "{name}" has invalid name (must ' \
                                                      'be an identifier). Ignoring it.'))

    return (valid_names, warnings)

##
# @brief Loads a plugin from its name.
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
        errors.append(Error(ErrorType.WARNING, 'No validate method specified. Assuming all ' \
                                               'config files are valid.', module.NAME))
        module.validate = lambda _: True # type: ignore

    elif not callable(module.validate) or len(signature(module.validate).parameters) != 1:

        errors.append(Error(ErrorType.WARNING, 'validate must be a method that takes in a ' \
                                               'single argument. Considering all config files ' \
                                               'to be valid.', \
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

    return (Plugin(module.NAME, module.VERSION, module.validate, module.configure), errors)

##
# @brief Loads all plugins.
# @returns A list of [Plugin](@ref powermodes.plugin.Plugin)s. Errors and warnings are also
#          returned.
##
def load_plugins() -> tuple[Union[list[Plugin], None], list[Error]]:
    plugin_names, errors = list_plugin_module_names()
    if plugin_names is None:
        return (None, errors)

    plugins = []
    for name in plugin_names:
        plug = handle_error_append(errors, load_plugin(name))
        if plug is not None:
            plugins.append(plug)

    return (plugins, errors)
