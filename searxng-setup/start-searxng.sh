#!/bin/bash

# SearXNG startup script

echo "Starting SearXNG with Valkey dependency..."

cd /home/todd/searxng-setup

# Start the services using Docker Compose
docker-compose up -d

echo "SearXNG and Redis are now running."
echo "Access SearXNG at: http://localhost:8080"
echo "To stop: docker-compose down"