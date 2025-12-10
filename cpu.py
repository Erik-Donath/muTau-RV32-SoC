#!/usr/bin/env python3
"""
RISC-V SoC for Sipeed Tang Nano 9K FPGA Board
Improved version with complete peripheral access and better code quality

Copyright (c) 2025
SPDX-License-Identifier: BSD-2-Clause
"""

import os
from migen import Signal, ClockDomain, If
from litex.gen import LiteXModule

from platform import sipeed_tang_nano_9k
from litex.soc.cores.clock.gowin_gw1n import GW1NPLL
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import Builder
from litex.soc.cores.timer import Timer
from litex.soc.cores.gpio import GPIOOut, GPIOIn
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.spi import SPIMaster

from hyperbus import HyperRAM

# Constants
KIB = 1024
MIB = 1024 * KIB

# Default Configuration
DEFAULT_SYS_CLK_FREQ = 27e6
DEFAULT_INTEGRATED_ROM_SIZE = 128 * KIB
DEFAULT_INTEGRATED_SRAM_SIZE = 8 * KIB
HYPERRAM_SIZE = 4 * MIB


class ClockResetGenerator(LiteXModule):
    """
    Clock and Reset Generator for Tang Nano 9K
    Generates system clock from 27 MHz input using PLL
    """
    
    def __init__(self, platform, sys_clk_freq):
        """
        Args:
            platform: FPGA platform object
            sys_clk_freq: Target system clock frequency in Hz
        """
        self.rst = Signal()
        self.cd_sys = ClockDomain()
        
        # Get platform resources
        clk_27mhz = platform.request("clk27")
        reset_btn = platform.request("user_btn", 0)
        
        # Configure PLL
        self.pll = GW1NPLL(
            devicename=platform.devicename,
            device=platform.device
        )
        self.comb += self.pll.reset.eq(~reset_btn)
        self.pll.register_clkin(clk_27mhz, 27e6)
        self.pll.create_clkout(self.cd_sys, sys_clk_freq)


class TangNano9KSoC(SoCCore):
    """
    Enhanced RISC-V SoC for Tang Nano 9K
    
    Features:
    - RISC-V CPU with customizable frequency
    - 4 MB HyperRAM main memory
    - Complete peripheral access:
      * 6 LEDs (GPIO out)
      * 2 Buttons (1 for reset, 1 programmable with IRQ)
      * I2C master
      * Secondary UART
      * 3 hardware timers with interrupts
    """
    
    def __init__(
        self,
        sys_clk_freq=DEFAULT_SYS_CLK_FREQ,
        integrated_rom_size=DEFAULT_INTEGRATED_ROM_SIZE,
        integrated_sram_size=DEFAULT_INTEGRATED_SRAM_SIZE,
        with_hyperram=True,
        **kwargs
    ):
        """
        Initialize SoC with all peripherals
        
        Args:
            sys_clk_freq: System clock frequency in Hz
            integrated_rom_size: Size of integrated ROM
            integrated_sram_size: Size of integrated SRAM
            with_hyperram: Enable HyperRAM as main memory
            **kwargs: Additional SoCCore arguments
        """
        # Initialize platform
        platform = sipeed_tang_nano_9k.Platform()
        
        # Setup clock and reset
        self.crg = ClockResetGenerator(platform, sys_clk_freq)
        
        # Configure memory sizes
        kwargs["integrated_rom_size"] = integrated_rom_size
        kwargs["integrated_sram_size"] = integrated_sram_size
        
        # Set ident if not already provided
        if "ident" not in kwargs:
            kwargs["ident"] = "Enhanced RISC-V SoC on Tang Nano 9K"
        
        # Initialize SoC core
        SoCCore.__init__(
            self,
            platform,
            sys_clk_freq,
            **kwargs
        )
        
        # Add HyperRAM if enabled
        if with_hyperram and not self.integrated_main_ram_size:
            self._add_hyperram(platform)
        
        # Add peripherals
        self._add_peripherals(platform)
    
    def _add_hyperram(self, platform):
        """Configure HyperRAM as main memory"""
        # Get HyperRAM pads
        dq = platform.request("IO_psram_dq")
        rwds = platform.request("IO_psram_rwds")
        reset_n = platform.request("O_psram_reset_n")
        cs_n = platform.request("O_psram_cs_n")
        ck = platform.request("O_psram_ck")
        ck_n = platform.request("O_psram_ck_n")
        
        # Helper class for HyperRAM pads
        class HyperRAMPads:
            def __init__(self, chip_index):
                self.clk = Signal()
                self.rst_n = reset_n[chip_index]
                self.dq = dq[8 * chip_index : 8 * (chip_index + 1)]
                self.cs_n = cs_n[chip_index]
                self.rwds = rwds[chip_index]
        
        # Configure first HyperRAM chip
        hyperram_pads = HyperRAMPads(0)
        self.comb += [
            ck[0].eq(hyperram_pads.clk),
            ck_n[0].eq(~hyperram_pads.clk),
        ]
        
        # Add HyperRAM controller
        self.hyperram = HyperRAM(hyperram_pads, latency=6)
        
        # Map to main memory region
        self.bus.add_slave(
            name="main_ram",
            slave=self.hyperram.bus,
            region=SoCRegion(
                origin=self.mem_map["main_ram"],
                size=HYPERRAM_SIZE
            )
        )
        
        # Disable memory test to speed up boot
        self.add_constant("CONFIG_MAIN_RAM_INIT")
        
        # TODO: Add second HyperRAM chip for 8 MB total
    
    def _add_peripherals(self, platform):
        """Add all peripheral controllers"""
        # LEDs - 6 user controllable
        self.leds = GPIOOut(
            pads=platform.request_all("user_led")
        )
        
        # Button with interrupt capability
        self.gpio_btn = GPIOIn(
            pads=platform.request("user_btn", 1),
            with_irq=True
        )
        self.irq.add("gpio_btn", use_loc_if_exists=True)
        
        # Hardware timers (3 total)
        self.timer0 = Timer()
        self.timer1 = Timer()
        self.timer2 = Timer()
        self.irq.add("timer0", use_loc_if_exists=True)
        self.irq.add("timer1", use_loc_if_exists=True)
        self.irq.add("timer2", use_loc_if_exists=True)
        
        # I2C master interface
        self.i2c0 = I2CMaster(pads=platform.request("i2c0"))
        
        # Secondary UART on expansion header
        self.add_uart(name="uart1", uart_name="uart0")
        
        # TODO: Add SPI, PWM, and GPIO expansion when tested


def main():
    """Main entry point for SoC build"""
    from litex.build.parser import LiteXArgumentParser
    
    parser = LiteXArgumentParser(
        platform=sipeed_tang_nano_9k.Platform,
        description="Enhanced RISC-V SoC for Tang Nano 9K FPGA"
    )
    
    # Add custom arguments
    parser.add_target_argument(
        "--flash",
        action="store_true",
        help="Flash bitstream and BIOS to SPI flash"
    )
    parser.add_target_argument(
        "--sys-clk-freq",
        default=DEFAULT_SYS_CLK_FREQ,
        type=float,
        help="System clock frequency (default: 27 MHz)"
    )
    parser.add_target_argument(
        "--bios-flash-offset",
        default="0x40000",
        help="BIOS offset in SPI flash (default: 0x40000)"
    )
    parser.add_target_argument(
        "--no-hyperram",
        action="store_true",
        help="Disable HyperRAM (use integrated RAM only)"
    )
    
    args = parser.parse_args()
    
    # Build SoC
    soc = TangNano9KSoC(
        sys_clk_freq=args.sys_clk_freq,
        with_hyperram=not args.no_hyperram,
        **parser.soc_argdict
    )
    
    # Build bitstream
    builder = Builder(soc, **parser.builder_argdict)
    
    if args.build:
        builder.build(**parser.toolchain_argdict)
    
    # Load to SRAM for testing
    if args.load:
        prog = soc.platform.create_programmer("openfpgaloader")
        prog.load_bitstream(
            builder.get_bitstream_filename(mode="sram")
        )
    
    # Flash to persistent storage
    if args.flash:
        prog = soc.platform.create_programmer("openfpgaloader")
        
        # Flash bitstream
        prog.flash(
            0,
            builder.get_bitstream_filename(mode="flash", ext=".fs")
        )
        
        # Flash BIOS
        bios_offset = int(args.bios_flash_offset, 0)
        prog.flash(
            bios_offset,
            builder.get_bios_filename(),
            external=True
        )
        
        print(f"\nFlashing complete!")
        print(f"  Bitstream at: 0x000000")
        print(f"  BIOS at:      {args.bios_flash_offset}")


if __name__ == "__main__":
    main()
