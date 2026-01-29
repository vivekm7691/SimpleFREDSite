/**
 * AdvancedAnalyticsPanel component - Main container for advanced analytics functionality
 * 
 * Features:
 * - Integrates AdvancedAnalyticsForm with API
 * - Manages advanced analytics state (data, loading, errors)
 * - Renders appropriate visualization components based on analytics types
 * - Handles loading and error states
 */

import { useState } from 'react'
import AdvancedAnalyticsForm from './AdvancedAnalyticsForm'
import { fetchAdvancedAnalytics } from '../services/api'
import {
  ForecastsView,
  TrendsView,
  AnomaliesView,
  SeasonalDecompositionView,
  VolatilityView,
} from './advanced-analytics'
import './AdvancedAnalyticsPanel.css'

/**
 * AdvancedAnalyticsPanel component
 * @param {Object} props - Component props
 * @param {string[]} props.initialSeriesIds - Initial series IDs to pre-fill in form (default: [])
 */
function AdvancedAnalyticsPanel({ initialSeriesIds = [] }) {
  // State management
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Handle form submission - fetch advanced analytics from API
   */
  const handleAdvancedAnalyticsSubmit = async (advancedAnalyticsRequest) => {
    setLoading(true)
    setError(null)
    setAnalyticsData(null)

    try {
      const response = await fetchAdvancedAnalytics(advancedAnalyticsRequest)
      setAnalyticsData(response)
    } catch (err) {
      // Enhanced error handling with user-friendly messages
      let errorMessage = 'Failed to fetch advanced analytics data'
      
      if (err.message) {
        errorMessage = err.message
        // Check for specific error patterns in the message
        if (err.message.includes('Failed to connect') || err.message.includes('Network error')) {
          errorMessage = 'Network error: Unable to connect to the backend server. Please ensure the backend is running and accessible.'
        } else if (err.message.includes('HTTP error! status: 400')) {
          errorMessage = 'Invalid request. Please check your input parameters and try again.'
        } else if (err.message.includes('HTTP error! status: 404')) {
          errorMessage = 'Advanced analytics endpoint not found. Please check the API configuration.'
        } else if (err.message.includes('HTTP error! status: 500')) {
          errorMessage = 'Server error occurred while processing your request. Please try again later.'
        } else if (err.message.includes('HTTP error! status: 503') || err.message.includes('Spark service is not available')) {
          errorMessage = 'Spark service is unavailable. Please ensure Spark is running and try again.'
        } else if (err.message.includes('timeout') || err.message.includes('Timeout')) {
          errorMessage = 'Request timed out. The server may be processing a large amount of data. Please try again with fewer series or a smaller limit.'
        }
      } else if (err instanceof TypeError && err.message && err.message.includes('fetch')) {
        errorMessage = 'Network error: Unable to connect to the backend server. Please ensure the backend is running and accessible.'
      }
      
      setError(errorMessage)
      console.error('Advanced analytics error:', err)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Retry the last analytics request
   */
  const handleRetry = () => {
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
    <div className="advanced-analytics-panel">
      <div className="advanced-analytics-panel-header">
        <h2>Advanced Analytics Dashboard</h2>
        <p className="advanced-analytics-panel-description">
          Perform advanced analytics including forecasting, anomaly detection, trend analysis, seasonal decomposition, and volatility analysis on FRED economic data.
        </p>
      </div>

      <div className="advanced-analytics-panel-form">
        <AdvancedAnalyticsForm
          onSubmit={handleAdvancedAnalyticsSubmit}
          loading={loading}
          initialSeriesIds={initialSeriesIds}
        />
      </div>

      {/* Loading state */}
      {loading && (
        <div className="advanced-analytics-loading">
          <div className="loading-spinner"></div>
          <p>Running advanced analytics...</p>
          <p className="loading-hint">This may take a few moments depending on the amount of data and selected analytics types.</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="advanced-analytics-error">
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
                    document.querySelector('.advanced-analytics-panel-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
        <div className="advanced-analytics-results">
          <div className="advanced-analytics-results-header">
            <h3>Results</h3>
            <p className="advanced-analytics-results-info">
              Analyzed {analyticsData.series_count} series
            </p>
          </div>

          <div className="advanced-analytics-results-content">
            {/* Forecasts */}
            {analyticsData.forecasts && analyticsData.forecasts.length > 0 && (
              <ForecastsView data={analyticsData.forecasts} />
            )}

            {/* Trends */}
            {analyticsData.trends && analyticsData.trends.length > 0 && (
              <TrendsView data={analyticsData.trends} />
            )}

            {/* Anomalies */}
            {analyticsData.anomalies && analyticsData.anomalies.length > 0 && (
              <AnomaliesView data={analyticsData.anomalies} />
            )}

            {/* Seasonal Decomposition */}
            {analyticsData.seasonal_decompositions && analyticsData.seasonal_decompositions.length > 0 && (
              <SeasonalDecompositionView data={analyticsData.seasonal_decompositions} />
            )}

            {/* Volatility */}
            {analyticsData.volatility && analyticsData.volatility.length > 0 && (
              <VolatilityView data={analyticsData.volatility} />
            )}

            {/* No results message */}
            {!analyticsData.forecasts &&
              !analyticsData.trends &&
              !analyticsData.anomalies &&
              !analyticsData.seasonal_decompositions &&
              !analyticsData.volatility && (
                <div className="advanced-analytics-empty-results">
                  <p>No advanced analytics results to display.</p>
                  <p className="advanced-analytics-empty-hint">
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

export default AdvancedAnalyticsPanel

