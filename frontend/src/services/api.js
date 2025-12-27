/**
 * API client for communicating with the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
  return result.summary || result
}

