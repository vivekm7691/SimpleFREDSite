# Testing Guide

This guide explains how to run backend and frontend tests manually.

## Backend Tests (Python/Pytest)

### Prerequisites
- Python 3.11+ installed
- Virtual environment activated
- Dependencies installed (`pip install -r requirements.txt requirements-dev.txt`)

### Running All Tests

From the `backend/` directory:

```bash
# Activate virtual environment (if not already active)
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Run all tests
pytest

# Or using Python module
python -m pytest
```

### Running Tests with Options

```bash
# Run tests with verbose output
pytest -v

# Run tests without coverage (faster)
pytest --no-cov

# Run specific test file
pytest tests/test_fred_service.py

# Run specific test class
pytest tests/test_fred_service.py::TestFREDServiceInitialization

# Run specific test function
pytest tests/test_fred_service.py::TestFREDServiceInitialization::test_init_with_api_key

# Run tests matching a pattern
pytest -k "fred"

# Run tests and show coverage report
pytest --cov=app --cov-report=html

# View coverage report (after running with HTML coverage)
# Open: backend/htmlcov/index.html in your browser
```

### Test Output
- Tests run with coverage by default (70% threshold)
- Coverage reports are generated in:
  - Terminal: `--cov-report=term-missing`
  - HTML: `backend/htmlcov/index.html`
  - XML: `backend/coverage.xml`

### Common Commands

```bash
# Quick test run (no coverage)
pytest --no-cov -v

# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Run tests and stop on first failure
pytest -x

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

---

## Frontend Tests (Jest)

### Prerequisites
- Node.js 18+ installed
- Dependencies installed (`npm install`)

### Running All Tests

From the `frontend/` directory:

```bash
# Run all tests
npm test

# Or using Jest directly
npx jest
```

### Running Tests with Options

```bash
# Run tests in watch mode (re-runs on file changes)
npm test -- --watch

# Run tests once (not in watch mode)
npm test -- --watchAll=false

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- App.test.jsx

# Run tests matching a pattern
npm test -- --testNamePattern="should render"

# Run tests in verbose mode
npm test -- --verbose

# Run tests and update snapshots (if using snapshots)
npm test -- -u
```

### Test Output
- Tests run with Jest's default output
- Coverage reports can be generated with `--coverage` flag
- Coverage threshold is set to 70% in `jest.config.cjs`

### Common Commands

```bash
# Quick test run (no watch mode)
npm test -- --watchAll=false

# Run tests with coverage report
npm test -- --coverage --watchAll=false

# Run tests and stop on first failure
npm test -- --bail

# Run tests in silent mode (less output)
npm test -- --silent
```

---

## Running Both Tests Together

### Option 1: Manual (Run in separate terminals)

**Terminal 1 (Backend):**
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
# or: source venv/bin/activate  # Linux/Mac
pytest
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm test -- --watchAll=false
```

### Option 2: Using npm scripts (if configured)

You could add a script to the root `package.json` to run both, but currently each must be run separately.

---

## Troubleshooting

### Backend Tests

**Issue: Module not found**
```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt requirements-dev.txt
```

**Issue: Tests failing with import errors**
```bash
# Make sure you're in the backend directory
cd backend
pytest
```

### Frontend Tests

**Issue: Jest not found**
```bash
# Install dependencies
npm install
```

**Issue: Babel transform errors**
```bash
# Make sure all dev dependencies are installed
npm install --save-dev @babel/preset-env @babel/preset-react
```

**Issue: Tests timing out**
```bash
# Increase timeout in jest.config.cjs or use:
npm test -- --testTimeout=10000
```

---

## Test Structure

### Backend Tests
- Location: `backend/tests/`
- Files: `test_*.py`
- Configuration: `backend/pytest.ini`
- Coverage threshold: 70%

### Frontend Tests
- Location: `frontend/__tests__/`
- Files: `*.test.{js,jsx}`
- Configuration: `frontend/jest.config.cjs`
- Coverage threshold: 70%

---

## Quick Reference

| Task | Backend | Frontend |
|------|---------|----------|
| Run all tests | `pytest` | `npm test` |
| Run with coverage | `pytest` (default) | `npm test -- --coverage` |
| Run specific file | `pytest tests/test_file.py` | `npm test -- file.test.jsx` |
| Verbose output | `pytest -v` | `npm test -- --verbose` |
| Watch mode | N/A | `npm test -- --watch` |
| Stop on failure | `pytest -x` | `npm test -- --bail` |

