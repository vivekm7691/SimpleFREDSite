// Custom Jest transform to handle import.meta
// This runs before Babel and coverage instrumentation to prevent parsing errors
module.exports = {
  process(sourceText, sourcePath) {
    // Replace all import.meta references with safe fallbacks
    // This prevents Jest from trying to parse import.meta which causes errors
    let transformed = sourceText
    
    // Replace import.meta.env.VITE_API_BASE_URL with process.env fallback
    transformed = transformed.replace(
      /import\.meta\.env\.VITE_API_BASE_URL/g,
      "(typeof process !== 'undefined' && process.env && process.env.VITE_API_BASE_URL) || (typeof global !== 'undefined' && global.import && global.import.meta && global.import.meta.env && global.import.meta.env.VITE_API_BASE_URL) || 'http://localhost:8000'"
    )
    
    // Replace any other import.meta.env.* references
    transformed = transformed.replace(
      /import\.meta\.env\.([a-zA-Z_][a-zA-Z0-9_]*)/g,
      "(typeof process !== 'undefined' && process.env && process.env.$1) || (typeof global !== 'undefined' && global.import && global.import.meta && global.import.meta.env && global.import.meta.env.$1) || undefined"
    )
    
    // Replace standalone import.meta references
    transformed = transformed.replace(
      /import\.meta/g,
      "(typeof global !== 'undefined' && global.import && global.import.meta) || {}"
    )
    
    return {
      code: transformed,
    }
  },
}




