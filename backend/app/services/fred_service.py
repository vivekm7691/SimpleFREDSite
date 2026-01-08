"""
FRED API service for fetching economic data.
"""

import os
from typing import List, Optional
import httpx
import asyncio

from app.models.schemas import (
    FREDDataResponse,
    FREDSeriesInfo,
    FREDObservation,
    SeriesListItem,
)


class FREDService:
    """Service for interacting with the FRED API."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED service.

        Args:
            api_key: FRED API key. If not provided, reads from FRED_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED_API_KEY environment variable is required")

    async def fetch_series(
        self, series_id: str, limit: int = 100, sort_order: str = "desc"
    ) -> FREDDataResponse:
        """
        Fetch economic data for a given series ID.

        Args:
            series_id: The FRED series ID (e.g., 'GDP', 'UNRATE')
            limit: Maximum number of observations to return
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            FREDDataResponse with series data and observations

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If series ID is invalid or data cannot be parsed
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, get series info
            series_info = await self._get_series_info(client, series_id)

            # Then, get observations
            observations = await self._get_observations(
                client, series_id, limit=limit, sort_order=sort_order
            )

            return FREDDataResponse(
                series_id=series_id,
                series_info=series_info,
                observations=observations,
                observation_count=len(observations),
            )

    async def _get_series_info(
        self, client: httpx.AsyncClient, series_id: str
    ) -> FREDSeriesInfo:
        """Get metadata for a FRED series."""
        params = {"series_id": series_id, "api_key": self.api_key, "file_type": "json"}

        response = await client.get(f"{self.BASE_URL}/series", params=params)
        response.raise_for_status()

        data = response.json()

        # FRED API returns series in 'seriess' array
        if "seriess" not in data or not data["seriess"]:
            raise ValueError(f"Series '{series_id}' not found")

        series_data = data["seriess"][0]

        return FREDSeriesInfo(
            id=series_data.get("id", series_id),
            title=series_data.get("title", ""),
            units=series_data.get("units"),
            frequency=series_data.get("frequency"),
            seasonal_adjustment=series_data.get("seasonal_adjustment"),
        )

    async def _get_observations(
        self,
        client: httpx.AsyncClient,
        series_id: str,
        limit: int = 100,
        sort_order: str = "desc",
    ) -> List[FREDObservation]:
        """Get observations for a FRED series."""
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "limit": limit,
            "sort_order": sort_order,
        }

        response = await client.get(
            f"{self.BASE_URL}/series/observations", params=params
        )
        response.raise_for_status()

        data = response.json()

        # FRED API returns observations in 'observations' array
        if "observations" not in data:
            raise ValueError("Invalid response format from FRED API")

        observations = []
        for obs in data["observations"]:
            # FRED uses '.' to represent missing data
            value = None
            if obs.get("value") != ".":
                try:
                    value = float(obs["value"])
                except (ValueError, TypeError):
                    value = None

            observations.append(FREDObservation(date=obs.get("date", ""), value=value))

        return observations

    async def get_series_list(self, series_ids: List[str]) -> List[SeriesListItem]:
        """
        Fetch metadata for multiple FRED series.

        Args:
            series_ids: List of FRED series IDs

        Returns:
            List of SeriesListItem objects with series metadata

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        if not series_ids:
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch all series info concurrently for better performance
            tasks = [
                self._get_series_info_for_list(client, series_id)
                for series_id in series_ids
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            series_list = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # If a series fails, skip it but log the error
                    # Use series_id as placeholder
                    series_list.append(
                        SeriesListItem(
                            id=series_ids[i],
                            title=series_ids[i],  # Fallback to ID if fetch fails
                            frequency=None,
                            units=None,
                            seasonal_adjustment=None,
                        )
                    )
                else:
                    series_list.append(result)

            return series_list

    async def _get_series_info_for_list(
        self, client: httpx.AsyncClient, series_id: str
    ) -> SeriesListItem:
        """
        Get series metadata and convert to SeriesListItem format.

        Args:
            client: HTTP client instance
            series_id: FRED series ID

        Returns:
            SeriesListItem with series metadata

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If series not found
        """
        params = {"series_id": series_id, "api_key": self.api_key, "file_type": "json"}

        response = await client.get(f"{self.BASE_URL}/series", params=params)
        response.raise_for_status()

        data = response.json()

        # FRED API returns series in 'seriess' array
        if "seriess" not in data or not data["seriess"]:
            raise ValueError(f"Series '{series_id}' not found")

        series_data = data["seriess"][0]

        return SeriesListItem(
            id=series_data.get("id", series_id),
            title=series_data.get("title", series_id),
            units=series_data.get("units"),
            frequency=series_data.get("frequency"),
            seasonal_adjustment=series_data.get("seasonal_adjustment"),
        )


# Singleton instance (will be initialized with API key from env)
_fred_service: Optional[FREDService] = None


def get_fred_service() -> FREDService:
    """Get or create FRED service instance."""
    global _fred_service
    if _fred_service is None:
        _fred_service = FREDService()
    return _fred_service
