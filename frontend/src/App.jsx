/**
 * Main App component for Simple FRED Site.
 * 
 * Allows users to:
 * - Enter a FRED series ID
 * - Browse FRED series by category
 * - Fetch economic data from FRED API
 * - Generate AI-powered summaries using Google Gemini
 */
import { useState, useEffect } from 'react'
import './App.css'
import { fetchFREDData, summarizeData } from './services/api'
import CategoryBrowser from './components/CategoryBrowser'

function App() {
  // State management for form input, loading, errors, and data
  const [seriesId, setSeriesId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [fredData, setFredData] = useState(null)
  const [summary, setSummary] = useState(null)

  // State management for category browser
  // These track the current state of category browsing for potential future use
  // (e.g., URL params, analytics, persistence)
  const [selectedCategoryId, setSelectedCategoryId] = useState(null)
  const [categoryView, setCategoryView] = useState('grid') // 'grid' | 'detail'
  const [categoryBrowserKey, setCategoryBrowserKey] = useState(0) // Key to reset CategoryBrowser component

  /**
   * Handle form submission:
   * 1. Validate series ID input
   * 2. Fetch FRED data for the series ID
   * 3. Generate AI summary of the fetched data
   * 4. Handle errors appropriately
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!seriesId.trim()) {
      setError('Please enter a FRED series ID')
      return
    }

    setLoading(true)
    setError(null)
    setFredData(null)
    setSummary(null)

    try {
      // Fetch FRED data
      const data = await fetchFREDData(seriesId.trim().toUpperCase())
      setFredData(data)

      // Generate summary using the fetched data
      const summaryData = await summarizeData(data)
      setSummary(summaryData)

      // Reset category browser after successful data fetch
      // This provides a clean state when user selects a new series
      resetCategoryBrowser()
    } catch (err) {
      setError(err.message || 'An error occurred while fetching data')
      setFredData(null)
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Reset category browser to initial state (grid view, no selected category).
   * This is called after successful data fetch to provide a clean state.
   */
  const resetCategoryBrowser = () => {
    setSelectedCategoryId(null)
    setCategoryView('grid')
    // Force CategoryBrowser to reset by changing its key
    // This causes React to unmount and remount the component, resetting all internal state
    setCategoryBrowserKey((prev) => prev + 1)
  }

  /**
   * Handle series selection from CategoryBrowser.
   * Auto-fills the input field with the selected series ID.
   * @param {string} selectedSeriesId - Selected series ID
   */
  const handleSeriesSelect = (selectedSeriesId) => {
    setSeriesId(selectedSeriesId)
    // Optionally, you could auto-trigger fetch here:
    // handleSubmit({ preventDefault: () => {} })
  }

  /**
   * Track category browser state changes for potential future use
   * (e.g., URL params, analytics, browser history)
   * Note: CategoryBrowser manages its own internal state, but we track
   * the high-level state here for App-level coordination.
   */
  useEffect(() => {
    // Future: Could sync selectedCategoryId and categoryView with URL params
    // Future: Could track analytics events for category navigation
    // For now, state is tracked but CategoryBrowser is self-contained
  }, [selectedCategoryId, categoryView])

  return (
    <div className="App">
      <header className="App-header">
        <h1>Simple FRED Site</h1>
        <p>Fetch and summarize economic data from FRED</p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="form-group">
            <label htmlFor="seriesId">FRED Series ID:</label>
            <input
              id="seriesId"
              type="text"
              value={seriesId}
              onChange={(e) => setSeriesId(e.target.value)}
              placeholder="e.g., GDP, UNRATE, CPIAUCSL"
              disabled={loading}
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Loading...
              </>
            ) : (
              'Fetch & Summarize'
            )}
          </button>
        </form>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Category Browser Section */}
        <CategoryBrowser
          key={categoryBrowserKey}
          onSeriesSelect={handleSeriesSelect}
        />

        {fredData && (
          <div className="data-section">
            <h2>FRED Economic Data</h2>
            {fredData.series_info && (
              <div className="series-info">
                <h3>{fredData.series_info.title || fredData.series_id}</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Series ID:</span>
                    <span className="info-value">{fredData.series_info.id || fredData.series_id}</span>
                  </div>
                  {fredData.series_info.units && (
                    <div className="info-item">
                      <span className="info-label">Units:</span>
                      <span className="info-value">{fredData.series_info.units}</span>
                    </div>
                  )}
                  {fredData.series_info.frequency && (
                    <div className="info-item">
                      <span className="info-label">Frequency:</span>
                      <span className="info-value">{fredData.series_info.frequency}</span>
                    </div>
                  )}
                  {fredData.series_info.seasonal_adjustment && (
                    <div className="info-item">
                      <span className="info-label">Seasonal Adjustment:</span>
                      <span className="info-value">{fredData.series_info.seasonal_adjustment}</span>
                    </div>
                  )}
                  <div className="info-item">
                    <span className="info-label">Observations:</span>
                    <span className="info-value">{fredData.observation_count || 0}</span>
                  </div>
                </div>
              </div>
            )}
            
            {fredData.observations && fredData.observations.length > 0 && (
              <div className="observations-section">
                <h3>Recent Data Points</h3>
                <div className="observations-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fredData.observations.slice(0, 20).map((obs, index) => (
                        <tr key={index}>
                          <td>{obs.date}</td>
                          <td>{obs.value !== null && obs.value !== undefined ? obs.value.toLocaleString() : 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {fredData.observations.length > 20 && (
                    <p className="more-data">Showing 20 of {fredData.observations.length} observations</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {summary && (
          <div className="summary-section">
            <h2>AI-Powered Summary</h2>
            <div className="summary-content">
              {typeof summary === 'string' ? (
                <p>{summary}</p>
              ) : (
                <p>{summary}</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App

