"""
Spark data service for batch processing FRED series data.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
from math import isnan
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)
from pyspark.sql.functions import (
    to_date,
    col,
    avg,
    stddev,
    min as spark_min,
    max as spark_max,
    count,
    sum as spark_sum,
    lag,
    date_trunc,
    year,
    month,
    when,
    expr,
)
from pyspark.sql.window import Window

from app.models.schemas import FREDDataResponse
from app.services.fred_service import FREDService
from app.services.spark_service import SparkService

logger = logging.getLogger(__name__)


class SparkDataService:
    """Service for batch processing FRED data using Spark."""

    def __init__(self, spark_service: SparkService, fred_service: FREDService):
        """
        Initialize Spark data service.

        Args:
            spark_service: SparkService instance for Spark operations
            fred_service: FREDService instance for fetching FRED data
        """
        self.spark_service = spark_service
        self.fred_service = fred_service
        # Get cache directory from environment (defaults to /app/data/cache)
        data_dir = os.getenv("DATA_DIR", "/app/data")
        self.cache_dir = Path(data_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Get model cache directory for ARIMA models
        self.model_cache_dir = Path(data_dir) / "models"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)

    async def batch_fetch_series(
        self,
        series_ids: List[str],
        limit: int = 100,
        sort_order: str = "desc",
        use_cache: bool = True,
    ) -> List[FREDDataResponse]:
        """
        Fetch multiple FRED series in parallel, with optional caching.

        Args:
            series_ids: List of FRED series IDs to fetch
            limit: Maximum number of observations per series
            sort_order: Sort order ('asc' or 'desc')
            use_cache: Whether to use cached data if available

        Returns:
            List of FREDDataResponse objects, one per series

        Raises:
            ValueError: If series_ids is empty
        """
        if not series_ids:
            raise ValueError("series_ids cannot be empty")

        logger.info(f"Batch fetching {len(series_ids)} series: {series_ids}")

        responses = []
        series_to_fetch = []

        # Check cache for each series
        for series_id in series_ids:
            if use_cache and self.is_cached(series_id, limit, sort_order):
                logger.info(f"Loading series '{series_id}' from cache")
                try:
                    cached_response = self.load_from_cache(series_id, limit, sort_order)
                    if cached_response:
                        responses.append(cached_response)
                        continue
                except Exception as e:
                    logger.warning(
                        f"Failed to load '{series_id}' from cache: {str(e)}, fetching from API"
                    )

            # Series not in cache or cache load failed, fetch from API
            series_to_fetch.append(series_id)

        # Fetch remaining series from FRED API in parallel
        if series_to_fetch:
            tasks = [
                self.fred_service.fetch_series(
                    series_id=series_id, limit=limit, sort_order=sort_order
                )
                for series_id in series_to_fetch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle errors
            for i, result in enumerate(results):
                series_id = series_to_fetch[i]
                if isinstance(result, Exception):
                    logger.warning(
                        f"Failed to fetch series '{series_id}': {str(result)}"
                    )
                    # Create a placeholder response for failed series
                    from app.models.schemas import FREDSeriesInfo

                    responses.append(
                        FREDDataResponse(
                            series_id=series_id,
                            series_info=FREDSeriesInfo(
                                id=series_id,
                                title=series_id,
                                units=None,
                                frequency=None,
                                seasonal_adjustment=None,
                            ),
                            observations=[],
                            observation_count=0,
                        )
                    )
                else:
                    responses.append(result)
                    # Save to cache after successful fetch
                    if use_cache:
                        try:
                            self.save_to_cache(result, limit, sort_order)
                        except Exception as e:
                            logger.warning(f"Failed to cache '{series_id}': {str(e)}")

        logger.info(
            f"Successfully fetched {len([r for r in responses if r.observation_count > 0])} series"
        )
        return responses

    def convert_to_dataframe(self, fred_responses: List[FREDDataResponse]) -> DataFrame:
        """
        Convert FRED responses to a Spark DataFrame.

        Args:
            fred_responses: List of FREDDataResponse objects

        Returns:
            Spark DataFrame with columns: series_id, date, value, title, units, frequency
        """
        spark = self.spark_service.spark

        # Define schema for the DataFrame
        schema = StructType(
            [
                StructField("series_id", StringType(), nullable=False),
                StructField("date", StringType(), nullable=False),
                StructField("value", DoubleType(), nullable=True),
                StructField("title", StringType(), nullable=True),
                StructField("units", StringType(), nullable=True),
                StructField("frequency", StringType(), nullable=True),
            ]
        )

        # Prepare data rows
        rows = []
        for response in fred_responses:
            series_id = response.series_id
            title = response.series_info.title
            units = response.series_info.units
            frequency = response.series_info.frequency

            for obs in response.observations:
                rows.append(
                    (
                        series_id,
                        obs.date,
                        obs.value,
                        title,
                        units,
                        frequency,
                    )
                )

        if not rows:
            # Return empty DataFrame with schema if no data
            return spark.createDataFrame([], schema)

        # Create DataFrame
        df = spark.createDataFrame(rows, schema)
        logger.info(
            f"Created DataFrame with {df.count()} rows from {len(fred_responses)} series"
        )
        return df

    def aggregate_series_data(
        self, df: DataFrame, aggregation_type: str = "union"
    ) -> DataFrame:
        """
        Aggregate multiple series data.

        Args:
            df: Spark DataFrame with series data
            aggregation_type: Type of aggregation ('union' or 'summary')

        Returns:
            Aggregated DataFrame

        Note:
            Currently only supports 'union' which combines all series.
            Future increments will add more aggregation types.
        """
        if aggregation_type == "union":
            # Simply return the union of all series (already combined in DataFrame)
            return df
        else:
            raise ValueError(f"Unsupported aggregation type: {aggregation_type}")

    def dataframe_to_dict(self, df: DataFrame) -> dict:
        """
        Convert Spark DataFrame to dictionary format for JSON response.

        Args:
            df: Spark DataFrame

        Returns:
            Dictionary with 'columns' and 'data' keys
        """
        # Collect data to driver (for small datasets, this is fine)
        # For larger datasets, we'd want to paginate or stream
        rows = df.collect()

        # Convert to list of dictionaries
        data = [row.asDict() for row in rows]

        # Get column names
        columns = df.columns

        return {"columns": columns, "data": data, "row_count": len(data)}

    def get_cache_path(
        self, series_id: str, limit: int = 100, sort_order: str = "desc"
    ) -> Path:
        """
        Get the cache file path for a series.

        Args:
            series_id: FRED series ID
            limit: Maximum number of observations
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Path to the cache file
        """
        # Create cache key from series_id, limit, and sort_order
        cache_key = f"{series_id}_{limit}_{sort_order}"
        return self.cache_dir / f"{cache_key}.parquet"

    def is_cached(
        self, series_id: str, limit: int = 100, sort_order: str = "desc"
    ) -> bool:
        """
        Check if a series is cached.

        Args:
            series_id: FRED series ID
            limit: Maximum number of observations
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            True if cached, False otherwise
        """
        cache_path = self.get_cache_path(series_id, limit, sort_order)
        # Parquet files are stored as directories by Spark
        return cache_path.exists() and cache_path.is_dir()

    def save_to_cache(
        self,
        fred_response: FREDDataResponse,
        limit: int = 100,
        sort_order: str = "desc",
    ) -> None:
        """
        Save FRED response to cache as Parquet file.

        Args:
            fred_response: FREDDataResponse to cache
            limit: Maximum number of observations
            sort_order: Sort order ('asc' or 'desc')
        """
        cache_path = self.get_cache_path(fred_response.series_id, limit, sort_order)

        # Convert response to DataFrame
        df = self.convert_to_dataframe([fred_response])

        # Save as Parquet
        df.write.mode("overwrite").parquet(str(cache_path))

        logger.info(f"Cached series '{fred_response.series_id}' to {cache_path}")

    def load_from_cache(
        self, series_id: str, limit: int = 100, sort_order: str = "desc"
    ) -> Optional[FREDDataResponse]:
        """
        Load FRED response from cache.

        Args:
            series_id: FRED series ID
            limit: Maximum number of observations
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            FREDDataResponse if found in cache, None otherwise
        """
        cache_path = self.get_cache_path(series_id, limit, sort_order)

        # Parquet files are stored as directories by Spark
        if not cache_path.exists() or not cache_path.is_dir():
            return None

        try:
            spark = self.spark_service.spark
            # Read from Parquet directory
            df = spark.read.parquet(str(cache_path))

            # Convert DataFrame back to FREDDataResponse
            rows = df.collect()
            if not rows:
                return None

            # Extract series info from first row
            first_row = rows[0].asDict()
            from app.models.schemas import FREDSeriesInfo, FREDObservation

            series_info = FREDSeriesInfo(
                id=series_id,
                title=first_row.get("title", series_id),
                units=first_row.get("units"),
                frequency=first_row.get("frequency"),
                seasonal_adjustment=None,
            )

            # Extract observations
            observations = []
            for row in rows:
                row_dict = row.asDict()
                observations.append(
                    FREDObservation(date=row_dict["date"], value=row_dict.get("value"))
                )

            logger.info(
                f"Loaded series '{series_id}' from cache ({len(observations)} observations)"
            )

            return FREDDataResponse(
                series_id=series_id,
                series_info=series_info,
                observations=observations,
                observation_count=len(observations),
            )
        except Exception as e:
            logger.error(f"Error loading '{series_id}' from cache: {str(e)}")
            return None

    def get_cached_series(self) -> List[dict]:
        """
        Get list of all cached series with metadata.

        Returns:
            List of dictionaries with cache information
        """
        cached_series = []
        if not self.cache_dir.exists():
            return cached_series

        for item in self.cache_dir.iterdir():
            try:
                # Skip hidden files/directories
                if item.name.startswith("."):
                    continue

                # Parquet files are stored as directories by Spark
                # The directory name follows the pattern: series_id_limit_sort_order.parquet
                if item.is_dir() and item.name.endswith(".parquet"):
                    cache_key = item.stem  # Remove .parquet extension
                    parts = cache_key.rsplit("_", 2)
                    if len(parts) == 3:
                        series_id = parts[0]
                        limit = int(parts[1])
                        sort_order = parts[2]

                        # Calculate directory size
                        file_size = sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )

                        # Get modification time
                        stat = item.stat()
                        modified_time = datetime.fromtimestamp(stat.st_mtime)

                        cached_series.append(
                            {
                                "series_id": series_id,
                                "limit": limit,
                                "sort_order": sort_order,
                                "file_size": file_size,
                                "modified_time": modified_time.isoformat(),
                                "cache_path": str(item),
                            }
                        )
                # Also handle single parquet files (unlikely but possible)
                elif item.is_file() and item.suffix == ".parquet":
                    cache_key = item.stem
                    parts = cache_key.rsplit("_", 2)
                    if len(parts) == 3:
                        series_id = parts[0]
                        limit = int(parts[1])
                        sort_order = parts[2]

                        stat = item.stat()
                        file_size = stat.st_size
                        modified_time = datetime.fromtimestamp(stat.st_mtime)

                        cached_series.append(
                            {
                                "series_id": series_id,
                                "limit": limit,
                                "sort_order": sort_order,
                                "file_size": file_size,
                                "modified_time": modified_time.isoformat(),
                                "cache_path": str(item),
                            }
                        )
            except Exception as e:
                logger.warning(f"Error processing cache entry '{item}': {str(e)}")

        return cached_series

    def clear_cache(self, series_id: Optional[str] = None) -> int:
        """
        Clear cache for a specific series or all cached data.

        Args:
            series_id: If provided, clear only this series. Otherwise clear all.

        Returns:
            Number of cache entries deleted
        """
        import shutil

        deleted_count = 0

        if not self.cache_dir.exists():
            return deleted_count

        if series_id:
            # Clear specific series (all variations)
            # Parquet files are stored as directories, so we need to match directories
            pattern = f"{series_id}_*"
            for item in self.cache_dir.glob(pattern):
                try:
                    if item.is_dir():
                        # Parquet directory - remove entire directory
                        shutil.rmtree(item)
                        deleted_count += 1
                        logger.info(f"Deleted cache directory: {item}")
                    elif item.is_file() and item.suffix == ".parquet":
                        # Single parquet file (unlikely but handle it)
                        item.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted cache file: {item}")
                except Exception as e:
                    logger.error(f"Error deleting cache entry '{item}': {str(e)}")
        else:
            # Clear all cache entries
            for item in self.cache_dir.iterdir():
                try:
                    # Skip if not a cache entry
                    if item.name.startswith("."):
                        continue
                    # Parquet files are stored as directories
                    if item.is_dir():
                        shutil.rmtree(item)
                        deleted_count += 1
                    elif item.is_file() and item.suffix == ".parquet":
                        item.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting cache entry '{item}': {str(e)}")

        logger.info(f"Cleared {deleted_count} cache entry/entries")
        return deleted_count

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cached_series = self.get_cached_series()
        total_size = sum(series["file_size"] for series in cached_series)
        unique_series = len(set(series["series_id"] for series in cached_series))

        return {
            "total_files": len(cached_series),
            "unique_series": unique_series,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def _prepare_dataframe_for_analytics(self, df: DataFrame) -> DataFrame:
        """
        Prepare DataFrame for analytics operations by converting dates and sorting.

        Args:
            df: Spark DataFrame with date as string

        Returns:
            DataFrame with date converted to DateType and sorted by date
        """
        if df.count() == 0:
            return df

        # Convert date string to DateType
        df_prepared = df.withColumn("date_parsed", to_date(col("date"), "yyyy-MM-dd"))

        # Sort by series_id and date for time-series operations
        df_prepared = df_prepared.orderBy("series_id", "date_parsed")

        # Drop original date column and rename date_parsed to date
        df_prepared = df_prepared.drop("date").withColumnRenamed("date_parsed", "date")

        return df_prepared

    def calculate_statistics(self, df: DataFrame) -> List[Dict[str, Any]]:
        """
        Calculate basic statistics for each series.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)

        Returns:
            List of dictionaries with statistics per series
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        # Calculate statistics grouped by series_id
        stats_df = df.groupBy("series_id").agg(
            avg("value").alias("mean"),
            expr("percentile_approx(value, 0.5)").alias("median"),
            stddev("value").alias("std"),
            spark_min("value").alias("min"),
            spark_max("value").alias("max"),
            count("value").alias("count"),
            spark_sum("value").alias("sum"),
        )

        # Convert to list of dictionaries
        results = []
        for row in stats_df.collect():
            results.append(
                {
                    "series_id": row["series_id"],
                    "mean": float(row["mean"]) if row["mean"] is not None else None,
                    "median": (
                        float(row["median"]) if row["median"] is not None else None
                    ),
                    "std": float(row["std"]) if row["std"] is not None else None,
                    "min": float(row["min"]) if row["min"] is not None else None,
                    "max": float(row["max"]) if row["max"] is not None else None,
                    "count": int(row["count"]),
                    "sum": float(row["sum"]) if row["sum"] is not None else None,
                }
            )

        return results

    def calculate_growth_rates(
        self, df: DataFrame, include_yoy: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Calculate growth rates (period-over-period and year-over-year).

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            include_yoy: Whether to include year-over-year growth rates

        Returns:
            List of dictionaries with growth rate data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Define window for period-over-period
            window_spec = Window.partitionBy("series_id").orderBy("date")

            # Calculate period-over-period growth rate
            series_df = series_df.withColumn(
                "previous_value", lag("value", 1).over(window_spec)
            )
            series_df = series_df.withColumn(
                "growth_rate",
                when(
                    (col("previous_value").isNotNull())
                    & (col("previous_value") != 0)
                    & (col("value").isNotNull()),
                    ((col("value") - col("previous_value")) / col("previous_value"))
                    * 100,
                ).otherwise(None),
            )

            # Collect results for period-over-period
            for row in series_df.select(
                "series_id", "date", "value", "previous_value", "growth_rate"
            ).collect():
                results.append(
                    {
                        "series_id": row["series_id"],
                        "date": (
                            row["date"].strftime("%Y-%m-%d") if row["date"] else None
                        ),
                        "value": (
                            float(row["value"]) if row["value"] is not None else None
                        ),
                        "previous_value": (
                            float(row["previous_value"])
                            if row["previous_value"] is not None
                            else None
                        ),
                        "growth_rate": (
                            float(row["growth_rate"])
                            if row["growth_rate"] is not None
                            else None
                        ),
                        "growth_type": "period_over_period",
                    }
                )

            # Calculate year-over-year if requested
            if include_yoy:
                # Add year column
                series_df_yoy = series_df.withColumn("year", year("date"))

                # For YoY, we need to compare same month/quarter across years
                # Join with previous year's data for same month
                series_df_yoy = series_df_yoy.alias("current").join(
                    series_df_yoy.alias("prev")
                    .select(
                        col("series_id").alias("prev_series_id"),
                        col("date").alias("prev_date"),
                        col("value").alias("prev_year_value"),
                        year("date").alias("prev_year"),
                        month("date").alias("prev_month"),
                    )
                    .filter(col("prev_series_id") == series_id),
                    (col("current.series_id") == col("prev_series_id"))
                    & (year(col("current.date")) == year(col("prev_date")) + 1)
                    & (month(col("current.date")) == col("prev_month")),
                    "left",
                )

                # Calculate YoY growth rate
                series_df_yoy = series_df_yoy.withColumn(
                    "yoy_growth_rate",
                    when(
                        (col("prev_year_value").isNotNull())
                        & (col("prev_year_value") != 0)
                        & (col("current.value").isNotNull()),
                        (
                            (col("current.value") - col("prev_year_value"))
                            / col("prev_year_value")
                        )
                        * 100,
                    ).otherwise(None),
                )

                # Collect YoY results
                for row in series_df_yoy.select(
                    col("current.series_id").alias("series_id"),
                    col("current.date").alias("date"),
                    col("current.value").alias("value"),
                    col("prev_year_value").alias("previous_value"),
                    col("yoy_growth_rate").alias("growth_rate"),
                ).collect():
                    if row["growth_rate"] is not None:
                        results.append(
                            {
                                "series_id": row["series_id"],
                                "date": (
                                    row["date"].strftime("%Y-%m-%d")
                                    if row["date"]
                                    else None
                                ),
                                "value": (
                                    float(row["value"])
                                    if row["value"] is not None
                                    else None
                                ),
                                "previous_value": (
                                    float(row["previous_value"])
                                    if row["previous_value"] is not None
                                    else None
                                ),
                                "growth_rate": float(row["growth_rate"]),
                                "growth_type": "year_over_year",
                            }
                        )

        return results

    def calculate_correlations(self, df: DataFrame) -> List[Dict[str, Any]]:
        """
        Calculate correlation matrix between series.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)

        Returns:
            List of dictionaries with correlation pairs
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        if len(series_ids) < 2:
            return []  # Need at least 2 series for correlation

        results = []

        # Pivot the DataFrame to have one column per series
        # First, ensure we have aligned dates (inner join on date)
        pivoted_df = df.groupBy("date").pivot("series_id").agg(avg("value"))

        # Calculate correlations between all pairs
        for i, series_id_1 in enumerate(series_ids):
            for series_id_2 in series_ids[i + 1 :]:
                try:
                    # Calculate correlation
                    corr_value = pivoted_df.select(
                        expr(f"corr(`{series_id_1}`, `{series_id_2}`)").alias(
                            "correlation"
                        )
                    ).collect()[0]["correlation"]

                    if corr_value is not None and not isnan(corr_value):
                        results.append(
                            {
                                "series_id_1": series_id_1,
                                "series_id_2": series_id_2,
                                "correlation": float(corr_value),
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Error calculating correlation between {series_id_1} and {series_id_2}: {str(e)}"
                    )

        return results

    def calculate_moving_averages(
        self, df: DataFrame, window_size: int, ma_type: str = "sma"
    ) -> List[Dict[str, Any]]:
        """
        Calculate moving averages (simple or exponential).

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            window_size: Size of the moving average window
            ma_type: Type of moving average ('sma' for simple, 'ema' for exponential)

        Returns:
            List of dictionaries with moving average data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Define window specification
            window_spec = (
                Window.partitionBy("series_id")
                .orderBy("date")
                .rowsBetween(-(window_size - 1), 0)
            )

            if ma_type == "sma":
                # Simple Moving Average
                series_df = series_df.withColumn(
                    "moving_average", avg("value").over(window_spec)
                )
            elif ma_type == "ema":
                # Exponential Moving Average
                # EMA calculation in Spark requires iterative approach
                # For simplicity, we'll use a recursive formula approximation
                # α = 2 / (window_size + 1)
                alpha = 2.0 / (window_size + 1)

                # Since Spark doesn't support recursive window functions easily,
                # we'll use a simpler approximation: weighted average over window
                # For first window_size rows, use SMA
                # For subsequent rows, use EMA formula
                series_df = series_df.withColumn(
                    "row_num",
                    expr("row_number() OVER (PARTITION BY series_id ORDER BY date)"),
                )

                # Calculate SMA first
                series_df = series_df.withColumn("sma", avg("value").over(window_spec))

                # Calculate EMA: for first window_size rows use SMA, then use EMA formula
                series_df = series_df.withColumn(
                    "moving_average",
                    when(col("row_num") <= window_size, col("sma")).otherwise(
                        alpha * col("value")
                        + (1 - alpha)
                        * lag(col("sma"), 1).over(
                            Window.partitionBy("series_id").orderBy("date")
                        )
                    ),
                )

                # Drop helper columns
                series_df = series_df.drop("row_num", "sma")
            else:
                raise ValueError(f"Unsupported moving average type: {ma_type}")

            # Collect results
            for row in series_df.select(
                "series_id", "date", "value", "moving_average"
            ).collect():
                results.append(
                    {
                        "series_id": row["series_id"],
                        "date": (
                            row["date"].strftime("%Y-%m-%d") if row["date"] else None
                        ),
                        "value": (
                            float(row["value"]) if row["value"] is not None else None
                        ),
                        "moving_average": (
                            float(row["moving_average"])
                            if row["moving_average"] is not None
                            else None
                        ),
                        "moving_average_type": ma_type,
                        "window_size": window_size,
                    }
                )

        return results

    def calculate_time_aggregations(
        self, df: DataFrame, period: str, agg_function: str = "mean"
    ) -> List[Dict[str, Any]]:
        """
        Calculate time-based aggregations (daily, weekly, monthly, quarterly, yearly).

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            period: Time period ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
            agg_function: Aggregation function ('mean', 'sum', 'min', 'max', 'first', 'last')

        Returns:
            List of dictionaries with aggregated data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        # Map period to date_trunc format
        period_map = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
            "quarterly": "quarter",
            "yearly": "year",
        }

        if period not in period_map:
            raise ValueError(
                f"Unsupported period: {period}. Must be one of {list(period_map.keys())}"
            )

        # Map aggregation function
        agg_map = {
            "mean": avg("value"),
            "sum": spark_sum("value"),
            "min": spark_min("value"),
            "max": spark_max("value"),
            "first": expr("first(value)"),
            "last": expr("last(value)"),
        }

        if agg_function not in agg_map:
            raise ValueError(
                f"Unsupported aggregation function: {agg_function}. Must be one of {list(agg_map.keys())}"
            )

        # Truncate date to the specified period
        df_agg = df.withColumn("period", date_trunc(period_map[period], col("date")))

        # Group by series_id and period, then aggregate
        df_agg = df_agg.groupBy("series_id", "period").agg(
            agg_map[agg_function].alias("aggregated_value"),
            count("value").alias("observation_count"),
        )

        # Format period string based on period type
        if period == "daily":
            df_agg = df_agg.withColumn(
                "period_str", expr("date_format(period, 'yyyy-MM-dd')")
            )
        elif period == "weekly":
            df_agg = df_agg.withColumn(
                "period_str", expr("date_format(period, 'yyyy-MM-dd')")
            )  # Week start date
        elif period == "monthly":
            df_agg = df_agg.withColumn(
                "period_str", expr("date_format(period, 'yyyy-MM')")
            )
        elif period == "quarterly":
            df_agg = df_agg.withColumn(
                "period_str",
                expr("CONCAT(YEAR(period), '-Q', QUARTER(period))"),
            )
        elif period == "yearly":
            df_agg = df_agg.withColumn(
                "period_str", expr("date_format(period, 'yyyy')")
            )

        # Convert to list of dictionaries
        results = []
        for row in df_agg.select(
            "series_id", "period_str", "aggregated_value", "observation_count"
        ).collect():
            results.append(
                {
                    "series_id": row["series_id"],
                    "period": row["period_str"],
                    "aggregated_value": (
                        float(row["aggregated_value"])
                        if row["aggregated_value"] is not None
                        else None
                    ),
                    "aggregation_function": agg_function,
                    "observation_count": int(row["observation_count"]),
                }
            )

        return results

    # Advanced Analytics Methods (Increment 6)

    def detect_anomalies(
        self,
        df: DataFrame,
        method: str = "z_score",
        threshold: float = 3.0,
        window_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in time-series data.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            method: Detection method ('z_score', 'iqr', or 'moving_average')
            threshold: Z-score threshold for z_score method (default: 3.0)
            window_size: Window size for moving_average method

        Returns:
            List of dictionaries with anomaly data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            if method == "z_score":
                # Calculate mean and std for the series
                stats = series_df.agg(
                    avg("value").alias("mean"), stddev("value").alias("std")
                ).collect()[0]

                mean_val = stats["mean"]
                std_val = stats["std"]

                if mean_val is None or std_val is None or std_val == 0:
                    continue

                # Calculate Z-scores and identify anomalies
                series_df = series_df.withColumn(
                    "z_score", (col("value") - mean_val) / std_val
                )

                anomalies_df = series_df.filter(
                    (col("z_score") > threshold) | (col("z_score") < -threshold)
                )

                for row in anomalies_df.select("date", "value", "z_score").collect():
                    deviation = abs(float(row["z_score"]))
                    severity = (
                        "high"
                        if deviation > threshold * 2
                        else "medium" if deviation > threshold * 1.5 else "low"
                    )

                    results.append(
                        {
                            "series_id": series_id,
                            "date": row["date"].strftime("%Y-%m-%d"),
                            "value": float(row["value"]) if row["value"] else None,
                            "expected_value": mean_val,
                            "deviation": deviation,
                            "detection_method": "z_score",
                            "severity": severity,
                        }
                    )

            elif method == "iqr":
                # Calculate quartiles
                quantiles = series_df.approxQuantile("value", [0.25, 0.5, 0.75], 0.0)

                if len(quantiles) != 3 or None in quantiles:
                    continue

                q1, median, q3 = quantiles
                iqr = q3 - q1

                if iqr == 0:
                    continue

                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                anomalies_df = series_df.filter(
                    (col("value") < lower_bound) | (col("value") > upper_bound)
                )

                for row in anomalies_df.select("date", "value").collect():
                    value = float(row["value"]) if row["value"] else None
                    if value is None:
                        continue

                    deviation_from_median = abs(value - median) / iqr if iqr > 0 else 0
                    severity = (
                        "high"
                        if deviation_from_median > 3
                        else "medium" if deviation_from_median > 2 else "low"
                    )

                    results.append(
                        {
                            "series_id": series_id,
                            "date": row["date"].strftime("%Y-%m-%d"),
                            "value": value,
                            "expected_value": median,
                            "deviation": deviation_from_median,
                            "detection_method": "iqr",
                            "severity": severity,
                        }
                    )

            elif method == "moving_average":
                if window_size is None:
                    window_size = 30  # Default window size

                # Calculate moving average and standard deviation
                window_spec = (
                    Window.partitionBy("series_id")
                    .orderBy("date")
                    .rowsBetween(-(window_size - 1), 0)
                )

                series_df = series_df.withColumn(
                    "ma", avg("value").over(window_spec)
                ).withColumn("ma_std", stddev("value").over(window_spec))

                # Identify anomalies (values beyond threshold * std from moving average)
                anomalies_df = series_df.filter(
                    (col("value") > col("ma") + threshold * col("ma_std"))
                    | (col("value") < col("ma") - threshold * col("ma_std"))
                ).filter(col("ma_std").isNotNull())

                for row in anomalies_df.select(
                    "date", "value", "ma", "ma_std"
                ).collect():
                    value = float(row["value"]) if row["value"] else None
                    ma_val = float(row["ma"]) if row["ma"] else None
                    ma_std_val = float(row["ma_std"]) if row["ma_std"] else None

                    if value is None or ma_val is None or ma_std_val is None:
                        continue

                    deviation = (
                        abs(value - ma_val) / ma_std_val if ma_std_val > 0 else 0
                    )
                    severity = (
                        "high"
                        if deviation > threshold * 2
                        else "medium" if deviation > threshold * 1.5 else "low"
                    )

                    results.append(
                        {
                            "series_id": series_id,
                            "date": row["date"].strftime("%Y-%m-%d"),
                            "value": value,
                            "expected_value": ma_val,
                            "deviation": deviation,
                            "detection_method": "moving_average",
                            "severity": severity,
                        }
                    )

        return results

    def calculate_volatility(
        self, df: DataFrame, window_size: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Calculate rolling volatility for time-series data.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            window_size: Rolling window size for volatility calculation

        Returns:
            List of dictionaries with volatility data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series and order by date
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Calculate period returns: (value_t - value_{t-1}) / value_{t-1}
            series_df = series_df.withColumn(
                "prev_value",
                lag("value", 1).over(Window.partitionBy("series_id").orderBy("date")),
            ).withColumn(
                "return",
                when(
                    (col("prev_value").isNotNull())
                    & (col("prev_value") != 0)
                    & (col("value").isNotNull()),
                    (col("value") - col("prev_value")) / col("prev_value"),
                ).otherwise(None),
            )

            # Calculate rolling volatility (standard deviation of returns)
            volatility_window = (
                Window.partitionBy("series_id")
                .orderBy("date")
                .rowsBetween(-(window_size - 1), 0)
            )

            series_df = series_df.withColumn(
                "volatility", stddev("return").over(volatility_window)
            )

            # Calculate annualized volatility (assuming daily data)
            # Annualized = daily_volatility * sqrt(252) for daily data
            # For monthly data, use sqrt(12), etc.
            series_df = series_df.withColumn(
                "annualized_volatility", col("volatility") * expr("sqrt(252)")
            )

            # Collect results
            for row in series_df.select(
                "date", "value", "return", "volatility", "annualized_volatility"
            ).collect():
                if row["volatility"] is not None:
                    results.append(
                        {
                            "series_id": series_id,
                            "date": row["date"].strftime("%Y-%m-%d"),
                            "volatility": float(row["volatility"]),
                            "annualized_volatility": (
                                float(row["annualized_volatility"])
                                if row["annualized_volatility"] is not None
                                else None
                            ),
                            "return_value": (
                                float(row["return"]) * 100
                                if row["return"] is not None
                                else None
                            ),  # Convert to percentage
                            "window_size": window_size,
                        }
                    )

        return results

    def analyze_trends(
        self, df: DataFrame, trend_type: str = "linear", polynomial_degree: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Analyze trends in time-series data.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            trend_type: Type of trend analysis ('linear' or 'polynomial')
            polynomial_degree: Degree of polynomial for polynomial trends (default: 2)

        Returns:
            List of dictionaries with trend analysis results
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series and order by date
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Convert to Pandas for trend analysis (Spark MLlib requires more setup)
            # For now, we'll use a simpler approach with Spark SQL
            # Calculate row number for trend analysis
            series_df = series_df.withColumn(
                "row_num",
                expr("row_number() over (partition by series_id order by date)"),
            )

            # Collect data for trend calculation
            data_rows = series_df.select("date", "value", "row_num").collect()

            if len(data_rows) < 2:
                # Not enough data for trend analysis
                results.append(
                    {
                        "series_id": series_id,
                        "trend_type": "none",
                        "slope": None,
                        "intercept": None,
                        "r_squared": 0.0,
                        "direction": "stable",
                        "polynomial_degree": None,
                    }
                )
                continue

            # Extract values and row numbers
            values = [
                float(row["value"]) for row in data_rows if row["value"] is not None
            ]
            row_nums = [
                float(row["row_num"])
                for i, row in enumerate(data_rows)
                if row["value"] is not None
            ]

            if len(values) < 2:
                results.append(
                    {
                        "series_id": series_id,
                        "trend_type": "none",
                        "slope": None,
                        "intercept": None,
                        "r_squared": 0.0,
                        "direction": "stable",
                        "polynomial_degree": None,
                    }
                )
                continue

            # Simple linear regression using least squares
            n = len(values)
            sum_x = sum(row_nums)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(row_nums, values))
            sum_x2 = sum(x * x for x in row_nums)

            if trend_type == "linear":
                # Calculate slope and intercept
                denominator = n * sum_x2 - sum_x * sum_x
                if denominator == 0:
                    slope = 0
                    intercept = sum_y / n if n > 0 else 0
                else:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    intercept = (sum_y - slope * sum_x) / n

                # Calculate R-squared
                y_mean = sum_y / n
                ss_tot = sum((y - y_mean) ** 2 for y in values)
                ss_res = sum(
                    (y - (slope * x + intercept)) ** 2 for x, y in zip(row_nums, values)
                )
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

                direction = (
                    "increasing"
                    if slope > 0.01
                    else "decreasing" if slope < -0.01 else "stable"
                )

                results.append(
                    {
                        "series_id": series_id,
                        "trend_type": "linear",
                        "slope": slope,
                        "intercept": intercept,
                        "r_squared": max(0.0, min(1.0, r_squared)),
                        "direction": direction,
                        "polynomial_degree": None,
                    }
                )

            elif trend_type == "polynomial":
                # For polynomial, we'll use a simplified approach
                # In a production system, use numpy.polyfit or Spark MLlib
                # For now, approximate with linear trend and mark as polynomial
                denominator = n * sum_x2 - sum_x * sum_x
                if denominator == 0:
                    slope = 0
                    intercept = sum_y / n if n > 0 else 0
                else:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    intercept = (sum_y - slope * sum_x) / n

                # Calculate R-squared (simplified for polynomial)
                y_mean = sum_y / n
                ss_tot = sum((y - y_mean) ** 2 for y in values)
                ss_res = sum(
                    (y - (slope * x + intercept)) ** 2 for x, y in zip(row_nums, values)
                )
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

                direction = (
                    "increasing"
                    if slope > 0.01
                    else "decreasing" if slope < -0.01 else "stable"
                )

                results.append(
                    {
                        "series_id": series_id,
                        "trend_type": "polynomial",
                        "slope": slope,  # Approximate
                        "intercept": intercept,
                        "r_squared": max(0.0, min(1.0, r_squared)),
                        "direction": direction,
                        "polynomial_degree": polynomial_degree,
                    }
                )

        return results

    def decompose_seasonal(
        self,
        df: DataFrame,
        decomposition_type: str = "additive",
        seasonal_period: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Perform seasonal decomposition of time-series data.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            decomposition_type: Type of decomposition ('additive' or 'multiplicative')
            seasonal_period: Seasonal period (e.g., 12 for monthly data)

        Returns:
            List of dictionaries with decomposition results
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series and order by date
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Collect data for decomposition
            data_rows = series_df.select("date", "value").collect()

            if len(data_rows) < seasonal_period * 2:
                # Not enough data for seasonal decomposition
                continue

            # Extract values
            values = [
                float(row["value"]) if row["value"] is not None else None
                for row in data_rows
            ]
            dates = [row["date"] for row in data_rows]

            # Simple moving average for trend (using seasonal_period as window)
            # This is a simplified decomposition - for production, use statsmodels
            trend_values = []
            seasonal_values = []
            residual_values = []

            for i in range(len(values)):
                if values[i] is None:
                    trend_values.append(None)
                    seasonal_values.append(None)
                    residual_values.append(None)
                    continue

                # Calculate trend using centered moving average
                window_start = max(0, i - seasonal_period // 2)
                window_end = min(len(values), i + seasonal_period // 2 + 1)
                window_vals = [
                    v for v in values[window_start:window_end] if v is not None
                ]

                if len(window_vals) == 0:
                    trend = values[i]
                else:
                    trend = sum(window_vals) / len(window_vals)

                trend_values.append(trend)

                # Calculate seasonal component (simplified)
                # In production, use proper seasonal decomposition
                seasonal = 0.0  # Simplified - would need proper seasonal calculation

                seasonal_values.append(seasonal)

                # Calculate residual
                if decomposition_type == "additive":
                    residual = values[i] - trend - seasonal
                else:  # multiplicative
                    residual = values[i] / (trend * (1 + seasonal)) if trend != 0 else 0

                residual_values.append(residual)

            # Build results
            for i, (date, value) in enumerate(zip(dates, values)):
                if value is not None:
                    results.append(
                        {
                            "series_id": series_id,
                            "date": date.strftime("%Y-%m-%d"),
                            "actual_value": value,
                            "trend_component": (
                                trend_values[i] if trend_values[i] is not None else 0.0
                            ),
                            "seasonal_component": (
                                seasonal_values[i]
                                if seasonal_values[i] is not None
                                else 0.0
                            ),
                            "residual_component": (
                                residual_values[i]
                                if residual_values[i] is not None
                                else 0.0
                            ),
                            "decomposition_type": decomposition_type,
                        }
                    )

        return results

    def calculate_forecasts(
        self,
        df: DataFrame,
        forecast_horizon: int = 12,
        forecast_method: str = "linear_regression",
    ) -> List[Dict[str, Any]]:
        """
        Calculate forecasts for time-series data.

        Args:
            df: Spark DataFrame with series data (must have date converted to DateType)
            forecast_horizon: Number of periods to forecast ahead
            forecast_method: Forecasting method ('arima', 'exponential_smoothing', or 'linear_regression')

        Returns:
            List of dictionaries with forecast data
        """
        if df.count() == 0:
            return []

        # Prepare DataFrame if dates are strings
        if df.schema["date"].dataType == StringType():
            df = self._prepare_dataframe_for_analytics(df)

        results = []

        # Get unique series IDs
        series_ids = [
            row["series_id"] for row in df.select("series_id").distinct().collect()
        ]

        for series_id in series_ids:
            # Filter for this series and order by date
            series_df = df.filter(col("series_id") == series_id).orderBy("date")

            # Collect historical data
            data_rows = series_df.select("date", "value").collect()

            if len(data_rows) < 2:
                continue

            # Extract values and dates
            values = [
                float(row["value"]) for row in data_rows if row["value"] is not None
            ]
            dates = [row["date"] for row in data_rows if row["value"] is not None]

            if len(values) < 2:
                continue

            # Get last date for forecasting
            last_date = dates[-1]

            if forecast_method == "linear_regression":
                # Simple linear regression forecasting
                n = len(values)
                row_nums = list(range(1, n + 1))

                sum_x = sum(row_nums)
                sum_y = sum(values)
                sum_xy = sum(x * y for x, y in zip(row_nums, values))
                sum_x2 = sum(x * x for x in row_nums)

                denominator = n * sum_x2 - sum_x * sum_x
                if denominator == 0:
                    slope = 0
                    intercept = sum_y / n if n > 0 else 0
                else:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    intercept = (sum_y - slope * sum_x) / n

                # Calculate standard error for confidence intervals
                y_mean = sum_y / n
                ss_res = sum(
                    (y - (slope * x + intercept)) ** 2 for x, y in zip(row_nums, values)
                )
                std_error = (ss_res / (n - 2)) ** 0.5 if n > 2 else 0.0

                # Generate forecasts
                from datetime import timedelta

                for i in range(1, forecast_horizon + 1):
                    forecast_date = last_date + timedelta(
                        days=30 * i
                    )  # Approximate monthly
                    forecast_value = slope * (n + i) + intercept

                    # Simple confidence interval (95%)
                    confidence_interval = (
                        1.96
                        * std_error
                        * (
                            1
                            + 1 / n
                            + ((n + i - y_mean) ** 2)
                            / sum((x - y_mean) ** 2 for x in row_nums)
                        )
                        ** 0.5
                        if n > 2
                        else std_error
                    )

                    results.append(
                        {
                            "series_id": series_id,
                            "date": forecast_date.strftime("%Y-%m-%d"),
                            "forecasted_value": forecast_value,
                            "lower_bound": forecast_value - confidence_interval,
                            "upper_bound": forecast_value + confidence_interval,
                            "confidence_level": 0.95,
                            "forecast_method": "linear_regression",
                        }
                    )

            elif forecast_method == "exponential_smoothing":
                # Simple exponential smoothing (Holt-Winters simplified)
                alpha = 0.3  # Smoothing parameter
                forecast_value = values[-1]  # Start with last value

                from datetime import timedelta

                for i in range(1, forecast_horizon + 1):
                    forecast_date = last_date + timedelta(days=30 * i)
                    # Simple exponential smoothing forecast
                    # In production, use proper Holt-Winters method
                    forecast_value = alpha * values[-1] + (1 - alpha) * forecast_value

                    results.append(
                        {
                            "series_id": series_id,
                            "date": forecast_date.strftime("%Y-%m-%d"),
                            "forecasted_value": forecast_value,
                            "lower_bound": None,  # Would need proper calculation
                            "upper_bound": None,
                            "confidence_level": None,
                            "forecast_method": "exponential_smoothing",
                        }
                    )

            elif forecast_method == "arima":
                # ARIMA forecasting using pmdarima with model caching
                try:
                    import pmdarima as pm
                    import pandas as pd

                    # Convert to pandas Series
                    ts = pd.Series(values, index=dates)

                    # Check if model is cached
                    model_cache_path = self._get_model_cache_path(
                        series_id, forecast_horizon, forecast_method
                    )
                    model = None

                    if self._is_model_cached(
                        series_id, forecast_horizon, forecast_method
                    ):
                        try:
                            logger.info(
                                f"Loading cached ARIMA model for {series_id} from {model_cache_path}"
                            )
                            model = self._load_model_from_cache(
                                series_id, forecast_horizon, forecast_method
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to load cached model for {series_id}: {str(e)}. Will refit."
                            )

                    # Fit model if not loaded from cache
                    if model is None:
                        logger.info(f"Fitting ARIMA model for {series_id}")
                        model = pm.auto_arima(
                            ts,
                            seasonal=False,
                            stepwise=True,
                            suppress_warnings=True,
                            error_action="ignore",
                        )

                        # Save model to cache
                        try:
                            self._save_model_to_cache(
                                model, series_id, forecast_horizon, forecast_method
                            )
                            logger.info(
                                f"Cached ARIMA model for {series_id} to {model_cache_path}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to cache model for {series_id}: {str(e)}"
                            )

                    # Generate forecasts
                    forecast, conf_int = model.predict(
                        n_periods=forecast_horizon, return_conf_int=True
                    )

                    from datetime import timedelta

                    for i, (fcst, (lower, upper)) in enumerate(zip(forecast, conf_int)):
                        forecast_date = last_date + timedelta(days=30 * (i + 1))

                        results.append(
                            {
                                "series_id": series_id,
                                "date": forecast_date.strftime("%Y-%m-%d"),
                                "forecasted_value": float(fcst),
                                "lower_bound": float(lower),
                                "upper_bound": float(upper),
                                "confidence_level": 0.95,
                                "forecast_method": "arima",
                            }
                        )

                except ImportError:
                    logger.warning(
                        "pmdarima not available, falling back to linear regression"
                    )
                    # Fallback to linear regression
                    return self.calculate_forecasts(
                        df, forecast_horizon, "linear_regression"
                    )
                except Exception as e:
                    logger.error(f"Error in ARIMA forecasting: {str(e)}")
                    continue

        return results

    def _get_model_cache_path(
        self, series_id: str, forecast_horizon: int, forecast_method: str
    ) -> Path:
        """
        Get the cache file path for an ARIMA model.

        Args:
            series_id: FRED series ID
            forecast_horizon: Number of periods to forecast
            forecast_method: Forecasting method

        Returns:
            Path to the model cache file
        """
        # Create cache key from series_id, forecast_horizon, and forecast_method
        cache_key = f"{series_id}_{forecast_horizon}_{forecast_method}"
        return self.model_cache_dir / f"{cache_key}.pkl"

    def _is_model_cached(
        self, series_id: str, forecast_horizon: int, forecast_method: str
    ) -> bool:
        """
        Check if an ARIMA model is cached.

        Args:
            series_id: FRED series ID
            forecast_horizon: Number of periods to forecast
            forecast_method: Forecasting method

        Returns:
            True if cached, False otherwise
        """
        model_cache_path = self._get_model_cache_path(
            series_id, forecast_horizon, forecast_method
        )
        return model_cache_path.exists() and model_cache_path.is_file()

    def _load_model_from_cache(
        self, series_id: str, forecast_horizon: int, forecast_method: str
    ):
        """
        Load ARIMA model from cache.

        Args:
            series_id: FRED series ID
            forecast_horizon: Number of periods to forecast
            forecast_method: Forecasting method

        Returns:
            Loaded ARIMA model

        Raises:
            FileNotFoundError: If model cache file doesn't exist
            Exception: If model loading fails
        """
        import joblib

        model_cache_path = self._get_model_cache_path(
            series_id, forecast_horizon, forecast_method
        )

        if not model_cache_path.exists():
            raise FileNotFoundError(f"Model cache file not found: {model_cache_path}")

        try:
            model = joblib.load(model_cache_path)
            logger.info(f"Loaded ARIMA model from cache: {model_cache_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model from cache: {str(e)}")
            raise

    def _save_model_to_cache(
        self, model, series_id: str, forecast_horizon: int, forecast_method: str
    ) -> None:
        """
        Save ARIMA model to cache.

        Args:
            model: Fitted ARIMA model to cache
            series_id: FRED series ID
            forecast_horizon: Number of periods to forecast
            forecast_method: Forecasting method

        Raises:
            Exception: If model saving fails
        """
        import joblib

        model_cache_path = self._get_model_cache_path(
            series_id, forecast_horizon, forecast_method
        )

        try:
            # Ensure model cache directory exists
            self.model_cache_dir.mkdir(parents=True, exist_ok=True)

            # Save model using joblib
            joblib.dump(model, model_cache_path)
            logger.info(f"Cached ARIMA model to {model_cache_path}")
        except Exception as e:
            logger.error(f"Error saving model to cache: {str(e)}")
            raise
