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
# @file intelpstate.py
# @package powermodes.plugins.intelpstate
# @brief Manage pstates on Intel processors
##

from utils import warning

def configure(config: any) -> ():
    print(f'I have just been configured with: {config}')

def interact() -> ():
    print('Say something and I\'ll say it louder!')
    print(input().upper())
    warning('I do nothing as of now')

