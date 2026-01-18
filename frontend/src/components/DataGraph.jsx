/**
 * DataGraph component - Interactive time series chart using Chart.js.
 * 
 * Replaces the observations table with an interactive line chart.
 * 
 * Features:
 * - Line chart displaying time series data
 * - Interactive tooltips (hover to see date and value)
 * - Responsive design
 * - Dark/light theme support
 * - Handles empty data and null values gracefully
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
  Filler
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import './DataGraph.css'
import './DataGraph.css'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

/**
 * DataGraph component
 * @param {Object} props - Component props
 * @param {Object} props.data - FRED data object with observations array
 * @param {Object} props.seriesInfo - Series metadata (title, units, etc.)
 */
function DataGraph({ data, seriesInfo }) {
  // Prepare chart data from observations
  const chartData = useMemo(() => {
    if (!data || !data.observations || data.observations.length === 0) {
      return null
    }

    // Sort observations by date (ascending) for proper time series display
    const sortedObservations = [...data.observations].sort((a, b) => {
      return new Date(a.date) - new Date(b.date)
    })

    // Extract dates and values
    const labels = sortedObservations.map(obs => obs.date)
    const values = sortedObservations.map(obs => obs.value)

    return {
      labels,
      datasets: [
        {
          label: seriesInfo?.title || data.series_id || 'Value',
          data: values,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: '#007bff',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        }
      ]
    }
  }, [data, seriesInfo])

  // Chart options
  const chartOptions = useMemo(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        title: {
          display: false, // Title handled by parent component
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              const value = context.parsed.y
              const formattedValue = value !== null && value !== undefined
                ? value.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })
                : 'N/A'
              const unit = seriesInfo?.units ? ` ${seriesInfo.units}` : ''
              return `${context.dataset.label}: ${formattedValue}${unit}`
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Date'
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          title: {
            display: true,
            text: seriesInfo?.units || 'Value'
          },
          beginAtZero: false
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }
  }, [seriesInfo])

  // Handle empty or no data
  if (!data || !data.observations || data.observations.length === 0) {
    return (
      <div className="data-graph-container">
        <div className="data-graph-empty">
          <p>No data available to display</p>
        </div>
      </div>
    )
  }

  if (!chartData) {
    return (
      <div className="data-graph-container">
        <div className="data-graph-empty">
          <p>Unable to process data for chart</p>
        </div>
      </div>
    )
  }

  return (
    <div className="data-graph-container">
      <div className="data-graph-wrapper">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="data-graph-info">
        <p className="data-graph-count">
          Showing {data.observations.length} observation{data.observations.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  )
}

export default DataGraph

