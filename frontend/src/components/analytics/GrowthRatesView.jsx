/**
 * GrowthRatesView component - Displays growth rates as line chart
 * 
 * Features:
 * - Line chart showing original values and growth rates
 * - Dual Y-axis (left: values, right: growth rate %)
 * - Toggle between period-over-period and year-over-year
 * - Color coding for positive/negative growth
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
 * GrowthRatesView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of GrowthRate objects
 */
function GrowthRatesView({ data }) {
  const [growthTypeFilter, setGrowthTypeFilter] = useState('all') // 'all', 'period_over_period', 'year_over_year'

  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Growth Rates</h3>
        <div className="analytics-empty">
          <p>No growth rate data available</p>
        </div>
      </div>
    )
  }

  // Filter data by growth type
  const filteredData = useMemo(() => {
    if (growthTypeFilter === 'all') {
      return data
    }
    return data.filter(item => item.growth_type === growthTypeFilter)
  }, [data, growthTypeFilter])

  // Group data by series_id
  const seriesData = useMemo(() => {
    const grouped = {}
    filteredData.forEach(item => {
      if (!grouped[item.series_id]) {
        grouped[item.series_id] = {
          dates: [],
          values: [],
          growthRates: [],
        }
      }
      grouped[item.series_id].dates.push(item.date)
      grouped[item.series_id].values.push(item.value)
      grouped[item.series_id].growthRates.push(item.growth_rate)
    })
    return grouped
  }, [filteredData])

  // Get unique growth types
  const growthTypes = useMemo(() => {
    const types = [...new Set(data.map(item => item.growth_type))]
    return types
  }, [data])

  // Prepare chart data
  const chartData = useMemo(() => {
    const datasets = []
    const seriesIds = Object.keys(seriesData)

    // Add value datasets
    seriesIds.forEach((seriesId, index) => {
      const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
      const color = colors[index % colors.length]
      
      datasets.push({
        label: `${seriesId} - Value`,
        data: seriesData[seriesId].values,
        borderColor: color,
        backgroundColor: `${color}40`,
        borderWidth: 2,
        yAxisID: 'y',
        tension: 0.4,
        pointRadius: 2,
      })
    })

    // Add growth rate datasets
    seriesIds.forEach((seriesId, index) => {
      const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
      const color = colors[index % colors.length]
      
      datasets.push({
        label: `${seriesId} - Growth Rate (%)`,
        data: seriesData[seriesId].growthRates.map(rate => 
          rate !== null && rate !== undefined ? rate * 100 : null
        ),
        borderColor: color,
        backgroundColor: `${color}20`,
        borderWidth: 2,
        borderDash: [5, 5],
        yAxisID: 'y1',
        tension: 0.4,
        pointRadius: 2,
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
              
              if (label.includes('Growth Rate')) {
                return `${label}: ${value !== null ? value.toFixed(2) + '%' : 'N/A'}`
              } else {
                return `${label}: ${value !== null ? value.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }) : 'N/A'}`
              }
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
            text: 'Value',
          },
          beginAtZero: false,
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Growth Rate (%)',
          },
          beginAtZero: false,
          grid: {
            drawOnChartArea: false,
          },
        },
      },
    }
  }, [])

  return (
    <div className="analytics-view">
      <div className="analytics-header">
        <h3>Growth Rates</h3>
        {growthTypes.length > 1 && (
          <div className="filter-controls">
            <label>Filter by type:</label>
            <select
              value={growthTypeFilter}
              onChange={(e) => setGrowthTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              {growthTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
      <div className="analytics-chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div className="analytics-info">
        <p>Showing {filteredData.length} growth rate calculation{filteredData.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  )
}

export default GrowthRatesView

