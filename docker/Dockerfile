FROM debian:bookworm-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config \
    python3 python3-pip python3-venv python3-dev \
    ninja-build \
    wget curl ca-certificates git \
    libgl1-mesa-glx libx11-6 libxext6 libxrender1 libxtst6 libxcomposite1 \
    libxdamage1 libxrandr2 libxkbcommon0 libdbus-1-3 libglib2.0-0 libnss3 \
    zlib1g libasound2 libfontconfig1 \
    openfpgaloader picocom \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

FROM base AS riscv-tools

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

FROM riscv-tools AS litex-deps

WORKDIR /opt

RUN git clone https://github.com/m-labs/migen.git && \
    git clone https://github.com/litex-hub/pythondata-software-compiler_rt.git pythondata_software_compiler_rt && \
    git clone https://github.com/litex-hub/pythondata-software-picolibc.git pythondata_software_picolibc && \
    git clone https://github.com/litex-hub/pythondata-cpu-vexriscv.git pythondata_cpu_vexriscv && \
    cd pythondata_software_picolibc && git submodule update --init --recursive

FROM litex-deps AS python-env

COPY litex /opt/litex
COPY docker/requirements.txt /tmp/requirements.txt

RUN cd /opt/litex/litex/soc/cores/cpu && \
    find . -mindepth 1 -maxdepth 1 -type d ! -name 'vexriscv' -exec rm -rf {} +

RUN python3 -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

FROM python-env AS runtime

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PYTHONPATH=/opt/litex:/opt/migen:/opt/pythondata_software_compiler_rt:/opt/pythondata_software_picolibc:/opt/pythondata_cpu_vexriscv
ENV PATH="/opt/venv/bin:/opt/riscv-bin:/opt/riscv-toolchain/bin:/opt/riscv-toolchain/riscv64-unknown-elf/bin:/usr/local/bin:/usr/bin:/bin"

RUN ln -sf /usr/bin/python3 /usr/local/bin/python

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
