@echo off
REM NumberShield one-click launcher for Windows.
REM First run: creates .venv, installs the app, builds the web page. Later runs just start it.
setlocal
cd /d "%~dp0"

where python >nul 2>nul || (echo [NumberShield] Python 3.10+ is required: https://www.python.org/downloads/ & pause & exit /b 1)

if not exist ".venv\Scripts\python.exe" (
  echo [NumberShield] Creating Python environment...
  python -m venv .venv || (pause & exit /b 1)
)

if not exist ".venv\Scripts\numbershield.exe" (
  echo [NumberShield] Installing the app...
  ".venv\Scripts\python.exe" -m pip install --quiet -e . || (pause & exit /b 1)
)

if not exist "frontend\dist\index.html" (
  where npm >nul 2>nul || (echo [NumberShield] Node.js 18+ is required to build the web page: https://nodejs.org/ & pause & exit /b 1)
  echo [NumberShield] Building the web page...
  pushd frontend
  call npm install --no-audit --no-fund || (popd & pause & exit /b 1)
  call npm run build || (popd & pause & exit /b 1)
  popd
)

echo [NumberShield] Starting at http://127.0.0.1:8765  (close this window or press Ctrl+C to stop)
start "" "http://127.0.0.1:8765"
".venv\Scripts\numbershield.exe" serve
