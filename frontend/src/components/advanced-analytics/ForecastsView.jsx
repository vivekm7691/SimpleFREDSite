/**
 * ForecastsView component - Displays forecasted values with confidence intervals
 * 
 * Features:
 * - Line chart showing historical data + forecasted values
 * - Confidence intervals as shaded area
 * - Display forecast method and confidence level
 */

import { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
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
  Filler,
  Title,
  Tooltip,
  Legend
)

/**
 * ForecastsView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of Forecast objects
 */
function ForecastsView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Forecasts</h3>
        <div className="analytics-empty">
          <p>No forecast data available</p>
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
          forecastedValues: [],
          lowerBounds: [],
          upperBounds: [],
          forecastMethod: item.forecast_method,
          confidenceLevel: item.confidence_level,
        }
      }
      grouped[item.series_id].dates.push(item.date)
      grouped[item.series_id].forecastedValues.push(item.forecasted_value)
      if (item.lower_bound !== null && item.lower_bound !== undefined) {
        grouped[item.series_id].lowerBounds.push(item.lower_bound)
      } else {
        grouped[item.series_id].lowerBounds.push(null)
      }
      if (item.upper_bound !== null && item.upper_bound !== undefined) {
        grouped[item.series_id].upperBounds.push(item.upper_bound)
      } else {
        grouped[item.series_id].upperBounds.push(null)
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
      
      // Confidence interval (shaded area)
      if (seriesInfo.lowerBounds.some(b => b !== null) && seriesInfo.upperBounds.some(b => b !== null)) {
        datasets.push({
          label: `${seriesId} - Confidence Interval`,
          data: seriesInfo.upperBounds.map((upper, i) => ({
            x: seriesInfo.dates[i],
            y: upper,
          })),
          borderColor: 'transparent',
          backgroundColor: `${color}20`,
          fill: '+1',
          pointRadius: 0,
          tension: 0.4,
        })

        datasets.push({
          label: `${seriesId} - Lower Bound`,
          data: seriesInfo.lowerBounds.map((lower, i) => ({
            x: seriesInfo.dates[i],
            y: lower,
          })),
          borderColor: 'transparent',
          backgroundColor: `${color}20`,
          fill: false,
          pointRadius: 0,
          tension: 0.4,
        })
      }

      // Forecasted values
      datasets.push({
        label: `${seriesId} - Forecast (${seriesInfo.forecastMethod})`,
        data: seriesInfo.forecastedValues,
        borderColor: color,
        backgroundColor: color,
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
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
              
              if (label.includes('Confidence Interval') || label.includes('Lower Bound')) {
                return null // Hide confidence interval labels in tooltip
              }
              
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
            text: 'Forecasted Value',
          },
          beginAtZero: false,
        },
      },
    }
  }, [])

  // Get unique forecast methods
  const forecastMethods = useMemo(() => {
    return [...new Set(data.map(item => item.forecast_method))]
  }, [data])

  // Get confidence level (assume same for all)
  const confidenceLevel = data[0]?.confidence_level

  return (
    <div className="analytics-view">
      <div className="analytics-header">
        <h3>Forecasts</h3>
        <div className="analytics-info">
          <p>
            Method: {forecastMethods.join(', ')}
            {confidenceLevel && ` | Confidence: ${(confidenceLevel * 100).toFixed(0)}%`}
          </p>
        </div>
      </div>
      <div className="analytics-chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="analytics-info">
        <p>Showing {data.length} forecast point{data.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  )
}

export default ForecastsView

