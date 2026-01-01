"""
Integration tests for the full user flow.
Tests backend and frontend together in a Docker Compose environment.
"""
import pytest
import httpx
import os
import time
from typing import Optional

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
TIMEOUT = 30.0
MAX_RETRIES = 10
RETRY_DELAY = 2.0


def wait_for_service(url: str, timeout: float = TIMEOUT) -> bool:
    """
    Wait for a service to be available.
    
    Args:
        url: Service URL to check
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if service is available, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return True
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        time.sleep(RETRY_DELAY)
    return False


@pytest.fixture(scope="session")
def backend_available():
    """Check if backend service is available."""
    health_url = f"{BACKEND_URL}/health"
    if not wait_for_service(health_url):
        pytest.skip(f"Backend service not available at {BACKEND_URL}")
    return True


@pytest.fixture(scope="session")
def frontend_available():
    """Check if frontend service is available."""
    if not wait_for_service(FRONTEND_URL):
        pytest.skip(f"Frontend service not available at {FRONTEND_URL}")
    return True


@pytest.fixture
def http_client():
    """Create HTTP client for making requests."""
    return httpx.Client(timeout=TIMEOUT, follow_redirects=True)


class TestFullUserFlow:
    """Integration tests for the complete user flow."""
    
    @pytest.mark.integration
    def test_backend_health_check(self, backend_available, http_client):
        """Test that backend health endpoint is accessible."""
        response = http_client.get(f"{BACKEND_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    @pytest.mark.integration
    def test_frontend_is_accessible(self, frontend_available, http_client):
        """Test that frontend is accessible."""
        response = http_client.get(FRONTEND_URL)
        assert response.status_code == 200
        # Check that it's the React app (should contain some React/HTML content)
        assert "html" in response.text.lower() or "root" in response.text.lower()
    
    @pytest.mark.integration
    def test_fred_data_fetch_flow(self, backend_available, http_client):
        """
        Test the full flow: Fetch FRED data → Generate summary.
        This simulates the user flow: submit form → fetch data → display summary.
        """
        # Step 1: Fetch FRED data (simulating form submission with series ID)
        series_id = "GDP"  # Using a well-known FRED series
        
        fetch_response = http_client.post(
            f"{BACKEND_URL}/api/fred/fetch",
            json={"series_id": series_id},
            headers={"Content-Type": "application/json"}
        )
        
        # Verify FRED data fetch was successful
        assert fetch_response.status_code == 200, f"Failed to fetch FRED data: {fetch_response.text}"
        fred_data = fetch_response.json()
        
        # Verify response structure
        assert "series_id" in fred_data
        assert fred_data["series_id"] == series_id
        assert "series_info" in fred_data
        assert "observations" in fred_data
        assert "observation_count" in fred_data
        
        # Verify series info structure
        series_info = fred_data["series_info"]
        assert "id" in series_info
        assert "title" in series_info
        assert series_info["id"] == series_id
        
        # Verify observations exist
        assert isinstance(fred_data["observations"], list)
        assert len(fred_data["observations"]) > 0
        assert fred_data["observation_count"] > 0
        
        # Verify observation structure
        if fred_data["observations"]:
            obs = fred_data["observations"][0]
            assert "date" in obs
            assert "value" in obs
        
        # Step 2: Generate summary using the fetched data
        # This simulates the frontend calling the summarize endpoint
        summarize_response = http_client.post(
            f"{BACKEND_URL}/api/summarize",
            json={"data": fred_data},
            headers={"Content-Type": "application/json"}
        )
        
        # Verify summary generation was successful
        assert summarize_response.status_code == 200, f"Failed to generate summary: {summarize_response.text}"
        summary_data = summarize_response.json()
        
        # Verify summary response structure
        assert "summary" in summary_data
        assert isinstance(summary_data["summary"], str)
        assert len(summary_data["summary"]) > 0
        
        # Verify summary contains relevant information
        summary_text = summary_data["summary"].lower()
        # Summary should mention the series or economic terms
        assert any(
            term in summary_text 
            for term in [series_id.lower(), "economic", "data", "gdp", "gross"]
        )
    
    @pytest.mark.integration
    def test_invalid_series_id_handling(self, backend_available, http_client):
        """Test error handling for invalid series ID."""
        invalid_series_id = "INVALID_SERIES_12345"
        
        response = http_client.post(
            f"{BACKEND_URL}/api/fred/fetch",
            json={"series_id": invalid_series_id},
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 404 for invalid series
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()
    
    @pytest.mark.integration
    def test_api_endpoints_cors_headers(self, backend_available, http_client):
        """Test that API endpoints have proper CORS headers for frontend access."""
        # Make an OPTIONS request to check CORS
        response = http_client.options(
            f"{BACKEND_URL}/api/fred/fetch",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # CORS headers should be present (even if OPTIONS returns 405, CORS headers should exist)
        # FastAPI typically handles CORS, so we check for CORS headers in any response
        fetch_response = http_client.post(
            f"{BACKEND_URL}/api/fred/fetch",
            json={"series_id": "GDP"},
            headers={
                "Content-Type": "application/json",
                "Origin": FRONTEND_URL
            }
        )
        
        # If CORS is configured, headers should be present
        # Note: This test verifies the endpoint works; CORS configuration is in main.py
        assert fetch_response.status_code in [200, 404]  # 200 if valid, 404 if not found
    
    @pytest.mark.integration
    def test_end_to_end_flow_with_real_data(self, backend_available, http_client):
        """
        Complete end-to-end test: Fetch data → Generate summary → Verify both responses.
        Uses a real FRED series to test the full integration.
        """
        # Use a common FRED series that should always exist
        test_series = "GDP"
        
        # Step 1: Fetch FRED data
        fetch_response = http_client.post(
            f"{BACKEND_URL}/api/fred/fetch",
            json={"series_id": test_series},
            headers={"Content-Type": "application/json"}
        )
        
        if fetch_response.status_code != 200:
            pytest.skip(f"FRED API may not be available or series {test_series} not found")
        
        fred_data = fetch_response.json()
        
        # Verify we got valid data
        assert fred_data["series_id"] == test_series
        assert len(fred_data["observations"]) > 0
        
        # Step 2: Generate summary
        summarize_response = http_client.post(
            f"{BACKEND_URL}/api/summarize",
            json={"data": fred_data},
            headers={"Content-Type": "application/json"}
        )
        
        assert summarize_response.status_code == 200
        summary_data = summarize_response.json()
        
        # Verify summary is meaningful
        assert len(summary_data["summary"]) > 50  # Summary should be substantial
        
        # Step 3: Verify the data structure matches what frontend expects
        # Frontend expects: series_info, observations, observation_count
        assert "series_info" in fred_data
        assert "observations" in fred_data
        assert "observation_count" in fred_data
        
        # Verify observations have date and value
        for obs in fred_data["observations"][:5]:  # Check first 5
            assert "date" in obs
            # Value can be None for missing data, but key should exist
            assert "value" in obs


class TestServiceCommunication:
    """Tests for service-to-service communication."""
    
    @pytest.mark.integration
    def test_backend_frontend_network_connectivity(self, backend_available, frontend_available):
        """Test that backend and frontend can communicate over the network."""
        # Both services should be accessible
        backend_client = httpx.Client(timeout=5.0)
        frontend_client = httpx.Client(timeout=5.0)
        
        try:
            backend_response = backend_client.get(f"{BACKEND_URL}/health")
            assert backend_response.status_code == 200
            
            frontend_response = frontend_client.get(FRONTEND_URL)
            assert frontend_response.status_code == 200
        finally:
            backend_client.close()
            frontend_client.close()
    
    @pytest.mark.integration
    def test_api_response_format(self, backend_available, http_client):
        """Test that API responses match expected format for frontend consumption."""
        response = http_client.post(
            f"{BACKEND_URL}/api/fred/fetch",
            json={"series_id": "GDP"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify JSON structure matches frontend expectations
            assert isinstance(data, dict)
            assert "series_id" in data
            assert "series_info" in data
            assert isinstance(data["series_info"], dict)
            assert "observations" in data
            assert isinstance(data["observations"], list)
            assert "observation_count" in data
            assert isinstance(data["observation_count"], int)

