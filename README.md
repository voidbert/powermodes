# powermodes

A laptop power consumption manager written in *pure* Python and licensed under the
[Apache License](https://www.apache.org/licenses/LICENSE-2.0). It's easily configurable and even
expandable with new modules!

### Installation

Clone the repo and install the package:

```bash
$ git clone https://github.com/voidbert/powermodes.git
$ pip install .
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
  --plugin-args PLUGIN_ARGS
                        arguments for PLUGIN (instead of interactive config)
  --list-plugins        list installed plugins
  -m MODE, --mode MODE  apply power MODE
  --list-modes          list power modes
```

If nothing / only CONFIG is specified, the interactive mode will be enabled. All options related
to power modes require a configuration file.

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

The option after the command-line option `plugin-args` must be a TOML value, i.e, something you'd
put after the `=` sign.

```bash
$ powermodes -p pluginC --plugin-args '{ option1 = 20, option2 = 100 }'
```

#### Configuration of included plugins

TODO

### Development

Project documentation can be generated with:

```bash
$ doxygen
```

#### Development of new plugins

Modules must define two methods:

```python
def configure(config: any) -> ():
    ...
def interact() -> ():
    ...
```

`configure` is called to configure the module, either from the configuration file or from
command-line arguments. The object is the one provided after `--plugin-args` or in the chosen mode
in configuration file. Read about how `tomllib`
[converts from TOML to Python objects](https://docs.python.org/3/library/tomllib.html#conversion-table).
The `interact` method is called to trigger the user-interaction mode.

Some code is injected before yours to allow you to import modules from `powermodes`. Access them
without any relative notation, as you were in the `powermodes` directory. For example:

```python
from utils import fatal
```

Keep in mind that plugins run with root permissions, so be careful!

