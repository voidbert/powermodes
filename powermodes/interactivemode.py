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
# @file interactivemode.py
# @package powermodes.interactivemode
# @brief User interaction to configure plugins / power modes.
##

from enum import Enum

from .configloader import load_config, list_modes, apply_mode
from .pluginloader import list_plugins, plugin_interact
from .utils import choose_from

##
# @enum ModeOrPlugin
# @brief Whether the user will choose a power mode or configure a plugin.
##
class ModeOrPlugin(Enum):
    MODE = 1   ##< @brief The user will apply a power mode
    PLUGIN = 2 ##< @brief The user will configure a plugin

##
# @brief Starts the interactive mode
# @param config_path Path to the configuration file. May be `None` for no power mode options.
##
def interactive_mode(config_path: str) -> ():
    config = load_config(config_path) if config_path is not None else None

    while True:
        action = None
        if config_path is None:
            action = ModeOrPlugin.PLUGIN
        else:
            print('Choose an action:')
            action = choose_from([ ModeOrPlugin.MODE,  ModeOrPlugin.PLUGIN ],
                                 [ 'Apply power mode', 'Configure plugin'  ])

        if action == ModeOrPlugin.MODE:
            modes = list_modes(config)
            if len(modes) == 0:
                print('No modes available!')
            else:
                print('Choose a mode to apply:')
                mode = choose_from(modes, modes)
                apply_mode(config, mode)
        else:
            plugins = list_plugins()
            if len(plugins) == 0:
                print('No plugins available!')
            else:
                print('Choose a plugin to configure:')
                plugin = choose_from(plugins, plugins)
                plugin_interact(plugin)

        print('') # For spacing

