/**
 * Tests for MovingAveragesView component
 */
import { render, screen } from '@testing-library/react'
import MovingAveragesView from '../../src/components/analytics/MovingAveragesView'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
}))

describe('MovingAveragesView Component', () => {
  test('renders empty state when no data', () => {
    render(<MovingAveragesView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /moving averages/i })).toBeInTheDocument()
    expect(screen.getByText(/no moving average data available/i)).toBeInTheDocument()
  })

  test('renders chart with original data and moving average', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        moving_average: 98.0,
        moving_average_type: 'sma',
        window_size: 7,
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        moving_average: 102.5,
        moving_average_type: 'sma',
        window_size: 7,
      },
    ]
    
    render(<MovingAveragesView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /moving averages/i })).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('displays SMA type and window size', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        moving_average: 98.0,
        moving_average_type: 'sma',
        window_size: 14,
      },
    ]
    
    render(<MovingAveragesView data={mockData} />)
    
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/SMA/i)).toBeInTheDocument()
    expect(screen.getByText(/14/i)).toBeInTheDocument()
  })

  test('displays EMA type and window size', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        moving_average: 98.0,
        moving_average_type: 'ema',
        window_size: 30,
      },
    ]
    
    render(<MovingAveragesView data={mockData} />)
    
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/EMA/i)).toBeInTheDocument()
    expect(screen.getByText(/30/i)).toBeInTheDocument()
  })

  test('handles multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        moving_average: 98.0,
        moving_average_type: 'sma',
        window_size: 7,
      },
      {
        series_id: 'UNRATE',
        date: '2024-01-01',
        value: 5.0,
        moving_average: 4.8,
        moving_average_type: 'sma',
        window_size: 7,
      },
    ]
    
    render(<MovingAveragesView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/UNRATE/i)).toBeInTheDocument()
  })

  test('handles null values gracefully', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: null,
        moving_average: null,
        moving_average_type: 'sma',
        window_size: 7,
      },
    ]
    
    render(<MovingAveragesView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })
})
