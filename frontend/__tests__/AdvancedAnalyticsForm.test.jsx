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
    expect(screen.getByText(/trends/i)).toBeInTheDocument()
    expect(screen.getByText(/seasonal decomposition/i)).toBeInTheDocument()
    expect(screen.getByText(/volatility/i)).toBeInTheDocument()
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
      expect(screen.getByLabelText(/anomaly method/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/anomaly threshold/i)).toBeInTheDocument()
    })
  })

  test('shows trend analysis parameters when trends is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/trend analysis/i))
    
    await waitFor(() => {
      expect(screen.getByLabelText(/trend type/i)).toBeInTheDocument()
    })
  })

  test('shows polynomial degree when polynomial trend is selected', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/trend analysis/i))
    
    const trendTypeSelect = screen.getByLabelText(/trend type/i)
    await user.selectOptions(trendTypeSelect, 'polynomial')
    
    await waitFor(() => {
      expect(screen.getByLabelText(/polynomial degree/i)).toBeInTheDocument()
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
    
    const anomalyMethodSelect = screen.getByLabelText(/anomaly method/i)
    await user.selectOptions(anomalyMethodSelect, 'iqr')
    
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

  test('validates forecast horizon is positive', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByLabelText(/forecasts/i))
    
    const forecastHorizonInput = screen.getByLabelText(/forecast horizon/i)
    fireEvent.change(forecastHorizonInput, { target: { value: '-5' } })
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/forecast horizon must be between 1 and 120/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates anomaly threshold is positive', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/anomaly detection/i))
    
    const anomalyThresholdInput = screen.getByLabelText(/anomaly threshold/i)
    fireEvent.change(anomalyThresholdInput, { target: { value: '-1' } })
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/anomaly threshold must be positive/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates polynomial degree is at least 2', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/trend analysis/i))
    
    const trendTypeSelect = screen.getByLabelText(/trend type/i)
    await user.selectOptions(trendTypeSelect, 'polynomial')
    
    const polynomialDegreeInput = screen.getByLabelText(/polynomial degree/i)
    fireEvent.change(polynomialDegreeInput, { target: { value: '1' } })
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/polynomial degree must be at least 2/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates seasonal period is positive', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText(/seasonal decomposition/i))
    
    const seasonalPeriodInput = screen.getByLabelText(/seasonal period/i)
    fireEvent.change(seasonalPeriodInput, { target: { value: '0' } })
    
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/seasonal period must be between/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates volatility window is positive', async () => {
    const user = userEvent.setup()
    render(<AdvancedAnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Find and click the volatility checkbox - use getAllByText to find the checkbox label
    const volatilityTexts = screen.getAllByText(/volatility analysis/i)
    const volatilityCheckboxLabel = volatilityTexts.find(el => 
      el.tagName === 'SPAN' && el.closest('label.checkbox-label')
    )
    expect(volatilityCheckboxLabel).toBeTruthy()
    await user.click(volatilityCheckboxLabel.closest('label'))
    
    // Wait for the volatility parameters section to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/rolling window size/i)).toBeInTheDocument()
    })
    
    const volatilityWindowInput = screen.getByLabelText(/rolling window size/i)
    // Clear and type the invalid value
    await user.clear(volatilityWindowInput)
    await user.type(volatilityWindowInput, '400')
    
    // Fill in required field
    await user.type(screen.getByLabelText(/series ids/i), 'GDP')
    
    const submitButton = screen.getByRole('button', { name: /run advanced analytics/i })
    await user.click(submitButton)
    
    // The validation should catch the invalid value (400 > 365)
    await waitFor(() => {
      expect(screen.getByText(/volatility window must be between/i)).toBeInTheDocument()
    }, { timeout: 3000 })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })
})

