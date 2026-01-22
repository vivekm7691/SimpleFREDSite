# Test script for Spark cache functionality
# Usage: .\test-cache.ps1

$baseUrl = "http://localhost:8000"

Write-Host "=== Testing Spark Cache Functionality ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Get cache stats (should be empty initially)
Write-Host "Test 1: Get cache stats (initial state)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/stats" -Method GET
    Write-Host "Success! Cache stats:" -ForegroundColor Green
    Write-Host "  Total files: $($response.total_files)" -ForegroundColor Gray
    Write-Host "  Unique series: $($response.unique_series)" -ForegroundColor Gray
    Write-Host "  Total size: $($response.total_size_mb) MB" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: List cached series (should be empty initially)
Write-Host "Test 2: List cached series (initial state)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/list" -Method GET
    Write-Host "Success! Cached series count: $($response.total_count)" -ForegroundColor Green
    if ($response.total_count -gt 0) {
        foreach ($entry in $response.entries) {
            Write-Host "  - $($entry.series_id): $($entry.file_size) bytes" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Batch fetch with caching enabled (will create cache)
Write-Host "Test 3: Batch fetch with caching enabled (creates cache)" -ForegroundColor Yellow
$body = @{
    series_ids = @("GDP", "UNRATE")
    limit = 10
    sort_order = "desc"
    use_cache = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/batch-fetch" -Method POST -ContentType "application/json" -Body $body
    Write-Host "Success! Fetched $($response.series_count) series with $($response.total_observations) total observations" -ForegroundColor Green
    Write-Host "  Series:" -ForegroundColor Gray
    foreach ($info in $response.series_info) {
        Write-Host "    - $($info.series_id): $($info.observation_count) observations" -ForegroundColor Gray
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# Wait a moment for cache to be written
Start-Sleep -Seconds 2

# Test 4: Get cache stats (should show cached data)
Write-Host "Test 4: Get cache stats (after caching)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/stats" -Method GET
    Write-Host "Success! Cache stats:" -ForegroundColor Green
    Write-Host "  Total files: $($response.total_files)" -ForegroundColor Gray
    Write-Host "  Unique series: $($response.unique_series)" -ForegroundColor Gray
    Write-Host "  Total size: $($response.total_size_mb) MB" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: List cached series (should show cached entries)
Write-Host "Test 5: List cached series (after caching)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/list" -Method GET
    Write-Host "Success! Cached series count: $($response.total_count)" -ForegroundColor Green
    if ($response.total_count -gt 0) {
        foreach ($entry in $response.entries) {
            $sizeKB = [math]::Round($entry.file_size / 1024, 2)
            Write-Host "  - $($entry.series_id) (limit=$($entry.limit), sort=$($entry.sort_order)): $sizeKB KB" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Batch fetch again with caching (should use cache)
Write-Host "Test 6: Batch fetch again with caching (should use cache)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/batch-fetch" -Method POST -ContentType "application/json" -Body $body
    Write-Host "Success! Fetched $($response.series_count) series with $($response.total_observations) total observations" -ForegroundColor Green
    Write-Host "  (This should be faster as it uses cache)" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Batch fetch with caching disabled (should fetch from API)
Write-Host "Test 7: Batch fetch with caching disabled (fetches from API)" -ForegroundColor Yellow
$bodyNoCache = @{
    series_ids = @("GDP")
    limit = 10
    sort_order = "desc"
    use_cache = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/batch-fetch" -Method POST -ContentType "application/json" -Body $bodyNoCache
    Write-Host "Success! Fetched $($response.series_count) series (bypassed cache)" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 8: Clear cache for specific series
Write-Host "Test 8: Clear cache for specific series (GDP)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/GDP" -Method DELETE
    Write-Host "Success! Deleted $($response.deleted_count) cache file(s)" -ForegroundColor Green
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 9: Get cache stats after partial clear
Write-Host "Test 9: Get cache stats after partial clear" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/stats" -Method GET
    Write-Host "Success! Cache stats:" -ForegroundColor Green
    Write-Host "  Total files: $($response.total_files)" -ForegroundColor Gray
    Write-Host "  Unique series: $($response.unique_series)" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 10: Clear all cache
Write-Host "Test 10: Clear all cache" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/clear" -Method DELETE
    Write-Host "Success! Deleted $($response.deleted_count) cache file(s)" -ForegroundColor Green
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 11: Verify cache is empty
Write-Host "Test 11: Verify cache is empty" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/spark/cache/stats" -Method GET
    Write-Host "Success! Cache stats:" -ForegroundColor Green
    Write-Host "  Total files: $($response.total_files)" -ForegroundColor Gray
    Write-Host "  Unique series: $($response.unique_series)" -ForegroundColor Gray
    if ($response.total_files -eq 0) {
        Write-Host "  Cache is empty (as expected)" -ForegroundColor Green
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== Cache Testing Complete ===" -ForegroundColor Cyan

