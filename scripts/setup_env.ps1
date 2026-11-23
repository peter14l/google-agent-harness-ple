# PowerShell environment setup script
Write-Host "==> Checking Docker daemon..."
try {
    docker info | Out-Null
    Write-Host "Docker daemon is running."
} catch {
    Write-Warning "Docker is not running or not installed. Please launch Docker Desktop."
}

Write-Host "==> Checking uv package manager..."
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
}

Write-Host "==> Installing Harbor 0.20.0 with websockets..."
uv tool install harbor==0.20.0 --with websockets

if (-not (Test-Path "local.env")) {
    Copy-Item "local.env.example" "local.env"
    Write-Host "Created local.env from template. Please update it with your API keys and project settings."
}

Write-Host "==> Setup completed successfully."
