/**
 * Tests for API client functions
 */
import {
  fetchFREDData,
  summarizeData,
  fetchCategories,
  fetchCategorySeries,
  searchCategorySeries,
} from '../src/services/api'

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

  describe('fetchCategories', () => {
    it('should fetch categories successfully', async () => {
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

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategories,
      })

      const result = await fetchCategories()

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/categories', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      expect(result).toEqual(mockCategories)
      expect(result.categories).toHaveLength(2)
      expect(result.categories[0].id).toBe('employment')
    })

    it('should handle API errors with error message', async () => {
      const errorResponse = {
        detail: 'Failed to fetch categories',
      }

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => errorResponse,
      })

      await expect(fetchCategories()).rejects.toThrow('Failed to fetch categories')
    })

    it('should handle HTTP errors without JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(fetchCategories()).rejects.toThrow('HTTP error! status: 500')
    })

    it('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetchCategories()).rejects.toThrow('Network error')
    })
  })

  describe('fetchCategorySeries', () => {
    it('should fetch category series successfully', async () => {
      const mockSeries = {
        category_id: 'employment',
        category_name: 'Employment',
        series: [
          {
            id: 'UNRATE',
            title: 'Unemployment Rate',
            frequency: 'Monthly',
            units: 'Percent',
            seasonal_adjustment: 'Seasonally Adjusted',
          },
          {
            id: 'PAYEMS',
            title: 'Nonfarm Payroll Employment',
            frequency: 'Monthly',
            units: 'Thousands of Persons',
            seasonal_adjustment: 'Seasonally Adjusted',
          },
        ],
        total_count: 2,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSeries,
      })

      const result = await fetchCategorySeries('employment')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/categories/employment',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      expect(result).toEqual(mockSeries)
      expect(result.series).toHaveLength(2)
      expect(result.category_id).toBe('employment')
    })

    it('should fetch category series with search term', async () => {
      const mockSeries = {
        category_id: 'employment',
        category_name: 'Employment',
        series: [
          {
            id: 'UNRATE',
            title: 'Unemployment Rate',
            frequency: 'Monthly',
            units: 'Percent',
            seasonal_adjustment: 'Seasonally Adjusted',
          },
        ],
        total_count: 1,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSeries,
      })

      const result = await fetchCategorySeries('employment', 'UN')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/categories/employment?q=UN',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      expect(result).toEqual(mockSeries)
      expect(result.series).toHaveLength(1)
    })

    it('should URL encode category ID correctly', async () => {
      const mockSeries = {
        category_id: 'interest_rates',
        category_name: 'Interest Rates',
        series: [],
        total_count: 0,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSeries,
      })

      await fetchCategorySeries('interest_rates')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/categories/interest_rates',
        expect.any(Object)
      )
    })

    it('should handle API errors with error message', async () => {
      const errorResponse = {
        detail: "Category 'invalid' not found",
      }

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => errorResponse,
      })

      await expect(fetchCategorySeries('invalid')).rejects.toThrow(
        "Category 'invalid' not found"
      )
    })

    it('should handle HTTP errors without JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(fetchCategorySeries('employment')).rejects.toThrow(
        'HTTP error! status: 500'
      )
    })

    it('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetchCategorySeries('employment')).rejects.toThrow('Network error')
    })
  })

  describe('searchCategorySeries', () => {
    it('should search category series successfully', async () => {
      const mockSeries = {
        category_id: 'employment',
        category_name: 'Employment',
        series: [
          {
            id: 'UNRATE',
            title: 'Unemployment Rate',
            frequency: 'Monthly',
            units: 'Percent',
            seasonal_adjustment: 'Seasonally Adjusted',
          },
        ],
        total_count: 1,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSeries,
      })

      const result = await searchCategorySeries('employment', 'UN')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/categories/employment?q=UN',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      expect(result).toEqual(mockSeries)
      expect(result.series).toHaveLength(1)
    })

    it('should handle empty search term', async () => {
      const mockSeries = {
        category_id: 'employment',
        category_name: 'Employment',
        series: [],
        total_count: 0,
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSeries,
      })

      const result = await searchCategorySeries('employment', '')

      // Empty search should still make request (backend handles empty search)
      expect(fetch).toHaveBeenCalled()
      expect(result).toEqual(mockSeries)
    })

    it('should handle API errors', async () => {
      const errorResponse = {
        detail: 'Search failed',
      }

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => errorResponse,
      })

      await expect(searchCategorySeries('employment', 'test')).rejects.toThrow(
        'Search failed'
      )
    })

    it('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(searchCategorySeries('employment', 'test')).rejects.toThrow(
        'Network error'
      )
    })
  })
})




