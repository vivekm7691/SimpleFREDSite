/**
 * CorrelationsView component - Displays correlation matrix between series
 * 
 * Features:
 * - Table format with series pairs and correlation values
 * - Color coding based on correlation strength
 * - Sortable table
 */

import { useState, useMemo } from 'react'
import './Analytics.css'

/**
 * CorrelationsView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of Correlation objects
 */
function CorrelationsView({ data }) {
  const [sortBy, setSortBy] = useState('correlation') // 'correlation', 'series1', 'series2'
  const [sortOrder, setSortOrder] = useState('desc') // 'asc', 'desc'

  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Correlations</h3>
        <div className="analytics-empty">
          <p>No correlation data available. Correlations require at least 2 series.</p>
        </div>
      </div>
    )
  }

  /**
   * Get color class based on correlation value
   */
  const getCorrelationColor = (correlation) => {
    if (correlation > 0.7) return 'correlation-strong-positive'
    if (correlation > 0.3) return 'correlation-moderate-positive'
    if (correlation > -0.3) return 'correlation-weak'
    if (correlation > -0.7) return 'correlation-moderate-negative'
    return 'correlation-strong-negative'
  }

  /**
   * Get correlation strength label
   */
  const getCorrelationLabel = (correlation) => {
    if (correlation > 0.7) return 'Strong Positive'
    if (correlation > 0.3) return 'Moderate Positive'
    if (correlation > -0.3) return 'Weak'
    if (correlation > -0.7) return 'Moderate Negative'
    return 'Strong Negative'
  }

  // Sort data
  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      let comparison = 0
      
      if (sortBy === 'correlation') {
        comparison = a.correlation - b.correlation
      } else if (sortBy === 'series1') {
        comparison = a.series_id_1.localeCompare(b.series_id_1)
      } else if (sortBy === 'series2') {
        comparison = a.series_id_2.localeCompare(b.series_id_2)
      }
      
      return sortOrder === 'asc' ? comparison : -comparison
    })
    
    return sorted
  }, [data, sortBy, sortOrder])

  /**
   * Handle column header click for sorting
   */
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  return (
    <div className="analytics-view">
      <h3>Correlations</h3>
      <div className="correlations-table-container">
        <table className="correlations-table">
          <thead>
            <tr>
              <th 
                className={sortBy === 'series1' ? 'sorted' : ''}
                onClick={() => handleSort('series1')}
              >
                Series 1 {sortBy === 'series1' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th 
                className={sortBy === 'series2' ? 'sorted' : ''}
                onClick={() => handleSort('series2')}
              >
                Series 2 {sortBy === 'series2' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th 
                className={sortBy === 'correlation' ? 'sorted' : ''}
                onClick={() => handleSort('correlation')}
              >
                Correlation {sortBy === 'correlation' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Strength</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((corr, index) => (
              <tr key={`${corr.series_id_1}-${corr.series_id_2}-${index}`}>
                <td>{corr.series_id_1}</td>
                <td>{corr.series_id_2}</td>
                <td className={`correlation-value ${getCorrelationColor(corr.correlation)}`}>
                  {corr.correlation.toFixed(4)}
                </td>
                <td className={getCorrelationColor(corr.correlation)}>
                  {getCorrelationLabel(corr.correlation)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="correlations-legend">
        <div className="legend-item">
          <span className="legend-color correlation-strong-positive"></span>
          <span>Strong Positive (&gt; 0.7)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color correlation-moderate-positive"></span>
          <span>Moderate Positive (0.3 - 0.7)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color correlation-weak"></span>
          <span>Weak (-0.3 - 0.3)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color correlation-moderate-negative"></span>
          <span>Moderate Negative (-0.7 - -0.3)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color correlation-strong-negative"></span>
          <span>Strong Negative (&lt; -0.7)</span>
        </div>
      </div>
    </div>
  )
}

export default CorrelationsView

