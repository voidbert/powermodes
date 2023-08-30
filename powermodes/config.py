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

"""
powermodes.config
=================

Methods for loading and validating configuration files, along with helper methods for plugins.

Configuration files are described in the `project's README <../../../README.md>`_. In this module,
powermodes developers are likely interested in :func:`load_config`, :func:`validate_config` and
:func:`apply_mode`. Plugin developers may be interested in :func:`plugin_is_in_all_powermodes`
and :func:`iterate_config`.

Module contents
^^^^^^^^^^^^^^^
"""

from collections.abc import Generator
from tomllib import TOMLDecodeError, load
from typing import Any, Optional

from .error import Error, ErrorType, handle_error_append
from .plugin import LoadedPlugins, Plugin, wrapped_validate, wrapped_configure

ParsedConfig = dict[str, Any]
"""Alias for a configuration file that has been parsed, but not yet validated. There is no
certainty that children of the root TOML object (powermodes) are dictionaries.
"""

ValidatedConfig = dict[str, dict[str, Any]]
"""Alias for a configuration file that has been parsed and at least partially validated, and it is
certain that all powermodes are dictionaries.
"""

def load_config(path: str) -> tuple[Optional[ParsedConfig], Optional[Error]]:
    """Loads a configuration file using ``tomllib``. Read more about how ``tomllib`` converts TOML
    into Python objects
    `here <https://docs.python.org/3/library/tomllib.html#conversion-table>`_. After loading the
    configuration file, you may be interested in :func:`validate_config`.

    :param path: Path to the configuration file.
    :return: A dictionary representing the TOML configuration, along with possible fatal errors in
             case of IO or parsing failures.

    Example:

    The object returned by ``load_config``, for the example config in the
    `project's README <../../../README.md>`_, is:

    .. code:: python

        {
            'powersave': { 'pluginA': 'Hello, world',
                           'pluginB': [ 123, 321 ],
                           'pluginC': { 'varX': 100, 'varY': 200 }
                         },
            'performance': { 'pluginA': 'Hello, Jupiter',
                             'pluginB': [],
                             'pluginC': { 'varX': 50, 'varY': 100 }
                           }
        }
    """

    try:
        with open(path, 'rb') as file:
            return (load(file), None)
    except OSError:
        return (None, Error(ErrorType.ERROR, f'Failed to read config from "{path}".'))
    except TOMLDecodeError as ex:
        return (None, Error(ErrorType.ERROR, f'Failed to parse config in "{path}".' \
                                             f'Here\'s the error message:\n{str(ex)}'))

def __remove_plugin_references(config: ValidatedConfig, plugin_name: str, \
                               blacklist: Optional[list[str]] = None) -> None:
    """Removes references to a plugin in a configuration. This is used when a plugin's
    configuration is deemed invalid, and powermodes tries to continue without it. This is an
    auxiliary method for :func:`validate_config`.

    :param config: :data:`ValidatedConfig` (partially validated configuration) that
                   **will be modified**.
    :param plugin_name: Name of the plugin that will be removed from ``config``.
    :param blacklist: List of names of powermodes from which the plugin references must not be
                      removed. Usually, these are the powermodes for which the plugin's
                      :attr:`~powermodes.plugin.Plugin.validate` method reported success.
    """

    if blacklist is None:
        blacklist = []

    for mode, mode_config in config.items():
        for name_key in list(mode_config):
            if name_key == plugin_name and mode not in blacklist:
                del mode_config[name_key]

def __validate_remove_non_dicts(config: ParsedConfig) -> tuple[None, list[Error]]:
    """Removes all non-dictionary powermodes from a configuration. This is an auxiliary method
    for :func:`validate_config`.

    :param config: Configuration that **may be modified**. After calling this method, it can
                   type-wise be considered a :data:`ValidatedConfig`, even if only partially
                   validated.
    :return: Warnings reported the non-dictionaries that were removed.
    """

    errors: list[Error] = []

    for mode in list(config):
        if not isinstance(config[mode], dict):
            errors.append(Error(ErrorType.WARNING, 'Config specified invalid powermode ' \
                                                  f'"{mode}". Must be a TOML table. Ignoring it.'))
            del config[mode]

    return (None, errors)

def __validate_remove_empty_dicts(config: ValidatedConfig, results_from_removal: bool) \
    -> tuple[None, list[Error]]:
    """Removes empty dictionaries (powermodes) from a configuration. This is an auxiliary method
    for :func:`validate_config`.

    :param config: Partially validated (:data:`ValidatedConfig`) configuration that **may be
                   modified** (on error).
    :param results_from_removal: Whether any empty dictionary (powermode) may have been modified
                                 before, by removing invalidly configured plugins (:data:`True`),
                                 or if the powermode was already empty in the user's configuration
                                 file (:data:`False`). Changing this parameter only influences
                                 eventual error messages.
    :return: Warnings for removed powermodes.
    """

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

# pylint: disable=too-many-locals
def __validate_remove_unknown_plugins(config: ValidatedConfig, plugins: LoadedPlugins) \
    -> tuple[set[str], list[Error]]:
    """Removes all unknown plugins from a configuration. This is an auxiliary method for
    :func:`validate_config`.

    :param config: Partially validated configuration that **may be modified**.
    :param plugins: Loaded plugins (see :func:`~powermodes.plugin.load_plugins`).
    :return: A set of the names of the plugins used in the configuration file, along with warnings
             for all unknown plugins.
    """

    errors: list[Error] = []
    known: set[str] = set()
    unknown: dict[str, list[str]] = {} # plugin -> list of powermodes where its defined

    for mode in config.keys():
        for plugin in config[mode].keys():
            if plugin in plugins:
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

def __validate_plugins(config: ValidatedConfig, plugins: set[Plugin]) -> \
    tuple[None, list[Error]]:
    """Calls the :attr:`~powermodes.plugin.Plugin.validate` method for every plugin present in a
    configuration, removing plugin configurations in case configuration errors are reported by
    plugins. This is an auxiliary method for :func:`validate_config`.

    :param config: Partially validated configuration (:data:`ValidatedConfig`) that
                   **may be modified** (on error).
    :param plugins: Plugins present in the configuration file
                    (see :func:`__validate_remove_unknown_plugins`).
    :return: Warnings from plugins.
    """

    errors: list[Error] = []

    for plugin in plugins:
        successful = handle_error_append(errors, wrapped_validate(plugin, config))

        error_modes: list[str] = \
            list(filter(lambda mode, suc=successful, name=plugin.name, cfg=config: # type: ignore
                        name in cfg[mode] and mode not in suc,
                        config.keys()))

        if len(error_modes) != 0:
            errors.append(Error(ErrorType.WARNING, f'Removing plugin {plugin.name} from the ' \
                                                    'following powermodes: ' + \
                                                    ', '.join(error_modes) + '. Plugin\'s ' \
                                                    'validate method failed.',
                                plugin.name))

        __remove_plugin_references(config, plugin.name, successful)

    return (None, errors)

def validate_config(config: ParsedConfig, plugins: LoadedPlugins) -> tuple[bool, list[Error]]:
    """Checks if a configuration file is valid, and modifies it, removing all invalid parts.

    The lists of checks performed is the following:

    - Powermodes (children of the root dictionary) that aren't themselves dictionaries are removed;
    - Empty powermodes are removed;
    - Configurations for unknown (not installed) plugins are removed;
    - Plugins' ``validate`` methods are called, to remove invalidly configured parts from
      powermodes;
    - Empty powermodes are removed again (these may result from previous deletion of invalid
      parts).

    :param config: Parsed configuration file (see :func:`load_config`). **Will be modified** and
                   will become an :data:`ValidatedConfig`.
    :param plugins: Loaded plugins (see :func:`~powermodes.plugin.load_plugins`).
    :return: Whether the configuration file is valid, i.e, powermodes can still proceed with it,
             even if some invalid parts had to be removed. Reported errors and warnings are also
             returned.
    """

    errors: list[Error] = []

    handle_error_append(errors, __validate_remove_non_dicts(config))
    handle_error_append(errors, __validate_remove_empty_dicts(config, False))
    known_plugin_names = \
        handle_error_append(errors, __validate_remove_unknown_plugins(config, plugins))
    known_plugins = set(map(plugins.__getitem__, known_plugin_names))
    handle_error_append(errors, __validate_plugins(config, known_plugins))
    handle_error_append(errors, __validate_remove_empty_dicts(config, True))

    if not config:
        errors.append(Error(ErrorType.ERROR, 'Empty configuration (this may be the result ' \
                                             'of the removal of invalid config parts).'))
        return (False, errors)
    else:
        return (True, errors)

def apply_mode(mode: str, config: ValidatedConfig, plugins: LoadedPlugins) -> \
    tuple[bool, list[Error]]:
    """Applies a powermode from a validated configuration file.

    :param mode: Name of the powermode to be applied.
    :param config: Validated configuration file.
    :param plugins: Loaded plugins (see :func:`~powermodes.plugin.load_plugins`).
    :return: Whether the mode was applied successfully (at least a single plugin reported success),
             along with errors and warnings reported from plugins'
             :attr:`~powermodes.plugin.Plugin.configure` methods.
    """

    errors: list[Error] = []

    if mode not in config:
        return (False, [ Error(ErrorType.ERROR, f'Powermode {mode} not in configuration file') ])

    all_failed = True
    for plugin_name, config_obj in config[mode].items():
        successful = handle_error_append(errors,
                                         wrapped_configure(plugins[plugin_name], config_obj))

        if successful is False:
            errors.append(Error(ErrorType.WARNING, 'configure reported insuccess. You may have ' \
                                                   'ended up with a partially configured ' \
                                                   'system.', \
                                plugin_name))
        else:
            all_failed = False


    if all_failed:
        errors.append(Error(ErrorType.ERROR, f'All plugins failed to apply mode {mode}'))
        return (False, errors)
    else:
        return (True, errors)

def plugin_is_in_all_powermodes(config: ValidatedConfig, plugin_name: str) -> \
    tuple[bool, Optional[Error]]:
    """Checks if all powermodes have a configuration object for a given plugin.

    :param config: A :data:`ValidatedConfig`.
    :param plugin_name: Name of the plugin to check for presence in all powermodes.
    :return: Whether or not the plugin is configured in every powermode, along with a warning for
             all powermodes that don't configure the plugin.
    """

    not_in: list[str] = []
    for powermode, powermode_config in config.items():
        if plugin_name not in powermode_config:
            not_in.append(powermode)

    if len(not_in) == 0:
        return (True, None)
    else:
        not_in_list = ', '.join(not_in)
        return (False, Error(ErrorType.WARNING, 'Not all powermodes have a configuration for ' \
                                               f'{plugin_name}. That means that you may get a ' \
                                                'partially configured system while hopping ' \
                                                'between modes. Here are the missing ' \
                                               f'powermodes: {not_in_list}.' ))

def iterate_config(config: ValidatedConfig, plugin_name: str) \
    -> Generator[tuple[str, Any], None, None]:
    """Iterates through a configuration file, through all powermodes, and returns tuples
    containing the name of the current powermode, and the configuration object for the plugin.

    :param config: :data:`ValidatedConfig` to iterate through.
    :param plugin_name: Name of the plugin that the returned configuration objects will configure.
    :return: Iterates through tuples, containing powermodes' names and configuration objects for
             the plugin.

    Example:

    Consider the following configuration file, after being parsed and validated
    (see :func:`powermodes.config.load_config` and :func:`powermodes.config.validate_config`).

    .. code:: toml

        [mode1]
            pluginA = 1
            pluginB = 2

        [mode2]
            pluginB = 3

        [mode3]
            pluginA = 4
            pluginB = 5

    Then,

    .. code:: python

        >>> list(iterate_config(config, 'pluginA'))
        [ ('mode1', 1), ('mode3', 4) ]
    """

    for powermode, powermode_config in config.items():
        if plugin_name in powermode_config:
            yield (powermode, powermode_config[plugin_name])
