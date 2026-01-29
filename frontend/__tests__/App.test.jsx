/**
 * Tests for App component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'
import { fetchFREDData, summarizeData, fetchCategories } from '../src/services/api'

// Mock the API service
jest.mock('../src/services/api', () => ({
  fetchFREDData: jest.fn(),
  summarizeData: jest.fn(),
  fetchCategories: jest.fn(),
}))

// Mock Sidebar component to avoid CategoryBrowser API calls in tests
jest.mock('../src/components/Sidebar', () => {
  return function MockSidebar({ onSeriesSelect }) {
    return <div data-testid="sidebar">Mock Sidebar</div>
  }
})

// Mock DataGraph component to avoid Chart.js canvas issues in jsdom
jest.mock('../src/components/DataGraph', () => {
  return function MockDataGraph({ data, seriesInfo }) {
    if (!data || !data.observations || data.observations.length === 0) {
      return <div data-testid="data-graph">No data available to display</div>
    }
    return (
      <div data-testid="data-graph">
        <div>Chart for {seriesInfo?.title || data.series_id}</div>
        <div>Showing {data.observations.length} observations</div>
      </div>
    )
  }
})

// Mock AnalyticsPanel and AdvancedAnalyticsPanel
jest.mock('../src/components/AnalyticsPanel', () => {
  return function MockAnalyticsPanel({ initialSeriesIds }) {
    return <div data-testid="analytics-panel">Analytics Panel: {initialSeriesIds.join(', ')}</div>
  }
})

jest.mock('../src/components/AdvancedAnalyticsPanel', () => {
  return function MockAdvancedAnalyticsPanel({ initialSeriesIds }) {
    return <div data-testid="advanced-analytics-panel">Advanced Analytics Panel: {initialSeriesIds.join(', ')}</div>
  }
})

describe('App Component', () => {
  const mockCategories = {
    categories: [
      {
        id: 'employment',
        name: 'Employment',
        icon: '📊',
        description: 'Labor market indicators',
        series_count: 12,
      },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock scrollIntoView for jsdom (not fully implemented)
    Element.prototype.scrollIntoView = jest.fn()
    // Mock fetchCategories to prevent errors from Sidebar/CategoryBrowser
    fetchCategories.mockResolvedValue(mockCategories)
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

    // Wait for data to appear - check for series info instead of "FRED Economic Data"
    await waitFor(() => {
      expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument()
    })

    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText('Billions of Dollars')).toBeInTheDocument()
    expect(screen.getByText('Quarterly')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()

    // Check DataGraph is rendered (replaces observations table)
    await waitFor(() => {
      expect(screen.getByTestId('data-graph')).toBeInTheDocument()
    })
    expect(screen.getByText(/Chart for/i)).toBeInTheDocument()
    expect(screen.getByText(/2 observations/i)).toBeInTheDocument()

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
    }, { timeout: 2000 })
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

  it('should display DataGraph with observations', async () => {
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

    // Check DataGraph is rendered (replaces observations table)
    await waitFor(() => {
      expect(screen.getByTestId('data-graph')).toBeInTheDocument()
    })
    expect(screen.getByText(/3 observations/i)).toBeInTheDocument()
  })

  it('should display all observations in DataGraph', async () => {
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

    // DataGraph shows all observations (no 20 limit like the old table)
    await waitFor(() => {
      expect(screen.getByTestId('data-graph')).toBeInTheDocument()
    })
    expect(screen.getByText(/25 observations/i)).toBeInTheDocument()
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
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData1)
    summarizeData.mockResolvedValueOnce('Summary 1')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    // First submission
    await user.type(input, 'GDP')
    await user.click(submitButton)

    // Wait for data to appear - check for data-graph
    await waitFor(() => {
      expect(screen.getByTestId('data-graph')).toBeInTheDocument()
    })

    // Second submission with error
    const errorMessage = 'Test error message'
    fetchFREDData.mockRejectedValueOnce(new Error(errorMessage))
    await user.clear(input)
    await user.type(input, 'INVALID')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.queryByTestId('data-graph')).not.toBeInTheDocument()
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should display analytics tab when data is loaded', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      const analyticsButtons = screen.getAllByRole('button', { name: /analytics/i })
      expect(analyticsButtons.length).toBeGreaterThan(0)
    })
  })

  it('should display advanced analytics tab when data is loaded', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /advanced analytics/i })).toBeInTheDocument()
    })
  })

  it('should switch to analytics tab when clicked', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      const analyticsButtons = screen.getAllByRole('button', { name: /analytics/i })
      expect(analyticsButtons.length).toBeGreaterThan(0)
    })

    const analyticsButtons = screen.getAllByRole('button', { name: /analytics/i })
    const analyticsTab = analyticsButtons.find(btn => btn.textContent === 'Analytics')
    expect(analyticsTab).toBeInTheDocument()
    await user.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getByTestId('analytics-panel')).toBeInTheDocument()
      expect(screen.getByText(/analytics panel: gdp/i)).toBeInTheDocument()
    })
  })

  it('should switch to advanced analytics tab when clicked', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /advanced analytics/i })).toBeInTheDocument()
    })

    const advancedAnalyticsTab = screen.getByRole('button', { name: /advanced analytics/i })
    await user.click(advancedAnalyticsTab)

    await waitFor(() => {
      expect(screen.getByTestId('advanced-analytics-panel')).toBeInTheDocument()
      expect(screen.getByText(/advanced analytics panel: gdp/i)).toBeInTheDocument()
    })
  })

  it('should pass initialSeriesIds to analytics panels', async () => {
    const user = userEvent.setup()
    const mockFREDData = {
      series_id: 'GDP',
      series_info: { id: 'GDP', title: 'GDP' },
      observations: [
        { date: '2024-01-01', value: 25000.0 },
      ],
      observation_count: 1,
    }

    fetchFREDData.mockResolvedValueOnce(mockFREDData)
    summarizeData.mockResolvedValueOnce('Summary')

    render(<App />)

    const input = screen.getByLabelText('FRED Series ID:')
    const submitButton = screen.getByRole('button', { name: /fetch & summarize/i })

    await user.type(input, 'GDP')
    await user.click(submitButton)

    await waitFor(() => {
      const analyticsButtons = screen.getAllByRole('button', { name: /analytics/i })
      expect(analyticsButtons.length).toBeGreaterThan(0)
    })

    const analyticsButtons = screen.getAllByRole('button', { name: /analytics/i })
    const analyticsTab = analyticsButtons.find(btn => btn.textContent === 'Analytics')
    expect(analyticsTab).toBeInTheDocument()
    await user.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getByText(/analytics panel: gdp/i)).toBeInTheDocument()
    })

    const advancedAnalyticsTab = screen.getByRole('button', { name: /advanced analytics/i })
    await user.click(advancedAnalyticsTab)

    await waitFor(() => {
      expect(screen.getByText(/advanced analytics panel: gdp/i)).toBeInTheDocument()
    })
  })
})

