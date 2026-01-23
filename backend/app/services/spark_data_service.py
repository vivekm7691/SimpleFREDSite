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
    DateType,
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
    window,
    date_trunc,
    year,
    quarter,
    month,
    when,
    isnan,
    isnull,
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
                    "median": float(row["median"]) if row["median"] is not None else None,
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
        series_ids = [row["series_id"] for row in df.select("series_id").distinct().collect()]

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
                    ((col("value") - col("previous_value")) / col("previous_value")) * 100,
                ).otherwise(None),
            )

            # Collect results for period-over-period
            for row in series_df.select(
                "series_id", "date", "value", "previous_value", "growth_rate"
            ).collect():
                results.append(
                    {
                        "series_id": row["series_id"],
                        "date": row["date"].strftime("%Y-%m-%d") if row["date"] else None,
                        "value": float(row["value"]) if row["value"] is not None else None,
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
                        ((col("current.value") - col("prev_year_value")) / col("prev_year_value"))
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
                                "date": row["date"].strftime("%Y-%m-%d") if row["date"] else None,
                                "value": float(row["value"]) if row["value"] is not None else None,
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
        series_ids = [row["series_id"] for row in df.select("series_id").distinct().collect()]

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
                        expr(f"corr(`{series_id_1}`, `{series_id_2}`)").alias("correlation")
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
        series_ids = [row["series_id"] for row in df.select("series_id").distinct().collect()]

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
                        * lag(col("sma"), 1).over(Window.partitionBy("series_id").orderBy("date"))
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
                        "date": row["date"].strftime("%Y-%m-%d") if row["date"] else None,
                        "value": float(row["value"]) if row["value"] is not None else None,
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
            df_agg = df_agg.withColumn("period_str", expr("date_format(period, 'yyyy-MM')"))
        elif period == "quarterly":
            df_agg = df_agg.withColumn(
                "period_str",
                expr("CONCAT(YEAR(period), '-Q', QUARTER(period))"),
            )
        elif period == "yearly":
            df_agg = df_agg.withColumn("period_str", expr("date_format(period, 'yyyy')"))

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
