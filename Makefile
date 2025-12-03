IMAGE_NAME := riscv
CONTAINER_NAME := riscv

.PHONY: build run clean help env

help:
	@echo "Commands:"
	@echo "  build    - Builds the Docker image"
	@echo "  env      - Opens a dev shell in the image"
	@echo "  run      - Builds SoC (same env as 'env' + auto cpu.py --build)"
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

run: build
	docker run --rm -it \
		-v "$(shell pwd)":/workspace \
		-w /workspace \
		--name $(CONTAINER_NAME) \
		-e PYTHON=/opt/venv/bin/python3 \
		-e GOWIN_HOME=/workspace/IDE \
		$(IMAGE_NAME) \
		bash -lc '/opt/venv/bin/python3 cpu.py --build'


clean:
	docker rmi $(IMAGE_NAME) || true
