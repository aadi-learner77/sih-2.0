@echo off
echo ========================================================
echo Starting PRAMAAN-X Mock Statutory Issuer Gateway (Port 8001)
echo ========================================================
set PYTHONPATH=.
if exist .\venv\Scripts\uvicorn.exe (
    .\venv\Scripts\uvicorn mock_issuer.app.main:app --host 127.0.0.1 --port 8001
) else if exist .\.venv\Scripts\uvicorn.exe (
    .\.venv\Scripts\uvicorn mock_issuer.app.main:app --host 127.0.0.1 --port 8001
) else (
    python -m uvicorn mock_issuer.app.main:app --host 127.0.0.1 --port 8001
)
pause
