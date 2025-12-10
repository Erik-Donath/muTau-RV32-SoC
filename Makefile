IMAGE_NAME := riscv
CONTAINER_NAME := riscv

.PHONY: build run clean help env flash load

help:
	@echo "Commands:"
	@echo "  build    - Builds the Docker image"
	@echo "  env      - Opens a dev shell in the image"
	@echo "  run      - Builds SoC (same env as 'env' + auto cpu.py --build)"
	@echo "  flash    - Flash bitstream and BIOS to board"
	@echo "  load     - Load bitstream to SRAM (temporary)"
	@echo "  clean    - Removes the Docker image"

build:
	docker build -t $(IMAGE_NAME) .

# Interactive dev environment
env: build
	docker run --rm -it \
		-v "$(shell pwd)":/workspace \
		-w /workspace \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME) \
		bash

# Non-interactive build, same container shape as env
run: build
	docker run --rm -it \
		-v "$(shell pwd)":/workspace \
		-w /workspace \
		--name $(CONTAINER_NAME) \
		-e PYTHON=/opt/venv/bin/python3 \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/lib/x86_64-linux-gnu/libfreetype.so.6:/usr/lib/x86_64-linux-gnu/libz.so" \
		$(IMAGE_NAME) \
		bash -lc 'export PATH="/workspace/IDE/bin:$$PATH"; /opt/venv/bin/python3 cpu.py --build'

# Flash to persistent storage
flash: build
	docker run --rm -it \
		-v "$(shell pwd)":/workspace \
		-w /workspace \
		--privileged \
		--device=/dev/bus/usb \
		--name $(CONTAINER_NAME) \
		-e PYTHON=/opt/venv/bin/python3 \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/lib/x86_64-linux-gnu/libfreetype.so.6:/usr/lib/x86_64-linux-gnu/libz.so" \
		$(IMAGE_NAME) \
		bash -lc 'export PATH="/workspace/IDE/bin:$$PATH"; /opt/venv/bin/python3 cpu.py --flash --bios-flash-offset=0x40000'

# Load to SRAM (temporary, for testing)
load: build
	docker run --rm -it \
		-v "$(shell pwd)":/workspace \
		-w /workspace \
		--privileged \
		--device=/dev/bus/usb \
		--name $(CONTAINER_NAME) \
		-e PYTHON=/opt/venv/bin/python3 \
		-e GOWIN_HOME=/workspace/IDE \
		-e QT_QPA_PLATFORM=offscreen \
		-e LD_PRELOAD="/lib/x86_64-linux-gnu/libfreetype.so.6:/usr/lib/x86_64-linux-gnu/libz.so" \
		$(IMAGE_NAME) \
		bash -lc 'export PATH="/workspace/IDE/bin:$$PATH"; /opt/venv/bin/python3 cpu.py --load'

clean:
	docker rmi $(IMAGE_NAME) || true
