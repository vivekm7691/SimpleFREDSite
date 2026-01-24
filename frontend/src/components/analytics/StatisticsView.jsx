/**
 * StatisticsView component - Displays basic statistics for each series
 * 
 * Features:
 * - Card-based layout showing statistics per series
 * - Displays mean, median, std dev, min, max, count, sum
 * - Responsive grid layout
 */

import './Analytics.css'

/**
 * StatisticsView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of SeriesStatistics objects
 */
function StatisticsView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Statistics</h3>
        <div className="analytics-empty">
          <p>No statistics data available</p>
        </div>
      </div>
    )
  }

  /**
   * Format number for display
   */
  const formatNumber = (value) => {
    if (value === null || value === undefined) {
      return 'N/A'
    }
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  return (
    <div className="analytics-view">
      <h3>Statistics</h3>
      <div className="statistics-grid">
        {data.map((stat, index) => (
          <div key={stat.series_id || index} className="statistics-card">
            <div className="statistics-header">
              <h4>{stat.series_id}</h4>
            </div>
            <div className="statistics-content">
              <div className="statistics-row">
                <div className="statistics-item">
                  <span className="statistics-label">Mean:</span>
                  <span className="statistics-value">{formatNumber(stat.mean)}</span>
                </div>
                <div className="statistics-item">
                  <span className="statistics-label">Median:</span>
                  <span className="statistics-value">{formatNumber(stat.median)}</span>
                </div>
              </div>
              <div className="statistics-row">
                <div className="statistics-item">
                  <span className="statistics-label">Std Dev:</span>
                  <span className="statistics-value">{formatNumber(stat.std)}</span>
                </div>
                <div className="statistics-item">
                  <span className="statistics-label">Count:</span>
                  <span className="statistics-value">{stat.count}</span>
                </div>
              </div>
              <div className="statistics-row">
                <div className="statistics-item">
                  <span className="statistics-label">Min:</span>
                  <span className="statistics-value">{formatNumber(stat.min)}</span>
                </div>
                <div className="statistics-item">
                  <span className="statistics-label">Max:</span>
                  <span className="statistics-value">{formatNumber(stat.max)}</span>
                </div>
              </div>
              {stat.sum !== null && stat.sum !== undefined && (
                <div className="statistics-row">
                  <div className="statistics-item full-width">
                    <span className="statistics-label">Sum:</span>
                    <span className="statistics-value">{formatNumber(stat.sum)}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default StatisticsView

