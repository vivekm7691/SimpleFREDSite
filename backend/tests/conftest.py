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

