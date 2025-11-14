from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.boards.platforms import generic_platform

from litex.soc.cores.cpu import Minerva  # RV32I CPU Core aus LiteX/nmigen

# Minimalplattform (leer) definieren
class BasePlatform(generic_platform.GenericPlatform):
    def __init__(self):
        io = []
        super().__init__(io, toolchain="iverilog")

# SoC definieren mit Minerva RV32I CPU
class BaseSoC(SoCCore):
    def __init__(self, **kwargs):
        platform = BasePlatform()
        # CPU-Instanz: RV32I Minerva
        cpu = Minerva()
        
        # SoCCore initialisieren mit CPU, Systemclock 50 MHz, 32-bit Wishbone Bus und etwas RAM
        super().__init__(
            platform,
            cpu_type=None,  # Wir geben direkt angelegte CPU-Instanz
            clk_freq=50e6,
            cpu=cpu,
            integrated_rom_size=0x2000,   # 8 KB ROM
            integrated_main_ram_size=0x4000, # 16 KB RAM
            **kwargs
        )

if __name__ == "__main__":
    soc = BaseSoC()
    builder = Builder(soc, output_dir="build")
    builder.build()

