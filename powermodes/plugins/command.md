# Command Plugin

This plugin allows you to run commands. It's a very simple utility, so that you don't need to
extend powermodes with a custom plugin if you just want quickly set something using a command.

`command` is configured with a list of TOML tables (dictionaries), each corresponding to a command.
All commands are run sequentially, but it cannot be known if the `command` plugin will start before
or after any other plugin. Here are the fields of each command's table:

- `command`: a string or a list of strings, for the executable to be run and its arguments.
  - When a string, like `"echo \"Hello, world!\""`, the command will be run through a shell
    (`sh -c`). Keep in mind that, like in the example, quotes may need to be escaped.

  - When a list of strings, like `["echo", "Hello, world!"]`, no shell needs to be invoked, as
    the command-line arguments are already split. No fancy things like pipes work in this case.

- `allow-stdin`: a boolean that defaults to `false`, and determines whether the child process can
  read from `stdin`. The default is `false`, so that there's no risk of powermodes hanging, waiting
  to read user input, while in the non-interactive mode
  (`powermodes -c config.toml -m powermode_name`).

- `show-stdout`: a boolean that defaults to `false`, and determines whether the program's standard
  output should be shown to the user.

- `show-stderr`: a boolean that defaults to `true`, and determines whether the program's standard
  error should be shown to the user.

- `warning-on-failure`: a boolean that defaults to `true`, and determines if a warning should be
  shown to the user if the command exits with a non-zero exit code (usually means failure). If this
  is `false`, apart from the lack of a warning message, the failure of the associated command won't
  be counted towards plugin failure.

As you can see, there's no notion of control flow in the execution of commands. For more complex
operations, write a simple shell script or, better yet, a powermodes plugin.

### Example

``` toml
[powersave]
	command = [
		# Lower screen refresh rate to save on battery
		{ command = ["sway", "output", "eDP-1", "mode", "1366x768@40.042Hz"] }
		{ command = "echo 'You just applied the powersave powermode!'", show-stdout = true }
	]

[performance]
	command = [
		{ command = ["sway", "output", "eDP-1", "mode", "1366x768@60.059Hz"] }
		{ command = "echo 'You just applied the performance powermode!'", show-stdout = true }
	]
```

### Root notices

Keep in mind that, just like powermodes, **these commands run as root**, so be careful! For
example, don't run commands and shell scripts stored inside your `HOME` directory, as those can be
modified by a malicious actor without password access, and then run with root permissions through
powermodes. The same applies to your configuration file: don't put in your `HOME`.

Also, keep in mind that the environment variables may be different for the root user. This includes
`PATH`, so use absolute paths for any program that can't be found. If any command you plan on
running needs environment variables (e.g.: `sway` needs `SWAYSOCK`), consider passing them through
by editing your `sudo` (or `doas`) config.
