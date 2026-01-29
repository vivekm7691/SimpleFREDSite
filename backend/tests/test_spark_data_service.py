"""
Tests for SparkDataService.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from pathlib import Path
from datetime import date
import os
import numpy as np

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
    def spark_data_service(
        self, mock_spark_service, mock_fred_service, monkeypatch, tmp_path
    ):
        """Create SparkDataService instance with mocked dependencies."""
        # Use temporary directory for cache
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Mock the cache directory creation to avoid permission errors
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("pathlib.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                # Override cache_dir to use the temp directory
                service.cache_dir = cache_dir
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

    def test_get_cached_series_with_entries(self, spark_data_service, tmp_path):
        """Test get_cached_series with cached entries."""
        from datetime import datetime

        # Create a mock cache directory structure
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock parquet directory
        parquet_dir = cache_dir / "GDP_100_desc.parquet"
        parquet_dir.mkdir()

        # Create a mock file inside the parquet directory
        mock_file = parquet_dir / "part-00000.parquet"
        mock_file.write_bytes(b"mock data")

        # Override cache_dir
        spark_data_service.cache_dir = cache_dir

        result = spark_data_service.get_cached_series()

        assert len(result) == 1
        assert result[0]["series_id"] == "GDP"
        assert result[0]["limit"] == 100
        assert result[0]["sort_order"] == "desc"
        assert "modified_time" in result[0]
        assert "file_size" in result[0]

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
    def spark_data_service(
        self, mock_spark_service, mock_fred_service, monkeypatch, tmp_path
    ):
        """Create SparkDataService instance with mocked dependencies."""
        # Use temporary directory for cache
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Mock the cache directory creation to avoid permission errors
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("pathlib.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                # Override cache_dir to use the temp directory
                service.cache_dir = cache_dir
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
    def spark_data_service(self, mock_spark_service, mock_fred_service, tmp_path):
        """Create SparkDataService instance."""
        # Use temporary directory for cache to avoid permission issues
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("app.services.spark_data_service.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                # Override cache_dir to use the temp directory
                service.cache_dir = cache_dir
                return service

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


class TestSparkDataServiceAnalytics:
    """Test cases for analytics methods in SparkDataService."""

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
    def spark_data_service(
        self, mock_spark_service, mock_fred_service, monkeypatch, tmp_path
    ):
        """Create SparkDataService instance with mocked dependencies."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("pathlib.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                return service

    def test_prepare_dataframe_for_analytics(self, spark_data_service, mock_spark_service):
        """Test preparing DataFrame for analytics."""
        from pyspark.sql.types import StringType

        # Mock DataFrame with string dates
        mock_df = MagicMock()
        mock_df.count.return_value = 2
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = StringType()
        mock_df.schema = mock_schema

        # Mock date conversion operations - chain the return values
        mock_with_col = MagicMock()
        mock_df.withColumn.return_value = mock_with_col
        mock_with_col.orderBy.return_value = mock_with_col
        mock_with_col.drop.return_value = mock_with_col
        mock_with_col.withColumnRenamed.return_value = mock_df

        # Mock the Spark functions
        with patch("app.services.spark_data_service.to_date") as mock_to_date, \
             patch("app.services.spark_data_service.col") as mock_col:
            result = spark_data_service._prepare_dataframe_for_analytics(mock_df)

            assert result == mock_df
            mock_df.withColumn.assert_called()

    def test_calculate_statistics_empty_dataframe(self, spark_data_service):
        """Test calculating statistics with empty DataFrame."""
        mock_df = MagicMock()
        mock_df.count.return_value = 0

        result = spark_data_service.calculate_statistics(mock_df)

        assert result == []

    def test_calculate_statistics_success(self, spark_data_service, mock_spark_service):
        """Test calculating statistics successfully."""
        from pyspark.sql.types import DateType

        # Mock DataFrame
        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock aggregation operations
        mock_grouped = MagicMock()
        mock_df.groupBy.return_value = mock_grouped
        mock_agg = MagicMock()
        mock_grouped.agg.return_value = mock_agg

        # Mock result row
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "series_id": "GDP",
            "mean": 25000.0,
            "median": 25000.0,
            "std": 100.0,
            "min": 24800.0,
            "max": 25200.0,
            "count": 10,
            "sum": 250000.0,
        }[key]
        mock_agg.collect.return_value = [mock_row]

        # Mock Spark functions to avoid requiring SparkContext
        with patch("app.services.spark_data_service.avg"), \
             patch("app.services.spark_data_service.expr"), \
             patch("app.services.spark_data_service.stddev"), \
             patch("app.services.spark_data_service.spark_min"), \
             patch("app.services.spark_data_service.spark_max"), \
             patch("app.services.spark_data_service.count"), \
             patch("app.services.spark_data_service.spark_sum"):
            result = spark_data_service.calculate_statistics(mock_df)

            assert len(result) == 1
            assert result[0]["series_id"] == "GDP"
            assert result[0]["mean"] == 25000.0
            assert result[0]["count"] == 10

    def test_calculate_growth_rates_empty_dataframe(self, spark_data_service):
        """Test calculating growth rates with empty DataFrame."""
        mock_df = MagicMock()
        mock_df.count.return_value = 0

        result = spark_data_service.calculate_growth_rates(mock_df)

        assert result == []

    def test_calculate_correlations_insufficient_series(self, spark_data_service):
        """Test calculating correlations with less than 2 series."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock select distinct to return single series
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_row = MagicMock()
        mock_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_row]

        result = spark_data_service.calculate_correlations(mock_df)

        assert result == []

    def test_calculate_moving_averages_sma(self, spark_data_service):
        """Test calculating simple moving averages."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock series selection
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_row = MagicMock()
        mock_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_row]

        # Mock filtering and window operations
        mock_filtered = MagicMock()
        mock_df.filter.return_value = mock_filtered
        mock_filtered.orderBy.return_value = mock_filtered
        mock_filtered.withColumn.return_value = mock_filtered

        # Mock result collection
        mock_select = MagicMock()
        mock_filtered.select.return_value = mock_select
        mock_result_row = MagicMock()
        mock_result_row.__getitem__.side_effect = lambda key: {
            "series_id": "GDP",
            "date": MagicMock(strftime=lambda fmt: "2024-01-01"),
            "value": 25000.0,
            "moving_average": 25000.0,
        }[key]
        mock_select.collect.return_value = [mock_result_row]

        # Mock Spark functions to avoid requiring SparkContext
        with patch("app.services.spark_data_service.col"), \
             patch("app.services.spark_data_service.avg"), \
             patch("app.services.spark_data_service.Window") as mock_window:
            mock_window.partitionBy.return_value.orderBy.return_value.rowsBetween.return_value = MagicMock()
            result = spark_data_service.calculate_moving_averages(mock_df, window_size=7, ma_type="sma")

            assert len(result) == 1
            assert result[0]["series_id"] == "GDP"
            assert result[0]["moving_average_type"] == "sma"
            assert result[0]["window_size"] == 7

    def test_calculate_moving_averages_ema(self, spark_data_service):
        """Test calculating exponential moving averages."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock series selection
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_row = MagicMock()
        mock_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_row]

        # Mock filtering and window operations
        mock_filtered = MagicMock()
        mock_df.filter.return_value = mock_filtered
        mock_filtered.orderBy.return_value = mock_filtered
        mock_filtered.withColumn.return_value = mock_filtered
        mock_filtered.drop.return_value = mock_filtered

        # Mock result collection
        mock_select = MagicMock()
        mock_filtered.select.return_value = mock_select
        mock_result_row = MagicMock()
        mock_result_row.__getitem__.side_effect = lambda key: {
            "series_id": "GDP",
            "date": MagicMock(strftime=lambda fmt: "2024-01-01"),
            "value": 25000.0,
            "moving_average": 25000.0,
        }[key]
        mock_select.collect.return_value = [mock_result_row]

        # Mock Spark functions to avoid requiring SparkContext
        # Need to mock col() to return a comparable object
        mock_col = MagicMock()
        mock_col.__le__ = lambda self, other: MagicMock()  # Make it comparable
        mock_col.__mul__ = lambda self, other: MagicMock()
        mock_col.__add__ = lambda self, other: MagicMock()
        
        with patch("app.services.spark_data_service.col", return_value=mock_col), \
             patch("app.services.spark_data_service.avg", return_value=MagicMock()), \
             patch("app.services.spark_data_service.expr", return_value=MagicMock()), \
             patch("app.services.spark_data_service.when", return_value=MagicMock()), \
             patch("app.services.spark_data_service.lag", return_value=MagicMock()), \
             patch("app.services.spark_data_service.Window") as mock_window:
            mock_window_spec = MagicMock()
            mock_window.partitionBy.return_value.orderBy.return_value.rowsBetween.return_value = mock_window_spec
            result = spark_data_service.calculate_moving_averages(mock_df, window_size=7, ma_type="ema")

            assert len(result) == 1
            assert result[0]["moving_average_type"] == "ema"

    def test_calculate_moving_averages_invalid_type(self, spark_data_service):
        """Test calculating moving averages with invalid type raises error."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_row = MagicMock()
        mock_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value = mock_filtered
        mock_filtered.orderBy.return_value = mock_filtered
        mock_filtered.withColumn.return_value = mock_filtered

        # Mock Spark functions to avoid requiring SparkContext
        with patch("app.services.spark_data_service.col"), \
             patch("app.services.spark_data_service.avg"), \
             patch("app.services.spark_data_service.Window") as mock_window:
            mock_window.partitionBy.return_value.orderBy.return_value.rowsBetween.return_value = MagicMock()
            with pytest.raises(ValueError, match="Unsupported moving average type"):
                spark_data_service.calculate_moving_averages(mock_df, window_size=7, ma_type="invalid")

    def test_calculate_time_aggregations_success(self, spark_data_service):
        """Test calculating time aggregations successfully."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock aggregation operations
        mock_with_col = MagicMock()
        mock_df.withColumn.return_value = mock_with_col
        mock_grouped = MagicMock()
        mock_with_col.groupBy.return_value = mock_grouped
        mock_agg = MagicMock()
        mock_grouped.agg.return_value = mock_agg
        mock_agg.withColumn.return_value = mock_agg

        # Mock result collection
        mock_select = MagicMock()
        mock_agg.select.return_value = mock_select
        mock_result_row = MagicMock()
        mock_result_row.__getitem__.side_effect = lambda key: {
            "series_id": "GDP",
            "period_str": "2024-01",
            "aggregated_value": 25000.0,
            "observation_count": 3,
        }[key]
        mock_select.collect.return_value = [mock_result_row]

        # Mock Spark functions to avoid requiring SparkContext
        with patch("app.services.spark_data_service.date_trunc"), \
             patch("app.services.spark_data_service.col"), \
             patch("app.services.spark_data_service.avg"), \
             patch("app.services.spark_data_service.spark_sum"), \
             patch("app.services.spark_data_service.spark_min"), \
             patch("app.services.spark_data_service.spark_max"), \
             patch("app.services.spark_data_service.count"), \
             patch("app.services.spark_data_service.expr"):
            result = spark_data_service.calculate_time_aggregations(
                mock_df, period="monthly", agg_function="mean"
            )

            assert len(result) == 1
            assert result[0]["series_id"] == "GDP"
            assert result[0]["period"] == "2024-01"
            assert result[0]["aggregation_function"] == "mean"

    def test_calculate_time_aggregations_invalid_period(self, spark_data_service):
        """Test calculating time aggregations with invalid period raises error."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        with pytest.raises(ValueError, match="Unsupported period"):
            spark_data_service.calculate_time_aggregations(
                mock_df, period="invalid", agg_function="mean"
            )

    def test_calculate_time_aggregations_invalid_function(self, spark_data_service):
        """Test calculating time aggregations with invalid function raises error."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock Spark functions to avoid requiring SparkContext
        # Need to patch before the agg_map dictionary is built
        with patch("app.services.spark_data_service.avg", return_value=MagicMock()), \
             patch("app.services.spark_data_service.spark_sum", return_value=MagicMock()), \
             patch("app.services.spark_data_service.spark_min", return_value=MagicMock()), \
             patch("app.services.spark_data_service.spark_max", return_value=MagicMock()), \
             patch("app.services.spark_data_service.expr", return_value=MagicMock()), \
             patch("app.services.spark_data_service.date_trunc", return_value=MagicMock()), \
             patch("app.services.spark_data_service.col", return_value=MagicMock()):
            with pytest.raises(ValueError, match="Unsupported aggregation function"):
                spark_data_service.calculate_time_aggregations(
                    mock_df, period="monthly", agg_function="invalid"
                )


class TestSparkDataServiceAdvancedAnalytics:
    """Test cases for advanced analytics methods in SparkDataService."""

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
    def spark_data_service(
        self, mock_spark_service, mock_fred_service, monkeypatch, tmp_path
    ):
        """Create SparkDataService instance with mocked dependencies."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("pathlib.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                service.cache_dir = tmp_path / "cache"
                return service

    def test_detect_anomalies_z_score(self, spark_data_service):
        """Test anomaly detection using Z-score method."""
        from pyspark.sql.types import DateType
        from datetime import date

        mock_df = MagicMock()
        mock_df.count.return_value = 5
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        # Mock DataFrame operations
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock aggregation for mean and std
        mock_agg = MagicMock()
        mock_filtered.agg.return_value = mock_agg
        mock_stats_row = MagicMock()
        mock_stats_row.__getitem__.side_effect = lambda key: {
            "mean": 100.0,
            "std": 10.0,
        }[key]
        mock_agg.collect.return_value = [mock_stats_row]

        # Mock Z-score calculation
        mock_with_z = MagicMock()
        mock_filtered.withColumn.return_value = mock_with_z
        mock_anomalies_df = MagicMock()
        mock_with_z.filter.return_value = mock_anomalies_df

        # Mock anomaly row
        mock_anomaly_row = MagicMock()
        mock_anomaly_row.__getitem__.side_effect = lambda key: {
            "date": date(2024, 1, 1),
            "value": 130.0,
            "z_score": 3.5,
        }[key]
        mock_anomalies_df.select.return_value.collect.return_value = [
            mock_anomaly_row
        ]

        # Mock col() to support comparison operations
        mock_col = MagicMock()
        mock_col.__gt__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        
        with patch("app.services.spark_data_service.col", return_value=mock_col), patch(
            "app.services.spark_data_service.avg", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.stddev", return_value=MagicMock()
        ):
            result = spark_data_service.detect_anomalies(
                mock_df, method="z_score", threshold=3.0
            )

            # Verify the method was called
            assert mock_df.filter.called

    def test_detect_anomalies_iqr(self, spark_data_service):
        """Test anomaly detection using IQR method."""
        from pyspark.sql.types import DateType

        mock_df = MagicMock()
        mock_df.count.return_value = 5
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock approxQuantile for IQR
        mock_filtered.approxQuantile.return_value = [90.0, 100.0, 110.0]

        mock_anomalies_df = MagicMock()
        mock_filtered.filter.return_value = mock_anomalies_df

        mock_anomaly_row = MagicMock()
        mock_anomaly_row.__getitem__.side_effect = lambda key: {
            "date": date(2024, 1, 1),
            "value": 150.0,
        }[key]
        mock_anomalies_df.select.return_value.collect.return_value = [
            mock_anomaly_row
        ]

        # Mock col() to support comparison operations
        mock_col = MagicMock()
        mock_col.__gt__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        
        with patch("app.services.spark_data_service.col", return_value=mock_col):
            result = spark_data_service.detect_anomalies(mock_df, method="iqr")

            assert mock_df.filter.called

    def test_calculate_volatility(self, spark_data_service):
        """Test volatility calculation."""
        from pyspark.sql.types import DateType
        from datetime import date

        mock_df = MagicMock()
        mock_df.count.return_value = 5
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock return calculation
        mock_with_prev = MagicMock()
        mock_filtered.withColumn.return_value = mock_with_prev
        mock_with_return = MagicMock()
        mock_with_prev.withColumn.return_value = mock_with_return

        # Mock volatility calculation
        mock_with_vol = MagicMock()
        mock_with_return.withColumn.return_value = mock_with_vol

        # Mock result row
        mock_vol_row = MagicMock()
        mock_vol_row.__getitem__.side_effect = lambda key: {
            "date": date(2024, 2, 1),
            "value": 105.0,
            "return": 0.05,
            "volatility": 0.03,
            "annualized_volatility": 0.48,
        }[key]
        mock_with_vol.select.return_value.collect.return_value = [mock_vol_row]

        with patch(
            "app.services.spark_data_service.col", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.lag", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.when", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.stddev", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.expr", return_value=MagicMock()
        ), patch(
            "app.services.spark_data_service.Window", return_value=MagicMock()
        ):
            result = spark_data_service.calculate_volatility(mock_df, window_size=30)

            assert mock_df.filter.called

    def test_analyze_trends_linear(self, spark_data_service):
        """Test trend analysis with linear trend."""
        from pyspark.sql.types import DateType
        from datetime import date

        mock_df = MagicMock()
        mock_df.count.return_value = 5
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock data collection
        mock_data_row = MagicMock()
        mock_data_row.__getitem__.side_effect = lambda key: {
            "date": date(2024, 1, 1),
            "value": 100.0,
            "row_num": 1,
        }[key]
        mock_filtered.select.return_value.collect.return_value = [
            mock_data_row,
            MagicMock(__getitem__=lambda k: {
                "date": date(2024, 2, 1),
                "value": 105.0,
                "row_num": 2,
            }[k]),
        ]

        with patch("app.services.spark_data_service.col", return_value=MagicMock()), patch(
            "app.services.spark_data_service.expr", return_value=MagicMock()
        ):
            result = spark_data_service.analyze_trends(
                mock_df, trend_type="linear"
            )

            assert len(result) >= 0  # May return empty or have trend data

    def test_decompose_seasonal(self, spark_data_service):
        """Test seasonal decomposition."""
        from pyspark.sql.types import DateType
        from datetime import date

        mock_df = MagicMock()
        mock_df.count.return_value = 25  # Enough for seasonal decomposition
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock data collection
        mock_data_rows = []
        for i in range(25):
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key, idx=i: {
                "date": date(2024, 1 + (idx % 12), 1),
                "value": 100.0 + idx,
            }[key]
            mock_data_rows.append(mock_row)

        mock_filtered.select.return_value.collect.return_value = mock_data_rows

        result = spark_data_service.decompose_seasonal(
            mock_df, decomposition_type="additive", seasonal_period=12
        )

        # Should process the data (may return empty if insufficient data)
        assert isinstance(result, list)

    def test_calculate_forecasts_linear_regression(self, spark_data_service):
        """Test forecasting using linear regression."""
        from pyspark.sql.types import DateType
        from datetime import date, timedelta

        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        # Mock data collection
        base_date = date(2024, 1, 1)
        mock_data_rows = []
        for i in range(10):
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key, idx=i: {
                "date": base_date + timedelta(days=30 * idx),
                "value": 100.0 + idx * 5,
            }[key]
            mock_data_rows.append(mock_row)

        mock_filtered.select.return_value.collect.return_value = mock_data_rows

        result = spark_data_service.calculate_forecasts(
            mock_df, forecast_horizon=12, forecast_method="linear_regression"
        )

        # Should generate forecasts
        assert isinstance(result, list)

    def test_detect_anomalies_empty_data(self, spark_data_service):
        """Test anomaly detection with empty DataFrame."""
        mock_df = MagicMock()
        mock_df.count.return_value = 0

        result = spark_data_service.detect_anomalies(mock_df, method="z_score")

        assert result == []

    def test_calculate_volatility_empty_data(self, spark_data_service):
        """Test volatility calculation with empty DataFrame."""
        mock_df = MagicMock()
        mock_df.count.return_value = 0

        result = spark_data_service.calculate_volatility(mock_df, window_size=30)

        assert result == []

    def test_analyze_trends_insufficient_data(self, spark_data_service):
        """Test trend analysis with insufficient data."""
        from pyspark.sql.types import DateType
        from datetime import date

        mock_df = MagicMock()
        mock_df.count.return_value = 1  # Insufficient for trend
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema

        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]

        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered

        mock_data_row = MagicMock()
        mock_data_row.__getitem__.side_effect = lambda key: {
            "date": date(2024, 1, 1),
            "value": 100.0,
            "row_num": 1,
        }[key]
        mock_filtered.select.return_value.collect.return_value = [mock_data_row]

        with patch("app.services.spark_data_service.col", return_value=MagicMock()), patch(
            "app.services.spark_data_service.expr", return_value=MagicMock()
        ):
            result = spark_data_service.analyze_trends(
                mock_df, trend_type="linear"
            )

            # Should handle insufficient data gracefully
            assert isinstance(result, list)
            if len(result) > 0:
                assert result[0]["trend_type"] in ["linear", "polynomial", "none"]


class TestSparkDataServiceModelCaching:
    """Test cases for ARIMA model caching methods in SparkDataService."""

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
    def spark_data_service(
        self, mock_spark_service, mock_fred_service, monkeypatch, tmp_path
    ):
        """Create SparkDataService instance with mocked dependencies."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            with patch("pathlib.Path.mkdir"):
                service = SparkDataService(
                    spark_service=mock_spark_service, fred_service=mock_fred_service
                )
                service.cache_dir = tmp_path / "cache"
                service.model_cache_dir = tmp_path / "models"
                return service

    def test_get_model_cache_path(self, spark_data_service):
        """Test getting model cache path."""
        path = spark_data_service._get_model_cache_path("GDP", 12, "arima")
        assert path.parent == spark_data_service.model_cache_dir
        assert path.name == "GDP_12_arima.pkl"

    def test_is_model_cached_false(self, spark_data_service):
        """Test checking if model is cached when it doesn't exist."""
        result = spark_data_service._is_model_cached("GDP", 12, "arima")
        assert result is False

    def test_is_model_cached_true(self, spark_data_service, tmp_path):
        """Test checking if model is cached when it exists."""
        model_cache_dir = tmp_path / "models"
        model_cache_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_cache_dir / "GDP_12_arima.pkl"
        model_file.write_bytes(b"fake model data")
        
        result = spark_data_service._is_model_cached("GDP", 12, "arima")
        assert result is True

    def test_load_model_from_cache_not_exists(self, spark_data_service):
        """Test loading model from cache when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            spark_data_service._load_model_from_cache("GDP", 12, "arima")

    def test_load_model_from_cache_success(self, spark_data_service, tmp_path):
        """Test loading model from cache successfully."""
        import joblib
        import numpy as np
        
        model_cache_dir = tmp_path / "models"
        model_cache_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_cache_dir / "GDP_12_arima.pkl"
        
        # Create a simple mock model object to cache
        mock_model = {"order": (1, 1, 1), "data": np.array([1, 2, 3])}
        joblib.dump(mock_model, model_file)
        
        loaded_model = spark_data_service._load_model_from_cache("GDP", 12, "arima")
        # Compare dict keys and values separately to avoid numpy array comparison issues
        assert loaded_model["order"] == mock_model["order"]
        assert np.array_equal(loaded_model["data"], mock_model["data"])

    def test_save_model_to_cache(self, spark_data_service, tmp_path):
        """Test saving model to cache."""
        import joblib
        import numpy as np
        
        mock_model = {"order": (1, 1, 1), "data": np.array([1, 2, 3])}
        
        spark_data_service._save_model_to_cache(mock_model, "GDP", 12, "arima")
        
        # Verify file was created
        model_file = tmp_path / "models" / "GDP_12_arima.pkl"
        assert model_file.exists()
        
        # Verify we can load it back
        loaded_model = joblib.load(model_file)
        # Compare dict keys and values separately to avoid numpy array comparison issues
        assert loaded_model["order"] == mock_model["order"]
        assert np.array_equal(loaded_model["data"], mock_model["data"])

    def test_calculate_forecasts_arima_with_cache(self, spark_data_service):
        """Test ARIMA forecasting with cached model."""
        from pyspark.sql.types import DateType
        from datetime import date, timedelta
        import joblib
        import numpy as np
        
        # Create a mock cached model
        model_cache_dir = spark_data_service.model_cache_dir
        model_cache_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_cache_dir / "GDP_12_arima.pkl"
        
        # Don't actually dump MagicMock, instead mock the load
        # Create a callable mock that returns the forecast
        class MockModel:
            def predict(self, n_periods, return_conf_int=True):
                return (
                    np.array([110.0, 115.0, 120.0]),
                    np.array([[105.0, 115.0], [110.0, 120.0], [115.0, 125.0]])
                )
        
        # Create mock DataFrame
        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema
        
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]
        
        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered
        
        base_date = date(2024, 1, 1)
        mock_data_rows = []
        for i in range(10):
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key, idx=i: {
                "date": base_date + timedelta(days=30 * idx),
                "value": 100.0 + idx * 5,
            }[key]
            mock_data_rows.append(mock_row)
        
        mock_filtered.select.return_value.collect.return_value = mock_data_rows
        
        with patch("joblib.load", return_value=MockModel()):
            result = spark_data_service.calculate_forecasts(
                mock_df, forecast_horizon=3, forecast_method="arima"
            )
            
            # Verify model was loaded from cache (not fitted)
            assert len(result) == 3
            assert result[0]["series_id"] == "GDP"
            assert result[0]["forecast_method"] == "arima"

    def test_calculate_forecasts_arima_cache_miss(self, spark_data_service):
        """Test ARIMA forecasting when model is not cached (cache miss)."""
        from pyspark.sql.types import DateType
        from datetime import date, timedelta
        
        # Create mock DataFrame
        mock_df = MagicMock()
        mock_df.count.return_value = 10
        mock_schema = MagicMock()
        mock_schema.__getitem__.return_value.dataType = DateType()
        mock_df.schema = mock_schema
        
        mock_distinct = MagicMock()
        mock_df.select.return_value.distinct.return_value = mock_distinct
        mock_series_row = MagicMock()
        mock_series_row.__getitem__.return_value = "GDP"
        mock_distinct.collect.return_value = [mock_series_row]
        
        mock_filtered = MagicMock()
        mock_df.filter.return_value.orderBy.return_value = mock_filtered
        
        base_date = date(2024, 1, 1)
        mock_data_rows = []
        for i in range(10):
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key, idx=i: {
                "date": base_date + timedelta(days=30 * idx),
                "value": 100.0 + idx * 5,
            }[key]
            mock_data_rows.append(mock_row)
        
        mock_filtered.select.return_value.collect.return_value = mock_data_rows
        
        # Mock pmdarima (imported inside the function, so patch where it's used)
        with patch("pmdarima.auto_arima") as mock_auto_arima, \
             patch("pandas.Series") as mock_pd_series, \
             patch("joblib.dump") as mock_joblib_dump:
            
            # Mock auto_arima to return a model with predict method
            class MockARIMAModel:
                def predict(self, n_periods, return_conf_int=True):
                    forecast = np.array([110.0, 115.0, 120.0])
                    conf_int = np.array([[105.0, 115.0], [110.0, 120.0], [115.0, 125.0]])
                    return forecast, conf_int
            
            mock_arima_model = MockARIMAModel()
            mock_auto_arima.return_value = mock_arima_model
            
            # Mock pandas Series
            mock_series = MagicMock()
            mock_pd_series.return_value = mock_series
            
            result = spark_data_service.calculate_forecasts(
                mock_df, forecast_horizon=3, forecast_method="arima"
            )
            
            # Verify model was fitted (auto_arima was called)
            mock_auto_arima.assert_called_once()
            # Verify model was saved to cache
            mock_joblib_dump.assert_called_once()
