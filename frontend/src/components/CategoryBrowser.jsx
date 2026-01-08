/**
 * CategoryBrowser component - Main container for category-based browsing.
 * 
 * Manages state and view switching between category grid and category detail views.
 * Handles fetching categories, category selection, and series selection.
 */

import { useState, useEffect } from 'react'
import CategoryGrid from './CategoryGrid'
import CategoryDetail from './CategoryDetail'
import { fetchCategories } from '../services/api'

/**
 * CategoryBrowser component
 * @param {Object} props - Component props
 * @param {Function} props.onSeriesSelect - Callback function when a series is selected (receives seriesId)
 */
function CategoryBrowser({ onSeriesSelect }) {
  const [categories, setCategories] = useState([])
  const [selectedCategoryId, setSelectedCategoryId] = useState(null)
  const [selectedCategoryName, setSelectedCategoryName] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  /**
   * Fetch all categories on component mount
   */
  useEffect(() => {
    const loadCategories = async () => {
      setLoading(true)
      setError(null)

      try {
        const response = await fetchCategories()
        setCategories(response.categories || [])
      } catch (err) {
        setError(err.message || 'Failed to load categories')
        setCategories([])
      } finally {
        setLoading(false)
      }
    }

    loadCategories()
  }, [])

  /**
   * Handle category selection - switch to detail view
   * @param {string} categoryId - Selected category ID
   */
  const handleCategoryClick = (categoryId) => {
    // Find category name from categories array
    const category = categories.find((cat) => cat.id === categoryId)
    setSelectedCategoryName(category?.name || null)
    setSelectedCategoryId(categoryId)
  }

  /**
   * Handle back navigation - return to grid view
   */
  const handleBack = () => {
    setSelectedCategoryId(null)
    setSelectedCategoryName(null)
  }

  /**
   * Handle series selection - pass to parent component
   * @param {string} seriesId - Selected series ID
   */
  const handleSeriesSelect = (seriesId) => {
    if (onSeriesSelect) {
      onSeriesSelect(seriesId)
    }
  }

  // Show error state
  if (error && !loading) {
    return (
      <div className="category-browser">
        <div className="category-browser-error">
          <p><strong>Error:</strong> {error}</p>
        </div>
      </div>
    )
  }

  // Show category detail view if a category is selected
  if (selectedCategoryId) {
    return (
      <div className="category-browser">
        <CategoryDetail
          categoryId={selectedCategoryId}
          categoryName={selectedCategoryName}
          onBack={handleBack}
          onSeriesSelect={handleSeriesSelect}
        />
      </div>
    )
  }

  // Show category grid view (default)
  return (
    <div className="category-browser">
      <h2 className="category-browser-title">Browse by Category</h2>
      <CategoryGrid
        categories={categories}
        onCategoryClick={handleCategoryClick}
        loading={loading}
      />
    </div>
  )
}

export default CategoryBrowser

