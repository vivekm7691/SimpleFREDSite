/**
 * Tests for CategoryCard component
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CategoryCard from '../src/components/CategoryCard'

describe('CategoryCard Component', () => {
  const mockCategory = {
    id: 'employment',
    name: 'Employment',
    icon: '📊',
    description: 'Labor market indicators',
    series_count: 12,
  }

  const mockOnClick = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render category information correctly', () => {
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    expect(screen.getByText('Employment')).toBeInTheDocument()
    expect(screen.getByText('12 series')).toBeInTheDocument()
    expect(screen.getByText('📊')).toBeInTheDocument()
  })

  it('should display singular form for series count of 1', () => {
    const singleSeriesCategory = {
      ...mockCategory,
      series_count: 1,
    }

    render(<CategoryCard category={singleSeriesCategory} onClick={mockOnClick} />)

    expect(screen.getByText('1 series')).toBeInTheDocument()
  })

  it('should call onClick when card is clicked', async () => {
    const user = userEvent.setup()
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    const card = screen.getByRole('button')
    await user.click(card)

    expect(mockOnClick).toHaveBeenCalledTimes(1)
    expect(mockOnClick).toHaveBeenCalledWith('employment')
  })

  it('should call onClick when Enter key is pressed', async () => {
    const user = userEvent.setup()
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    const card = screen.getByRole('button')
    card.focus()
    await user.keyboard('{Enter}')

    expect(mockOnClick).toHaveBeenCalledTimes(1)
    expect(mockOnClick).toHaveBeenCalledWith('employment')
  })

  it('should call onClick when Space key is pressed', async () => {
    const user = userEvent.setup()
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    const card = screen.getByRole('button')
    card.focus()
    await user.keyboard(' ')

    expect(mockOnClick).toHaveBeenCalledTimes(1)
    expect(mockOnClick).toHaveBeenCalledWith('employment')
  })

  it('should have correct aria-label for accessibility', () => {
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    const card = screen.getByRole('button')
    expect(card).toHaveAttribute(
      'aria-label',
      'Category: Employment, 12 series available'
    )
  })

  it('should have role="button" and tabIndex for keyboard navigation', () => {
    render(<CategoryCard category={mockCategory} onClick={mockOnClick} />)

    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('tabIndex', '0')
  })

  it('should not call onClick if onClick prop is not provided', async () => {
    const user = userEvent.setup()
    render(<CategoryCard category={mockCategory} />)

    const card = screen.getByRole('button')
    await user.click(card)

    // Should not throw error, just not call anything
    expect(mockOnClick).not.toHaveBeenCalled()
  })

  it('should render with different category data', () => {
    const differentCategory = {
      id: 'inflation',
      name: 'Inflation',
      icon: '📈',
      description: 'Price level indicators',
      series_count: 10,
    }

    render(<CategoryCard category={differentCategory} onClick={mockOnClick} />)

    expect(screen.getByText('Inflation')).toBeInTheDocument()
    expect(screen.getByText('10 series')).toBeInTheDocument()
    expect(screen.getByText('📈')).toBeInTheDocument()
  })
})

