#!/bin/bash
# Script to run integration tests in Docker Compose environment

set -e

echo "Starting services with Docker Compose..."
docker-compose up -d

echo "Waiting for services to be healthy..."
sleep 10

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    echo "Waiting for backend..."
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "ERROR: Backend did not become ready in time"
    docker-compose logs backend
    docker-compose down
    exit 1
fi

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "Frontend is ready!"
        break
    fi
    echo "Waiting for frontend..."
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "ERROR: Frontend did not become ready in time"
    docker-compose logs frontend
    docker-compose down
    exit 1
fi

echo "Running integration tests..."
cd "$(dirname "$0")"
python -m pytest tests/ -v -m integration --tb=short

TEST_EXIT_CODE=$?

echo "Stopping services..."
docker-compose down

exit $TEST_EXIT_CODE

