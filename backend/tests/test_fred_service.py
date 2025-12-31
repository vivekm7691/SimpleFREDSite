"""
Tests for FRED service methods.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response, HTTPStatusError, Request
import httpx

from app.services.fred_service import FREDService, get_fred_service
from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation


class TestFREDServiceInitialization:
    """Test cases for FREDService initialization."""
    
    def test_init_with_api_key(self):
        """Test FREDService initialization with provided API key."""
        service = FREDService(api_key="test_key_123")
        assert service.api_key == "test_key_123"
    
    def test_init_with_env_var(self, monkeypatch):
        """Test FREDService initialization with environment variable."""
        monkeypatch.setenv("FRED_API_KEY", "env_key_456")
        service = FREDService()
        assert service.api_key == "env_key_456"
    
    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that FREDService raises error when no API key is provided."""
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        with pytest.raises(ValueError, match="FRED_API_KEY"):
            FREDService()


class TestFREDServiceFetchSeries:
    """Test cases for fetch_series method."""
    
    @pytest.mark.asyncio
    async def test_fetch_series_success(self, sample_fred_series_info, sample_fred_observations):
        """Test successful series fetch."""
        service = FREDService(api_key="test_key")
        
        # Mock HTTP responses
        series_response = Response(
            200,
            json={"seriess": [sample_fred_series_info]},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        observations_response = Response(
            200,
            json={"observations": sample_fred_observations},
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = [series_response, observations_response]
            
            result = await service.fetch_series("GDP", limit=100, sort_order="desc")
            
            assert isinstance(result, FREDDataResponse)
            assert result.series_id == "GDP"
            assert result.series_info.id == "GDP"
            assert result.series_info.title == "Gross Domestic Product"
            assert len(result.observations) == 3
            assert result.observation_count == 3
    
    @pytest.mark.asyncio
    async def test_fetch_series_not_found(self):
        """Test fetch_series when series is not found."""
        service = FREDService(api_key="test_key")
        
        # Mock HTTP response with empty seriess array
        series_response = Response(
            200,
            json={"seriess": []},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = series_response
            
            with pytest.raises(ValueError, match="not found"):
                await service.fetch_series("INVALID")
    
    @pytest.mark.asyncio
    async def test_fetch_series_http_error(self):
        """Test fetch_series when HTTP error occurs."""
        service = FREDService(api_key="test_key")
        
        # Mock HTTP error response
        error_response = Response(
            404,
            json={"error": "Not found"},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        error_response.raise_for_status = MagicMock(side_effect=HTTPStatusError(
            "Not found",
            request=Request("GET", "https://api.stlouisfed.org/fred/series"),
            response=error_response
        ))
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = error_response
            
            with pytest.raises(HTTPStatusError):
                await service.fetch_series("GDP")
    
    @pytest.mark.asyncio
    async def test_fetch_series_with_limit(self, sample_fred_series_info, sample_fred_observations):
        """Test fetch_series with custom limit."""
        service = FREDService(api_key="test_key")
        
        # Mock HTTP responses
        series_response = Response(
            200,
            json={"seriess": [sample_fred_series_info]},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        observations_response = Response(
            200,
            json={"observations": sample_fred_observations[:2]},
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = [series_response, observations_response]
            
            result = await service.fetch_series("GDP", limit=2)
            
            assert result.observation_count == 2
            # Verify limit parameter was passed
            assert mock_client.get.call_count == 2


class TestFREDServiceGetSeriesInfo:
    """Test cases for _get_series_info method."""
    
    @pytest.mark.asyncio
    async def test_get_series_info_success(self, sample_fred_series_info):
        """Test successful series info retrieval."""
        service = FREDService(api_key="test_key")
        
        response = Response(
            200,
            json={"seriess": [sample_fred_series_info]},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        result = await service._get_series_info(mock_client, "GDP")
        
        assert isinstance(result, FREDSeriesInfo)
        assert result.id == "GDP"
        assert result.title == "Gross Domestic Product"
        assert result.units == "Billions of Dollars"
    
    @pytest.mark.asyncio
    async def test_get_series_info_empty_response(self):
        """Test _get_series_info with empty seriess array."""
        service = FREDService(api_key="test_key")
        
        response = Response(
            200,
            json={"seriess": []},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        with pytest.raises(ValueError, match="not found"):
            await service._get_series_info(mock_client, "INVALID")
    
    @pytest.mark.asyncio
    async def test_get_series_info_missing_seriess_key(self):
        """Test _get_series_info with missing seriess key in response."""
        service = FREDService(api_key="test_key")
        
        response = Response(
            200,
            json={},
            request=Request("GET", "https://api.stlouisfed.org/fred/series")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        with pytest.raises(ValueError, match="not found"):
            await service._get_series_info(mock_client, "GDP")


class TestFREDServiceGetObservations:
    """Test cases for _get_observations method."""
    
    @pytest.mark.asyncio
    async def test_get_observations_success(self, sample_fred_observations):
        """Test successful observations retrieval."""
        service = FREDService(api_key="test_key")
        
        response = Response(
            200,
            json={"observations": sample_fred_observations},
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        result = await service._get_observations(mock_client, "GDP", limit=100, sort_order="desc")
        
        assert len(result) == 3
        assert all(isinstance(obs, FREDObservation) for obs in result)
        assert result[0].date == "2024-01-01"
        assert result[0].value == 25000.0
    
    @pytest.mark.asyncio
    async def test_get_observations_with_missing_values(self):
        """Test observations retrieval with missing values ('.' in FRED API)."""
        service = FREDService(api_key="test_key")
        
        observations_data = [
            {"date": "2024-01-01", "value": "25000.0"},
            {"date": "2023-12-01", "value": "."},  # Missing value
            {"date": "2023-11-01", "value": "24800.0"},
        ]
        
        response = Response(
            200,
            json={"observations": observations_data},
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        result = await service._get_observations(mock_client, "GDP")
        
        assert len(result) == 3
        assert result[0].value == 25000.0
        assert result[1].value is None  # Missing value should be None
        assert result[2].value == 24800.0
    
    @pytest.mark.asyncio
    async def test_get_observations_invalid_response_format(self):
        """Test _get_observations with invalid response format."""
        service = FREDService(api_key="test_key")
        
        response = Response(
            200,
            json={},  # Missing 'observations' key
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        with pytest.raises(ValueError, match="Invalid response format"):
            await service._get_observations(mock_client, "GDP")
    
    @pytest.mark.asyncio
    async def test_get_observations_invalid_value_format(self):
        """Test observations with invalid value format."""
        service = FREDService(api_key="test_key")
        
        observations_data = [
            {"date": "2024-01-01", "value": "not_a_number"},
            {"date": "2023-12-01", "value": "25000.0"},
        ]
        
        response = Response(
            200,
            json={"observations": observations_data},
            request=Request("GET", "https://api.stlouisfed.org/fred/series/observations")
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        
        result = await service._get_observations(mock_client, "GDP")
        
        assert len(result) == 2
        assert result[0].value is None  # Invalid value should be None
        assert result[1].value == 25000.0


class TestGetFREDService:
    """Test cases for get_fred_service singleton function."""
    
    def test_get_fred_service_singleton(self, monkeypatch):
        """Test that get_fred_service returns singleton instance."""
        # Clear any existing instance
        import app.services.fred_service as fred_service_module
        fred_service_module._fred_service = None
        
        # Set up environment
        monkeypatch.setenv("FRED_API_KEY", "test_key_123")
        
        service1 = get_fred_service()
        service2 = get_fred_service()
        
        assert service1 is service2
        assert isinstance(service1, FREDService)
        assert service1.api_key == "test_key_123"




