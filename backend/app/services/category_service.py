"""
Category service for organizing FRED series into browseable categories.
"""

from typing import List, Optional
from app.models.schemas import CategoryInfo, SeriesListItem, CategorySeriesResponse


# Curated category-to-series mapping
CATEGORIES = {
    "employment": {
        "id": "employment",
        "name": "Employment",
        "icon": "📊",
        "description": "Labor market indicators",
        "series_ids": [
            "UNRATE",  # Unemployment Rate
            "PAYEMS",  # Nonfarm Payroll Employment
            "CIVPART",  # Labor Force Participation Rate
            "U6RATE",  # Total Unemployed, Plus All Persons Marginally Attached to the Labor Force
            "EMRATIO",  # Employment-Population Ratio
            "ICSA",  # Initial Claims
            "UNEMPLOY",  # Number of Unemployed Persons
            "LNS12032194",  # Employment Level - 25-54 Yrs.
        ],
    },
    "inflation": {
        "id": "inflation",
        "name": "Inflation",
        "icon": "📈",
        "description": "Price level and inflation indicators",
        "series_ids": [
            "CPIAUCSL",  # Consumer Price Index for All Urban Consumers
            "CPILFESL",  # Consumer Price Index for All Urban Consumers: All Items Less Food & Energy
            "PCEPI",  # Personal Consumption Expenditures: Chain-type Price Index
            "PCEPILFE",  # Personal Consumption Expenditures Excluding Food and Energy
            "CPIAUCSL",  # Consumer Price Index
            "USACPIALLMINMEI",  # Consumer Price Index: All Items for the United States
        ],
    },
    "gdp": {
        "id": "gdp",
        "name": "GDP & Components",
        "icon": "💰",
        "description": "Gross Domestic Product and related measures",
        "series_ids": [
            "GDP",  # Gross Domestic Product
            "GDPC1",  # Real Gross Domestic Product
            "GDPPOT",  # Real Potential GDP
            "GDPDEF",  # Gross Domestic Product: Implicit Price Deflator
            "A191RL1Q225SBEA",  # Real Gross Domestic Product
            "PCECC96",  # Real Personal Consumption Expenditures
            "GPDIC1",  # Real Gross Private Domestic Investment
        ],
    },
    "interest_rates": {
        "id": "interest_rates",
        "name": "Interest Rates",
        "icon": "📉",
        "description": "Interest rates and monetary policy",
        "series_ids": [
            "FEDFUNDS",  # Effective Federal Funds Rate
            "DGS10",  # 10-Year Treasury Constant Maturity Rate
            "DGS30",  # 30-Year Treasury Constant Maturity Rate
            "DGS5",  # 5-Year Treasury Constant Maturity Rate
            "DGS2",  # 2-Year Treasury Constant Maturity Rate
            "DFF",  # Federal Funds Effective Rate
            "TB3MS",  # 3-Month Treasury Bill: Secondary Market Rate
        ],
    },
    "money_banking": {
        "id": "money_banking",
        "name": "Money & Banking",
        "icon": "🏦",
        "description": "Money supply and banking indicators",
        "series_ids": [
            "M1SL",  # M1 Money Stock
            "M2SL",  # M2 Money Stock
            "TOTRESNS",  # Total Reserves of Depository Institutions
            "BOGMBASE",  # Monetary Base
            "BOGNONBR",  # Non-Borrowed Reserves of Depository Institutions
            "WALCL",  # Assets: Total Assets: Total Assets (Less Eliminations from Consolidation)
        ],
    },
    "production": {
        "id": "production",
        "name": "Production & Business Activity",
        "icon": "🏭",
        "description": "Industrial production and business indicators",
        "series_ids": [
            "INDPRO",  # Industrial Production Index
            "IPB50001N",  # Industrial Production: Durable Consumer Goods
            "IPB50002N",  # Industrial Production: Nondurable Consumer Goods
            "IPB50003N",  # Industrial Production: Business Equipment
            "IPB50004N",  # Industrial Production: Materials
            "IPB50005N",  # Industrial Production: Final Products
        ],
    },
    "prices": {
        "id": "prices",
        "name": "Prices",
        "icon": "💵",
        "description": "Price indices and commodity prices",
        "series_ids": [
            "PPIACO",  # Producer Price Index for All Commodities
            "WPSFD49207",  # Producer Price Index by Commodity: Processed Foods and Feeds
            "WPSID61",  # Producer Price Index by Commodity: Intermediate Materials
            "WPSID62",  # Producer Price Index by Commodity: Crude Materials
            "PPIFIS",  # Producer Price Index by Industry: Finance and Insurance
        ],
    },
}


class CategoryService:
    """Service for managing FRED series categories."""

    def __init__(self):
        """Initialize category service with curated category mappings."""
        self.categories = CATEGORIES

    def get_all_categories(self) -> List[CategoryInfo]:
        """
        Get all available categories with series counts.

        Returns:
            List of CategoryInfo objects
        """
        categories = []
        for category_data in self.categories.values():
            categories.append(
                CategoryInfo(
                    id=category_data["id"],
                    name=category_data["name"],
                    icon=category_data["icon"],
                    description=category_data.get("description"),
                    series_count=len(category_data["series_ids"]),
                )
            )
        return categories

    def get_category(self, category_id: str) -> Optional[dict]:
        """
        Get category data by ID.

        Args:
            category_id: Category identifier

        Returns:
            Category data dictionary or None if not found
        """
        return self.categories.get(category_id)

    def get_category_series_ids(self, category_id: str) -> List[str]:
        """
        Get list of series IDs for a category.

        Args:
            category_id: Category identifier

        Returns:
            List of series IDs

        Raises:
            ValueError: If category ID is invalid
        """
        category = self.get_category(category_id)
        if not category:
            raise ValueError(f"Category '{category_id}' not found")
        return category["series_ids"].copy()

    def search_series_in_category(
        self, category_id: str, search_term: str
    ) -> List[str]:
        """
        Search for series IDs within a category by matching search term.

        Args:
            category_id: Category identifier
            search_term: Search term to match against series IDs (case-insensitive)

        Returns:
            List of matching series IDs

        Raises:
            ValueError: If category ID is invalid
        """
        series_ids = self.get_category_series_ids(category_id)
        if not search_term:
            return series_ids

        search_term_lower = search_term.lower()
        matching_series = [
            series_id
            for series_id in series_ids
            if search_term_lower in series_id.lower()
        ]
        return matching_series

    async def get_category_series(
        self,
        category_id: str,
        search_term: Optional[str] = None,
        fred_service=None,
    ) -> CategorySeriesResponse:
        """
        Get series list for a category, optionally filtered by search term.

        This method will fetch series metadata from FRED API if fred_service is provided.
        Otherwise, it returns series IDs only (metadata will need to be fetched separately).

        Args:
            category_id: Category identifier
            search_term: Optional search term to filter series
            fred_service: Optional FREDService instance to fetch series metadata

        Returns:
            CategorySeriesResponse with series list

        Raises:
            ValueError: If category ID is invalid
        """
        category = self.get_category(category_id)
        if not category:
            raise ValueError(f"Category '{category_id}' not found")

        # Get series IDs (filtered by search if provided)
        if search_term:
            series_ids = self.search_series_in_category(category_id, search_term)
        else:
            series_ids = self.get_category_series_ids(category_id)

        # If FRED service is provided, fetch metadata for each series
        # For now, we'll return basic info - metadata fetching will be handled
        # by extending FREDService in the next step
        series_list = []
        for series_id in series_ids:
            # Basic series info - full metadata will come from FREDService
            series_list.append(
                SeriesListItem(
                    id=series_id,
                    title=series_id,  # Placeholder - will be replaced with actual title
                    frequency=None,
                    units=None,
                    seasonal_adjustment=None,
                )
            )

        return CategorySeriesResponse(
            category_id=category["id"],
            category_name=category["name"],
            series=series_list,
            total_count=len(series_ids),
        )


# Singleton instance
_category_service: Optional[CategoryService] = None


def get_category_service() -> CategoryService:
    """Get or create category service instance."""
    global _category_service
    if _category_service is None:
        _category_service = CategoryService()
    return _category_service

