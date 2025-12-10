"""Base SoC Implementation"""

from migen import Signal
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc import SoCRegion

from .clocking import ClockDomainGenerator
from .config import SoCConfig
from cores.hyperbus import create_hyperram_controller
from boards import get_board


class BaseSoC(SoCCore):
    """
    Base RISC-V SoC
    
    This is the main SoC class that integrates:
    - CPU (VexRiscv by default)
    - Memory (integrated + HyperRAM)
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
            sys_clk_freq=config.sys_clk_freq
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
        
        # Add main memory
        if config.with_hyperram and not self.integrated_main_ram_size:
            self._add_hyperram(platform, board)
        
        # Add peripherals
        board.add_peripherals(self, platform, config)
    
    def _add_hyperram(self, platform, board):
        """Add HyperRAM as main memory"""
        # Get board-specific HyperRAM pads
        pads = board.get_hyperram_pads(platform)
        
        # Connect HyperRAM clocks (pads object has _ck and _ck_n)
        if hasattr(pads, '_ck'):
            self.comb += [
                pads._ck.eq(pads.clk),
                pads._ck_n.eq(~pads.clk),
            ]
        
        # Create HyperRAM controller
        self.hyperram = create_hyperram_controller(pads)
        
        # Add to bus as main RAM
        self.bus.add_slave(
            name="main_ram",
            slave=self.hyperram.bus,
            region=SoCRegion(
                origin=self.mem_map["main_ram"],
                size=self.soc_config.hyperram_size  # Use soc_config instead of config
            )
        )
        
        # Skip memory test during boot (faster)
        self.add_constant("CONFIG_MAIN_RAM_INIT")
