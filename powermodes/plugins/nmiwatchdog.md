# NMI Watchdog Plugin

This plugin allows you to enable and disable the NMI watchdog. This part of the Linux kernel
periodically checks if the kernel has hung, resulting in a kernel panic. Disabling it means that,
if the kernel hangs, you won't get a panic, and the system will keep looping forever. In return,
you may get a slight improvement in power consumption.

`nmi-watchdog` is simply configured with a boolean.

### Example

``` toml
[powersave]
	nmi-watchdog = false

[performance]
	nmi-watchdog = true
```
