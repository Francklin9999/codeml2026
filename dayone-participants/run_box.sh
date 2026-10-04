#!/usr/bin/env bash
# Start the DayOne edge box (serves the phone app on http://<this-machine>:8765)
set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
[ -z "$DAYONE_BOX_KEY" ] && echo "warning: DAYONE_BOX_KEY not set, using the demo key" >&2
exec python -m uvicorn edge_server:app --app-dir work/strat20 --host 0.0.0.0 --port "${1:-8765}"
