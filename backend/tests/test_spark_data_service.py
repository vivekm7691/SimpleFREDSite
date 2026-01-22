"""
Tests for SparkDataService.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from pathlib import Path
import os

from app.services.spark_data_service import SparkDataService
from app.models.schemas import FREDDataResponse, FREDSeriesInfo, FREDObservation


class TestSparkDataServiceCacheMethods:
    """Test cases for cache-related methods in SparkDataService."""

    @pytest.fixture
    def mock_spark_service(self):
        """Create a mock Spark service."""
        mock_service = MagicMock()
        mock_spark = MagicMock()
        mock_spark.version = "3.5.0"
        mock_service.spark = mock_spark
        mock_service.is_available = MagicMock(return_value=True)
        return mock_service

    @pytest.fixture
    def mock_fred_service(self):
        """Create a mock FRED service."""
        return MagicMock()

    @pytest.fixture
    def spark_data_service(self, mock_spark_service, mock_fred_service, monkeypatch):
        """Create SparkDataService instance with mocked dependencies."""
        # Mock the cache directory to use a temporary path
        with patch.dict(os.environ, {"DATA_DIR": "/tmp/test_data"}):
            service = SparkDataService(
                spark_service=mock_spark_service, fred_service=mock_fred_service
            )
            # Override cache_dir to use a test directory
            service.cache_dir = Path("/tmp/test_data/cache")
            return service

    def test_get_cache_path(self, spark_data_service):
        """Test getting cache path for a series."""
        path = spark_data_service.get_cache_path("GDP", limit=100, sort_order="desc")
        assert str(path).endswith("GDP_100_desc.parquet")
        assert "cache" in str(path)

    def test_is_cached_false(self, spark_data_service):
        """Test is_cached returns False when cache doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            result = spark_data_service.is_cached("GDP", limit=100, sort_order="desc")
            assert result is False

    def test_is_cached_true(self, spark_data_service):
        """Test is_cached returns True when cache exists."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        with patch.object(spark_data_service, "get_cache_path", return_value=mock_path):
            result = spark_data_service.is_cached("GDP", limit=100, sort_order="desc")
            assert result is True

    def test_save_to_cache(self, spark_data_service, mock_spark_service):
        """Test saving data to cache."""
        # Create mock FRED response
        fred_response = FREDDataResponse(
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
        )

        # Mock DataFrame operations
        mock_df = MagicMock()
        mock_spark_service.spark.createDataFrame.return_value = mock_df
        mock_df.write.mode.return_value = mock_df

        # Mock convert_to_dataframe
        with patch.object(
            spark_data_service, "convert_to_dataframe", return_value=mock_df
        ):
            spark_data_service.save_to_cache(
                fred_response, limit=100, sort_order="desc"
            )

        # Verify DataFrame write was called
        mock_df.write.mode.assert_called_once_with("overwrite")
        mock_df.write.mode.return_value.parquet.assert_called_once()

    def test_load_from_cache_not_exists(self, spark_data_service, mock_spark_service):
        """Test loading from cache when cache doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False

        with patch.object(spark_data_service, "get_cache_path", return_value=mock_path):
            result = spark_data_service.load_from_cache(
                "GDP", limit=100, sort_order="desc"
            )
            assert result is None

    def test_load_from_cache_success(self, spark_data_service, mock_spark_service):
        """Test loading from cache successfully."""
        # Mock cache path exists
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        # Mock DataFrame with data
        mock_df = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.asDict.return_value = {
            "series_id": "GDP",
            "date": "2024-01-01",
            "value": 25000.0,
            "title": "Gross Domestic Product",
            "units": "Billions of Dollars",
            "frequency": "Quarterly",
        }
        mock_df.collect.return_value = [mock_row1]
        mock_spark_service.spark.read.parquet.return_value = mock_df

        with patch.object(spark_data_service, "get_cache_path", return_value=mock_path):
            result = spark_data_service.load_from_cache(
                "GDP", limit=100, sort_order="desc"
            )

            assert result is not None
            assert result.series_id == "GDP"
            assert len(result.observations) == 1
            assert result.observations[0].date == "2024-01-01"
            assert result.observations[0].value == 25000.0

    def test_get_cached_series_empty(self, spark_data_service):
        """Test get_cached_series when cache directory doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            result = spark_data_service.get_cached_series()
            assert result == []

    def test_get_cached_series_with_entries(self, spark_data_service):
        """Test get_cached_series with cached entries."""
        # Mock cache directory with entries
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [
            MagicMock(
                name="GDP_100_desc.parquet",
                stem="GDP_100_desc",
                suffix=".parquet",
                is_dir=lambda: True,
                stat=lambda: MagicMock(st_size=1024, st_mtime=1234567890),
                rglob=lambda pattern: [
                    MagicMock(is_file=lambda: True, stat=lambda: MagicMock(st_size=512))
                ],
            )
        ]

        with patch.object(spark_data_service, "cache_dir", mock_dir):
            result = spark_data_service.get_cached_series()

            assert len(result) == 1
            assert result[0]["series_id"] == "GDP"
            assert result[0]["limit"] == 100
            assert result[0]["sort_order"] == "desc"

    def test_get_cache_stats(self, spark_data_service):
        """Test getting cache statistics."""
        mock_cached_series = [
            {"series_id": "GDP", "file_size": 1024},
            {"series_id": "UNRATE", "file_size": 512},
            {"series_id": "GDP", "file_size": 256},  # Same series, different cache
        ]

        with patch.object(
            spark_data_service, "get_cached_series", return_value=mock_cached_series
        ):
            stats = spark_data_service.get_cache_stats()

            assert stats["total_files"] == 3
            assert stats["unique_series"] == 2  # GDP and UNRATE
            assert stats["total_size_bytes"] == 1792
            assert stats["total_size_mb"] == round(1792 / (1024 * 1024), 2)

    def test_clear_cache_specific_series(self, spark_data_service):
        """Test clearing cache for specific series."""
        import shutil

        # Mock cache directory with entries
        mock_item1 = MagicMock()
        mock_item1.name = "GDP_100_desc.parquet"
        mock_item1.is_dir.return_value = True

        mock_item2 = MagicMock()
        mock_item2.name = "UNRATE_50_asc.parquet"
        mock_item2.is_dir.return_value = True

        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_item1]

        with patch.object(spark_data_service, "cache_dir", mock_dir):
            with patch("shutil.rmtree") as mock_rmtree:
                result = spark_data_service.clear_cache(series_id="GDP")

                assert result == 1
                mock_rmtree.assert_called_once()

    def test_clear_cache_all(self, spark_data_service):
        """Test clearing all cache."""
        import shutil

        # Mock cache directory with entries
        mock_item1 = MagicMock()
        mock_item1.name = "GDP_100_desc.parquet"
        mock_item1.is_dir.return_value = True

        mock_item2 = MagicMock()
        mock_item2.name = "UNRATE_50_asc.parquet"
        mock_item2.is_dir.return_value = True

        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [mock_item1, mock_item2]

        with patch.object(spark_data_service, "cache_dir", mock_dir):
            with patch("shutil.rmtree") as mock_rmtree:
                result = spark_data_service.clear_cache()

                assert result == 2
                assert mock_rmtree.call_count == 2

    def test_clear_cache_directory_not_exists(self, spark_data_service):
        """Test clearing cache when directory doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            result = spark_data_service.clear_cache()
            assert result == 0


class TestSparkDataServiceBatchFetch:
    """Test cases for batch_fetch_series method with caching."""

    @pytest.fixture
    def mock_spark_service(self):
        """Create a mock Spark service."""
        mock_service = MagicMock()
        mock_spark = MagicMock()
        mock_spark.version = "3.5.0"
        mock_service.spark = mock_spark
        mock_service.is_available = MagicMock(return_value=True)
        return mock_service

    @pytest.fixture
    def mock_fred_service(self):
        """Create a mock FRED service."""
        return MagicMock()

    @pytest.fixture
    def spark_data_service(self, mock_spark_service, mock_fred_service, monkeypatch):
        """Create SparkDataService instance with mocked dependencies."""
        with patch.dict(os.environ, {"DATA_DIR": "/tmp/test_data"}):
            service = SparkDataService(
                spark_service=mock_spark_service, fred_service=mock_fred_service
            )
            service.cache_dir = Path("/tmp/test_data/cache")
            return service

    @pytest.mark.asyncio
    async def test_batch_fetch_with_cache_hit(self, spark_data_service):
        """Test batch fetch when data is in cache."""
        # Mock cached response
        cached_response = FREDDataResponse(
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
        )

        # Mock cache check and load
        with patch.object(spark_data_service, "is_cached", return_value=True):
            with patch.object(
                spark_data_service, "load_from_cache", return_value=cached_response
            ):
                result = await spark_data_service.batch_fetch_series(
                    ["GDP"], limit=100, sort_order="desc", use_cache=True
                )

                assert len(result) == 1
                assert result[0].series_id == "GDP"
                # Should not call FRED service
                spark_data_service.fred_service.fetch_series.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_fetch_with_cache_miss(self, spark_data_service):
        """Test batch fetch when data is not in cache."""
        # Mock FRED response
        fred_response = FREDDataResponse(
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
        )

        # Mock cache check returns False, then fetch from API
        with patch.object(spark_data_service, "is_cached", return_value=False):
            with patch.object(spark_data_service, "load_from_cache", return_value=None):
                spark_data_service.fred_service.fetch_series = AsyncMock(
                    return_value=fred_response
                )
                with patch.object(spark_data_service, "save_to_cache"):
                    result = await spark_data_service.batch_fetch_series(
                        ["GDP"], limit=100, sort_order="desc", use_cache=True
                    )

                    assert len(result) == 1
                    assert result[0].series_id == "GDP"
                    # Should call FRED service
                    spark_data_service.fred_service.fetch_series.assert_called_once()
                    # Should save to cache
                    spark_data_service.save_to_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_fetch_without_cache(self, spark_data_service):
        """Test batch fetch with caching disabled."""
        # Mock FRED response
        fred_response = FREDDataResponse(
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
        )

        spark_data_service.fred_service.fetch_series = AsyncMock(
            return_value=fred_response
        )

        # Mock is_cached to verify it's not called when use_cache=False
        with patch.object(spark_data_service, "is_cached") as mock_is_cached:
            result = await spark_data_service.batch_fetch_series(
                ["GDP"], limit=100, sort_order="desc", use_cache=False
            )

            assert len(result) == 1
            # Should not check cache when use_cache=False
            mock_is_cached.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_fetch_empty_series_ids(self, spark_data_service):
        """Test batch fetch with empty series_ids raises ValueError."""
        with pytest.raises(ValueError, match="series_ids cannot be empty"):
            await spark_data_service.batch_fetch_series([], use_cache=True)


class TestSparkDataServiceDataFrameMethods:
    """Test cases for DataFrame conversion methods."""

    @pytest.fixture
    def mock_spark_service(self):
        """Create a mock Spark service."""
        mock_service = MagicMock()
        mock_spark = MagicMock()
        mock_spark.version = "3.5.0"
        mock_service.spark = mock_spark
        return mock_service

    @pytest.fixture
    def mock_fred_service(self):
        """Create a mock FRED service."""
        return MagicMock()

    @pytest.fixture
    def spark_data_service(self, mock_spark_service, mock_fred_service):
        """Create SparkDataService instance."""
        return SparkDataService(
            spark_service=mock_spark_service, fred_service=mock_fred_service
        )

    def test_convert_to_dataframe(self, spark_data_service, mock_spark_service):
        """Test converting FRED responses to DataFrame."""
        # Create mock FRED responses
        fred_responses = [
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
        ]

        # Mock DataFrame creation
        mock_df = MagicMock()
        mock_df.count.return_value = 2
        mock_spark_service.spark.createDataFrame.return_value = mock_df

        result = spark_data_service.convert_to_dataframe(fred_responses)

        assert result == mock_df
        mock_spark_service.spark.createDataFrame.assert_called_once()

    def test_convert_to_dataframe_empty(self, spark_data_service, mock_spark_service):
        """Test converting empty FRED responses to DataFrame."""
        # Mock empty DataFrame
        mock_df = MagicMock()
        mock_spark_service.spark.createDataFrame.return_value = mock_df

        result = spark_data_service.convert_to_dataframe([])

        assert result == mock_df
        mock_spark_service.spark.createDataFrame.assert_called_once()

    def test_dataframe_to_dict(self, spark_data_service):
        """Test converting DataFrame to dictionary."""
        # Mock DataFrame with rows
        mock_df = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.asDict.return_value = {
            "series_id": "GDP",
            "date": "2024-01-01",
            "value": 25000.0,
        }
        mock_row2 = MagicMock()
        mock_row2.asDict.return_value = {
            "series_id": "GDP",
            "date": "2023-10-01",
            "value": 24800.0,
        }
        mock_df.collect.return_value = [mock_row1, mock_row2]
        mock_df.columns = ["series_id", "date", "value"]

        result = spark_data_service.dataframe_to_dict(mock_df)

        assert result["row_count"] == 2
        assert len(result["data"]) == 2
        assert result["columns"] == ["series_id", "date", "value"]
        assert result["data"][0]["series_id"] == "GDP"

    def test_aggregate_series_data_union(self, spark_data_service):
        """Test aggregating series data with union type."""
        mock_df = MagicMock()
        result = spark_data_service.aggregate_series_data(
            mock_df, aggregation_type="union"
        )
        assert result == mock_df

    def test_aggregate_series_data_unsupported(self, spark_data_service):
        """Test aggregating series data with unsupported type raises error."""
        mock_df = MagicMock()
        with pytest.raises(ValueError, match="Unsupported aggregation type"):
            spark_data_service.aggregate_series_data(
                mock_df, aggregation_type="invalid"
            )
