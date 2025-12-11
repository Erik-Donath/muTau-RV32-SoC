#!/usr/bin/env python3
"""
SoC Builder Script
Main entry point for building the SoC
"""

import argparse
import sys
from pathlib import Path

from litex.soc.integration.builder import Builder

from .config import SoCConfig, FirmwareTarget
from .base import BaseSoC


def build_soc(config: SoCConfig, build=False, flash=False, load=False):
    """
    Build SoC with given configuration
    
    Args:
        config: SoC configuration
        build: Whether to build bitstream
        flash: Whether to flash to board
        load: Whether to load to SRAM
    
    Returns:
        Builder instance
    """
    # Create SoC
    soc = BaseSoC(config)
    
    # Create builder
    builder = Builder(
        soc,
        output_dir=config.output_path,
        csr_csv=f"{config.output_path}/csr.csv"
    )
    
    # Build if requested
    if build:
        print(f"Building SoC for {config.board_name}...")
        builder.build()
        print(f"\nBuild complete! Output in {config.output_path}/")
        print(f"CSR map: {config.output_path}/csr.csv")
    
    # Flash if requested
    if flash:
        print("Flashing to board...")
        prog = soc.platform.create_programmer()
        
        # Flash bitstream
        bitstream = builder.get_bitstream_filename(mode="flash", ext=".fs")
        prog.flash(0, bitstream)
        
        # Flash BIOS
        bios = builder.get_bios_filename()
        prog.flash(0x40000, bios, external=True)
        
        print("Flash complete!")
    
    # Load to SRAM if requested
    if load:
        print("Loading to SRAM...")
        prog = soc.platform.create_programmer()
        bitstream = builder.get_bitstream_filename(mode="sram")
        prog.load_bitstream(bitstream)
        print("Load complete!")
    
    return builder


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RISC-V SoC Builder for FPGA"
    )
    
    # Board selection
    parser.add_argument(
        "--board",
        default="tang_nano_9k",
        help="Target board (default: tang_nano_9k)"
    )
    
    # Firmware target
    parser.add_argument(
        "--firmware",
        choices=["bios", "barebone", "freertos", "linux"],
        default="bios",
        help="Firmware target (default: bios)"
    )
    
    # Actions
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--flash", action="store_true", help="Flash to board")
    parser.add_argument("--load", action="store_true", help="Load to SRAM")
    
    # Configuration
    parser.add_argument("--sys-clk-freq", type=float, default=27e6, help="System clock frequency")
    
    args = parser.parse_args()
    
    # Create configuration
    config = SoCConfig(
        board_name=args.board,
        firmware_target=FirmwareTarget(args.firmware),
        sys_clk_freq=args.sys_clk_freq,
        with_external_ram=True
    )
    
    # Build SoC
    build_soc(
        config=config,
        build=args.build,
        flash=args.flash,
        load=args.load
    )


if __name__ == "__main__":
    main()
