"""
API routes for FRED data and summarization.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    FREDFetchRequest,
    FREDDataResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.fred_service import get_fred_service

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
