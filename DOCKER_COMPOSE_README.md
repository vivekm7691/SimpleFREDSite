# Docker Compose Setup

This document explains how to use Docker Compose to run the Simple FRED Site application.

## Prerequisites

1. Docker Desktop installed and running
2. `.env` file in the project root with your API keys (see `.env.example`)

## Quick Start

1. **Create `.env` file** (if you haven't already):
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. **Start all services**:
   ```bash
   docker-compose up
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Backend Health: http://localhost:8000/health

## Common Commands

### Start services in detached mode (background):
```bash
docker-compose up -d
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop services:
```bash
docker-compose down
```

### Rebuild images:
```bash
docker-compose build
# Or rebuild and start
docker-compose up --build
```

### Restart a specific service:
```bash
docker-compose restart backend
docker-compose restart frontend
```

### View running containers:
```bash
docker-compose ps
```

## Service Details

### Backend Service
- **Container name**: `fred-backend`
- **Port**: 8000 (mapped to host port 8000)
- **Health check**: Checks `/health` endpoint every 30s
- **Environment variables**:
  - `FRED_API_KEY`: Your FRED API key
  - `GEMINI_API_KEY`: Your Google Gemini API key

### Frontend Service
- **Container name**: `fred-frontend`
- **Port**: 80 (mapped to host port 3000)
- **Depends on**: Backend service (waits for backend to be healthy)
- **Health check**: Checks nginx root endpoint every 30s

## Networking

Both services are on the same Docker network (`fred-network`), allowing them to communicate using service names:
- Frontend nginx proxies `/api` requests to `http://backend:8000`
- Services can reach each other by service name (e.g., `backend`, `frontend`)

## Development Mode

For development with hot-reload, you can uncomment the volumes section in `docker-compose.yml`:

```yaml
backend:
  volumes:
    - ./backend/app:/app/app:ro
```

**Note**: Hot-reload requires uvicorn's `--reload` flag, which is not enabled in the production Dockerfile. For true hot-reload, you may want to run services locally or use a development docker-compose override file.

## Troubleshooting

### Services won't start
- Check that Docker Desktop is running
- Verify `.env` file exists and has valid API keys
- Check logs: `docker-compose logs`

### Frontend can't reach backend
- Verify both services are on the same network: `docker network inspect simplefredsite_fred-network`
- Check backend health: `curl http://localhost:8000/health`
- Check frontend logs for proxy errors

### Port already in use
- Stop any services using ports 3000 or 8000
- Or change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "3001:8000"  # Backend on different port
    - "3002:80"    # Frontend on different port
  ```

### Environment variables not loading
- Ensure `.env` file is in the project root (same directory as `docker-compose.yml`)
- Check variable names match exactly (case-sensitive)
- Restart services: `docker-compose down && docker-compose up`

## Production Considerations

For production deployment:
1. Remove or comment out volume mounts
2. Use environment-specific `.env` files
3. Consider using Docker secrets for sensitive data
4. Set up proper logging and monitoring
5. Configure reverse proxy (nginx/traefik) for SSL/TLS

