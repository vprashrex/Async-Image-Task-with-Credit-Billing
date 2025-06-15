# Deployment Guide

## Prerequisites
- Docker and Docker Compose installed
- Port 8000 and 6379 available

## Quick Start

1. **Clone and navigate to project directory**
   ```bash
   git clone <repository-url>
   cd virtual-space
   ```

2. **Build and start services**
   ```bash
   docker-compose up --build -d
   ```

3. **Verify deployment**
   - Web app: http://localhost:8000
   - Health check: http://localhost:8000/health
   - Redis: localhost:6379

## Services

- **web**: FastAPI application (port 8000)
- **redis**: Cache and message broker (port 6379)
- **celery-worker**: Background task processor
- **celery-beat**: Scheduled task runner

## Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build -d

```

