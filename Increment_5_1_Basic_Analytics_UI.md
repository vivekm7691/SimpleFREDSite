# Increment 5.1: Basic Analytics UI

## Overview
Add comprehensive UI components to visualize and interact with the analytics capabilities implemented in Increment 5. This includes forms for selecting analytics types and parameters, visualizations for each analytics type, and integration with the `/api/spark/analytics` endpoint.

## Current State

### Existing Infrastructure
- ✅ Sidebar component with "Spark Analytics" section (placeholder)
- ✅ Tab navigation with "Analytics" tab (disabled placeholder)
- ✅ Chart.js installed and configured
- ✅ DataGraph component for time series visualization
- ✅ Backend API endpoint `/api/spark/analytics` fully implemented

### Missing Components
- ❌ Analytics form/controls UI
- ❌ Analytics visualizations
- ❌ API integration for analytics endpoint
- ❌ State management for analytics data

---

## Implementation Plan

### Phase 1: API Integration

#### 1.1 Update API Service
**File:** `frontend/src/services/api.js`

Add function to call analytics endpoint:

```javascript
/**
 * Fetch analytics for one or more FRED series
 * @param {Object} analyticsRequest - Analytics request parameters
 * @param {string[]} analyticsRequest.series_ids - Array of series IDs
 * @param {string[]} analyticsRequest.analytics_types - Array of analytics types
 * @param {number} analyticsRequest.limit - Maximum observations per series
 * @param {string} analyticsRequest.sort_order - Sort order ('asc' or 'desc')
 * @param {boolean} analyticsRequest.use_cache - Whether to use cached data
 * @param {number} [analyticsRequest.moving_average_window] - Window size for moving averages
 * @param {string} [analyticsRequest.moving_average_type] - 'sma' or 'ema'
 * @param {string} [analyticsRequest.time_aggregation_period] - 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
 * @param {string} [analyticsRequest.time_aggregation_function] - 'mean', 'sum', 'min', 'max', 'first', 'last'
 * @returns {Promise<Object>} Analytics response
 */
export async function fetchAnalytics(analyticsRequest) {
  const response = await fetch(`${API_BASE_URL}/api/spark/analytics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(analyticsRequest),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch analytics')
  }

  return response.json()
}
```

---

### Phase 2: Analytics Form Component

#### 2.1 Create AnalyticsForm Component
**File:** `frontend/src/components/AnalyticsForm.jsx`

**Features:**
- Multi-series selection (input field with comma-separated or array input)
- Analytics type checkboxes (statistics, growth_rates, correlations, moving_averages, time_aggregations)
- Conditional parameter inputs based on selected analytics types
- Form validation
- Submit button with loading state

**Component Structure:**
```javascript
function AnalyticsForm({ onSubmit, loading, initialSeriesIds = [] }) {
  // State for form fields
  // - seriesIds (array)
  // - analyticsTypes (array)
  // - limit, sortOrder, useCache
  // - movingAverageWindow, movingAverageType
  // - timeAggregationPeriod, timeAggregationFunction
  
  // Form handlers
  // - handleSubmit
  // - handleSeriesIdsChange
  // - handleAnalyticsTypeToggle
  // - Validation logic
}
```

**UI Elements:**
1. **Series Selection:**
   - Text input for comma-separated series IDs
   - Helper text: "Enter series IDs separated by commas (e.g., GDP, UNRATE)"
   - Validation: At least one series ID required

2. **Analytics Types Selection:**
   - Checkboxes for each type:
     - ☐ Statistics
     - ☐ Growth Rates
     - ☐ Correlations (requires 2+ series)
     - ☐ Moving Averages
     - ☐ Time Aggregations
   - Validation: At least one type required

3. **Common Parameters:**
   - Limit: Number input (1-1000, default: 100)
   - Sort Order: Radio buttons (Ascending / Descending)
   - Use Cache: Checkbox (default: checked)

4. **Moving Averages Parameters (conditional):**
   - Window Size: Number input (2-365, required if moving_averages selected)
   - Type: Radio buttons (Simple Moving Average / Exponential Moving Average)

5. **Time Aggregations Parameters (conditional):**
   - Period: Dropdown (Daily, Weekly, Monthly, Quarterly, Yearly)
   - Function: Dropdown (Mean, Sum, Min, Max, First, Last)

**Validation Rules:**
- At least one series ID required
- At least one analytics type required
- If "correlations" selected, require 2+ series
- If "moving_averages" selected, require window and type
- If "time_aggregations" selected, require period and function

---

### Phase 3: Analytics Visualization Components

#### 3.1 Statistics Visualization
**File:** `frontend/src/components/analytics/StatisticsView.jsx`

**Display Format:**
- Card-based layout showing statistics for each series
- Each card shows:
  - Series ID and title
  - Statistics grid:
    - Mean | Median
    - Std Dev | Count
    - Min | Max
    - Sum (if applicable)

**Visual Design:**
- Use cards with clear labels
- Highlight key metrics (mean, median)
- Color-code positive/negative values if applicable

#### 3.2 Growth Rates Visualization
**File:** `frontend/src/components/analytics/GrowthRatesView.jsx`

**Display Format:**
- Line chart showing:
  - Original values (primary line)
  - Growth rate overlay (secondary line or bar chart)
- Toggle between period-over-period and year-over-year
- Tooltip showing: date, value, previous value, growth rate percentage

**Chart Configuration:**
- Dual Y-axis (left: values, right: growth rate %)
- Color coding: positive growth (green), negative growth (red)
- Legend showing series and growth type

#### 3.3 Correlations Visualization
**File:** `frontend/src/components/analytics/CorrelationsView.jsx`

**Display Format:**
- Correlation matrix/heatmap
- Table format with series pairs and correlation values
- Color coding:
  - Strong positive (dark blue): > 0.7
  - Moderate positive (light blue): 0.3-0.7
  - Weak (gray): -0.3 to 0.3
  - Moderate negative (light red): -0.7 to -0.3
  - Strong negative (dark red): < -0.7

**Visual Options:**
- Table view (series pairs with correlation values)
- Heatmap visualization (if Chart.js supports it, or use CSS grid)

#### 3.4 Moving Averages Visualization
**File:** `frontend/src/components/analytics/MovingAveragesView.jsx`

**Display Format:**
- Line chart with:
  - Original data (primary line)
  - Moving average (secondary line, different color/style)
- Toggle between SMA and EMA if both available
- Window size indicator in legend

**Chart Configuration:**
- Two datasets: original values and moving average
- Different line styles (solid for original, dashed for MA)
- Legend showing series, window size, and type

#### 3.5 Time Aggregations Visualization
**File:** `frontend/src/components/analytics/TimeAggregationsView.jsx`

**Display Format:**
- Bar chart or line chart (depending on period)
- X-axis: Time periods (e.g., "2024-01", "2024-Q1", "2024")
- Y-axis: Aggregated values
- Tooltip showing: period, aggregated value, function used, observation count

**Chart Configuration:**
- Bar chart for discrete periods (monthly, quarterly, yearly)
- Line chart for continuous periods (daily, weekly)
- Legend showing aggregation function

---

### Phase 4: Main Analytics Component

#### 4.1 Create AnalyticsPanel Component
**File:** `frontend/src/components/AnalyticsPanel.jsx`

**Purpose:** Main container that orchestrates form and visualizations

**Structure:**
```javascript
function AnalyticsPanel() {
  // State management
  // - analyticsData (response from API)
  // - loading state
  // - error state
  // - selectedSeriesIds (from form or parent)
  
  // Handlers
  // - handleAnalyticsSubmit
  // - handleFormReset
  
  return (
    <div className="analytics-panel">
      <AnalyticsForm 
        onSubmit={handleAnalyticsSubmit}
        loading={loading}
        initialSeriesIds={selectedSeriesIds}
      />
      
      {loading && <LoadingSpinner />}
      {error && <ErrorMessage error={error} />}
      
      {analyticsData && (
        <div className="analytics-results">
          {analyticsData.statistics && (
            <StatisticsView data={analyticsData.statistics} />
          )}
          {analyticsData.growth_rates && (
            <GrowthRatesView data={analyticsData.growth_rates} />
          )}
          {analyticsData.correlations && (
            <CorrelationsView data={analyticsData.correlations} />
          )}
          {analyticsData.moving_averages && (
            <MovingAveragesView data={analyticsData.moving_averages} />
          )}
          {analyticsData.time_aggregations && (
            <TimeAggregationsView data={analyticsData.time_aggregations} />
          )}
        </div>
      )}
    </div>
  )
}
```

---

### Phase 5: Integration with Existing UI

#### 5.1 Update Sidebar Component
**File:** `frontend/src/components/Sidebar.jsx`

**Changes:**
- Replace placeholder in analytics section (lines 133-136) with:
  - Quick analytics link/button
  - Option to pre-fill series IDs from selected series
  - Link to analytics tab

**New Props:**
- `onAnalyticsClick` - Callback when analytics section is clicked
- `selectedSeriesIds` - Currently selected series IDs

#### 5.2 Update App Component
**File:** `frontend/src/App.jsx`

**Changes:**
1. **Enable Analytics Tab:**
   - Remove `disabled={true}` from Analytics tab button (line 215)
   - Remove placeholder title attribute

2. **Add Analytics Tab Content:**
   - Replace placeholder (lines 239-247) with `<AnalyticsPanel />`
   - Pass `seriesId` or `fredData.series_id` as initial series

3. **State Management:**
   - Add `analyticsData` state
   - Add `analyticsLoading` state
   - Add `analyticsError` state

4. **Integration Points:**
   - When series is fetched, optionally pre-fill analytics form
   - Allow switching between Main Graph and Analytics tabs
   - Share series selection between tabs

**Updated Tab Content:**
```javascript
{activeTab === 'analytics' && (
  <div className="tab-panel">
    <AnalyticsPanel 
      initialSeriesIds={fredData ? [fredData.series_id] : []}
    />
  </div>
)}
```

---

### Phase 6: Styling

#### 6.1 Create Analytics CSS
**File:** `frontend/src/components/analytics/Analytics.css`

**Styles for:**
- Analytics form layout
- Analytics results container
- Statistics cards
- Correlation matrix/table
- Chart containers
- Loading and error states

#### 6.2 Update App.css
**File:** `frontend/src/App.css`

**Add styles for:**
- Analytics tab panel
- Analytics form integration
- Responsive layout for analytics views

---

### Phase 7: Error Handling and Loading States

#### 7.1 Loading States
- Form submission: Disable form, show spinner
- API call: Show loading overlay or skeleton
- Individual visualizations: Show loading placeholders

#### 7.2 Error Handling
- API errors: Display user-friendly error messages
- Validation errors: Inline form validation
- Empty results: Show appropriate messages
- Network errors: Retry mechanism or clear error message

---

## File Structure

```
frontend/src/
├── components/
│   ├── AnalyticsForm.jsx              # NEW: Analytics form component
│   ├── AnalyticsPanel.jsx              # NEW: Main analytics container
│   ├── analytics/                      # NEW: Analytics visualization components
│   │   ├── StatisticsView.jsx
│   │   ├── GrowthRatesView.jsx
│   │   ├── CorrelationsView.jsx
│   │   ├── MovingAveragesView.jsx
│   │   ├── TimeAggregationsView.jsx
│   │   └── Analytics.css
│   ├── Sidebar.jsx                     # MODIFY: Replace placeholder
│   ├── DataGraph.jsx                   # EXISTING: May extend for analytics
│   └── ...
├── services/
│   └── api.js                          # MODIFY: Add fetchAnalytics function
├── App.jsx                             # MODIFY: Enable analytics tab, add AnalyticsPanel
└── App.css                             # MODIFY: Add analytics styles
```

---

## Implementation Details

### Data Flow

1. **User Interaction:**
   - User fills analytics form
   - User clicks "Run Analytics" button

2. **API Call:**
   - Form data validated
   - `fetchAnalytics()` called with request object
   - Loading state set to true

3. **Response Handling:**
   - API response parsed
   - Analytics data stored in state
   - Loading state set to false

4. **Visualization:**
   - AnalyticsPanel renders appropriate views based on response
   - Each view component receives its data subset
   - Charts and visualizations render

### State Management

**App Component State:**
```javascript
const [analyticsData, setAnalyticsData] = useState(null)
const [analyticsLoading, setAnalyticsLoading] = useState(false)
const [analyticsError, setAnalyticsError] = useState(null)
```

**AnalyticsPanel State:**
- Manages form state
- Handles API calls
- Manages visualization state

### Chart.js Extensions

**Additional Chart Types Needed:**
- Bar charts for time aggregations
- Dual-axis line charts for growth rates
- Heatmap for correlations (may need additional library or custom implementation)

**Chart Configuration:**
- Consistent color scheme across all charts
- Responsive design
- Accessible tooltips and legends
- Dark/light theme support

---

## Testing Strategy

### Unit Tests
- **AnalyticsForm.test.jsx:**
  - Form validation
  - Conditional field display
  - Form submission

- **AnalyticsPanel.test.jsx:**
  - State management
  - API integration
  - Error handling

- **Individual View Components:**
  - Data rendering
  - Empty state handling
  - Chart configuration

### Integration Tests
- Full analytics flow (form → API → visualization)
- Tab switching
- Series selection integration
- Error scenarios

### Manual Testing
- Test all analytics types
- Test with various series combinations
- Test parameter combinations
- Test error scenarios
- Test responsive design

---

## Success Criteria

- ✅ Users can select multiple series for analytics
- ✅ Users can choose analytics types and parameters
- ✅ All analytics types have appropriate visualizations
- ✅ Charts are interactive and responsive
- ✅ Error handling is user-friendly
- ✅ Loading states provide good UX
- ✅ Analytics tab is fully functional
- ✅ Integration with existing UI is seamless
- ✅ Code is well-tested and documented

---

## Dependencies

### Existing Dependencies (Already Installed)
- `chart.js` - Chart library
- `react-chartjs-2` - React wrapper for Chart.js

### Potential Additional Dependencies
- `chartjs-plugin-annotation` - For annotations on charts (optional)
- `react-select` - For better dropdown/select components (optional)
- `react-hot-toast` - For toast notifications (optional)

---

## Future Enhancements (Out of Scope)

- Export analytics results (CSV, PDF)
- Save analytics configurations
- Compare analytics across different time periods
- Advanced filtering and date range selection
- Real-time analytics updates
- Analytics history/previous results

---

## Notes

- This plan builds on the existing UI infrastructure
- All backend APIs are already implemented
- Focus on user experience and visual clarity
- Ensure accessibility (ARIA labels, keyboard navigation)
- Maintain consistency with existing UI design
- Consider performance for large datasets

