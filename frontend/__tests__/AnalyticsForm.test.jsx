/**
 * Tests for AnalyticsForm component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AnalyticsForm from '../src/components/AnalyticsForm'

describe('AnalyticsForm Component', () => {
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
  })

  test('renders form with all input fields', () => {
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    expect(screen.getByLabelText(/series ids/i)).toBeInTheDocument()
    expect(screen.getByText(/statistics/i)).toBeInTheDocument()
    expect(screen.getByText(/growth rates/i)).toBeInTheDocument()
    expect(screen.getByText(/correlations/i)).toBeInTheDocument()
    expect(screen.getByText(/moving averages/i)).toBeInTheDocument()
    expect(screen.getByText(/time aggregations/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/limit/i)).toBeInTheDocument()
  })

  test('initializes with initialSeriesIds', () => {
    render(<AnalyticsForm onSubmit={mockOnSubmit} initialSeriesIds={['GDP', 'UNRATE']} />)
    
    const seriesInput = screen.getByLabelText(/series ids/i)
    expect(seriesInput).toHaveValue('GDP, UNRATE')
  })

  test('validates empty series IDs on submit', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Select an analytics type
    await user.click(screen.getByLabelText(/statistics/i))
    
    // Try to submit without series IDs
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/at least one series id is required/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('validates analytics types selection on submit', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Enter series IDs but don't select any analytics type
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    
    // Try to submit without selecting analytics types
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/at least one analytics type is required/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  test('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Fill in form
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    
    await user.click(screen.getByLabelText(/statistics/i))
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        series_ids: ['GDP'],
        analytics_types: ['statistics'],
        limit: 100,
        sort_order: 'desc',
        use_cache: true,
      })
    })
  })

  test('shows moving averages parameters when moving averages is selected', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Select moving averages
    await user.click(screen.getByLabelText(/moving averages/i))
    
    // Check that moving average parameters appear
    expect(screen.getByLabelText(/window size/i)).toBeInTheDocument()
    expect(screen.getByText(/simple moving average/i)).toBeInTheDocument()
  })

  test('shows time aggregations parameters when time aggregations is selected', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Select time aggregations
    await user.click(screen.getByLabelText(/time aggregations/i))
    
    // Check that time aggregation parameters appear
    expect(screen.getByText(/period/i)).toBeInTheDocument()
    expect(screen.getByText(/function/i)).toBeInTheDocument()
  })

  test('disables form when loading', () => {
    render(<AnalyticsForm onSubmit={mockOnSubmit} loading={true} />)
    
    const seriesInput = screen.getByLabelText(/series ids/i)
    expect(seriesInput).toBeDisabled()
    
    const submitButton = screen.getByRole('button', { name: /running analytics/i })
    expect(submitButton).toBeDisabled()
  })

  test('validates correlations require 2+ series', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} />)
    
    // Enter only one series
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.type(seriesInput, 'GDP')
    
    // Select correlations
    await user.click(screen.getByLabelText(/correlations/i))
    
    // Try to submit
    const submitButton = screen.getByRole('button', { name: /run analytics/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/correlations require at least 2 series/i)).toBeInTheDocument()
    })
  })

  test('resets form when reset button is clicked', async () => {
    const user = userEvent.setup()
    render(<AnalyticsForm onSubmit={mockOnSubmit} initialSeriesIds={['GDP']} />)
    
    // Fill in form
    const seriesInput = screen.getByLabelText(/series ids/i)
    await user.clear(seriesInput)
    await user.type(seriesInput, 'UNRATE, CPIAUCSL')
    
    await user.click(screen.getByLabelText(/statistics/i))
    
    // Verify form is filled
    expect(seriesInput).toHaveValue('UNRATE, CPIAUCSL')
    expect(screen.getByLabelText(/statistics/i)).toBeChecked()
    
    // Reset
    const resetButton = screen.getByRole('button', { name: /reset/i })
    await user.click(resetButton)
    
    // Form should be reset (checkboxes cleared, values reset to defaults)
    expect(screen.getByLabelText(/statistics/i)).not.toBeChecked()
    // Note: Reset may not restore initialSeriesIds, it resets to empty/defaults
  })
})

