# Academic Paper Recommendation System Startup Script
# Please ensure Python 3.8+ and Node.js 16+ are installed

Write-Host "Academic Paper Recommendation System Startup Script" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# Check required tools
Write-Host "Checking environment..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found, please install Python 3.8+ first" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found, please install Node.js 16+ first" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "npm not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# --- 1. Setup Python virtual environment and install backend dependencies ---
Write-Host "Setting up backend environment..." -ForegroundColor Cyan

if (!(Test-Path "article_recommend")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv article_recommend
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "./article_recommend/Scripts/Activate.ps1"

if (!(Test-Path "backend/requirements.txt")) {
    Write-Host "backend/requirements.txt file not found" -ForegroundColor Red
    exit 1
}

Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
pip install -r ./backend/requirements.txt

Write-Host "Backend environment setup completed" -ForegroundColor Green
Write-Host ""

# --- 2. Install frontend dependencies ---
Write-Host "Setting up frontend environment..." -ForegroundColor Cyan

if (!(Test-Path "frontend/package.json")) {
    Write-Host "frontend/package.json file not found" -ForegroundColor Red
    exit 1
}

Set-Location frontend
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
npm install

# Install additional Tailwind CSS plugins
Write-Host "Installing Tailwind CSS plugins..." -ForegroundColor Yellow
npm install @tailwindcss/forms @tailwindcss/typography @tailwindcss/aspect-ratio

Set-Location ..
Write-Host "Frontend environment setup completed" -ForegroundColor Green
Write-Host ""

# --- 3. Start services ---
Write-Host "Starting services..." -ForegroundColor Cyan

# Start backend service (in new window)
Write-Host "Starting FastAPI backend service..." -ForegroundColor Yellow
$backendScript = @"
# Activate virtual environment
& './article_recommend/Scripts/Activate.ps1'
# Enter backend directory
Set-Location backend  # <-- CORRECT: Stay in the 'backend' folder
# Start service
Write-Host 'FastAPI backend service starting...' -ForegroundColor Green
Write-Host 'API URL: http://127.0.0.1:8000' -ForegroundColor Yellow
Write-Host 'API Docs: http://127.0.0.1:8000/docs' -ForegroundColor Yellow
Write-Host 'Press Ctrl+C to stop service' -ForegroundColor Gray
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000  # <-- CORRECT: Use 'app.main:app'
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# Wait for backend to start
Write-Host "Waiting for backend service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start frontend service
Write-Host "Starting Vue frontend development server..." -ForegroundColor Yellow
Set-Location frontend

$frontendScript = @"
Write-Host 'Vue frontend development server starting...' -ForegroundColor Green
Write-Host 'Frontend URL: http://localhost:5173' -ForegroundColor Yellow
Write-Host 'Press Ctrl+C to stop service' -ForegroundColor Gray
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host ""
Write-Host "Project startup completed!" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Frontend Application: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test Account:" -ForegroundColor Yellow
Write-Host "   Username: student_zhang" -ForegroundColor White
Write-Host "   Password: password" -ForegroundColor White
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "   - Wait for frontend compilation to complete, then visit http://localhost:5173" -ForegroundColor White
Write-Host "   - You can register a new account or use the test account to login" -ForegroundColor White
Write-Host "   - Press Ctrl+C to stop the corresponding services" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
Read-Host