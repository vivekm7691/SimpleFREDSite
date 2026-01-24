/**
 * Tests for StatisticsView component
 */
import { render, screen } from '@testing-library/react'
import StatisticsView from '../../src/components/analytics/StatisticsView'

describe('StatisticsView Component', () => {
  test('renders empty state when no data', () => {
    render(<StatisticsView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /statistics/i })).toBeInTheDocument()
    expect(screen.getByText(/no statistics data available/i)).toBeInTheDocument()
  })

  test('renders statistics for single series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        mean: 100.5,
        median: 100.0,
        std: 10.25,
        min: 90.0,
        max: 110.0,
        count: 20,
        sum: 2010.0,
      },
    ]
    
    render(<StatisticsView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /statistics/i })).toBeInTheDocument()
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/100.50/i)).toBeInTheDocument() // Mean
    expect(screen.getByText(/20/i)).toBeInTheDocument() // Count
  })

  test('renders statistics for multiple series', () => {
    const mockData = [
      {
        series_id: 'GDP',
        mean: 100.5,
        median: 100.0,
        std: 10.25,
        min: 90.0,
        max: 110.0,
        count: 20,
        sum: 2010.0,
      },
      {
        series_id: 'UNRATE',
        mean: 5.5,
        median: 5.0,
        std: 1.25,
        min: 4.0,
        max: 7.0,
        count: 20,
        sum: 110.0,
      },
    ]
    
    render(<StatisticsView data={mockData} />)
    
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/UNRATE/i)).toBeInTheDocument()
  })

  test('handles null values gracefully', () => {
    const mockData = [
      {
        series_id: 'GDP',
        mean: null,
        median: null,
        std: null,
        min: 90.0,
        max: 110.0,
        count: 20,
        sum: null,
      },
    ]
    
    render(<StatisticsView data={mockData} />)
    
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    // Check that N/A appears (there may be multiple, so use getAllByText)
    const naElements = screen.getAllByText(/N\/A/i)
    expect(naElements.length).toBeGreaterThan(0)
  })
})

