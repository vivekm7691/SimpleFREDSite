/**
 * Tests for VolatilityView component
 */
import { render, screen } from '@testing-library/react'
import VolatilityView from '../../src/components/advanced-analytics/VolatilityView'

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart">
      <div data-testid="chart-labels">{JSON.stringify(data.labels)}</div>
      <div data-testid="chart-datasets">{data.datasets.length} datasets</div>
    </div>
  ),
}))

describe('VolatilityView Component', () => {
  test('renders empty state when no data', () => {
    render(<VolatilityView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /volatility analysis/i })).toBeInTheDocument()
    expect(screen.getByText(/no volatility data available/i)).toBeInTheDocument()
  })

  test('renders chart with volatility data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: 0.15,
        return_value: 0.02,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /volatility analysis/i })).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByText(/window size: 30 periods/i)).toBeInTheDocument()
  })

  test('displays window size information', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: 0.15,
        return_value: 0.02,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByText(/window size: 30 periods/i)).toBeInTheDocument()
  })

  test('handles null annualized volatility', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: null,
        return_value: 0.02,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('handles null return value', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: 0.15,
        return_value: null,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('displays volatility count', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: 0.15,
        return_value: 0.02,
        window_size: 30,
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        volatility: 0.06,
        annualized_volatility: 0.18,
        return_value: 0.03,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByText(/showing 2 volatility data points/i)).toBeInTheDocument()
  })

  test('displays multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        volatility: 0.05,
        annualized_volatility: 0.15,
        return_value: 0.02,
        window_size: 30,
      },
      {
        series_id: 'UNRATE',
        date: '2024-01-01',
        volatility: 0.10,
        annualized_volatility: 0.30,
        return_value: 0.05,
        window_size: 30,
      },
    ]
    
    render(<VolatilityView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })
})

