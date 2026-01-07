# ============================================================================
# Cleanup API Server Processes - Veriply
# ============================================================================
# This script stops all running API server processes to free up database
# connections and prevent the "too many connections" error.

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "Veriply API Server Cleanup" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# Check for uvicorn processes
$uvicornProcesses = Get-Process uvicorn -ErrorAction SilentlyContinue
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*Veriply*" -or $_.MainWindowTitle -like "*Veriply*"
}

if ($uvicornProcesses.Count -eq 0 -and $pythonProcesses.Count -eq 0) {
    Write-Host "✓ No API server processes found running." -ForegroundColor Green
    Write-Host "`nYou can now start the API server safely." -ForegroundColor Green
    exit 0
}

Write-Host "Found running processes:" -ForegroundColor Yellow

if ($uvicornProcesses) {
    Write-Host "`nUvicorn Processes:" -ForegroundColor Yellow
    $uvicornProcesses | Format-Table Id, ProcessName, StartTime, @{
        Name='Memory(MB)'; Expression={[math]::Round($_.WorkingSet64/1MB,2)}
    } -AutoSize
}

if ($pythonProcesses) {
    Write-Host "`nPython Processes (Veriply-related):" -ForegroundColor Yellow
    $pythonProcesses | Format-Table Id, ProcessName, StartTime, @{
        Name='Memory(MB)'; Expression={[math]::Round($_.WorkingSet64/1MB,2)}
    } -AutoSize
}

# Ask for confirmation
$confirmation = Read-Host "`nDo you want to stop all these processes? (Y/N)"

if ($confirmation -eq 'Y' -or $confirmation -eq 'y') {
    Write-Host "`nStopping processes..." -ForegroundColor Yellow
    
    # Stop uvicorn
    if ($uvicornProcesses) {
        $uvicornProcesses | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force
                Write-Host "  ✓ Stopped uvicorn (PID: $($_.Id))" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Failed to stop uvicorn (PID: $($_.Id)): $_" -ForegroundColor Red
            }
        }
    }
    
    # Stop Python processes
    if ($pythonProcesses) {
        $pythonProcesses | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force
                Write-Host "  ✓ Stopped python (PID: $($_.Id))" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Failed to stop python (PID: $($_.Id)): $_" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "`n✓ Cleanup complete!" -ForegroundColor Green
    Write-Host "`nDatabase connections should now be freed." -ForegroundColor Green
    Write-Host "You can start the API server with:" -ForegroundColor Cyan
    Write-Host "  cd apps/api" -ForegroundColor White
    Write-Host "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    
} else {
    Write-Host "`nCleanup cancelled." -ForegroundColor Yellow
}

Write-Host ""
