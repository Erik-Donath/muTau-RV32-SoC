"""Tang Nano 9K Board Support"""

from migen import Signal

from boards import Board, register_board

from .platform import TangNano9KPlatform
from .peripherals import add_peripherals

from cores.hyperbus import create_hyperram_controller
from litex.soc.integration.soc import SoCRegion


@register_board("tang_nano_9k")
class TangNano9K(Board):
    """
    Sipeed Tang Nano 9K Board.

    Specifications:
    - FPGA: Gowin GW1NR-9C
    - LUTs:  ~8640
    - BlockRAM: ~468 Kbits
    - PSRAM: 2x 32Mbit (HyperRAM-like)
    - USB-UART: FT2232D
    """

    name = "Tang Nano 9K"

    # Clock configuration for this board
    input_clk_name = "clk27"
    input_clk_freq = 27e6

    # Platform ----------------------------------------------------------------
    def create_platform(self):
        """Create platform instance."""
        return TangNano9KPlatform()

    # Main memory (HyperRAM via HyperBus) ------------------------------------
    def add_main_memory(self, soc, platform, config):
        """
        Add HyperRAM as main RAM using the internal PSRAM dies.

        This is only meaningful on Tang Nano 9K; other boards implement their
        own memory strategy.
        """

        pads = self.get_hyperram_pads(platform)

        # Connect HyperRAM clocks if board exposes physical pins.
        if hasattr(pads, "_ck"):
            soc.comb += [
                pads._ck.eq(pads.clk),
                pads._ck_n.eq(~pads.clk),
            ]

        # Create HyperRAM controller and map as main RAM.
        hyperram = create_hyperram_controller(pads)
        soc.hyperram = hyperram

        soc.bus.add_slave(
            name="main_ram",
            slave=hyperram.bus,
            region=SoCRegion(
                origin=soc.mem_map["main_ram"],
                size=soc.soc_config.external_ram_size,
            ),
        )


        # Skip memory test during boot (faster)
        soc.add_constant("CONFIG_MAIN_RAM_INIT")

    # HyperBus helper --------------------------------------------------------
    def get_hyperram_pads(self, platform):
        """
        Get HyperRAM pads for the first internal chip.

        Clock connections from SoC: this returns a pads object with a logical
        clk Signal and physical clock pins exposed as _ck/_ck_n.
        """
        dq     = platform.request("IO_psram_dq")
        rwds   = platform.request("IO_psram_rwds")
        resetn = platform.request("O_psram_reset_n")
        csn    = platform.request("O_psram_cs_n")
        ck     = platform.request("O_psram_ck")
        ckn    = platform.request("O_psram_ck_n")

        class HyperRAMPads:
            def __init__(self):
                # Logical clock driven by SoC/CRG
                self.clk   = Signal()
                # Names must match HyperRAMController expectations:
                self.rst_n = resetn[0]
                self.cs_n  = csn[0]
                self.dq    = dq[0:8]
                self.rwds  = rwds[0]
                # Physical clock pins for external routing if needed
                self._ck   = ck[0]
                self._ck_n = ckn[0]

        return HyperRAMPads()

    # Board-specific peripherals ---------------------------------------------
    def add_peripherals(self, soc, platform, config):
        """Add Tang Nano 9K specific peripherals to the SoC."""
        add_peripherals(soc, platform, config)
