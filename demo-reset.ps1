# PowerShell script to restore PRAMAAN-X to the exact presentation state
Write-Host "Restoring database, issuer registry, and audit receipt ledger to deterministic demo state..." -ForegroundColor Cyan

.venv\Scripts\python.exe -m backend.app.data.seed_data --reset
.venv\Scripts\python.exe mock_issuer/seed_registry.py

Write-Host "PRAMAAN-X demo baseline restored successfully!" -ForegroundColor Green
