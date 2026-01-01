# Simple FRED Site

A simple website that fetches economic data from the Federal Reserve Economic Data (FRED) API and provides AI-powered summaries using the Google Gemini API.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Setup Instructions](#setup-instructions)
- [Running Locally with Docker](#running-locally-with-docker)
- [Running Tests](#running-tests)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [CI/CD](#cicd)
- [Additional Documentation](#additional-documentation)
- [License](#license)

## Project Overview

This project consists of:
- **Backend**: FastAPI service that integrates with FRED API and Google Gemini API
- **Frontend**: React application for user interaction
- **Infrastructure**: Docker containerization for easy local development and deployment
- **Testing**: Comprehensive test suite including unit, API, and integration tests
- **CI/CD**: Automated testing, linting, security scanning, and Docker image building

## Features

- Fetch economic data from FRED by series ID
- Generate AI-powered summaries of economic data using Google Gemini
- Modern, responsive web interface
- Containerized deployment with Docker
- Comprehensive test coverage
- Automated CI/CD pipelines
- Health check endpoints for monitoring

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** installed and running
  - Download from: https://www.docker.com/products/docker-desktop
  - Verify installation: `docker --version` and `docker-compose --version`
- **FRED API key** ([Get one here](https://fred.stlouisfed.org/docs/api/api_key.html))
  - Free API key available
  - Allows up to 120 requests per minute
- **Google Gemini API key** ([Get one here](https://ai.google.dev/))
  - Sign in with your Google account
  - Create an API key in the Google AI Studio

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SimpleFREDSite
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys
   # FRED_API_KEY=your_fred_api_key_here
   # GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs (Swagger UI)
   - Health Check: http://localhost:8000/health

## Setup Instructions

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SimpleFREDSite
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure API keys**
   Edit the `.env` file and add your API keys:
   ```bash
   FRED_API_KEY=your_fred_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Verify Docker is running**
   ```bash
   docker ps
   ```

### Development Setup (Optional)

If you want to run the services locally without Docker:

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt requirements-dev.txt

# Run the backend
python start_backend.py
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the frontend
npm run dev
```

## Running Locally with Docker

### Basic Commands

```bash
# Start all services in the foreground
docker-compose up

# Start all services in detached mode (background)
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images (after code changes)
docker-compose build

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Service Management

```bash
# Start only the backend
docker-compose up backend

# Start only the frontend (requires backend to be running)
docker-compose up frontend

# Restart a specific service
docker-compose restart backend

# Check service status
docker-compose ps

# Execute commands in a running container
docker-compose exec backend python -c "print('Hello from backend')"
docker-compose exec frontend sh
```

### Health Checks

Both services include health checks:
- **Backend**: `http://localhost:8000/health`
- **Frontend**: Automatically checked by Docker

You can verify services are healthy:
```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"Simple FRED Site API"}
```

## Running Tests

This project includes comprehensive test suites for backend, frontend, and integration testing.

### Quick Test Commands

```bash
# Run all backend tests
docker-compose run backend pytest

# Run all frontend tests
docker-compose run frontend npm test

# Run integration tests
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

### Detailed Testing Guide

For comprehensive testing instructions, see **[TESTING_GUIDE.md](./TESTING_GUIDE.md)**.

The testing guide includes:
- Backend tests (unit tests, API tests, coverage)
- Frontend tests (component tests, API client tests)
- Integration tests (end-to-end testing)
- Running tests manually (without Docker)
- Running specific tests
- Coverage reports

### Test Coverage

- **Backend**: Unit tests for services, API endpoint tests, ~90%+ coverage
- **Frontend**: Component tests, API client tests
- **Integration**: End-to-end tests covering full user flow

## API Endpoints

The backend API is available at `http://localhost:8000` (or your configured base URL).

### Base URL

- Development: `http://localhost:8000`
- Production: Configure via `VITE_API_BASE_URL` environment variable

### Endpoints

#### 1. Health Check

**GET** `/health`

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "service": "Simple FRED Site API"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

#### 2. Fetch FRED Data

**POST** `/api/fred/fetch`

Fetch economic data from FRED by series ID.

**Request Body:**
```json
{
  "series_id": "GDP"
}
```

**Request Schema:**
- `series_id` (string, required): FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
  - Must be 1-100 characters
  - Automatically converted to uppercase
  - Valid characters: alphanumeric, underscores, hyphens

**Response:**
```json
{
  "series_id": "GDP",
  "series_info": {
    "id": "GDP",
    "title": "Gross Domestic Product",
    "units": "Billions of Dollars",
    "frequency": "Quarterly",
    "seasonal_adjustment": "Seasonally Adjusted Annual Rate"
  },
  "observations": [
    {
      "date": "2024-01-01",
      "value": 27229.0
    },
    {
      "date": "2023-10-01",
      "value": 27105.0
    }
  ],
  "observation_count": 100
}
```

**Response Schema:**
- `series_id` (string): The FRED series ID
- `series_info` (object): Series metadata
  - `id` (string): Series ID
  - `title` (string): Series title
  - `units` (string, optional): Units of measurement
  - `frequency` (string, optional): Data frequency
  - `seasonal_adjustment` (string, optional): Seasonal adjustment method
- `observations` (array): Array of observation objects
  - `date` (string): Observation date (YYYY-MM-DD)
  - `value` (float, optional): Observation value
- `observation_count` (integer): Number of observations returned

**Error Responses:**

- **404 Not Found**: Series ID not found
  ```json
  {
    "detail": "Series ID 'INVALID' not found"
  }
  ```

- **500 Internal Server Error**: API request failed
  ```json
  {
    "detail": "Error fetching FRED data: <error message>"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:8000/api/fred/fetch \
  -H "Content-Type: application/json" \
  -d '{"series_id": "GDP"}'
```

**Popular FRED Series IDs:**
- `GDP` - Gross Domestic Product
- `UNRATE` - Unemployment Rate
- `CPIAUCSL` - Consumer Price Index
- `FEDFUNDS` - Federal Funds Rate
- `DGS10` - 10-Year Treasury Rate

---

#### 3. Summarize Data

**POST** `/api/summarize`

Generate an AI-powered summary of economic data using Google Gemini.

**Request Body:**
```json
{
  "data": {
    "series_id": "GDP",
    "series_info": {
      "id": "GDP",
      "title": "Gross Domestic Product",
      "units": "Billions of Dollars"
    },
    "observations": [
      {
        "date": "2024-01-01",
        "value": 27229.0
      }
    ]
  }
}
```

**Request Schema:**
- `data` (object, required): Data to summarize (typically FRED data response)

**Response:**
```json
{
  "summary": "The Gross Domestic Product (GDP) data shows..."
}
```

**Response Schema:**
- `summary` (string): Generated AI summary of the data

**Error Responses:**

- **400 Bad Request**: Invalid request data
  ```json
  {
    "detail": "<validation error message>"
  }
  ```

- **500 Internal Server Error**: Summary generation failed
  ```json
  {
    "detail": "Error generating summary: <error message>"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "series_id": "GDP",
      "series_info": {"id": "GDP", "title": "Gross Domestic Product"},
      "observations": [{"date": "2024-01-01", "value": 27229.0}]
    }
  }'
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

### Required Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

#### `FRED_API_KEY`

Your FRED API key for accessing economic data.

- **Get one free at**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Rate limit**: Up to 120 requests per minute
- **Format**: Alphanumeric string
- **Example**: `FRED_API_KEY=abc123def456ghi789`

#### `GEMINI_API_KEY`

Your Google Gemini API key for AI-powered summaries.

- **Get one at**: https://ai.google.dev/
- **Sign in** with your Google account
- **Create an API key** in Google AI Studio
- **Format**: Must start with `AIza...`
- **Example**: `GEMINI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567`

### Optional Environment Variables

#### `VITE_API_BASE_URL`

Frontend API base URL (defaults to `http://localhost:8000`).

- **When to use**: If running services on different ports or hosts
- **Example**: `VITE_API_BASE_URL=http://localhost:8000`
- **Production example**: `VITE_API_BASE_URL=https://api.example.com`

#### `PYTHONUNBUFFERED`

Python output buffering (set to `1` in Docker for real-time logs).

- **Default**: `1` (in docker-compose.yml)
- **Purpose**: Ensures Python output is immediately visible in Docker logs

### Security Notes

⚠️ **Important Security Guidelines:**

- **Never commit `.env` file to version control** - it's already in `.gitignore`
- Keep your API keys secure and private
- Rotate API keys if they are exposed
- For production, use secure secret management:
  - Docker secrets
  - AWS Secrets Manager
  - Azure Key Vault
  - HashiCorp Vault
  - Kubernetes secrets
- Do not share API keys in screenshots or documentation
- Use different API keys for development and production

### Environment File Example

```bash
# .env file
FRED_API_KEY=your_fred_api_key_here
GEMINI_API_KEY=AIzaSyYour_gemini_api_key_here
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
SimpleFREDSite/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py      # API route handlers
│   │   ├── models/
│   │   │   └── schemas.py     # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── fred_service.py    # FRED API integration
│   │   │   └── gemini_service.py  # Gemini API integration
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Backend test suite
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── test_fred_service.py
│   │   ├── test_gemini_service.py
│   │   ├── test_routes.py
│   │   └── test_main.py
│   ├── Dockerfile             # Backend Docker image
│   ├── requirements.txt       # Python dependencies
│   ├── requirements-dev.txt   # Development dependencies
│   └── pytest.ini             # Pytest configuration
│
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── App.jsx            # Main application component
│   │   ├── main.jsx           # React entry point
│   │   └── services/
│   │       └── api.js         # API client functions
│   ├── __tests__/             # Frontend test suite
│   │   ├── App.test.jsx
│   │   └── api.test.js
│   ├── Dockerfile             # Frontend Docker image
│   ├── package.json           # Node.js dependencies
│   ├── jest.config.cjs        # Jest configuration
│   └── vite.config.js         # Vite configuration
│
├── tests/                     # Integration tests
│   ├── conftest.py            # Integration test fixtures
│   ├── test_integration.py    # End-to-end tests
│   └── README.md              # Integration test documentation
│
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI pipeline (linting, testing, security)
│       └── docker-build.yml   # CD pipeline (Docker image building)
│
├── docker-compose.yml         # Docker Compose configuration
├── docker-compose.test.yml    # Docker Compose for integration tests
├── pytest.ini                 # Root-level pytest configuration
│
├── README.md                  # This file
├── TESTING_GUIDE.md           # Comprehensive testing documentation
├── DOCKER_BUILD_PIPELINE.md   # Docker build pipeline documentation
│
├── run_integration_tests.ps1  # PowerShell script for integration tests
├── run_integration_tests.sh   # Bash script for integration tests
│
└── .env.example               # Environment variables template
```

## CI/CD

This project includes automated CI/CD pipelines using GitHub Actions.

### Continuous Integration (CI)

The CI pipeline (`.github/workflows/ci.yml`) runs on every push and pull request:

1. **Backend Linting**: Ruff and Black code formatting checks
2. **Backend Testing**: Pytest with coverage reporting
3. **Frontend Linting**: ESLint checks
4. **Frontend Testing**: Jest with coverage reporting
5. **Integration Tests**: End-to-end tests in Docker Compose environment
6. **Security Scanning**: 
   - Backend: `safety check` for Python dependencies
   - Frontend: `npm audit` for Node.js dependencies

### Continuous Delivery (CD)

The Docker build pipeline (`.github/workflows/docker-build.yml`) runs after successful CI:

1. **Build Backend Image**: Builds and pushes backend Docker image to GHCR
2. **Build Frontend Image**: Builds and pushes frontend Docker image to GHCR
3. **Verify Images**: Pulls and tests the pushed images

**Image Locations:**
- Backend: `ghcr.io/<username>/SimpleFREDSite/fred-backend:latest`
- Frontend: `ghcr.io/<username>/SimpleFREDSite/fred-frontend:latest`

For detailed information, see **[DOCKER_BUILD_PIPELINE.md](./DOCKER_BUILD_PIPELINE.md)**.

### GitHub Secrets Required

For CI/CD to work, configure these secrets in your GitHub repository:

1. **FRED_API_KEY**: Your FRED API key
2. **GEMINI_API_KEY**: Your Google Gemini API key

**To add secrets:**
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its value

## Additional Documentation

- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)**: Comprehensive guide for running all types of tests
- **[DOCKER_BUILD_PIPELINE.md](./DOCKER_BUILD_PIPELINE.md)**: Documentation for the Docker build and push pipeline
- **[tests/README.md](./tests/README.md)**: Integration test documentation

## License

MIT
