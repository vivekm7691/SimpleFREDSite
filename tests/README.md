# Integration Tests

Integration tests verify that the backend and frontend work together correctly in a Docker Compose environment.

## Overview

These tests verify the complete user flow:
1. **Form Submission** → User submits a FRED series ID
2. **Data Fetch** → Backend fetches data from FRED API
3. **Summary Generation** → Backend generates summary using Gemini API
4. **Display** → Frontend displays the data and summary

## Prerequisites

- Docker and Docker Compose installed
- Environment variables set (`.env` file with `FRED_API_KEY` and `GEMINI_API_KEY`)
- Services can be started with `docker-compose up`

## Running Integration Tests

### Option 1: Using the Test Scripts (Recommended)

**Windows (PowerShell):**
```powershell
.\run_integration_tests.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x run_integration_tests.sh
./run_integration_tests.sh
```

The script will:
1. Start Docker Compose services
2. Wait for services to be healthy
3. Run integration tests
4. Stop services after tests complete

### Option 2: Manual Steps

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be ready:**
   ```bash
   # Check backend health
   curl http://localhost:8000/health
   
   # Check frontend
   curl http://localhost:3000
   ```

3. **Run tests:**
   ```bash
   # From project root
   cd backend
   .\venv\Scripts\Activate.ps1  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   cd ..
   pytest tests/ -v -m integration
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Option 3: Using Docker Compose Test Service

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm integration-tests
```

## Test Structure

- **Location**: `tests/`
- **Test File**: `test_integration.py`
- **Markers**: All tests are marked with `@pytest.mark.integration`

## Test Cases

### Full User Flow Tests

1. **`test_fred_data_fetch_flow`**
   - Tests complete flow: Fetch FRED data → Generate summary
   - Verifies response structure and data integrity

2. **`test_end_to_end_flow_with_real_data`**
   - End-to-end test with real FRED API calls
   - Verifies data structure matches frontend expectations

### Service Communication Tests

3. **`test_backend_health_check`**
   - Verifies backend health endpoint is accessible

4. **`test_frontend_is_accessible`**
   - Verifies frontend is accessible

5. **`test_backend_frontend_network_connectivity`**
   - Verifies both services can communicate

### Error Handling Tests

6. **`test_invalid_series_id_handling`**
   - Tests error handling for invalid series IDs

7. **`test_api_endpoints_cors_headers`**
   - Verifies CORS configuration for frontend access

8. **`test_api_response_format`**
   - Verifies API responses match frontend expectations

## Configuration

Tests use environment variables to configure service URLs:

- `BACKEND_URL`: Backend service URL (default: `http://localhost:8000`)
- `FRONTEND_URL`: Frontend service URL (default: `http://localhost:3000`)

When running in Docker Compose, these are automatically set to use service names:
- `BACKEND_URL=http://backend:8000`
- `FRONTEND_URL=http://frontend:80`

## Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker-compose logs backend
docker-compose logs frontend

# Check service status
docker-compose ps
```

### Tests Timing Out

- Ensure services are healthy before running tests
- Check that API keys are set in `.env` file
- Verify network connectivity between services

### API Key Issues

- Ensure `.env` file exists with valid API keys
- Check that environment variables are loaded: `docker-compose config`

### Port Conflicts

If ports 8000 or 3000 are already in use:
```bash
# Stop conflicting services or
# Modify ports in docker-compose.yml
```

## Running Specific Tests

```bash
# Run specific test
pytest tests/test_integration.py::TestFullUserFlow::test_fred_data_fetch_flow -v

# Run all integration tests
pytest tests/ -v -m integration

# Run with coverage
pytest tests/ -v -m integration --cov=app
```

## Notes

- Integration tests make real API calls to FRED and Gemini APIs
- Tests require valid API keys in `.env` file
- Some tests may be skipped if services are not available
- Tests verify the complete flow but may take longer than unit tests

