"""SoC Configuration"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FirmwareTarget(Enum):
    """Firmware target options"""
    BIOS = "bios"
    BAREBONE = "barebone"
    FREERTOS = "freertos"
    LINUX = "linux"


@dataclass
class SoCConfig:
    """
    SoC Configuration Parameters

    This dataclass holds all configuration options for the SoC build.
    It allows different firmware targets and board configurations.
    """

    # Board configuration
    board_name: str = "tang_nano_9k"

    # Firmware target
    firmware_target: FirmwareTarget = FirmwareTarget.BIOS

    # Clock configuration
    sys_clk_freq: float = 27e6

    # Memory configuration
    # When true, the board is allowed to add external main RAM
    # (HyperRAM, SDRAM, etc.) via add_main_memory().
    with_external_ram: bool = True

    integrated_rom_size: int = 128 * 1024  # 128 KiB
    integrated_sram_size: int = 8 * 1024   # 8 KiB
    external_ram_size: int = 4 * 1024 * 1024  # 4 MiB (board interprets this)

    # CPU configuration
    cpu_type: str = "vexriscv"
    cpu_variant: str = "standard"
    cpu_reset_address: Optional[int] = None

    # Peripheral configuration
    with_uart: bool = True
    with_timer: bool = True
    with_gpio: bool = True
    with_i2c: bool = True
    with_spi: bool = True
    with_pwm: bool = True

    # Build configuration
    build_name: str = "soc"
    output_dir: str = "build"

    def __post_init__(self):
        """Adjust configuration based on firmware target"""
        if self.firmware_target == FirmwareTarget.LINUX:
            self.cpu_variant = "linux"
            self.integrated_rom_size = 0
        elif self.firmware_target == FirmwareTarget.FREERTOS:
            self.cpu_variant = "standard"
        elif self.firmware_target == FirmwareTarget.BAREBONE:
            pass

    @property
    def output_path(self):
        """Get full output path"""
        return f"{self.output_dir}/{self.board_name}"
