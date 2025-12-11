"""
Tang Primer 25K Peripheral Configuration
"""

from litex.soc.cores.timer import Timer
from litex.soc.cores.gpio import GPIOOut, GPIOIn, GPIOTristate
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster


def add_peripherals(soc, platform, config):
    """
    Add peripherals to SoC based on configuration.

    Args:
        soc:      SoC instance.
        platform: Platform instance.
        config:   SoC configuration object.
    """
    # LEDs (always add).
    soc.leds = GPIOOut(
        pads=platform.request_all("user_led")
    )

    # Button with interrupt (always add) - use second button as in 9K design.
    soc.gpio_btn = GPIOIn(
        pads=platform.request("user_btn", 1),
        with_irq=True
    )
    soc.irq.add("gpio_btn", use_loc_if_exists=True)

    # Timers.
    if getattr(config, "with_timer", False):
        soc.timer0 = Timer()
        soc.timer1 = Timer()
        soc.timer2 = Timer()
        soc.irq.add("timer0", use_loc_if_exists=True)
        soc.irq.add("timer1", use_loc_if_exists=True)
        soc.irq.add("timer2", use_loc_if_exists=True)

    # I2C Master (assumed on a dock connector; user adds pads in their platform
    # extension if desired).
    if getattr(config, "with_i2c", False):
        soc.i2c0 = I2CMaster(pads=platform.request("i2c0"))

    # Secondary UART (if you later add an extra uart0 in platform; pattern kept
    # identical to Tang Nano 9K).
    if getattr(config, "with_uart", False):
        soc.add_uart(name="uart1", uart_name="uart0")

    # SPI master for an external SDCard (user must provide "spisdcard" pads via
    # platform extension if used).
    if getattr(config, "with_spi", False):
        soc.spi_sdcard = SPIMaster(
            pads=platform.request("spisdcard"),
            data_width=8,
            sys_clk_freq=config.sys_clk_freq,
            spi_clk_freq=10e6,
        )

    # GPIO expansion bank (could be one of the PMOD/connector pin-groups).
    if getattr(config, "with_gpio", False):
        pads = platform.request("gpio")
        soc.gpio = GPIOTristate(pads)
        soc.add_csr("gpio")

    # PWM outputs; for now expose as simple GPIOOut like the 9K board.
    if getattr(config, "with_pwm", False):
        soc.pwm0 = GPIOOut(pads=platform.request("pwm0"))
        soc.pwm1 = GPIOOut(pads=platform.request("pwm1"))
