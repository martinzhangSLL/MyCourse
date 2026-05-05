$backendDir = Split-Path -Parent $PSScriptRoot
Set-Location $backendDir

.\.venv\Scripts\python -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8001

