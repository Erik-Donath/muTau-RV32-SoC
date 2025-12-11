"""HyperBus / HyperRAM Core"""

from .controller import HyperRAMController


def create_hyperram_controller(pads):
    """
    Convenience helper to create a HyperRAM controller with default latency.

    Boards that have HyperBus-capable RAM can use this to implement
    add_main_memory() and expose HyperRAM as main RAM.
    """
    # You can tune latency globally here if needed.
    return HyperRAMController(pads=pads, latency=6)

__all__ = ["HyperRAMController", "create_hyperram_controller"]
