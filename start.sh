#!/usr/bin/env sh
# NumberShield one-click launcher for macOS / Linux.
# First run: creates .venv, installs the app, builds the web page. Later runs just start it.
set -e
cd "$(dirname "$0")"

PY=$(command -v python3 || command -v python || true)
[ -n "$PY" ] || { echo "[NumberShield] Python 3.10+ is required: https://www.python.org/downloads/"; exit 1; }

if [ ! -x .venv/bin/python ]; then
  echo "[NumberShield] Creating Python environment..."
  "$PY" -m venv .venv
fi

if [ ! -x .venv/bin/numbershield ]; then
  echo "[NumberShield] Installing the app..."
  .venv/bin/python -m pip install --quiet -e .
fi

if [ ! -f frontend/dist/index.html ]; then
  command -v npm >/dev/null 2>&1 || { echo "[NumberShield] Node.js 18+ is required to build the web page: https://nodejs.org/"; exit 1; }
  echo "[NumberShield] Building the web page..."
  (cd frontend && npm install --no-audit --no-fund && npm run build)
fi

URL="http://127.0.0.1:8765"
echo "[NumberShield] Starting at $URL  (press Ctrl+C to stop)"
( sleep 2; (command -v open >/dev/null && open "$URL") || (command -v xdg-open >/dev/null && xdg-open "$URL") || true ) >/dev/null 2>&1 &
exec .venv/bin/numbershield serve
