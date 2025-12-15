BOARD ?= tang_nano_9k
FIRMWARE ?= bios
DOCKER_IMAGE := mutau-soc
WORKSPACE := $(shell pwd)
KERNEL ?= "invalid kernel"

ifdef CI
    DOCKER_FLAGS := --rm
else
    DOCKER_FLAGS := --rm -it
endif

USB_DOCKER_FLAGS := --privileged -v /dev:/dev

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
	@echo "  FIRMWARE=$(FIRMWARE)"
	@echo "  KERNEL=$(KERNEL)"

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
		bash -c 'export PATH="/workspace/IDE/bin:$$PATH" && python3 -m soc.builder --board $(BOARD) --firmware $(FIRMWARE) --build'

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

terminal:
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		$(USB_DOCKER_FLAGS) \
		$(DOCKER_IMAGE) \
		bash -c 'echo "Press Ctrl+A then Ctrl+X to exit" && picocom -b 115200 /dev/ttyUSB1'

upload: docker-build
	docker run $(DOCKER_FLAGS) \
		-v "$(WORKSPACE)":/workspace \
		-w /workspace \
		$(USB_DOCKER_FLAGS) \
		$(DOCKER_IMAGE) \
		litex_term --kernel $(KERNEL)

clean:
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
