# Start the DayOne edge box (serves the phone app on http://<this-machine>:8765) — PowerShell
# Usage: .\run_box.ps1 [-Port 8765]
param([int]$Port = 8765)
$env:PYTHONIOENCODING = "utf-8"
if (-not $env:DAYONE_BOX_KEY) { Write-Warning "DAYONE_BOX_KEY not set: using the demo key (set a real secret on a real box)" }
python -m uvicorn edge_server:app --app-dir "$PSScriptRoot\work\strat20" --host 0.0.0.0 --port $Port
