#!/bin/bash

# Check if a branch name is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <branch-name>"
  exit 1
fi

BRANCH=$1

# Change to the directory where your code is located
cd v2

# Pull the latest changes from the specified branch
git checkout $BRANCH
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    git pull origin $BRANCH

    if [ $? -eq 0 ]; then
        echo "Updates found and applied. Building new Docker image using Makefile..."

        # Use the Makefile to build, push, and run the Docker image
        make BRANCH=$BRANCH restart

        echo "New Docker image built and container restarted."
    else
        echo "Failed to pull updates."
    fi
else
    echo "No updates found."
fi
