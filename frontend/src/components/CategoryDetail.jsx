/**
 * CategoryDetail component for displaying series within a selected category.
 * 
 * Shows breadcrumb navigation, category header, search functionality, and
 * a list of series cards. Handles loading and error states.
 */

import { useState, useEffect } from 'react'
import SeriesCard from './SeriesCard'
import { fetchCategorySeries } from '../services/api'

/**
 * CategoryDetail component
 * @param {Object} props - Component props
 * @param {string} props.categoryId - Selected category ID
 * @param {string} [props.categoryName] - Category name (optional, will be fetched if not provided)
 * @param {Function} props.onBack - Callback function to return to category grid
 * @param {Function} props.onSeriesSelect - Callback function when a series is selected
 */
function CategoryDetail({ categoryId, categoryName, onBack, onSeriesSelect }) {
  const [series, setSeries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [displayedCategoryName, setDisplayedCategoryName] = useState(categoryName || '')
  const [totalCount, setTotalCount] = useState(0)

  /**
   * Fetch series for the category
   */
  useEffect(() => {
    const loadSeries = async () => {
      if (!categoryId) return

      setLoading(true)
      setError(null)

      try {
        const response = await fetchCategorySeries(categoryId, searchTerm || null)
        setSeries(response.series || [])
        setTotalCount(response.total_count || 0)
        
        // Update category name from response if not provided as prop
        if (response.category_name) {
          if (categoryName) {
            // Use prop if provided
            setDisplayedCategoryName(categoryName)
          } else {
            // Use API response if prop not provided
            setDisplayedCategoryName(response.category_name)
          }
        }
      } catch (err) {
        setError(err.message || 'Failed to load series')
        setSeries([])
        setTotalCount(0)
      } finally {
        setLoading(false)
      }
    }

    loadSeries()
  }, [categoryId, searchTerm])

  // Update displayed category name when prop changes
  useEffect(() => {
    if (categoryName) {
      setDisplayedCategoryName(categoryName)
    }
  }, [categoryName])

  /**
   * Handle search input change
   * @param {Event} e - Input change event
   */
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value)
  }

  /**
   * Handle back button click
   */
  const handleBack = () => {
    if (onBack) {
      onBack()
    }
  }

  /**
   * Handle series selection
   * @param {string} seriesId - Selected series ID
   */
  const handleSeriesSelect = (seriesId) => {
    if (onSeriesSelect) {
      onSeriesSelect(seriesId)
    }
  }

  return (
    <div className="category-detail">
      {/* Breadcrumb Navigation */}
      <div className="category-header">
        <button
          className="category-back-btn"
          onClick={handleBack}
          aria-label="Back to categories"
        >
          ← Back to Categories
        </button>
        <div className="category-header-info">
          <h2 className="category-header-name">
            {displayedCategoryName || categoryId}
          </h2>
          {totalCount > 0 && (
            <span className="category-header-count">
              ({totalCount} {totalCount === 1 ? 'series' : 'series'})
            </span>
          )}
        </div>
      </div>

      {/* Search Input */}
      <div className="category-search">
        <input
          type="text"
          className="category-search-input"
          placeholder="Search in category..."
          value={searchTerm}
          onChange={handleSearchChange}
          aria-label="Search series in category"
        />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="category-detail-loading">
          <p>Loading series...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="category-detail-error">
          <p><strong>Error:</strong> {error}</p>
        </div>
      )}

      {/* Series List */}
      {!loading && !error && (
        <div className="series-list">
          {series.length === 0 ? (
            <div className="series-list-empty">
              <p>
                {searchTerm
                  ? `No series found matching "${searchTerm}"`
                  : 'No series available in this category'}
              </p>
            </div>
          ) : (
            <>
              {series.map((seriesItem) => (
                <SeriesCard
                  key={seriesItem.id}
                  series={seriesItem}
                  onSelect={handleSeriesSelect}
                />
              ))}
              {searchTerm && series.length > 0 && (
                <p className="series-list-info">
                  Showing {series.length} of {totalCount} series
                  {searchTerm && ` matching "${searchTerm}"`}
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default CategoryDetail

