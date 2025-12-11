"""Tang Primer 25K Peripheral Configuration"""

from litex.soc.cores.timer import Timer
from litex.soc.cores.gpio import GPIOOut, GPIOIn, GPIOTristate
from litex.soc.cores.spi import SPIMaster


def add_peripherals(soc, platform, config):
    """
    Add peripherals to SoC based on configuration and Primer 25K capabilities.
    """

    # LEDs (READY/DONE on dock)
    soc.leds = GPIOOut(
        pads=platform.request_all("user_led")
    )

    # Button with interrupt (use e.g. user_btn[1])
    soc.gpio_btn = GPIOIn(
        pads=platform.request("user_btn", 1),
        with_irq=True,
    )
    soc.irq.add("gpio_btn", use_loc_if_exists=True)

    # Timers
    if getattr(config, "want_timer", False):
        soc.timer0 = Timer()
        soc.timer1 = Timer()
        soc.timer2 = Timer()
        soc.irq.add("timer0", use_loc_if_exists=True)
        soc.irq.add("timer1", use_loc_if_exists=True)
        soc.irq.add("timer2", use_loc_if_exists=True)

    # UART: assume primary UART is provided by LiteX core; no secondary UART
    # wired here yet, so ignore want_uart for now.

    if getattr(config, "want_spi", False):
        try:
            pads = platform.request("spisdcard")
        except Exception:
            pads = None
        if pads is not None:
            soc.spi_sdcard = SPIMaster(
                pads=pads,
                data_width=8,
                sys_clk_freq=config.sys_clk_freq,
                spi_clk_freq=10e6,
            )

    if getattr(config, "want_gpio", False):
        try:
            pads = platform.request("gpio")
        except Exception:
            pads = None
        if pads is not None:
            soc.gpio = GPIOTristate(pads)
            soc.add_csr("gpio")

    if getattr(config, "want_pwm", False):
        try:
            pwm0 = platform.request("pwm0")
            pwm1 = platform.request("pwm1")
        except Exception:
            pwm0 = pwm1 = None
        if pwm0 is not None and pwm1 is not None:
            soc.pwm0 = GPIOOut(pads=pwm0)
            soc.pwm1 = GPIOOut(pads=pwm1)
