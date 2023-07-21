#!/usr/bin/env python3

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
# @file main.py
# @package powermodes.main
# @brief Contains the entry point to program.
##

from enum import Enum
from argparse import ArgumentParser, Namespace
from importlib.metadata import version
from os import getuid

from .utils import fatal, warning
from .pluginloader import list_plugins, plugin_interact

##
# @enum ArgumentsActionType
# @brief Action to be performed after parsing command-line arguments.
##
class ArgumentsActionType(Enum):
    CONFIG_PLUGIN_ARGS        = 1 ##< @brief Configure a plugin from command-line arguments.
    LIST_PLUGINS              = 2 ##< @brief List installed plugins.

    APPLY_MODE                = 3 ##< @brief Apply power mode in the configuration file.
    LIST_MODES                = 4 ##< @brief List power modes in the configuration file.

    INTERACTIVE_MODE          = 5 ##< @brief Interactively configure power modes / plugins.
    PLUGIN_INTERACTIVE_MODE   = 6 ##< @brief Configure a single plugin interactively.
    PLUGINS_INTERACTIVE_MODE  = 7 ##< @brief Interactively configure plugins (config file not
                                  #          provided).

##
# @brief Parses command-line arguments.
# @returns A `argparse.Namespace` with the following keys:
#            - `config`:       path to configuration file;
#
#            - `mode`:         power mode to be activated;
#            - `list_modes`:   if the user wants to list power modes;
#
#            - `plugin`:       plugin to be configured;
#            - `plugin_args`:  arguments for the plugin to be configured;
#            - `list_plugins`: if the user wants to list installed plugins.
##
def parse_arguments() -> Namespace:
    parser = ArgumentParser(prog='powermodes',
                            description='Laptop power consumption manager',
                            epilog='If nothing / only CONFIG is specified, the interactive mode '
                                   'will be enabled.',
                            usage='powermodes [options]')

    try:
        powermodes_version = version('powermodes')
    except:
        powermodes_version = 'Unknown version'

    parser.add_argument('-v', '--version', action='version', version=powermodes_version)
    parser.add_argument('-c', '--config', help='specify path to configuration file')

    parser.add_argument('-p', '--plugin', help='configure installed PLUGIN.')
    parser.add_argument('--plugin-args',
                        help='arguments for PLUGIN (instead of interactive config)')
    parser.add_argument('--list-plugins', action='store_true', help='list installed plugins')

    parser.add_argument('-m', '--mode', help='apply power MODE')
    parser.add_argument('--list-modes', action='store_true', help='list power modes')

    return parser.parse_args()

##
# @brief Validates and interprets command line arguments.
# @details Exits with a message in case of error.
# @returns The action the user wants to perform.
##
def analyze_arguments(args: Namespace) -> ArgumentsActionType:

    # Determine action
    action_type: ArgumentsActionType = None
    args_dict: dict = vars(args)

    for var in ['plugin', 'list_plugins', 'mode', 'list_modes']:
        if args_dict[var]:
            if action_type is not None:
                fatal('multiple actions specified!')
            else:
                action_type = {
                    'plugin': ArgumentsActionType.PLUGIN_INTERACTIVE_MODE,
                    'list_plugins': ArgumentsActionType.LIST_PLUGINS,
                    'mode': ArgumentsActionType.APPLY_MODE,
                    'list_modes': ArgumentsActionType.LIST_MODES,
                }[var]

    if action_type is None:
        if args.config is None:
            action_type = ArgumentsActionType.PLUGINS_INTERACTIVE_MODE
            warning('no config file provided. Only plugin configuration available!')
        else:
            action_type = ArgumentsActionType.INTERACTIVE_MODE

    elif action_type == ArgumentsActionType.PLUGIN_INTERACTIVE_MODE and \
            args.plugin_args is not None:
        action_type = ArgumentsActionType.CONFIG_PLUGIN_ARGS

    # Configuration requirement
    if action_type in [ ArgumentsActionType.APPLY_MODE, ArgumentsActionType.LIST_MODES ] and \
       args.config is None:
        fatal('a config file needs to be specified for this action!')

    # Warnings for excessive arguments
    if args.config is not None and action_type in [ ArgumentsActionType.CONFIG_PLUGIN_ARGS,
                                                    ArgumentsActionType.LIST_PLUGINS,
                                                    ArgumentsActionType.PLUGIN_INTERACTIVE_MODE ]:
        warning('unnecessary config file specified!')

    if args.plugin_args is not None and action_type != ArgumentsActionType.CONFIG_PLUGIN_ARGS:
        warning('unnecessary plugin args specified!')

    return action_type

##
# @brief Leaves the program if the current user isn't root.
# @details An error message is printed to stderr.
##
def assert_root() -> ():
    if getuid() != 0:
        fatal('powermodes must be run as root')

##
# @brief The entry point to powermodes.
##
def main() -> ():
    args = parse_arguments()
    action = analyze_arguments(args)

    if action not in [ ArgumentsActionType.LIST_PLUGINS, ArgumentsActionType.LIST_MODES ]:
        assert_root()

    if action == ArgumentsActionType.LIST_PLUGINS:
        for plugin in list_plugins():
            print(plugin)
    elif action == ArgumentsActionType.PLUGIN_INTERACTIVE_MODE:
        plugin_interact(args.plugin)
    else:
        fatal('feature not implemented')

if __name__ == '__main__':
    main()

