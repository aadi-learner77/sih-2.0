@echo off
set PYTHON=python
if exist .venv\Scripts\python.exe set PYTHON=.venv\Scripts\python.exe
if exist venv\Scripts\python.exe set PYTHON=venv\Scripts\python.exe

if "%1"=="demo-reset" (
    echo Restoring database, issuer registry, and audit receipt ledger to deterministic demo state...
    %PYTHON% -m backend.app.data.seed_data --reset
    %PYTHON% mock_issuer\seed_registry.py
    echo PRAMAAN-X demo baseline restored successfully!
    exit /b 0
)

if "%1"=="test" (
    echo Running all automated test suites...
    %PYTHON% -m pytest backend/tests mock_issuer backend/test_api.py -v
    exit /b 0
)

if "%1"=="seed-data" (
    echo Seeding database and registry...
    %PYTHON% -m backend.app.data.seed_data
    %PYTHON% mock_issuer\seed_registry.py
    exit /b 0
)

if "%1"=="" (
    echo Available commands:
    echo   make demo-reset
    echo   make test
    echo   make seed-data
    exit /b 0
)

echo Unknown command: %1
echo Run 'make' to view available options.
exit /b 1
