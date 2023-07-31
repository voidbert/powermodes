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
# @file pluginloader.py
# @package powermodes.pluginloader
# @brief Loading and listing of plugins.
##

from os import listdir
from os.path import dirname, realpath, isfile, join
from pathlib import Path
from textwrap import dedent

from importlib import import_module
from types import ModuleType

from .utils import fatal, set_running_plugin

##
# @brief The directory that contains the plugins.
##
plugins_dir = join(dirname(realpath(__file__)), 'plugins')

##
# @brief Lists all plugins installed.
# @returns The list of plugin names.
##
def list_plugins() -> list[str]:
    try:
        files = listdir(plugins_dir)
        plugins = []

        for file in files:
            path = join(plugins_dir, file)

            # Plugins are Python scripts other than __init__.py
            if isfile(path) and path.endswith('.py') and not path.endswith('__init__.py'):
                name = Path(path).stem
                plugins.append(name)

        return plugins
    except:
        fatal('failed to list plugins!')

##
# @brief Loads a Python module for plugin loading purposes.
# @details Some source code is injected to allow the plugin to import code from powermodes'
#          modules. In case of failure, the program is exited with an error and a message.
# @param name The name of the plugin.
# @returns The Python module object.
##
def __load_plugin(name: str) -> ModuleType:

    # Special error for plugins that don't exist
    path = join(plugins_dir, f'{name}.py')
    if not isfile(path):
        fatal(f'plugin {name} does not exist!')

    # Load module
    try:
        module = import_module('powermodes.plugins.' + name)
        return module
    except Exception as e:
        print(e)
        fatal(f'failed to load Python module in "{path}"!')


##
# @brief Loads a plugin and enters its interactive mode.
# @details In case of failure, the program is exited with an error message.
# @param name The name of the plugin.
##
def plugin_interact(name: str) -> ():
    module = __load_plugin(name)

    # Check for interact() before calling it
    interact = None
    try:
        interact = getattr(module, 'interact')
        if not callable(interact):
            raise Exception()
    except:
        fatal(f'module {name} doesn\'t support interaction')

    set_running_plugin(name)
    interact()
    set_running_plugin(None)

##
# @brief Loads a plugin and configures it.
# @details In case of failure, the program is exited with an error message.
# @param name The name of the plugin.
# @param config The object to configure the plugin with (for the `configure` method).
##
def plugin_configure(name: str, config: any) -> ():
    module = __load_plugin(name)

    # Check for configure() before calling it
    configure = None
    try:
        configure = getattr(module, 'configure')
        if not callable(configure):
            raise Exception()
    except:
        fatal(f'module {name} doesn\'t support configuration')

    set_running_plugin(name)
    configure(config)
    set_running_plugin(None)

