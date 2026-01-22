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

        # Fetch all series in parallel
        fred_responses = await spark_data_service.batch_fetch_series(
            series_ids=request.series_ids,
            limit=request.limit,
            sort_order=request.sort_order,
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
