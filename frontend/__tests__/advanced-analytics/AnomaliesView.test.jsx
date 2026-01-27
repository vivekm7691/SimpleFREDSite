/**
 * Tests for AnomaliesView component
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AnomaliesView from '../../src/components/advanced-analytics/AnomaliesView'

describe('AnomaliesView Component', () => {
  test('renders empty state when no data', () => {
    render(<AnomaliesView data={[]} />)
    
    expect(screen.getByRole('heading', { name: /anomaly detection/i })).toBeInTheDocument()
    expect(screen.getByText(/no anomalies detected/i)).toBeInTheDocument()
  })

  test('renders table with anomaly data', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: 100.0,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    expect(screen.getByRole('heading', { name: /anomaly detection/i })).toBeInTheDocument()
    expect(screen.getByText('GDP')).toBeInTheDocument()
    expect(screen.getByText('2024-01-01')).toBeInTheDocument()
    expect(screen.getAllByText(/high/i).length).toBeGreaterThan(0)
  })

  test('filters by severity', async () => {
    const user = userEvent.setup()
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: 100.0,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        expected_value: 100.0,
        deviation: 2.0,
        detection_method: 'z_score',
        severity: 'low',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    const severitySelect = screen.getByLabelText(/filter by severity/i)
    await user.selectOptions(severitySelect, 'high')
    
    await waitFor(() => {
      expect(screen.getByText('GDP')).toBeInTheDocument()
      expect(screen.queryByText('2024-02-01')).not.toBeInTheDocument()
    })
  })

  test('filters by detection method', async () => {
    const user = userEvent.setup()
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: 100.0,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        expected_value: 100.0,
        deviation: 2.0,
        detection_method: 'iqr',
        severity: 'medium',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    const methodSelect = screen.getByLabelText(/filter by method/i)
    await user.selectOptions(methodSelect, 'z_score')
    
    await waitFor(() => {
      expect(screen.getByText('GDP')).toBeInTheDocument()
    })
  })

  test('displays severity badges', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: 100.0,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        expected_value: 100.0,
        deviation: 2.0,
        detection_method: 'z_score',
        severity: 'medium',
      },
      {
        series_id: 'GDP',
        date: '2024-03-01',
        value: 102.0,
        expected_value: 100.0,
        deviation: 1.0,
        detection_method: 'z_score',
        severity: 'low',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    expect(screen.getAllByText(/high/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/medium/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/low/i).length).toBeGreaterThan(0)
  })

  test('displays anomaly count', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: 100.0,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
      {
        series_id: 'GDP',
        date: '2024-02-01',
        value: 105.0,
        expected_value: 100.0,
        deviation: 2.0,
        detection_method: 'z_score',
        severity: 'low',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    expect(screen.getByText(/showing 2 of 2 anomalies/i)).toBeInTheDocument()
  })

  test('handles null expected value', () => {
    const mockData = [
      {
        series_id: 'GDP',
        date: '2024-01-01',
        value: 150.0,
        expected_value: null,
        deviation: 5.0,
        detection_method: 'z_score',
        severity: 'high',
      },
    ]
    
    render(<AnomaliesView data={mockData} />)
    
    expect(screen.getByText('GDP')).toBeInTheDocument()
  })
})

