# Stage 1: Base system and dependencies
FROM debian:bookworm-slim AS base

ARG ENV=prod

RUN apt-get update && apt-get install -y --no-install-recommends \
    yosys \
    python3-pip python3-venv python3-full build-essential wget curl git \
    libevent-dev libjson-c-dev verilator ca-certificates tar meson ninja-build \
    cmake clang llvm python3-dev libboost-dev libboost-filesystem-dev \
    libboost-thread-dev libboost-program-options-dev libboost-iostreams-dev \
    libeigen3-dev tcl-dev libreadline-dev libffi-dev bison flex pkg-config \
    yosys openfpgaloader libgl1-mesa-glx libxtst6 libasound2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Stage 2: Python environment with LiteX installed
FROM base AS python-lite

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel apycula --timeout 100 --retries 3

WORKDIR /opt

RUN wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py \
 && chmod +x litex_setup.py \
 && ./litex_setup.py --init --install --config=standard \
 && rm litex_setup.py

# Stage 3: RISC-V Toolchain
FROM python-lite AS riscv-toolchain

WORKDIR /opt

RUN curl -L \
  https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz \
  -o riscv64-unknown-elf-gcc.tar.gz \
 && tar -xf riscv64-unknown-elf-gcc.tar.gz -C /opt \
 && rm riscv64-unknown-elf-gcc.tar.gz \
 && mv /opt/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14 /opt/riscv-tools

# Expose full toolchain bin + per-triple bin
ENV PATH="$PATH:/opt/riscv-tools/bin:/opt/riscv-tools/riscv64-unknown-elf/bin"

# Create exact binaries LiteX/meson expect
RUN ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-gcc      /usr/local/bin/riscv64-unknown-elf-gcc      && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-ar       /usr/local/bin/riscv64-unknown-elf-ar       && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-ranlib   /usr/local/bin/riscv64-unknown-elf-ranlib   && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-objcopy  /usr/local/bin/riscv64-unknown-elf-objcopy  && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-readelf  /usr/local/bin/riscv64-unknown-elf-readelf  && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-ar       /usr/local/bin/riscv64-unknown-elf-gcc-ar   && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-gcc      /usr/local/bin/riscv-sifive-elf-gcc         && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-ar       /usr/local/bin/riscv-sifive-elf-ar          && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-ranlib   /usr/local/bin/riscv-sifive-elf-ranlib      && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-objcopy  /usr/local/bin/riscv-sifive-elf-objcopy     && \
    ln -sf /opt/riscv-tools/bin/riscv64-unknown-elf-readelf  /usr/local/bin/riscv-sifive-elf-readelf

# Stage 4: nextpnr-himbaechel build and install
FROM riscv-toolchain AS nextpnr

WORKDIR /opt

RUN git clone --recursive https://github.com/YosysHQ/nextpnr.git /opt/nextpnr \
 && mkdir -p /opt/nextpnr/build \
 && cd /opt/nextpnr/build \
 && cmake .. -DARCH=himbaechel -DHIMBAECHEL_UARCH=gowin \
 && make -j"$(nproc)" \
 && make install

# Stage 5: Final runtime image with Gowin IDE
FROM nextpnr

WORKDIR /workspace

# Copy Gowin IDE from build context into the image.
COPY IDE /workspace/IDE

# Make IDE binaries executable
RUN if [ -d "/workspace/IDE/bin" ]; then \
      chmod -R a+rx /workspace/IDE/bin; \
    fi

# Headless Qt
ENV QT_QPA_PLATFORM=offscreen

# Use system freetype and zlib to avoid FT_Done_MM_Var symbol issue
ENV LD_PRELOAD="/lib/x86_64-linux-gnu/libfreetype.so.6:/usr/lib/x86_64-linux-gnu/libz.so"

# venv + host + RISC-V tools + Gowin IDE bin
ENV PATH="/opt/venv/bin:/opt/riscv-tools/bin:/opt/riscv-tools/riscv64-unknown-elf/bin:/workspace/IDE/bin:$PATH"

RUN if [ -x "/workspace/IDE/bin/gw_sh" ]; then \
      ln -sf /workspace/IDE/bin/gw_sh /usr/local/bin/gw_sh; \
    fi

CMD ["/bin/bash"]
