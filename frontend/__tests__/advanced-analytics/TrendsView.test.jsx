/**
 * Tests for TrendsView component
 */
import { render, screen } from '@testing-library/react'
import TrendsView from '../../src/components/advanced-analytics/TrendsView'

describe('TrendsView Component', () => {
  test('renders empty state when no data', () => {
    render(<TrendsView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /trends/i })).toBeInTheDocument()
    expect(screen.getByText(/no trend data available/i)).toBeInTheDocument()
  })

  test('renders trend card with linear trend data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'linear',
        slope: 0.5,
        intercept: 100.0,
        r_squared: 0.95,
        direction: 'increasing',
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /trend analysis/i })).toBeInTheDocument()
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText(/increasing/i)).toBeInTheDocument()
    expect(screen.getByText(/linear/i)).toBeInTheDocument()
  })

  test('renders trend card with polynomial trend data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'polynomial',
        slope: null,
        intercept: null,
        r_squared: 0.92,
        direction: 'increasing',
        polynomial_degree: 2,
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText(/polynomial/i)).toBeInTheDocument()
    expect(screen.getByText(/2/i)).toBeInTheDocument() // Polynomial degree
  })

  test('displays trend direction with correct color', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'linear',
        slope: -0.5,
        intercept: 100.0,
        r_squared: 0.85,
        direction: 'decreasing',
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByText(/decreasing/i)).toBeInTheDocument()
  })

  test('displays R² value and strength bar', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'linear',
        slope: 0.5,
        intercept: 100.0,
        r_squared: 0.95,
        direction: 'increasing',
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByText(/r²/i)).toBeInTheDocument()
  })

  test('handles null slope and intercept', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'polynomial',
        slope: null,
        intercept: null,
        r_squared: 0.90,
        direction: 'stable',
        polynomial_degree: 3,
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText(/polynomial/i)).toBeInTheDocument()
  })

  test('displays multiple trend cards', () => {
    const mockData = [
      {
        series_id: 'GDP',
        trend_type: 'linear',
        slope: 0.5,
        intercept: 100.0,
        r_squared: 0.95,
        direction: 'increasing',
      },
      {
        series_id: 'UNRATE',
        trend_type: 'linear',
        slope: -0.1,
        intercept: 5.0,
        r_squared: 0.88,
        direction: 'decreasing',
      },
    ]
    
    render(<TrendsView data={mockData} />)
    
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText('UNRATE')).toBeInTheDocument()
  })
})

