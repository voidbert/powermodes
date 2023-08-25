# Intel EPB Plugin

This plugin allows you the configure the
[Intel Performance and Energy Bias Hint](https://docs.kernel.org/admin-guide/pm/intel_epb.html)
for all CPUs in the system. As the name of this plugin may suggest, it's only available on Intel
processors.

<!--
	TODO - when  energy_performance_preference is implemented, redirect the user to that plugin
-->

`intel-epb` can be configured one of the following ways:

- An integer between 0 (highest performance) and 15 (highest power savings).
- One of the following strings:

| String                                     | Corresponding EPB value                 |
| :----------------------------------------- | :-------------------------------------- |
| performance                                | 0                                       |
| balance-performance                        | 4                                       |
| normal                                     | 6                                       |
| default                                    | 6                                       |
| normal-powersave                           | 7                                       |
| balance-power                              | 8                                       |
| power                                      | 15                                      |

Source: https://elixir.bootlin.com/linux/v6.4.12/source/arch/x86/include/asm/msr-index.h#L837

### Example

``` toml
[powersave]
	intel-epb = 15

[performance]
	intel-epb = 0
```
