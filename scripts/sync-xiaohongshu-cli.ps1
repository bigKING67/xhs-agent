param(
    [string]$SubmodulePath = "xiaohongshu-cli",
    [string]$Branch = "main",
    [switch]$AutoStash,
    [switch]$AllowDirty,
    [switch]$SkipChecks,
    [switch]$NoCommitPointer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string[]]$Args
    )
    & git -C $RepoPath @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in ${RepoPath}: git $($Args -join ' ')"
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host ""
    Write-Host "=== $Title ==="
    & $Action
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$submodule = Join-Path $root $SubmodulePath
$xhsAgent = Join-Path $root "xhs-agent"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git command not found in PATH."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv command not found in PATH."
}

if (-not (Test-Path $submodule)) {
    throw "Submodule path not found: $submodule"
}

Invoke-Step -Title "Init Submodule Mapping" -Action {
    Invoke-Git -RepoPath $root -Args @("submodule", "update", "--init", "--recursive", "--", $SubmodulePath)
}

$oldHead = (& git -C $submodule rev-parse --short HEAD).Trim()
$dirtyOutput = (& git -C $submodule status --porcelain)
$isDirty = -not [string]::IsNullOrWhiteSpace(($dirtyOutput -join ""))
$didStash = $false
$stashName = ""

if ($isDirty -and -not $AutoStash -and -not $AllowDirty) {
    throw (
        "Submodule has local changes. Re-run with -AutoStash to stash/apply automatically, " +
        "or with -AllowDirty if you intentionally keep local changes during update."
    )
}

if ($isDirty -and $AutoStash) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stashName = "sync-before-upstream-$stamp"
    Invoke-Step -Title "Auto Stash Local Changes" -Action {
        Invoke-Git -RepoPath $submodule -Args @("stash", "push", "-u", "-m", $stashName)
    }
    $didStash = $true
}

Invoke-Step -Title "Fetch + Fast-Forward Upstream" -Action {
    Invoke-Git -RepoPath $submodule -Args @("fetch", "origin", "--prune")
    Invoke-Git -RepoPath $submodule -Args @("checkout", $Branch)
    Invoke-Git -RepoPath $submodule -Args @("pull", "--ff-only", "origin", $Branch)
}

if ($didStash) {
    try {
        Invoke-Step -Title "Re-apply Stashed Local Changes" -Action {
            Invoke-Git -RepoPath $submodule -Args @("stash", "apply", "stash@{0}")
        }
    }
    catch {
        throw (
            "Failed to apply stash automatically. Resolve conflicts in submodule manually. " +
            "Recent stash: $stashName"
        )
    }
}

$newHead = (& git -C $submodule rev-parse --short HEAD).Trim()

if (-not $NoCommitPointer -and $oldHead -ne $newHead) {
    Invoke-Step -Title "Commit Submodule Pointer Bump" -Action {
        Invoke-Git -RepoPath $root -Args @("add", "--", $SubmodulePath)
        Invoke-Git -RepoPath $root -Args @(
            "commit",
            "-m",
            "chore: bump $SubmodulePath submodule to origin/$Branch@$newHead",
            "--",
            $SubmodulePath
        )
    }
}

if (-not $SkipChecks) {
    Invoke-Step -Title "Validate xiaohongshu-cli" -Action {
        Push-Location $submodule
        try {
            uv sync
            $env:PYTHONUTF8 = "1"
            uv run xhs --help | Out-Null
        }
        finally {
            Pop-Location
        }
    }

    Invoke-Step -Title "Validate xhs-agent" -Action {
        Push-Location $xhsAgent
        try {
            uv sync
            uv run pytest -v
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "Done."
Write-Host "Submodule: $SubmodulePath"
Write-Host "Old HEAD: $oldHead"
Write-Host "New HEAD: $newHead"
Write-Host "Dirty before sync: $isDirty"
Write-Host "AutoStash used: $didStash"
