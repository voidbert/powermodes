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
# @file configloader.py
# @package powermodes.configloader
# @brief Loading and processing of configuration files.
##

import tomllib

from .utils import fatal

##
# @brief Loads a configuration file.
# @details May leave the program in case of a fatal error.
# @param path The path to the file.
##
def load_config(path: str) -> dict[str, any]:
    try:
        with open(path, 'rb') as file:
            return tomllib.load(file)
    except Exception as e:
        fatal(e)
        fatal(f'failed to load config from "{path}"!')

##
# @brief Converts a command-line argument to a configuration object to be used by a plugin.
# @details The argument must be a valid TOML value (to the right of the equal sign)
# @details Will leave the program in case of an error.
# @param arg The command-line argument
##
def load_args_config(arg: str) -> any:
    toml = f'property = {arg}'
    try:
        return tomllib.loads(toml)['property']
    except:
        fatal(f'failed to parse TOML plugin config argument!')

##
# @brief Lists all modes in a loaded configuration.
# @returns A list of mode names.
##
def list_modes(config: dict[str, any]) -> list[str]:
    return list(config.keys())

