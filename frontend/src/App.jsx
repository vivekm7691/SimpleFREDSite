/**
 * Main App component for Simple FRED Site.
 * 
 * Allows users to:
 * - Enter a FRED series ID
 * - Browse FRED series by category
 * - Fetch economic data from FRED API
 * - Generate AI-powered summaries using Google Gemini
 */
import { useState, useEffect, useRef } from 'react'
import './App.css'
import { fetchFREDData, summarizeData } from './services/api'
import Sidebar from './components/Sidebar'
import DataGraph from './components/DataGraph'

function App() {
  // State management for form input, loading, errors, and data
  const [seriesId, setSeriesId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [fredData, setFredData] = useState(null)
  const [summary, setSummary] = useState(null)

  // State management for sidebar
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  // State management for tabs
  const [activeTab, setActiveTab] = useState('main') // 'main' | 'analytics'
  
  // State management for category browser (for reset functionality)
  const [categoryBrowserKey, setCategoryBrowserKey] = useState(0) // Key to reset CategoryBrowser component

  // Ref for scrolling to data section
  const dataSectionRef = useRef(null)

  /**
   * Scroll to the data section smoothly when data is fetched.
   * This provides better UX by automatically showing the fetched data.
   */
  const scrollToData = () => {
    if (dataSectionRef.current) {
      dataSectionRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      })
    }
  }

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

      // Scroll to data section after DOM updates
      setTimeout(() => {
        scrollToData()
      }, 100)

      // Generate summary using the fetched data
      const summaryData = await summarizeData(data)
      setSummary(summaryData)

      // Reset category browser after successful data fetch
      // This provides a clean state when user selects a new series
      resetCategoryBrowser()
      
      // Switch to Main Graph tab when data is loaded
      setActiveTab('main')
    } catch (err) {
      setError(err.message || 'An error occurred while fetching data')
      setFredData(null)
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Reset category browser to initial state.
   * This is called after successful data fetch to provide a clean state.
   */
  const resetCategoryBrowser = () => {
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


  return (
    <div className="App">
      <header className="App-header">
        <h1>Simple FRED Site</h1>
        <p>Fetch and summarize economic data from FRED</p>
      </header>

      <div className="App-container">
        {/* Sidebar */}
        <Sidebar
          key={categoryBrowserKey}
          onSeriesSelect={handleSeriesSelect}
        />

        {/* Main Content Area */}
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

          {fredData && (
            <div className="data-section" ref={dataSectionRef}>
              {/* Series Info Card */}
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

              {/* Tab Navigation */}
              <div className="tab-navigation">
                <button
                  className={`tab-button ${activeTab === 'main' ? 'active' : ''}`}
                  onClick={() => setActiveTab('main')}
                  aria-selected={activeTab === 'main'}
                >
                  Main Graph
                </button>
                <button
                  className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
                  onClick={() => setActiveTab('analytics')}
                  aria-selected={activeTab === 'analytics'}
                  disabled={true}
                  title="Analytics features coming in Increment 5"
                >
                  Analytics
                </button>
              </div>

              {/* Tab Content */}
              <div className="tab-content">
                {activeTab === 'main' && (
                  <div className="tab-panel">
                    {fredData.observations && fredData.observations.length > 0 ? (
                      <DataGraph
                        data={fredData}
                        seriesInfo={fredData.series_info}
                      />
                    ) : (
                      <div className="no-data-message">
                        <p>No observations available to display</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'analytics' && (
                  <div className="tab-panel">
                    <div className="analytics-placeholder">
                      <p>Analytics features coming in Increment 5</p>
                      <p className="placeholder-note">
                        Correlation analysis, statistical summaries, aggregations, and more
                      </p>
                    </div>
                  </div>
                )}
              </div>
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
    </div>
  )
}

export default App

