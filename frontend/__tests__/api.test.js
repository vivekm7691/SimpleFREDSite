/**
 * Tests for API client functions
 */
import { fetchFREDData, summarizeData } from '../src/services/api'

// Mock fetch globally
global.fetch = jest.fn()

describe('API Client', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  describe('fetchFREDData', () => {
    it('should fetch FRED data successfully', async () => {
      const mockData = {
        series_id: 'GDP',
        series_info: {
          id: 'GDP',
          title: 'Gross Domestic Product',
          units: 'Billions of Dollars',
          frequency: 'Quarterly',
        },
        observations: [
          { date: '2024-01-01', value: 25000.0 },
          { date: '2023-10-01', value: 24800.0 },
        ],
        observation_count: 2,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await fetchFREDData('GDP')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/fred/fetch',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ series_id: 'GDP' }),
        }
      )
      expect(result).toEqual(mockData)
    })

    it('should handle API errors with error message', async () => {
      const errorResponse = {
        detail: 'Series not found',
      }

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => errorResponse,
      })

      await expect(fetchFREDData('INVALID')).rejects.toThrow('Series not found')
    })

    it('should handle HTTP errors without JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(fetchFREDData('GDP')).rejects.toThrow('HTTP error! status: 500')
    })

    it('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetchFREDData('GDP')).rejects.toThrow('Network error')
    })
  })

  describe('summarizeData', () => {
    it('should summarize data successfully with summary object', async () => {
      const mockSummary = {
        summary: 'This is a test summary of economic data.',
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      })

      const data = { series_info: { title: 'GDP' }, observations: [] }
      const result = await summarizeData(data)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/summarize',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ data }),
        }
      )
      expect(result).toBe('This is a test summary of economic data.')
    })

    it('should handle string response directly', async () => {
      const mockSummary = 'Direct string summary'

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      })

      const data = { test: 'data' }
      const result = await summarizeData(data)

      expect(result).toBe('Direct string summary')
    })

    it('should handle object response without summary key', async () => {
      const mockResponse = { otherKey: 'value' }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const data = { test: 'data' }
      const result = await summarizeData(data)

      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors', async () => {
      const errorResponse = {
        detail: 'Failed to generate summary',
      }

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => errorResponse,
      })

      await expect(summarizeData({})).rejects.toThrow('Failed to generate summary')
    })

    it('should handle HTTP errors without JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(summarizeData({})).rejects.toThrow('HTTP error! status: 500')
    })

    it('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(summarizeData({})).rejects.toThrow('Network error')
    })
  })
})

