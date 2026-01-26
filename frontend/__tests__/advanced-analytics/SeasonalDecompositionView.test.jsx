/**
 * Tests for SeasonalDecompositionView component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SeasonalDecompositionView from '../../src/components/advanced-analytics/SeasonalDecompositionView'

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart">
      <div data-testid="chart-labels">{JSON.stringify(data.labels)}</div>
      <div data-testid="chart-datasets">{data.datasets.length} datasets</div>
    </div>
  ),
}))

describe('SeasonalDecompositionView Component', () => {
  test('renders empty state when no data', () => {
    render(<SeasonalDecompositionView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /seasonal decomposition/i })).toBeInTheDocument()
    expect(screen.getByText(/no seasonal decomposition data available/i)).toBeInTheDocument()
  })

  test('renders chart with decomposition data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        actual_value: 100.0,
        trend_component: 95.0,
        seasonal_component: 5.0,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
    ]
    
    render(<SeasonalDecompositionView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /seasonal decomposition/i })).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByText(/type: additive/i)).toBeInTheDocument()
  })

  test('displays decomposition type', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        actual_value: 100.0,
        trend_component: 95.0,
        seasonal_component: 1.05,
        residual_component: 1.0,
        decomposition_type: 'multiplicative',
      },
    ]
    
    render(<SeasonalDecompositionView data={mockData} />)
    
    expect(screen.getByText(/type: multiplicative/i)).toBeInTheDocument()
  })

  test('toggles component visibility', async () => {
    const user = userEvent.setup()
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        actual_value: 100.0,
        trend_component: 95.0,
        seasonal_component: 5.0,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
    ]
    
    render(<SeasonalDecompositionView data={mockData} />)
    
    const residualCheckbox = screen.getByLabelText(/residual/i)
    expect(residualCheckbox).not.toBeChecked()
    
    await user.click(residualCheckbox)
    
    await waitFor(() => {
      expect(residualCheckbox).toBeChecked()
    })
  })

  test('displays decomposition count', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        actual_value: 100.0,
        trend_component: 95.0,
        seasonal_component: 5.0,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        actual_value: 105.0,
        trend_component: 100.0,
        seasonal_component: 5.0,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
    ]
    
    render(<SeasonalDecompositionView data={mockData} />)
    
    expect(screen.getByText(/showing 2 decomposition points/i)).toBeInTheDocument()
  })

  test('handles multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        actual_value: 100.0,
        trend_component: 95.0,
        seasonal_component: 5.0,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
      {
        series_id: 'UNRATE',
        date: '2024-01-01',
        actual_value: 3.5,
        trend_component: 3.0,
        seasonal_component: 0.5,
        residual_component: 0.0,
        decomposition_type: 'additive',
      },
    ]
    
    render(<SeasonalDecompositionView data={mockData} />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })
})

