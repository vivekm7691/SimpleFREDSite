/**
 * Tests for AdvancedAnalyticsPanel component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AdvancedAnalyticsPanel from '../src/components/AdvancedAnalyticsPanel'
import { fetchAdvancedAnalytics } from '../src/services/api'

// Mock the API service
jest.mock('../src/services/api', () => ({
  fetchAdvancedAnalytics: jest.fn(),
}))

// Mock AdvancedAnalyticsForm
jest.mock('../src/components/AdvancedAnalyticsForm', () => {
  return function MockAdvancedAnalyticsForm({ onSubmit, loading, initialSeriesIds }) {
    return (
      <div data-testid="advanced-analytics-form">
        <button
          onClick={() => onSubmit({
            series_ids: initialSeriesIds.length > 0 ? initialSeriesIds : ['GDP'],
            analytics_types: ['forecasts'],
            limit: 100,
            sort_order: 'desc',
            use_cache: true,
            forecast_horizon: 12,
            forecast_method: 'linear_regression',
          })}
          disabled={loading}
        >
          {loading ? 'Running Advanced Analytics...' : 'Run Advanced Analytics'}
        </button>
      </div>
    )
  }
})

// Mock advanced analytics visualization components
jest.mock('../src/components/advanced-analytics', () => ({
  ForecastsView: ({ data }) => <div data-testid="forecasts-view">Forecasts: {data.length} items</div>,
  TrendsView: ({ data }) => <div data-testid="trends-view">Trends: {data.length} items</div>,
  AnomaliesView: ({ data }) => <div data-testid="anomalies-view">Anomalies: {data.length} items</div>,
  SeasonalDecompositionView: ({ data }) => <div data-testid="seasonal-decomposition-view">Seasonal Decomposition: {data.length} items</div>,
  VolatilityView: ({ data }) => <div data-testid="volatility-view">Volatility: {data.length} items</div>,
}))

describe('AdvancedAnalyticsPanel Component', () => {
  beforeEach(() => {
    fetchAdvancedAnalytics.mockClear()
  })

  test('renders advanced analytics panel with header', () => {
    render(<AdvancedAnalyticsPanel />)
    
    expect(screen.getByText(/advanced analytics dashboard/i)).toBeInTheDocument()
    expect(screen.getByText(/perform advanced analytics including forecasting/i)).toBeInTheDocument()
  })

  test('renders advanced analytics form', () => {
    render(<AdvancedAnalyticsPanel />)
    
    expect(screen.getByTestId('advanced-analytics-form')).toBeInTheDocument()
  })

  test('shows loading state when fetching advanced analytics', async () => {
    fetchAdvancedAnalytics.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const loadingElements = screen.getAllByText(/running advanced analytics/i)
      expect(loadingElements.length).toBeGreaterThan(0)
    })
  })

  test('displays advanced analytics results after successful fetch', async () => {
    const mockResponse = {
      series_count: 1,
      forecasts: [
        {
          series_id: 'GDP',
          date: '2024-12-01',
          forecasted_value: 110.0,
          lower_bound: 105.0,
          upper_bound: 115.0,
          confidence_level: 0.95,
          forecast_method: 'linear_regression',
        },
      ],
    }
    
    fetchAdvancedAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument()
      expect(screen.getByTestId('forecasts-view')).toBeInTheDocument()
    })
  })

  test('handles API failure', async () => {
    fetchAdvancedAnalytics.mockRejectedValue(new Error('Network error'))
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  }, 10000)

  test('displays multiple advanced analytics views when multiple types are selected', async () => {
    const mockResponse = {
      series_count: 2,
      forecasts: [{ series_id: 'GDP', date: '2024-12-01', forecasted_value: 110.0, lower_bound: 105.0, upper_bound: 115.0, confidence_level: 0.95, forecast_method: 'linear_regression' }],
      trends: [{ series_id: 'GDP', trend_type: 'linear', slope: 0.5, intercept: 100.0, r_squared: 0.95, direction: 'increasing' }],
      anomalies: [{ series_id: 'GDP', date: '2024-01-01', value: 150.0, expected_value: 100.0, deviation: 5.0, detection_method: 'z_score', severity: 'high' }],
    }
    
    fetchAdvancedAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('forecasts-view')).toBeInTheDocument()
      expect(screen.getByTestId('trends-view')).toBeInTheDocument()
      expect(screen.getByTestId('anomalies-view')).toBeInTheDocument()
    })
  })

  test('displays empty results message when no advanced analytics data', async () => {
    const mockResponse = {
      series_count: 1,
    }
    
    fetchAdvancedAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/no advanced analytics results to display/i)).toBeInTheDocument()
    })
  })

  test('passes initialSeriesIds to form', () => {
    render(<AdvancedAnalyticsPanel initialSeriesIds={['GDP', 'UNRATE']} />)
    
    expect(screen.getByTestId('advanced-analytics-form')).toBeInTheDocument()
  })

  test('handles different error types with appropriate messages', async () => {
    fetchAdvancedAnalytics.mockRejectedValue(new Error('HTTP error! status: 503'))
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('handles timeout errors', async () => {
    fetchAdvancedAnalytics.mockRejectedValue(new Error('Request timeout'))
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorHeading = screen.queryByRole('heading', { name: /error/i })
      expect(errorHeading).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('clears error when dismiss button is clicked', async () => {
    fetchAdvancedAnalytics.mockRejectedValue(new Error('Test error'))
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
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

  test('displays all advanced analytics types when all are present', async () => {
    const mockResponse = {
      series_count: 2,
      forecasts: [{ series_id: 'GDP', date: '2024-12-01', forecasted_value: 110.0, lower_bound: 105.0, upper_bound: 115.0, confidence_level: 0.95, forecast_method: 'linear_regression' }],
      trends: [{ series_id: 'GDP', trend_type: 'linear', slope: 0.5, intercept: 100.0, r_squared: 0.95, direction: 'increasing' }],
      anomalies: [{ series_id: 'GDP', date: '2024-01-01', value: 150.0, expected_value: 100.0, deviation: 5.0, detection_method: 'z_score', severity: 'high' }],
      seasonal_decompositions: [{ series_id: 'GDP', date: '2024-01-01', actual_value: 100.0, trend_component: 95.0, seasonal_component: 5.0, residual_component: 0.0, decomposition_type: 'additive' }],
      volatility: [{ series_id: 'GDP', date: '2024-01-01', volatility: 0.05, annualized_volatility: 0.15, return_value: 0.02, window_size: 30 }],
    }
    
    fetchAdvancedAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('forecasts-view')).toBeInTheDocument()
      expect(screen.getByTestId('trends-view')).toBeInTheDocument()
      expect(screen.getByTestId('anomalies-view')).toBeInTheDocument()
      expect(screen.getByTestId('seasonal-decomposition-view')).toBeInTheDocument()
      expect(screen.getByTestId('volatility-view')).toBeInTheDocument()
    })
  })

  test('displays series count in results header', async () => {
    const mockResponse = {
      series_count: 3,
      forecasts: [{ series_id: 'GDP', date: '2024-12-01', forecasted_value: 110.0, lower_bound: 105.0, upper_bound: 115.0, confidence_level: 0.95, forecast_method: 'linear_regression' }],
    }
    
    fetchAdvancedAnalytics.mockResolvedValue(mockResponse)
    
    const user = userEvent.setup()
    render(<AdvancedAnalyticsPanel />)
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/analyzed 3 series/i)).toBeInTheDocument()
    })
  })
})

