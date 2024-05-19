# Variables
ARCH := $(shell uname -m)
IMAGE_NAME = gps-mqtt-app
CONTAINER_NAME = gps-mqtt-app
REPO_ADDRESS = localhost:5000
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
TAG := $(IMAGE_NAME):$(ARCH)-$(BRANCH)

# Build the Docker image
build:
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

# Run the Docker container
run:
	docker run -d --name $(CONTAINER_NAME) --network host $(REPO_ADDRESS)/$(TAG)

# Start the Docker container if it has been stopped
start:
	docker start $(CONTAINER_NAME)

# Stop the Docker container
stop:
	docker stop $(CONTAINER_NAME)

# Remove the Docker container
remove:
	docker rm $(CONTAINER_NAME)

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

# Rebuild the Docker image and restart the container
restart: stop remove build push run
