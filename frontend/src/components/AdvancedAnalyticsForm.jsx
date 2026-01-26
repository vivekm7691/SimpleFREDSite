/**
 * AdvancedAnalyticsForm component - Form for configuring and submitting advanced analytics requests
 * 
 * Features:
 * - Multi-series selection (comma-separated input)
 * - Advanced analytics type checkboxes
 * - Conditional parameter inputs based on selected analytics types
 * - Form validation
 * - Submit button with loading state
 */

import { useState, useEffect } from 'react'
import './AdvancedAnalyticsForm.css'

/**
 * AdvancedAnalyticsForm component
 * @param {Object} props - Component props
 * @param {Function} props.onSubmit - Callback when form is submitted with advanced analytics request
 * @param {boolean} props.loading - Whether advanced analytics request is in progress
 * @param {string[]} props.initialSeriesIds - Initial series IDs to pre-fill (default: [])
 */
function AdvancedAnalyticsForm({ onSubmit, loading = false, initialSeriesIds = [] }) {
  // Form state
  const [seriesIdsInput, setSeriesIdsInput] = useState('')
  const [analyticsTypes, setAnalyticsTypes] = useState([])
  const [limit, setLimit] = useState(100)
  const [sortOrder, setSortOrder] = useState('desc')
  const [useCache, setUseCache] = useState(true)
  
  // Forecasting parameters
  const [forecastHorizon, setForecastHorizon] = useState(12)
  const [forecastMethod, setForecastMethod] = useState('linear_regression')
  
  // Anomaly detection parameters
  const [anomalyMethod, setAnomalyMethod] = useState('z_score')
  const [anomalyThreshold, setAnomalyThreshold] = useState(3.0)
  
  // Trend analysis parameters
  const [trendType, setTrendType] = useState('linear')
  const [polynomialDegree, setPolynomialDegree] = useState(2)
  
  // Seasonal decomposition parameters
  const [decompositionType, setDecompositionType] = useState('additive')
  const [seasonalPeriod, setSeasonalPeriod] = useState(12)
  
  // Volatility parameters
  const [volatilityWindow, setVolatilityWindow] = useState(30)
  
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

    // Validate forecasting parameters
    if (analyticsTypes.includes('forecasts')) {
      if (!forecastHorizon || forecastHorizon < 1 || forecastHorizon > 120) {
        newErrors.forecastHorizon = 'Forecast horizon must be between 1 and 120'
      }
      if (!forecastMethod || !['arima', 'exponential_smoothing', 'linear_regression'].includes(forecastMethod)) {
        newErrors.forecastMethod = 'Forecast method is required'
      }
    }

    // Validate anomaly detection parameters
    if (analyticsTypes.includes('anomalies')) {
      if (!anomalyMethod || !['z_score', 'iqr', 'moving_average'].includes(anomalyMethod)) {
        newErrors.anomalyMethod = 'Anomaly detection method is required'
      }
      if (anomalyMethod === 'z_score' && (!anomalyThreshold || anomalyThreshold < 1.0 || anomalyThreshold > 10.0)) {
        newErrors.anomalyThreshold = 'Anomaly threshold must be between 1.0 and 10.0'
      }
    }

    // Validate trend analysis parameters
    if (analyticsTypes.includes('trends')) {
      if (!trendType || !['linear', 'polynomial'].includes(trendType)) {
        newErrors.trendType = 'Trend type is required'
      }
      if (trendType === 'polynomial' && (!polynomialDegree || polynomialDegree < 2 || polynomialDegree > 5)) {
        newErrors.polynomialDegree = 'Polynomial degree must be between 2 and 5'
      }
    }

    // Validate seasonal decomposition parameters
    if (analyticsTypes.includes('seasonal_decomposition')) {
      if (!decompositionType || !['additive', 'multiplicative'].includes(decompositionType)) {
        newErrors.decompositionType = 'Decomposition type is required'
      }
      if (!seasonalPeriod || seasonalPeriod < 2 || seasonalPeriod > 365) {
        newErrors.seasonalPeriod = 'Seasonal period must be between 2 and 365'
      }
    }

    // Validate volatility parameters
    if (analyticsTypes.includes('volatility')) {
      if (!volatilityWindow || volatilityWindow < 2 || volatilityWindow > 365) {
        newErrors.volatilityWindow = 'Volatility window must be between 2 and 365'
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

    // Build advanced analytics request
    const advancedAnalyticsRequest = {
      series_ids: parsedSeriesIds,
      analytics_types: analyticsTypes,
      limit: limit,
      sort_order: sortOrder,
      use_cache: useCache,
    }

    // Add conditional parameters
    if (analyticsTypes.includes('forecasts')) {
      advancedAnalyticsRequest.forecast_horizon = forecastHorizon
      advancedAnalyticsRequest.forecast_method = forecastMethod
    }

    if (analyticsTypes.includes('anomalies')) {
      advancedAnalyticsRequest.anomaly_method = anomalyMethod
      if (anomalyMethod === 'z_score') {
        advancedAnalyticsRequest.anomaly_threshold = anomalyThreshold
      }
    }

    if (analyticsTypes.includes('trends')) {
      advancedAnalyticsRequest.trend_type = trendType
      if (trendType === 'polynomial') {
        advancedAnalyticsRequest.polynomial_degree = polynomialDegree
      }
    }

    if (analyticsTypes.includes('seasonal_decomposition')) {
      advancedAnalyticsRequest.decomposition_type = decompositionType
      advancedAnalyticsRequest.seasonal_period = seasonalPeriod
    }

    if (analyticsTypes.includes('volatility')) {
      advancedAnalyticsRequest.volatility_window = volatilityWindow
    }

    // Call onSubmit callback
    onSubmit(advancedAnalyticsRequest)
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
    setForecastHorizon(12)
    setForecastMethod('linear_regression')
    setAnomalyMethod('z_score')
    setAnomalyThreshold(3.0)
    setTrendType('linear')
    setPolynomialDegree(2)
    setDecompositionType('additive')
    setSeasonalPeriod(12)
    setVolatilityWindow(30)
    setErrors({})
  }

  return (
    <form className="advanced-analytics-form" onSubmit={handleSubmit}>
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
        <h3>Advanced Analytics Types <span className="required">*</span></h3>
        <div className="form-group">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('forecasts')}
                onChange={() => handleAnalyticsTypeToggle('forecasts')}
                disabled={loading}
              />
              <span>Forecasts</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('anomalies')}
                onChange={() => handleAnalyticsTypeToggle('anomalies')}
                disabled={loading}
              />
              <span>Anomaly Detection</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('trends')}
                onChange={() => handleAnalyticsTypeToggle('trends')}
                disabled={loading}
              />
              <span>Trend Analysis</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('seasonal_decomposition')}
                onChange={() => handleAnalyticsTypeToggle('seasonal_decomposition')}
                disabled={loading}
              />
              <span>Seasonal Decomposition</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={analyticsTypes.includes('volatility')}
                onChange={() => handleAnalyticsTypeToggle('volatility')}
                disabled={loading}
              />
              <span>Volatility Analysis</span>
            </label>
          </div>
          {errors.analyticsTypes && (
            <div className="error-message">{errors.analyticsTypes}</div>
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

      {analyticsTypes.includes('forecasts') && (
        <div className="form-section">
          <h3>Forecasting Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="forecastHorizon">
                Forecast Horizon <span className="required">*</span>
              </label>
              <input
                id="forecastHorizon"
                type="number"
                min="1"
                max="120"
                value={forecastHorizon}
                onChange={(e) => setForecastHorizon(parseInt(e.target.value) || 12)}
                disabled={loading}
                className={errors.forecastHorizon ? 'error' : ''}
              />
              <small className="help-text">Number of periods to forecast (1-120)</small>
              {errors.forecastHorizon && (
                <div className="error-message">{errors.forecastHorizon}</div>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="forecastMethod">
                Forecast Method <span className="required">*</span>
              </label>
              <select
                id="forecastMethod"
                value={forecastMethod}
                onChange={(e) => setForecastMethod(e.target.value)}
                disabled={loading}
                className={errors.forecastMethod ? 'error' : ''}
              >
                <option value="linear_regression">Linear Regression</option>
                <option value="arima">ARIMA</option>
                <option value="exponential_smoothing">Exponential Smoothing</option>
              </select>
              {errors.forecastMethod && (
                <div className="error-message">{errors.forecastMethod}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {analyticsTypes.includes('anomalies') && (
        <div className="form-section">
          <h3>Anomaly Detection Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="anomalyMethod">
                Detection Method <span className="required">*</span>
              </label>
              <select
                id="anomalyMethod"
                value={anomalyMethod}
                onChange={(e) => setAnomalyMethod(e.target.value)}
                disabled={loading}
                className={errors.anomalyMethod ? 'error' : ''}
              >
                <option value="z_score">Z-Score</option>
                <option value="iqr">IQR (Interquartile Range)</option>
                <option value="moving_average">Moving Average Deviation</option>
              </select>
              {errors.anomalyMethod && (
                <div className="error-message">{errors.anomalyMethod}</div>
              )}
            </div>
            {anomalyMethod === 'z_score' && (
              <div className="form-group">
                <label htmlFor="anomalyThreshold">
                  Z-Score Threshold <span className="required">*</span>
                </label>
                <input
                  id="anomalyThreshold"
                  type="number"
                  min="1.0"
                  max="10.0"
                  step="0.1"
                  value={anomalyThreshold}
                  onChange={(e) => setAnomalyThreshold(parseFloat(e.target.value) || 3.0)}
                  disabled={loading}
                  className={errors.anomalyThreshold ? 'error' : ''}
                />
                <small className="help-text">Threshold for anomaly detection (1.0-10.0)</small>
                {errors.anomalyThreshold && (
                  <div className="error-message">{errors.anomalyThreshold}</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {analyticsTypes.includes('trends') && (
        <div className="form-section">
          <h3>Trend Analysis Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="trendType">
                Trend Type <span className="required">*</span>
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="trendType"
                    value="linear"
                    checked={trendType === 'linear'}
                    onChange={(e) => setTrendType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Linear</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="trendType"
                    value="polynomial"
                    checked={trendType === 'polynomial'}
                    onChange={(e) => setTrendType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Polynomial</span>
                </label>
              </div>
              {errors.trendType && (
                <div className="error-message">{errors.trendType}</div>
              )}
            </div>
            {trendType === 'polynomial' && (
              <div className="form-group">
                <label htmlFor="polynomialDegree">
                  Polynomial Degree <span className="required">*</span>
                </label>
                <input
                  id="polynomialDegree"
                  type="number"
                  min="2"
                  max="5"
                  value={polynomialDegree}
                  onChange={(e) => setPolynomialDegree(parseInt(e.target.value) || 2)}
                  disabled={loading}
                  className={errors.polynomialDegree ? 'error' : ''}
                />
                <small className="help-text">Degree of polynomial (2-5)</small>
                {errors.polynomialDegree && (
                  <div className="error-message">{errors.polynomialDegree}</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {analyticsTypes.includes('seasonal_decomposition') && (
        <div className="form-section">
          <h3>Seasonal Decomposition Parameters</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="decompositionType">
                Decomposition Type <span className="required">*</span>
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="decompositionType"
                    value="additive"
                    checked={decompositionType === 'additive'}
                    onChange={(e) => setDecompositionType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Additive</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="decompositionType"
                    value="multiplicative"
                    checked={decompositionType === 'multiplicative'}
                    onChange={(e) => setDecompositionType(e.target.value)}
                    disabled={loading}
                  />
                  <span>Multiplicative</span>
                </label>
              </div>
              {errors.decompositionType && (
                <div className="error-message">{errors.decompositionType}</div>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="seasonalPeriod">
                Seasonal Period <span className="required">*</span>
              </label>
              <input
                id="seasonalPeriod"
                type="number"
                min="2"
                max="365"
                value={seasonalPeriod}
                onChange={(e) => setSeasonalPeriod(parseInt(e.target.value) || 12)}
                disabled={loading}
                className={errors.seasonalPeriod ? 'error' : ''}
              />
              <small className="help-text">Seasonal period (e.g., 12 for monthly data)</small>
              {errors.seasonalPeriod && (
                <div className="error-message">{errors.seasonalPeriod}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {analyticsTypes.includes('volatility') && (
        <div className="form-section">
          <h3>Volatility Analysis Parameters</h3>
          <div className="form-group">
            <label htmlFor="volatilityWindow">
              Rolling Window Size <span className="required">*</span>
            </label>
            <input
              id="volatilityWindow"
              type="number"
              min="2"
              max="365"
              value={volatilityWindow}
              onChange={(e) => setVolatilityWindow(parseInt(e.target.value) || 30)}
              disabled={loading}
              className={errors.volatilityWindow ? 'error' : ''}
            />
            <small className="help-text">Rolling window size for volatility calculation (2-365)</small>
            {errors.volatilityWindow && (
              <div className="error-message">{errors.volatilityWindow}</div>
            )}
          </div>
        </div>
      )}

      <div className="form-actions">
        <button type="submit" disabled={loading} className="submit-button">
          {loading ? (
            <>
              <span className="spinner"></span>
              Running Advanced Analytics...
            </>
          ) : (
            'Run Advanced Analytics'
          )}
        </button>
        <button type="button" onClick={handleReset} disabled={loading} className="reset-button">
          Reset
        </button>
      </div>
    </form>
  )
}

export default AdvancedAnalyticsForm

