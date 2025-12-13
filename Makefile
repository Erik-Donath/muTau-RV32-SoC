# RISC-V SoC Build System
BOARD ?= tang_nano_9k
FIRMWARE ?= bios
DOCKER_IMAGE := riscv-soc
WORKSPACE := $(shell pwd)

# Detect if running in CI (GitHub Actions sets CI=true)
ifdef CI
    DOCKER_FLAGS := --rm
else
    DOCKER_FLAGS := --rm -it
endif

.PHONY: help build flash load terminal clean docker-build shell

help:
	@echo "RISC-V SoC Build System"
	@echo ""
	@echo "Targets:"
	@echo "  build          - Build bitstream for $(BOARD)"
	@echo "  flash          - Flash to board"
	@echo "  load           - Load to SRAM (temporary)"
	@echo "  terminal       - Open serial terminal"
	@echo "  shell          - Open Docker shell"
	@echo "  clean          - Clean build artifacts"
	@echo "  docker-build   - Build Docker image"
	@echo ""
	@echo "Variables:"
	@echo "  BOARD=$(BOARD)"
	@echo "  FIRMWARE=$(FIRMWARE)"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make flash"
	@echo "  make terminal"

docker-build:
	docker build -t $(DOCKER_IMAGE) -f Dockerfile .

build: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH"; python3 -m soc.builder --board $(BOARD) --firmware $(FIRMWARE) --build'

flash: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		--privileged \
		--device=/dev/bus/usb \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH"; python3 -m soc.builder --board $(BOARD) --flash'

load: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		--privileged \
		--device=/dev/bus/usb \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH"; python3 -m soc.builder --board $(BOARD) --load'

shell: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6" \
		$(DOCKER_IMAGE) \
		bash

terminal:
	@echo "Opening serial terminal on /dev/ttyUSB1..."
	@echo "Press Ctrl+A then Ctrl+X to exit picocom"
	@picocom -b 115200 /dev/ttyUSB1

clean:
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
