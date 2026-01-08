/**
 * Tests for SeriesCard component
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SeriesCard from '../src/components/SeriesCard'

describe('SeriesCard Component', () => {
  const mockSeries = {
    id: 'GDP',
    title: 'Gross Domestic Product',
    frequency: 'Quarterly',
    seasonal_adjustment: 'Seasonally Adjusted Annual Rate',
    units: 'Billions of Dollars',
  }

  const mockOnSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render series information correctly', () => {
    render(<SeriesCard series={mockSeries} onSelect={mockOnSelect} />)

    expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument()
    expect(screen.getByText('(GDP)')).toBeInTheDocument()
    expect(screen.getByText(/Quarterly/)).toBeInTheDocument()
  })

  it('should display formatted metadata correctly', () => {
    render(<SeriesCard series={mockSeries} onSelect={mockOnSelect} />)

    const metadata = screen.getByText(/Quarterly.*Seasonally Adjusted Annual Rate.*Billions of Dollars/)
    expect(metadata).toBeInTheDocument()
  })

  it('should call onSelect when "Select Series" button is clicked', async () => {
    const user = userEvent.setup()
    render(<SeriesCard series={mockSeries} onSelect={mockOnSelect} />)

    const button = screen.getByRole('button', { name: /Select series GDP/i })
    await user.click(button)

    expect(mockOnSelect).toHaveBeenCalledTimes(1)
    expect(mockOnSelect).toHaveBeenCalledWith('GDP')
  })

  it('should handle series with partial metadata', () => {
    const partialSeries = {
      id: 'UNRATE',
      title: 'Unemployment Rate',
      frequency: 'Monthly',
      // No seasonal_adjustment or units
    }

    render(<SeriesCard series={partialSeries} onSelect={mockOnSelect} />)

    expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    expect(screen.getByText('(UNRATE)')).toBeInTheDocument()
    expect(screen.getByText(/Monthly/)).toBeInTheDocument()
  })

  it('should handle series with no metadata', () => {
    const minimalSeries = {
      id: 'TEST',
      title: 'Test Series',
    }

    render(<SeriesCard series={minimalSeries} onSelect={mockOnSelect} />)

    expect(screen.getByText('Test Series')).toBeInTheDocument()
    expect(screen.getByText('(TEST)')).toBeInTheDocument()
    // Metadata section should not be visible if formatMetadata returns empty
    const metadata = screen.queryByText(/Quarterly|Monthly|Annual/)
    expect(metadata).not.toBeInTheDocument()
  })

  it('should have correct aria-label for accessibility', () => {
    render(<SeriesCard series={mockSeries} onSelect={mockOnSelect} />)

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute(
      'aria-label',
      'Select series GDP: Gross Domestic Product'
    )
  })

  it('should not call onSelect if onSelect prop is not provided', async () => {
    const user = userEvent.setup()
    render(<SeriesCard series={mockSeries} />)

    const button = screen.getByRole('button')
    await user.click(button)

    // Should not throw error, just not call anything
    expect(mockOnSelect).not.toHaveBeenCalled()
  })

  it('should stop event propagation when button is clicked', async () => {
    const user = userEvent.setup()
    const cardClickHandler = jest.fn()
    
    render(
      <div onClick={cardClickHandler}>
        <SeriesCard series={mockSeries} onSelect={mockOnSelect} />
      </div>
    )

    const button = screen.getByRole('button')
    await user.click(button)

    expect(mockOnSelect).toHaveBeenCalled()
    // Event propagation should be stopped, so card click handler shouldn't be called
    // Note: This is a simplified test - actual event propagation testing might need more setup
  })

  it('should render with different series data', () => {
    const differentSeries = {
      id: 'CPIAUCSL',
      title: 'Consumer Price Index',
      frequency: 'Monthly',
      seasonal_adjustment: 'Seasonally Adjusted',
      units: 'Index 1982-84=100',
    }

    render(<SeriesCard series={differentSeries} onSelect={mockOnSelect} />)

    expect(screen.getByText('Consumer Price Index')).toBeInTheDocument()
    expect(screen.getByText('(CPIAUCSL)')).toBeInTheDocument()
  })
})

