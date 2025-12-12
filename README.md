# RiscV-SoC

[![CodeQL](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/github-code-scanning/codeql)
[![Build](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/build.yml/badge.svg)](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/build.yml)
[![Pages](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/pages.yml/badge.svg)](https://github.com/Erik-Donath/RiscV-SoC/actions/workflows/pages.yml)

A small, modular RISC‑V System‑on‑Chip built with [LiteX](https://github.com/enjoy-digital/litex) for Gowin FPGA boards (e.g. Tang Nano 9K, Tang Primer 25K).  
The project includes board support, basic peripherals, and a simple build flow using Make.

## Prerequisites

- Gowin EDA (Education Edition)
- A supported Gowin FPGA board (with USB‑UART)
- Python 3 and standard build tools (`make`, `git`, etc.)

To enable synthesis and bitstream generation, copy the `IDE` directory from your Gowin EDA installation into the root of this repository.


# Use 
To use the Project and the build tools you need to download the gowin-eda (education) from there website and place the `IDE` directory in the root of this project.

```bash
make build # Build the Enviroment and then build the litex project
make flash # or make load to temporarly load
make terminal # to connect to the FPGA (USB UART Port)
```

## Repository structure
- `boards/` – Board support (platform, pinout, peripherals)
- `cores/` – Reusable hardware cores (e.g. HyperBus/HyperRAM)
- `soc/` – SoC definition, clocking, builder and configuration
- `firmware/` – Baremetal and BIOS firmware targets
- `docs/` – Documentation sources (LaTeX, images)
- `pages/` - Github Pages site
