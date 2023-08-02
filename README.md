# powermodes

A laptop power consumption manager for Linux, written in *pure* Python and licensed under the
[Apache License](https://www.apache.org/licenses/LICENSE-2.0). It's easily configurable and
even expandable with new plugins!

### Installation

Clone the repo and install the package:

```bash
$ git clone https://github.com/voidbert/powermodes.git
$ sudo pip install .
```

Now, the `powermodes` command should be installed.

### Usage

```
usage: powermodes [options]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -c CONFIG, --config CONFIG
                        specify path to configuration file
  -p PLUGIN, --plugin PLUGIN
                        configure installed PLUGIN
  --plugin-config PLUGIN_CONFIG
                        configuration for PLUGIN (instead of interactive)
  --list-plugins        list installed plugins
  -m MODE, --mode MODE  apply power MODE
  --list-modes          list power modes
```

If nothing / only CONFIG is specified, the interactive mode will be enabled. `-m` / `--mode` and
`--list-modes` require a configuration file. Lastly, the option after the command-line option
`--plugin-config` must be a TOML value, i.e, something you'd put after the `=` sign:

```bash
$ powermodes -p exampleplugin --plugin-args '{ option1 = 20, option2 = 100 }'
```

Here are some other examples:

```bash
# powermodes -c config.toml                # full interactive mode
# powermodes                               # choose what plugins to interactively configure
# powermodes -p intelpstate                # interactively configure intelpstate plugin
# powermodes -c config.toml -m performance # enable performance mode defined in the config.toml
```

### Configuration

`powermodes` is configured with [TOML](https://toml.io). Here's an example:

```toml
[power-saving] # Create a mode called power-saving

    # The following hypothetical plugin is configured with a string
    pluginA = "Hello, world!"

    # The following plugin is configured with a list
    pluginB = [ 123, 456, 789 ]

    # The following plugin is configured with a table (dictionary)
    [power-saving.pluginC]
    option1 = 100
    option2 = 20

[performance]
    pluginA = "Hello, Jupiter!"
    pluginB = [ 987, 654, 321 ]
    pluginC = { option1 = 20, option2 = 100 } # Inline table example
```

#### Configuration of included plugins

Each plugin is configured differently. Here is the configuration documentation for the included
plugins:

TODO

### Development

Project documentation can be generated with:

```bash
$ doxygen
```

#### Development of new plugins

Plugins are Python scripts in [`powermodes/plugins`](powermodes/plugins). In order to be correctly
imported, their file names must have the format `[identifier].py`, so only letters, numbers
(not in the beginning) and underscores are accepted. Plugins must also define the following
methods:

```python
def configure(config: any) -> ():
    ...
def interact() -> ():
    ...
```

`configure` is called to configure the module, either from the configuration file or from
command-line arguments. The `config` object may be the one provided after `--plugin-args`, or
present in the chosen mode from the configuration file (read about how `tomllib`
[converts from TOML to Python objects](https://docs.python.org/3/library/tomllib.html#conversion-table)).
The `interact` method is called to trigger the user-interaction mode.

You can import modules from `powermodes` using relative notation. For example:

```python
from ..utils import fatal
```

Keep in mind that **plugins run with root permissions**, so be careful!

