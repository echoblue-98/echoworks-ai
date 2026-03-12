# AION OS - Quick Start with Your API Key

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     AION OS - Claude API Integration Setup              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "Current Status:" -ForegroundColor Green
Write-Host ""

# Load .env and check API key
$envContent = Get-Content ".env" -Raw
if ($envContent -match "ANTHROPIC_API_KEY=(.+)") {
    $apiKey = $matches[1].Trim()
    
    if ($apiKey -eq "your-key-here" -or $apiKey -eq "your_anthropic_key_here") {
        Write-Host "  ⚠  API Key: NOT SET" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To activate Claude API:" -ForegroundColor Cyan
        Write-Host "  1. Open .env file: notepad .env" -ForegroundColor White
        Write-Host "  2. Replace 'your-key-here' with your actual Anthropic API key" -ForegroundColor White
        Write-Host "  3. Save and close" -ForegroundColor White
        Write-Host ""
        Write-Host "Get your API key from: https://console.anthropic.com/" -ForegroundColor Gray
    } else {
        Write-Host "  ✓  API Key: CONFIGURED" -ForegroundColor Green
        Write-Host "  ✓  Model: claude-3-5-sonnet-20241022" -ForegroundColor Green
        Write-Host ""
        Write-Host "Testing connection..." -ForegroundColor Yellow
        python test_api_integration.py
    }
} else {
    Write-Host "  ⚠  .env file needs ANTHROPIC_API_KEY" -ForegroundColor Yellow
}

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Next Steps                                           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Once API key is set:" -ForegroundColor Green
Write-Host ""
Write-Host "  Test integration:" -ForegroundColor White
Write-Host "    python test_api_integration.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run legal analysis:" -ForegroundColor White
Write-Host "    python -m aionos.api.cli analyze-legal examples/sample_brief.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run security scan:" -ForegroundColor White
Write-Host "    python -m aionos.api.cli red-team examples/sample_infrastructure.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "  Check usage stats:" -ForegroundColor White
Write-Host "    python -m aionos.api.cli stats" -ForegroundColor Gray
Write-Host ""
Write-Host "  Attorney departure demo:" -ForegroundColor White
Write-Host "    python demo_attorney_departure.py" -ForegroundColor Gray
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Green
Write-Host "  • API_READY.md - Quick overview" -ForegroundColor Gray
Write-Host "  • API_INTEGRATION_PLAN.md - Full strategy" -ForegroundColor Gray
Write-Host "  • CLAUDE_API_SETUP.md - Detailed setup" -ForegroundColor Gray
Write-Host ""
