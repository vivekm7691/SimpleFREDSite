/**
 * TrendsView component - Displays trend analysis results
 * 
 * Features:
 * - Show trend direction, slope, R², and polynomial degree
 * - Visualize trend information in cards
 */

import './AdvancedAnalytics.css'

/**
 * TrendsView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of Trend objects
 */
function TrendsView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="advanced-analytics-view">
        <h3>Trends</h3>
        <div className="advanced-analytics-empty">
          <p>No trend data available</p>
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
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    })
  }

  /**
   * Get trend direction color
   */
  const getDirectionColor = (direction) => {
    switch (direction) {
      case 'increasing':
        return '#28a745'
      case 'decreasing':
        return '#dc3545'
      default:
        return '#6c757d'
    }
  }

  return (
    <div className="advanced-analytics-view">
      <h3>Trend Analysis</h3>
      <div className="trends-grid">
        {data.map((trend, index) => (
          <div key={trend.series_id || index} className="trend-card">
            <div className="trend-header">
              <h4>{trend.series_id}</h4>
              <span 
                className="trend-direction"
                style={{ color: getDirectionColor(trend.direction) }}
              >
                {trend.direction.charAt(0).toUpperCase() + trend.direction.slice(1)}
              </span>
            </div>
            <div className="trend-content">
              <div className="trend-row">
                <div className="trend-item">
                  <span className="trend-label">Trend Type:</span>
                  <span className="trend-value">{trend.trend_type}</span>
                </div>
                {trend.polynomial_degree && (
                  <div className="trend-item">
                    <span className="trend-label">Polynomial Degree:</span>
                    <span className="trend-value">{trend.polynomial_degree}</span>
                  </div>
                )}
              </div>
              {trend.slope !== null && trend.slope !== undefined && (
                <div className="trend-row">
                  <div className="trend-item">
                    <span className="trend-label">Slope:</span>
                    <span className="trend-value">{formatNumber(trend.slope)}</span>
                  </div>
                  {trend.intercept !== null && trend.intercept !== undefined && (
                    <div className="trend-item">
                      <span className="trend-label">Intercept:</span>
                      <span className="trend-value">{formatNumber(trend.intercept)}</span>
                    </div>
                  )}
                </div>
              )}
              <div className="trend-row">
                <div className="trend-item full-width">
                  <span className="trend-label">R² (Trend Strength):</span>
                  <span className="trend-value">{formatNumber(trend.r_squared)}</span>
                  <div className="trend-strength-bar">
                    <div 
                      className="trend-strength-fill"
                      style={{ width: `${(trend.r_squared * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TrendsView

