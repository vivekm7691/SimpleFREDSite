/**
 * Tests for GrowthRatesView component
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import GrowthRatesView from '../../src/components/analytics/GrowthRatesView'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
}))

describe('GrowthRatesView Component', () => {
  test('renders empty state when no data', () => {
    render(<GrowthRatesView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /growth rates/i })).toBeInTheDocument()
    expect(screen.getByText(/no growth rate data available/i)).toBeInTheDocument()
  })

  test('renders chart with growth rate data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        previous_value: 95.0,
        growth_rate: 0.0526,
        growth_type: 'period_over_period',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        previous_value: 100.0,
        growth_rate: 0.05,
        growth_type: 'period_over_period',
      },
    ]
    
    render(<GrowthRatesView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /growth rates/i })).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('filters by growth type when filter is changed', async () => {
    const user = userEvent.setup()
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        previous_value: 95.0,
        growth_rate: 0.05,
        growth_type: 'period_over_period',
      },
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        previous_value: 90.0,
        growth_rate: 0.1111,
        growth_type: 'year_over_year',
      },
    ]
    
    render(<GrowthRatesView data={mockData} />)
    
    // Check that filter dropdown exists
    const filterSelect = screen.getByRole('combobox')
    expect(filterSelect).toBeInTheDocument()
    
    // Change filter
    await user.selectOptions(filterSelect, 'period_over_period')
    
    // Chart should still be rendered
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('displays multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        previous_value: 95.0,
        growth_rate: 0.05,
        growth_type: 'period_over_period',
      },
      {
        series_id: 'UNRATE',
        date: '2024-01-01',
        value: 5.0,
        previous_value: 4.8,
        growth_rate: 0.0417,
        growth_type: 'period_over_period',
      },
    ]
    
    render(<GrowthRatesView data={mockData} />)
    
    // Chart should be rendered
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    // Series count should be displayed in info section
    expect(screen.getByText(/2 growth rate calculation/i)).toBeInTheDocument()
  })

  test('handles null values gracefully', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: null,
        previous_value: null,
        growth_rate: null,
        growth_type: 'period_over_period',
      },
    ]
    
    render(<GrowthRatesView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  test('does not show filter when only one growth type exists', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 100.0,
        previous_value: 95.0,
        growth_rate: 0.05,
        growth_type: 'period_over_period',
      },
    ]
    
    render(<GrowthRatesView data={mockData} />)
    
    // Filter should not appear when only one type exists
    const filterSelect = screen.queryByRole('combobox')
    expect(filterSelect).not.toBeInTheDocument()
  })
})
