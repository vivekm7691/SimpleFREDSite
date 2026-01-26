/**
 * VolatilityView component - Displays volatility analysis
 * 
 * Features:
 * - Line chart showing rolling volatility and annualized volatility over time
 * - Display return values if available
 */

import { useMemo } from 'react'
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
 * VolatilityView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of Volatility objects
 */
function VolatilityView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Volatility Analysis</h3>
        <div className="analytics-empty">
          <p>No volatility data available</p>
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
          volatilities: [],
          annualizedVolatilities: [],
          returnValues: [],
          windowSize: item.window_size,
        }
      }
      grouped[item.series_id].dates.push(item.date)
      grouped[item.series_id].volatilities.push(item.volatility)
      if (item.annualized_volatility !== null && item.annualized_volatility !== undefined) {
        grouped[item.series_id].annualizedVolatilities.push(item.annualized_volatility)
      } else {
        grouped[item.series_id].annualizedVolatilities.push(null)
      }
      if (item.return_value !== null && item.return_value !== undefined) {
        grouped[item.series_id].returnValues.push(item.return_value)
      } else {
        grouped[item.series_id].returnValues.push(null)
      }
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
      
      // Rolling volatility
      datasets.push({
        label: `${seriesId} - Rolling Volatility`,
        data: seriesInfo.volatilities,
        borderColor: color,
        backgroundColor: `${color}40`,
        borderWidth: 2,
        yAxisID: 'y',
        tension: 0.4,
        pointRadius: 2,
      })

      // Annualized volatility (if available)
      if (seriesInfo.annualizedVolatilities.some(v => v !== null)) {
        datasets.push({
          label: `${seriesId} - Annualized Volatility`,
          data: seriesInfo.annualizedVolatilities,
          borderColor: color,
          backgroundColor: `${color}20`,
          borderWidth: 2,
          borderDash: [5, 5],
          yAxisID: 'y',
          tension: 0.4,
          pointRadius: 2,
        })
      }
    })

    return {
      labels: seriesData[seriesIds[0]]?.dates || [],
      datasets,
    }
  }, [seriesData])

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
              return `${label}: ${value !== null ? (value * 100).toFixed(2) + '%' : 'N/A'}`
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
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Volatility',
          },
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return (value * 100).toFixed(1) + '%'
            },
          },
        },
      },
    }
  }, [])

  // Get window size (assume same for all)
  const windowSize = data[0]?.window_size

  return (
    <div className="analytics-view">
      <div className="analytics-header">
        <h3>Volatility Analysis</h3>
        {windowSize && (
          <div className="analytics-info">
            <p>Window Size: {windowSize} periods</p>
          </div>
        )}
      </div>
      <div className="analytics-chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="analytics-info">
        <p>Showing {data.length} volatility data point{data.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  )
}

export default VolatilityView

