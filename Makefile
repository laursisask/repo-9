

DOCKER_EXECUTABLE := podman

IMAGE_NAME := m3-modular-admin
IMAGE_TAG := latest

image:
	$(DOCKER_EXECUTABLE) build -t $(IMAGE_NAME):$(IMAGE_TAG) .

clear:
	-rm modular_api.log modular_api_cli.log


clean-installed-modules:
	-rm -r modular_api/modules
	-rm modular_api/web_service/commands_base.json