param(
    [string]$Profile = "fast",
    [string]$Subdir = "xiaohongshu-cli"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-SmokeStep {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string[]]$Args
    )

    Write-Host ""
    Write-Host "=== $Title ==="
    $fullArgs = @()
    if ($Profile) {
        $fullArgs += @("-p", $Profile)
    }
    $fullArgs += $Args

    Write-Host ("codex " + ($fullArgs -join " "))

    & codex @fullArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke check failed: $Title (exit=$LASTEXITCODE)"
    }
}

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw "codex command not found in PATH."
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$subdirPath = Join-Path $root $Subdir
if (-not (Test-Path $subdirPath)) {
    throw "Subdir not found: $Subdir"
}

Push-Location $root
try {
    Invoke-SmokeStep -Title "Root Instruction Summary" -Args @(
        "exec",
        "-c", "approval_policy=""never""",
        "Summarize the current instructions."
    )

    Invoke-SmokeStep -Title "Subdir Active Instruction Files" -Args @(
        "exec",
        "-C", $Subdir,
        "-c", "approval_policy=""never""",
        "Show which instruction files are active."
    )
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "All codex smoke checks passed."
