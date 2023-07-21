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
# @brief Loading and listing of plugins
##

from os import listdir
from os.path import dirname, realpath, isfile, join
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from types import ModuleType

from .utils import fatal

##
# @brief The directory that contains the plugins
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
        fatal('failed to list plugins')

##
# @brief Loads and returns a Python module.
##
def __load_module(name: str) -> ModuleType:
    try:
        path = join(plugins_dir, f'{name}.py')
        if not isfile(path):
            fatal(f'plugin {name} does not exist!')

        spec = spec_from_file_location(name, path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        return module
    except Exception as e:
        print(e)
        fatal(f'failed to load module {name}!')

##
# @brief Loads a plugin and enters its interactive mode.
##
def plugin_interact(name: str) -> ():
    __load_module(name).interact()

