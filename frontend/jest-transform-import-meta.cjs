// Custom Jest transform to handle import.meta
// This runs before Babel and coverage instrumentation to prevent parsing errors
module.exports = {
  process(sourceText, sourcePath) {
    // Since we've removed import.meta from source code, this transform only handles
    // edge cases that might appear in dependencies or generated code
    let transformed = sourceText
    
    // Only replace standalone import.meta.env.VITE_API_BASE_URL (not in property chains)
    // Match only when import.meta is at the start of an expression or after certain operators
    transformed = transformed.replace(
      /(^|[^a-zA-Z0-9_.])import\.meta\.env\.VITE_API_BASE_URL([^a-zA-Z0-9_.]|$)/g,
      (match, before, after) => {
        return before + "(typeof process !== 'undefined' && process.env && process.env.VITE_API_BASE_URL) || (typeof global !== 'undefined' && global.import && global.import.meta && global.import.meta.env && global.import.meta.env.VITE_API_BASE_URL) || 'http://localhost:8000'" + after
      }
    )
    
    // Only replace standalone import.meta.env.* (not in property chains)
    transformed = transformed.replace(
      /(^|[^a-zA-Z0-9_.])import\.meta\.env\.([a-zA-Z_][a-zA-Z0-9_]*)([^a-zA-Z0-9_.]|$)/g,
      (match, before, varName, after) => {
        return before + "(typeof process !== 'undefined' && process.env && process.env." + varName + ") || (typeof global !== 'undefined' && global.import && global.import.meta && global.import.meta.env && global.import.meta.env." + varName + ") || undefined" + after
      }
    )
    
    // Only replace standalone import.meta (not in property chains like global.import.meta)
    // Match only when it's not preceded by a word character or dot
    transformed = transformed.replace(
      /(^|[^a-zA-Z0-9_.])import\.meta([^a-zA-Z0-9_.]|$)/g,
      (match, before, after) => {
        return before + "((typeof global !== 'undefined' && global.import && global.import.meta) || {})" + after
      }
    )
    
    return {
      code: transformed,
    }
  },
}

