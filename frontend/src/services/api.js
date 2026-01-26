/**
 * API client for communicating with the backend
 */

// Get API base URL - works in both Vite and Jest environments
// Vite exposes env vars via both import.meta.env and process.env
// Jest can use process.env or global.import.meta (set up in jest.setup.js)
let API_BASE_URL = 'http://localhost:8000'

// Priority 1: Use global.import.meta (set up in jest.setup.js for tests)
if (typeof global !== 'undefined' && global.import && global.import.meta && global.import.meta.env && global.import.meta.env.VITE_API_BASE_URL) {
  API_BASE_URL = global.import.meta.env.VITE_API_BASE_URL
} 
// Priority 2: Use process.env (works in both Jest and Vite)
else if (typeof process !== 'undefined' && process.env && process.env.VITE_API_BASE_URL) {
  API_BASE_URL = process.env.VITE_API_BASE_URL
}

/**
 * Fetch FRED data by series ID
 * @param {string} seriesId - The FRED series ID to fetch
 * @returns {Promise<Object>} The FRED data
 */
export async function fetchFREDData(seriesId) {
  const response = await fetch(`${API_BASE_URL}/api/fred/fetch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ series_id: seriesId }),
  })

  if (!response.ok) {
    let error
    try {
      error = await response.json()
    } catch {
      // If JSON parsing fails, use HTTP status message
      error = {}
    }
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * Summarize data using Google Gemini
 * @param {Object} data - The data to summarize
 * @returns {Promise<string>} The summary text
 */
export async function summarizeData(data) {
  const response = await fetch(`${API_BASE_URL}/api/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ data }),
  })

  if (!response.ok) {
    let error
    try {
      error = await response.json()
    } catch {
      // If JSON parsing fails, use HTTP status message
      error = {}
    }
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  const result = await response.json()
  // Handle both string and object responses
  if (typeof result === 'string') {
    return result
  }
  return result.summary || result
}

/**
 * Fetch all available categories with series counts
 * @returns {Promise<Object>} CategoryResponse with list of categories
 */
export async function fetchCategories() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/categories`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch {
        // If JSON parsing fails, use HTTP status message
        error = {}
      }
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    // Handle network errors (e.g., backend not running, CORS issues)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to backend at ${API_BASE_URL}. Please ensure the backend server is running.`
      )
    }
    // Re-throw other errors
    throw error
  }
}

/**
 * Fetch series list for a specific category
 * @param {string} categoryId - The category identifier (e.g., 'employment', 'inflation')
 * @param {string} [searchTerm] - Optional search term to filter series within the category
 * @returns {Promise<Object>} CategorySeriesResponse with series list
 */
export async function fetchCategorySeries(categoryId, searchTerm = null) {
  // Build URL with optional search query parameter
  let url = `${API_BASE_URL}/api/categories/${encodeURIComponent(categoryId)}`
  if (searchTerm) {
    const params = new URLSearchParams({ q: searchTerm })
    url += `?${params.toString()}`
  }

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    let error
    try {
      error = await response.json()
    } catch {
      // If JSON parsing fails, use HTTP status message
      error = {}
    }
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * Search for series within a category
 * @param {string} categoryId - The category identifier
 * @param {string} searchTerm - Search term to filter series
 * @returns {Promise<Object>} CategorySeriesResponse with filtered series list
 */
export async function searchCategorySeries(categoryId, searchTerm) {
  return fetchCategorySeries(categoryId, searchTerm)
}

/**
 * Fetch analytics for one or more FRED series
 * @param {Object} analyticsRequest - Analytics request parameters
 * @param {string[]} analyticsRequest.series_ids - Array of series IDs
 * @param {string[]} analyticsRequest.analytics_types - Array of analytics types
 * @param {number} analyticsRequest.limit - Maximum observations per series
 * @param {string} analyticsRequest.sort_order - Sort order ('asc' or 'desc')
 * @param {boolean} analyticsRequest.use_cache - Whether to use cached data
 * @param {number} [analyticsRequest.moving_average_window] - Window size for moving averages
 * @param {string} [analyticsRequest.moving_average_type] - 'sma' or 'ema'
 * @param {string} [analyticsRequest.time_aggregation_period] - 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
 * @param {string} [analyticsRequest.time_aggregation_function] - 'mean', 'sum', 'min', 'max', 'first', 'last'
 * @returns {Promise<Object>} Analytics response
 */
export async function fetchAnalytics(analyticsRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/spark/analytics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(analyticsRequest),
    })

    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch {
        // If JSON parsing fails, use HTTP status message
        error = {}
      }
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    // Handle network errors (e.g., backend not running, CORS issues)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to backend at ${API_BASE_URL}. Please ensure the backend server is running.`
      )
    }
    // Re-throw other errors
    throw error
  }
}

/**
 * Fetch advanced analytics for one or more FRED series
 * @param {Object} advancedAnalyticsRequest - Advanced analytics request parameters
 * @param {string[]} advancedAnalyticsRequest.series_ids - Array of series IDs
 * @param {string[]} advancedAnalyticsRequest.analytics_types - Array of analytics types: 'forecasts', 'anomalies', 'trends', 'seasonal_decomposition', 'volatility'
 * @param {number} advancedAnalyticsRequest.limit - Maximum observations per series
 * @param {string} advancedAnalyticsRequest.sort_order - Sort order ('asc' or 'desc')
 * @param {boolean} advancedAnalyticsRequest.use_cache - Whether to use cached data
 * @param {number} [advancedAnalyticsRequest.forecast_horizon] - Number of periods to forecast
 * @param {string} [advancedAnalyticsRequest.forecast_method] - 'arima', 'exponential_smoothing', or 'linear_regression'
 * @param {string} [advancedAnalyticsRequest.anomaly_method] - 'z_score', 'iqr', or 'moving_average'
 * @param {number} [advancedAnalyticsRequest.anomaly_threshold] - Z-score threshold (default: 3.0)
 * @param {string} [advancedAnalyticsRequest.trend_type] - 'linear' or 'polynomial'
 * @param {number} [advancedAnalyticsRequest.polynomial_degree] - For polynomial trends
 * @param {string} [advancedAnalyticsRequest.decomposition_type] - 'additive' or 'multiplicative'
 * @param {number} [advancedAnalyticsRequest.seasonal_period] - Seasonal period (e.g., 12 for monthly)
 * @param {number} [advancedAnalyticsRequest.volatility_window] - Rolling window size (default: 30)
 * @returns {Promise<Object>} Advanced analytics response
 */
export async function fetchAdvancedAnalytics(advancedAnalyticsRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/spark/advanced-analytics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(advancedAnalyticsRequest),
    })

    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch {
        // If JSON parsing fails, use HTTP status message
        error = {}
      }
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    // Handle network errors (e.g., backend not running, CORS issues)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to backend at ${API_BASE_URL}. Please ensure the backend server is running.`
      )
    }
    // Re-throw other errors
    throw error
  }
}
