# Variables
ARCH := $(shell uname -m)
IMAGE_NAME = gps-mqtt-app
CONTAINER_NAME = gps-mqtt-app
REPO_ADDRESS = localhost:5000
BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
GITHASH := $(shell git rev-parse --short HEAD)
HEXTIME := $(shell bash create_ver.sh)
TAG := $(IMAGE_NAME):$(ARCH)-$(BRANCH)-$(HEXTIME)-$(GITHASH)
DOCS_DIR ?= doc

version:
	@echo "$(BRANCH)-$(HEXTIME)-$(GITHASH)" > VERSION
	@cat VERSION
# Build the Docker image
build: version
	docker build -t $(TAG) .
	docker tag $(TAG) $(REPO_ADDRESS)/$(TAG)
ifeq ($(BRANCH),master)
	docker tag $(TAG) $(REPO_ADDRESS)/$(IMAGE_NAME):$(ARCH)-stable
	docker tag $(TAG) $(REPO_ADDRESS)/$(IMAGE_NAME):stable
endif
ifeq ($(BRANCH),dev)
	docker tag $(TAG) $(REPO_ADDRESS)/$(IMAGE_NAME):$(ARCH)-latest
	docker tag $(TAG) $(REPO_ADDRESS)/$(IMAGE_NAME):latest
endif

# Push the Docker image to the repository
push:
	docker push $(REPO_ADDRESS)/$(TAG)
ifeq ($(BRANCH),master)
	docker push $(REPO_ADDRESS)/$(IMAGE_NAME):$(ARCH)-stable
	docker push $(REPO_ADDRESS)/$(IMAGE_NAME):stable
endif
ifeq ($(BRANCH),dev)
	docker push $(REPO_ADDRESS)/$(IMAGE_NAME):$(ARCH)-latest
	docker push $(REPO_ADDRESS)/$(IMAGE_NAME):latest
endif

# Stop the Docker container
stop:
	docker stop $(CONTAINER_NAME) || true

# Remove the Docker container
remove:
	docker rm $(CONTAINER_NAME) || true

# Run the Docker container
run:
	docker run -d --name $(CONTAINER_NAME) --restart=unless-stopped --network host $(REPO_ADDRESS)/$(TAG)

# Cleanup old Docker images
cleanup:
	# Remove all images except the ones matching the current tag
	docker image prune -f
	# Optional: remove dangling images and unused images
	docker image prune -af --filter "until=24h"

# Rebuild the Docker image and restart the container
restart: build stop remove run cleanup

debug: version
	python3 -d app.py
