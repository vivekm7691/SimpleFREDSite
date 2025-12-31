# Building the Backend Docker Image

## Prerequisites

You need one of the following container tools installed:

### Option 1: Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop/
- Start Docker Desktop before building

### Option 2: Podman Desktop (Alternative to Docker Desktop)
- Download from: https://podman-desktop.io/
- Works without Docker Desktop
- Commands are the same (just replace `docker` with `podman`)

### Option 3: WSL2 with Docker/Podman
- Install WSL2: `wsl --install`
- Install Docker or Podman inside WSL2
- Build from WSL2 terminal

## Building the Image

### Using Docker:
```bash
cd backend
docker build -t fred-backend .
```

### Using Podman:
```bash
cd backend
podman build -t fred-backend .
```

## Running the Container

### Using Docker:
```bash
docker run -p 8000:8000 \
  -e FRED_API_KEY=your_fred_key \
  -e GEMINI_API_KEY=your_gemini_key \
  fred-backend
```

### Using Podman:
```bash
podman run -p 8000:8000 \
  -e FRED_API_KEY=your_fred_key \
  -e GEMINI_API_KEY=your_gemini_key \
  fred-backend
```

### Using .env file:
```bash
# Docker
docker run -p 8000:8000 --env-file ../.env fred-backend

# Podman
podman run -p 8000:8000 --env-file ../.env fred-backend
```

## Testing the Container

Once the container is running, test the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"Simple FRED Site API"}
```

## Building via GitHub Actions

If you don't have Docker/Podman installed locally, you can trigger a build via GitHub Actions:

1. Push your code to GitHub
2. The workflow will automatically build and test the Docker image
3. Or manually trigger it: Actions → "Build and Test Docker Image" → Run workflow

## Troubleshooting

### "Cannot connect to Docker daemon"
- Make sure Docker Desktop or Podman Desktop is running
- Try restarting the application

### "Permission denied"
- On Linux/WSL2, you may need to add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  # Then log out and back in
  ```

### Build fails with "package not found"
- Check that `requirements.txt` is in the `backend/` directory
- Verify all dependencies are listed correctly

