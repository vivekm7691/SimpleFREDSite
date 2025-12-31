import { useState } from 'react'
import './App.css'
import { fetchFREDData, summarizeData } from './services/api'

function App() {
  const [seriesId, setSeriesId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [fredData, setFredData] = useState(null)
  const [summary, setSummary] = useState(null)

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
    } catch (err) {
      setError(err.message || 'An error occurred while fetching data')
      setFredData(null)
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

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

