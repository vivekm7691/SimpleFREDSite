/**
 * MovingAveragesView component - Displays moving averages as line chart
 * 
 * Features:
 * - Line chart showing original data and moving average
 * - Different line styles (solid for original, dashed for MA)
 * - Window size and type indicator
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
import './Analytics.css'

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
 * MovingAveragesView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of MovingAverage objects
 */
function MovingAveragesView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Moving Averages</h3>
        <div className="analytics-empty">
          <p>No moving average data available</p>
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
          values: [],
          movingAverages: [],
          windowSize: item.window_size,
          maType: item.moving_average_type,
        }
      }
      grouped[item.series_id].dates.push(item.date)
      grouped[item.series_id].values.push(item.value)
      grouped[item.series_id].movingAverages.push(item.moving_average)
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
      
      // Original values
      datasets.push({
        label: `${seriesId} - Original`,
        data: seriesInfo.values,
        borderColor: color,
        backgroundColor: `${color}40`,
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      })

      // Moving average
      const maLabel = seriesInfo.maType === 'sma' ? 'SMA' : 'EMA'
      datasets.push({
        label: `${seriesId} - ${maLabel} (${seriesInfo.windowSize})`,
        data: seriesInfo.movingAverages,
        borderColor: color,
        backgroundColor: `${color}20`,
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      })
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
              return `${label}: ${value !== null && value !== undefined ? value.toLocaleString('en-US', {
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

  // Get unique series info for display
  const seriesInfo = useMemo(() => {
    const info = {}
    data.forEach(item => {
      if (!info[item.series_id]) {
        info[item.series_id] = {
          windowSize: item.window_size,
          maType: item.moving_average_type,
        }
      }
    })
    return info
  }, [data])

  return (
    <div className="analytics-view">
      <h3>Moving Averages</h3>
      <div className="analytics-chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="analytics-info">
        <p>Showing {data.length} moving average calculation{data.length !== 1 ? 's' : ''}</p>
        <div className="ma-info">
          {Object.entries(seriesInfo).map(([seriesId, info]) => (
            <div key={seriesId} className="ma-info-item">
              <strong>{seriesId}:</strong> {info.maType.toUpperCase()} with window size {info.windowSize}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default MovingAveragesView

