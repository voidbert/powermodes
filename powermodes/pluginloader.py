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
# @brief Loads a Python module for plugin loading purposes
# @details Some source code is injected to allow the plugin to import code from powermodes'
#          modules. In case of failure, the program is exited with an error.
# @param name The name of the plugin.
##
def __load_plugin(name: str) -> ModuleType:

    # Special error for plugins that don't exist
    path = join(plugins_dir, f'{name}.py')
    if not isfile(path):
        fatal(f'plugin {name} does not exist!')

    # Load module
    try:
        spec = spec_from_file_location(name, path)
        source = spec.loader.get_source(name)

        source = f'''
def prepare_module_imports():
    from os.path import dirname
    from sys import path
    path.insert(0, dirname(dirname(__file__)))

prepare_module_imports()

{source}
'''
        module = module_from_spec(spec)
        codeobj = compile(source, module.__spec__.origin, 'exec')
        exec(codeobj, module.__dict__)

        return module
    except Exception as e:
        print(e)
        fatal(f'failed to load Python module in "{path}"!')


##
# @brief Loads a plugin and enters its interactive mode.
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

    interact()

