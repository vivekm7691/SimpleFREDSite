/**
 * Tests for AdvancedAnalyticsForm component
 */
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AdvancedAnalyticsForm from '../src/components/AdvancedAnalyticsForm'

describe('AdvancedAnalyticsForm Component', () => {
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
  })

  test('renders form with all input fields', () => {
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    expect(screen.getByLabelText(/series ids/i)).toBeInTheDocument()
    expect(screen.getByText(/forecasts/i)).toBeInTheDocument()
    expect(screen.getByText(/anomaly detection/i)).toBeInTheDocument()
    // Use getAllByText since "Trend Analysis" appears in checkbox label
    expect(screen.getAllByText(/trend analysis/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/seasonal decomposition/i)).toBeInTheDocument()
    // Use getAllByText since "Volatility Analysis" appears in checkbox label and heading
    expect(screen.getAllByText(/volatility analysis/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/limit/i)).toBeInTheDocument()
  })

  test('initializes with initialSeriesIds', () => {
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} initialSeriesIds={['GDP', 'UNRATE']} />)
    
    const seriesInput = screen.getByLabelText(/series ids/i)
    expect(seriesInput).toHaveValue('GDP, UNRATE')
  })

  test('validates empty series IDs on submit', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Select an analytics type
    await user.click(screen.getByLabelText(/forecasts/i))
    
    // Try to submit without series IDs
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/at least one series id is required/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates analytics types selection on submit', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Enter series IDs but don't select any analytics type
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    
    // Try to submit
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/at least one analytics type is required/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Fill in form
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    
    await user.click(screen.getByLabelText(/forecasts/i))
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          series_ids: ['GDP'],
          analytics_types: ['forecasts'],
          limit: 100,
          sort_order: 'desc',
          use_cache: true,
        })
      )
    })
  })

  test('shows forecasting parameters when forecasts is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByLabelText(/forecasts/i))
    
    await waitFor(() => {
      expect(screen.getByLabelText(/forecast horizon/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/forecast method/i)).toBeInTheDocument()
    })
  })

  test('shows anomaly detection parameters when anomalies is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/anomaly detection/i))
    
    await waitFor(() => {
      expect(screen.getByLabelText(/detection method/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/z-score threshold/i)).toBeInTheDocument()
    })
  })

  test('shows trend analysis parameters when trends is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/trend analysis/i))
    
    await waitFor(() => {
      // Trend Type is a radio group, so we check for the label text
      expect(screen.getByText(/trend type/i)).toBeInTheDocument()
      expect(screen.getByText(/linear/i)).toBeInTheDocument()
      expect(screen.getByText(/polynomial/i)).toBeInTheDocument()
    })
  })

  test('shows polynomial degree when polynomial trend is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/trend analysis/i))
    
    // Wait for trend type radio buttons to appear
    await waitFor(() => {
      expect(screen.getByText(/trend type/i)).toBeInTheDocument()
    })
    
    // Click the polynomial radio button
    const polynomialRadio = screen.getByLabelText(/polynomial/i)
    await user.click(polynomialRadio)
    
    await waitFor(() => {
      const polynomialDegreeInput = screen.getByLabelText(/polynomial degree/i)
      expect(polynomialDegreeInput).toBeInTheDocument()
    })
  })

  test('shows seasonal decomposition parameters when seasonal_decomposition is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/seasonal decomposition/i))
    
    await waitFor(() => {
      expect(screen.getByText(/decomposition type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/seasonal period/i)).toBeInTheDocument()
    })
  })

  test('shows volatility parameters when volatility is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/volatility analysis/i))
    
    await waitFor(() => {
      expect(screen.getByLabelText(/rolling window size/i)).toBeInTheDocument()
    })
  })

  test('disables submit button when loading', () => {
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} loading={true} />)
    
    const submitButton = screen.getByRole('button', { name: /running advanced analytics/i })
    expect(submitButton).toBeDisabled()
  })

  test('resets form when reset button is clicked', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Fill in form
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    await user.click(screen.getByLabelText(/forecasts/i))
    
    // Reset
    const resetButton = screen.getByRole('button', { name: /reset/i })
    await user.click(resetButton)
    
    expect(seriesInput).toHaveValue('')
    expect(screen.getByLabelText(/forecasts/i)).not.toBeChecked()
  })

  test('parses multiple series IDs correctly', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP, UNRATE, CPIAUCSL')
    
    await user.click(screen.getByLabelText(/forecasts/i))
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          series_ids: ['GDP', 'UNRATE', 'CPIAUCSL'],
        })
      )
    })
  })

  test('handles forecast method selection', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByLabelText(/forecasts/i))
    
    const forecastMethodSelect = screen.getByLabelText(/forecast method/i)
    await user.selectOptions(forecastMethodSelect, 'arima')
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          forecast_method: 'arima',
        })
      )
    })
  })

  test('handles anomaly method selection', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/anomaly detection/i))
    
    await waitFor(() => {
      expect(screen.getByLabelText(/detection method/i)).toBeInTheDocument()
    })
    
    const anomalyMethodSelect = screen.getByLabelText(/detection method/i)
    await user.selectOptions(anomalyMethodSelect, 'iqr')
    
    await waitFor(() => {
      // IQR method doesn't require threshold, so threshold input should not be visible
      expect(screen.queryByLabelText(/z-score threshold/i)).not.toBeInTheDocument()
    })
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          anomaly_method: 'iqr',
        })
      )
    })
  })

})

