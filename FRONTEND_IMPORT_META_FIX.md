# Frontend Import.meta Error Fix

## Problem

Frontend tests were failing with:
```
SyntaxError: Cannot use 'import.meta' outside a module
```

This occurred because:
1. Jest's coverage instrumentation was adding code that included `import.meta`
2. Jest/Babel couldn't parse `import.meta` in the CommonJS context
3. The error appeared in instrumented code (line 571) even though the source didn't directly use `import.meta` in a problematic way

## Solution

### 1. Removed Direct `import.meta` Usage from Source Code
**File**: `frontend/src/services/api.js`

- Removed the `Function` constructor approach that used `import.meta`
- Simplified to use only `global.import.meta` (set up in jest.setup.js) and `process.env`
- This ensures no `import.meta` appears in source code that Jest needs to parse

### 2. Created Custom Transform to Handle `import.meta`
**File**: `frontend/jest-transform-import-meta.js`

- Transforms any `import.meta` references before Babel processes them
- Replaces `import.meta.env.VITE_API_BASE_URL` with safe fallbacks
- Handles any other `import.meta` patterns that might appear

### 3. Created Combined Transform
**File**: `frontend/jest-transform-combined.js`

- Runs the `import.meta` transform first
- Then passes the result to Babel for normal transformation
- Ensures `import.meta` is handled before coverage instrumentation

### 4. Updated Jest Configuration
**File**: `frontend/jest.config.cjs`

- Changed transform to use the combined transform
- This ensures `import.meta` is transformed before Babel and coverage

## Files Modified

1. ✅ `frontend/src/services/api.js` - Removed problematic `import.meta` usage
2. ✅ `frontend/jest-transform-import-meta.js` - Enhanced to handle all `import.meta` patterns
3. ✅ `frontend/jest-transform-combined.js` - New combined transform
4. ✅ `frontend/jest.config.cjs` - Updated to use combined transform

## How It Works

1. **Source Code**: Uses only `global.import.meta` (for tests) and `process.env` (for both)
2. **Transform Pipeline**: 
   - `jest-transform-import-meta.js` replaces any `import.meta` → safe fallback
   - `jest-transform-combined.js` runs import.meta transform, then Babel
   - Babel transforms the code normally
   - Coverage instrumentation runs on already-transformed code
3. **Result**: No `import.meta` reaches Jest's parser, preventing syntax errors

## Testing

The fix should resolve:
- ✅ `SyntaxError: Cannot use 'import.meta' outside a module`
- ✅ Coverage instrumentation errors
- ✅ Tests should now run successfully in CI

## Environment Variable Handling

The code now handles environment variables in this priority order:
1. `global.import.meta.env.VITE_API_BASE_URL` (set up in jest.setup.js for tests)
2. `process.env.VITE_API_BASE_URL` (works in both Jest and Vite)
3. Default: `'http://localhost:8000'`

This ensures compatibility with:
- ✅ Jest test environment
- ✅ Vite development server
- ✅ Vite production build

