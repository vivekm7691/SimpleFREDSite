"""
Tests for main FastAPI application and health check endpoint.
"""
import pytest
from fastapi import status


class TestHealthCheck:
    """Test cases for the health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test that health check endpoint returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Simple FRED Site API"
    
    def test_health_check_response_structure(self, client):
        """Test that health check response has correct structure."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "service" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
    
    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client):
        """Test health check endpoint with async client."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

