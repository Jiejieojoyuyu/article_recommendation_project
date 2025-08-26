# Academic Paper Recommendation System - Quick Start
Write-Host "Starting Academic Paper Recommendation System..." -ForegroundColor Green

# Check if in correct directory
if (!(Test-Path "backend") -or !(Test-Path "frontend")) {
    Write-Host "Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Start backend
Write-Host "Starting backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

# Wait a moment
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd frontend
npm run dev
"@

Write-Host ""
Write-Host "Services starting..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan