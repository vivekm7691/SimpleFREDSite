/**
 * AnomaliesView component - Displays detected anomalies
 * 
 * Features:
 * - Table showing anomalous data points with severity indicators
 * - Filter by severity and detection method
 */

import { useState, useMemo } from 'react'
import './AdvancedAnalytics.css'

/**
 * AnomaliesView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of Anomaly objects
 */
function AnomaliesView({ data }) {
  const [severityFilter, setSeverityFilter] = useState('all')
  const [methodFilter, setMethodFilter] = useState('all')

  if (!data || data.length === 0) {
    return (
      <div className="advanced-analytics-view">
        <h3>Anomalies</h3>
        <div className="advanced-analytics-empty">
          <p>No anomalies detected</p>
        </div>
      </div>
    )
  }

  // Filter data
  const filteredData = useMemo(() => {
    return data.filter(item => {
      const severityMatch = severityFilter === 'all' || item.severity === severityFilter
      const methodMatch = methodFilter === 'all' || item.detection_method === methodFilter
      return severityMatch && methodMatch
    })
  }, [data, severityFilter, methodFilter])

  // Get unique severities and methods
  const severities = useMemo(() => {
    return [...new Set(data.map(item => item.severity))]
  }, [data])

  const methods = useMemo(() => {
    return [...new Set(data.map(item => item.detection_method))]
  }, [data])

  /**
   * Get severity badge class
   */
  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'high':
        return 'severity-high'
      case 'medium':
        return 'severity-medium'
      default:
        return 'severity-low'
    }
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
    <div className="advanced-analytics-view">
      <div className="advanced-analytics-header">
        <h3>Anomaly Detection</h3>
        <div className="filter-controls">
          <label>Filter by severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">All Severities</option>
            {severities.map(severity => (
              <option key={severity} value={severity}>
                {severity.charAt(0).toUpperCase() + severity.slice(1)}
              </option>
            ))}
          </select>
          <label>Filter by method:</label>
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
          >
            <option value="all">All Methods</option>
            {methods.map(method => (
              <option key={method} value={method}>
                {method.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="anomalies-table-container">
        <table className="anomalies-table">
          <thead>
            <tr>
              <th>Series ID</th>
              <th>Date</th>
              <th>Value</th>
              <th>Expected Value</th>
              <th>Deviation</th>
              <th>Method</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((anomaly, index) => (
              <tr key={index}>
                <td>{anomaly.series_id}</td>
                <td>{anomaly.date}</td>
                <td>{formatNumber(anomaly.value)}</td>
                <td>{formatNumber(anomaly.expected_value)}</td>
                <td>{formatNumber(anomaly.deviation)}</td>
                <td>{anomaly.detection_method.replace('_', ' ')}</td>
                <td>
                  <span className={`severity-badge ${getSeverityClass(anomaly.severity)}`}>
                    {anomaly.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="advanced-analytics-info">
        <p>Showing {filteredData.length} of {data.length} anomal{data.length !== 1 ? 'ies' : 'y'}</p>
      </div>
    </div>
  )
}

export default AnomaliesView

