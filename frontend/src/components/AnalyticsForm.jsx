/**
 * AnalyticsForm component - Form for configuring and submitting analytics requests
 * 
 * Features:
 * - Multi-series selection (comma-separated input)
 * - Analytics type checkboxes
 * - Conditional parameter inputs based on selected analytics types
 * - Form validation
 * - Submit button with loading state
 */

import { useState, useEffect } from 'react'
import './AnalyticsForm.css'

/**
 * AnalyticsForm component
 * @param {Object} props - Component props
 * @param {Function} props.onSubmit - Callback when form is submitted with analytics request
 * @param {boolean} props.loading - Whether analytics request is in progress
 * @param {string[]} props.initialSeriesIds - Initial series IDs to pre-fill (default: [])
 */
function AnalyticsForm({ onSubmit, loading = false, initialSeriesIds = [] }) {
  // Form state
  const [seriesIdsInput, setSeriesIdsInput] = useState('')
  const [analyticsTypes, setAnalyticsTypes] = useState([])
  const [limit, setLimit] = useState(100)
  const [sortOrder, setSortOrder] = useState('desc')
  const [useCache, setUseCache] = useState(true)
  
  // Moving averages parameters
  const [movingAverageWindow, setMovingAverageWindow] = useState(7)
  const [movingAverageType, setMovingAverageType] = useState('sma')
  
  // Time aggregations parameters
  const [timeAggregationPeriod, setTimeAggregationPeriod] = useState('monthly')
  const [timeAggregationFunction, setTimeAggregationFunction] = useState('mean')
  
  // Validation errors
  const [errors, setErrors] = useState({})

  // Initialize series IDs from props
  useEffect(() => {
    if (initialSeriesIds && initialSeriesIds.length > 0) {
      setSeriesIdsInput(initialSeriesIds.join(', '))
    }
  }, [initialSeriesIds])

  /**
   * Handle series IDs input change
   */
  const handleSeriesIdsChange = (e) => {
    setSeriesIdsInput(e.target.value)
    // Clear series IDs error when user types
    if (errors.seriesIds) {
      setErrors(prev => ({ ...prev, seriesIds: null }))
    }
  }

  /**
   * Handle analytics type checkbox toggle
   */
  const handleAnalyticsTypeToggle = (type) => {
    setAnalyticsTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type)
      } else {
        return [...prev, type]
      }
    })
    // Clear analytics types error when user selects
    if (errors.analyticsTypes) {
      setErrors(prev => ({ ...prev, analyticsTypes: null }))
    }
  }

  /**
   * Validate form data
   */
  const validateForm = () => {
    const newErrors = {}

    // Parse series IDs
    const parsedSeriesIds = seriesIdsInput
      .split(',')
      .map(id => id.trim())
      .filter(id => id.length > 0)
      .map(id => id.toUpperCase())

    // Validate series IDs
    if (parsedSeriesIds.length === 0) {
      newErrors.seriesIds = 'At least one series ID is required'
    } else if (parsedSeriesIds.length > 50) {
      newErrors.seriesIds = 'Maximum 50 series IDs allowed'
    } else {
      // Validate each series ID format
      for (const id of parsedSeriesIds) {
        if (!id.replace('_', '').replace('-', '').match(/^[A-Z0-9_\-]+$/)) {
          newErrors.seriesIds = `Invalid series ID format: ${id}`
          break
        }
      }
    }

    // Validate analytics types
    if (analyticsTypes.length === 0) {
      newErrors.analyticsTypes = 'At least one analytics type is required'
    }

    // Validate correlations requires 2+ series
    if (analyticsTypes.includes('correlations') && parsedSeriesIds.length < 2) {
      newErrors.correlations = 'Correlations require at least 2 series'
    }

    // Validate moving averages parameters
    if (analyticsTypes.includes('moving_averages')) {
      if (!movingAverageWindow || movingAverageWindow < 2 || movingAverageWindow > 365) {
        newErrors.movingAverageWindow = 'Window size must be between 2 and 365'
      }
      if (!movingAverageType || !['sma', 'ema'].includes(movingAverageType)) {
        newErrors.movingAverageType = 'Moving average type is required'
      }
    }

    // Validate time aggregations parameters
    if (analyticsTypes.includes('time_aggregations')) {
      if (!timeAggregationPeriod || !['daily', 'weekly', 'monthly', 'quarterly', 'yearly'].includes(timeAggregationPeriod)) {
        newErrors.timeAggregationPeriod = 'Time aggregation period is required'
      }
      if (!timeAggregationFunction || !['mean', 'sum', 'min', 'max', 'first', 'last'].includes(timeAggregationFunction)) {
        newErrors.timeAggregationFunction = 'Time aggregation function is required'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    // Parse series IDs
    const parsedSeriesIds = seriesIdsInput
      .split(',')
      .map(id => id.trim())
      .filter(id => id.length > 0)
      .map(id => id.toUpperCase())

    // Build analytics request
    const analyticsRequest = {
      series_ids: parsedSeriesIds,
      analytics_types: analyticsTypes,
      limit: limit,
      sort_order: sortOrder,
      use_cache: useCache,
    }

    // Add conditional parameters
    if (analyticsTypes.includes('moving_averages')) {
      analyticsRequest.moving_average_window = movingAverageWindow
      analyticsRequest.moving_average_type = movingAverageType
    }

    if (analyticsTypes.includes('time_aggregations')) {
      analyticsRequest.time_aggregation_period = timeAggregationPeriod
      analyticsRequest.time_aggregation_function = timeAggregationFunction
    }

    // Call onSubmit callback
    onSubmit(analyticsRequest)
  }

  /**
   * Handle form reset
   */
  const handleReset = () => {
    setSeriesIdsInput('')
    setAnalyticsTypes([])
    setLimit(100)
    setSortOrder('desc')
    setUseCache(true)
    setMovingAverageWindow(7)
    setMovingAverageType('sma')
    setTimeAggregationPeriod('monthly')
    setTimeAggregationFunction('mean')
    setErrors({})
  }

  return (
    <form className="analytics-form" onSubmit={handleSubmit}>
      <div className="form-section">
        <h3>Series Selection</h3>
        <div className="form-group">
          <label htmlFor="seriesIds">
            Series IDs <span className="required">*</span>
          </label>
          <input
            id="seriesIds"
            type="text"
            value={seriesIdsInput}
            onChange={handleSeriesIdsChange}
            placeholder="e.g., GDP, UNRATE, CPIAUCSL"
            disabled={loading}
            className={errors.seriesIds ? 'error' : ''}
          />
          <small className="help-text">
            Enter series IDs separated by commas (e.g., GDP, UNRATE)
          </small>
          {errors.seriesIds && (
            <div className="error-message">{errors.seriesIds}</div>
          )}
        </div>
      </div>

      <div className="form-section">
        <h3>Analytics Types <span className="required">*</span></h3>
        <div className="form-group">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('statistics')}
                onChange={() => handleAnalyticsTypeToggle('statistics')}
                disabled={loading}
              />
              <span>Statistics</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('growth_rates')}
                onChange={() => handleAnalyticsTypeToggle('growth_rates')}
                disabled={loading}
              />
              <span>Growth Rates</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('correlations')}
                onChange={() => handleAnalyticsTypeToggle('correlations')}
                disabled={loading}
              />
              <span>Correlations</span>
              {seriesIdsInput.split(',').filter(id => id.trim()).length < 2 && (
                <small className="warning-text"> (requires 2+ series)</small>
              )}
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('moving_averages')}
                onChange={() => handleAnalyticsTypeToggle('moving_averages')}
                disabled={loading}
              />
              <span>Moving Averages</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('time_aggregations')}
                onChange={() => handleAnalyticsTypeToggle('time_aggregations')}
                disabled={loading}
              />
              <span>Time Aggregations</span>
            </label>
          </div>
          {errors.analyticsTypes && (
            <div className="error-message">{errors.analyticsTypes}</div>
          )}
          {errors.correlations && (
            <div className="error-message">{errors.correlations}</div>
          )}
        </div>
      </div>

      <div className="form-section">
        <h3>Common Parameters</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="limit">Limit</label>
            <input
              id="limit"
              type="number"
              min="1"
              max="1000"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
              disabled={loading}
            />
            <small className="help-text">Maximum observations per series (1-1000)</small>
          </div>
          <div className="form-group">
            <label htmlFor="sortOrder">Sort Order</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="sortOrder"
                  value="asc"
                  checked={sortOrder === 'asc'}
                  onChange={(e) => setSortOrder(e.target.value)}
                  disabled={loading}
                />
                <span>Ascending</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="sortOrder"
                  value="desc"
                  checked={sortOrder === 'desc'}
                  onChange={(e) => setSortOrder(e.target.value)}
                  disabled={loading}
                />
                <span>Descending</span>
              </label>
            </div>
          </div>
        </div>
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useCache}
              onChange={(e) => setUseCache(e.target.checked)}
              disabled={loading}
            />
            <span>Use Cache</span>
          </label>
          <small className="help-text">Use cached data if available</small>
        </div>
      </div>

      {analyticsTypes.includes('moving_averages') && (
        <div className="form-section">
          <h3>Moving Averages Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="movingAverageWindow">
                Window Size <span className="required">*</span>
              </label>
              <input
                id="movingAverageWindow"
                type="number"
                min="2"
                max="365"
                value={movingAverageWindow}
                onChange={(e) => setMovingAverageWindow(parseInt(e.target.value) || 7)}
                disabled={loading}
                className={errors.movingAverageWindow ? 'error' : ''}
              />
              <small className="help-text">Window size (2-365)</small>
              {errors.movingAverageWindow && (
                <div className="error-message">{errors.movingAverageWindow}</div>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="movingAverageType">
                Type <span className="required">*</span>
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="movingAverageType"
                    value="sma"
                    checked={movingAverageType === 'sma'}
                    onChange={(e) => setMovingAverageType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Simple Moving Average (SMA)</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="movingAverageType"
                    value="ema"
                    checked={movingAverageType === 'ema'}
                    onChange={(e) => setMovingAverageType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Exponential Moving Average (EMA)</span>
                </label>
              </div>
              {errors.movingAverageType && (
                <div className="error-message">{errors.movingAverageType}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {analyticsTypes.includes('time_aggregations') && (
        <div className="form-section">
          <h3>Time Aggregations Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="timeAggregationPeriod">
                Period <span className="required">*</span>
              </label>
              <select
                id="timeAggregationPeriod"
                value={timeAggregationPeriod}
                onChange={(e) => setTimeAggregationPeriod(e.target.value)}
                disabled={loading}
                className={errors.timeAggregationPeriod ? 'error' : ''}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
              </select>
              {errors.timeAggregationPeriod && (
                <div className="error-message">{errors.timeAggregationPeriod}</div>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="timeAggregationFunction">
                Function <span className="required">*</span>
              </label>
              <select
                id="timeAggregationFunction"
                value={timeAggregationFunction}
                onChange={(e) => setTimeAggregationFunction(e.target.value)}
                disabled={loading}
                className={errors.timeAggregationFunction ? 'error' : ''}
              >
                <option value="mean">Mean</option>
                <option value="sum">Sum</option>
                <option value="min">Min</option>
                <option value="max">Max</option>
                <option value="first">First</option>
                <option value="last">Last</option>
              </select>
              {errors.timeAggregationFunction && (
                <div className="error-message">{errors.timeAggregationFunction}</div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button type="submit" disabled={loading} className="submit-button">
          {loading ? (
            <>
              <span className="spinner"></span>
              Running Analytics...
            </>
          ) : (
            'Run Analytics'
          )}
        </button>
        <button type="button" onClick={handleReset} disabled={loading} className="reset-button">
          Reset
        </button>
      </div>
    </form>
  )
}

export default AnalyticsForm

