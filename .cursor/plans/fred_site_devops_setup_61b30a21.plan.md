# FRED Website DevOps Plan

## Step-by-Step Implementation Plan

### Phase 1: Project Foundation (Steps 1-3)

**Step 1: Initialize Project Structure**

- Create root directory structure
- Initialize Git repository
- Create `.gitignore` file
- Create `README.md` with project overview
- Set up basic folder structure (backend/, frontend/, .github/)

**Step 2: Backend Foundation**

- Initialize Python project in `backend/`
- Create `requirements.txt` with FastAPI, uvicorn, httpx, python-dotenv
- Create `requirements-dev.txt` with pytest and testing dependencies
- Set up basic FastAPI app structure (`app/main.py`)
- Create basic health check endpoint (`GET /health`)
- Test backend runs locally (without Docker)

**Step 3: Frontend Foundation**

- Initialize React app in `frontend/` using `create-react-app` or Vite
- Set up basic project structure
- Create simple UI with form input for FRED series ID
- Set up API client utilities
- Test frontend runs locally (without Docker)

### Phase 2: Core Functionality (Steps 4-6)

**Step 4: Implement FRED API Integration**

- Create `backend/app/services/fred_service.py`
- Implement FRED API client using httpx
- Create Pydantic models for FRED data (`backend/app/models/schemas.py`)
- Create API endpoint `POST /api/fred/fetch`
- Test with real FRED API (using test API key)

**Step 5: Implement Google Gemini Integration**

- Create `backend/app/services/gemini_service.py`
- Implement Google Gemini API client
- Create summarization logic
- Create API endpoint `POST /api/summarize`
- Test with real Google Gemini API (using test API key)

**Step 6: Connect Frontend to Backend**

- Update frontend to call backend API endpoints
- Implement form submission handling
- Display FRED data in UI
- Display summaries in UI
- Test end-to-end flow locally

### Phase 3: Docker Setup (Steps 7-9)

**Step 7: Backend Dockerization**

- Create `backend/Dockerfile` (multi-stage build)
- Create `backend/.dockerignore`
- Test building backend Docker image: `docker build -t fred-backend ./backend`
- Test running backend container: `docker run -p 8000:8000 fred-backend`

**Step 8: Frontend Dockerization**

- Create `frontend/Dockerfile` (multi-stage with nginx)
- Create `frontend/.dockerignore`
- Test building frontend Docker image: `docker build -t fred-frontend ./frontend`
- Test running frontend container: `docker run -p 3000:80 fred-frontend`

**Step 9: Docker Compose Setup**

- Create `docker-compose.yml` with backend and frontend services
- Configure environment variables
- Set up volume mounts for development
- Configure networking between services
- Test: `docker-compose up` and verify both services work together

### Phase 4: Environment & Configuration (Step 10)

**Step 10: Environment Configuration**

- Create `.env.example` with all required variables
- Update `.gitignore` to exclude `.env`
- Update `docker-compose.yml` to use `.env` file
- Document required API keys in README
- Test with environment variables loaded from `.env`

### Phase 5: Testing Infrastructure (Steps 11-13)

**Step 11: Backend Testing Setup**

- Create `backend/tests/` directory structure
- Create `backend/pytest.ini` configuration
- Create `backend/tests/conftest.py` with fixtures
- Write unit tests for FRED service (with mocks)
- Write unit tests for Google Gemini service (with mocks)
- Write API tests for endpoints (with mocked external APIs)
- Run tests locally: `pytest`

**Step 12: Frontend Testing Setup**

- Create `frontend/__tests__/` directory
- Create `frontend/jest.config.js`
- Write component tests for form and display components
- Write API client tests (with mocks)
- Run tests locally: `npm test`

**Step 13: Integration Testing**

- Create integration tests that test backend and frontend together
- Test full user flow: submit form → fetch data → display summary
- Run integration tests in Docker Compose environment

### Phase 6: CI/CD Pipeline (Steps 14-15)

**Step 14: GitHub Actions CI Pipeline**

- Create `.github/workflows/ci.yml`
- Set up backend job: lint, test, coverage
- Set up frontend job: lint, test, coverage
- Set up integration test job with Docker Compose
- Add security scanning jobs
- Test CI pipeline by pushing to GitHub

**Step 15: Docker Build Pipeline**

- Create `.github/workflows/docker-build.yml`
- Configure Docker image building
- Set up GitHub Container Registry or Docker Hub integration
- Configure image tagging (commit SHA, branch name)
- Test building and pushing images

### Phase 7: Documentation & Polish (Step 16)

**Step 16: Final Documentation**

- Update `README.md` with:
- Setup instructions
- How to run locally with Docker
- How to run tests
- API endpoint documentation
- Environment variables guide
- Add code comments where needed
- Verify all documentation is accurate

## Architecture Overview

The application will consist of:

- **Backend**: FastAPI service that fetches data from FRED API and uses Google Gemini API for summarization
- **Frontend**: React application for user interaction
- **Containerization**: Docker containers for both services
- **Orchestration**: Docker Compose for local development

## Project Structure

```javascript
SimpleFREDSite/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── api/
│   │   │   └── routes.py    # API endpoints
│   │   ├── services/
│   │   │   ├── fred_service.py    # FRED API integration
│   │   │   └── gemini_service.py  # Google Gemini API integration
│   │   └── models/
│   │       └── schemas.py   # Pydantic models
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py      # API endpoint tests
│   │   ├── test_services.py # Service layer tests
│   │   ├── conftest.py      # Pytest configuration and fixtures
│   │   └── test_health.py   # Health check tests
│   ├── requirements.txt
│   ├── requirements-dev.txt # Development dependencies (pytest, etc.)
│   ├── pytest.ini           # Pytest configuration
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── src/
│   ├── public/
│   ├── __tests__/           # React component tests
│   │   ├── App.test.jsx
│   │   └── api.test.js      # API client tests
│   ├── package.json
│   ├── jest.config.js       # Jest configuration
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml        # Local development orchestration
├── docker-compose.prod.yml   # Production configuration (future)
├── .env.example              # Environment variable template
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml            # Continuous Integration pipeline
│       └── docker-build.yml  # Docker image building
└── README.md
```



## Phase 1: Local Docker Development Setup

### 1. Docker Configuration

**Backend Dockerfile** (`backend/Dockerfile`):

- Multi-stage build for optimization
- Python 3.11 slim base image
- Install dependencies from requirements.txt
- Expose port 8000
- Run FastAPI with uvicorn

**Frontend Dockerfile** (`frontend/Dockerfile`):

- Multi-stage build (build stage + nginx serve stage)
- Node.js 18+ for build stage
- Nginx alpine for production serve
- Build React app and serve static files

**Docker Compose** (`docker-compose.yml`):

- Backend service: FastAPI on port 8000
- Frontend service: React app on port 3000
- Environment variables from `.env` file
- Volume mounts for hot-reload during development
- Network configuration for service communication

### 2. Environment Configuration

**`.env.example`**:

- FRED_API_KEY
- GEMINI_API_KEY
- Backend and frontend configuration variables
- CORS settings

**`.env`** (local, gitignored):

- Actual API keys for local development

### 3. Automated Testing Strategy

**Backend Testing** (`backend/tests/`):

- **Unit Tests**: Test individual functions and methods
- FRED service: Mock FRED API responses, test data parsing
- Gemini service: Mock Google Gemini API responses, test prompt formatting
- Models: Test Pydantic schema validation
- **API Tests**: Test FastAPI endpoints using TestClient
- Health check endpoint
- FRED data fetching endpoint (with mocked FRED API)
- Summarization endpoint (with mocked Google Gemini API)
- Error handling (invalid series IDs, API failures)
- **Test Fixtures**: Reusable test data and mocks in `conftest.py`
- **Coverage**: Aim for 80%+ code coverage using pytest-cov

**Frontend Testing** (`frontend/__tests__/`):

- **Component Tests**: Test React components with React Testing Library
- Form input validation
- Data display components
- Error and loading states
- **API Client Tests**: Mock API calls, test request/response handling
- **Integration Tests**: Test user flows (submit form, display results)
- **Coverage**: Aim for 70%+ code coverage

**Test Execution**:

- Run tests locally: `pytest` (backend) and `npm test` (frontend)
- Run tests in Docker: `docker-compose run backend pytest` and `docker-compose run frontend npm test`
- Coverage reports generated in CI and optionally published

### 4. CI/CD Pipeline (GitHub Actions)

**`.github/workflows/ci.yml`**:

- **Trigger**: On push/PR to main/develop branches
- **Backend Jobs**:
- Setup Python 3.11
- Install dependencies (including dev dependencies)
- Run linting: `ruff check` or `flake8` + `black --check`
- Run type checking: `mypy` (optional)
- Run tests: `pytest --cov=app --cov-report=xml`
- Upload coverage to Codecov or similar (optional)
- **Frontend Jobs**:
- Setup Node.js 18+
- Install dependencies
- Run linting: `npm run lint` (ESLint)
- Run type checking: `npm run type-check` (TypeScript, if used)
- Run tests: `npm test -- --coverage`
- Upload coverage reports
- **Integration Test Job**:
- Build Docker images
- Start services with docker-compose
- Run integration tests (test API from frontend container)
- Verify services can communicate
- **Security Scanning**:
- Run `safety check` for Python dependencies
- Run `npm audit` for Node.js dependencies
- Optional: Trivy scan for Docker images

**`.github/workflows/docker-build.yml`**:

- Trigger: Only on successful CI completion
- Build and tag Docker images on successful CI
- Push to GitHub Container Registry (ghcr.io) or Docker Hub
- Tag images with commit SHA and branch name
- Only run on main branch merges

### 5. Development Workflow

**Local Development**:

1. Clone repository
2. Copy `.env.example` to `.env` and fill in API keys
3. Run `docker-compose up` to start all services
4. Backend accessible at `http://localhost:8000`
5. Frontend accessible at `http://localhost:3000`
6. Hot-reload enabled for both services during development

**Docker Commands**:

- `docker-compose up` - Start all services
- `docker-compose up -d` - Start in detached mode
- `docker-compose down` - Stop all services
- `docker-compose build` - Rebuild images
- `docker-compose logs -f` - View logs

## Implementation Details

### Backend Service

- FastAPI with CORS enabled for frontend communication
- RESTful API endpoints:
- `GET /health` - Health check
- `POST /api/fred/fetch` - Fetch FRED data by series ID
- `POST /api/summarize` - Summarize data using Google Gemini
- Error handling and validation
- Environment-based configuration

### Frontend Service

- React app with API client
- Form for FRED series ID input
- Display fetched data and summaries
- Error handling and loading states
- Proxy API calls to backend (or direct CORS)

### Docker Networking

- Services communicate via Docker network
- Frontend calls backend at `http://backend:8000` (internal)
- External access via mapped ports

## Security Considerations

- API keys stored in environment variables (never in code)
- `.env` file in `.gitignore`
- Docker images scan for vulnerabilities in CI