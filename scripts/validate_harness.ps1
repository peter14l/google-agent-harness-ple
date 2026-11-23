# PowerShell script to validate the harness via kit check
param (
    [string]$EnvFile = "local.env"
)

Write-Host "==> Running kit check on harness..."
Set-Location -Path ple
uv run python -m kit check ../harness --env-file "../$EnvFile"
Set-Location -Path ..
