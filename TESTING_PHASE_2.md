# Testing Phase 2: AnalyticsForm Component

## Quick Start: Temporary Integration

To test the AnalyticsForm component, temporarily integrate it into `App.jsx`:

### Step 1: Import the Component

Add this import at the top of `App.jsx`:

```javascript
import AnalyticsForm from './components/AnalyticsForm'
```

### Step 2: Replace Analytics Tab Placeholder

Find the Analytics tab placeholder (around line 239-247) and replace it with:

```javascript
{activeTab === 'analytics' && (
  <div className="tab-panel">
    <AnalyticsForm 
      onSubmit={(request) => {
        console.log('Analytics Request:', request)
        alert('Form submitted! Check console for request data.\n\n' + JSON.stringify(request, null, 2))
      }}
      loading={false}
      initialSeriesIds={fredData ? [fredData.series_id] : []}
    />
  </div>
)}
```

### Step 3: Enable Analytics Tab

Remove `disabled={true}` from the Analytics tab button (around line 215):

```javascript
<button
  className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
  onClick={() => setActiveTab('analytics')}
  aria-selected={activeTab === 'analytics'}
  // Remove: disabled={true}
  // Remove: title="Analytics features coming in Increment 5"
>
  Analytics
</button>
```

### Step 4: Start the Development Server

```bash
cd frontend
npm run dev
```

### Step 5: Test the Form

1. Navigate to `http://localhost:3000` (or the port shown)
2. Click the "Analytics" tab
3. Fill out the form and test various scenarios

---

## Testing Scenarios

### 1. Series ID Input
- ✅ Enter single series: `GDP`
- ✅ Enter multiple series: `GDP, UNRATE`
- ✅ Enter with spaces: `GDP, UNRATE, CPIAUCSL`
- ✅ Test empty input → Should show error: "At least one series ID is required"
- ✅ Test invalid format (e.g., `GDP@123`) → Should show error

### 2. Analytics Types Selection
- ✅ Select "Statistics" checkbox
- ✅ Select multiple types (e.g., Statistics + Growth Rates)
- ✅ Select "Correlations" with only 1 series → Should show warning "(requires 2+ series)"
- ✅ Submit with no types selected → Should show error: "At least one analytics type is required"
- ✅ Select "Correlations" with 2+ series → Should work

### 3. Common Parameters
- ✅ Change limit to 50
- ✅ Change limit to 2000 → Should be capped at 1000
- ✅ Toggle sort order between Ascending and Descending
- ✅ Toggle "Use Cache" checkbox

### 4. Moving Averages (Conditional)
- ✅ Select "Moving Averages" checkbox → Parameters section should appear
- ✅ Change window size to 14
- ✅ Change window size to 1 → Should show error (min is 2)
- ✅ Change window size to 500 → Should show error (max is 365)
- ✅ Toggle between SMA and EMA
- ✅ Deselect "Moving Averages" → Parameters section should disappear
- ✅ Select "Moving Averages" but don't set window → Submit should show error

### 5. Time Aggregations (Conditional)
- ✅ Select "Time Aggregations" checkbox → Parameters section should appear
- ✅ Change period to "Quarterly"
- ✅ Change function to "Sum"
- ✅ Deselect "Time Aggregations" → Parameters section should disappear
- ✅ Select "Time Aggregations" but don't set period → Submit should show error

### 6. Form Submission
- ✅ Fill valid form and click "Run Analytics" → Should call `onSubmit` callback
- ✅ Check browser console → Should see the analytics request object
- ✅ Verify request object has correct structure:
  ```javascript
  {
    series_ids: ["GDP", "UNRATE"],
    analytics_types: ["statistics", "growth_rates"],
    limit: 100,
    sort_order: "desc",
    use_cache: true,
    moving_average_window: 7,        // if moving_averages selected
    moving_average_type: "sma",       // if moving_averages selected
    time_aggregation_period: "monthly",      // if time_aggregations selected
    time_aggregation_function: "mean"        // if time_aggregations selected
  }
  ```

### 7. Loading State
- ✅ Set `loading={true}` in props → Form should be disabled
- ✅ Submit button should show spinner and "Running Analytics..." text

### 8. Reset Button
- ✅ Fill out form
- ✅ Click "Reset" → All fields should clear to defaults

### 9. Initial Values
- ✅ Fetch a series (e.g., "GDP") in Main Graph tab
- ✅ Switch to Analytics tab → Series ID should be pre-filled with "GDP"

### 10. Responsive Design
- ✅ Resize browser window → Form should adapt
- ✅ Test on mobile viewport → Form should stack vertically

---

## Expected Console Output

When you submit a valid form, you should see in the browser console:

```javascript
Analytics Request: {
  series_ids: ["GDP", "UNRATE"],
  analytics_types: ["statistics", "growth_rates"],
  limit: 100,
  sort_order: "desc",
  use_cache: true
}
```

If moving averages are selected:
```javascript
{
  ...,
  moving_average_window: 7,
  moving_average_type: "sma"
}
```

If time aggregations are selected:
```javascript
{
  ...,
  time_aggregation_period: "monthly",
  time_aggregation_function: "mean"
}
```

---

## Visual Checks

- ✅ Form sections have proper spacing
- ✅ Error messages appear in red below invalid fields
- ✅ Required fields are marked with red asterisk (*)
- ✅ Conditional sections appear/disappear smoothly
- ✅ Loading spinner appears when loading is true
- ✅ Form is disabled when loading is true
- ✅ Help text appears below inputs
- ✅ Warning text appears for correlations with < 2 series

---

## Browser DevTools Testing

1. **React DevTools:**
   - Install React DevTools browser extension
   - Inspect AnalyticsForm component
   - View state changes as you interact with form

2. **Console Testing:**
   - Open DevTools Console (F12)
   - Type in form fields and watch for validation
   - Submit form and check console output

3. **Network Tab:**
   - When form is submitted, you can monitor network requests
   - (Note: Currently onSubmit just logs to console, no actual API call yet)

---

## Reverting Test Changes

After testing, you can revert the temporary changes to `App.jsx`:

```bash
git checkout frontend/src/App.jsx
```

Or manually remove the import and restore the placeholder.

---

## Next Steps

Once Phase 2 testing is complete:
- Phase 3: Create visualization components
- Phase 4: Create AnalyticsPanel to integrate form with API
- Phase 5: Integrate into App.jsx permanently

