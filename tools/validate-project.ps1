param(
  [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
  param([string]$Message)
  $script:failures.Add($Message)
}

function Invoke-Checked {
  param(
    [string]$Label,
    [scriptblock]$Command
  )
  & $Command
  if ($LASTEXITCODE -ne 0) {
    Add-Failure "$Label failed with exit code $LASTEXITCODE"
  }
  $global:LASTEXITCODE = 0
}

Push-Location -LiteralPath $root
try {
  $previousPythonPath = $env:PYTHONPATH
  $env:PYTHONPATH = Join-Path $root "src"
  Invoke-Checked "strict Python project validation" { python -m ci_guardrails validate --root $root --strict }
  $env:PYTHONPATH = $previousPythonPath

  $resultPath = Join-Path $root "benchmarks\results\guardrails-baseline.json"
  if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
    Add-Failure "Missing benchmark JSON: benchmarks/results/guardrails-baseline.json"
  } else {
    Invoke-Checked "benchmark JSON validation" { python -m json.tool $resultPath | Out-Null }
  }

  if (-not $SkipDocker -and (Test-Path -LiteralPath (Join-Path $root "Dockerfile") -PathType Leaf)) {
    $imageName = (Split-Path -Leaf $root).ToLowerInvariant()
    Invoke-Checked "docker build" { docker build -t $imageName $root | Out-Null }
  }
} finally {
  Pop-Location
}

if ($failures.Count -gt 0) {
  # Write-Error is a terminating error while $ErrorActionPreference is "Stop",
  # so emitting the list through it aborts on the first entry and hides every
  # remaining failure. Report the complete list on the success stream instead.
  Write-Host "portfolio project validation failed with $($failures.Count) issue(s):"
  foreach ($failure in $failures) {
    Write-Host "  - $failure"
    if ($env:GITHUB_ACTIONS -eq "true") {
      Write-Host "::error::$failure"
    }
  }
  exit 1
}

Write-Host "portfolio project validation passed"
