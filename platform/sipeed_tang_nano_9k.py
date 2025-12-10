"""
Extended Sipeed Tang Nano 9K Platform Definition
Complete pin mapping with better organization and documentation

Copyright (c) 2022-2025 Icenowy Zheng
SPDX-License-Identifier: BSD-2-Clause
"""

from litex.build.generic_platform import Pins, Subsignal, IOStandard, Misc
from litex.build.gowin.platform import GowinPlatform
from litex.build.gowin.programmer import GowinProgrammer
from litex.build.openfpgaloader import OpenFPGALoader


# Pin Definitions grouped by functionality
_io = [
    # ========== Clock and Reset ==========
    ("clk27", 0, Pins("52"), IOStandard("LVCMOS33")),
    
    # ========== User Interface ==========
    # LEDs (6 total)
    ("user_led", 0, Pins("10"), IOStandard("LVCMOS18")),
    ("user_led", 1, Pins("11"), IOStandard("LVCMOS18")),
    ("user_led", 2, Pins("13"), IOStandard("LVCMOS18")),
    ("user_led", 3, Pins("14"), IOStandard("LVCMOS18")),
    ("user_led", 4, Pins("15"), IOStandard("LVCMOS18")),
    ("user_led", 5, Pins("16"), IOStandard("LVCMOS18")),
    
    # Buttons (2 total)
    ("user_btn", 0, Pins("3"), IOStandard("LVCMOS18")),   # Used for reset
    ("user_btn", 1, Pins("4"), IOStandard("LVCMOS18")),   # Programmable
    
    # ========== Communication Interfaces ==========
    # Primary UART (built-in USB-UART)
    ("serial", 0,
        Subsignal("rx", Pins("18")),
        Subsignal("tx", Pins("17")),
        IOStandard("LVCMOS33")
    ),
    
    # Secondary UART (on expansion header)
    ("uart0", 0,
        Subsignal("rx", Pins("41")),
        Subsignal("tx", Pins("42")),
        IOStandard("LVCMOS33")
    ),
    
    # I2C Interface
    ("i2c0", 0,
        Subsignal("sda", Pins("40")),
        Subsignal("scl", Pins("35")),
        IOStandard("LVCMOS33"),
    ),
    
    # SPI for SD Card
    ("spisdcard", 0,
        Subsignal("clk", Pins("36")),
        Subsignal("mosi", Pins("37")),
        Subsignal("cs_n", Pins("38")),
        Subsignal("miso", Pins("39")),
        IOStandard("LVCMOS33"),
    ),
    
    # SPI for LCD Display
    ("spilcd", 0,
        Subsignal("reset", Pins("47")),
        Subsignal("cs", Pins("48")),
        Subsignal("clk", Pins("79")),
        Subsignal("mosi", Pins("77")),
        Subsignal("rs", Pins("86")),  # Register select
        IOStandard("LVCMOS33"),
    ),
    
    # ========== Memory Interfaces ==========
    # SPI Flash (for bitstream and data storage)
    ("spiflash", 0,
        Subsignal("cs_n", Pins("60"), IOStandard("LVCMOS33")),
        Subsignal("clk", Pins("59"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("62"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("61"), IOStandard("LVCMOS33")),
    ),
    
    # ========== HyperRAM / PSRAM (2x 32Mbit chips) ==========
    # These pins are NOT standard numbered pins - they are special signals
    # The original uses Pins("2") which means 2 instances, not pin number 2
    ("O_psram_ck", 0, Pins(2)),
    ("O_psram_ck_n", 0, Pins(2)),
    ("O_psram_cs_n", 0, Pins(2)),
    ("O_psram_reset_n", 0, Pins(2)),
    ("IO_psram_dq", 0, Pins(16)),      # 16 bits total (8 per chip)
    ("IO_psram_rwds", 0, Pins(2)),     # 2 bits (1 per chip)
    
    # ========== Video Output ==========
    # HDMI Interface
    ("hdmi", 0,
        Subsignal("clk_p", Pins("69")),
        Subsignal("clk_n", Pins("68")),
        Subsignal("data0_p", Pins("71")),
        Subsignal("data0_n", Pins("70")),
        Subsignal("data1_p", Pins("73")),
        Subsignal("data1_n", Pins("72")),
        Subsignal("data2_p", Pins("75")),
        Subsignal("data2_n", Pins("74")),
        Misc("PULL_MODE=NONE"),
    ),
    
    # ========== Expansion GPIO ==========
    # General Purpose IO (8 pins)
    ("gpio", 0, Pins("25"), IOStandard("LVCMOS33")),
    ("gpio", 1, Pins("26"), IOStandard("LVCMOS33")),
    ("gpio", 2, Pins("27"), IOStandard("LVCMOS33")),
    ("gpio", 3, Pins("28"), IOStandard("LVCMOS33")),
    ("gpio", 4, Pins("29"), IOStandard("LVCMOS33")),
    ("gpio", 5, Pins("30"), IOStandard("LVCMOS33")),
    ("gpio", 6, Pins("33"), IOStandard("LVCMOS33")),
    ("gpio", 7, Pins("34"), IOStandard("LVCMOS33")),
    
    # ========== PWM Outputs ==========
    ("pwm0", 0, Pins("51"), IOStandard("LVCMOS33")),
    ("pwm1", 0, Pins("53"), IOStandard("LVCMOS33")),
]

# Expansion Connectors
_connectors = [
    # J6: GPIO expansion header
    [
        "J6",
        "38 37 36 39 "  # SPI SD card
        "25 26 27 28 29 30 33 34 "  # GPIO
        "40 35 "  # I2C
        "41 42 "  # UART
        "51 53 "  # PWM
        "54 55 56 57 "  # Additional pins
        "68 69"  # HDMI clock
    ],
    
    # J7: LCD and additional expansion
    [
        "J7",
        "63 "  # Unknown
        "86 85 84 83 82 81 80 "  # Additional pins
        "79 77 76 "  # SPI LCD
        "75 74 73 72 71 70 "  # HDMI data
        "- "  # Not connected
        "48 49 "  # LCD control
        "31 32 "  # Additional
        "- -"  # Not connected
    ],
]


class Platform(GowinPlatform):
    """
    Tang Nano 9K FPGA Platform
    
    Board specifications:
    - FPGA: Gowin GW1NR-9C (GW1NR-LV9QN88PC6/I5)
    - LUTs: 8640
    - Flip-Flops: 6480
    - Block RAM: 468 Kbits (26 blocks)
    - User Flash: 608 Kbits
    - PLLs: 2
    - PSRAM: 2x 32Mbit (64Mbit total)
    - I/O: 62 user I/Os
    """
    
    default_clk_name = "clk27"
    default_clk_period = 1e9 / 27e6  # 27 MHz = 37.037 ns
    
    def __init__(self, toolchain="gowin"):
        """
        Initialize Tang Nano 9K platform
        
        Args:
            toolchain: FPGA toolchain ("gowin" or "apicula")
        """
        GowinPlatform.__init__(
            self,
            "GW1NR-LV9QN88PC6/I5",
            _io,
            _connectors,
            toolchain=toolchain,
            devicename="GW1NR-9C"
        )
        
        # Enable Multi-Purpose SPI pins as GPIO
        self.toolchain.options["use_mspi_as_gpio"] = 1
    
    def create_programmer(self, kit="openfpgaloader"):
        """
        Create programmer for bitstream loading
        
        Args:
            kit: Programming tool ("openfpgaloader" or "gowin")
        
        Returns:
            Programmer instance
        """
        if kit == "gowin":
            return GowinProgrammer(self.devicename)
        else:
            # Use OpenFPGALoader with FT2232 cable (built-in on Tang Nano 9K)
            return OpenFPGALoader(cable="ft2232")
    
    def do_finalize(self, fragment):
        """Finalize platform configuration"""
        GowinPlatform.do_finalize(self, fragment)
        
        # Add timing constraint for 27 MHz clock
        self.add_period_constraint(
            self.lookup_request("clk27", loose=True),
            1e9 / 27e6
        )
