from migen import Signal, ClockDomain
from litex.gen import LiteXModule
from litex.soc.cores.clock.gowin_gw1n import GW1NPLL


class ClockDomainGenerator(LiteXModule):
    """Clock and Reset Generator."""

    def __init__(self, platform, sys_clk_freq,
                 input_clk_name="clk27", input_clk_freq=27e6):
        self.rst   = Signal()
        self.cd_sys = ClockDomain()

        # Get platform resources
        clk_in    = platform.request(input_clk_name)
        reset_btn = platform.request("user_btn", 0)

        # Detect platform type and create appropriate PLL / clocking
        if hasattr(platform, "devicename"):  # Gowin
            self._create_gowin_pll(platform, clk_in, reset_btn,
                                   input_clk_freq, sys_clk_freq)
        else:
            raise NotImplementedError(f"Platform {type(platform)} not supported")

    def _create_gowin_pll(self, platform, clk_in, reset_btn,
                          input_freq, output_freq):
        """Create Gowin-specific PLL or simple buffer for unsupported devices."""
        dev = getattr(platform, "device", "")

        if dev.startswith("GW1N") or dev.startswith("GW1NR"):
            # Use GW1N PLL for Tang Nano 9K and other GW1N/R parts.
            self.pll = GW1NPLL(
                devicename=platform.devicename,
                device=platform.device,
            )

            # Reset is active-low on button
            self.comb += self.pll.reset.eq(~reset_btn)

            # Register input clock
            self.pll.register_clkin(clk_in, input_freq)

            # Create output clock
            self.pll.create_clkout(self.cd_sys, output_freq)
        else:
            # GW5A and others: no supported PLL yet -> simple pass-through.
            # Assumes input_freq == output_freq (enforced by your config).
            self.comb += self.cd_sys.clk.eq(clk_in)
            self.comb += self.cd_sys.rst.eq(~reset_btn)
