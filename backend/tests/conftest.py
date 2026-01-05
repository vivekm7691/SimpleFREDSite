"""
Shared pytest fixtures and configuration.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.fred_service import FREDService
from app.services.gemini_service import GeminiService
from app.services.category_service import CategoryService
from app.services.category_service import CategoryService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_fred_service(monkeypatch):
    """Create a mock FRED service."""
    mock_service = MagicMock(spec=FREDService)
    
    # Mock the get_fred_service function
    def get_mock_service():
        return mock_service
    
    monkeypatch.setattr("app.api.routes.get_fred_service", get_mock_service)
    return mock_service


@pytest.fixture
def mock_gemini_service(monkeypatch):
    """Create a mock Gemini service."""
    mock_service = MagicMock(spec=GeminiService)
    mock_service.summarize_data = AsyncMock(return_value="This is a test summary of the economic data.")
    mock_service.model_name = "models/gemini-2.5-flash"
    mock_service.api_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
    
    # Mock the GeminiService class constructor
    # Since routes.py imports GeminiService inside the function, we need to mock it in the services module
    class MockGeminiService:
        def __init__(self, api_key=None, model_name="models/gemini-2.5-flash"):
            # Store reference to mock_service for dynamic delegation
            self._mock_service = mock_service
            self.api_key = api_key or "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
            self.model_name = model_name
            self.model = MagicMock()
        
        async def summarize_data(self, data):
            # Delegate to mock_service dynamically so test updates work
            return await self._mock_service.summarize_data(data)
    
    # Replace GeminiService in the services module (where routes imports it from)
    monkeypatch.setattr("app.services.gemini_service.GeminiService", MockGeminiService)
    
    return mock_service


@pytest.fixture
def mock_category_service(monkeypatch):
    """Create a mock Category service."""
    mock_service = MagicMock(spec=CategoryService)
    
    # Mock the get_category_service function
    def get_mock_service():
        return mock_service
    
    monkeypatch.setattr("app.api.routes.get_category_service", get_mock_service)
    return mock_service


@pytest.fixture
def sample_fred_series_info():
    """Sample FRED series info for testing."""
    return {
        "id": "GDP",
        "title": "Gross Domestic Product",
        "units": "Billions of Dollars",
        "frequency": "Quarterly",
        "seasonal_adjustment": "Seasonally Adjusted Annual Rate"
    }


@pytest.fixture
def sample_fred_observations():
    """Sample FRED observations for testing."""
    return [
        {"date": "2024-01-01", "value": "25000.0"},
        {"date": "2023-10-01", "value": "24800.0"},
        {"date": "2023-07-01", "value": "24600.0"},
    ]


@pytest.fixture
def sample_fred_api_response(sample_fred_series_info, sample_fred_observations):
    """Sample FRED API response for series endpoint."""
    return {
        "seriess": [sample_fred_series_info]
    }


@pytest.fixture
def sample_fred_observations_response(sample_fred_observations):
    """Sample FRED API response for observations endpoint."""
    return {
        "observations": sample_fred_observations
    }

