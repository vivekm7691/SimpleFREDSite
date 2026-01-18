# Testing Guide for Increment 1: UI Foundation Changes

This guide will help you test the sidebar and compact series display changes.

## Prerequisites

1. **Backend Server** - Must be running for category browsing to work
2. **Frontend Dev Server** - For hot-reload during development

## Option 1: Using Docker (Recommended)

### Start Backend and Frontend with Docker Compose

```bash
cd SimpleFREDSite
docker-compose up
```

This will start:
- Backend at `http://localhost:8000`
- Frontend at `http://localhost:3000`

**Note:** The Docker frontend is built for production. For development with hot-reload, use Option 2.

## Option 2: Development Mode (Hot Reload)

### Step 1: Start Backend

**Option A: Using Docker (Backend only)**
```bash
cd SimpleFREDSite
docker-compose up backend
```

**Option B: Local Python**
```bash
cd SimpleFREDSite/backend
# Activate virtual environment if you have one
python -m uvicorn app.main:app --reload --port 8000
```

### Step 2: Start Frontend Dev Server

Open a **new terminal** and run:

```bash
cd SimpleFREDSite/frontend
npm run dev
```

The frontend will start at `http://localhost:5173` (or another port if 5173 is busy).

## Testing Steps

### 1. Open the Application

Navigate to:
- **Docker**: `http://localhost:3000`
- **Dev Mode**: `http://localhost:5173` (or the port shown in terminal)

### 2. Test Sidebar Functionality

1. **Verify Sidebar is Visible**
   - You should see a sidebar on the left side of the screen
   - Sidebar should be open by default (250px wide)

2. **Test Sidebar Toggle**
   - Click the hamburger icon (☰) at the top of the sidebar
   - Sidebar should collapse to 60px width
   - Click again to expand
   - **Keyboard Shortcut**: Press `Ctrl+B` (or `Cmd+B` on Mac) to toggle

3. **Test Categories Section**
   - In the sidebar, find the "Categories" section
   - Click the "Categories" header to expand/collapse
   - Verify it expands to show category grid

### 3. Test Category Browsing

1. **Browse Categories**
   - With Categories section expanded, you should see category cards
   - Click on any category card (e.g., "Employment", "Inflation")

2. **Verify Compact Series Display**
   - After clicking a category, you should see a list of series
   - **Check these improvements:**
     - ✅ Series cards are compact (small padding)
     - ✅ Title and ID are on the same line (horizontally aligned)
     - ✅ Font sizes are smaller (0.8rem for title, 0.7rem for ID)
     - ✅ Metadata is on a separate line below
     - ✅ "Select" button is on the right side
     - ✅ Less vertical scrolling required

3. **Test Series Selection**
   - Click "Select" button on any series
   - The series ID should populate in the main search form
   - You can then click "Fetch & Summarize" to load data

4. **Test Search in Category**
   - In the category detail view, use the search input
   - Type a search term (e.g., "unemployment")
   - Series list should filter in real-time

5. **Test Back Navigation**
   - Click "← Back to Categories" button
   - Should return to category grid view

### 4. Test Main Graph Tab

1. **Fetch a Series**
   - Enter a series ID (e.g., "GDP", "UNRATE") in the main form
   - Click "Fetch & Summarize"

2. **Verify DataGraph Component**
   - Should see an interactive line chart (replaces old table)
   - Chart should be responsive and show tooltips on hover
   - Tab navigation should show "Main Graph" and "Analytics" tabs

3. **Test Tab Navigation**
   - Click "Main Graph" tab (should be active by default)
   - Click "Analytics" tab (should show placeholder for Increment 5)

### 5. Test Responsive Design

1. **Resize Browser Window**
   - Make window narrower (< 768px)
   - Sidebar should become an overlay on mobile
   - Series cards should remain compact

2. **Test Sidebar on Mobile**
   - Sidebar should slide in from left when opened
   - Should have a backdrop overlay
   - Series cards should still be horizontally aligned

## What to Look For

### ✅ Success Indicators

- Sidebar opens/closes smoothly
- Categories section expands/collapses
- Series cards are compact with horizontal layout
- Title and ID are on same line
- Font sizes are smaller (0.8rem/0.7rem)
- Less scrolling required
- Search works in category view
- Series selection populates main form
- DataGraph displays interactive chart
- Tabs switch correctly

### ❌ Issues to Report

- Sidebar doesn't toggle
- Categories don't load (check backend is running)
- Series cards still show vertically
- Font sizes are too large
- Excessive scrolling still required
- Chart doesn't display
- Tabs don't work

## Troubleshooting

### Backend Not Running
**Error**: "Failed to connect to backend at http://localhost:8000"

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend
cd SimpleFREDSite
docker-compose up backend
```

### Frontend Not Loading
**Error**: Page doesn't load or shows errors

**Solution**:
```bash
# Check if frontend dev server is running
# Look for "Local: http://localhost:5173" in terminal

# Restart frontend
cd SimpleFREDSite/frontend
npm run dev
```

### Categories Not Loading
**Error**: "Failed to fetch" in sidebar

**Solution**:
1. Verify backend is running: `http://localhost:8000/api/categories`
2. Check browser console for CORS errors
3. Ensure `VITE_API_BASE_URL` is set correctly

### Chart Not Displaying
**Error**: Chart doesn't show or shows "No data available"

**Solution**:
1. Verify you fetched a series with data
2. Check browser console for Chart.js errors
3. Ensure Chart.js dependencies are installed: `npm install chart.js react-chartjs-2`

## Quick Test Checklist

- [ ] Sidebar toggles open/close
- [ ] Categories section expands/collapses
- [ ] Category grid displays
- [ ] Clicking category shows series list
- [ ] Series cards are compact (horizontal layout)
- [ ] Title and ID on same line
- [ ] Font sizes are smaller
- [ ] Search works in category view
- [ ] Series selection works
- [ ] Back button returns to grid
- [ ] DataGraph displays chart
- [ ] Tabs switch correctly
- [ ] Responsive on mobile

## Next Steps

After testing, if everything works:
1. Commit changes to the feature branch
2. Test on different browsers (Chrome, Firefox, Safari)
3. Test with different screen sizes
4. Ready for Increment 2: Spark Infrastructure

