"""
Optimized HyperRAM Controller for LiteX
Improved version with better documentation and configurability

Copyright (c) 2019-2025 Antti Lukats, Florent Kermarrec, Franck Jullien
SPDX-License-Identifier: BSD-2-Clause
"""

from migen import (
    Module, Signal, If, Case, Cat, TSTriple,
    ClockDomain
)
from migen.genlib.misc import timeline
from litex.build.io import DifferentialOutput
from litex.soc.interconnect import wishbone


class HyperRAM(Module):
    """
    Portable HyperRAM Memory Controller
    
    Features:
    - FPGA vendor agnostic implementation
    - Supports 8-bit and 16-bit data widths
    - Configurable latency (default: 6 cycles)
    - Simple Wishbone interface
    - No chip-specific initialization required
    
    This controller prioritizes portability and simplicity over maximum
    performance. It operates at sys_clk/4 to ensure reliable timing.
    
    Args:
        pads: HyperRAM physical pads (clk, cs_n, dq, rwds, rst_n)
        latency: Number of latency cycles (default: 6)
    """
    
    # Command-Address bit positions
    CA_RW_BIT = 47          # Read/Write bit (1=Read, 0=Write)
    CA_ADDRESS_SPACE = 46   # Address space (0=Memory, 1=Register)
    CA_BURST_TYPE = 45      # Burst type (1=Linear, 0=Wrapped)
    
    def __init__(self, pads, latency=6):
        self.pads = pads
        self.bus = wishbone.Interface()
        
        # Internal signals
        clk = Signal()
        clk_phase = Signal(2)
        cs = Signal()
        ca = Signal(48)  # Command-Address register
        ca_active = Signal()
        sr = Signal(48)  # Shift register for data
        
        # Handle different pad types (with/without explicit OE)
        dq = self._add_tristate(pads.dq) if not hasattr(pads.dq, "oe") else pads.dq
        rwds = self._add_tristate(pads.rwds) if not hasattr(pads.rwds, "oe") else pads.rwds
        
        dw = len(pads.dq) if not hasattr(pads.dq, "oe") else len(pads.dq.o)
        assert dw in [8, 16], f"Unsupported data width: {dw}"
        
        # Configure reset and chip select
        self._setup_control_signals(pads, cs, clk)
        
        # Generate clock at sys_clk/4
        self._setup_clock_generation(clk, clk_phase, cs)
        
        # Setup data shift register
        self._setup_data_path(dq, dw, sr, ca_active, clk_phase)
        
        # Generate command-address word
        self._setup_command_address(ca, dw)
        
        # Create access sequence
        self._setup_sequencer(
            clk_phase, cs, ca, ca_active,
            dq, rwds, sr, dw, latency
        )
    
    def _setup_control_signals(self, pads, cs, clk):
        """Configure reset, chip select, and clock outputs"""
        # Reset is always high (active)
        if hasattr(pads, "rst_n"):
            self.comb += pads.rst_n.eq(1)
        
        # Chip select (use first chip, disable second if present)
        self.comb += pads.cs_n[0].eq(~cs)
        if len(pads.cs_n) == 2:
            self.comb += pads.cs_n[1].eq(1)
        
        # Clock output (differential or single-ended)
        if hasattr(pads, "clk"):
            self.comb += pads.clk.eq(clk)
        else:
            self.specials += DifferentialOutput(clk, pads.clk_p, pads.clk_n)
    
    def _setup_clock_generation(self, clk, clk_phase, cs):
        """
        Generate HyperRAM clock at sys_clk/4
        Clock transitions on 90° and 270° phases
        """
        self.sync += clk_phase.eq(clk_phase + 1)
        
        cases = {
            1: clk.eq(cs),  # Rising edge at 90° (if CS active)
            3: clk.eq(0),   # Falling edge at 270°
        }
        self.sync += Case(clk_phase, cases)
    
    def _setup_data_path(self, dq, dw, sr, ca_active, clk_phase):
        """Setup bidirectional data shift register"""
        dqi = Signal(dw)
        
        # Sample input data on 90° and 270°
        self.sync += dqi.eq(dq.i)
        
        # Shift data on 0° and 180°
        self.sync += [
            If(
                (clk_phase == 0) | (clk_phase == 2),
                If(
                    ca_active,
                    # During CA phase, only lower 8 bits used
                    sr.eq(Cat(dqi[:8], sr[:-8]))
                ).Else(
                    # During data phase, use full width
                    sr.eq(Cat(dqi, sr[:-dw]))
                )
            )
        ]
        
        # Output assignments
        self.comb += [
            self.bus.dat_r.eq(sr),  # Read data to Wishbone
            If(
                ca_active,
                dq.o.eq(sr[-8:])    # CA phase: 8-bit output
            ).Else(
                dq.o.eq(sr[-dw:])   # Data phase: full width output
            )
        ]
    
    def _setup_command_address(self, ca, dw):
        """
        Generate HyperRAM command-address word
        
        CA Word structure (48 bits):
        [47]    R/W# (1=Read, 0=Write)
        [46]    Address Space (0=Memory, 1=Register)
        [45]    Burst Type (1=Linear, 0=Wrapped)
        [44:16] Row and Upper Column Address
        [15:3]  Reserved
        [2:0]   Lower Column Address
        """
        self.comb += [
            ca[self.CA_RW_BIT].eq(~self.bus.we),     # Read = 1, Write = 0
            ca[self.CA_BURST_TYPE].eq(1),             # Linear burst
        ]
        
        if dw == 8:
            # 8-bit mode addressing
            self.comb += [
                ca[16:45].eq(self.bus.adr[2:]),   # Row & upper column
                ca[1:3].eq(self.bus.adr[0:2]),    # Lower column
                ca[0].eq(0),
            ]
        else:  # dw == 16
            # 16-bit mode addressing
            self.comb += [
                ca[16:45].eq(self.bus.adr[3:]),   # Row & upper column
                ca[1:3].eq(self.bus.adr[1:3]),    # Lower column
                ca[0].eq(self.bus.adr[0]),
            ]
    
    def _setup_sequencer(
        self, clk_phase, cs, ca, ca_active,
        dq, rwds, sr, dw, latency
    ):
        """
        Create timed sequence for HyperRAM access
        
        Sequence:
        1. Idle
        2. Command-Address phase (6 clocks)
        3. Latency phase (configurable)
        4. Data phase (write or read)
        5. End and acknowledge
        """
        # Calculate latency in sys_clk cycles
        # Latency count starts from middle of CA phase (-4)
        # Fixed latency mode: 2 * latency cycles
        # 4 sys_clks per RAM clock
        lat_cycles = (latency * 8) - 4
        
        # Build delta-time sequence
        dt_sequence = self._build_access_sequence(
            cs, ca, ca_active, dq, rwds, sr, dw, lat_cycles
        )
        
        # Convert to absolute time sequence
        t_sequence = []
        t = 0
        for dt, actions in dt_sequence:
            t_sequence.append((t, actions))
            t += dt
        
        # Execute sequence on bus cycle with proper phase
        sequence_start = (clk_phase == 1)
        self.sync += timeline(
            self.bus.cyc & self.bus.stb & sequence_start,
            t_sequence
        )
    
    def _build_access_sequence(
        self, cs, ca, ca_active, dq, rwds, sr, dw, latency_cycles
    ):
        """Build the complete access sequence with delta times"""
        rwds_out = Signal(2)
        self.comb += rwds.o.eq(rwds_out)
        
        sequence = [
            # Initial delay
            (3, []),
            
            # Command-Address phase (6 RAM clocks = 24 sys_clks)
            (12, [
                cs.eq(1),
                dq.oe.eq(1),
                sr.eq(ca),
                ca_active.eq(1)
            ]),
            
            # Latency period
            (latency_cycles, [
                dq.oe.eq(0),
                ca_active.eq(0)
            ]),
        ]
        
        # Data phase (different for 8-bit vs 16-bit)
        if dw == 8:
            sequence.extend([
                # Byte 0
                (2, [
                    dq.oe.eq(self.bus.we),
                    sr[:16].eq(0),
                    sr[16:].eq(self.bus.dat_w),
                    rwds.oe.eq(self.bus.we),
                    rwds_out[0].eq(~self.bus.sel[3])
                ]),
                # Byte 1
                (2, [rwds_out[0].eq(~self.bus.sel[2])]),
                # Byte 2
                (2, [rwds_out[0].eq(~self.bus.sel[1])]),
                # Byte 3
                (2, [rwds_out[0].eq(~self.bus.sel[0])]),
            ])
        else:  # dw == 16
            sequence.extend([
                # Word 0 (bytes 3:2)
                (2, [
                    dq.oe.eq(self.bus.we),
                    sr[:16].eq(0),
                    sr[16:].eq(self.bus.dat_w),
                    rwds.oe.eq(self.bus.we),
                    rwds_out[1].eq(~self.bus.sel[3]),
                    rwds_out[0].eq(~self.bus.sel[2])
                ]),
                # Word 1 (bytes 1:0)
                (2, [
                    rwds_out[1].eq(~self.bus.sel[1]),
                    rwds_out[0].eq(~self.bus.sel[0])
                ]),
            ])
        
        # End sequence
        sequence.extend([
            # Deassert control signals
            (2, [
                cs.eq(0),
                rwds.oe.eq(0),
                dq.oe.eq(0)
            ]),
            # Assert acknowledge
            (1, [self.bus.ack.eq(1)]),
            # Deassert acknowledge
            (1, [self.bus.ack.eq(0)]),
            # Sequence end
            (0, [])
        ])
        
        return sequence
    
    def _add_tristate(self, pad):
        """Create tristate buffer for pad without explicit OE"""
        tristate = TSTriple(len(pad))
        self.specials += tristate.get_tristate(pad)
        return tristate
