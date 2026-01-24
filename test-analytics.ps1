# Test script for Spark analytics endpoint
# Usage: .\test-analytics.ps1

$baseUrl = "http://localhost:8000/api/spark"
$headers = @{"Content-Type" = "application/json"}

function Invoke-AnalyticsCall {
    param (
        [string]$TestName,
        [hashtable]$RequestBody,
        [string]$SuccessMessage = "Success"
    )
    
    Write-Host "`n### $TestName ###" -ForegroundColor Yellow
    Write-Host "Request:" -ForegroundColor Cyan
    $RequestBody | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Gray
    Write-Host ""
    
    try {
        $body = $RequestBody | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "$baseUrl/analytics" -Method POST -Headers $headers -Body $body
        
        Write-Host "$SuccessMessage ✓" -ForegroundColor Green
        Write-Host "Series count: $($response.series_count)" -ForegroundColor Green
        Write-Host ""
        
        # Display results based on what was requested
        if ($response.statistics) {
            Write-Host "Statistics:" -ForegroundColor Cyan
            foreach ($stat in $response.statistics) {
                Write-Host "  Series: $($stat.series_id)" -ForegroundColor Yellow
                Write-Host "    Mean: $($stat.mean)" -ForegroundColor White
                Write-Host "    Median: $($stat.median)" -ForegroundColor White
                Write-Host "    Std Dev: $($stat.std)" -ForegroundColor White
                Write-Host "    Min: $($stat.min) | Max: $($stat.max)" -ForegroundColor White
                Write-Host "    Count: $($stat.count) | Sum: $($stat.sum)" -ForegroundColor White
            }
        }
        
        if ($response.growth_rates) {
            Write-Host "Growth Rates:" -ForegroundColor Cyan
            $growthCount = $response.growth_rates.Count
            Write-Host "  Total growth rate calculations: $growthCount" -ForegroundColor Yellow
            if ($growthCount -gt 0 -and $growthCount -le 5) {
                foreach ($growth in $response.growth_rates) {
                    Write-Host "    $($growth.date): $($growth.series_id) - Growth: $($growth.growth_rate)" -ForegroundColor White
                }
            } elseif ($growthCount -gt 5) {
                Write-Host "    (Showing first 3 of $growthCount)" -ForegroundColor Gray
                for ($i = 0; $i -lt 3; $i++) {
                    $growth = $response.growth_rates[$i]
                    Write-Host "    $($growth.date): $($growth.series_id) - Growth: $($growth.growth_rate)" -ForegroundColor White
                }
            }
        }
        
        if ($response.correlations) {
            Write-Host "Correlations:" -ForegroundColor Cyan
            foreach ($corr in $response.correlations) {
                Write-Host "  $($corr.series_id_1) <-> $($corr.series_id_2): $($corr.correlation)" -ForegroundColor Yellow
            }
        }
        
        if ($response.moving_averages) {
            Write-Host "Moving Averages:" -ForegroundColor Cyan
            $maCount = $response.moving_averages.Count
            Write-Host "  Total MA calculations: $maCount" -ForegroundColor Yellow
            if ($maCount -gt 0 -and $maCount -le 5) {
                foreach ($ma in $response.moving_averages) {
                    Write-Host "    $($ma.date): $($ma.series_id) - Value: $($ma.value), MA: $($ma.moving_average) (Type: $($ma.moving_average_type), Window: $($ma.window_size))" -ForegroundColor White
                }
            } elseif ($maCount -gt 5) {
                Write-Host "    (Showing first 3 of $maCount)" -ForegroundColor Gray
                for ($i = 0; $i -lt 3; $i++) {
                    $ma = $response.moving_averages[$i]
                    Write-Host "    $($ma.date): $($ma.series_id) - Value: $($ma.value), MA: $($ma.moving_average)" -ForegroundColor White
                }
            }
        }
        
        if ($response.time_aggregations) {
            Write-Host "Time Aggregations:" -ForegroundColor Cyan
            foreach ($agg in $response.time_aggregations) {
                Write-Host "  $($agg.series_id) - Period: $($agg.period), Value: $($agg.aggregated_value) ($($agg.aggregation_function), $($agg.observation_count) obs)" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        return $response
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $responseBody = $reader.ReadToEnd()
                $reader.Close()
                $stream.Close()
                Write-Host "Response body: $responseBody" -ForegroundColor Red
            }
            catch {
                Write-Host "Could not read response body" -ForegroundColor Red
            }
        }
        return $null
    }
}

# Test 1: Basic Statistics
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "Testing Analytics Endpoint" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

Invoke-AnalyticsCall -TestName "Test 1: Basic Statistics" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("statistics")
    limit = 50
    sort_order = "desc"
    use_cache = $true
}

# Test 2: Growth Rates
Invoke-AnalyticsCall -TestName "Test 2: Growth Rates" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("growth_rates")
    limit = 50
    sort_order = "desc"
    use_cache = $true
}

# Test 3: Correlations (requires at least 2 series)
Invoke-AnalyticsCall -TestName "Test 3: Correlations" -RequestBody @{
    series_ids = @("GDP", "UNRATE")
    analytics_types = @("correlations")
    limit = 50
    sort_order = "desc"
    use_cache = $true
}

# Test 4: Simple Moving Average
Invoke-AnalyticsCall -TestName "Test 4: Simple Moving Average (SMA)" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("moving_averages")
    limit = 50
    sort_order = "desc"
    use_cache = $true
    moving_average_window = 7
    moving_average_type = "sma"
}

# Test 5: Exponential Moving Average
Invoke-AnalyticsCall -TestName "Test 5: Exponential Moving Average (EMA)" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("moving_averages")
    limit = 50
    sort_order = "desc"
    use_cache = $true
    moving_average_window = 7
    moving_average_type = "ema"
}

# Test 6: Time Aggregations - Monthly Mean
Invoke-AnalyticsCall -TestName "Test 6: Time Aggregations - Monthly Mean" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("time_aggregations")
    limit = 100
    sort_order = "desc"
    use_cache = $true
    time_aggregation_period = "monthly"
    time_aggregation_function = "mean"
}

# Test 7: Time Aggregations - Quarterly Sum
Invoke-AnalyticsCall -TestName "Test 7: Time Aggregations - Quarterly Sum" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("time_aggregations")
    limit = 100
    sort_order = "desc"
    use_cache = $true
    time_aggregation_period = "quarterly"
    time_aggregation_function = "sum"
}

# Test 8: Multiple Analytics Types
Invoke-AnalyticsCall -TestName "Test 8: Multiple Analytics Types" -RequestBody @{
    series_ids = @("GDP", "UNRATE")
    analytics_types = @("statistics", "correlations")
    limit = 50
    sort_order = "desc"
    use_cache = $true
}

# Test 9: All Analytics Types (comprehensive)
Invoke-AnalyticsCall -TestName "Test 9: All Analytics Types" -RequestBody @{
    series_ids = @("GDP")
    analytics_types = @("statistics", "growth_rates", "moving_averages")
    limit = 50
    sort_order = "desc"
    use_cache = $true
    moving_average_window = 7
    moving_average_type = "sma"
}

# Test 10: Error Handling - Missing Required Parameters
Write-Host "`n### Test 10: Error Handling - Missing Moving Average Parameters ###" -ForegroundColor Yellow
try {
    $errorBody = @{
        series_ids = @("GDP")
        analytics_types = @("moving_averages")
        limit = 50
    } | ConvertTo-Json -Depth 10
    
    Invoke-RestMethod -Uri "$baseUrl/analytics" -Method POST -Headers $headers -Body $errorBody
    Write-Host "ERROR: Should have failed but didn't!" -ForegroundColor Red
}
catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "Expected error received ✓" -ForegroundColor Green
        Write-Host "Status: 400 Bad Request" -ForegroundColor Green
    }
    else {
        Write-Host "Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "Testing Complete!" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

