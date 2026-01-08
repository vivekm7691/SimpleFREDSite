"""
Tests for Category service methods.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.category_service import CategoryService, get_category_service
from app.models.schemas import CategoryInfo, SeriesListItem, CategorySeriesResponse


class TestCategoryServiceInitialization:
    """Test cases for CategoryService initialization."""

    def test_init(self):
        """Test CategoryService initialization."""
        service = CategoryService()
        assert service.categories is not None
        assert len(service.categories) > 0

    def test_get_category_service_singleton(self):
        """Test that get_category_service returns a singleton instance."""
        service1 = get_category_service()
        service2 = get_category_service()
        assert service1 is service2


class TestCategoryServiceGetAllCategories:
    """Test cases for get_all_categories method."""

    def test_get_all_categories_returns_list(self):
        """Test that get_all_categories returns a list of categories."""
        service = CategoryService()
        categories = service.get_all_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_get_all_categories_returns_category_info(self):
        """Test that get_all_categories returns CategoryInfo objects."""
        service = CategoryService()
        categories = service.get_all_categories()
        for category in categories:
            assert isinstance(category, CategoryInfo)
            assert category.id is not None
            assert category.name is not None
            assert category.icon is not None
            assert category.series_count >= 0

    def test_get_all_categories_includes_expected_categories(self):
        """Test that get_all_categories includes expected category IDs."""
        service = CategoryService()
        categories = service.get_all_categories()
        category_ids = [cat.id for cat in categories]
        
        # Check for expected categories
        assert "employment" in category_ids
        assert "inflation" in category_ids
        assert "gdp" in category_ids
        assert "interest_rates" in category_ids
        assert "money_banking" in category_ids
        assert "production" in category_ids
        assert "prices" in category_ids

    def test_get_all_categories_series_count(self):
        """Test that series_count is correctly calculated."""
        service = CategoryService()
        categories = service.get_all_categories()
        
        for category in categories:
            # Get the actual category data
            category_data = service.get_category(category.id)
            expected_count = len(category_data["series_ids"])
            assert category.series_count == expected_count


class TestCategoryServiceGetCategory:
    """Test cases for get_category method."""

    def test_get_category_valid_id(self):
        """Test getting a category with a valid ID."""
        service = CategoryService()
        category = service.get_category("employment")
        assert category is not None
        assert category["id"] == "employment"
        assert category["name"] == "Employment"
        assert "series_ids" in category

    def test_get_category_invalid_id(self):
        """Test getting a category with an invalid ID."""
        service = CategoryService()
        category = service.get_category("invalid_category")
        assert category is None

    def test_get_category_all_categories(self):
        """Test getting all defined categories."""
        service = CategoryService()
        all_categories = service.get_all_categories()
        
        for category_info in all_categories:
            category = service.get_category(category_info.id)
            assert category is not None
            assert category["id"] == category_info.id
            assert category["name"] == category_info.name


class TestCategoryServiceGetCategorySeriesIds:
    """Test cases for get_category_series_ids method."""

    def test_get_category_series_ids_valid_category(self):
        """Test getting series IDs for a valid category."""
        service = CategoryService()
        series_ids = service.get_category_series_ids("employment")
        assert isinstance(series_ids, list)
        assert len(series_ids) > 0
        assert "UNRATE" in series_ids
        assert "PAYEMS" in series_ids

    def test_get_category_series_ids_returns_copy(self):
        """Test that get_category_series_ids returns a copy, not the original list."""
        service = CategoryService()
        series_ids1 = service.get_category_series_ids("employment")
        series_ids2 = service.get_category_series_ids("employment")
        
        # They should be equal but not the same object
        assert series_ids1 == series_ids2
        assert series_ids1 is not series_ids2
        
        # Modifying one should not affect the other
        series_ids1.append("TEST")
        assert "TEST" not in series_ids2

    def test_get_category_series_ids_invalid_category(self):
        """Test getting series IDs for an invalid category raises ValueError."""
        service = CategoryService()
        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            service.get_category_series_ids("invalid")


class TestCategoryServiceSearchSeriesInCategory:
    """Test cases for search_series_in_category method."""

    def test_search_series_in_category_no_search_term(self):
        """Test search with no search term returns all series."""
        service = CategoryService()
        all_series = service.get_category_series_ids("employment")
        search_results = service.search_series_in_category("employment", "")
        assert search_results == all_series

    def test_search_series_in_category_case_insensitive(self):
        """Test that search is case-insensitive."""
        service = CategoryService()
        results_lower = service.search_series_in_category("employment", "unrate")
        results_upper = service.search_series_in_category("employment", "UNRATE")
        results_mixed = service.search_series_in_category("employment", "UnRaTe")
        
        assert results_lower == results_upper == results_mixed
        assert "UNRATE" in results_lower

    def test_search_series_in_category_partial_match(self):
        """Test that search matches partial series IDs."""
        service = CategoryService()
        results = service.search_series_in_category("employment", "UN")
        assert len(results) > 0
        assert all("UN" in series_id.upper() for series_id in results)

    def test_search_series_in_category_exact_match(self):
        """Test that search matches exact series IDs."""
        service = CategoryService()
        results = service.search_series_in_category("employment", "UNRATE")
        assert "UNRATE" in results
        assert len(results) == 1

    def test_search_series_in_category_no_match(self):
        """Test that search returns empty list when no matches found."""
        service = CategoryService()
        results = service.search_series_in_category("employment", "NONEXISTENT123")
        assert results == []

    def test_search_series_in_category_invalid_category(self):
        """Test that search with invalid category raises ValueError."""
        service = CategoryService()
        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            service.search_series_in_category("invalid", "test")


class TestCategoryServiceGetCategorySeries:
    """Test cases for get_category_series method."""

    @pytest.mark.asyncio
    async def test_get_category_series_without_fred_service(self):
        """Test getting category series without FRED service (returns basic info)."""
        service = CategoryService()
        response = await service.get_category_series("employment")
        
        assert isinstance(response, CategorySeriesResponse)
        assert response.category_id == "employment"
        assert response.category_name == "Employment"
        assert len(response.series) > 0
        assert response.total_count > 0
        
        # Without FRED service, titles should be series IDs
        for series in response.series:
            assert isinstance(series, SeriesListItem)
            assert series.id is not None
            assert series.title == series.id  # Title defaults to ID without FRED service

    @pytest.mark.asyncio
    async def test_get_category_series_with_fred_service(self):
        """Test getting category series with FRED service (returns full metadata)."""
        service = CategoryService()
        
        # Mock FRED service
        mock_fred_service = MagicMock()
        mock_series_list = [
            SeriesListItem(
                id="UNRATE",
                title="Unemployment Rate",
                frequency="Monthly",
                units="Percent",
                seasonal_adjustment="Seasonally Adjusted"
            ),
            SeriesListItem(
                id="PAYEMS",
                title="Nonfarm Payroll Employment",
                frequency="Monthly",
                units="Thousands of Persons",
                seasonal_adjustment="Seasonally Adjusted"
            ),
        ]
        mock_fred_service.get_series_list = AsyncMock(return_value=mock_series_list)
        
        response = await service.get_category_series(
            "employment",
            fred_service=mock_fred_service
        )
        
        assert isinstance(response, CategorySeriesResponse)
        assert response.category_id == "employment"
        assert response.category_name == "Employment"
        assert len(response.series) > 0
        
        # With FRED service, titles should be full names
        assert any(series.title != series.id for series in response.series)
        mock_fred_service.get_series_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_category_series_with_search_term(self):
        """Test getting category series with search filter."""
        service = CategoryService()
        response = await service.get_category_series("employment", search_term="UN")
        
        assert isinstance(response, CategorySeriesResponse)
        assert response.category_id == "employment"
        # Should only include series matching "UN"
        assert all("UN" in series.id.upper() for series in response.series)

    @pytest.mark.asyncio
    async def test_get_category_series_fred_service_error_handling(self):
        """Test that FRED service errors are handled gracefully."""
        service = CategoryService()
        
        # Mock FRED service that raises an exception
        mock_fred_service = MagicMock()
        mock_fred_service.get_series_list = AsyncMock(side_effect=Exception("FRED API error"))
        
        # Should not raise exception, but return basic info instead
        response = await service.get_category_series(
            "employment",
            fred_service=mock_fred_service
        )
        
        assert isinstance(response, CategorySeriesResponse)
        assert len(response.series) > 0
        # Should fall back to basic info (title = id)
        assert all(series.title == series.id for series in response.series)

    @pytest.mark.asyncio
    async def test_get_category_series_invalid_category(self):
        """Test that getting series for invalid category raises ValueError."""
        service = CategoryService()
        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            await service.get_category_series("invalid")

    @pytest.mark.asyncio
    async def test_get_category_series_total_count(self):
        """Test that total_count matches the number of series."""
        service = CategoryService()
        response = await service.get_category_series("employment")
        
        # Total count should match the number of series returned
        assert response.total_count == len(response.series)
        
        # With search, total_count should match filtered results
        response_filtered = await service.get_category_series("employment", search_term="UN")
        assert response_filtered.total_count == len(response_filtered.series)
        assert response_filtered.total_count <= response.total_count

