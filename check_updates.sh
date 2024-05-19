#!/bin/bash
SLEEPFOR=${SLEEPFOR:-1}
# Wait for 3 minutes after boot
sleep $SLEEPFOR

# Change to the directory where your code is located
cd v2 || exit

# Pull the latest changes from the GitHub repository
git fetch -a
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin)

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    git pull

    if [ $? -eq 0 ]; then
        echo "Updates found and applied. Building new Docker image using Makefile..."

        # Use the Makefile to build, push, and run the Docker image
        make restart

        echo "New Docker image built and container restarted."
    else
        echo "Failed to pull updates."
    fi
else
    echo "No updates found."
fi
