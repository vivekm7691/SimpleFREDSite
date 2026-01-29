# Testing Guide for Increment 6: Advanced Analytics

## Overview
This guide provides instructions for manually testing the advanced analytics features implemented in Increment 6.

## Prerequisites

1. **Backend service running**:
   ```powershell
   # From SimpleFREDSite directory
   docker-compose up backend
   ```
   Or ensure backend is running on `http://localhost:8000`

2. **FRED API Key**: Ensure `.env` file contains `FRED_API_KEY`

3. **Docker containers**: Backend container should be running with Spark available

## Testing the Advanced Analytics Endpoint

### Endpoint
`POST http://localhost:8000/api/spark/advanced-analytics`

### Test Script
Use the provided PowerShell script: `test-advanced-analytics.ps1`

```powershell
# Run the test script
.\test-advanced-analytics.ps1
```

## Manual Test Cases

### Test 1: Anomaly Detection (Z-Score Method)

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["anomalies"],
  "limit": 100,
  "sort_order": "desc",
  "use_cache": true,
  "anomaly_method": "z_score",
  "anomaly_threshold": 3.0
}
```

**Expected:**
- Returns list of anomalies with:
  - `series_id`, `date`, `value`
  - `expected_value` (mean)
  - `deviation` (Z-score)
  - `detection_method`: "z_score"
  - `severity`: "low", "medium", or "high"

**PowerShell Command:**
```powershell
$body = @{
    series_ids = @("GDP")
    analytics_types = @("anomalies")
    limit = 100
    sort_order = "desc"
    use_cache = $true
    anomaly_method = "z_score"
    anomaly_threshold = 3.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/spark/advanced-analytics" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body | ConvertTo-Json -Depth 10
```

### Test 2: Anomaly Detection (IQR Method)

**Request:**
```json
{
  "series_ids": ["UNRATE"],
  "analytics_types": ["anomalies"],
  "limit": 100,
  "anomaly_method": "iqr"
}
```

**Expected:**
- Returns anomalies detected using interquartile range method
- `detection_method`: "iqr"
- `expected_value` should be the median

### Test 3: Anomaly Detection (Moving Average Method)

**Request:**
```json
{
  "series_ids": ["CPIAUCSL"],
  "analytics_types": ["anomalies"],
  "limit": 100,
  "anomaly_method": "moving_average",
  "anomaly_threshold": 2.5
}
```

**Expected:**
- Returns anomalies based on deviation from moving average
- `detection_method`: "moving_average"
- `expected_value` should be the moving average

### Test 4: Volatility Analysis

**Request:**
```json
{
  "series_ids": ["GDP", "UNRATE"],
  "analytics_types": ["volatility"],
  "limit": 100,
  "volatility_window": 30
}
```

**Expected:**
- Returns volatility metrics for each date:
  - `volatility`: Rolling volatility
  - `annualized_volatility`: Annualized volatility
  - `return_value`: Period return (percentage)
  - `window_size`: 30

### Test 5: Trend Analysis (Linear)

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["trends"],
  "limit": 100,
  "trend_type": "linear"
}
```

**Expected:**
- Returns trend analysis results:
  - `trend_type`: "linear"
  - `slope`: Linear trend slope
  - `intercept`: Y-intercept
  - `r_squared`: Trend strength (0-1)
  - `direction`: "increasing", "decreasing", or "stable"

### Test 6: Trend Analysis (Polynomial)

**Request:**
```json
{
  "series_ids": ["UNRATE"],
  "analytics_types": ["trends"],
  "limit": 100,
  "trend_type": "polynomial",
  "polynomial_degree": 2
}
```

**Expected:**
- Returns polynomial trend analysis
- `trend_type`: "polynomial"
- `polynomial_degree`: 2

### Test 7: Seasonal Decomposition (Additive)

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["seasonal_decomposition"],
  "limit": 200,
  "decomposition_type": "additive",
  "seasonal_period": 12
}
```

**Expected:**
- Returns decomposition for each date:
  - `actual_value`: Original value
  - `trend_component`: Trend component
  - `seasonal_component`: Seasonal component
  - `residual_component`: Residual component
  - `decomposition_type`: "additive"

### Test 8: Seasonal Decomposition (Multiplicative)

**Request:**
```json
{
  "series_ids": ["CPIAUCSL"],
  "analytics_types": ["seasonal_decomposition"],
  "limit": 200,
  "decomposition_type": "multiplicative",
  "seasonal_period": 12
}
```

**Expected:**
- Returns multiplicative decomposition
- `decomposition_type`: "multiplicative"

### Test 9: Forecasting (Linear Regression)

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["forecasts"],
  "limit": 100,
  "forecast_horizon": 12,
  "forecast_method": "linear_regression"
}
```

**Expected:**
- Returns forecasted values for next 12 periods:
  - `forecasted_value`: Predicted value
  - `lower_bound`: Confidence interval lower bound
  - `upper_bound`: Confidence interval upper bound
  - `confidence_level`: 0.95
  - `forecast_method`: "linear_regression"

### Test 10: Forecasting (Exponential Smoothing)

**Request:**
```json
{
  "series_ids": ["UNRATE"],
  "analytics_types": ["forecasts"],
  "limit": 100,
  "forecast_horizon": 6,
  "forecast_method": "exponential_smoothing"
}
```

**Expected:**
- Returns exponential smoothing forecasts
- `forecast_method`: "exponential_smoothing"

### Test 11: Forecasting (ARIMA)

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["forecasts"],
  "limit": 100,
  "forecast_horizon": 12,
  "forecast_method": "arima"
}
```

**Expected:**
- Returns ARIMA forecasts (requires pmdarima package)
- `forecast_method`: "arima"
- Includes confidence intervals

**Note:** ARIMA requires `pmdarima` package. If not available, falls back to linear regression.

### Test 12: Multiple Analytics Types

**Request:**
```json
{
  "series_ids": ["GDP", "UNRATE"],
  "analytics_types": ["anomalies", "volatility", "trends"],
  "limit": 100,
  "anomaly_method": "z_score",
  "trend_type": "linear",
  "volatility_window": 30
}
```

**Expected:**
- Returns all three analytics types in response
- `anomalies`: List of detected anomalies
- `volatility`: List of volatility metrics
- `trends`: List of trend analysis results

### Test 13: Error Handling - Missing Required Parameters

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["forecasts"],
  "limit": 100
}
```

**Expected:**
- Returns 400 Bad Request
- Error message indicating `forecast_horizon` and `forecast_method` are required

### Test 14: Error Handling - Invalid Analytics Type

**Request:**
```json
{
  "series_ids": ["GDP"],
  "analytics_types": ["invalid_type"],
  "limit": 100
}
```

**Expected:**
- Returns 400 Bad Request
- Error message indicating invalid analytics type

### Test 15: Error Handling - Spark Unavailable

**Scenario:** Stop Spark service or make it unavailable

**Expected:**
- Returns 503 Service Unavailable
- Error message: "Spark service is not available"

## Quick Test Commands

### Test Anomaly Detection
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/spark/advanced-analytics" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"series_ids":["GDP"],"analytics_types":["anomalies"],"limit":100,"anomaly_method":"z_score","anomaly_threshold":3.0}' | ConvertTo-Json -Depth 10
```

### Test Volatility
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/spark/advanced-analytics" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"series_ids":["GDP"],"analytics_types":["volatility"],"limit":100,"volatility_window":30}' | ConvertTo-Json -Depth 10
```

### Test Trends
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/spark/advanced-analytics" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"series_ids":["GDP"],"analytics_types":["trends"],"limit":100,"trend_type":"linear"}' | ConvertTo-Json -Depth 10
```

### Test Forecasting
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/spark/advanced-analytics" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"series_ids":["GDP"],"analytics_types":["forecasts"],"limit":100,"forecast_horizon":12,"forecast_method":"linear_regression"}' | ConvertTo-Json -Depth 10
```

## Verification Checklist

- [ ] Anomaly detection (Z-score) returns anomalies with correct structure
- [ ] Anomaly detection (IQR) returns anomalies with median as expected value
- [ ] Anomaly detection (moving average) uses moving average for detection
- [ ] Volatility analysis returns rolling volatility metrics
- [ ] Volatility includes annualized volatility and returns
- [ ] Trend analysis (linear) returns slope, intercept, R², and direction
- [ ] Trend analysis (polynomial) returns polynomial degree
- [ ] Seasonal decomposition returns trend, seasonal, and residual components
- [ ] Forecasting (linear regression) returns forecasts with confidence intervals
- [ ] Forecasting (exponential smoothing) returns forecasts
- [ ] Forecasting (ARIMA) works if pmdarima is available
- [ ] Multiple analytics types can be requested together
- [ ] Error handling works for missing parameters
- [ ] Error handling works for invalid analytics types
- [ ] Error handling works when Spark is unavailable

## Troubleshooting

### Issue: "Spark service is not available"
**Solution:** Ensure Spark is running in the backend container. Check Docker logs:
```powershell
docker-compose logs backend
```

### Issue: ARIMA forecasting fails
**Solution:** Ensure `pmdarima` is installed in requirements.txt. If not available, the system falls back to linear regression.

### Issue: No anomalies detected
**Solution:** 
- Try lowering the `anomaly_threshold` (e.g., 2.0 instead of 3.0)
- Try different series with more variation
- Check that the series has enough data points

### Issue: Seasonal decomposition returns empty results
**Solution:** 
- Ensure `limit` is at least 2x the `seasonal_period`
- For monthly data, use `seasonal_period: 12` and `limit: 200` or more

### Issue: High response times
**Solution:**
- Use `use_cache: true` to leverage cached data
- Reduce `limit` for faster processing
- Request fewer analytics types at once

## Performance Notes

- **Anomaly Detection**: Fast (O(n) operations)
- **Volatility Analysis**: Fast (O(n) operations)
- **Trend Analysis**: Fast (O(n) operations)
- **Seasonal Decomposition**: Moderate (O(n) operations)
- **Forecasting (Linear/Exponential)**: Fast (O(n) operations)
- **Forecasting (ARIMA)**: Slow (requires model fitting, can take 10-30 seconds)

For best performance:
- Use caching (`use_cache: true`)
- Request one analytics type at a time for initial testing
- Use smaller `limit` values for faster responses

