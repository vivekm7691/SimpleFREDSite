"""
Spark data service for batch processing FRED series data.
"""

import logging
from typing import List
import asyncio
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)

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

    async def batch_fetch_series(
        self, series_ids: List[str], limit: int = 100, sort_order: str = "desc"
    ) -> List[FREDDataResponse]:
        """
        Fetch multiple FRED series in parallel.

        Args:
            series_ids: List of FRED series IDs to fetch
            limit: Maximum number of observations per series
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of FREDDataResponse objects, one per series

        Raises:
            ValueError: If series_ids is empty
        """
        if not series_ids:
            raise ValueError("series_ids cannot be empty")

        logger.info(f"Batch fetching {len(series_ids)} series: {series_ids}")

        # Fetch all series in parallel using asyncio
        tasks = [
            self.fred_service.fetch_series(
                series_id=series_id, limit=limit, sort_order=sort_order
            )
            for series_id in series_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle errors
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    f"Failed to fetch series '{series_ids[i]}': {str(result)}"
                )
                # Create a placeholder response for failed series
                from app.models.schemas import FREDSeriesInfo

                responses.append(
                    FREDDataResponse(
                        series_id=series_ids[i],
                        series_info=FREDSeriesInfo(
                            id=series_ids[i],
                            title=series_ids[i],
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
