BOARD ?= tang_nano_9k
NO_EXTERNAL_RAM ?= 0
DOCKER_IMAGE := mutau-soc
WORKSPACE := $(shell pwd)
KERNEL ?= "/path/to/kernel"

# Hack to fix litex_term for now. #FIXME later
ifeq ($(NO_EXTERNAL_RAM),1)
	KERNEL_ADR = 0x10000000
else
	KERNEL_ADR = 0x40000000
endif

# Default serial port inside container (host /dev is bind-mounted)
PORT ?= /dev/ttyUSB1

ifdef CI
    DOCKER_FLAGS := --rm
else
    DOCKER_FLAGS := --rm -it
endif

USB_DOCKER_FLAGS := --privileged -v /dev:/dev

# Build flags based on configuration
ifeq ($(NO_EXTERNAL_RAM),1)
    BUILD_FLAGS := --no-external-ram
else
    BUILD_FLAGS :=
endif

.PHONY: help setup docker-build build flash load shell terminal upload clean

help:
	@echo "muTau RISC-V SoC Build System"
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Initialize git submodules"
	@echo "  docker-build   - Build Docker image"
	@echo ""
	@echo "Build:"
	@echo "  build          - Build bitstream for $(BOARD)"
	@echo "  flash          - Flash to board"
	@echo "  load           - Load to SRAM (temporary)"
	@echo "  shell          - Open Docker shell"
	@echo "  terminal       - Open serial terminal"
	@echo "  upload         - Upload kernel via serialboot"
	@echo "  clean          - Clean build artifacts"
	@echo ""
	@echo "Variables:"
	@echo "  BOARD=$(BOARD)"
	@echo "  NO_EXTERNAL_RAM=$(NO_EXTERNAL_RAM) (0=use external RAM, 1=SRAM only)"
	@echo "  KERNEL=$(KERNEL)"
	@echo "  PORT=$(PORT)"

setup:
	git submodule update --init --recursive

docker-build:
	docker build -t $(DOCKER_IMAGE) -f docker/Dockerfile .

build: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH" && python3 -m soc.builder --board $(BOARD) $(BUILD_FLAGS) --build'

flash: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		$(USB_DOCKER_FLAGS) \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH" && python3 -m soc.builder --board $(BOARD) --flash'

load: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		$(USB_DOCKER_FLAGS) \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH" && python3 -m soc.builder --board $(BOARD) --load'

shell: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash

terminal: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		$(USB_DOCKER_FLAGS) \
		$(DOCKER_IMAGE) \
		bash -c 'echo "Press Ctrl+A then Ctrl+X to exit" && picocom -b 115200 $(PORT)'

upload: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(abspath $(KERNEL))":/kernel.bin \
		$(USB_DOCKER_FLAGS) \
		$(DOCKER_IMAGE) \
		litex_term $(PORT) --kernel-adr $(KERNEL_ADR) --kernel /kernel.bin

clean:
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
