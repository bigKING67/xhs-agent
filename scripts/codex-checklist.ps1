param(
    [ValidateSet("all", "cli", "agent")]
    [string]$Target = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Command
    )

    Write-Host ""
    Write-Host "=== $Title ==="
    Write-Host $Command
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Title (exit=$LASTEXITCODE)"
    }
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $root
try {
    if ($Target -in @("all", "cli")) {
        Push-Location "xiaohongshu-cli"
        try {
            Invoke-Step -Title "CLI Lint" -Command "uv run ruff check ."
            Invoke-Step -Title "CLI Type Check" -Command "uv run mypy xhs_cli/"
            Invoke-Step -Title "CLI Tests (not smoke)" -Command "uv run pytest tests/ -v -m ""not smoke"""
        }
        finally {
            Pop-Location
        }
    }

    if ($Target -in @("all", "agent")) {
        Push-Location "xhs-agent"
        try {
            Invoke-Step -Title "Agent Tests" -Command "pytest -v"
        }
        finally {
            Pop-Location
        }
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "All checklist steps passed."
