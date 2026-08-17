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
  if ($SkipDocker) {
    $previousPythonPath = $env:PYTHONPATH
    $env:PYTHONPATH = Join-Path $root "src"
    Invoke-Checked "strict Python project validation" { python -m ci_guardrails validate --root $root --strict }
    Invoke-Checked "publication evidence validation" { python tools/validate-publication.py }
    $env:PYTHONPATH = $previousPythonPath
  }

  $resultPath = Join-Path $root "benchmarks\results\guardrails-baseline.json"
  if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
    Invoke-Checked "benchmark JSON validation" { python -m json.tool $resultPath | Out-Null }
  }

  if (-not $SkipDocker -and (Test-Path -LiteralPath (Join-Path $root "Dockerfile") -PathType Leaf)) {
    $imageName = (Split-Path -Leaf $root).ToLowerInvariant()
    Invoke-Checked "docker build" { docker build -t $imageName $root | Out-Null }
    Invoke-Checked "docker default run" { docker run --rm --network none $imageName | Out-Null }
    Invoke-Checked "docker strict validation" { docker run --rm --network none $imageName validate --strict | Out-Null }
    Invoke-Checked "docker publication validation" {
      docker run --rm --network none --entrypoint python $imageName tools/validate-publication.py | Out-Null
    }
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
