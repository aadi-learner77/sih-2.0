@echo off
echo ========================================================
echo Starting PRAMAAN-X Full Stack Platform
echo ========================================================
echo.

set PYTHONPATH=.

echo [1/3] Starting Mock Issuer Gateway on port 8001...
start "PRAMAAN-X Mock Issuer (Port 8001)" cmd /k "set PYTHONPATH=. && python -m uvicorn mock_issuer.app.main:app --host 127.0.0.1 --port 8001"

echo [2/3] Starting FastAPI Backend on port 8000...
start "PRAMAAN-X Backend (Port 8000)" cmd /k "set PYTHONPATH=. && python -m uvicorn backend.app.main:app --reload-dir backend --host 127.0.0.1 --port 8000"

echo [3/3] Starting Vite Frontend on port 5173...
start "PRAMAAN-X Frontend (Port 5173)" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ========================================================
echo Waiting for servers to initialize...
echo ========================================================
timeout /t 3 /nobreak >nul

echo Opening browser at http://127.0.0.1:5173 ...
start http://127.0.0.1:5173

echo.
echo All services launched! Keep the opened terminal windows running.

