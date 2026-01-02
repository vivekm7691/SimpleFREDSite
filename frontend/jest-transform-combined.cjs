// Combined Jest transform that handles import.meta first, then passes to Babel
const importMetaTransform = require('./jest-transform-import-meta.cjs')

// Get babel-jest transformer
let babelJest
try {
  babelJest = require('babel-jest')
  // Handle both default export and named export
  if (babelJest.default) {
    babelJest = babelJest.default
  }
} catch (e) {
  throw new Error('babel-jest is required. Please install it: npm install --save-dev babel-jest')
}

module.exports = {
  process(sourceText, sourcePath, options) {
    // First, transform import.meta to prevent parsing errors
    const importMetaResult = importMetaTransform.process(sourceText, sourcePath, options)
    
    // Then, pass to Babel for normal transformation
    const babelTransformer = babelJest.createTransformer({
      presets: [
        ['@babel/preset-env', { modules: 'auto' }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    })
    
    return babelTransformer.process(importMetaResult.code, sourcePath, options)
  },
}

