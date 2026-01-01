/**
 * Tests for App component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'
import { fetchFREDData, summarizeData } from '../src/services/api'

// Mock the API service
jest.mock('../src/services/api', () => ({
  fetchFREDData: jest.fn(),
  summarizeData: jest.fn(),
}))

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render the app with header and form', () => {
    render(<App />)

    expect(screen.getByText('Simple FRED Site')).toBeInTheDocument()
    expect(screen.getByText('Fetch and summarize economic data from FRED')).toBeInTheDocument()
    expect(screen.getByLabelText('FRED Series ID:')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('e.g., GDP, UNRATE, CPIAUCSL')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /fetch & summarize/i })).toBeInTheDocument()
  })

  it('should update input value when user types', async () => {
    const user = userEvent.setup()
    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    await user.type(input, 'GDP')

    expect(input).toHaveValue('GDP')
  })

  it('should show error when submitting empty form', async () => {
    const user = userEvent.setup()
    render(<App />)

    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/please enter a fred series id/i)).toBeInTheDocument()
    })
  })

  it('should show error when submitting form with only whitespace', async () => {
    const user = userEvent.setup()
    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, '   ')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/please enter a fred series id/i)).toBeInTheDocument()
    })
  })

  it('should fetch and display FRED data successfully', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: {
        id: 'GDP',
        title: 'Gross Domestic Product',
        units: 'Billions of Dollars',
        frequency: 'Quarterly',
        seasonal_adjustment: 'Seasonally Adjusted Annual Rate',
      },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
        { date: '2023-10-01', value: 24800.0 },
      ],
      observation_count: 2,
    }

    const mockSummary = 'This is a test summary of the economic data.'

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce(mockSummary)

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    // Verify API calls
    expect(fetchFREDData).toHaveBeenCalledWith('GDP')
    expect(summarizeData).toHaveBeenCalledWith(mockFREDData)

    // Wait for data to appear
    await waitFor(() => {
      expect(screen.getByText('FRED Economic Data')).toBeInTheDocument()
    })

    expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument()
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText('Billions of Dollars')).toBeInTheDocument()
    expect(screen.getByText('Quarterly')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()

    // Check observations table
    expect(screen.getByText('Recent Data Points')).toBeInTheDocument()
    expect(screen.getByText('2024-01-01')).toBeInTheDocument()
    expect(screen.getByText('25,000')).toBeInTheDocument()

    // Check summary
    await waitFor(() => {
      expect(screen.getByText('AI-Powered Summary')).toBeInTheDocument()
    })
    expect(screen.getByText(mockSummary)).toBeInTheDocument()
  })

  it('should show loading state during fetch', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [],
      observation_count: 0,
    }

    // Delay the promise resolution
    fetchFREDData.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockFREDData), 100))
    )
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    // Check loading state
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })
  })

  it('should handle API errors and display error message', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Series not found'

    fetchFREDData.mockRejectedValueOnce(new Error(errorMessage))

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'INVALID')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(new RegExp(errorMessage, 'i'))).toBeInTheDocument()
    })

    // Verify data sections are not displayed
    expect(screen.queryByText('FRED Economic Data')).not.toBeInTheDocument()
    expect(screen.queryByText('AI-Powered Summary')).not.toBeInTheDocument()
  })

  it('should handle generic errors', async () => {
    const user = userEvent.setup()

    fetchFREDData.mockRejectedValueOnce(new Error('Network error'))

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })

  it('should display observations table with formatted values', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.5 },
        { date: '2023-12-01', value: null },
        { date: '2023-11-01', value: 24800.25 },
      ],
      observation_count: 3,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Recent Data Points')).toBeInTheDocument()
    })

    // Check formatted values
    expect(screen.getByText('25,000.5')).toBeInTheDocument()
    expect(screen.getByText('N/A')).toBeInTheDocument() // null value
    expect(screen.getByText('24,800.25')).toBeInTheDocument()
  })

  it('should limit displayed observations to 20', async () => {
    const user = userEvent.setup()
    const observations = Array.from({ length: 25 }, (_, i) => ({
      date: `2024-${String(i + 1).padStart(2, '0')}-01`,
      value: 1000 + i,
    }))

    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations,
      observation_count: 25,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/showing 20 of 25 observations/i)).toBeInTheDocument()
    })
  })

  it('should convert series ID to uppercase', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [],
      observation_count: 0,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'gdp')
    await user.click(submitButton)

    // Verify API was called with uppercase
    expect(fetchFREDData).toHaveBeenCalledWith('GDP')
  })

  it('should clear previous data when submitting new request', async () => {
    const user = userEvent.setup()
    const mockFREDData1 = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [],
      observation_count: 0,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData1)
    summarizeData.mockResolvedValueOnce('Summary 1')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    // First submission
    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('FRED Economic Data')).toBeInTheDocument()
    })

    // Second submission with error
    const errorMessage = 'Test error message'
    fetchFREDData.mockRejectedValueOnce(new Error(errorMessage))
    await user.clear(input)
    await user.type(input, 'INVALID')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.queryByText('FRED Economic Data')).not.toBeInTheDocument()
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})

