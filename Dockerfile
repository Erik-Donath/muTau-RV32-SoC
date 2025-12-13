FROM debian:bookworm-slim AS base

# System dependencies installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential cmake pkg-config \
    # Python and tools
    python3 python3-pip python3-venv python3-dev \
    # Meson backend for LiteX software
    ninja-build \
    # Network and download tools
    wget curl ca-certificates git \
    # GUI / OpenGL / X11 / NSS / font stack needed by Gowin gw_sh
    libgl1-mesa-glx libx11-6 libxext6 libxrender1 libxtst6 libxcomposite1 \
    libxdamage1 libxrandr2 libxkbcommon0 libdbus-1-3 libglib2.0-0 libnss3 \
    zlib1g libasound2 libfontconfig1 \
    # APT cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Stage 1: Python Environment with LiteX
FROM base AS python-env
RUN python3 -m venv /opt/litex-venv
ENV VIRTUAL_ENV="/opt/litex-venv"
ENV PATH="/opt/litex-venv/bin:$PATH"

# Upgrade pip and install Python dependencies (Meson)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir meson

# Install LiteX ecosystem
WORKDIR /tmp
RUN wget -q https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py && \
    chmod +x litex_setup.py && \
    ./litex_setup.py --init --install --config=standard && \
    rm -rf /tmp/litex_setup.py

# Stage 2: RISC-V Toolchain
FROM python-env AS riscv-tools

WORKDIR /tmp
RUN wget -q https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz && \
    tar -xzf riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz -C /opt && \
    mv /opt/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14 /opt/riscv-toolchain && \
    rm riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz

RUN mkdir -p /opt/riscv-bin && \
    cd /opt/riscv-bin && \
    for tool in gcc g++ ar as ld objcopy objdump ranlib readelf size strip nm; do \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv64-unknown-elf-${tool}; \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv-none-elf-${tool}; \
        ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-${tool} riscv32-unknown-elf-${tool}; \
    done && \
    ln -sf /opt/riscv-toolchain/bin/riscv64-unknown-elf-ar riscv64-unknown-elf-gcc-ar

# Final runtime image
FROM riscv-tools AS runtime
WORKDIR /workspace

ENV VIRTUAL_ENV="/opt/litex-venv"
ENV PYTHONUNBUFFERED=1

RUN ln -sf /usr/bin/python3 /usr/local/bin/python

ENV PATH="/opt/litex-venv/bin:/usr/local/bin:/usr/bin:/bin:/opt/riscv-bin:/opt/riscv-toolchain/bin:/opt/riscv-toolchain/riscv64-unknown-elf/bin"

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
