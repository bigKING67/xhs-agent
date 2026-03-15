param(
    [string]$SubmodulePath = "xiaohongshu-cli",
    [string]$Branch = "main",
    [string]$BaseRef = "",
    [string]$TargetRef = "origin/main",
    [string]$OutputFile = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-GitOutput {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string[]]$Args
    )
    $output = & git -C $RepoPath @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in ${RepoPath}: git $($Args -join ' ')"
    }
    return $output
}

function Is-MatchAny {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns
    )
    foreach ($pattern in $Patterns) {
        if ($Path -like $pattern) {
            return $true
        }
    }
    return $false
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$submodule = Join-Path $root $SubmodulePath

if (-not (Test-Path $submodule)) {
    throw "Submodule path not found: $submodule"
}

Invoke-GitOutput -RepoPath $root -Args @("submodule", "update", "--init", "--recursive", "--", $SubmodulePath) | Out-Null
Invoke-GitOutput -RepoPath $submodule -Args @("fetch", "origin", "--prune") | Out-Null

$baseCommit = ""
if ([string]::IsNullOrWhiteSpace($BaseRef)) {
    $treeLine = (Invoke-GitOutput -RepoPath $root -Args @("ls-tree", "HEAD", "--", $SubmodulePath) | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($treeLine)) {
        throw "Cannot resolve submodule pointer from root HEAD for path: $SubmodulePath"
    }
    $parts = ($treeLine -split "\s+")
    if ($parts.Count -lt 3) {
        throw "Unexpected ls-tree output: $treeLine"
    }
    $baseCommit = $parts[2]
}
else {
    $baseCommit = (Invoke-GitOutput -RepoPath $submodule -Args @("rev-parse", "--verify", $BaseRef) | Select-Object -First 1).Trim()
}

$targetCommit = (Invoke-GitOutput -RepoPath $submodule -Args @("rev-parse", "--verify", $TargetRef) | Select-Object -First 1).Trim()

$range = "$baseCommit..$targetCommit"
$commitLines = @(Invoke-GitOutput -RepoPath $submodule -Args @("log", "--oneline", $range))
$fileLines = @(Invoke-GitOutput -RepoPath $submodule -Args @("diff", "--name-only", $range))

$commits = @($commitLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$files = @($fileLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

$docsPatterns = @("*.md", "docs/*")
$ciPatterns = @(".github/*")
$depPatterns = @("pyproject.toml", "uv.lock", "requirements*.txt")
$coreApiPaths = @(
    "xhs_cli/client.py",
    "xhs_cli/client_mixins.py",
    "xhs_cli/commands/reading.py"
)
$schemaPaths = @(
    "SCHEMA.md",
    "xhs_cli/formatter.py",
    "xhs_cli/formatter_normalizers.py",
    "xhs_cli/formatter_utils.py",
    "xhs_cli/commands/_common.py"
)

$changedDocs = New-Object System.Collections.Generic.List[string]
$changedCi = New-Object System.Collections.Generic.List[string]
$changedDeps = New-Object System.Collections.Generic.List[string]
$changedCore = New-Object System.Collections.Generic.List[string]
$changedSchema = New-Object System.Collections.Generic.List[string]
$changedOtherCode = New-Object System.Collections.Generic.List[string]

foreach ($file in $files) {
    if ($coreApiPaths -contains $file) {
        $changedCore.Add($file) | Out-Null
        continue
    }
    if ($schemaPaths -contains $file) {
        $changedSchema.Add($file) | Out-Null
        continue
    }
    if (Is-MatchAny -Path $file -Patterns $depPatterns) {
        $changedDeps.Add($file) | Out-Null
        continue
    }
    if (Is-MatchAny -Path $file -Patterns $ciPatterns) {
        $changedCi.Add($file) | Out-Null
        continue
    }
    if (Is-MatchAny -Path $file -Patterns $docsPatterns) {
        $changedDocs.Add($file) | Out-Null
        continue
    }
    if ($file -like "xhs_cli/*") {
        $changedOtherCode.Add($file) | Out-Null
        continue
    }
    $changedOtherCode.Add($file) | Out-Null
}

$riskLevel = "NONE"
$needsAgentPatch = $false
$reason = "No upstream changes in selected range."

if ($files.Count -gt 0) {
    if ($changedCore.Count -gt 0 -or $changedSchema.Count -gt 0) {
        $riskLevel = "HIGH"
        $needsAgentPatch = $true
        $reason = "Core API or output/schema related files changed."
    }
    elseif ($changedOtherCode.Count -gt 0 -or $changedDeps.Count -gt 0) {
        $riskLevel = "MEDIUM"
        $needsAgentPatch = $false
        $reason = "Code/dependency changed; run compatibility tests and inspect failures."
    }
    else {
        $riskLevel = "LOW"
        $needsAgentPatch = $false
        $reason = "Only docs/CI files changed."
    }
}

$lines = @()
$lines += "# xiaohongshu-cli Upstream Update Analysis"
$lines += ""
$lines += "- Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")"
$lines += "- Submodule: $SubmodulePath"
$lines += "- Branch: $Branch"
$lines += "- Base: $baseCommit"
$lines += "- Target: $targetCommit"
$lines += "- Commits in range: $($commits.Count)"
$lines += "- Files changed: $($files.Count)"
$lines += "- Risk level: $riskLevel"
$lines += "- Needs xhs-agent patch: $needsAgentPatch"
$lines += "- Reason: $reason"
$lines += ""

$lines += "## Commit List"
if ($commits.Count -eq 0) {
    $lines += "- (none)"
}
else {
    foreach ($c in $commits) {
        $lines += "- $c"
    }
}
$lines += ""

$lines += "## Changed Files"
if ($files.Count -eq 0) {
    $lines += "- (none)"
}
else {
    foreach ($f in $files) {
        $lines += "- $f"
    }
}
$lines += ""

$lines += "## Category Summary"
$lines += "- Core API files: $($changedCore.Count)"
$lines += "- Schema/output files: $($changedSchema.Count)"
$lines += "- Dependency files: $($changedDeps.Count)"
$lines += "- Docs files: $($changedDocs.Count)"
$lines += "- CI files: $($changedCi.Count)"
$lines += "- Other code files: $($changedOtherCode.Count)"
$lines += ""

$lines += "## Recommended Actions"
$lines += '1. `cd xhs-agent && uv sync && uv run pytest -v`'
if ($riskLevel -eq "HIGH") {
    $lines += '2. Review adapter boundary: `xhs_agent/integrations/xhs_factory.py` and collector files.'
    $lines += "3. Re-check payload conversion tests and update transformers if schema changed."
}
elseif ($riskLevel -eq "MEDIUM") {
    $lines += '2. Run focused collector tests: `uv run pytest tests/test_collectors_integration.py -v`.'
}
else {
    $lines += '2. No immediate `xhs-agent` code patch expected unless tests fail.'
}

$report = ($lines -join [Environment]::NewLine)
Write-Host $report

if (-not [string]::IsNullOrWhiteSpace($OutputFile)) {
    $outPath = $OutputFile
    if (-not [System.IO.Path]::IsPathRooted($outPath)) {
        $outPath = Join-Path $root $outPath
    }
    $outDir = Split-Path -Parent $outPath
    if (-not [string]::IsNullOrWhiteSpace($outDir) -and -not (Test-Path $outDir)) {
        New-Item -Path $outDir -ItemType Directory -Force | Out-Null
    }
    Set-Content -Path $outPath -Value $report -Encoding utf8
    Write-Host ""
    Write-Host "Report written to: $outPath"
}
