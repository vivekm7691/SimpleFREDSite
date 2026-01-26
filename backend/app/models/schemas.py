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
    use_cache: bool = Field(
        default=True, description="Whether to use cached data if available"
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


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    total_files: int = Field(..., description="Total number of cache files")
    unique_series: int = Field(..., description="Number of unique series cached")
    total_size_bytes: int = Field(..., description="Total cache size in bytes")
    total_size_mb: float = Field(..., description="Total cache size in MB")


class CacheEntry(BaseModel):
    """Model for a single cache entry."""

    series_id: str = Field(..., description="FRED series ID")
    limit: int = Field(..., description="Maximum observations")
    sort_order: str = Field(..., description="Sort order")
    file_size: int = Field(..., description="Cache file size in bytes")
    modified_time: str = Field(..., description="Last modification time (ISO format)")
    cache_path: str = Field(..., description="Path to cache file")


class CacheListResponse(BaseModel):
    """Response model for cache list."""

    entries: List[CacheEntry] = Field(..., description="List of cache entries")
    total_count: int = Field(..., description="Total number of cache entries")


class SeriesStatistics(BaseModel):
    """Model for series statistics."""

    series_id: str = Field(..., description="FRED series ID")
    mean: Optional[float] = Field(None, description="Mean value")
    median: Optional[float] = Field(None, description="Median value")
    std: Optional[float] = Field(None, description="Standard deviation")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")
    count: int = Field(..., description="Number of observations")
    sum: Optional[float] = Field(None, description="Sum of values")


class GrowthRate(BaseModel):
    """Model for growth rate data."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Observation date")
    value: Optional[float] = Field(None, description="Current value")
    previous_value: Optional[float] = Field(None, description="Previous period value")
    growth_rate: Optional[float] = Field(None, description="Growth rate percentage")
    growth_type: str = Field(
        ..., description="Type of growth rate: 'period_over_period' or 'year_over_year'"
    )


class Correlation(BaseModel):
    """Model for correlation between two series."""

    series_id_1: str = Field(..., description="First FRED series ID")
    series_id_2: str = Field(..., description="Second FRED series ID")
    correlation: float = Field(..., description="Correlation coefficient (-1 to 1)")


class MovingAverage(BaseModel):
    """Model for moving average data."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Observation date")
    value: Optional[float] = Field(None, description="Original value")
    moving_average: Optional[float] = Field(None, description="Moving average value")
    moving_average_type: str = Field(..., description="Type: 'sma' or 'ema'")
    window_size: int = Field(..., description="Window size for moving average")


class TimeAggregation(BaseModel):
    """Model for time-based aggregation data."""

    series_id: str = Field(..., description="FRED series ID")
    period: str = Field(
        ..., description="Time period (e.g., '2024-01', '2024-Q1', '2024')"
    )
    aggregated_value: Optional[float] = Field(None, description="Aggregated value")
    aggregation_function: str = Field(
        ...,
        description="Aggregation function used: 'mean', 'sum', 'min', 'max', 'first', 'last'",
    )
    observation_count: int = Field(..., description="Number of observations in period")


class AnalyticsRequest(BaseModel):
    """Request model for analytics operations."""

    series_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of FRED series IDs to analyze",
    )
    analytics_types: List[str] = Field(
        ...,
        min_length=1,
        description="Types of analytics to perform: 'statistics', 'growth_rates', 'correlations', 'moving_averages', 'time_aggregations'",
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum observations per series"
    )
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order"
    )
    use_cache: bool = Field(
        default=True, description="Whether to use cached data if available"
    )
    moving_average_window: Optional[int] = Field(
        None,
        ge=2,
        le=365,
        description="Window size for moving averages (required if 'moving_averages' in analytics_types)",
    )
    moving_average_type: Optional[str] = Field(
        None,
        pattern="^(sma|ema)$",
        description="Type of moving average: 'sma' or 'ema' (required if 'moving_averages' in analytics_types)",
    )
    time_aggregation_period: Optional[str] = Field(
        None,
        pattern="^(daily|weekly|monthly|quarterly|yearly)$",
        description="Time period for aggregation (required if 'time_aggregations' in analytics_types)",
    )
    time_aggregation_function: Optional[str] = Field(
        None,
        pattern="^(mean|sum|min|max|first|last)$",
        description="Aggregation function (required if 'time_aggregations' in analytics_types)",
    )

    @field_validator("series_ids")
    @classmethod
    def validate_series_ids(cls, v: List[str]) -> List[str]:
        """Validate series IDs format."""
        if not v:
            raise ValueError("At least one series ID is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 series IDs allowed per request")
        validated = []
        for series_id in v:
            if not series_id.strip():
                raise ValueError("Series ID cannot be empty")
            if not series_id.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Series ID '{series_id}' contains invalid characters")
            validated.append(series_id.strip().upper())
        return validated

    @field_validator("analytics_types")
    @classmethod
    def validate_analytics_types(cls, v: List[str]) -> List[str]:
        """Validate analytics types."""
        valid_types = [
            "statistics",
            "growth_rates",
            "correlations",
            "moving_averages",
            "time_aggregations",
        ]
        for analytics_type in v:
            if analytics_type not in valid_types:
                raise ValueError(
                    f"Invalid analytics type: {analytics_type}. Must be one of {valid_types}"
                )
        return v


class AnalyticsResponse(BaseModel):
    """Response model for analytics operations."""

    series_count: int = Field(..., description="Number of series analyzed")
    statistics: Optional[List[SeriesStatistics]] = Field(
        None, description="Basic statistics per series"
    )
    growth_rates: Optional[List[GrowthRate]] = Field(
        None, description="Growth rate data"
    )
    correlations: Optional[List[Correlation]] = Field(
        None, description="Correlation matrix between series"
    )
    moving_averages: Optional[List[MovingAverage]] = Field(
        None, description="Moving average data"
    )
    time_aggregations: Optional[List[TimeAggregation]] = Field(
        None, description="Time-based aggregation data"
    )


# Advanced Analytics Models (Increment 6)


class Forecast(BaseModel):
    """Model for forecasted values."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Forecast date (YYYY-MM-DD)")
    forecasted_value: float = Field(..., description="Forecasted value")
    lower_bound: Optional[float] = Field(
        None, description="Lower bound of confidence interval"
    )
    upper_bound: Optional[float] = Field(
        None, description="Upper bound of confidence interval"
    )
    confidence_level: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence level (e.g., 0.95 for 95%)"
    )
    forecast_method: str = Field(
        ...,
        description="Forecasting method: 'arima', 'exponential_smoothing', or 'linear_regression'",
    )


class Anomaly(BaseModel):
    """Model for detected anomalies."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Date of anomaly (YYYY-MM-DD)")
    value: float = Field(..., description="Anomalous value")
    expected_value: Optional[float] = Field(
        None, description="Expected value (mean or moving average)"
    )
    deviation: float = Field(
        ..., description="Deviation in standard deviations from mean"
    )
    detection_method: str = Field(
        ...,
        description="Detection method: 'z_score', 'iqr', or 'moving_average'",
    )
    severity: str = Field(
        ..., description="Severity level: 'low', 'medium', or 'high'"
    )


class Trend(BaseModel):
    """Model for trend analysis results."""

    series_id: str = Field(..., description="FRED series ID")
    trend_type: str = Field(
        ..., description="Type of trend: 'linear', 'polynomial', or 'none'"
    )
    slope: Optional[float] = Field(None, description="Slope for linear trends")
    intercept: Optional[float] = Field(
        None, description="Intercept for linear trends"
    )
    r_squared: float = Field(
        ..., ge=0.0, le=1.0, description="R-squared value (trend strength)"
    )
    direction: str = Field(
        ...,
        description="Trend direction: 'increasing', 'decreasing', or 'stable'",
    )
    polynomial_degree: Optional[int] = Field(
        None, ge=2, le=5, description="Polynomial degree for polynomial trends"
    )


class SeasonalDecomposition(BaseModel):
    """Model for seasonal decomposition results."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    actual_value: float = Field(..., description="Original value")
    trend_component: float = Field(..., description="Trend component")
    seasonal_component: float = Field(..., description="Seasonal component")
    residual_component: float = Field(..., description="Residual component")
    decomposition_type: str = Field(
        ...,
        description="Decomposition type: 'additive' or 'multiplicative'",
    )


class Volatility(BaseModel):
    """Model for volatility analysis results."""

    series_id: str = Field(..., description="FRED series ID")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    volatility: float = Field(..., description="Rolling volatility")
    annualized_volatility: Optional[float] = Field(
        None, description="Annualized volatility"
    )
    return_value: Optional[float] = Field(
        None, description="Period return (percentage change)"
    )
    window_size: int = Field(..., ge=2, description="Rolling window size used")


class AdvancedAnalyticsRequest(BaseModel):
    """Request model for advanced analytics operations."""

    series_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of FRED series IDs to analyze",
    )
    analytics_types: List[str] = Field(
        ...,
        min_length=1,
        description="Types of analytics to perform: 'forecasts', 'anomalies', 'trends', 'seasonal_decomposition', 'volatility'",
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum observations per series"
    )
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order"
    )
    use_cache: bool = Field(
        default=True, description="Whether to use cached data if available"
    )
    # Forecasting options
    forecast_horizon: Optional[int] = Field(
        None,
        ge=1,
        le=120,
        description="Number of periods to forecast (required if 'forecasts' in analytics_types)",
    )
    forecast_method: Optional[str] = Field(
        None,
        pattern="^(arima|exponential_smoothing|linear_regression)$",
        description="Forecasting method (required if 'forecasts' in analytics_types)",
    )
    # Anomaly detection options
    anomaly_method: Optional[str] = Field(
        None,
        pattern="^(z_score|iqr|moving_average)$",
        description="Anomaly detection method (required if 'anomalies' in analytics_types)",
    )
    anomaly_threshold: Optional[float] = Field(
        None,
        ge=1.0,
        le=10.0,
        description="Z-score threshold for anomaly detection (default: 3.0)",
    )
    # Trend analysis options
    trend_type: Optional[str] = Field(
        None,
        pattern="^(linear|polynomial)$",
        description="Type of trend analysis (required if 'trends' in analytics_types)",
    )
    polynomial_degree: Optional[int] = Field(
        None,
        ge=2,
        le=5,
        description="Polynomial degree for polynomial trends (default: 2)",
    )
    # Seasonal decomposition options
    decomposition_type: Optional[str] = Field(
        None,
        pattern="^(additive|multiplicative)$",
        description="Decomposition type (required if 'seasonal_decomposition' in analytics_types)",
    )
    seasonal_period: Optional[int] = Field(
        None,
        ge=2,
        le=365,
        description="Seasonal period (e.g., 12 for monthly data, required if 'seasonal_decomposition' in analytics_types)",
    )
    # Volatility options
    volatility_window: Optional[int] = Field(
        None,
        ge=2,
        le=365,
        description="Rolling window size for volatility calculation (default: 30)",
    )

    @field_validator("series_ids")
    @classmethod
    def validate_series_ids(cls, v: List[str]) -> List[str]:
        """Validate and normalize series IDs."""
        validated = []
        for series_id in v:
            if not series_id.strip():
                raise ValueError("Series ID cannot be empty")
            if not series_id.replace("_", "").replace("-", "").isalnum():
                raise ValueError(
                    f"Series ID '{series_id}' contains invalid characters"
                )
            validated.append(series_id.strip().upper())
        return validated

    @field_validator("analytics_types")
    @classmethod
    def validate_analytics_types(cls, v: List[str]) -> List[str]:
        """Validate analytics types."""
        valid_types = [
            "forecasts",
            "anomalies",
            "trends",
            "seasonal_decomposition",
            "volatility",
        ]
        for analytics_type in v:
            if analytics_type not in valid_types:
                raise ValueError(
                    f"Invalid analytics type: {analytics_type}. Must be one of {valid_types}"
                )
        return v


class AdvancedAnalyticsResponse(BaseModel):
    """Response model for advanced analytics operations."""

    series_count: int = Field(..., description="Number of series analyzed")
    forecasts: Optional[List[Forecast]] = Field(
        None, description="Forecasted values"
    )
    anomalies: Optional[List[Anomaly]] = Field(
        None, description="Detected anomalies"
    )
    trends: Optional[List[Trend]] = Field(None, description="Trend analysis results")
    seasonal_decompositions: Optional[List[SeasonalDecomposition]] = Field(
        None, description="Seasonal decomposition results"
    )
    volatility: Optional[List[Volatility]] = Field(
        None, description="Volatility analysis results"
    )