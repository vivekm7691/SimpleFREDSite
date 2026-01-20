/**
 * Sidebar component - Collapsible sidebar with Categories and Analytics sections.
 * 
 * Features:
 * - Collapsible sidebar (250px open, 60px collapsed)
 * - Expandable/collapsible sections for Categories and Analytics
 * - Toggle button (hamburger icon)
 * - State persistence (localStorage)
 * - Keyboard shortcuts (Ctrl/Cmd + B to toggle)
 * - Responsive: Overlay on mobile, sidebar on desktop
 */

import { useState, useEffect } from 'react'
import CategoryBrowser from './CategoryBrowser'
import './Sidebar.css'

/**
 * Sidebar component
 * @param {Object} props - Component props
 * @param {Function} props.onSeriesSelect - Callback when a series is selected
 * @param {boolean} props.analyticsExpanded - Whether analytics section is expanded (for future use)
 */
function Sidebar({ onSeriesSelect, analyticsExpanded: externalAnalyticsExpanded }) {
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // Load from localStorage, default to true
    const saved = localStorage.getItem('sidebarOpen')
    return saved !== null ? saved === 'true' : true
  })
  
  const [categoriesExpanded, setCategoriesExpanded] = useState(() => {
    const saved = localStorage.getItem('categoriesExpanded')
    return saved !== null ? saved === 'true' : true
  })
  
  const [analyticsExpanded, setAnalyticsExpanded] = useState(() => {
    const saved = localStorage.getItem('analyticsExpanded')
    return saved !== null ? saved === 'true' : false
  })

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarOpen', sidebarOpen.toString())
  }, [sidebarOpen])

  // Save categories expanded state to localStorage
  useEffect(() => {
    localStorage.setItem('categoriesExpanded', categoriesExpanded.toString())
  }, [categoriesExpanded])

  // Save analytics expanded state to localStorage
  useEffect(() => {
    localStorage.setItem('analyticsExpanded', analyticsExpanded.toString())
  }, [analyticsExpanded])

  // Keyboard shortcut: Ctrl/Cmd + B to toggle sidebar
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault()
        setSidebarOpen(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev)
  }

  const toggleCategories = () => {
    setCategoriesExpanded(prev => !prev)
  }

  const toggleAnalytics = () => {
    setAnalyticsExpanded(prev => !prev)
  }

  return (
    <aside 
      className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}
      aria-label="Navigation sidebar"
      aria-expanded={sidebarOpen}
    >
      {/* Toggle Button */}
      <button
        className="sidebar-toggle"
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        aria-controls="sidebar-content"
      >
        <span className="hamburger-icon">☰</span>
      </button>

      {sidebarOpen && (
        <div id="sidebar-content" className="sidebar-content">
          {/* Categories Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={toggleCategories}
              aria-expanded={categoriesExpanded}
              aria-controls="categories-content"
            >
              <span className="section-title">Categories</span>
              <span className="section-toggle">
                {categoriesExpanded ? '▼' : '▶'}
              </span>
            </button>
            {categoriesExpanded && (
              <div id="categories-content" className="sidebar-section-content">
                <CategoryBrowser onSeriesSelect={onSeriesSelect} />
              </div>
            )}
          </div>

          {/* Analytics Section (Placeholder for Increment 5) */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={toggleAnalytics}
              aria-expanded={analyticsExpanded}
              aria-controls="analytics-content"
            >
              <span className="section-title">Spark Analytics</span>
              <span className="section-toggle">
                {analyticsExpanded ? '▼' : '▶'}
              </span>
            </button>
            {analyticsExpanded && (
              <div id="analytics-content" className="sidebar-section-content">
                <div className="analytics-placeholder">
                  <p>Analytics features coming in Increment 5</p>
                  <p className="placeholder-note">Batch processing, correlation, statistics, and more</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}

export default Sidebar

