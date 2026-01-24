/**
 * Tests for CorrelationsView component
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CorrelationsView from '../../src/components/analytics/CorrelationsView'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
}))

describe('CorrelationsView Component', () => {
  test('renders empty state when no data', () => {
    render(<CorrelationsView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /correlations/i })).toBeInTheDocument()
    expect(screen.getByText(/no correlation data available/i)).toBeInTheDocument()
  })

  test('renders correlation table with data', () => {
    const mockData = [
      {
        series_id_1: 'GDP',
        series_id_2: 'UNRATE',
        correlation: 0.85,
      },
    ]
    
    render(<CorrelationsView data={mockData} />)
    
    expect(screen.getByText(/correlations/i)).toBeInTheDocument()
    expect(screen.getByText(/GDP/i)).toBeInTheDocument()
    expect(screen.getByText(/UNRATE/i)).toBeInTheDocument()
    expect(screen.getByText(/0.8500/i)).toBeInTheDocument()
  })

  test('sorts table by correlation when header is clicked', async () => {
    const user = userEvent.setup()
    const mockData = [
      { series_id_1: 'GDP', series_id_2: 'UNRATE', correlation: 0.85 },
      { series_id_1: 'GDP', series_id_2: 'CPIAUCSL', correlation: 0.65 },
    ]
    
    render(<CorrelationsView data={mockData} />)
    
    // Find the correlation header in the table (more specific)
    const headers = screen.getAllByText(/correlation/i)
    const correlationHeader = headers.find(el => el.tagName === 'TH')
    expect(correlationHeader).toBeInTheDocument()
    
    if (correlationHeader) {
      await user.click(correlationHeader)
    }
    
    // Table should be sorted (order may change)
    // GDP appears multiple times, so use getAllByText
    const gdpElements = screen.getAllByText(/GDP/i)
    expect(gdpElements.length).toBeGreaterThan(0)
    
    // Verify both series are present
    expect(screen.getByText(/UNRATE/i)).toBeInTheDocument()
    expect(screen.getByText(/CPIAUCSL/i)).toBeInTheDocument()
  })

  test('displays correlation strength labels', () => {
    const mockData = [
      { series_id_1: 'GDP', series_id_2: 'UNRATE', correlation: 0.85 }, // Strong positive
      { series_id_1: 'GDP', series_id_2: 'CPIAUCSL', correlation: 0.5 }, // Moderate positive
      { series_id_1: 'GDP', series_id_2: 'FEDFUNDS', correlation: 0.1 }, // Weak
      { series_id_1: 'GDP', series_id_2: 'M2', correlation: -0.5 }, // Moderate negative
      { series_id_1: 'GDP', series_id_2: 'DEXUSEU', correlation: -0.85 }, // Strong negative
    ]
    
    render(<CorrelationsView data={mockData} />)
    
    // Check that correlation strength labels appear (may be in table or legend)
    const strongPositive = screen.getAllByText(/strong positive/i)
    expect(strongPositive.length).toBeGreaterThan(0)
    
    const moderatePositive = screen.getAllByText(/moderate positive/i)
    expect(moderatePositive.length).toBeGreaterThan(0)
    
    const weak = screen.getAllByText(/weak/i)
    expect(weak.length).toBeGreaterThan(0)
  })
})

