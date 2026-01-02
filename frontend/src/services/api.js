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
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch FRED data' }))
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
    const error = await response.json().catch(() => ({ detail: 'Failed to generate summary' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  const result = await response.json()
  // Handle both string and object responses
  if (typeof result === 'string') {
    return result
  }
  return result.summary || result
}

