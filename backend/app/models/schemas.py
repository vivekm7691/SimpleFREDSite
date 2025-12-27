"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class FREDFetchRequest(BaseModel):
    """Request model for fetching FRED data."""
    series_id: str = Field(..., min_length=1, max_length=100, description="FRED series ID")
    
    @field_validator('series_id')
    @classmethod
    def validate_series_id(cls, v: str) -> str:
        """Validate series ID format."""
        if not v.strip():
            raise ValueError("Series ID cannot be empty")
        # FRED series IDs are typically uppercase alphanumeric with underscores
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Series ID contains invalid characters")
        return v.strip().upper()


class FREDObservation(BaseModel):
    """Model for a single FRED observation."""
    date: str = Field(..., description="Observation date (YYYY-MM-DD)")
    value: Optional[float] = Field(None, description="Observation value")


class FREDSeriesInfo(BaseModel):
    """Model for FRED series metadata."""
    id: str = Field(..., description="Series ID")
    title: str = Field(..., description="Series title")
    units: Optional[str] = Field(None, description="Units of measurement")
    frequency: Optional[str] = Field(None, description="Data frequency")
    seasonal_adjustment: Optional[str] = Field(None, description="Seasonal adjustment")


class FREDDataResponse(BaseModel):
    """Response model for FRED data."""
    series_id: str = Field(..., description="FRED series ID")
    series_info: FREDSeriesInfo = Field(..., description="Series metadata")
    observations: List[FREDObservation] = Field(..., description="Data observations")
    observation_count: int = Field(..., description="Number of observations")


class SummarizeRequest(BaseModel):
    """Request model for data summarization."""
    data: dict = Field(..., description="Data to summarize")


class SummarizeResponse(BaseModel):
    """Response model for summarization."""
    summary: str = Field(..., description="Generated summary")

