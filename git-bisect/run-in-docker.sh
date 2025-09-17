#!/bin/bash

# Exit on any error
set -e

# Configuration - Replace with your actual container ID
CONTAINER_ID=$1

echo "Running tests in Docker container ${CONTAINER_ID}..."

# Check if container is running
if ! docker ps -q --filter "id=${CONTAINER_ID}" | grep -q "${CONTAINER_ID}"; then
    echo "Error: Container ${CONTAINER_ID} is not running"
    echo "Please start the container first"
    exit 1
fi

# Copy test files to container if needed (optional)
# docker cp ./test-files ${CONTAINER_ID}:/app/

# Run your test commands in the container
echo "Executing test commands in container..."

# Example test commands - replace with your actual tests
if docker exec ${CONTAINER_ID} /bin/bash -c "
    set -e

    /root/docker-run.sh

    echo 'All tests completed successfully'
"; then
    echo "Docker tests passed"
    exit 0
else
    echo "Docker tests failed"
    exit 1
fi
