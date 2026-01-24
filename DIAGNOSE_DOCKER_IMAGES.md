# Diagnosing Docker Image Issues with PR Tags

## Problem: PR-4 Images Don't Have Expected Changes

When you pull Docker images using PR tags (like `pr-4`), the tag can be **overwritten** if the PR is updated with new commits. This means `pr-4` might point to a different commit than yesterday.

## Understanding PR Tags

From the workflow (`docker-build.yml`), PR images are tagged with:
- `pr-{PR_NUMBER}` (e.g., `pr-4`) - **This tag gets overwritten on each PR update**
- `{COMMIT_SHA}` - **This tag is immutable and always points to the same commit**

## Solution: Use Commit SHA Tags Instead

Instead of using `pr-4`, use the **commit SHA** tag to get a specific version that won't change.

### Step 1: Find the Commit SHA from Yesterday

You can find the commit SHA in several ways:

**Option A: Check GitHub Actions Logs**
1. Go to: https://github.com/vivekm7691/SimpleFREDSite/actions
2. Find the "Docker Build and Push" workflow run from yesterday
3. Check the job logs - it will show the commit SHA that was built

**Option B: Check PR #4 Commits**
1. Go to PR #4 on GitHub
2. Look at the commit history
3. Find the commit from yesterday that had your changes
4. Copy the commit SHA (first 7-12 characters)

**Option C: Use GitHub API**
```bash
# List tags for backend image (requires authentication)
curl -H "Authorization: Bearer YOUR_PAT_TOKEN" \
  https://ghcr.io/v2/vivekm7691/simplefredsite/fred-backend/tags/list
```

### Step 2: Pull Images Using Commit SHA

Once you have the commit SHA (e.g., `abc1234`), pull the images:

```bash
# Pull backend with commit SHA
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234

# Pull frontend with commit SHA
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:abc1234
```

### Step 3: Verify You Have the Right Image

Check the image metadata to confirm it's from the right commit:

```bash
# Inspect backend image
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234 | grep -i commit

# Or check image creation date
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234 | grep Created
```

## Alternative: Force Pull Latest PR-4

If you want the **latest** version of PR-4 (which may have changed since yesterday):

```bash
# Remove local cached images
docker rmi ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4 2>/dev/null || true
docker rmi ghcr.io/vivekm7691/simplefredsite/fred-frontend:pr-4 2>/dev/null || true

# Force pull fresh images (bypasses cache)
docker pull --no-cache ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4
docker pull --no-cache ghcr.io/vivekm7691/simplefredsite/fred-frontend:pr-4
```

## Check Current PR-4 Commit

To see what commit the current `pr-4` tag points to:

```bash
# Check backend image labels/metadata
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4 | grep -A 10 Labels

# Or pull and check
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4
docker inspect ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4 | grep -i commit
```

## Best Practice: Use Commit SHA for Testing

For reproducible testing, always use commit SHA tags instead of PR tags:

```yaml
# docker-compose.yml
services:
  backend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234  # Use SHA, not pr-4
    # ...
  
  frontend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-frontend:abc1234  # Use SHA, not pr-4
    # ...
```

## Quick Diagnostic Commands

Run these to diagnose your current situation:

```bash
# 1. Check if PR-4 images exist locally
docker images | grep "pr-4"

# 2. Check when they were pulled/created
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | grep pr-4

# 3. Pull fresh PR-4 images (may be different from yesterday)
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4
docker pull ghcr.io/vivekm7691/simplefredsite/fred-frontend:pr-4

# 4. Compare image IDs (if you have the old one)
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | grep -E "pr-4|abc1234"
```

## Why This Happens

The workflow creates tags like this:
- `pr-4` - **Mutable tag** (overwritten when PR is updated)
- `{commit-sha}` - **Immutable tag** (never changes)

When PR #4 gets new commits pushed to it, the workflow rebuilds and **overwrites** the `pr-4` tag with the new build. The old commit's image still exists with its SHA tag, but `pr-4` now points to the new commit.

## Next Steps

1. **Find the commit SHA from yesterday** that had your working changes
2. **Pull images using that commit SHA** instead of `pr-4`
3. **Update your docker-compose.yml** to use commit SHA tags for reproducibility
4. **Consider pinning to specific commits** in your testing workflow




