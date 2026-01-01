# Docker Build Pipeline

This document explains the Docker build and push pipeline configured in GitHub Actions.

## Overview

The Docker Build Pipeline automatically builds and pushes Docker images to GitHub Container Registry (ghcr.io) after the CI pipeline passes successfully.

## Workflow File

**Location**: `.github/workflows/docker-build.yml`

## Triggers

The pipeline runs in the following scenarios:

1. **After CI Pipeline Success**: Automatically runs after the "CI Pipeline" workflow completes successfully on `main` or `develop` branches
2. **Manual Trigger**: Can be manually triggered from the GitHub Actions UI
3. **Direct Push**: Runs on direct pushes to `main` branch (when backend/frontend files change)

## Jobs

### 1. Build and Push Backend Image

- Builds the backend Docker image from `backend/Dockerfile`
- Pushes to: `ghcr.io/<repository>/fred-backend`
- Tags:
  - `latest` (on main branch)
  - `<branch-name>` (branch name tag)
  - `<branch-name>-<commit-sha>` (branch + commit SHA)
  - `<commit-sha>` (full commit SHA)

### 2. Build and Push Frontend Image

- Builds the frontend Docker image from `frontend/Dockerfile`
- Pushes to: `ghcr.io/<repository>/fred-frontend`
- Tags:
  - `latest` (on main branch)
  - `<branch-name>` (branch name tag)
  - `<branch-name>-<commit-sha>` (branch + commit SHA)
  - `<commit-sha>` (full commit SHA)

### 3. Verify Built Images

- Pulls the newly built images
- Tests that images can start and respond to health checks
- Verifies both backend and frontend images work correctly

## Image Registry

**GitHub Container Registry (ghcr.io)**

- Images are stored at: `ghcr.io/<your-username>/<repo-name>/<image-name>`
- Example: `ghcr.io/vivekm7691/SimpleFREDSite/fred-backend:latest`
- Images are private by default (can be made public in repository settings)

## Image Tags

Images are tagged with multiple tags for flexibility:

- **`latest`**: Always points to the latest build on main branch
- **Branch name**: e.g., `main`, `develop`
- **Branch + SHA**: e.g., `main-abc1234`**
- **Commit SHA**: Full commit SHA for precise versioning

## Pulling Images

### Public Images

If images are made public, you can pull them with:

```bash
# Pull backend image
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:latest

# Pull frontend image
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:latest
```

### Private Images

For private images, you need to authenticate first:

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Then pull images
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:latest
```

## Using Images in Docker Compose

You can update `docker-compose.yml` to use the registry images:

```yaml
services:
  backend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-backend:latest
    # ... rest of config
  
  frontend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-frontend:latest
    # ... rest of config
```

## Multi-Platform Builds

Images are built for multiple platforms:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, e.g., Apple Silicon, AWS Graviton)

## Caching

The pipeline uses GitHub Actions cache for faster builds:
- Build cache is stored between runs
- Significantly speeds up subsequent builds

## Permissions

The workflow requires:
- `contents: read` - To checkout code
- `packages: write` - To push images to GitHub Container Registry

These permissions are automatically granted via `GITHUB_TOKEN`.

## Viewing Images

1. Go to your GitHub repository
2. Click on "Packages" (right sidebar)
3. You'll see `fred-backend` and `fred-frontend` packages
4. Click on a package to see all versions/tags

## Making Images Public

By default, images are private. To make them public:

1. Go to your repository on GitHub
2. Click "Packages" in the right sidebar
3. Click on the package (e.g., `fred-backend`)
4. Click "Package settings"
5. Scroll down to "Danger Zone"
6. Click "Change visibility" → "Make public"

## Troubleshooting

### Images Not Appearing

- Check that the workflow ran successfully
- Verify permissions are set correctly
- Check the "Packages" section of your repository

### Authentication Errors

- Ensure `GITHUB_TOKEN` is available (automatically provided)
- Check that repository has package write permissions enabled

### Build Failures

- Check workflow logs in the Actions tab
- Verify Dockerfiles are correct
- Ensure all dependencies are available

## Manual Trigger

To manually trigger the build:

1. Go to GitHub Actions tab
2. Select "Docker Build and Push" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## Integration with CI

The build pipeline is designed to run **after** the CI pipeline succeeds:

```
CI Pipeline (Step 14) → ✅ Tests Pass
                          ↓
Docker Build (Step 15) → 📦 Images Built & Pushed
```

This ensures only tested, validated code gets packaged into Docker images.

