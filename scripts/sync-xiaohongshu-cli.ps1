param(
    [string]$SubmodulePath = "xiaohongshu-cli",
    [string]$Branch = "main",
    [switch]$AutoStash,
    [switch]$AllowDirty,
    [switch]$SkipChecks,
    [switch]$SkipAnalysis,
    [string]$AnalysisOutputFile = "",
    [switch]$PushPointer,
    [string]$PushRemote = "origin",
    [string]$PushBranch = "",
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

function Get-GitSingleLine {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string[]]$Args
    )
    $output = & git -C $RepoPath @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in ${RepoPath}: git $($Args -join ' ')"
    }
    if ($null -eq $output) {
        return ""
    }
    return ($output | Select-Object -First 1).ToString().Trim()
}

function Test-GitRefExists {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string]$Ref
    )
    & git -C $RepoPath rev-parse --verify --quiet $Ref *> $null
    return ($LASTEXITCODE -eq 0)
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
$analysisScript = Join-Path $root "scripts/analyze-xiaohongshu-cli-update.ps1"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git command not found in PATH."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv command not found in PATH."
}

if (-not (Test-Path $submodule)) {
    throw "Submodule path not found: $submodule"
}
if (-not $SkipAnalysis -and -not (Test-Path $analysisScript)) {
    throw "Analysis script not found: $analysisScript"
}
if ($PushPointer -and $NoCommitPointer) {
    throw "-PushPointer cannot be used with -NoCommitPointer."
}

$currentBranch = Get-GitSingleLine -RepoPath $root -Args @("branch", "--show-current")
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
    throw "Current branch is detached; cannot determine push branch."
}
if ([string]::IsNullOrWhiteSpace($PushBranch)) {
    $candidate = $currentBranch
    if (Test-GitRefExists -RepoPath $root -Ref "$PushRemote/$candidate") {
        $PushBranch = $candidate
    }
    elseif (Test-GitRefExists -RepoPath $root -Ref "$PushRemote/main") {
        $PushBranch = "main"
    }
    else {
        throw (
            "Cannot infer remote push branch. Tried $PushRemote/$candidate and $PushRemote/main. " +
            "Please set -PushBranch explicitly."
        )
    }
}
elseif (-not (Test-GitRefExists -RepoPath $root -Ref "$PushRemote/$PushBranch")) {
    throw "Remote ref not found: $PushRemote/$PushBranch. Please set a valid -PushBranch."
}

Invoke-Git -RepoPath $root -Args @("fetch", $PushRemote, "--prune")
$preAheadBehind = Get-GitSingleLine -RepoPath $root -Args @("rev-list", "--left-right", "--count", "HEAD...$PushRemote/$PushBranch")
$preAhead = 0
if (-not [string]::IsNullOrWhiteSpace($preAheadBehind)) {
    $parts = $preAheadBehind -split "\s+"
    if ($parts.Count -ge 1) {
        $preAhead = [int]$parts[0]
    }
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
$pointerCommitted = $false

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
    $pointerCommitted = $true
}

if ($PushPointer) {
    if (-not $pointerCommitted) {
        Write-Host ""
        Write-Host "=== Push Pointer ==="
        Write-Host "Skip push: submodule pointer unchanged, no new commit."
    }
    elseif ($preAhead -gt 0) {
        throw (
            "Auto push aborted: root branch already had $preAhead local commit(s) ahead of " +
            "$PushRemote/$PushBranch before this sync. Push manually to avoid unintended commits."
        )
    }
    else {
        Invoke-Step -Title "Push Pointer Commit" -Action {
            Invoke-Git -RepoPath $root -Args @("push", $PushRemote, "HEAD:$PushBranch")
        }
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

if (-not $SkipAnalysis) {
    Invoke-Step -Title "Analyze Upstream Impact" -Action {
        $args = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $analysisScript,
            "-SubmodulePath", $SubmodulePath,
            "-Branch", $Branch,
            "-BaseRef", $oldHead,
            "-TargetRef", $newHead
        )
        if (-not [string]::IsNullOrWhiteSpace($AnalysisOutputFile)) {
            $args += @("-OutputFile", $AnalysisOutputFile)
        }
        & powershell @args
        if ($LASTEXITCODE -ne 0) {
            throw "Upstream impact analysis failed."
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
Write-Host "Analysis executed: $(-not $SkipAnalysis)"
Write-Host "Pointer committed: $pointerCommitted"
Write-Host "Push requested: $PushPointer"
