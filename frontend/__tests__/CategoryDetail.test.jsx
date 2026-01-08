/**
 * Tests for CategoryDetail component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CategoryDetail from '../src/components/CategoryDetail'
import { fetchCategorySeries } from '../src/services/api'

// Mock the API module
jest.mock('../src/services/api', () => ({
  fetchCategorySeries: jest.fn(),
}))

// Mock SeriesCard component
jest.mock('../src/components/SeriesCard', () => {
  return function MockSeriesCard({ series, onSelect }) {
    return (
      <div data-testid={`series-card-${series.id}`}>
        <span>{series.title}</span>
        <button onClick={() => onSelect(series.id)}>Select</button>
      </div>
    )
  }
})

describe('CategoryDetail Component', () => {
  const mockOnBack = jest.fn()
  const mockOnSeriesSelect = jest.fn()

  const mockSeriesResponse = {
    category_name: 'Employment',
    total_count: 2,
    series: [
      {
        id: 'UNRATE',
        title: 'Unemployment Rate',
        frequency: 'Monthly',
        units: 'Percent',
      },
      {
        id: 'PAYEMS',
        title: 'Total Nonfarm Payrolls',
        frequency: 'Monthly',
        units: 'Thousands of Persons',
      },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
    fetchCategorySeries.mockResolvedValue(mockSeriesResponse)
  })

  it('should render loading state initially', () => {
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    expect(screen.getByText('Loading series...')).toBeInTheDocument()
  })

  it('should fetch and display series after loading', async () => {
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(fetchCategorySeries).toHaveBeenCalledWith('employment', null)
    })

    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
      expect(screen.getByText('(2 series)')).toBeInTheDocument()
    })

    expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    expect(screen.getByText('Total Nonfarm Payrolls')).toBeInTheDocument()
  })

  it('should display category name from prop when provided', async () => {
    render(
      <CategoryDetail
        categoryId="employment"
        categoryName="Employment Category"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Employment Category')).toBeInTheDocument()
    })
  })

  it('should display category name from API when prop not provided', async () => {
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
    })
  })

  it('should call onBack when back button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back to Categories/i })
    await user.click(backButton)

    expect(mockOnBack).toHaveBeenCalledTimes(1)
  })

  it('should handle search input changes', async () => {
    const user = userEvent.setup()
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search in category...')
    await user.type(searchInput, 'unemployment')

    await waitFor(() => {
      expect(fetchCategorySeries).toHaveBeenCalledWith('employment', 'unemployment')
    })
  })

  it('should call onSeriesSelect when a series is selected', async () => {
    const user = userEvent.setup()
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByText('Select')
    await user.click(selectButtons[0])

    expect(mockOnSeriesSelect).toHaveBeenCalledWith('UNRATE')
  })

  it('should display error message when API call fails', async () => {
    fetchCategorySeries.mockRejectedValue(new Error('Network error'))

    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument()
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })
  })

  it('should display empty state when no series are available', async () => {
    fetchCategorySeries.mockResolvedValue({
      category_name: 'Empty Category',
      total_count: 0,
      series: [],
    })

    render(
      <CategoryDetail
        categoryId="empty"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('No series available in this category')).toBeInTheDocument()
    })
  })

  it('should display search empty state when search returns no results', async () => {
    const user = userEvent.setup()
    
    // Use mockImplementation to handle calls based on search term
    fetchCategorySeries.mockImplementation((categoryId, searchTerm) => {
      if (searchTerm === 'nonexistent') {
        return Promise.resolve({
          category_name: 'Employment',
          total_count: 0,
          series: [],
        })
      }
      return Promise.resolve(mockSeriesResponse)
    })

    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
      expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search in category...')
    await user.clear(searchInput)
    await user.type(searchInput, 'nonexistent')

    // Wait for search API call to complete and UI to update
    await waitFor(() => {
      expect(screen.queryByText('Unemployment Rate')).not.toBeInTheDocument()
      expect(screen.getByText(/No series found matching "nonexistent"/)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should display search results count when search is active', async () => {
    const user = userEvent.setup()
    
    // Use mockImplementation to handle calls based on search term
    fetchCategorySeries.mockImplementation((categoryId, searchTerm) => {
      if (searchTerm === 'unemployment') {
        return Promise.resolve({
          category_name: 'Employment',
          total_count: 10,
          series: [mockSeriesResponse.series[0]], // Only one result
        })
      }
      return Promise.resolve(mockSeriesResponse)
    })

    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
      expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search in category...')
    await user.clear(searchInput)
    await user.type(searchInput, 'unemployment')

    // Wait for search API call to complete and UI to update
    await waitFor(() => {
      expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
      expect(screen.queryByText('Total Nonfarm Payrolls')).not.toBeInTheDocument()
      expect(screen.getByText(/Showing 1 of 10 series/)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should not fetch when categoryId is not provided', () => {
    render(
      <CategoryDetail
        categoryId=""
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    expect(fetchCategorySeries).not.toHaveBeenCalled()
  })

  it('should have correct aria-labels for accessibility', async () => {
    render(
      <CategoryDetail
        categoryId="employment"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Employment')).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back to Categories/i })
    expect(backButton).toHaveAttribute('aria-label', 'Back to categories')

    const searchInput = screen.getByPlaceholderText('Search in category...')
    expect(searchInput).toHaveAttribute('aria-label', 'Search series in category')
  })

  it('should handle singular series count', async () => {
    fetchCategorySeries.mockResolvedValue({
      category_name: 'Single Series',
      total_count: 1,
      series: [mockSeriesResponse.series[0]],
    })

    render(
      <CategoryDetail
        categoryId="single"
        onBack={mockOnBack}
        onSeriesSelect={mockOnSeriesSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('(1 series)')).toBeInTheDocument()
    })
  })
})

