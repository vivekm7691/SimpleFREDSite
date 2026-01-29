// Jest setup file for testing library
require('@testing-library/jest-dom')

// Mock import.meta for Vite environment variables
// This is needed because Jest doesn't support import.meta natively
// Set up global import.meta for tests
global.import = global.import || {}
global.import.meta = global.import.meta || {}
global.import.meta.env = global.import.meta.env || {}
global.import.meta.env.VITE_API_BASE_URL =
  global.import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Suppress React act() warnings in tests
// These warnings occur when async state updates happen outside of act()
// Testing Library's userEvent and waitFor already handle this, but React still logs warnings
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    // Suppress act() warnings
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: An update to') ||
        args[0].includes('not wrapped in act(...)') ||
        args[0].includes('inside a test was not wrapped'))
    ) {
      return
    }
    // Suppress console.error from error handling tests
    if (
      args.length > 0 &&
      typeof args[0] === 'string' &&
      (args[0].includes('Error loading categories:') ||
        args[0].includes('Advanced analytics error:') ||
        args[0].includes('Analytics error:'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})


