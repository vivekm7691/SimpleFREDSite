# Test script for Increment 6: Advanced Analytics
# Tests the /api/spark/advanced-analytics endpoint

$baseUrl = "http://localhost:8000"
$endpoint = "$baseUrl/api/spark/advanced-analytics"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Advanced Analytics Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Anomaly Detection (Z-Score)
Write-Host "Test 1: Anomaly Detection (Z-Score Method)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("anomalies")
        limit = 100
        sort_order = "desc"
        use_cache = $true
        anomaly_method = "z_score"
        anomaly_threshold = 3.0
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    Write-Host "  Series Count: $($response.series_count)" -ForegroundColor Gray
    if ($response.anomalies) {
        Write-Host "  Anomalies Found: $($response.anomalies.Count)" -ForegroundColor Gray
        if ($response.anomalies.Count -gt 0) {
            $firstAnomaly = $response.anomalies[0]
            Write-Host "  Sample Anomaly:" -ForegroundColor Gray
            Write-Host "    Series: $($firstAnomaly.series_id)" -ForegroundColor Gray
            Write-Host "    Date: $($firstAnomaly.date)" -ForegroundColor Gray
            Write-Host "    Value: $($firstAnomaly.value)" -ForegroundColor Gray
            Write-Host "    Deviation: $($firstAnomaly.deviation)" -ForegroundColor Gray
            Write-Host "    Severity: $($firstAnomaly.severity)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Anomaly Detection (IQR)
Write-Host "Test 2: Anomaly Detection (IQR Method)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("UNRATE")
        analytics_types = @("anomalies")
        limit = 100
        anomaly_method = "iqr"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.anomalies) {
        Write-Host "  Anomalies Found: $($response.anomalies.Count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Volatility Analysis
Write-Host "Test 3: Volatility Analysis" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("volatility")
        limit = 100
        volatility_window = 30
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.volatility) {
        Write-Host "  Volatility Data Points: $($response.volatility.Count)" -ForegroundColor Gray
        if ($response.volatility.Count -gt 0) {
            $firstVol = $response.volatility[0]
            Write-Host "  Sample Volatility:" -ForegroundColor Gray
            Write-Host "    Date: $($firstVol.date)" -ForegroundColor Gray
            Write-Host "    Volatility: $($firstVol.volatility)" -ForegroundColor Gray
            Write-Host "    Annualized: $($firstVol.annualized_volatility)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Trend Analysis (Linear)
Write-Host "Test 4: Trend Analysis (Linear)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("trends")
        limit = 100
        trend_type = "linear"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.trends) {
        Write-Host "  Trends Analyzed: $($response.trends.Count)" -ForegroundColor Gray
        if ($response.trends.Count -gt 0) {
            $trend = $response.trends[0]
            Write-Host "  Trend Results:" -ForegroundColor Gray
            Write-Host "    Type: $($trend.trend_type)" -ForegroundColor Gray
            Write-Host "    Direction: $($trend.direction)" -ForegroundColor Gray
            Write-Host "    R-squared: $($trend.r_squared)" -ForegroundColor Gray
            Write-Host "    Slope: $($trend.slope)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Seasonal Decomposition
Write-Host "Test 5: Seasonal Decomposition (Additive)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("seasonal_decomposition")
        limit = 200
        decomposition_type = "additive"
        seasonal_period = 12
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.seasonal_decompositions) {
        Write-Host "  Decomposition Points: $($response.seasonal_decompositions.Count)" -ForegroundColor Gray
        if ($response.seasonal_decompositions.Count -gt 0) {
            $decomp = $response.seasonal_decompositions[0]
            Write-Host "  Sample Decomposition:" -ForegroundColor Gray
            Write-Host "    Date: $($decomp.date)" -ForegroundColor Gray
            Write-Host "    Actual: $($decomp.actual_value)" -ForegroundColor Gray
            Write-Host "    Trend: $($decomp.trend_component)" -ForegroundColor Gray
            Write-Host "    Seasonal: $($decomp.seasonal_component)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Forecasting (Linear Regression)
Write-Host "Test 6: Forecasting (Linear Regression)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("forecasts")
        limit = 100
        forecast_horizon = 12
        forecast_method = "linear_regression"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.forecasts) {
        Write-Host "  Forecasts Generated: $($response.forecasts.Count)" -ForegroundColor Gray
        if ($response.forecasts.Count -gt 0) {
            $forecast = $response.forecasts[0]
            Write-Host "  Sample Forecast:" -ForegroundColor Gray
            Write-Host "    Date: $($forecast.date)" -ForegroundColor Gray
            Write-Host "    Forecasted Value: $($forecast.forecasted_value)" -ForegroundColor Gray
            Write-Host "    Method: $($forecast.forecast_method)" -ForegroundColor Gray
            if ($forecast.lower_bound) {
                Write-Host "    Confidence Interval: [$($forecast.lower_bound), $($forecast.upper_bound)]" -ForegroundColor Gray
            }
        }
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Forecasting (Exponential Smoothing)
Write-Host "Test 7: Forecasting (Exponential Smoothing)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("UNRATE")
        analytics_types = @("forecasts")
        limit = 100
        forecast_horizon = 6
        forecast_method = "exponential_smoothing"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    if ($response.forecasts) {
        Write-Host "  Forecasts Generated: $($response.forecasts.Count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 8: Multiple Analytics Types
Write-Host "Test 8: Multiple Analytics Types" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP", "UNRATE")
        analytics_types = @("anomalies", "volatility", "trends")
        limit = 100
        anomaly_method = "z_score"
        trend_type = "linear"
        volatility_window = 30
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    
    Write-Host "  Success!" -ForegroundColor Green
    Write-Host "  Series Count: $($response.series_count)" -ForegroundColor Gray
    Write-Host "  Anomalies: $($response.anomalies.Count)" -ForegroundColor Gray
    Write-Host "  Volatility Points: $($response.volatility.Count)" -ForegroundColor Gray
    Write-Host "  Trends: $($response.trends.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 9: Error Handling - Missing Required Parameters
Write-Host "Test 9: Error Handling (Missing Parameters)" -ForegroundColor Yellow
try {
    $body = @{
        series_ids = @("GDP")
        analytics_types = @("forecasts")
        limit = 100
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    Write-Host "  Unexpected Success (should have failed)" -ForegroundColor Red
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 400) {
        Write-Host "  Expected Error (400): Missing required parameters" -ForegroundColor Green
    } else {
        Write-Host "  Unexpected Error: $statusCode" -ForegroundColor Red
    }
}
Write-Host ""

# Test 10: Health Check
Write-Host "Test 10: Spark Health Check" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/api/spark/health" -Method GET
    Write-Host "  Spark Status: $($healthResponse.status)" -ForegroundColor Green
    if ($healthResponse.status -eq "available") {
        Write-Host "  Spark Version: $($healthResponse.spark_version)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

