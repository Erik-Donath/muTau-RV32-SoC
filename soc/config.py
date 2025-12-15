"""SoC Configuration"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SoCConfig:
    """
    SoC Configuration Parameters
    
    This dataclass holds all configuration options for the SoC build.
    It always uses LiteX BIOS with different kernels loaded via serialboot.
    """
    
    # Board configuration
    board_name: str = "tang_nano_9k"
    
    # Clock configuration
    sys_clk_freq: float = 27e6
    
    # Memory configuration
    # When true, the board is allowed to add external main RAM
    # (HyperRAM, SDRAM, etc.) via add_main_memory().
    with_external_ram: bool = True
    integrated_rom_size: int = 128 * 1024  # 128 KiB
    integrated_sram_size: int = 8 * 1024  # 8 KiB
    external_ram_size: int = 4 * 1024 * 1024  # 4 MiB (board interprets this)
    
    # Kernel configuration
    # When external RAM is disabled, kernel address is set to SRAM
    kernel_address: Optional[int] = None
    
    # CPU configuration
    cpu_type: str = "vexriscv"
    cpu_variant: str = "standard"
    cpu_reset_address: Optional[int] = None
    
    # Peripheral configuration (desire; board decides what it can provide)
    want_uart: bool = True
    want_timer: bool = True
    want_gpio: bool = True
    want_i2c: bool = True
    want_spi: bool = True
    want_pwm: bool = True
    
    # Build configuration
    build_name: str = "soc"
    output_dir: str = "build"
    
    def __post_init__(self):
        """Adjust configuration based on memory settings"""
        if not self.with_external_ram and self.kernel_address is None:
            # Set kernel address to SRAM when no external RAM
            # LiteX typically places SRAM at 0x10000000 for VexRiscv
            self.kernel_address = 0x10000000
    
    @property
    def output_path(self):
        """Get full output path"""
        return f"{self.output_dir}/{self.board_name}"
