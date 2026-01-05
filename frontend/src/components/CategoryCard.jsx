/**
 * CategoryCard component for displaying a single category in the category grid.
 * 
 * Displays category icon, name, and series count. Handles click events to
 * navigate to category detail view.
 */

/**
 * CategoryCard component
 * @param {Object} props - Component props
 * @param {Object} props.category - Category object with id, name, icon, series_count
 * @param {Function} props.onClick - Callback function when card is clicked
 */
function CategoryCard({ category, onClick }) {
  /**
   * Handle card click event
   */
  const handleClick = () => {
    if (onClick) {
      onClick(category.id)
    }
  }

  /**
   * Handle keyboard events for accessibility
   */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <div
      className="category-card"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Category: ${category.name}, ${category.series_count} series available`}
    >
      <div className="category-card-icon">{category.icon}</div>
      <div className="category-card-content">
        <h3 className="category-card-name">{category.name}</h3>
        <p className="category-card-count">
          {category.series_count} {category.series_count === 1 ? 'series' : 'series'}
        </p>
      </div>
    </div>
  )
}

export default CategoryCard

