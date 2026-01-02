# Frontend Test Error Analysis and Solutions

## Problem Description

The frontend tests are failing in the CI pipeline with the error:
```
error enoent Could not read package.json: Error: ENOENT: no such file or directory, open 'C:\Users\malviv01\package.json'
```

This error indicates that Jest/npm is trying to read `package.json` from the wrong location (user's home directory) instead of the project's `frontend/` directory.

## Root Causes Identified

### 1. **Missing `rootDir` in Jest Configuration** ✅ FIXED
   - **Issue**: The `jest.config.cjs` file didn't explicitly set `rootDir`, causing Jest to resolve paths relative to an incorrect location
   - **Impact**: Jest couldn't find `package.json` in the expected location
   - **Solution**: Added `rootDir: __dirname` to `jest.config.cjs` to explicitly set the project root

### 2. **ESM/CommonJS Module Type Conflict** (Potential Issue)
   - **Issue**: `package.json` has `"type": "module"` (ESM), but `jest.config.cjs` is CommonJS
   - **Impact**: This can cause path resolution issues in some environments
   - **Status**: This is typically handled correctly, but worth monitoring

### 3. **Working Directory Resolution** (Potential Issue)
   - **Issue**: Even though CI sets `working-directory: ./frontend`, Jest might resolve paths differently
   - **Impact**: Jest could look for files relative to where it's invoked rather than where the config is
   - **Status**: The `rootDir` fix should resolve this

## Solutions Implemented

### ✅ Solution 1: Add Explicit `rootDir` to Jest Config
**File**: `frontend/jest.config.cjs`

```javascript
module.exports = {
  rootDir: __dirname,  // ← Added this line
  testEnvironment: 'jsdom',
  // ... rest of config
}
```

This explicitly tells Jest where the project root is, ensuring it always looks for `package.json` in the correct location.

## Additional Recommendations

### Recommendation 1: Verify CI Working Directory
The CI workflow already sets `working-directory: ./frontend`, which is correct. However, you can add an explicit check:

```yaml
- name: Verify working directory
  working-directory: ./frontend
  run: |
    pwd
    ls -la package.json
```

### Recommendation 2: Add Jest Verbose Output for Debugging
If issues persist, add verbose output to see what Jest is doing:

```yaml
- name: Run tests with coverage
  working-directory: ./frontend
  run: |
    npm test -- --coverage --watchAll=false --ci --verbose
```

### Recommendation 3: Ensure package-lock.json is Committed
Make sure `frontend/package-lock.json` is committed to the repository. The CI uses `npm ci` which requires this file.

### Recommendation 4: Check for .npmrc or npm Configuration Issues
If the problem persists, check if there's an `.npmrc` file that might be affecting npm's behavior, or if npm is configured to look in a different location.

## Testing the Fix

To verify the fix works:

1. **Locally** (Windows):
   ```powershell
   cd SimpleFREDSite\frontend
   npm test
   ```

2. **In CI**: The next GitHub Actions run should pass the frontend-test job

## Alternative Solutions (If Issue Persists)

### Alternative 1: Use `npx jest` with explicit config
```yaml
- name: Run tests with coverage
  working-directory: ./frontend
  run: |
    npx jest --config=jest.config.cjs --coverage --watchAll=false --ci
```

### Alternative 2: Set NODE_PATH explicitly
```yaml
- name: Run tests with coverage
  working-directory: ./frontend
  run: |
    NODE_PATH=./frontend npm test -- --coverage --watchAll=false --ci
  env:
    CI: true
```

### Alternative 3: Use `npm run test` with explicit path
```yaml
- name: Run tests with coverage
  working-directory: ./frontend
  run: |
    npm run test -- --coverage --watchAll=false --ci --rootDir=.
```

## Expected Behavior After Fix

After applying the `rootDir` fix:
- Jest should correctly resolve `package.json` from `frontend/package.json`
- Tests should run successfully in CI
- No more "ENOENT" errors about missing package.json

## Files Modified

- ✅ `SimpleFREDSite/frontend/jest.config.cjs` - Added `rootDir: __dirname`

## Next Steps

1. Commit the fix to `jest.config.cjs`
2. Push to trigger CI pipeline
3. Monitor the `frontend-test` job in GitHub Actions
4. If issues persist, try the alternative solutions listed above

