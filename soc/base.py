"""Base SoC Implementation"""

from migen import Signal

from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc import SoCRegion

from .clocking import ClockDomainGenerator
from .config import SoCConfig

from boards import get_board


class BaseSoC(SoCCore):
    """
    Base RISC-V SoC

    This is the main SoC class that integrates:
    - CPU (VexRiscv by default)
    - Memory (integrated + optional external)
    - Peripherals (UART, GPIO, Timers, etc.)
    """

    def __init__(self, config: SoCConfig):
        """
        Initialize SoC

        Args:
            config: SoC configuration object
        """
        # Store config under different name to avoid conflict with SoCCore.config
        self.soc_config = config

        # Get board configuration
        board = get_board(config.board_name)
        platform = board.create_platform()

        # Create clock and reset generator
        self.crg = ClockDomainGenerator(
            platform=platform,
            sys_clk_freq=config.sys_clk_freq,
            input_clk_name=getattr(board, "input_clk_name", platform.default_clk_name),
            input_clk_freq=getattr(board, "input_clk_freq", config.sys_clk_freq),
        )

        # Initialize SoC Core
        SoCCore.__init__(
            self,
            platform,
            config.sys_clk_freq,
            cpu_type=config.cpu_type,
            cpu_variant=config.cpu_variant,
            cpu_reset_address=config.cpu_reset_address,
            integrated_rom_size=config.integrated_rom_size,
            integrated_sram_size=config.integrated_sram_size,
            ident=f"RISC-V SoC on {board.name}",
            ident_version=True,
        )

        # Add main memory: let the board decide how to implement external RAM.
        if not self.integrated_main_ram_size and getattr(config, "with_external_ram", False):
            board.add_main_memory(self, platform, config)

        # Add peripherals
        board.add_peripherals(self, platform, config)
