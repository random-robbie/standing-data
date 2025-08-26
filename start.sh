#!/bin/bash

# Aviation Standing Data API Startup Script
# This script builds and starts the API service with nginx frontend

set -e

echo "🛩️  Starting Aviation Standing Data API..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker compose is available
if ! command -v docker compose &> /dev/null; then
    echo "❌ docker compose is not installed. Please install docker compose and try again."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run this script from the standing-data directory."
    exit 1
fi

echo "🔨 Building containers..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Wait for services to be healthy
echo "🔍 Checking service health..."
timeout=60
elapsed=0

while [ $elapsed -lt $timeout ]; do
    if docker compose ps | grep -q "healthy"; then
        break
    fi
    echo "   Waiting for services to be ready... (${elapsed}s)"
    sleep 5
    elapsed=$((elapsed + 5))
done

# Check final status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "🎉 Aviation Standing Data API is now running!"
echo ""
echo "🌐 Access points:"
echo "   Web Interface:     http://localhost:30000"
echo "   API Documentation: http://localhost:30000/docs"
echo "   Health Check:      http://localhost:30000/health"
echo ""
echo "📝 Useful commands:"
echo "   View logs:         docker compose logs -f"
echo "   Stop services:     docker compose down"
echo "   Rebuild:           docker compose up --build -d"
echo ""
echo "🔧 API Endpoints:"
echo "   GET /aircraft      - Search aircraft"
echo "   GET /airlines      - List airlines"
echo "   GET /airports      - Search airports"
echo "   GET /routes        - Search routes"
echo "   GET /countries     - List countries"
echo "   GET /model-types   - List aircraft models"
echo ""

# Test the API
echo "🧪 Testing API connectivity..."
if curl -s -f http://localhost:30000/health > /dev/null; then
    echo "✅ API is responding correctly"
else
    echo "⚠️  API may not be fully ready yet. Check logs with: docker compose logs"
fi

echo ""
echo "Ready for takeoff! ✈️"