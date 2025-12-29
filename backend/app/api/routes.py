"""
API routes for FRED data and summarization.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict

from app.models.schemas import (
    FREDFetchRequest,
    FREDDataResponse,
    SummarizeRequest,
    SummarizeResponse
)
from app.services.fred_service import get_fred_service
from app.services.gemini_service import get_gemini_service

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching FRED data: {str(e)}"
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
    try:
        gemini_service = get_gemini_service()
        summary = await gemini_service.summarize_data(request.data)
        return SummarizeResponse(summary=summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

