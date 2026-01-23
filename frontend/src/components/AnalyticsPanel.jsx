/**
 * AnalyticsPanel component - Main container for analytics functionality
 * 
 * Features:
 * - Integrates AnalyticsForm with API
 * - Manages analytics state (data, loading, errors)
 * - Renders appropriate visualization components based on analytics types
 * - Handles loading and error states
 */

import { useState } from 'react'
import AnalyticsForm from './AnalyticsForm'
import { fetchAnalytics } from '../services/api'
import {
  StatisticsView,
  GrowthRatesView,
  CorrelationsView,
  MovingAveragesView,
  TimeAggregationsView,
} from './analytics'
import './AnalyticsPanel.css'

/**
 * AnalyticsPanel component
 * @param {Object} props - Component props
 * @param {string[]} props.initialSeriesIds - Initial series IDs to pre-fill in form (default: [])
 */
function AnalyticsPanel({ initialSeriesIds = [] }) {
  // State management
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Handle form submission - fetch analytics from API
   */
  const handleAnalyticsSubmit = async (analyticsRequest) => {
    setLoading(true)
    setError(null)
    setAnalyticsData(null)

    try {
      const response = await fetchAnalytics(analyticsRequest)
      setAnalyticsData(response)
    } catch (err) {
      // Enhanced error handling with user-friendly messages
      let errorMessage = 'Failed to fetch analytics data'
      
      if (err.message) {
        errorMessage = err.message
      } else if (err instanceof TypeError && err.message.includes('fetch')) {
        errorMessage = 'Network error: Unable to connect to the backend server. Please ensure the backend is running.'
      } else if (err.response) {
        // Handle HTTP error responses
        const status = err.response.status
        if (status === 400) {
          errorMessage = 'Invalid request. Please check your input parameters.'
        } else if (status === 404) {
          errorMessage = 'Analytics endpoint not found. Please check the API configuration.'
        } else if (status === 500) {
          errorMessage = 'Server error occurred while processing your request. Please try again later.'
        } else if (status === 503) {
          errorMessage = 'Spark service is unavailable. Please ensure Spark is running and try again.'
        } else {
          errorMessage = `Server error (${status}). Please try again later.`
        }
      }
      
      setError(errorMessage)
      console.error('Analytics error:', err)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Retry the last analytics request
   */
  const handleRetry = () => {
    // Store the last request to retry
    // For now, we'll just clear the error and let user resubmit
    // In a more advanced implementation, we could store the last request
    setError(null)
  }

  /**
   * Handle form reset
   */
  const handleFormReset = () => {
    setAnalyticsData(null)
    setError(null)
  }

  return (
    <div className="analytics-panel">
      <div className="analytics-panel-header">
        <h2>Analytics Dashboard</h2>
        <p className="analytics-panel-description">
          Perform statistical analysis, growth rate calculations, correlations, moving averages, and time-based aggregations on FRED economic data.
        </p>
      </div>

      <div className="analytics-panel-form">
        <AnalyticsForm
          onSubmit={handleAnalyticsSubmit}
          loading={loading}
          initialSeriesIds={initialSeriesIds}
        />
      </div>

      {/* Loading state */}
      {loading && (
        <div className="analytics-loading">
          <div className="loading-spinner"></div>
          <p>Running analytics...</p>
          <p className="loading-hint">This may take a few moments depending on the amount of data.</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="analytics-error">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <h3>Error</h3>
            <p>{error}</p>
            <div className="error-actions">
              <button
                className="error-retry-button"
                onClick={handleRetry}
              >
                Dismiss
              </button>
              {error.includes('Network error') || error.includes('Server error') || error.includes('unavailable') ? (
                <button
                  className="error-retry-button primary"
                  onClick={() => {
                    setError(null)
                    // Scroll to form to encourage retry
                    document.querySelector('.analytics-panel-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                  }}
                >
                  Try Again
                </button>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {analyticsData && !loading && (
        <div className="analytics-results">
          <div className="analytics-results-header">
            <h3>Results</h3>
            <p className="analytics-results-info">
              Analyzed {analyticsData.series_count} series
            </p>
          </div>

          <div className="analytics-results-content">
            {/* Statistics */}
            {analyticsData.statistics && analyticsData.statistics.length > 0 && (
              <StatisticsView data={analyticsData.statistics} />
            )}

            {/* Growth Rates */}
            {analyticsData.growth_rates && analyticsData.growth_rates.length > 0 && (
              <GrowthRatesView data={analyticsData.growth_rates} />
            )}

            {/* Correlations */}
            {analyticsData.correlations && analyticsData.correlations.length > 0 && (
              <CorrelationsView data={analyticsData.correlations} />
            )}

            {/* Moving Averages */}
            {analyticsData.moving_averages && analyticsData.moving_averages.length > 0 && (
              <MovingAveragesView data={analyticsData.moving_averages} />
            )}

            {/* Time Aggregations */}
            {analyticsData.time_aggregations && analyticsData.time_aggregations.length > 0 && (
              <TimeAggregationsView data={analyticsData.time_aggregations} />
            )}

            {/* No results message */}
            {!analyticsData.statistics &&
              !analyticsData.growth_rates &&
              !analyticsData.correlations &&
              !analyticsData.moving_averages &&
              !analyticsData.time_aggregations && (
                <div className="analytics-empty-results">
                  <p>No analytics results to display.</p>
                  <p className="analytics-empty-hint">
                    Select one or more analytics types and submit the form to see results.
                  </p>
                </div>
              )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalyticsPanel

