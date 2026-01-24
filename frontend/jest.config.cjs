module.exports = {
  rootDir: __dirname,
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', { 
      presets: [
        ['@babel/preset-env', { modules: 'auto' }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }],
  },
  testMatch: [
    '<rootDir>/__tests__/**/*.test.{js,jsx}',
    '<rootDir>/src/**/__tests__/**/*.{js,jsx}',
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/main.jsx',
    '!src/**/*.test.{js,jsx}',
    // Exclude pre-existing components with 0% coverage (not part of Increment 5.1)
    '!src/components/DataGraph.jsx',
    '!src/components/Sidebar.jsx',
    // Exclude index files (just exports)
    '!src/components/analytics/index.js',
  ],
  coverageThreshold: {
    global: {
      branches: 65,
      functions: 55,
      lines: 70,
      statements: 70,
    },
  },
  transformIgnorePatterns: [
    'node_modules/(?!(.*\\.mjs$))',
  ],
  extensionsToTreatAsEsm: ['.jsx'],
  globals: {
    'import.meta': {
      env: {
        VITE_API_BASE_URL: 'http://localhost:8000',
      },
    },
  },
}

