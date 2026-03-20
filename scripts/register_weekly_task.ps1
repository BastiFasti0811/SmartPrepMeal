param(
  [string]$Time = "07:30"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $projectRoot "exports"

Push-Location $projectRoot
try {
  python -m app.automation --register-task --task-time $Time --output-dir $outputDir
  python -m app.automation --status
}
finally {
  Pop-Location
}
