"""Tang Nano 9K Peripheral Configuration"""

from litex.soc.cores.timer import Timer
from litex.soc.cores.gpio import GPIOOut, GPIOIn, GPIOTristate
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster


def add_peripherals(soc, platform, config):
    """
    Add peripherals to SoC based on configuration and Nano 9K capabilities.
    """

    # LEDs (always add)
    soc.leds = GPIOOut(
        pads=platform.request_all("user_led")
    )

    # Button with interrupt (always add)
    soc.gpio_btn = GPIOIn(
        pads=platform.request("user_btn", 1),
        with_irq=True
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

    # I2C Master (Nano has i2c0 on expansion header)
    if getattr(config, "want_i2c", False):
        soc.i2c0 = I2CMaster(pads=platform.request("i2c0"))

    # Secondary UART (expansion header)
    if getattr(config, "want_uart", False):
        # Expose expansion UART as "uart1"
        soc.add_uart(name="uart1", uart_name="uart0")

    # SPI (SDCard on J6)
    if getattr(config, "want_spi", False):
        soc.spi_sdcard = SPIMaster(
            pads=platform.request("spisdcard"),
            data_width=8,
            sys_clk_freq=config.sys_clk_freq,
            spi_clk_freq=10e6,
        )

    # GPIO expansion pins (J6/J7)
    if getattr(config, "want_gpio", False):
        pads = platform.request("gpio")
        soc.gpio = GPIOTristate(pads)
        soc.add_csr("gpio")

    # PWM outputs
    if getattr(config, "want_pwm", False):
        # For now, just expose pins as GPIOOut.
        soc.pwm0 = GPIOOut(pads=platform.request("pwm0"))
        soc.pwm1 = GPIOOut(pads=platform.request("pwm1"))
