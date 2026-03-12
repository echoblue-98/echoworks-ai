# ============================================================
# AION OS - LM Studio Sovereign Benchmark Quick Start
# ============================================================
# 
# USAGE:
#   .\benchmark_lmstudio.ps1           # Default 5 scenarios
#   .\benchmark_lmstudio.ps1 -Quick    # Quick 3 scenarios  
#   .\benchmark_lmstudio.ps1 -Full     # All 10 scenarios
#   .\benchmark_lmstudio.ps1 -Verbose  # Detailed output
#
# PREREQUISITES:
#   1. LM Studio running with model loaded
#   2. Server started (green status)
#   3. Python 3.8+ with requests module
# ============================================================

param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$Verbose,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Color($Text, $Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}

# Header
Write-Host ""
Write-Color "============================================================" Cyan
Write-Color "  AION OS - LM Studio Sovereign Inference Benchmark" Cyan
Write-Color "============================================================" Cyan
Write-Host ""

if ($Help) {
    Write-Color "USAGE:" Yellow
    Write-Host "  .\benchmark_lmstudio.ps1           # Default 5 scenarios"
    Write-Host "  .\benchmark_lmstudio.ps1 -Quick    # Quick 3 scenarios"
    Write-Host "  .\benchmark_lmstudio.ps1 -Full     # All 10 scenarios"
    Write-Host "  .\benchmark_lmstudio.ps1 -Verbose  # Show details"
    Write-Host ""
    Write-Color "PREREQUISITES:" Yellow
    Write-Host "  1. LM Studio running with model loaded"
    Write-Host "  2. Server started (green status indicator)"
    Write-Host "  3. Python 3.8+ with requests module"
    Write-Host ""
    Write-Color "GOAL:" Yellow
    Write-Host "  Achieve 85%+ accuracy for sovereign inference"
    Write-Host ""
    exit 0
}

# Check if LM Studio is running
Write-Color "Checking LM Studio connection..." Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:1234/v1/models" -TimeoutSec 3 -ErrorAction Stop
    $models = ($response.Content | ConvertFrom-Json).data
    if ($models.Count -gt 0) {
        Write-Color "  LM Studio connected: $($models[0].id)" Green
    } else {
        Write-Color "  LM Studio running but no model loaded!" Yellow
        Write-Host "  Load a model in LM Studio, then try again."
        exit 1
    }
} catch {
    Write-Color "  LM Studio not running!" Red
    Write-Host ""
    Write-Color "To get started:" Yellow
    Write-Host "  1. Open LM Studio"
    Write-Host "  2. Search for 'DeepSeek-V2-Lite' or 'Mixtral 8x7B'"
    Write-Host "  3. Download Q4_K_M or Q5_K_M quantization"
    Write-Host "  4. Load the model"
    Write-Host "  5. Click 'Start Server' (wait for green status)"
    Write-Host "  6. Run this script again"
    Write-Host ""
    exit 1
}

# Build args
$args = @()
if ($Quick) { $args += "--quick" }
if ($Full) { $args += "--scenarios=10" }
if ($Verbose) { $args += "--verbose" }

Write-Host ""

# Run benchmark
$scriptPath = Join-Path $PSScriptRoot "aionos\api\lmstudio_client.py"
if (Test-Path $scriptPath) {
    python $scriptPath @args
} else {
    Write-Color "Error: lmstudio_client.py not found at expected path" Red
    Write-Host "Expected: $scriptPath"
    exit 1
}

Write-Host ""
Write-Color "============================================================" Cyan
Write-Color "  Benchmark complete. Check results above." Cyan
Write-Color "============================================================" Cyan
Write-Host ""
