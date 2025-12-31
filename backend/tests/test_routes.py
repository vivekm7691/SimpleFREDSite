"""
Tests for API routes (FRED data fetching and summarization endpoints).
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock
from httpx import HTTPStatusError, Response

from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation


class TestFREDFetchEndpoint:
    """Test cases for the FRED data fetching endpoint."""
    
    @pytest.mark.asyncio
    async def test_fetch_fred_data_success(self, async_client, mock_fred_service):
        """Test successful FRED data fetch."""
        # Setup mock response
        mock_response = FREDDataResponse(
            series_id="GDP",
            series_info=FREDSeriesInfo(
                id="GDP",
                title="Gross Domestic Product",
                units="Billions of Dollars",
                frequency="Quarterly",
                seasonal_adjustment="Seasonally Adjusted Annual Rate"
            ),
            observations=[
                FREDObservation(date="2024-01-01", value=25000.0),
                FREDObservation(date="2023-10-01", value=24800.0),
            ],
            observation_count=2
        )
        
        mock_fred_service.fetch_series = AsyncMock(return_value=mock_response)
        
        # Make request
        response = await async_client.post(
            "/api/fred/fetch",
            json={"series_id": "GDP"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_id"] == "GDP"
        assert data["series_info"]["title"] == "Gross Domestic Product"
        assert len(data["observations"]) == 2
        assert data["observation_count"] == 2
        mock_fred_service.fetch_series.assert_called_once_with("GDP")
    
    @pytest.mark.asyncio
    async def test_fetch_fred_data_series_not_found(self, async_client, mock_fred_service):
        """Test FRED data fetch when series is not found."""
        # Setup mock to raise ValueError (series not found)
        mock_fred_service.fetch_series = AsyncMock(side_effect=ValueError("Series 'INVALID' not found"))
        
        # Make request
        response = await async_client.post(
            "/api/fred/fetch",
            json={"series_id": "INVALID"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_fetch_fred_data_internal_error(self, async_client, mock_fred_service):
        """Test FRED data fetch when internal error occurs."""
        # Setup mock to raise generic exception
        mock_fred_service.fetch_series = AsyncMock(side_effect=Exception("Internal server error"))
        
        # Make request
        response = await async_client.post(
            "/api/fred/fetch",
            json={"series_id": "GDP"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()
    
    def test_fetch_fred_data_invalid_request(self, client):
        """Test FRED data fetch with invalid request body."""
        # Missing series_id
        response = client.post("/api/fred/fetch", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty series_id
        response = client.post("/api/fred/fetch", json={"series_id": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_fetch_fred_data_series_id_validation(self, client):
        """Test that series_id is validated and normalized."""
        # Test with lowercase - should be converted to uppercase
        response = client.post("/api/fred/fetch", json={"series_id": "gdp"})
        # Should pass validation (will fail at service level if not found, but validation should pass)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_fetch_fred_data_invalid_characters(self, client):
        """Test FRED data fetch with invalid characters in series_id."""
        # Invalid characters
        response = client.post("/api/fred/fetch", json={"series_id": "GDP@123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSummarizeEndpoint:
    """Test cases for the summarization endpoint."""
    
    @pytest.mark.asyncio
    async def test_summarize_success(self, async_client, mock_gemini_service, monkeypatch):
        """Test successful data summarization."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr("pathlib.Path.exists", lambda x: False)  # Prevent .env loading
        
        # Setup mock response
        mock_gemini_service.summarize_data = AsyncMock(
            return_value="This is a test summary of the economic data."
        )
        
        # Make request
        response = await async_client.post(
            "/api/summarize",
            json={"data": {"series_info": {"title": "GDP"}, "observations": []}}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summary" in data
        assert data["summary"] == "This is a test summary of the economic data."
        mock_gemini_service.summarize_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_api_error(self, async_client, mock_gemini_service, monkeypatch):
        """Test summarization when Gemini API fails."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr("pathlib.Path.exists", lambda x: False)  # Prevent .env loading
        
        # Setup mock to raise exception
        mock_gemini_service.summarize_data = AsyncMock(
            side_effect=Exception("Gemini API error")
        )
        
        # Make request
        response = await async_client.post(
            "/api/summarize",
            json={"data": {"test": "data"}}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_summarize_value_error(self, async_client, mock_gemini_service, monkeypatch):
        """Test summarization when ValueError is raised."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr("pathlib.Path.exists", lambda x: False)  # Prevent .env loading
        
        # Setup mock to raise ValueError
        mock_gemini_service.summarize_data = AsyncMock(
            side_effect=ValueError("Invalid API key")
        )
        
        # Make request
        response = await async_client.post(
            "/api/summarize",
            json={"data": {"test": "data"}}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid API key" in data["detail"]
    
    def test_summarize_invalid_request(self, client):
        """Test summarize endpoint with invalid request."""
        # Missing data field
        response = client.post("/api/summarize", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

