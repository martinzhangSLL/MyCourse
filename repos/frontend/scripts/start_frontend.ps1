$frontendDir = Split-Path -Parent $PSScriptRoot
Set-Location $frontendDir

if (-not (Test-Path ".\\node_modules")) {
  npm install
}

npm run dev

