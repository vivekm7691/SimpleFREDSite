# Testing Guide for Category Browsing Feature

This guide provides comprehensive steps to test all changes made in the `feature/FRED-001-add-category-browsing` branch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Integration Testing](#integration-testing)
5. [Manual Testing](#manual-testing)
6. [API Endpoint Testing](#api-endpoint-testing)
7. [End-to-End User Flow Testing](#end-to-end-user-flow-testing)

---

## Prerequisites

### Environment Setup

1. **Python Environment** (for backend tests):
   ```bash
   cd SimpleFREDSite/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Node.js Environment** (for frontend tests):
   ```bash
   cd SimpleFREDSite/frontend
   npm install
   ```

3. **Environment Variables**:
   - `FRED_API_KEY`: Your FRED API key (for backend API calls)
   - `GEMINI_API_KEY`: Your Google Gemini API key (for summarization)

---

## Backend Testing

### Run All Backend Tests

```bash
cd SimpleFREDSite/backend
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test category service
pytest tests/test_category_service.py -v

# Test category API endpoints
pytest tests/test_routes.py::TestCategoryEndpoints -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
```

### Expected Results

- ✅ **test_category_service.py**: 25+ tests should pass
  - CategoryService initialization
  - get_all_categories()
  - get_category()
  - get_category_series_ids()
  - search_series_in_category()
  - get_category_series()

- ✅ **test_routes.py (CategoryEndpoints)**: 7 tests should pass
  - GET /api/categories
  - GET /api/categories/{category_id}
  - Search parameter handling
  - Error responses

### Coverage Target

Backend tests should achieve **≥70% coverage** for category-related code.

---

## Frontend Testing

### Run All Frontend Tests

```bash
cd SimpleFREDSite/frontend
npm test
```

### Run Specific Test Files

```bash
# Test CategoryCard component
npm test -- CategoryCard.test.jsx

# Test CategoryBrowser component
npm test -- CategoryBrowser.test.jsx

# Test category API functions
npm test -- api.test.js

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

### Expected Results

- ✅ **CategoryCard.test.jsx**: 9 tests should pass
  - Rendering
  - Click interactions
  - Keyboard navigation
  - Accessibility

- ✅ **CategoryBrowser.test.jsx**: 9 tests should pass
  - Initial rendering
  - View switching
  - Series selection
  - Error handling

- ✅ **api.test.js (category functions)**: 12 tests should pass
  - fetchCategories()
  - fetchCategorySeries()
  - searchCategorySeries()
  - Error handling

---

## Integration Testing

### Using Docker Compose

1. **Start the services**:
   ```bash
   cd SimpleFREDSite
   docker-compose up -d
   ```

2. **Wait for services to be healthy**:
   ```bash
   docker-compose ps
   # Both backend and frontend should show "healthy"
   ```

3. **Run integration tests** (if available):
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm integration-tests
   ```

### Manual Integration Test

1. **Start backend**:
   ```bash
   cd SimpleFREDSite/backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start frontend** (in another terminal):
   ```bash
   cd SimpleFREDSite/frontend
   npm run dev
   ```

3. **Verify services are running**:
   - Backend: http://localhost:8000/docs (FastAPI docs)
   - Frontend: http://localhost:3000 (or Vite dev server port)

---

## API Endpoint Testing

### Using FastAPI Docs (Recommended)

1. Navigate to: http://localhost:8000/docs
2. Test the following endpoints:

#### 1. GET /api/categories
- **Expected Response**: List of all categories with series counts
- **Test**: Click "Try it out" → "Execute"
- **Verify**: 
  - Returns 200 status
  - Contains categories array
  - Each category has: id, name, icon, description, series_count

#### 2. GET /api/categories/{category_id}
- **Test with**: `employment`
- **Expected Response**: List of series in employment category
- **Verify**:
  - Returns 200 status
  - Contains category_id, category_name
  - Contains series array with metadata
  - Each series has: id, title, frequency, units, seasonal_adjustment

#### 3. GET /api/categories/{category_id}?q={search_term}
- **Test with**: `employment` and `q=UN`
- **Expected Response**: Filtered series matching "UN"
- **Verify**:
  - Returns 200 status
  - Only series with "UN" in ID are returned
  - Search is case-insensitive

#### 4. Error Cases
- **Test**: GET /api/categories/invalid_category
- **Expected**: 404 Not Found with error message

### Using cURL

```bash
# Get all categories
curl http://localhost:8000/api/categories

# Get series for employment category
curl http://localhost:8000/api/categories/employment

# Search series in category
curl "http://localhost:8000/api/categories/employment?q=UN"

# Test invalid category (should return 404)
curl http://localhost:8000/api/categories/invalid
```

### Using Postman/Insomnia

Import the following requests:

1. **GET Categories**
   - Method: GET
   - URL: `http://localhost:8000/api/categories`

2. **GET Category Series**
   - Method: GET
   - URL: `http://localhost:8000/api/categories/employment`

3. **Search Category Series**
   - Method: GET
   - URL: `http://localhost:8000/api/categories/employment?q=UN`

---

## Manual Testing

### Test Checklist

#### 1. Category Grid View
- [ ] Navigate to http://localhost:3000
- [ ] Verify "Browse by Category" section appears below search form
- [ ] Verify category cards are displayed in a grid (3 columns on desktop)
- [ ] Verify each category shows:
  - [ ] Icon (emoji)
  - [ ] Category name
  - [ ] Series count
- [ ] Verify categories match expected list:
  - [ ] Employment
  - [ ] Inflation
  - [ ] GDP & Components
  - [ ] Interest Rates
  - [ ] Money & Banking
  - [ ] Production & Business Activity
  - [ ] Prices

#### 2. Category Card Interactions
- [ ] Click on a category card
- [ ] Verify it navigates to category detail view
- [ ] Test keyboard navigation:
  - [ ] Tab to focus a category card
  - [ ] Press Enter - should navigate to detail view
  - [ ] Press Space - should navigate to detail view
- [ ] Verify hover effects (if visible):
  - [ ] Card elevates slightly
  - [ ] Border highlights
  - [ ] Shadow appears

#### 3. Category Detail View
- [ ] Verify breadcrumb navigation appears
- [ ] Verify "Back to Categories" button is present
- [ ] Verify category name and series count are displayed
- [ ] Verify search input is present
- [ ] Verify series list is displayed
- [ ] Verify each series card shows:
  - [ ] Series icon
  - [ ] Series title
  - [ ] Series ID (in parentheses)
  - [ ] Metadata (frequency, seasonal adjustment, units)
  - [ ] "Select Series" button

#### 4. Search Functionality
- [ ] Type in search box (e.g., "UN")
- [ ] Verify series list filters in real-time
- [ ] Verify only matching series are shown
- [ ] Verify search is case-insensitive
- [ ] Clear search and verify all series return
- [ ] Test with partial matches

#### 5. Series Selection
- [ ] Click "Select Series" button on a series card
- [ ] Verify series ID is auto-filled in the main search input
- [ ] Verify category browser resets to grid view (after data fetch)
- [ ] Click "Fetch & Summarize"
- [ ] Verify FRED data is fetched and displayed
- [ ] Verify AI summary is generated

#### 6. Back Navigation
- [ ] From category detail view, click "Back to Categories"
- [ ] Verify it returns to category grid view
- [ ] Verify search term is cleared
- [ ] Verify category selection is cleared

#### 7. Error Handling
- [ ] Stop backend server
- [ ] Verify error message is displayed in category browser
- [ ] Restart backend
- [ ] Verify categories load successfully

#### 8. Responsive Design
- [ ] Test on desktop (3-column grid)
- [ ] Test on tablet (2-column grid)
- [ ] Test on mobile (1-column stack)
- [ ] Verify cards are properly sized on each breakpoint
- [ ] Verify touch interactions work on mobile

#### 9. Loading States
- [ ] Verify "Loading categories..." appears while fetching
- [ ] Verify loading state in category detail while fetching series
- [ ] Verify loading indicators disappear when data loads

#### 10. Empty States
- [ ] Verify "No categories available" if categories fail to load
- [ ] Verify empty search results are handled gracefully

---

## End-to-End User Flow Testing

### Complete User Journey

1. **Browse Categories**
   - User lands on homepage
   - Sees category grid below search form
   - Clicks "Employment" category

2. **View Category Series**
   - Category detail view opens
   - Sees list of employment-related series
   - Searches for "UN" to filter unemployment-related series

3. **Select Series**
   - Clicks "Select Series" on "Unemployment Rate (UNRATE)"
   - Series ID "UNRATE" is auto-filled in main search input
   - Category browser resets to grid view

4. **Fetch Data**
   - User clicks "Fetch & Summarize"
   - FRED data is fetched and displayed
   - AI summary is generated

5. **Browse Another Category**
   - User clicks "Back" or selects another category
   - Repeats process with different category

### Test Scenarios

#### Scenario 1: Happy Path
1. Load page → See categories
2. Click category → See series
3. Select series → Auto-fill input
4. Fetch data → See results

#### Scenario 2: Search and Filter
1. Click category
2. Type search term
3. Verify filtered results
4. Select filtered series

#### Scenario 3: Navigation
1. Click category → Detail view
2. Click back → Grid view
3. Click different category → New detail view

#### Scenario 4: Error Recovery
1. Stop backend
2. See error message
3. Restart backend
4. Verify recovery

---

## Performance Testing

### Backend Performance
```bash
# Test API response times
time curl http://localhost:8000/api/categories
time curl http://localhost:8000/api/categories/employment
```

### Frontend Performance
- Open browser DevTools → Network tab
- Verify category API calls complete in < 500ms
- Verify no unnecessary re-renders (React DevTools)

---

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all category cards
- [ ] Enter/Space activates card
- [ ] Focus indicators are visible
- [ ] Screen reader announces category information

### Screen Reader Testing
- [ ] Use NVDA (Windows) or VoiceOver (Mac)
- [ ] Verify aria-labels are announced
- [ ] Verify role="button" is recognized
- [ ] Verify navigation is logical

### Color Contrast
- [ ] Verify text is readable
- [ ] Verify focus indicators are visible
- [ ] Test in light/dark mode (if applicable)

---

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

---

## Troubleshooting

### Backend Tests Failing
- Verify Python environment is activated
- Verify all dependencies are installed: `pip install -r requirements-dev.txt`
- Check for API key in environment variables

### Frontend Tests Failing
- Verify Node modules are installed: `npm install`
- Clear Jest cache: `npm test -- --clearCache`
- Verify test environment setup

### API Endpoints Not Working
- Verify backend is running: `curl http://localhost:8000/health`
- Check backend logs for errors
- Verify FRED_API_KEY is set

### Frontend Not Loading Categories
- Check browser console for errors
- Verify API_BASE_URL is correct
- Check network tab for failed requests
- Verify CORS is configured correctly

---

## Test Results Summary

After completing all tests, document:

- ✅ Backend tests: X/Y passing
- ✅ Frontend tests: X/Y passing
- ✅ Manual tests: X/Y scenarios passing
- ✅ API endpoints: X/Y working correctly
- ✅ Browser compatibility: X/Y browsers tested
- ✅ Accessibility: X/Y checks passing

---

## Next Steps

After successful testing:
1. Review test coverage reports
2. Fix any failing tests
3. Address any bugs found during manual testing
4. Update documentation if needed
5. Create pull request to merge into `develop` branch

---

## Additional Resources

- [Backend Test Files](../backend/tests/)
- [Frontend Test Files](../frontend/__tests__/)
- [API Documentation](http://localhost:8000/docs)
- [Wireframe Documentation](./wireframes/category-browsing-wireframe.md)
