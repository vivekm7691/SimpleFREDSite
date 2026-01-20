/**
 * SeriesCard component for displaying a single FRED series in the category detail view.
 * 
 * Displays series title, ID, metadata (frequency, seasonal adjustment, units), and
 * a "Select Series" button that triggers the onSelect callback.
 */

/**
 * SeriesCard component
 * @param {Object} props - Component props
 * @param {Object} props.series - Series object with id, title, frequency, units, seasonal_adjustment
 * @param {Function} props.onSelect - Callback function when "Select Series" button is clicked
 */
function SeriesCard({ series, onSelect }) {
  /**
   * Handle "Select Series" button click
   */
  const handleSelect = (e) => {
    e.stopPropagation() // Prevent card click if card itself is clickable
    if (onSelect) {
      onSelect(series.id)
    }
  }

  /**
   * Format metadata for display
   * @returns {string} Formatted metadata string
   */
  const formatMetadata = () => {
    const parts = []
    if (series.frequency) {
      parts.push(series.frequency)
    }
    if (series.seasonal_adjustment) {
      parts.push(series.seasonal_adjustment)
    }
    if (series.units) {
      parts.push(series.units)
    }
    return parts.join(' | ')
  }

  return (
    <div className="series-card">
      <div className="series-card-content">
        <div className="series-card-header">
          <span className="series-card-icon">📈</span>
          <div className="series-card-title-section">
            <h4 className="series-card-title">{series.title}</h4>
            <span className="series-card-id">({series.id})</span>
          </div>
        </div>
        {formatMetadata() && (
          <p className="series-card-metadata">{formatMetadata()}</p>
        )}
      </div>
      <button
        className="select-series-btn"
        onClick={handleSelect}
        aria-label={`Select series ${series.id}: ${series.title}`}
      >
        Select
      </button>
    </div>
  )
}

export default SeriesCard







