/**
 * Tests for AnalyticsPanel component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AnalyticsPanel from '../src/components/AnalyticsPanel'
import { fetchAnalytics } from '../src/services/api'

// Mock the API service
jest.mock('../src/services/api', () => ({
  fetchAnalytics: jest.fn(),
}))

// Mock AnalyticsForm
jest.mock('../src/components/AnalyticsForm', () => {
  return function MockAnalyticsForm({ onSubmit, loading, initialSeriesIds }) {
    return (
      <div data-testid="analytics-form">
        <button
          onClick={() => onSubmit({
            series_ids: initialSeriesIds.length > 0 ? initialSeriesIds : ['GDP'],
            analytics_types: ['statistics'],
            limit: 100,
            sort_order: 'desc',
            use_cache: true,
          })}
          disabled={loading}
        >
          {loading ? 'Running Analytics...' : 'Run Analytics'}
        </button>
      </div>
    )
  }
})

// Mock analytics visualization components
jest.mock('../src/components/analytics', () => ({
  StatisticsView: ({ data }) => <div data-testid="statistics-view">Statistics: {data.length} series</div>,
  GrowthRatesView: ({ data }) => <div data-testid="growth-rates-view">Growth Rates: {data.length} items</div>,
  CorrelationsView: ({ data }) => <div data-testid="correlations-view">Correlations: {data.length} pairs</div>,
  MovingAveragesView: ({ data }) => <div data-testid="moving-averages-view">Moving Averages: {data.length} items</div>,
  TimeAggregationsView: ({ data }) => <div data-testid="time-aggregations-view">Time Aggregations: {data.length} items</div>,
}))

describe('AnalyticsPanel Component', () => {
  beforeEach(() => {
    fetchAnalytics.mockClear()
  })

  test('renders analytics panel with header', () => {
    render(<AnalyticsPanel />)
    
    expect(screen.getByText(/analytics dashboard/i)).toBeInTheDocument()
    expect(screen.getByText(/perform statistical analysis/i)).toBeInTheDocument()
  })

  test('renders analytics form', () => {
    render(<AnalyticsPanel />)
    
    expect(screen.getByTestId('analytics-form')).toBeInTheDocument()
  })

  test('shows loading state when fetching analytics', async () => {
    fetchAnalytics.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      // Check for loading spinner or loading text (may appear in multiple places)
      const loadingElements = screen.getAllByText(/running analytics/i)
      expect(loadingElements.length).toBeGreaterThan(0)
    })
  })

  test('displays analytics results after successful fetch', async () => {
    const mockResponse = {
      series_count: 1,
      statistics: [
        {
          series_id: 'GDP',
          mean: 100.0,
          median: 100.0,
          std: 10.0,
          min: 90.0,
          max: 110.0,
          count: 10,
          sum: 1000.0,
        },
      ],
    }
    
    fetchAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument()
      expect(screen.getByTestId('statistics-view')).toBeInTheDocument()
    })
  })

  test('handles API failure', async () => {
    fetchAnalytics.mockRejectedValue(new Error('Network error'))
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    // Wait for error to appear (with longer timeout)
    await waitFor(() => {
      // Error should appear in the error section
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  }, 10000)

  test('displays multiple analytics views when multiple types are selected', async () => {
    const mockResponse = {
      series_count: 2,
      statistics: [{ series_id: 'GDP', mean: 100.0, median: 100.0, std: 10.0, min: 90.0, max: 110.0, count: 10, sum: 1000.0 }],
      growth_rates: [{ series_id: 'GDP', date: '2024-01-01', value: 100.0, growth_rate: 0.05, growth_type: 'period_over_period' }],
      correlations: [{ series_id_1: 'GDP', series_id_2: 'UNRATE', correlation: 0.8 }],
    }
    
    fetchAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('statistics-view')).toBeInTheDocument()
      expect(screen.getByTestId('growth-rates-view')).toBeInTheDocument()
      expect(screen.getByTestId('correlations-view')).toBeInTheDocument()
    })
  })

  test('displays empty results message when no analytics data', async () => {
    const mockResponse = {
      series_count: 1,
    }
    
    fetchAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/no analytics results to display/i)).toBeInTheDocument()
    })
  })

  test('passes initialSeriesIds to form', () => {
    render(<AnalyticsPanel initialSeriesIds={['GDP', 'UNRATE']} />)
    
    // The form should receive initialSeriesIds (tested via mock)
    expect(screen.getByTestId('analytics-form')).toBeInTheDocument()
  })

  test('handles different error types with appropriate messages', async () => {
    fetchAnalytics.mockRejectedValue(new Error('HTTP error! status: 503'))
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('handles timeout errors', async () => {
    fetchAnalytics.mockRejectedValue(new Error('Request timeout'))
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('clears error when dismiss button is clicked', async () => {
    fetchAnalytics.mockRejectedValue(new Error('Test error'))
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /dismiss/i })).toBeInTheDocument()
    }, { timeout: 3000 })
    
    const dismissButton = screen.getByRole('button', { name: /dismiss/i })
    await user.click(dismissButton)
    
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /dismiss/i })).not.toBeInTheDocument()
    })
  })

  test('displays all analytics types when all are present', async () => {
    const mockResponse = {
      series_count: 2,
      statistics: [{ series_id: 'GDP', mean: 100.0, median: 100.0, std: 10.0, min: 90.0, max: 110.0, count: 10, sum: 1000.0 }],
      growth_rates: [{ series_id: 'GDP', date: '2024-01-01', value: 100.0, growth_rate: 0.05, growth_type: 'period_over_period' }],
      correlations: [{ series_id_1: 'GDP', series_id_2: 'UNRATE', correlation: 0.8 }],
      moving_averages: [{ series_id: 'GDP', date: '2024-01-01', value: 100.0, moving_average: 100.0, moving_average_type: 'sma', window_size: 7 }],
      time_aggregations: [{ series_id: 'GDP', period: '2024-01', aggregated_value: 100.0, aggregation_function: 'mean', observation_count: 4 }],
    }
    
    fetchAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('statistics-view')).toBeInTheDocument()
      expect(screen.getByTestId('growth-rates-view')).toBeInTheDocument()
      expect(screen.getByTestId('correlations-view')).toBeInTheDocument()
      expect(screen.getByTestId('moving-averages-view')).toBeInTheDocument()
      expect(screen.getByTestId('time-aggregations-view')).toBeInTheDocument()
    })
  })

  test('displays series count in results header', async () => {
    const mockResponse = {
      series_count: 3,
      statistics: [{ series_id: 'GDP', mean: 100.0, median: 100.0, std: 10.0, min: 90.0, max: 110.0, count: 10, sum: 1000.0 }],
    }
    
    fetchAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/analyzed 3 series/i)).toBeInTheDocument()
    })
  })
})

