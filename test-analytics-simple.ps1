# Simple test script for analytics endpoint
# Usage: .\test-analytics-simple.ps1

$uri = "http://localhost:8000/api/spark/analytics"
$headers = @{"Content-Type" = "application/json"}

# Test 1: Basic Statistics
Write-Host "Testing Basic Statistics..." -ForegroundColor Cyan
$body = @{
    series_ids = @("GDP")
    analytics_types = @("statistics")
    limit = 50
    sort_order = "desc"
    use_cache = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
    
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Series count: $($response.series_count)" -ForegroundColor Green
    Write-Host ""
    
    if ($response.statistics) {
        Write-Host "Statistics:" -ForegroundColor Cyan
        foreach ($stat in $response.statistics) {
            Write-Host "  Series: $($stat.series_id)" -ForegroundColor Yellow
            Write-Host "    Mean: $($stat.mean)" -ForegroundColor White
            Write-Host "    Median: $($stat.median)" -ForegroundColor White
            Write-Host "    Std Dev: $($stat.std)" -ForegroundColor White
            $minMax = "    Min: $($stat.min) | Max: $($stat.max)"
            Write-Host $minMax -ForegroundColor White
            $countSum = "    Count: $($stat.count) | Sum: $($stat.sum)"
            Write-Host $countSum -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "Full Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
}
catch {
    $errorMsg = $_.Exception.Message
    Write-Host "Error: $errorMsg" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $details = $_.ErrorDetails.Message
        Write-Host "Details: $details" -ForegroundColor Red
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
            $readError = "Could not read response body"
            Write-Host $readError -ForegroundColor Red
        }
    }
    exit 1
}
