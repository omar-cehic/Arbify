Write-Host "========================================" -ForegroundColor Green
Write-Host "     ARBITRAGE DEPLOYMENT SCRIPT" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Set location
Set-Location "C:\arbtitrage_betting"
Write-Host "✅ Set location to project directory" -ForegroundColor Green

# Set git pager
$env:GIT_PAGER = ""
Write-Host "✅ Set git pager configuration" -ForegroundColor Green

# Build frontend
Write-Host ""
Write-Host "🔧 Building frontend..." -ForegroundColor Yellow
Set-Location "frontend"
try {
    npm run build
    Write-Host "✅ Frontend built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Frontend build failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Set-Location ".."

# Git operations
Write-Host ""
Write-Host "📝 Staging changes..." -ForegroundColor Yellow
git add .
Write-Host "✅ Changes staged" -ForegroundColor Green

Write-Host ""
Write-Host "💾 Committing fixes..." -ForegroundColor Yellow
git commit -m "🎯 FIXES: Remove profit limit + Add debug panel + Cache debugging"
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ WARNING: Commit failed (might be nothing to commit)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Deploying to live site..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Push failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "📋 Look for the RED DEBUG PANEL at the top" -ForegroundColor Cyan
Write-Host "   of the arbitrage page in 2-3 minutes" -ForegroundColor Cyan
Write-Host "🔍 It will show cache status and profits" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
