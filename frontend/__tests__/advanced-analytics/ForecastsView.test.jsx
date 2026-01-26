/**
 * Tests for ForecastsView component
 */
import { render, screen } from '@testing-library/react'
import ForecastsView from '../../src/components/advanced-analytics/ForecastsView'

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart">
      <div data-testid="chart-labels">{JSON.stringify(data.labels)}</div>
      <div data-testid="chart-datasets">{data.datasets.length} datasets</div>
    </div>
  ),
}))

describe('ForecastsView Component', () => {
  test('renders empty state when no data', () => {
    render(<ForecastsView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /forecasts/i })).toBeInTheDocument()
    expect(screen.getByText(/no forecast data available/i)).toBeInTheDocument()
  })

  test('renders chart with forecast data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-12-01',
        forecasted_value: 110.0,
        lower_bound: 105.0,
        upper_bound: 115.0,
        confidence_level: 0.95,
        forecast_method: 'linear_regression',
      },
      {
        series_id: 'GDP',
        date: '2025-01-01',
        forecasted_value: 115.0,
        lower_bound: 110.0,
        upper_bound: 120.0,
        confidence_level: 0.95,
        forecast_method: 'linear_regression',
      },
    ]
    
    render(<ForecastsView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /forecasts/i })).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByText(/method: linear_regression/i)).toBeInTheDocument()
    expect(screen.getByText(/confidence: 95%/i)).toBeInTheDocument()
  })

  test('displays forecast method and confidence level', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-12-01',
        forecasted_value: 110.0,
        lower_bound: 105.0,
        upper_bound: 115.0,
        confidence_level: 0.95,
        forecast_method: 'arima',
      },
    ]
    
    render(<ForecastsView data={mockData} />)
    
    expect(screen.getByText(/method: arima/i)).toBeInTheDocument()
    expect(screen.getByText(/confidence: 95%/i)).toBeInTheDocument()
  })

  test('displays multiple series forecasts', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-12-01',
        forecasted_value: 110.0,
        lower_bound: 105.0,
        upper_bound: 115.0,
        confidence_level: 0.95,
        forecast_method: 'linear_regression',
      },
      {
        series_id: 'UNRATE',
        date: '2024-12-01',
        forecasted_value: 3.5,
        lower_bound: 3.0,
        upper_bound: 4.0,
        confidence_level: 0.95,
        forecast_method: 'linear_regression',
      },
    ]
    
    render(<ForecastsView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('handles null confidence intervals', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-12-01',
        forecasted_value: 110.0,
        lower_bound: null,
        upper_bound: null,
        confidence_level: null,
        forecast_method: 'exponential_smoothing',
      },
    ]
    
    render(<ForecastsView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('displays forecast count', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-12-01',
        forecasted_value: 110.0,
        lower_bound: 105.0,
        upper_bound: 115.0,
        confidence_level: 0.95,
        forecast_method: 'linear_regression',
      },
    ]
    
    render(<ForecastsView data={mockData} />)
    
    expect(screen.getByText(/showing 1 forecast point/i)).toBeInTheDocument()
  })
})

