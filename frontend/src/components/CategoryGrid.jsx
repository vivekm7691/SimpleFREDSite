/**
 * CategoryGrid component for displaying categories in a grid layout.
 * 
 * Renders CategoryCard components in a 3-column grid (desktop). Displays
 * loading state while categories are being fetched.
 */

import CategoryCard from './CategoryCard'

/**
 * CategoryGrid component
 * @param {Object} props - Component props
 * @param {Array} props.categories - Array of category objects
 * @param {Function} props.onCategoryClick - Callback function when a category is clicked
 * @param {boolean} [props.loading] - Whether categories are currently being loaded
 */
function CategoryGrid({ categories, onCategoryClick, loading = false }) {
  /**
   * Handle category card click
   * @param {string} categoryId - The ID of the clicked category
   */
  const handleCategoryClick = (categoryId) => {
    if (onCategoryClick) {
      onCategoryClick(categoryId)
    }
  }

  // Show loading state
  if (loading) {
    return (
      <div className="category-grid">
        <div className="category-grid-loading">
          <p>Loading categories...</p>
        </div>
      </div>
    )
  }

  // Show empty state
  if (!categories || categories.length === 0) {
    return (
      <div className="category-grid">
        <div className="category-grid-empty">
          <p>No categories available</p>
        </div>
      </div>
    )
  }

  // Render grid of category cards
  return (
    <div className="category-grid">
      {categories.map((category) => (
        <CategoryCard
          key={category.id}
          category={category}
          onClick={handleCategoryClick}
        />
      ))}
    </div>
  )
}

export default CategoryGrid

