"""
Tests for API routes (FRED data fetching and summarization endpoints).
"""

import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock
from httpx import HTTPStatusError, Response
from pyspark.sql.types import StringType

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
                seasonal_adjustment="Seasonally Adjusted Annual Rate",
            ),
            observations=[
                FREDObservation(date="2024-01-01", value=25000.0),
                FREDObservation(date="2023-10-01", value=24800.0),
            ],
            observation_count=2,
        )

        mock_fred_service.fetch_series = AsyncMock(return_value=mock_response)

        # Make request
        response = await async_client.post("/api/fred/fetch", json={"series_id": "GDP"})

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_id"] == "GDP"
        assert data["series_info"]["title"] == "Gross Domestic Product"
        assert len(data["observations"]) == 2
        assert data["observation_count"] == 2
        mock_fred_service.fetch_series.assert_called_once_with("GDP")

    @pytest.mark.asyncio
    async def test_fetch_fred_data_series_not_found(
        self, async_client, mock_fred_service
    ):
        """Test FRED data fetch when series is not found."""
        # Setup mock to raise ValueError (series not found)
        mock_fred_service.fetch_series = AsyncMock(
            side_effect=ValueError("Series 'INVALID' not found")
        )

        # Make request
        response = await async_client.post(
            "/api/fred/fetch", json={"series_id": "INVALID"}
        )

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_fetch_fred_data_internal_error(
        self, async_client, mock_fred_service
    ):
        """Test FRED data fetch when internal error occurs."""
        # Setup mock to raise generic exception
        mock_fred_service.fetch_series = AsyncMock(
            side_effect=Exception("Internal server error")
        )

        # Make request
        response = await async_client.post("/api/fred/fetch", json={"series_id": "GDP"})

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
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_fetch_fred_data_invalid_characters(self, client):
        """Test FRED data fetch with invalid characters in series_id."""
        # Invalid characters
        response = client.post("/api/fred/fetch", json={"series_id": "GDP@123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSummarizeEndpoint:
    """Test cases for the summarization endpoint."""

    @pytest.mark.asyncio
    async def test_summarize_success(
        self, async_client, mock_gemini_service, monkeypatch
    ):
        """Test successful data summarization."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr(
            "pathlib.Path.exists", lambda x: False
        )  # Prevent .env loading

        # Setup mock response
        mock_gemini_service.summarize_data = AsyncMock(
            return_value="This is a test summary of the economic data."
        )

        # Make request
        response = await async_client.post(
            "/api/summarize",
            json={"data": {"series_info": {"title": "GDP"}, "observations": []}},
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summary" in data
        assert data["summary"] == "This is a test summary of the economic data."
        mock_gemini_service.summarize_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_api_error(
        self, async_client, mock_gemini_service, monkeypatch
    ):
        """Test summarization when Gemini API fails."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr(
            "pathlib.Path.exists", lambda x: False
        )  # Prevent .env loading

        # Setup mock to raise exception
        mock_gemini_service.summarize_data = AsyncMock(
            side_effect=Exception("Gemini API error")
        )

        # Make request
        response = await async_client.post(
            "/api/summarize", json={"data": {"test": "data"}}
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_summarize_value_error(
        self, async_client, mock_gemini_service, monkeypatch
    ):
        """Test summarization when ValueError is raised."""
        # Mock environment variables and file system for routes.py
        test_key = "AIzaSyCfeYlom4MDQVu4TyY5ciXXYnhnP9_testkey"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)
        monkeypatch.setattr(
            "pathlib.Path.exists", lambda x: False
        )  # Prevent .env loading

        # Setup mock to raise ValueError
        mock_gemini_service.summarize_data = AsyncMock(
            side_effect=ValueError("Invalid API key")
        )

        # Make request
        response = await async_client.post(
            "/api/summarize", json={"data": {"test": "data"}}
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


class TestCategoryEndpoints:
    """Test cases for category browsing endpoints."""

    @pytest.mark.asyncio
    async def test_get_categories_success(self, async_client, mock_category_service):
        """Test successful retrieval of all categories."""
        # Setup mock response
        from app.models.schemas import CategoryInfo

        mock_categories = [
            CategoryInfo(
                id="employment",
                name="Employment",
                icon="📊",
                description="Labor market indicators",
                series_count=12,
            ),
            CategoryInfo(
                id="inflation",
                name="Inflation",
                icon="📈",
                description="Price level and inflation indicators",
                series_count=10,
            ),
        ]
        mock_category_service.get_all_categories.return_value = mock_categories

        # Make request
        response = await async_client.get("/api/categories")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 2
        assert data["categories"][0]["id"] == "employment"
        assert data["categories"][0]["name"] == "Employment"
        assert data["categories"][0]["series_count"] == 12
        mock_category_service.get_all_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_error(self, async_client, mock_category_service):
        """Test categories endpoint when service raises an error."""
        # Setup mock to raise exception
        mock_category_service.get_all_categories.side_effect = Exception(
            "Service error"
        )

        # Make request
        response = await async_client.get("/api/categories")

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_category_series_success(
        self, async_client, mock_category_service, mock_fred_service
    ):
        """Test successful retrieval of series for a category."""
        # Setup mock response
        from app.models.schemas import CategorySeriesResponse, SeriesListItem

        mock_response = CategorySeriesResponse(
            category_id="employment",
            category_name="Employment",
            series=[
                SeriesListItem(
                    id="UNRATE",
                    title="Unemployment Rate",
                    frequency="Monthly",
                    units="Percent",
                    seasonal_adjustment="Seasonally Adjusted",
                ),
                SeriesListItem(
                    id="PAYEMS",
                    title="Nonfarm Payroll Employment",
                    frequency="Monthly",
                    units="Thousands of Persons",
                    seasonal_adjustment="Seasonally Adjusted",
                ),
            ],
            total_count=2,
        )
        mock_category_service.get_category_series = AsyncMock(
            return_value=mock_response
        )

        # Make request
        response = await async_client.get("/api/categories/employment")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["category_id"] == "employment"
        assert data["category_name"] == "Employment"
        assert len(data["series"]) == 2
        assert data["series"][0]["id"] == "UNRATE"
        assert data["series"][0]["title"] == "Unemployment Rate"
        assert data["total_count"] == 2
        mock_category_service.get_category_series.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_category_series_with_search(
        self, async_client, mock_category_service, mock_fred_service
    ):
        """Test category series endpoint with search query parameter."""
        # Setup mock response
        from app.models.schemas import CategorySeriesResponse, SeriesListItem

        mock_response = CategorySeriesResponse(
            category_id="employment",
            category_name="Employment",
            series=[
                SeriesListItem(
                    id="UNRATE",
                    title="Unemployment Rate",
                    frequency="Monthly",
                    units="Percent",
                    seasonal_adjustment="Seasonally Adjusted",
                ),
            ],
            total_count=1,
        )
        mock_category_service.get_category_series = AsyncMock(
            return_value=mock_response
        )

        # Make request with search parameter
        response = await async_client.get("/api/categories/employment?q=UN")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["series"]) == 1
        assert data["series"][0]["id"] == "UNRATE"
        # Verify search term was passed
        call_args = mock_category_service.get_category_series.call_args
        assert call_args.kwargs["search_term"] == "UN"

    @pytest.mark.asyncio
    async def test_get_category_series_not_found(
        self, async_client, mock_category_service, mock_fred_service
    ):
        """Test category series endpoint when category is not found."""
        # Setup mock to raise ValueError (category not found)
        mock_category_service.get_category_series = AsyncMock(
            side_effect=ValueError("Category 'invalid' not found")
        )

        # Make request
        response = await async_client.get("/api/categories/invalid")

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_category_series_internal_error(
        self, async_client, mock_category_service, mock_fred_service
    ):
        """Test category series endpoint when internal error occurs."""
        # Setup mock to raise generic exception
        mock_category_service.get_category_series = AsyncMock(
            side_effect=Exception("Internal server error")
        )

        # Make request
        response = await async_client.get("/api/categories/employment")

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_category_series_empty_search(
        self, async_client, mock_category_service, mock_fred_service
    ):
        """Test category series endpoint with empty search term returns all series."""
        # Setup mock response
        from app.models.schemas import CategorySeriesResponse, SeriesListItem

        mock_response = CategorySeriesResponse(
            category_id="employment",
            category_name="Employment",
            series=[
                SeriesListItem(id="UNRATE", title="UNRATE"),
                SeriesListItem(id="PAYEMS", title="PAYEMS"),
            ],
            total_count=2,
        )
        mock_category_service.get_category_series = AsyncMock(
            return_value=mock_response
        )

        # Make request with empty search parameter
        response = await async_client.get("/api/categories/employment?q=")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["series"]) == 2


class TestSparkHealthEndpoint:
    """Test cases for the Spark health check endpoint."""

    @pytest.mark.asyncio
    async def test_spark_health_success(self, async_client, mock_spark_service):
        """Test successful Spark health check."""
        # Setup mock response
        mock_spark_service.is_available.return_value = True
        mock_spark_service.spark.version = "3.5.0"

        # Make request
        response = await async_client.get("/api/spark/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Spark"
        assert data["version"] == "3.5.0"
        assert data["available"] is True
        mock_spark_service.is_available.assert_called_once()

    @pytest.mark.asyncio
    async def test_spark_health_unavailable(self, async_client, mock_spark_service):
        """Test Spark health check when Spark is unavailable."""
        # Setup mock to return False for availability
        mock_spark_service.is_available.return_value = False

        # Make request
        response = await async_client.get("/api/spark/health")

        # Assertions
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "not available" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_spark_health_error(self, async_client, mock_spark_service):
        """Test Spark health check when an error occurs."""
        # Setup mock to raise exception
        mock_spark_service.is_available.side_effect = Exception("Spark error")

        # Make request
        response = await async_client.get("/api/spark/health")

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()


class TestBatchFetchEndpoint:
    """Test cases for the Spark batch fetch endpoint."""

    @pytest.mark.asyncio
    async def test_batch_fetch_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful batch fetch of multiple series."""
        from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation

        # Setup mock FRED responses
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=25000.0),
                    FREDObservation(date="2023-10-01", value=24800.0),
                ],
                observation_count=2,
            ),
            FREDDataResponse(
                series_id="UNRATE",
                series_info=FREDSeriesInfo(
                    id="UNRATE",
                    title="Unemployment Rate",
                    units="Percent",
                    frequency="Monthly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=3.5),
                    FREDObservation(date="2023-12-01", value=3.6),
                ],
                observation_count=2,
            ),
        ]

        # Setup mock DataFrame dictionary
        mock_data_dict = {
            "columns": ["series_id", "date", "value", "title", "units", "frequency"],
            "data": [
                {
                    "series_id": "GDP",
                    "date": "2024-01-01",
                    "value": 25000.0,
                    "title": "Gross Domestic Product",
                    "units": "Billions of Dollars",
                    "frequency": "Quarterly",
                },
                {
                    "series_id": "GDP",
                    "date": "2023-10-01",
                    "value": 24800.0,
                    "title": "Gross Domestic Product",
                    "units": "Billions of Dollars",
                    "frequency": "Quarterly",
                },
                {
                    "series_id": "UNRATE",
                    "date": "2024-01-01",
                    "value": 3.5,
                    "title": "Unemployment Rate",
                    "units": "Percent",
                    "frequency": "Monthly",
                },
                {
                    "series_id": "UNRATE",
                    "date": "2023-12-01",
                    "value": 3.6,
                    "title": "Unemployment Rate",
                    "units": "Percent",
                    "frequency": "Monthly",
                },
            ],
            "row_count": 4,
        }

        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_spark_data_service.convert_to_dataframe = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.aggregate_series_data = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.dataframe_to_dict = MagicMock(
            return_value=mock_data_dict
        )

        # Make request
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP", "UNRATE"], "limit": 10, "sort_order": "desc"},
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_count"] == 2
        assert data["total_observations"] == 4
        assert len(data["columns"]) == 6
        assert len(data["data"]) == 4
        assert len(data["series_info"]) == 2
        assert data["series_info"][0]["series_id"] == "GDP"
        assert data["series_info"][1]["series_id"] == "UNRATE"
        mock_spark_service.is_available.assert_called_once()
        mock_spark_data_service.batch_fetch_series.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_fetch_spark_unavailable(
        self, async_client, mock_spark_service, mock_fred_service
    ):
        """Test batch fetch when Spark is unavailable."""
        # Setup mock to return False for availability
        mock_spark_service.is_available.return_value = False

        # Make request
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP", "UNRATE"], "limit": 10, "sort_order": "desc"},
        )

        # Assertions
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "not available" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_batch_fetch_invalid_request(self, client):
        """Test batch fetch with invalid request body."""
        # Missing series_ids
        response = client.post("/api/spark/batch-fetch", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Empty series_ids
        response = client.post("/api/spark/batch-fetch", json={"series_ids": []})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Too many series_ids (max 50)
        response = client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": [f"SERIES{i}" for i in range(51)]},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid limit (too high)
        response = client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP"], "limit": 2000},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid sort_order
        response = client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP"], "sort_order": "invalid"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_batch_fetch_series_id_validation(self, client):
        """Test that series_ids are validated and normalized."""
        # Test with lowercase - should be converted to uppercase
        response = client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["gdp", "unrate"]},
        )
        # Should pass validation (will fail at service level if not found, but validation should pass)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]

        # Invalid characters
        response = client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP@123"]},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_batch_fetch_internal_error(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test batch fetch when internal error occurs."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            side_effect=Exception("Internal server error")
        )

        # Make request
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP", "UNRATE"], "limit": 10, "sort_order": "desc"},
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_batch_fetch_value_error(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test batch fetch when ValueError is raised."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            side_effect=ValueError("Invalid series IDs")
        )

        # Make request
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={"series_ids": ["GDP", "UNRATE"], "limit": 10, "sort_order": "desc"},
        )

        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid series IDs" in data["detail"]


class TestCacheEndpoints:
    """Test cases for cache management endpoints."""

    @pytest.mark.asyncio
    async def test_get_cache_stats_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful cache stats retrieval."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.get_cache_stats = MagicMock(
            return_value={
                "total_files": 5,
                "unique_series": 3,
                "total_size_bytes": 1024000,
                "total_size_mb": 0.98,
            }
        )

        # Make request
        response = await async_client.get("/api/spark/cache/stats")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_files"] == 5
        assert data["unique_series"] == 3
        assert data["total_size_bytes"] == 1024000
        assert data["total_size_mb"] == 0.98

    @pytest.mark.asyncio
    async def test_get_cache_stats_spark_unavailable(
        self, async_client, mock_spark_service
    ):
        """Test cache stats when Spark is unavailable."""
        mock_spark_service.is_available.return_value = False

        response = await async_client.get("/api/spark/cache/stats")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_list_cached_series_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful cache list retrieval."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_cache_entries = [
            {
                "series_id": "GDP",
                "limit": 100,
                "sort_order": "desc",
                "file_size": 512000,
                "modified_time": "2024-01-01T12:00:00",
                "cache_path": "/app/data/cache/GDP_100_desc.parquet",
            },
            {
                "series_id": "UNRATE",
                "limit": 50,
                "sort_order": "asc",
                "file_size": 256000,
                "modified_time": "2024-01-01T13:00:00",
                "cache_path": "/app/data/cache/UNRATE_50_asc.parquet",
            },
        ]
        mock_spark_data_service.get_cached_series = MagicMock(
            return_value=mock_cache_entries
        )

        # Make request
        response = await async_client.get("/api/spark/cache/list")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["entries"]) == 2
        assert data["entries"][0]["series_id"] == "GDP"
        assert data["entries"][1]["series_id"] == "UNRATE"

    @pytest.mark.asyncio
    async def test_clear_all_cache_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful clearing of all cache."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.clear_cache = MagicMock(return_value=5)

        # Make request
        response = await async_client.delete("/api/spark/cache/clear")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 5
        assert data["series_id"] == "all"
        mock_spark_data_service.clear_cache.assert_called_once_with(series_id=None)

    @pytest.mark.asyncio
    async def test_clear_specific_series_cache_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful clearing of specific series cache."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.clear_cache = MagicMock(return_value=2)

        # Make request
        response = await async_client.delete("/api/spark/cache/clear?series_id=GDP")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 2
        assert data["series_id"] == "GDP"
        mock_spark_data_service.clear_cache.assert_called_once_with(series_id="GDP")

    @pytest.mark.asyncio
    async def test_clear_series_cache_by_path_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful clearing of series cache using path parameter."""
        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.clear_cache = MagicMock(return_value=2)

        # Make request
        response = await async_client.delete("/api/spark/cache/UNRATE")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 2
        assert data["series_id"] == "UNRATE"
        assert "UNRATE" in data["message"]
        mock_spark_data_service.clear_cache.assert_called_once_with(series_id="UNRATE")

    @pytest.mark.asyncio
    async def test_batch_fetch_with_cache(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test batch fetch with caching enabled."""
        from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation

        # Setup mock responses
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=25000.0),
                ],
                observation_count=1,
            ),
        ]

        # Setup mocks
        mock_spark_service.is_available.return_value = True
        # Mock cache check - first call returns False (not cached), second returns True (cached)
        mock_spark_data_service.is_cached = MagicMock(return_value=False)
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_spark_data_service.convert_to_dataframe = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.aggregate_series_data = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.dataframe_to_dict = MagicMock(
            return_value={
                "columns": ["series_id", "date", "value"],
                "data": [{"series_id": "GDP", "date": "2024-01-01", "value": 25000.0}],
                "row_count": 1,
            }
        )

        # Make request with use_cache=True
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={
                "series_ids": ["GDP"],
                "limit": 10,
                "sort_order": "desc",
                "use_cache": True,
            },
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_count"] == 1
        # Verify use_cache was passed
        call_args = mock_spark_data_service.batch_fetch_series.call_args
        assert call_args.kwargs["use_cache"] is True

    @pytest.mark.asyncio
    async def test_batch_fetch_without_cache(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test batch fetch with caching disabled."""
        from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation

        # Setup mock responses
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=25000.0),
                ],
                observation_count=1,
            ),
        ]

        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_spark_data_service.convert_to_dataframe = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.aggregate_series_data = MagicMock(
            return_value=MagicMock()
        )
        mock_spark_data_service.dataframe_to_dict = MagicMock(
            return_value={
                "columns": ["series_id", "date", "value"],
                "data": [{"series_id": "GDP", "date": "2024-01-01", "value": 25000.0}],
                "row_count": 1,
            }
        )

        # Make request with use_cache=False
        response = await async_client.post(
            "/api/spark/batch-fetch",
            json={
                "series_ids": ["GDP"],
                "limit": 10,
                "sort_order": "desc",
                "use_cache": False,
            },
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_count"] == 1
        # Verify use_cache was passed
        call_args = mock_spark_data_service.batch_fetch_series.call_args
        assert call_args.kwargs["use_cache"] is False


class TestAnalyticsEndpoint:
    """Test cases for analytics endpoint."""

    @pytest.mark.asyncio
    async def test_analytics_statistics_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful statistics calculation."""
        # Mock FRED response
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=25000.0),
                    FREDObservation(date="2024-02-01", value=25100.0),
                ],
                observation_count=2,
            ),
        ]

        # Setup mocks
        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe = MagicMock(return_value=mock_df)
        mock_spark_data_service._prepare_dataframe_for_analytics = MagicMock(
            return_value=mock_df
        )
        mock_spark_data_service.calculate_statistics = MagicMock(
            return_value=[
                {
                    "series_id": "GDP",
                    "mean": 25050.0,
                    "median": 25050.0,
                    "std": 50.0,
                    "min": 25000.0,
                    "max": 25100.0,
                    "count": 2,
                    "sum": 50100.0,
                }
            ]
        )

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["statistics"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["series_count"] == 1
        assert data["statistics"] is not None
        assert len(data["statistics"]) == 1
        assert data["statistics"][0]["series_id"] == "GDP"
        assert data["statistics"][0]["mean"] == 25050.0

    @pytest.mark.asyncio
    async def test_analytics_growth_rates_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful growth rates calculation."""
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[
                    FREDObservation(date="2024-01-01", value=25000.0),
                    FREDObservation(date="2024-02-01", value=25100.0),
                ],
                observation_count=2,
            ),
        ]

        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe.return_value = mock_df
        mock_spark_data_service._prepare_dataframe_for_analytics.return_value = mock_df
        mock_spark_data_service.calculate_growth_rates = MagicMock(
            return_value=[
                {
                    "series_id": "GDP",
                    "date": "2024-02-01",
                    "value": 25100.0,
                    "previous_value": 25000.0,
                    "growth_rate": 0.4,
                    "growth_type": "period_over_period",
                }
            ]
        )

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["growth_rates"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["growth_rates"] is not None
        assert len(data["growth_rates"]) == 1
        assert data["growth_rates"][0]["growth_type"] == "period_over_period"

    @pytest.mark.asyncio
    async def test_analytics_correlations_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful correlations calculation."""
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[FREDObservation(date="2024-01-01", value=25000.0)],
                observation_count=1,
            ),
            FREDDataResponse(
                series_id="UNRATE",
                series_info=FREDSeriesInfo(
                    id="UNRATE",
                    title="Unemployment Rate",
                    units="Percent",
                    frequency="Monthly",
                    seasonal_adjustment=None,
                ),
                observations=[FREDObservation(date="2024-01-01", value=3.5)],
                observation_count=1,
            ),
        ]

        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe.return_value = mock_df
        mock_spark_data_service._prepare_dataframe_for_analytics.return_value = mock_df
        mock_spark_data_service.calculate_correlations = MagicMock(
            return_value=[
                {
                    "series_id_1": "GDP",
                    "series_id_2": "UNRATE",
                    "correlation": -0.75,
                }
            ]
        )

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP", "UNRATE"],
                "analytics_types": ["correlations"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["correlations"] is not None
        assert len(data["correlations"]) == 1
        assert data["correlations"][0]["series_id_1"] == "GDP"
        assert data["correlations"][0]["correlation"] == -0.75

    @pytest.mark.asyncio
    async def test_analytics_moving_averages_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful moving averages calculation."""
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[FREDObservation(date="2024-01-01", value=25000.0)],
                observation_count=1,
            ),
        ]

        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe.return_value = mock_df
        mock_spark_data_service._prepare_dataframe_for_analytics.return_value = mock_df
        mock_spark_data_service.calculate_moving_averages = MagicMock(
            return_value=[
                {
                    "series_id": "GDP",
                    "date": "2024-01-01",
                    "value": 25000.0,
                    "moving_average": 25000.0,
                    "moving_average_type": "sma",
                    "window_size": 7,
                }
            ]
        )

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["moving_averages"],
                "limit": 10,
                "moving_average_window": 7,
                "moving_average_type": "sma",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["moving_averages"] is not None
        assert len(data["moving_averages"]) == 1
        assert data["moving_averages"][0]["moving_average_type"] == "sma"

    @pytest.mark.asyncio
    async def test_analytics_time_aggregations_success(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test successful time aggregations calculation."""
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[FREDObservation(date="2024-01-01", value=25000.0)],
                observation_count=1,
            ),
        ]

        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe.return_value = mock_df
        mock_spark_data_service._prepare_dataframe_for_analytics.return_value = mock_df
        mock_spark_data_service.calculate_time_aggregations = MagicMock(
            return_value=[
                {
                    "series_id": "GDP",
                    "period": "2024-01",
                    "aggregated_value": 25000.0,
                    "aggregation_function": "mean",
                    "observation_count": 1,
                }
            ]
        )

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["time_aggregations"],
                "limit": 10,
                "time_aggregation_period": "monthly",
                "time_aggregation_function": "mean",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["time_aggregations"] is not None
        assert len(data["time_aggregations"]) == 1
        assert data["time_aggregations"][0]["period"] == "2024-01"

    @pytest.mark.asyncio
    async def test_analytics_missing_moving_average_params(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test analytics endpoint with missing moving average parameters."""
        mock_spark_service.is_available.return_value = True

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["moving_averages"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_analytics_missing_time_aggregation_params(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test analytics endpoint with missing time aggregation parameters."""
        mock_spark_service.is_available.return_value = True

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["time_aggregations"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_analytics_spark_unavailable(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test analytics endpoint when Spark is unavailable."""
        mock_spark_service.is_available.return_value = False

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["statistics"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_analytics_multiple_types(
        self,
        async_client,
        mock_spark_service,
        mock_fred_service,
        mock_spark_data_service,
    ):
        """Test analytics endpoint with multiple analytics types."""
        mock_responses = [
            FREDDataResponse(
                series_id="GDP",
                series_info=FREDSeriesInfo(
                    id="GDP",
                    title="Gross Domestic Product",
                    units="Billions of Dollars",
                    frequency="Quarterly",
                    seasonal_adjustment=None,
                ),
                observations=[FREDObservation(date="2024-01-01", value=25000.0)],
                observation_count=1,
            ),
        ]

        mock_spark_service.is_available.return_value = True
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_df = MagicMock()
        # Mock count() to return non-zero value
        mock_df.count.return_value = 10
        # Mock schema to avoid AttributeError when accessing df.schema["date"]
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema
        mock_spark_data_service.convert_to_dataframe = MagicMock(return_value=mock_df)
        mock_spark_data_service._prepare_dataframe_for_analytics = MagicMock(
            return_value=mock_df
        )
        # Ensure batch_fetch_series is also properly mocked
        mock_spark_data_service.batch_fetch_series = AsyncMock(
            return_value=mock_responses
        )
        mock_spark_data_service.calculate_statistics = MagicMock(
            return_value=[
                {
                    "series_id": "GDP",
                    "mean": 25000.0,
                    "median": 25000.0,
                    "std": 0.0,
                    "min": 25000.0,
                    "max": 25000.0,
                    "count": 1,
                    "sum": 25000.0,
                }
            ]
        )
        mock_spark_data_service.calculate_growth_rates = MagicMock(return_value=[])

        response = await async_client.post(
            "/api/spark/analytics",
            json={
                "series_ids": ["GDP"],
                "analytics_types": ["statistics", "growth_rates"],
                "limit": 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["statistics"] is not None
        assert data["growth_rates"] is not None
