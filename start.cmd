@echo off
REM ConfigSphere Quick Start Script for Windows
REM This script sets up and starts ConfigSphere with Docker Compose

echo ======================================
echo ConfigSphere - Quick Start
echo ======================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo X Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

echo + Docker is installed
REM Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo X Docker Compose is not available. Please ensure Docker Desktop is installed properly.
    exit /b 1
)

echo + Docker Compose is available
echo.

REM Navigate to backend directory
cd backend

echo Packaging and starting services...
echo.

REM Build and start services
docker compose up --build

REM Note: Press Ctrl+C to stop
