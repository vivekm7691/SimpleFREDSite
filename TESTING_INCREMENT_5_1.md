# Manual Testing Guide for Increment 5.1: Basic Analytics UI

## Prerequisites

1. **Backend Server Running:**
   ```bash
   cd SimpleFREDSite
   docker-compose up
   ```
   Or if running backend separately:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend Server Running:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application:**
   - Open browser to `http://localhost:3000` (or the port shown in terminal)

4. **Verify Backend Health:**
   - Navigate to `http://localhost:8000/health` - should return `{"status":"healthy"}`
   - Navigate to `http://localhost:8000/api/spark/health` - should return Spark status

---

## Test Scenarios

### Phase 1: API Integration Testing

#### Test 1.1: Verify API Endpoint
- **Action:** Open browser DevTools → Network tab
- **Expected:** API calls to `/api/spark/analytics` should be visible when form is submitted

#### Test 1.2: Test API with curl/PowerShell
```powershell
$uri = "http://localhost:8000/api/spark/analytics"
$body = @{
    series_ids = @("GDP")
    analytics_types = @("statistics")
    limit = 10
    sort_order = "desc"
    use_cache = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri $uri -Method POST -ContentType "application/json" -Body $body
```
- **Expected:** Returns analytics response with statistics data

---

### Phase 2: Analytics Form Component Testing

#### Test 2.1: Form Rendering
- **Action:** Navigate to Analytics tab
- **Expected:** 
  - Form is visible with all input fields
  - Series IDs input field is present
  - Analytics type checkboxes are visible
  - Common parameters (limit, sort order, use cache) are visible

#### Test 2.2: Series ID Input
- **Test Cases:**
  1. Enter single series: `GDP`
  2. Enter multiple series: `GDP, UNRATE`
  3. Enter with spaces: `GDP, UNRATE, CPIAUCSL`
  4. Leave empty and submit → Should show error
  5. Enter invalid format (e.g., `GDP@123`) → Should show error
  6. Enter more than 50 series → Should show error

#### Test 2.3: Analytics Types Selection
- **Test Cases:**
  1. Select "Statistics" checkbox
  2. Select multiple types (e.g., Statistics + Growth Rates)
  3. Select "Correlations" with only 1 series → Should show warning
  4. Select "Correlations" with 2+ series → Should work
  5. Submit with no types selected → Should show error

#### Test 2.4: Conditional Parameters
- **Moving Averages:**
  1. Select "Moving Averages" checkbox → Parameters section should appear
  2. Change window size to 14
  3. Change window size to 1 → Should show error (min is 2)
  4. Change window size to 500 → Should show error (max is 365)
  5. Toggle between SMA and EMA
  6. Deselect "Moving Averages" → Parameters section should disappear

- **Time Aggregations:**
  1. Select "Time Aggregations" checkbox → Parameters section should appear
  2. Change period to "Quarterly"
  3. Change function to "Sum"
  4. Deselect "Time Aggregations" → Parameters section should disappear

#### Test 2.5: Common Parameters
- **Test Cases:**
  1. Change limit to 50
  2. Change limit to 2000 → Should be capped at 1000
  3. Toggle sort order between Ascending and Descending
  4. Toggle "Use Cache" checkbox

#### Test 2.6: Form Submission
- **Test Cases:**
  1. Fill valid form and click "Run Analytics" → Should call API
  2. Check browser console → Should see analytics request object
  3. Verify request object has correct structure

#### Test 2.7: Loading State
- **Test Cases:**
  1. Submit form → Form should be disabled
  2. Submit button should show "Running Analytics..." text
  3. All inputs should be disabled during loading

#### Test 2.8: Reset Button
- **Test Cases:**
  1. Fill out form completely
  2. Click "Reset" → All fields should clear to defaults

#### Test 2.9: Initial Values
- **Test Cases:**
  1. Fetch a series (e.g., "GDP") in Main Graph tab
  2. Switch to Analytics tab → Series ID should be pre-filled with "GDP"

---

### Phase 3: Analytics Visualization Components Testing

#### Test 3.1: Statistics View
- **Action:** Submit form with "Statistics" selected
- **Expected:**
  - Card-based layout showing statistics per series
  - Displays: Mean, Median, Std Dev, Min, Max, Count, Sum
  - Responsive grid layout
  - Numbers properly formatted

#### Test 3.2: Growth Rates View
- **Action:** Submit form with "Growth Rates" selected
- **Expected:**
  - Line chart with dual Y-axis (values on left, growth rate % on right)
  - Filter dropdown for growth type (if multiple types)
  - Color-coded lines for different series
  - Tooltips showing values and growth rates

#### Test 3.3: Correlations View
- **Action:** Submit form with "Correlations" selected (requires 2+ series)
- **Expected:**
  - Sortable table with series pairs and correlation values
  - Color coding based on correlation strength
  - Legend showing correlation strength categories
  - Click column headers to sort

#### Test 3.4: Moving Averages View
- **Action:** Submit form with "Moving Averages" selected (with window size and type)
- **Expected:**
  - Line chart showing original data (solid line) and moving average (dashed line)
  - Window size and type (SMA/EMA) indicator
  - Multiple series support with different colors

#### Test 3.5: Time Aggregations View
- **Action:** Submit form with "Time Aggregations" selected (with period and function)
- **Expected:**
  - Bar chart for discrete periods (monthly, quarterly, yearly)
  - Line chart for continuous periods (daily, weekly)
  - Aggregation function indicator
  - Proper period labels on X-axis

#### Test 3.6: Empty Data Handling
- **Action:** Submit form with series that has no data
- **Expected:** Each view component should show "No data available" message

---

### Phase 4: AnalyticsPanel Integration Testing

#### Test 4.1: Panel Rendering
- **Action:** Navigate to Analytics tab
- **Expected:**
  - AnalyticsPanel is visible
  - Header with title and description
  - Form is integrated
  - Results section appears after submission

#### Test 4.2: API Integration
- **Action:** Submit valid form
- **Expected:**
  - Loading spinner appears
  - API call is made
  - Results are displayed in appropriate visualization components
  - No errors in console

#### Test 4.3: Multiple Analytics Types
- **Action:** Submit form with multiple analytics types selected
- **Expected:**
  - All selected analytics types are displayed
  - Each visualization component appears in order
  - Results are properly formatted

---

### Phase 5: UI Integration Testing

#### Test 5.1: Analytics Tab
- **Test Cases:**
  1. Click "Analytics" tab → Should switch to analytics view
  2. Tab button should be highlighted when active
  3. Tab should not be disabled

#### Test 5.2: Sidebar Integration
- **Test Cases:**
  1. Expand "Spark Analytics" section in sidebar
  2. Click "Open Analytics Dashboard" button → Should switch to Analytics tab
  3. Verify sidebar shows analytics features list

#### Test 5.3: Series Pre-filling
- **Test Cases:**
  1. Fetch series "GDP" in Main Graph tab
  2. Switch to Analytics tab → Series ID should be pre-filled
  3. Add more series IDs manually
  4. Submit form → Should work correctly

#### Test 5.4: Tab Switching
- **Test Cases:**
  1. Switch between Main Graph and Analytics tabs
  2. Verify data persists when switching tabs
  3. Verify form state is maintained

---

### Phase 6: Styling and Responsive Design Testing

#### Test 6.1: Desktop Layout
- **Test Cases:**
  1. View on desktop (1920x1080 or larger)
  2. Verify analytics panel fits within tab panel
  3. Verify charts are properly sized
  4. Verify statistics cards are in grid layout

#### Test 6.2: Tablet Layout
- **Test Cases:**
  1. Resize browser to tablet size (768px - 1024px width)
  2. Verify analytics panel adjusts padding
  3. Verify charts remain visible and usable
  4. Verify statistics cards adapt to smaller screen

#### Test 6.3: Mobile Layout
- **Test Cases:**
  1. Resize browser to mobile size (< 768px width)
  2. Verify analytics panel padding is reduced
  3. Verify form stacks vertically
  4. Verify charts are scrollable if needed
  5. Verify statistics cards stack in single column

#### Test 6.4: Chart Responsiveness
- **Test Cases:**
  1. Resize browser window while charts are displayed
  2. Verify charts resize properly
  3. Verify tooltips still work
  4. Verify legends remain visible

---

### Phase 7: Error Handling and Loading States Testing

#### Test 7.1: Loading States
- **Test Cases:**
  1. Submit form → Loading spinner should appear
  2. Form should be disabled during loading
  3. Loading message should be visible
  4. Loading hint should appear

#### Test 7.2: Network Errors
- **Test Cases:**
  1. Stop backend server
  2. Submit form → Should show network error message
  3. Error message should be user-friendly
  4. "Try Again" button should appear
  5. Click "Try Again" → Should scroll to form

#### Test 7.3: API Errors
- **Test Cases:**
  1. Submit form with invalid series ID → Should show 400 error
  2. Submit form with invalid parameters → Should show appropriate error
  3. Error messages should be specific and helpful

#### Test 7.4: Spark Service Unavailable
- **Test Cases:**
  1. If Spark is not running, submit form → Should show 503 error
  2. Error message should mention Spark service
  3. "Try Again" button should be available

#### Test 7.5: Timeout Errors
- **Test Cases:**
  1. Submit form with very large limit (1000) and many series
  2. If timeout occurs, should show timeout error message
  3. Error should suggest reducing series count or limit

#### Test 7.6: Empty Results
- **Test Cases:**
  1. Submit form with series that has no data
  2. Should show "No analytics results to display" message
  3. Should provide guidance to user

#### Test 7.7: Error Dismissal
- **Test Cases:**
  1. Trigger an error
  2. Click "Dismiss" button → Error should disappear
  3. Form should remain usable

---

## Comprehensive Test Scenarios

### Scenario 1: Complete Analytics Workflow
1. Navigate to Analytics tab
2. Enter series IDs: `GDP, UNRATE`
3. Select analytics types: Statistics, Growth Rates, Correlations
4. Set limit to 50
5. Submit form
6. **Expected:** All three visualizations appear with data

### Scenario 2: Moving Averages Workflow
1. Navigate to Analytics tab
2. Enter series ID: `GDP`
3. Select "Moving Averages"
4. Set window size to 14
5. Select "EMA"
6. Submit form
7. **Expected:** Chart shows original data and EMA line

### Scenario 3: Time Aggregations Workflow
1. Navigate to Analytics tab
2. Enter series ID: `GDP`
3. Select "Time Aggregations"
4. Set period to "Quarterly"
5. Set function to "Sum"
6. Submit form
7. **Expected:** Bar chart showing quarterly sums

### Scenario 4: Error Recovery
1. Stop backend server
2. Submit form → Error appears
3. Start backend server
4. Click "Try Again" → Form scrolls into view
5. Submit form again
6. **Expected:** Analytics results appear

### Scenario 5: Multi-Series Analytics
1. Navigate to Analytics tab
2. Enter series IDs: `GDP, UNRATE, CPIAUCSL, FEDFUNDS`
3. Select all analytics types
4. Submit form
5. **Expected:** All visualizations show data for all series

---

## Browser Console Testing

### Check for Errors
1. Open browser DevTools (F12)
2. Go to Console tab
3. Perform various actions
4. **Expected:** No JavaScript errors should appear

### Check Network Requests
1. Open browser DevTools (F12)
2. Go to Network tab
3. Submit analytics form
4. **Expected:**
   - POST request to `/api/spark/analytics`
   - Request payload is correct
   - Response status is 200
   - Response contains analytics data

---

## Performance Testing

### Test Response Times
1. Submit form with 1 series, 1 analytics type
2. Measure time from submission to results display
3. Submit form with 5 series, all analytics types
4. Compare response times
5. **Expected:** Response times are reasonable (< 30 seconds for most cases)

### Test Large Data Sets
1. Submit form with limit=1000 and multiple series
2. Verify charts render properly
3. Verify no browser freezing
4. **Expected:** Application remains responsive

---

## Accessibility Testing

### Keyboard Navigation
1. Use Tab key to navigate through form
2. Use Enter to submit form
3. Use Space to toggle checkboxes
4. **Expected:** All form elements are keyboard accessible

### Screen Reader Testing
1. Enable screen reader (if available)
2. Navigate through analytics form
3. **Expected:** Form elements are properly labeled

---

## Regression Testing

### Verify Existing Functionality
1. Test Main Graph tab still works
2. Test category browser still works
3. Test FRED data fetching still works
4. Test summarization still works
5. **Expected:** No existing functionality is broken

---

## Test Checklist

- [ ] Form renders correctly
- [ ] Form validation works
- [ ] Form submission works
- [ ] Loading states appear
- [ ] Error handling works
- [ ] Statistics view displays correctly
- [ ] Growth rates view displays correctly
- [ ] Correlations view displays correctly
- [ ] Moving averages view displays correctly
- [ ] Time aggregations view displays correctly
- [ ] Analytics tab is accessible
- [ ] Sidebar integration works
- [ ] Series pre-filling works
- [ ] Responsive design works
- [ ] Error messages are user-friendly
- [ ] Retry functionality works
- [ ] Empty states are handled
- [ ] No console errors
- [ ] Network requests are correct
- [ ] Performance is acceptable

---

## Troubleshooting

### Issue: Form doesn't submit
- **Check:** Backend server is running
- **Check:** Browser console for errors
- **Check:** Network tab for failed requests

### Issue: Charts don't display
- **Check:** Analytics data is returned from API
- **Check:** Browser console for JavaScript errors
- **Check:** Chart.js is loaded correctly

### Issue: Error messages not showing
- **Check:** Error state is being set correctly
- **Check:** Error component is rendering
- **Check:** CSS styles are applied

### Issue: Loading spinner not appearing
- **Check:** Loading state is being set
- **Check:** CSS animation is working
- **Check:** Component is rendering

---

## Notes

- All tests should be performed in a clean browser session
- Clear browser cache if experiencing issues
- Check browser console for any warnings or errors
- Verify API responses in Network tab
- Test with different browsers (Chrome, Firefox, Edge)
- Test with different screen sizes
- Test with different data sets

