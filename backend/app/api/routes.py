"""
API routes for FRED data and summarization.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from app.models.schemas import (
    FREDFetchRequest,
    FREDDataResponse,
    SummarizeRequest,
    SummarizeResponse,
    CategoryResponse,
    CategorySeriesResponse,
    BatchFetchRequest,
    BatchFetchResponse,
    CacheStatsResponse,
    CacheListResponse,
    AnalyticsRequest,
    AnalyticsResponse,
)
from app.services.fred_service import get_fred_service
from app.services.category_service import get_category_service
from app.services.spark_service import get_spark_service
from app.services.spark_data_service import SparkDataService

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/fred/fetch", response_model=FREDDataResponse)
async def fetch_fred_data(request: FREDFetchRequest):
    """
    Fetch economic data from FRED by series ID.

    Args:
        request: FREDFetchRequest with series_id

    Returns:
        FREDDataResponse with series data and observations

    Raises:
        HTTPException: If FRED API request fails or series not found
    """
    try:
        fred_service = get_fred_service()
        data = await fred_service.fetch_series(request.series_id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching FRED data: {str(e)}",
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_data(request: SummarizeRequest):
    """
    Summarize data using Google Gemini API.

    Args:
        request: SummarizeRequest with data to summarize

    Returns:
        SummarizeResponse with generated summary

    Raises:
        HTTPException: If Gemini API request fails or summary cannot be generated
    """
    logger.info("=== /api/summarize endpoint called ===")
    logger.info(
        f"Request data keys: {list(request.data.keys()) if isinstance(request.data, dict) else 'N/A'}"
    )

    # Declare api_key and gemini_service at function scope so they're available in exception handler
    api_key = None
    gemini_service = None

    try:
        # Force reload environment variables and get the API key directly
        import os
        from pathlib import Path
        from dotenv import load_dotenv

        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)

        # Get the API key directly from environment after reload
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY not found in environment",
            )

        api_key = api_key.strip()

        # Verify the key format
        if not api_key.startswith("AIza"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid API key format. Expected to start with 'AIza', got: {api_key[:10]}...",
            )

        logger.info(
            f"Using API Key: {api_key[:10]}...{api_key[-5:]} (length: {len(api_key)})"
        )

        # Create a NEW service instance with the API key directly
        # This bypasses any singleton caching
        from app.services.gemini_service import GeminiService

        # Create service with the API key
        gemini_service = GeminiService(api_key=api_key)

        logger.info(f"Using Gemini service with model: {gemini_service.model_name}")
        logger.info("Calling summarize_data...")
        summary = await gemini_service.summarize_data(request.data)
        logger.info(f"Summary generated successfully (length: {len(summary)})")
        return SummarizeResponse(summary=summary)
    except ValueError as e:
        logger.error(f"ValueError in summarize_data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Exception in summarize_data: {type(e).__name__}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}",
        )


@router.get("/categories", response_model=CategoryResponse)
async def get_categories():
    """
    Get all available categories with series counts.

    Returns:
        CategoryResponse with list of all categories

    Raises:
        HTTPException: If categories cannot be retrieved
    """
    try:
        category_service = get_category_service()
        categories = category_service.get_all_categories()
        return CategoryResponse(categories=categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching categories: {str(e)}",
        )


@router.get("/categories/{category_id}", response_model=CategorySeriesResponse)
async def get_category_series(
    category_id: str,
    q: Optional[str] = Query(None, description="Search term to filter series"),
):
    """
    Get series list for a specific category, optionally filtered by search term.

    Args:
        category_id: Category identifier (e.g., 'employment', 'inflation')
        q: Optional search term to filter series within the category

    Returns:
        CategorySeriesResponse with series list for the category

    Raises:
        HTTPException: If category not found or series cannot be retrieved
    """
    try:
        category_service = get_category_service()
        fred_service = get_fred_service()

        # Get series for category with optional search filter
        response = await category_service.get_category_series(
            category_id=category_id,
            search_term=q,
            fred_service=fred_service,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error fetching series for category '{category_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching category series: {str(e)}",
        )


@router.get("/spark/health")
async def spark_health_check():
    """
    Health check endpoint to verify Spark connectivity and availability.

    Returns:
        JSON response with Spark status and version information

    Raises:
        HTTPException: If Spark is not available
    """
    try:
        spark_service = get_spark_service()
        is_available = spark_service.is_available()

        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        spark = spark_service.spark
        version = spark.version

        return {
            "status": "healthy",
            "service": "Spark",
            "version": version,
            "available": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking Spark health: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking Spark health: {str(e)}",
        )


@router.post("/spark/batch-fetch", response_model=BatchFetchResponse)
async def batch_fetch_series(request: BatchFetchRequest):
    """
    Batch fetch multiple FRED series and process them using Spark.

    Fetches multiple series in parallel, converts them to Spark DataFrames,
    and returns combined results.

    Args:
        request: BatchFetchRequest with list of series IDs and options

    Returns:
        BatchFetchResponse with combined data from all series

    Raises:
        HTTPException: If batch processing fails
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        logger.info(
            f"Batch fetching {len(request.series_ids)} series: {request.series_ids}"
        )

        # Fetch all series in parallel (with caching if enabled)
        fred_responses = await spark_data_service.batch_fetch_series(
            series_ids=request.series_ids,
            limit=request.limit,
            sort_order=request.sort_order,
            use_cache=request.use_cache,
        )

        # Convert to DataFrame
        df = spark_data_service.convert_to_dataframe(fred_responses)

        # Aggregate data
        aggregated_df = spark_data_service.aggregate_series_data(
            df, aggregation_type=request.aggregation_type
        )

        # Convert to dictionary for JSON response
        data_dict = spark_data_service.dataframe_to_dict(aggregated_df)

        # Prepare series info
        series_info = []
        for response in fred_responses:
            series_info.append(
                {
                    "series_id": response.series_id,
                    "title": response.series_info.title,
                    "units": response.series_info.units,
                    "frequency": response.series_info.frequency,
                    "observation_count": response.observation_count,
                }
            )

        return BatchFetchResponse(
            series_count=len(request.series_ids),
            total_observations=data_dict["row_count"],
            columns=data_dict["columns"],
            data=data_dict["data"],
            series_info=series_info,
        )

    except ValueError as e:
        logger.error(f"ValueError in batch_fetch_series: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in batch_fetch_series: {type(e).__name__}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch fetch: {str(e)}",
        )


@router.get("/spark/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get cache statistics.

    Returns:
        CacheStatsResponse with cache statistics

    Raises:
        HTTPException: If cache stats cannot be retrieved
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        stats = spark_data_service.get_cache_stats()

        return CacheStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache stats: {str(e)}",
        )


@router.get("/spark/cache/list", response_model=CacheListResponse)
async def list_cached_series():
    """
    List all cached series.

    Returns:
        CacheListResponse with list of cached series

    Raises:
        HTTPException: If cache list cannot be retrieved
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        cached_series = spark_data_service.get_cached_series()

        return CacheListResponse(entries=cached_series, total_count=len(cached_series))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing cached series: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing cached series: {str(e)}",
        )


@router.delete("/spark/cache/clear")
async def clear_cache(
    series_id: Optional[str] = Query(
        None, description="Series ID to clear (optional, clears all if not provided)"
    )
):
    """
    Clear cache for a specific series or all cached data.

    Args:
        series_id: Optional series ID to clear. If not provided, clears all cache.

    Returns:
        JSON response with number of files deleted

    Raises:
        HTTPException: If cache cannot be cleared
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        # Normalize series_id if provided
        if series_id:
            series_id = series_id.strip().upper()

        deleted_count = spark_data_service.clear_cache(series_id=series_id)

        return {
            "message": f"Cleared {deleted_count} cache file(s)",
            "deleted_count": deleted_count,
            "series_id": series_id if series_id else "all",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}",
        )


@router.delete("/spark/cache/{series_id}")
async def clear_series_cache(series_id: str):
    """
    Clear cache for a specific series.

    Args:
        series_id: Series ID to clear from cache

    Returns:
        JSON response with number of files deleted

    Raises:
        HTTPException: If cache cannot be cleared
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        # Normalize series_id
        series_id = series_id.strip().upper()

        deleted_count = spark_data_service.clear_cache(series_id=series_id)

        return {
            "message": f"Cleared {deleted_count} cache file(s) for series '{series_id}'",
            "deleted_count": deleted_count,
            "series_id": series_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error clearing cache for series '{series_id}': {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache for series '{series_id}': {str(e)}",
        )


@router.post("/spark/analytics", response_model=AnalyticsResponse)
async def perform_analytics(request: AnalyticsRequest):
    """
    Perform analytics on FRED series data.

    Supports:
    - Basic statistics (mean, median, std, min, max, count, sum)
    - Growth rates (period-over-period, year-over-year)
    - Correlations between series
    - Moving averages (simple and exponential)
    - Time-based aggregations (daily, weekly, monthly, quarterly, yearly)

    Args:
        request: AnalyticsRequest with series IDs, analytics types, and options

    Returns:
        AnalyticsResponse with requested analytics results

    Raises:
        HTTPException: If analytics processing fails
    """
    try:
        spark_service = get_spark_service()
        fred_service = get_fred_service()

        # Verify Spark is available
        if not spark_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spark service is not available",
            )

        # Create Spark data service
        spark_data_service = SparkDataService(
            spark_service=spark_service, fred_service=fred_service
        )

        logger.info(
            f"Performing analytics on {len(request.series_ids)} series: {request.series_ids}"
        )
        logger.info(f"Analytics types requested: {request.analytics_types}")

        # Validate required parameters for specific analytics types
        if "moving_averages" in request.analytics_types:
            if request.moving_average_window is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="moving_average_window is required when 'moving_averages' is requested",
                )
            if request.moving_average_type is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="moving_average_type is required when 'moving_averages' is requested",
                )

        if "time_aggregations" in request.analytics_types:
            if request.time_aggregation_period is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="time_aggregation_period is required when 'time_aggregations' is requested",
                )
            if request.time_aggregation_function is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="time_aggregation_function is required when 'time_aggregations' is requested",
                )

        # Fetch all series in parallel (with caching if enabled)
        fred_responses = await spark_data_service.batch_fetch_series(
            series_ids=request.series_ids,
            limit=request.limit,
            sort_order=request.sort_order,
            use_cache=request.use_cache,
        )

        # Convert to DataFrame
        df = spark_data_service.convert_to_dataframe(fred_responses)

        # Prepare DataFrame for analytics (convert dates, sort)
        df = spark_data_service._prepare_dataframe_for_analytics(df)

        # Initialize response data
        statistics = None
        growth_rates = None
        correlations = None
        moving_averages = None
        time_aggregations = None

        # Perform requested analytics
        if "statistics" in request.analytics_types:
            logger.info("Calculating statistics")
            statistics = spark_data_service.calculate_statistics(df)

        if "growth_rates" in request.analytics_types:
            logger.info("Calculating growth rates")
            growth_rates = spark_data_service.calculate_growth_rates(df, include_yoy=True)

        if "correlations" in request.analytics_types:
            logger.info("Calculating correlations")
            correlations = spark_data_service.calculate_correlations(df)

        if "moving_averages" in request.analytics_types:
            logger.info(
                f"Calculating {request.moving_average_type} moving averages with window {request.moving_average_window}"
            )
            moving_averages = spark_data_service.calculate_moving_averages(
                df, window_size=request.moving_average_window, ma_type=request.moving_average_type
            )

        if "time_aggregations" in request.analytics_types:
            logger.info(
                f"Calculating time aggregations: {request.time_aggregation_period} with {request.time_aggregation_function}"
            )
            time_aggregations = spark_data_service.calculate_time_aggregations(
                df,
                period=request.time_aggregation_period,
                agg_function=request.time_aggregation_function,
            )

        return AnalyticsResponse(
            series_count=len(request.series_ids),
            statistics=statistics,
            growth_rates=growth_rates,
            correlations=correlations,
            moving_averages=moving_averages,
            time_aggregations=time_aggregations,
        )

    except ValueError as e:
        logger.error(f"ValueError in perform_analytics: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in perform_analytics: {type(e).__name__}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing analytics: {str(e)}",
        )
