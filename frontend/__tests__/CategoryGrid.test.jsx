/**
 * Tests for CategoryGrid component
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CategoryGrid from '../src/components/CategoryGrid'

// Mock CategoryCard component
jest.mock('../src/components/CategoryCard', () => {
  return function MockCategoryCard({ category, onClick }) {
    return (
      <div data-testid={`category-card-${category.id}`}>
        <button onClick={() => onClick(category.id)}>
          {category.name}
        </button>
      </div>
    )
  }
})

describe('CategoryGrid Component', () => {
  const mockCategories = [
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
    {
      id: 'gdp',
      name: 'GDP',
      icon: '💰',
      description: 'Economic output',
      series_count: 5,
    },
  ]

  const mockOnCategoryClick = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render loading state when loading is true', () => {
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
        loading={true}
      />
    )

    expect(screen.getByText('Loading categories...')).toBeInTheDocument()
    expect(screen.queryByTestId('category-card-employment')).not.toBeInTheDocument()
  })

  it('should render empty state when categories array is empty', () => {
    render(
      <CategoryGrid
        categories={[]}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.getByText('No categories available')).toBeInTheDocument()
  })

  it('should render empty state when categories is null', () => {
    render(
      <CategoryGrid
        categories={null}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.getByText('No categories available')).toBeInTheDocument()
  })

  it('should render empty state when categories is undefined', () => {
    render(
      <CategoryGrid
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.getByText('No categories available')).toBeInTheDocument()
  })

  it('should render all category cards when categories are provided', () => {
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.getByTestId('category-card-employment')).toBeInTheDocument()
    expect(screen.getByTestId('category-card-inflation')).toBeInTheDocument()
    expect(screen.getByTestId('category-card-gdp')).toBeInTheDocument()
  })

  it('should call onCategoryClick when a category card is clicked', async () => {
    const user = userEvent.setup()
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    const employmentButton = screen.getByText('Employment')
    await user.click(employmentButton)

    expect(mockOnCategoryClick).toHaveBeenCalledTimes(1)
    expect(mockOnCategoryClick).toHaveBeenCalledWith('employment')
  })

  it('should call onCategoryClick for different categories', async () => {
    const user = userEvent.setup()
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    const inflationButton = screen.getByText('Inflation')
    await user.click(inflationButton)

    expect(mockOnCategoryClick).toHaveBeenCalledWith('inflation')
  })

  it('should not call onCategoryClick if prop is not provided', async () => {
    const user = userEvent.setup()
    render(
      <CategoryGrid
        categories={mockCategories}
        loading={false}
      />
    )

    const employmentButton = screen.getByText('Employment')
    await user.click(employmentButton)

    // Should not throw error, just not call anything
    expect(mockOnCategoryClick).not.toHaveBeenCalled()
  })

  it('should not show loading state when loading is false', () => {
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.queryByText('Loading categories...')).not.toBeInTheDocument()
    expect(screen.getByTestId('category-card-employment')).toBeInTheDocument()
  })

  it('should handle single category', () => {
    const singleCategory = [mockCategories[0]]

    render(
      <CategoryGrid
        categories={singleCategory}
        onCategoryClick={mockOnCategoryClick}
        loading={false}
      />
    )

    expect(screen.getByTestId('category-card-employment')).toBeInTheDocument()
    expect(screen.queryByTestId('category-card-inflation')).not.toBeInTheDocument()
  })

  it('should default loading to false when not provided', () => {
    render(
      <CategoryGrid
        categories={mockCategories}
        onCategoryClick={mockOnCategoryClick}
      />
    )

    expect(screen.queryByText('Loading categories...')).not.toBeInTheDocument()
    expect(screen.getByTestId('category-card-employment')).toBeInTheDocument()
  })
})

