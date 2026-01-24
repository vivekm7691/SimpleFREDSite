/**
 * Tests for TimeAggregationsView component
 */
import { render, screen } from '@testing-library/react'
import TimeAggregationsView from '../../src/components/analytics/TimeAggregationsView'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
}))

describe('TimeAggregationsView Component', () => {
  test('renders empty state when no data', () => {
    render(<TimeAggregationsView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /time aggregations/i })).toBeInTheDocument()
    expect(screen.getByText(/no time aggregation data available/i)).toBeInTheDocument()
  })

  test('renders bar chart for discrete periods (monthly)', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-01',
        aggregated_value: 100.0,
        aggregation_function: 'mean',
        observation_count: 30,
      },
      {
        series_id: 'GDP',
        period: '2024-02',
        aggregated_value: 105.0,
        aggregation_function: 'mean',
        observation_count: 28,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /time aggregations/i })).toBeInTheDocument()
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  test('renders bar chart for quarterly periods', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-Q1',
        aggregated_value: 100.0,
        aggregation_function: 'sum',
        observation_count: 90,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  test('renders line chart for continuous periods (daily)', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-01-01',
        aggregated_value: 100.0,
        aggregation_function: 'mean',
        observation_count: 1,
      },
      {
        series_id: 'GDP',
        period: '2024-01-02',
        aggregated_value: 101.0,
        aggregation_function: 'mean',
        observation_count: 1,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('displays aggregation function', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-01',
        aggregated_value: 100.0,
        aggregation_function: 'sum',
        observation_count: 30,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    expect(screen.getByText(/sum/i)).toBeInTheDocument()
  })

  test('handles multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-01',
        aggregated_value: 100.0,
        aggregation_function: 'mean',
        observation_count: 30,
      },
      {
        series_id: 'UNRATE',
        period: '2024-01',
        aggregated_value: 5.0,
        aggregation_function: 'mean',
        observation_count: 30,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    // Chart should be rendered
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    // Aggregation count should be displayed
    expect(screen.getByText(/2 aggregation/i)).toBeInTheDocument()
  })

  test('handles null values gracefully', () => {
    const mockData = [
      {
        series_id: 'GDP',
        period: '2024-01',
        aggregated_value: null,
        aggregation_function: 'mean',
        observation_count: 0,
      },
    ]
    
    render(<TimeAggregationsView data={mockData} />)
    
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })
})
