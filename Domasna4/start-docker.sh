#!/bin/bash

# CryptoInfo Docker Quick Start Script

echo "🚀 Starting CryptoInfo Application with Docker Compose"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null

echo ""
echo "🏗️  Building and starting services..."
echo "This may take 5-10 minutes on first run..."
echo ""

# Build and start all services
docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend:    http://localhost:3000"
    echo "   Backend API: http://localhost:8080/api"
    echo "   Health:      http://localhost:8080/api/health"
    echo ""
    echo "📝 View logs with: docker-compose logs -f"
    echo "🛑 Stop services with: docker-compose down"
    echo ""
    echo "⏳ Waiting for services to be fully ready..."
    echo "   (This may take 1-2 minutes for database initialization)"
    echo ""
    
    # Wait for backend health check
    for i in {1..30}; do
        if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        echo "   Waiting... ($i/30)"
        sleep 2
    done
    
    echo ""
    echo "🎉 Application is ready to use!"
else
    echo ""
    echo "❌ Failed to start services. Check logs with: docker-compose logs"
    exit 1
fi

