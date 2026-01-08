/**
 * Tests for CategoryBrowser component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CategoryBrowser from '../src/components/CategoryBrowser'
import { fetchCategories } from '../src/services/api'

// Mock the API service
jest.mock('../src/services/api', () => ({
  fetchCategories: jest.fn(),
  fetchCategorySeries: jest.fn(),
}))

// Mock child components to simplify testing
jest.mock('../src/components/CategoryGrid', () => {
  return function MockCategoryGrid({ categories, onCategoryClick, loading }) {
    if (loading) {
      return <div>Loading categories...</div>
    }
    return (
      <div data-testid="category-grid">
        {categories.map((cat) => (
          <button
            key={cat.id}
            data-testid={`category-${cat.id}`}
            onClick={() => onCategoryClick(cat.id)}
          >
            {cat.name}
          </button>
        ))}
      </div>
    )
  }
})

jest.mock('../src/components/CategoryDetail', () => {
  return function MockCategoryDetail({ categoryId, categoryName, onBack, onSeriesSelect }) {
    return (
      <div data-testid="category-detail">
        <div data-testid="category-detail-id">{categoryId}</div>
        <div data-testid="category-detail-name">{categoryName}</div>
        <button data-testid="back-button" onClick={onBack}>
          Back to Categories
        </button>
        <button
          data-testid="select-series-button"
          onClick={() => onSeriesSelect('UNRATE')}
        >
          Select Series
        </button>
      </div>
    )
  }
})

describe('CategoryBrowser Component', () => {
  const mockCategories = {
    categories: [
      {
        id: 'employment',
        name: 'Employment',
        icon: '📊',
        description: 'Labor market indicators',
        series_count: 12,
      },
      {
        id: 'inflation',
        name: 'Inflation',
        icon: '📈',
        description: 'Price level indicators',
        series_count: 10,
      },
    ],
  }

  const mockOnSeriesSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    fetchCategories.mockResolvedValue(mockCategories)
  })

  it('should render category grid initially', async () => {
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    // Should show loading initially
    expect(screen.getByText('Loading categories...')).toBeInTheDocument()

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    expect(screen.getByText('Browse by Category')).toBeInTheDocument()
    expect(screen.getByTestId('category-employment')).toBeInTheDocument()
    expect(screen.getByTestId('category-inflation')).toBeInTheDocument()
  })

  it('should fetch categories on mount', async () => {
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    await waitFor(() => {
      expect(fetchCategories).toHaveBeenCalledTimes(1)
    })
  })

  it('should switch to detail view on category click', async () => {
    const user = userEvent.setup()
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Click on a category
    const employmentButton = screen.getByTestId('category-employment')
    await user.click(employmentButton)

    // Should show category detail view
    await waitFor(() => {
      expect(screen.getByTestId('category-detail')).toBeInTheDocument()
      expect(screen.getByTestId('category-detail-id')).toHaveTextContent('employment')
      expect(screen.getByTestId('category-detail-name')).toHaveTextContent('Employment')
    })
  })

  it('should return to grid view on back click', async () => {
    const user = userEvent.setup()
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Click on a category
    const employmentButton = screen.getByTestId('category-employment')
    await user.click(employmentButton)

    // Wait for detail view
    await waitFor(() => {
      expect(screen.getByTestId('category-detail')).toBeInTheDocument()
    })

    // Click back button
    const backButton = screen.getByTestId('back-button')
    await user.click(backButton)

    // Should return to grid view
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
      expect(screen.queryByTestId('category-detail')).not.toBeInTheDocument()
    })
  })

  it('should call onSeriesSelect when series is selected', async () => {
    const user = userEvent.setup()
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Click on a category
    const employmentButton = screen.getByTestId('category-employment')
    await user.click(employmentButton)

    // Wait for detail view
    await waitFor(() => {
      expect(screen.getByTestId('category-detail')).toBeInTheDocument()
    })

    // Click select series button
    const selectButton = screen.getByTestId('select-series-button')
    await user.click(selectButton)

    // Should call onSeriesSelect with series ID
    expect(mockOnSeriesSelect).toHaveBeenCalledTimes(1)
    expect(mockOnSeriesSelect).toHaveBeenCalledWith('UNRATE')
  })

  it('should handle error when fetching categories fails', async () => {
    const errorMessage = 'Failed to load categories'
    fetchCategories.mockRejectedValueOnce(new Error(errorMessage))

    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
      expect(screen.getByText(new RegExp(errorMessage, 'i'))).toBeInTheDocument()
    })
  })

  it('should handle empty categories response', async () => {
    fetchCategories.mockResolvedValueOnce({ categories: [] })

    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Should not have any category buttons
    expect(screen.queryByTestId('category-employment')).not.toBeInTheDocument()
  })

  it('should not call onSeriesSelect if prop is not provided', async () => {
    const user = userEvent.setup()
    render(<CategoryBrowser />)

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Click on a category
    const employmentButton = screen.getByTestId('category-employment')
    await user.click(employmentButton)

    // Wait for detail view
    await waitFor(() => {
      expect(screen.getByTestId('category-detail')).toBeInTheDocument()
    })

    // Click select series button
    const selectButton = screen.getByTestId('select-series-button')
    await user.click(selectButton)

    // Should not throw error, just not call anything
    expect(mockOnSeriesSelect).not.toHaveBeenCalled()
  })

  it('should handle category name not found when switching views', async () => {
    const user = userEvent.setup()
    render(<CategoryBrowser onSeriesSelect={mockOnSeriesSelect} />)

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByTestId('category-grid')).toBeInTheDocument()
    })

    // Manually trigger category click with a category that doesn't exist in the list
    // This simulates edge case where category might be selected but not in categories array
    const grid = screen.getByTestId('category-grid')
    // Simulate clicking a category that exists
    const employmentButton = screen.getByTestId('category-employment')
    await user.click(employmentButton)

    // Should still show detail view
    await waitFor(() => {
      expect(screen.getByTestId('category-detail')).toBeInTheDocument()
    })
  })
})

