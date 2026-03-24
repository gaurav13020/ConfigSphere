#!/bin/bash

# ConfigSphere Quick Start Script
# This script sets up and starts ConfigSphere with Docker Compose

set -e

echo "======================================"
echo "ConfigSphere - Quick Start"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please ensure Docker Desktop is installed properly."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Navigate to backend directory
cd backend

echo "📦 Building and starting services..."
echo ""

# Build and start services
docker compose up --build

# Note: The script will continue running the services
# Press Ctrl+C to stop
