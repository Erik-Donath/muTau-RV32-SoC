"""Tang Primer 25K Board Support"""

from boards import Board, register_board
from .platform import TangPrimer25KPlatform
from .peripherals import add_peripherals as primer_add_peripherals


@register_board("tang_primer_25k")
class TangPrimer25K(Board):
    """
    Sipeed Tang Primer 25K Board.

    Specifications:
    - FPGA: Gowin GW5A-25A
    """

    name = "Tang Primer 25K"

    # Clock configuration for this board
    input_clk_name = "clk50"
    input_clk_freq = 50e6

    # Platform ----------------------------------------------------------------
    def create_platform(self):
        """Create platform instance."""
        return TangPrimer25KPlatform()

    # Main memory ------------------------------------------------------------
    def add_main_memory(self, soc, platform, config):
        """
        Add main memory for Tang Primer 25K.

        Currently this board does not have built-in HyperRAM like Tang Nano 9K.
        External memory (e.g. SDRAM on the dock) can be added later via a
        dedicated SDRAM controller. For now, rely on integrated RAM only.
        """
        # No external main RAM; nothing to do here for now.
        return

    # Board-specific peripherals ---------------------------------------------
    def add_peripherals(self, soc, platform, config):
        """
        Add Tang Primer 25K specific peripherals to the SoC.

        Delegates to the board's peripherals helper, which should interpret
        config.want_* flags but only request IOs that exist on this platform.
        """
        primer_add_peripherals(soc, platform, config)
