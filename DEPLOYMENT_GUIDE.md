# ConfigSphere - Complete Setup & Deployment Guide

A complete guide for setting up and deploying ConfigSphere with both backend and frontend components.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Setup (Development)](#manual-setup-development)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ConfigSphere System                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (React + TypeScript)          Backend (Django)    │
│  ┌──────────────────────────┐           ┌────────────────┐  │
│  │ Port: 3000               │           │ Port: 8000     │  │
│  │ - Dashboard              │◄─────────►│ API Endpoints  │  │
│  │ - Schemas Manager        │ CORS      │ - /schemas/    │  │
│  │ - Config Items           │ Enabled   │ - /config-items/
│  │ - Versions Manager       │           │ - /versions/   │  │
│  │ - Config Resolver        │           │ - /resolved/   │  │
│  │ - Audit Trail            │           │ - /audit/      │  │
│  └──────────────────────────┘           ├────────────────┤  │
│                                          │ Database       │  │
│                                          │ PostgreSQL 15  │  │
│                                          │ Port: 5432     │  │
│                                          └────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### System Requirements
- Docker Desktop (recommended for easiest setup)
- OR:
  - Python 3.10+
  - Node.js 16+
  - PostgreSQL 15
  - npm/yarn package manager

### Port Availability
- Port 3000 - React Frontend
- Port 8000 - Django Backend API
- Port 5432 - PostgreSQL Database

## 🚀 Quick Start with Docker

### Option 1: Using Docker Compose (Recommended)

```bash
# Navigate to backend directory (docker-compose is here)
cd backend

# Build and start all services (Frontend + Backend + Database)
docker compose up --build

# Wait for all services to start (you'll see output like):
# configsphere_db is now running
# configsphere_web is running
# configsphere_frontend is running
```

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **Database**: localhost:5432

To run initial migrations and seed data:

```bash
# In another terminal
docker compose exec web python manage.py migrate
docker compose exec web python manage.py loaddata initial_data  # if available
```

### Option 2: Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (careful - deletes database!)
docker compose down -v
```

### View Logs

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f web      # Backend
docker compose logs -f frontend # Frontend
docker compose logs -f db       # Database
```

## 🛠️ Manual Setup (Development)

### Backend Setup

#### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Create Environment File

```bash
# .env or export these
export DB_NAME=configsphere
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DJANGO_SECRET_KEY=your-secret-key-here
export DJANGO_SETTINGS_MODULE=config_sphere.settings.local
```

#### 3. Initialize Database

```bash
# Make sure PostgreSQL is running
python manage.py migrate
```

#### 4. Run Backend Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Create Environment File

```bash
# .env
VITE_API_URL=http://localhost:8000/api/v1
```

#### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📚 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently, the API allows all requests (AllowAny permission). In production, implement authentication.

### Main Endpoints

#### Schemas
```
GET    /schemas/              - List all schemas
POST   /schemas/              - Create schema
GET    /schemas/{id}/         - Get schema by ID
```

#### Config Items
```
GET    /config-items/         - List config items
POST   /config-items/         - Create config item
GET    /config-items/{id}/    - Get config item by ID
```

#### Config Versions
```
GET    /config-items/{id}/versions/           - List versions
POST   /config-items/{id}/versions/           - Create version
GET    /config-versions/{id}/                 - Get version by ID
POST   /config-versions/{id}/activate/        - Activate version
```

#### Resolved Config
```
GET    /resolved-config/?global=default&region=us-west&group=team&service=app
```

#### Audit Events
```
GET    /audit-events/         - List all events
GET    /audit-events/?event_type=version_activated
GET    /audit-events/?actor=admin
```

## ⚙️ Configuration

### Backend Configuration

#### Database Settings (`config_sphere/settings/base.py`)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "configsphere"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

#### CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### Frontend Configuration

#### API Base URL (`src/services/api.ts`)

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
```

## 🚢 Production Deployment

### Backend Deployment (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

# Copy application code
COPY . .

# Run migrations and start gunicorn
CMD ["bash", "-c", "python manage.py migrate && gunicorn config_sphere.wsgi:application --bind 0.0.0.0:8000 --workers 4"]
```

### Frontend Deployment (Docker)

```dockerfile
# See Dockerfile in frontend directory
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Production Docker Compose

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: configsphere
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - configsphere

  web:
    build: ./backend
    environment:
      DJANGO_SETTINGS_MODULE: config_sphere.settings.production
      DB_HOST: db
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - db
    networks:
      - configsphere

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: https://api.your-domain.com  # Update to your domain
    ports:
      - "3000:3000"
    networks:
      - configsphere

networks:
  configsphere:

volumes:
  postgres_data:
```

### Environment Variables for Production

Create a `.env` file:

```bash
# Database
DB_NAME=configsphere
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=your-super-secret-key-min-50-chars
DJANGO_SETTINGS_MODULE=config_sphere.settings.production
DEBUG=False

# Frontend
VITE_API_URL=https://api.your-domain.com
```

### Kubernetes Deployment Example

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: configsphere

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: configsphere-backend
  namespace: configsphere
spec:
  replicas: 3
  selector:
    matchLabels:
      app: configsphere-backend
  template:
    metadata:
      labels:
        app: configsphere-backend
    spec:
      containers:
      - name: backend
        image: your-registry/configsphere-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_HOST
          value: postgres-service
        - name: DJANGO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: django-secrets
              key: secret-key

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: configsphere-frontend
  namespace: configsphere
spec:
  replicas: 2
  selector:
    matchLabels:
      app: configsphere-frontend
  template:
    metadata:
      labels:
        app: configsphere-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/configsphere-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: VITE_API_URL
          value: https://api.configsphere.your-domain.com
```

## 🐛 Troubleshooting

### Frontend can't connect to backend

1. **Check CORS headers**: Ensure `CORS_ALLOWED_ORIGINS` includes frontend URL
   ```bash
   curl -i -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/schemas/
   ```

2. **Check backend is running**:
   ```bash
   curl http://localhost:8000/api/v1/
   ```

3. **Check environment variable**:
   ```bash
   # Frontend should have
   VITE_API_URL=http://localhost:8000/api/v1
   ```

### Database connection errors

1. **Verify PostgreSQL is running**:
   ```bash
   psql -U postgres -h localhost -d configsphere
   ```

2. **Check environment variables**:
   ```bash
   echo $DB_HOST $DB_PORT $DB_NAME $DB_USER
   ```

### Docker Compose issues

1. **Rebuild containers**:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

2. **Check service health**:
   ```bash
   docker compose ps
   ```

3. **View logs**:
   ```bash
   docker compose logs web
   docker compose logs frontend
   ```

### Port already in use

```bash
# Find process using port 3000
lsof -i :3000

# Find process using port 8000
lsof -i :8000

# Kill process (macOS)
kill -9 <PID>
```

### Migrations failing

```bash
# Reset database and run fresh migrations
docker compose exec web python manage.py migrate config_sphere zero
docker compose exec web python manage.py migrate
```

## 📊 Performance Optimization

### Frontend
- Uses Vite for faster builds
- Code splitting with React Router
- Material-UI component optimization
- CSS-in-JS with Emotion for better performance

### Backend
- PostgreSQL with optimized indexes
- Atomic transactions for data consistency
- Django ORM with select_related/prefetch_related
- REST Framework pagination for large datasets

## 🔐 Security Considerations

### Production Checklist

- [ ] Set `DEBUG = False` in Django settings
- [ ] Use strong `DJANGO_SECRET_KEY` (50+ chars)
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS/TLS in production
- [ ] Implement authentication (JWT tokens recommended)
- [ ] Set up proper CORS for production domain only
- [ ] Use database encryption
- [ ] Enable Django security middleware
- [ ] Set up monitoring and logging
- [ ] Regular security updates and patches

## 📞 Support & Documentation

- API Guide: See [API_GUIDE.md](../API_GUIDE.md)
- Backend README: See [backend/README.md](../backend/README.md)
- Frontend README: See [frontend/README.md](../frontend/README.md)

## 📄 License

Same as ConfigSphere project

---

**Last Updated**: March 2026
**Version**: 1.0.0
