/**
 * SeasonalDecompositionView component - Displays seasonal decomposition
 * 
 * Features:
 * - Multi-line chart showing actual, trend, seasonal, and residual components
 * - Toggle visibility of individual components
 */

import { useState, useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import '../analytics/Analytics.css'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

/**
 * SeasonalDecompositionView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of SeasonalDecomposition objects
 */
function SeasonalDecompositionView({ data }) {
  const [visibleComponents, setVisibleComponents] = useState({
    actual: true,
    trend: true,
    seasonal: true,
    residual: false,
  })

  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Seasonal Decomposition</h3>
        <div className="analytics-empty">
          <p>No seasonal decomposition data available</p>
        </div>
      </div>
    )
  }

  // Group data by series_id
  const seriesData = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      if (!grouped[item.series_id]) {
        grouped[item.series_id] = {
          dates: [],
          actualValues: [],
          trendComponents: [],
          seasonalComponents: [],
          residualComponents: [],
          decompositionType: item.decomposition_type,
        }
      }
      grouped[item.series_id].dates.push(item.date)
      grouped[item.series_id].actualValues.push(item.actual_value)
      grouped[item.series_id].trendComponents.push(item.trend_component)
      grouped[item.series_id].seasonalComponents.push(item.seasonal_component)
      grouped[item.series_id].residualComponents.push(item.residual_component)
    })
    return grouped
  }, [data])

  // Prepare chart data
  const chartData = useMemo(() => {
    const datasets = []
    const seriesIds = Object.keys(seriesData)
    const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']

    seriesIds.forEach((seriesId, index) => {
      const color = colors[index % colors.length]
      const seriesInfo = seriesData[seriesId]
      
      if (visibleComponents.actual) {
        datasets.push({
          label: `${seriesId} - Actual`,
          data: seriesInfo.actualValues,
          borderColor: color,
          backgroundColor: `${color}40`,
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 2,
        })
      }

      if (visibleComponents.trend) {
        datasets.push({
          label: `${seriesId} - Trend`,
          data: seriesInfo.trendComponents,
          borderColor: '#28a745',
          backgroundColor: '#28a74540',
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.4,
          pointRadius: 2,
        })
      }

      if (visibleComponents.seasonal) {
        datasets.push({
          label: `${seriesId} - Seasonal`,
          data: seriesInfo.seasonalComponents,
          borderColor: '#ffc107',
          backgroundColor: '#ffc10740',
          borderWidth: 2,
          borderDash: [10, 5],
          tension: 0.4,
          pointRadius: 2,
        })
      }

      if (visibleComponents.residual) {
        datasets.push({
          label: `${seriesId} - Residual`,
          data: seriesInfo.residualComponents,
          borderColor: '#dc3545',
          backgroundColor: '#dc354540',
          borderWidth: 1,
          borderDash: [2, 2],
          tension: 0.4,
          pointRadius: 1,
        })
      }
    })

    return {
      labels: seriesData[seriesIds[0]]?.dates || [],
      datasets,
    }
  }, [seriesData, visibleComponents])

  // Chart options
  const chartOptions = useMemo(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              return `${label}: ${value !== null ? value.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              }) : 'N/A'}`
            },
          },
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Date',
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45,
          },
        },
        y: {
          title: {
            display: true,
            text: 'Value',
          },
          beginAtZero: false,
        },
      },
    }
  }, [])

  // Get decomposition type
  const decompositionType = data[0]?.decomposition_type

  return (
    <div className="analytics-view">
      <div className="analytics-header">
        <h3>Seasonal Decomposition</h3>
        <div className="filter-controls">
          <label>
            <input
              type="checkbox"
              checked={visibleComponents.actual}
              onChange={(e) => setVisibleComponents(prev => ({ ...prev, actual: e.target.checked }))}
            />
            Actual
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleComponents.trend}
              onChange={(e) => setVisibleComponents(prev => ({ ...prev, trend: e.target.checked }))}
            />
            Trend
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleComponents.seasonal}
              onChange={(e) => setVisibleComponents(prev => ({ ...prev, seasonal: e.target.checked }))}
            />
            Seasonal
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleComponents.residual}
              onChange={(e) => setVisibleComponents(prev => ({ ...prev, residual: e.target.checked }))}
            />
            Residual
          </label>
        </div>
      </div>
      <div className="analytics-info">
        <p>Type: {decompositionType ? decompositionType.charAt(0).toUpperCase() + decompositionType.slice(1) : 'N/A'}</p>
      </div>
      <div className="analytics-chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="analytics-info">
        <p>Showing {data.length} decomposition point{data.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  )
}

export default SeasonalDecompositionView

