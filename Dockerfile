# Stage 1: Base system and dependencies
FROM debian:bookworm-slim AS base

ARG ENV=prod

RUN apt-get update && apt-get install -y --no-install-recommends \
    yosys \
    python3-pip python3-venv python3-full build-essential wget curl git \
    libevent-dev libjson-c-dev verilator ca-certificates tar meson ninja-build \
    cmake clang llvm python3-dev libboost-dev libboost-filesystem-dev libboost-thread-dev libboost-program-options-dev libboost-iostreams-dev libeigen3-dev \
    tcl-dev libreadline-dev libffi-dev bison flex pkg-config \
    yosys openfpgaloader libgl1-mesa-glx libxtst6 libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Stage 2: Python environment with LiteX installed
FROM base AS python-lite

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install Python deps into the venv (no extra symlinks)
RUN python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip install migen apycula --timeout 100 --retries 3

WORKDIR /opt

RUN wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py \
    && chmod +x litex_setup.py \
    && python3 litex_setup.py --init --install --config=standard \
    && rm litex_setup.py

# Stage 3: RISC-V Toolchain
FROM python-lite AS riscv-toolchain

RUN curl -L https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz \
    -o riscv64-unknown-elf-gcc.tar.gz \
    && tar -xf riscv64-unknown-elf-gcc.tar.gz -C /opt \
    && rm riscv64-unknown-elf-gcc.tar.gz

ENV PATH="/opt/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14/bin:${PATH}"

# Stage 4: nextpnr-himbaechel build and install
FROM riscv-toolchain AS nextpnr

RUN git clone --recursive https://github.com/YosysHQ/nextpnr.git /opt/nextpnr \
    && mkdir -p /opt/nextpnr/build \
    && cd /opt/nextpnr/build \
    && cmake .. -DARCH="himbaechel" -DHIMBAECHEL_UARCH="gowin" \
    && make -j"$(nproc)" \
    && make install

# Stage 5: Final image with Gowin Toolchain
FROM nextpnr

# Use the venv Python at runtime
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace

COPY IDE /workspace/IDE

ENV QT_QPA_PLATFORM=offscreen
ENV PATH="/workspace/IDE/bin:${PATH}"

RUN if [ -d "/workspace/IDE/bin" ]; then \
      echo "Setting execute permission on files in /workspace/IDE/bin" && \
      find "/workspace/IDE/bin" -maxdepth 1 -type f -exec chmod a+x '{}' \; 2>/dev/null || true; \
    fi

CMD ["/bin/bash"]
