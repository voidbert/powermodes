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
powermodes.plugin
=================

This module contains methods for loading and interacting with plugins.

Developing plugins
^^^^^^^^^^^^^^^^^^

A plugin is just a submodule of :mod:`powermodes.plugins`. Its name must be a Python identifier, so
that it can be imported (see `str.isidentifier
<https://docs.python.org/3/library/stdtypes.html#str.isidentifier>`_). Plugins whose module names
start with two underscores (``__``) are ignored.

To create a plugin, you must define two constants and two methods:

.. code:: python

    NAME: str = 'pluginA' # So that a plugin can have a name different from its module name.
    VERSION: str = '0.1'

    # Used to validate a configuration file. Described below.
    def validate(config: dict[str, dict[str, Any]]) -> tuple[list[str], list[Error]]:
        ...

    # Used to apply a configuration. Also described below.
    def configure(config: Any) -> tuple[bool, list[Error]]:
        ...

Before writing any code, keep in mind that **plugins should only report warnings**, and no errors.
That is because powermodes can still go on even if your plugin fails.

Configuration validation
^^^^^^^^^^^^^^^^^^^^^^^^

``validate`` will be called before ``configure``. Its job is to validate a configuration file. The
object it receives is the full configuration file, filtered not to include data from other plugins,

For example, in the configuration file from `README <../../../README.md>`_, this is the object that
``pluginA`` would receive:

.. code:: python

    {
        'powersave':   { 'pluginA': 'Hello, world' },
        'performance': { 'pluginA': 'Hello, Jupiter' }
    }

``validate`` must return the powermodes for which the configuration is valid (along with errors /
warnings that occurred). Suppose ``pluginA`` only likes to salute gas giants; it must return
something like:

.. code:: python

    (['performance'], Error(ErrorType.WARNING, 'world is not a gas giant'))

The ``pluginA`` object is removed from the ``powersave`` powermode, so that the user can't apply
an invalid configuration (and you don't need to handle it in ``configure``). You don't have to
return powermodes that don't have a configuration object for your plugin: warnings won't be
reported for those.

Why does ``validate`` get called with the whole configuration file, instead of once per powermode?
The way it's done, you can check if all powermodes have configurations for your plugin. That way,
if you're handling some operating system state, like CPU frequency, for example, you can warn the
user that they may end up with a partially configured system if they switch from a mode to another
(see :func:`powermodes.config.plugin_is_in_all_powermodes`).

Configuration application
^^^^^^^^^^^^^^^^^^^^^^^^^

Considering the previous example, if the user applies the ``performance`` powermode, ``configure``
will be called with the ``'Hello, Jupiter'`` argument, and it's up to you to apply that
configuration (whatever that means in this bad plugin example). ``configure`` must return whether
it was successful (or not), along with a list of warnings that may have occurred, for example,
``(True, [])``.

Module contents
^^^^^^^^^^^^^^^
"""

from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from inspect import signature
from pathlib import Path
from traceback import format_exception
from typing import Any, Callable, Optional

from .error import Error, ErrorType, handle_error_append, set_unspecified_origins

ValidatedConfig = dict[str, dict[str, Any]]
"""See :data:`powermodes.config.ValidatedConfig`. This type alias only exists to avoid cyclical
module imports from :mod:`powermodes.config`.
"""

__plugins_dir = Path(__file__).parent.joinpath('plugins')
"""Path to the directory that contains the plugins."""

@dataclass(frozen=True)
class Plugin:
    """The type of a powermodes plugin."""

    file: str
    """Python file containing the plugin, excluding directory name. E.g.: ``'plugin.py'``."""

    name: str
    """Name of the plugin (self-reported ``NAME`` constant, or the module name, if ``NAME`` isn't
    set)."""

    version: str
    """Version of the plugin (self-reported ``VERSION`` constant, or ``'unknown'``, if ``VERSION``
    isn't set)."""

    validate: Callable[[ValidatedConfig], tuple[list[str], list[Error]]]
    """Method called to validate the parts of a configuration file related to this plugin. Takes
    in a filtered :data:`ValidatedConfig` (excludes data from other plugins) and returns the list
    of validly configured powermodes, along with all warnings reported.

    **DO NOT USE** unless you *really* know what you're doing. Use :func:`wrapped_validate`
    instead.
    """

    configure: Callable[[Any], tuple[bool, list[Error]]]
    """Method called to apply a configuration. Takes in the configuration object for the plugin,
    for the chosen powermode, and returns whether the application of the configuration was
    successful, along with warnings that may have occurred.

    **DO NOT USE** unless you *really* know what you're doing. Use :func:`wrapped_configure`
    instead.
    """

LoadedPlugins = dict[str, Plugin]
"""Dictionary associating (self-reported) plugin names with the plugins themselves. See
   :func:`load_plugins`."""

def __valid_plugin_validate_return(obj: Any) -> bool:
    """Checks if the value returned by a plugin's :attr:`~Plugin.validate` is valid type-wise.
    Auxiliary function for :func:`wrapped_validate`.

    :param obj: Value returned by the :attr:`~Plugin.validate` method.
    :return: Whether or not the value returned by a plugin's :attr:`~Plugin.validate` is valid
             type-wise.
    """

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

def __valid_plugin_configure_return(obj: Any) -> bool:
    """Checks if the value returned by a plugin's :attr:`~Plugin.configure` is valid type-wise.
    Auxiliary function for :func:`wrapped_configure`.

    :param obj: Value returned by the :attr:`~Plugin.configure` method.
    :return: Whether or not the value returned by a plugin's :attr:`~Plugin.configure` is valid
             type-wise.
    """


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

def __filter_config_for_plugin(config: ValidatedConfig, plugin_name: str) -> ValidatedConfig:
    """Removes configuration objects unrelated to a plugin in a configuration, so that plugins
    don't have access to data that's not theirs.

    :param config: Partially validated configuration (:data:`ValidatedConfig`). It must be
                   certain that all powermodes are dictionaries.
    :param plugin_name: Name of the plugin whose configurations must be kept.
    :return: The filtered (and deep-copied) configuration.
    """

    copy = deepcopy(config)

    for mode in list(config):
        for name_key in list(config[mode]):
            if name_key != plugin_name:
                del copy[mode][name_key]

    return copy

def wrapped_validate(plugin: Plugin, config: ValidatedConfig) -> tuple[list[str], list[Error]]:
    """
    Wrapper around a plugin's :attr:`~Plugin.validate` method. This method performs some checks to
    make sure that the plugin won't crash powermodes:

    - The configuration provided to the plugin is filtered, not to share data about other plugins;
    - Exceptions raised by the plugin are handled and transformed into errors;
    - The plugin is forced to return an object of the expected type (deep-check). Otherwise, an
      error is reported;
    - The origins of errors / warnings returned by the plugin are set to the name of that plugin.

    :param plugin: Plugin whose :attr:`~Plugin.validate` method will be called.
    :param config: Validated configuration (:data:`ValidatedConfig`).
    :return: The same as :attr:`~Plugin.validate`, or ``[]`` and errors (on failure).
    """

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

def wrapped_configure(plugin: Plugin, obj: Any) -> tuple[bool, list[Error]]:
    """
    Wrapper around a plugin's :attr:`~Plugin.configure` method. This method performs some checks to
    make sure that the plugin won't crash powermodes:

    - Exceptions raised by the plugin are handled and transformed into errors;
    - The plugin is forced to return an object of the expected type (deep-check). Otherwise, an
      error is reported;
    - The origins of errors / warnings returned by the plugin are set to the name of that plugin.

    :param plugin: Plugin whose :attr:`~Plugin.configure` method will be called.
    :param config: Validated configuration (:data:`ValidatedConfig`).
    :return: The same as :attr:`~Plugin.configure`, or :data:`False` and errors (on failure).
    """

    try:
        plugin_return = plugin.configure(obj)
        if __valid_plugin_configure_return(plugin_return):
            success, plugin_errors = plugin_return
            set_unspecified_origins(plugin_errors, plugin.name)
            return (success, plugin_errors)
        else:
            return (False, [ Error(ErrorType.WARNING, 'configure returned an invalid value: ' \
                                                     f'{plugin_return}. Unable to report any ' \
                                                      'error / warning from this plugin. You ' \
                                                      'may have ended up with a partially ' \
                                                      'configured system.', plugin.name) ])

    # Needed pylint suppression because a module can throw any type of error
    # pylint: disable=broad-exception-caught
    except BaseException as ex:
        exception_text = ''.join(format_exception(ex))
        return (False, [ Error(ErrorType.WARNING, f'Calling configure resulted in an ' \
                                                   'exception. You may have ended up with a ' \
                                                   'partially configured system. Unable to ' \
                                                   'report any other error / warning from this ' \
                                                   'plugin. Here\'s the exception:\n' \
                                                  f'{exception_text}', \
                             plugin.name) ])

def list_plugin_module_names() -> tuple[Optional[list[str]], list[Error]]:
    """Lists the names of the Python modules that contain the installed plugins. Note that these
    differ from the plugins' self-reported ``NAME`` s.

    :return: On success, the list of module names (:data:`None` on failure), along with reported
             errors and warnings.
    """

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

def load_plugin(module_name: str) -> tuple[Optional[Plugin], list[Error]]:
    """Loads a plugin from its module name. Plugin validation is also performed in this method. The
    following checks are performed:

    - Importing the plugin's method musn't result on an exception (parsing error, Python exception,
      ...). This will result in the failure of this function.
    - The module must define a ``NAME`` and ``VERSION``. Warnings are reported if that's not the
      case, and ``NAME`` is set to be the ``module_name``, and ``VERSION`` to be ``'unknown'``.
    - :attr:`~Plugin.validate` and :attr:`~Plugin.configure` must be defined, resulting in failure
      of this function if not.

    :param module_name: Name of the Python module containing the plugin.
    :returns: The loaded plugin (:data:`None` on failure), along with errors and warnings.
    """

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

def load_plugins() -> tuple[Optional[LoadedPlugins], list[Error]]:
    """Loads all installed plugins. Note that plugins with equal self-reported ``NAME`` s may be
    ignored (with a warning, of course).

    :return: A dictionary associating plugin names with plugins themselves
             (see :data:`LoadedPlugins`), or, on failure, :data:`None`, along with errors.
    """

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
