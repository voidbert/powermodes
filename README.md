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
  -h, --help                 show this help message
  --version                  show powermode's version

  -c CONFIG, --config CONFIG use CONFIG file

  -i, --interactive          interactively choose power mode
  -v, --validate             validate CONFIG file
  -m MODE, --mode MODE       apply power MODE from CONFIG
```

Here are some examples. Note that powermodes needs to be **run as root**:

| Action                                     | Command                                 |
| :----------------------------------------- | :-------------------------------------- |
| Interactively choose mode in configuration | `# powermodes -ic config.toml`          |
| Validate configuration                     | `# powermodes -vc config.toml`          |
| Apply power mode in configuration          | `# powermodes -c config.toml -m` *mode* |

### Configuration

A configuration file is just a [TOML](https://toml.io) file with the following properties:

- Top-level objects (children of the root object) must be tables, and are called powermodes. These
  are the things you actually enable, like `powersave`, `balanced`, `performance`, etc.

- Each powermode contains key-object pairs, to describe how a mode should be applied. The key
  refers to the name of a plugin, and the object is given to that plugin to apply the
  configuration.

Here's an example with **hypothetical plugins**:

```toml
[powersave]
	pluginA = "Hello, world" # pluginA is configured with a string
	pluginB = [ 123, 321 ]   # pluginB is configured with a list
	[powersave.pluginC]      # pluginC is configured with a table
		varX = 100
		varY = 200

[performance]
	pluginA = "Hello, Jupiter"
	pluginB = []
	pluginC = { varX = 50, varY = 100 } # inline table example
```

As you can see, each plugin can be configured in its own way. Here's the documentation for the
first-party plugins:

- [`command`](./powermodes/plugins/command.md) - Run commands;
- [`intel-epb`](./powermodes/plugins/intelepb.md) - Energy Performance and Energy Bias Hint
  (Intel CPUs only);
- [`nmi-watchdog`](./powermodes/plugins/nmiwatchdog.md) - Linux NMI watchdog (kernel hang
  detector).

### Development

If you'd like to develop a plugin, or contribute to the `powermodes` application, make sure to
check build developer documentation:

```bash
$ cd docs
$ ./make.sh build           # For plugin developers
$ ./make.sh build --private # For powermodes developers (includes internal methods)
```

Make sure you have `sphinx` and `sphinx-autodoc-typehints` installed:

```bash
$ pip install sphinx sphinx-autodoc-typehints
```

That documentation contains essential information to starting coding!
