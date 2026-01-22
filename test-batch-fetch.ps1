# Test script for Spark batch fetch endpoint
# Usage: .\test-batch-fetch.ps1

$uri = "http://localhost:8000/api/spark/batch-fetch"
$body = @{
    series_ids = @("GDP", "UNRATE")
    limit = 10
    sort_order = "desc"
} | ConvertTo-Json

Write-Host "Testing batch fetch endpoint..." -ForegroundColor Cyan
Write-Host "URI: $uri" -ForegroundColor Gray
Write-Host "Request body:" -ForegroundColor Gray
Write-Host ($body | ConvertFrom-Json | ConvertTo-Json -Depth 10) -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -ContentType "application/json" -Body $body
    
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Series count: $($response.series_count)" -ForegroundColor Green
    Write-Host "Total observations: $($response.total_observations)" -ForegroundColor Green
    $columnsStr = $response.columns -join ", "
    Write-Host "Columns: $columnsStr" -ForegroundColor Green
    Write-Host ""
    Write-Host "Series Info:" -ForegroundColor Cyan
    foreach ($info in $response.series_info) {
        $obsCount = $info.observation_count
        $seriesId = $info.series_id
        $title = $info.title
        $infoText = "  - $seriesId : $title - $obsCount observations"
        Write-Host $infoText -ForegroundColor Yellow
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
            Write-Host "Response body:" -ForegroundColor Red
            Write-Host $responseBody -ForegroundColor Red
        }
        catch {
            $readError = "Could not read response body"
            Write-Host $readError -ForegroundColor Red
        }
    }
    exit 1
}
