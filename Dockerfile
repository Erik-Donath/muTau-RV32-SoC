FROM debian:bookworm-slim AS base

# System dependencies installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential cmake ninja-build meson pkg-config \
    # Compilers (g++ for host compilation)
    g++ gcc binutils \
    # Python and tools
    python3 python3-pip python3-venv python3-dev python3-full \
    # Network and download tools
    wget curl ca-certificates git \
    # FPGA tools
    yosys verilator openfpgaloader \
    # Development libraries
    libevent-dev libjson-c-dev libboost-dev libboost-filesystem-dev \
    libboost-thread-dev libboost-program-options-dev libboost-iostreams-dev \
    libeigen3-dev tcl-dev libreadline-dev libffi-dev \
    # Compiler toolchain
    clang llvm bison flex \
    # GUI/Qt dependencies for headless GOWIN IDE
    libgl1-mesa-glx libxtst6 libasound2 libfreetype6 zlib1g \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Stage 1: Python Environment with LiteX
FROM base AS python-env
RUN python3 -m venv /opt/litex-venv
ENV VIRTUAL_ENV="/opt/litex-venv"
ENV PATH="/opt/litex-venv/bin:$PATH"

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir apycula

# Install LiteX ecosystem
WORKDIR /tmp
RUN wget -q https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py && \
    chmod +x litex_setup.py && \
    ./litex_setup.py --init --install --config=standard && \
    rm -rf /tmp/litex_setup.py

# Stage 2: nextpnr-himbaechel (build BEFORE RISC-V toolchain to avoid conflicts)
FROM python-env AS nextpnr-build

WORKDIR /tmp

# Clone and build nextpnr for GOWIN FPGAs
RUN git clone --recursive --depth 1 https://github.com/YosysHQ/nextpnr.git && \
    cd nextpnr && \
    mkdir build && cd build && \
    cmake .. \
        -DARCH=himbaechel \
        -DHIMBAECHEL_UARCH=gowin \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    cd /tmp && rm -rf nextpnr

# Stage 3: RISC-V Toolchain (installed AFTER nextpnr to avoid PATH conflicts)
FROM nextpnr-build AS riscv-tools

WORKDIR /tmp

# Download and install RISC-V GCC toolchain
RUN wget -q https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz && \
    tar -xzf riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz -C /opt && \
    mv /opt/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14 /opt/riscv-toolchain && \
    rm riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz

# Create symlinks in /opt/riscv-bin to avoid PATH pollution
RUN mkdir -p /opt/riscv-bin && \
    cd /opt/riscv-bin && \
    for tool in gcc g++ ar as ld objcopy objdump ranlib readelf size strip nm; do \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv64-unknown-elf-${tool}; \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv-none-elf-${tool}; \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv32-unknown-elf-${tool}; \
    done && \
    ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-ar riscv64-unknown-elf-gcc-ar

# Stage 4: Final Runtime Image
FROM riscv-tools AS runtime
WORKDIR /workspace

# Configure environment for headless GOWIN IDE operation
ENV QT_QPA_PLATFORM=offscreen
ENV LD_PRELOAD="/lib/x86_64-linux-gnu/libfreetype.so.6:/usr/lib/x86_64-linux-gnu/libz.so"

# Configure Python environment
ENV VIRTUAL_ENV="/opt/litex-venv"
ENV PYTHONUNBUFFERED=1

# Ensure Python3 is available as both python3 and python
RUN ln -sf /usr/bin/python3 /usr/local/bin/python

# Set PATH: venv first, then RISC-V tools at the END to avoid conflicts with system tools
ENV PATH="/opt/litex-venv/bin:/usr/local/bin:/usr/bin:/bin:/opt/riscv-bin:/opt/riscv-toolchain/bin:/opt/riscv-toolchain/riscv64-unknown-elf/bin"

# Create directory for runtime venv in workspace (will be created if needed)
RUN mkdir -p /workspace/.venv

# Add entrypoint script to ensure venv is properly activated
RUN echo '#!/bin/bash\n\
# Activate system-wide LiteX venv\n\
source /opt/litex-venv/bin/activate\n\
\n\
# If project-specific venv exists in workspace, use it\n\
if [ -d "/workspace/.venv" ] && [ -f "/workspace/.venv/bin/activate" ]; then\n\
    source /workspace/.venv/bin/activate\n\
fi\n\
\n\
# Execute provided command or default to bash\n\
exec "$@"\n' > /entrypoint.sh && \
chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
