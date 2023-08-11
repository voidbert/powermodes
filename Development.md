# powermodes development

### Installation

See [README.md](README.md).

### Documentation

Project documentation can be generated by running:

```bash
$ doxygen
```

If you plan to contribute any code, make sure to document it thoroughly. Check out doxygen's
documentation [here](https://www.doxygen.nl/manual/index.html).

### Static code analysis

This project uses [pylint](https://pypi.org/project/pylint/) and [mypy](https://mypy-lang.org/) to
assure code quality. These tools can be installed with the following command:

```bash
$ pip install pylint mypy
```

Before opening a pull request, make sure that running the following commands from the root of the
repository doesn't result in any errors:

```bash
$ pylint powermodes
$ mypy --strict powermodes
```