/**
 * TimeAggregationsView component - Displays time-based aggregations as bar/line chart
 * 
 * Features:
 * - Bar chart for discrete periods (monthly, quarterly, yearly)
 * - Line chart for continuous periods (daily, weekly)
 * - Shows aggregated values by time period
 */

import { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import './Analytics.css'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

/**
 * TimeAggregationsView component
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of TimeAggregation objects
 */
function TimeAggregationsView({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-view">
        <h3>Time Aggregations</h3>
        <div className="analytics-empty">
          <p>No time aggregation data available</p>
        </div>
      </div>
    )
  }

  // Determine chart type based on period format
  const chartType = useMemo(() => {
    // If periods look like dates (daily/weekly), use line chart
    // If periods look like months/quarters/years, use bar chart
    const firstPeriod = data[0]?.period || ''
    if (firstPeriod.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return 'line' // Daily/weekly
    }
    return 'bar' // Monthly/quarterly/yearly
  }, [data])

  // Group data by series_id
  const seriesData = useMemo(() => {
    const grouped = {}
    data.forEach(item => {
      if (!grouped[item.series_id]) {
        grouped[item.series_id] = {
          periods: [],
          values: [],
          aggregationFunction: item.aggregation_function,
        }
      }
      grouped[item.series_id].periods.push(item.period)
      grouped[item.series_id].values.push(item.aggregated_value)
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
      
      datasets.push({
        label: `${seriesId} (${seriesInfo.aggregationFunction})`,
        data: seriesInfo.values,
        borderColor: color,
        backgroundColor: chartType === 'bar' ? color : `${color}40`,
        borderWidth: 2,
        tension: chartType === 'line' ? 0.4 : 0,
        pointRadius: chartType === 'line' ? 3 : 0,
        pointHoverRadius: chartType === 'line' ? 5 : 0,
      })
    })

    return {
      labels: seriesData[seriesIds[0]]?.periods || [],
      datasets,
    }
  }, [seriesData, chartType])

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
            text: 'Period',
          },
          ticks: {
            maxRotation: chartType === 'bar' ? 45 : 0,
            minRotation: chartType === 'bar' ? 45 : 0,
          },
        },
        y: {
          title: {
            display: true,
            text: 'Aggregated Value',
          },
          beginAtZero: chartType === 'bar',
        },
      },
    }
  }, [chartType])

  // Get aggregation function for display
  const aggregationFunction = data[0]?.aggregation_function || 'mean'

  return (
    <div className="analytics-view">
      <h3>Time Aggregations</h3>
      <div className="analytics-chart-container">
        {chartType === 'bar' ? (
          <Bar data={chartData} options={chartOptions} />
        ) : (
          <Line data={chartData} options={chartOptions} />
        )}
      </div>
      <div className="analytics-info">
        <p>
          Showing {data.length} aggregation{data.length !== 1 ? 's' : ''} using{' '}
          <strong>{aggregationFunction}</strong> function
        </p>
      </div>
    </div>
  )
}

export default TimeAggregationsView

