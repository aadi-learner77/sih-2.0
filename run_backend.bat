@echo off
echo ========================================================
echo Starting PRAMAAN-X FastAPI Backend (Local Dev Mode)
echo ========================================================
set PYTHONPATH=.
.\venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
pause
