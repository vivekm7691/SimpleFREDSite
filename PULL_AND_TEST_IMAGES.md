# How to Pull and Test Docker Images from CI/CD

This guide explains how to pull the Docker images built by the CI/CD pipeline and test them locally.

## Image Registry

Images are pushed to **GitHub Container Registry (ghcr.io)**:
- Registry: `ghcr.io`
- Repository: `vivekm7691/simplefredsite`
- Backend Image: `ghcr.io/vivekm7691/simplefredsite/fred-backend`
- Frontend Image: `ghcr.io/vivekm7691/simplefredsite/fred-frontend`

## Step 1: Authenticate with GitHub Container Registry

You need to authenticate with GitHub Container Registry to pull private images.

### Option A: Using Personal Access Token (PAT)

1. **Create a Personal Access Token** (if you don't have one):
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: "Docker Pull Access"
   - Scopes: Select `read:packages`
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Login to GitHub Container Registry**:
   ```bash
   echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

   Example:
   ```bash
   echo "ghp_xxxxxxxxxxxx" | docker login ghcr.io -u vivekm7691 --password-stdin
   ```

### Option B: Using GitHub CLI (gh)

If you have GitHub CLI installed:
```bash
gh auth login
gh auth token | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## Step 2: Find the Image Tags

Images are tagged based on the branch/PR and commit SHA. You can find available tags in several ways:

### Method 1: Check GitHub Actions Run

1. Go to your repository: https://github.com/vivekm7691/SimpleFREDSite
2. Click "Actions" tab
3. Find the "Docker Build and Push" workflow run
4. Check the job logs to see what tags were created

### Method 2: Use GitHub API (if images are public)

```bash
# List backend image tags
curl -H "Authorization: Bearer YOUR_PAT_TOKEN" \
  https://ghcr.io/v2/vivekm7691/simplefredsite/fred-backend/tags/list

# List frontend image tags
curl -H "Authorization: Bearer YOUR_PAT_TOKEN" \
  https://ghcr.io/v2/vivekm7691/simplefredsite/fred-frontend/tags/list
```

### Method 3: Common Tag Patterns

Based on your branch `feature/increment-1-ui-foundation` and commit `6b9e5c7`, try these tags:

**For Branch-based builds:**
- `feature-increment-1-ui-foundation-6b9e5c7` (branch name + commit SHA)
- `feature-increment-1-ui-foundation` (branch name)
- `6b9e5c7` (commit SHA)

**For PR builds:**
- `pr-{PR_NUMBER}` (if built from a PR)
- `{COMMIT_SHA}` (commit SHA)

## Step 3: Pull the Images

Once authenticated, pull the images:

```bash
# Pull backend image (replace TAG with actual tag)
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:TAG

# Pull frontend image (replace TAG with actual tag)
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:TAG
```

**Example with commit SHA:**
```bash
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:6b9e5c7
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:6b9e5c7
```

**Example with branch name:**
```bash
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:feature-increment-1-ui-foundation-6b9e5c7
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:feature-increment-1-ui-foundation-6b9e5c7
```

## Step 4: Test the Images

### Option A: Run Images Individually

**Test Backend:**
```bash
docker run -d \
  --name test-backend \
  -p 8000:8000 \
  -e FRED_API_KEY=your_fred_api_key \
  -e GEMINI_API_KEY=your_gemini_api_key \
  ghcr.io/vivekm7691/simplefredsite/fred-backend:6b9e5c7

# Test health endpoint
curl http://localhost:8000/health

# View logs
docker logs test-backend

# Stop and remove
docker stop test-backend
docker rm test-backend
```

**Test Frontend:**
```bash
docker run -d \
  --name test-frontend \
  -p 3000:80 \
  ghcr.io/vivekm7691/simplefredsite/fred-frontend:6b9e5c7

# Test frontend
curl http://localhost:3000

# View logs
docker logs test-frontend

# Stop and remove
docker stop test-frontend
docker rm test-frontend
```

### Option B: Use Docker Compose with Pulled Images

Create a `docker-compose.test.yml` file:

```yaml
services:
  backend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-backend:6b9e5c7
    container_name: fred-backend-test
    ports:
      - "8000:8000"
    environment:
      - FRED_API_KEY=${FRED_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    networks:
      - fred-network

  frontend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-frontend:6b9e5c7
    container_name: fred-frontend-test
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - fred-network

networks:
  fred-network:
    driver: bridge
```

Then run:
```bash
# Set environment variables
export FRED_API_KEY=your_fred_api_key
export GEMINI_API_KEY=your_gemini_api_key

# Start services
docker compose -f docker-compose.test.yml up -d

# Test services
curl http://localhost:8000/health
curl http://localhost:3000

# View logs
docker compose -f docker-compose.test.yml logs

# Stop services
docker compose -f docker-compose.test.yml down
```

## Step 5: Verify Images

Check that images were pulled successfully:

```bash
# List pulled images
docker images | grep simplefredsite

# Inspect image details
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-backend:6b9e5c7
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-frontend:6b9e5c7
```

## Troubleshooting

### Error: "unauthorized: authentication required"

**Solution:** Make sure you're authenticated:
```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

### Error: "manifest unknown" or "tag not found"

**Possible causes:**
1. Image tag doesn't exist (check GitHub Actions logs)
2. Image is private and you don't have access
3. Branch name was sanitized differently

**Solution:**
1. Check the GitHub Actions workflow run to see actual tags created
2. Try different tag variations (commit SHA, branch name, etc.)
3. Verify the image exists in GitHub Packages:
   - Go to: https://github.com/vivekm7691/SimpleFREDSite/pkgs/container/fred-backend
   - Check available tags

### Images are not being built

**Check:**
1. Did the "Docker Build and Push" workflow run?
2. Did it complete successfully?
3. Is it configured to run on your branch? (Currently runs on `main`, `develop`, and PRs)

**Note:** The workflow only runs on:
- `main` and `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

If you're on a feature branch, the images might not be built unless you:
- Create a PR to `develop` or `main`
- Manually trigger the workflow

## Quick Reference

**Image URLs:**
- Backend: `ghcr.io/vivekm7691/simplefredsite/fred-backend:TAG`
- Frontend: `ghcr.io/vivekm7691/simplefredsite/fred-frontend:TAG`

**Common Tags to Try:**
- `latest` (if on main/develop branch)
- `{commit-sha}` (e.g., `6b9e5c7`)
- `{branch-name}-{commit-sha}` (e.g., `feature-increment-1-ui-foundation-6b9e5c7`)
- `pr-{PR_NUMBER}` (if built from PR)

**View Images in GitHub:**
- Backend: https://github.com/vivekm7691/SimpleFREDSite/pkgs/container/fred-backend
- Frontend: https://github.com/vivekm7691/SimpleFREDSite/pkgs/container/fred-frontend






