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
      const data = await fetchFREDData(seriesId)
      setFredData(data)

      // Generate summary
      const summaryData = await summarizeData(data)
      setSummary(summaryData)
    } catch (err) {
      setError(err.message || 'An error occurred while fetching data')
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
            {loading ? 'Loading...' : 'Fetch & Summarize'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {fredData && (
          <div className="data-section">
            <h2>FRED Data</h2>
            <pre>{JSON.stringify(fredData, null, 2)}</pre>
          </div>
        )}

        {summary && (
          <div className="summary-section">
            <h2>AI Summary</h2>
            <p>{summary}</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App

