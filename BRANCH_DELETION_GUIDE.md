# Feature Branch Deletion Guide

## Should You Delete the Feature Branch?

**Short Answer: Yes, after the PR is merged and you've verified everything works.**

## When to Delete Feature Branches

### ✅ Safe to Delete After:
1. **PR is merged** into the target branch (main/develop)
2. **CI/CD pipelines completed successfully** after merge
3. **Docker images are built and pushed** (if needed)
4. **You've verified the changes work** in the merged state
5. **No active work** is happening on that branch

### ❌ Don't Delete If:
1. PR is still **open and under review**
2. PR is **draft** and work is ongoing
3. You need the branch for **reference or rollback**
4. Other team members are **actively using** the branch

## Impact on Docker Images

### ✅ **Good News: Deleting the branch does NOT affect Docker images**

Docker images are:
- **Stored in GitHub Container Registry (ghcr.io)** - independent of git branches
- **Tagged with multiple tags** including:
  - `pr-{PR_NUMBER}` (e.g., `pr-4`) - **Still exists after branch deletion**
  - `{commit-sha}` - **Immutable, always available**
  - `{branch-name}` - May become stale but image still exists

### What Happens to Tags After Branch Deletion?

1. **PR tags (`pr-4`)**: ✅ **Still work** - These are tied to the PR, not the branch
2. **Commit SHA tags**: ✅ **Still work** - Immutable, always available
3. **Branch name tags**: ⚠️ **May become stale** - But the image still exists in registry

### Example Scenario

```bash
# You have PR #4 from branch "feature/my-feature"
# Branch gets merged and deleted

# These still work:
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:pr-4  ✅
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234  ✅ (commit SHA)

# This may become stale (but image still exists):
docker pull ghcr.io/vivekm7691/simplefredsite/fred-backend:feature-my-feature  ⚠️
```

## Best Practices

### 1. Use Commit SHA Tags for Production

For reproducible deployments, use commit SHA tags instead of PR or branch tags:

```yaml
# docker-compose.yml
services:
  backend:
    image: ghcr.io/vivekm7691/simplefredsite/fred-backend:abc1234  # Use SHA
    # ...
```

### 2. Delete Branches After Merge

**Benefits:**
- Keeps repository clean
- Reduces confusion about which branches are active
- Prevents accidental work on old branches
- GitHub can auto-delete branches after merge (enable in repo settings)

**How to Delete:**

**Option A: Via GitHub UI (Recommended)**
1. After PR is merged, GitHub shows a "Delete branch" button
2. Click it to delete both local and remote branch

**Option B: Via Command Line**
```bash
# Delete remote branch (after merge)
git push origin --delete feature/my-feature

# Delete local branch
git branch -d feature/my-feature

# Force delete if needed (use with caution)
git branch -D feature/my-feature
```

### 3. Keep Important Commits

Before deleting, ensure:
- ✅ All commits are merged
- ✅ No uncommitted work
- ✅ Important changes are documented

### 4. Document Critical Images

If you need specific Docker images for production:
- **Pin to commit SHA** in your deployment configs
- **Document which SHA** corresponds to which release
- **Don't rely on PR tags** for production deployments

## GitHub Auto-Delete Setting

You can enable automatic branch deletion after PR merge:

1. Go to repository **Settings** → **General**
2. Scroll to **Pull Requests** section
3. Check **"Automatically delete head branches"**
4. Save changes

This will automatically delete feature branches after PRs are merged.

## Summary

| Action | Impact on Docker Images | Recommendation |
|--------|------------------------|----------------|
| Delete feature branch after merge | ✅ **No impact** - Images remain in registry | ✅ **Recommended** - Keeps repo clean |
| Keep branch after merge | ✅ No impact | ⚠️ **Not recommended** - Clutters repo |
| Delete branch before merge | ❌ **Don't do this** - PR will break | ❌ **Never** |

## Quick Checklist

Before deleting a feature branch:

- [ ] PR is merged successfully
- [ ] CI/CD pipelines passed
- [ ] Docker images built (if needed)
- [ ] Changes verified in merged state
- [ ] No active work on branch
- [ ] Important commits documented
- [ ] Using commit SHA tags for deployments (not PR/branch tags)

## Related Documentation

- **[DIAGNOSE_DOCKER_IMAGES.md](./DIAGNOSE_DOCKER_IMAGES.md)** - Troubleshooting Docker image issues
- **[DOCKER_BUILD_PIPELINE.md](./DOCKER_BUILD_PIPELINE.md)** - Understanding Docker image tags
- **[PULL_AND_TEST_IMAGES.md](./PULL_AND_TEST_IMAGES.md)** - How to pull and test images



