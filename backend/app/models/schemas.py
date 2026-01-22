"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class FREDFetchRequest(BaseModel):
    """Request model for fetching FRED data."""

    series_id: str = Field(
        ..., min_length=1, max_length=100, description="FRED series ID"
    )

    @field_validator("series_id")
    @classmethod
    def validate_series_id(cls, v: str) -> str:
        """Validate series ID format."""
        if not v.strip():
            raise ValueError("Series ID cannot be empty")
        # FRED series IDs are typically uppercase alphanumeric with underscores
        if not v.replace("_", "").replace("-", "").isalnum():
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


# Category browsing models


class CategoryInfo(BaseModel):
    """Model for individual category information."""

    id: str = Field(..., description="Category ID (e.g., 'employment', 'inflation')")
    name: str = Field(..., description="Category display name")
    icon: str = Field(..., description="Category icon (emoji or icon identifier)")
    description: Optional[str] = Field(None, description="Category description")
    series_count: int = Field(..., description="Number of series in this category")


class SeriesListItem(BaseModel):
    """Simplified series model for category listings."""

    id: str = Field(..., description="Series ID")
    title: str = Field(..., description="Series title")
    frequency: Optional[str] = Field(None, description="Data frequency")
    units: Optional[str] = Field(None, description="Units of measurement")
    seasonal_adjustment: Optional[str] = Field(
        None, description="Seasonal adjustment method"
    )


class CategoryResponse(BaseModel):
    """Response model for list of categories."""

    categories: List[CategoryInfo] = Field(
        ..., description="List of available categories"
    )


class CategorySeriesResponse(BaseModel):
    """Response model for series within a category."""

    category_id: str = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    series: List[SeriesListItem] = Field(..., description="List of series in category")
    total_count: int = Field(..., description="Total number of series in category")


# Spark batch processing models


class BatchFetchRequest(BaseModel):
    """Request model for batch fetching multiple FRED series."""

    series_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of FRED series IDs to fetch",
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum observations per series"
    )
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order"
    )
    aggregation_type: str = Field(
        default="union",
        description="Type of aggregation to perform",
    )

    @field_validator("series_ids")
    @classmethod
    def validate_series_ids(cls, v: List[str]) -> List[str]:
        """Validate series IDs format."""
        if not v:
            raise ValueError("At least one series ID is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 series IDs allowed per request")
        # Validate each series ID
        validated = []
        for series_id in v:
            if not series_id.strip():
                raise ValueError("Series ID cannot be empty")
            if not series_id.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Series ID '{series_id}' contains invalid characters")
            validated.append(series_id.strip().upper())
        return validated


class BatchFetchResponse(BaseModel):
    """Response model for batch fetch operation."""

    series_count: int = Field(..., description="Number of series processed")
    total_observations: int = Field(..., description="Total number of observations")
    columns: List[str] = Field(..., description="Column names in the data")
    data: List[dict] = Field(..., description="Combined data from all series")
    series_info: List[dict] = Field(
        ..., description="Metadata for each series processed"
    )
