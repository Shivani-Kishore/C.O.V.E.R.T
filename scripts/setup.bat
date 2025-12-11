@echo off
REM C.O.V.E.R.T Setup Script for Windows
REM Automates the initial setup process

echo.
echo ======================================
echo    C.O.V.E.R.T Setup Script (Windows)
echo ======================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed. Please install Node.js 18+
    exit /b 1
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed. Please install Python 3.11+
    exit /b 1
)

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed. Please install Docker
    exit /b 1
)

where forge >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Foundry is not installed. Please install Foundry
    exit /b 1
)

echo All prerequisites installed
echo.

REM Copy environment files
echo Setting up environment files...
if not exist .env copy .env.example .env
if not exist frontend\.env copy frontend\.env.example frontend\.env
if not exist backend\.env copy backend\.env.example backend\.env
if not exist contracts\.env copy contracts\.env.example contracts\.env
echo Environment files created
echo.

REM Start Docker services
echo Starting Docker services...
docker-compose up -d
echo Docker services started
echo.

REM Wait for services
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul
echo Services should be ready
echo.

REM Setup backend
echo Setting up Python backend...
cd backend
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..
echo Backend setup complete
echo.

REM Setup frontend
echo Setting up React frontend...
cd frontend
call npm install
cd ..
echo Frontend setup complete
echo.

REM Setup smart contracts
echo Setting up smart contracts...
cd contracts
forge install foundry-rs/forge-std
forge build
cd ..
echo Smart contracts setup complete
echo.

echo ======================================
echo Setup Complete!
echo.
echo Next steps:
echo 1. Start backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo 2. Start frontend: cd frontend ^&^& npm run dev
echo 3. Deploy contracts: cd contracts ^&^& forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast
echo.
echo Access points:
echo - Frontend: http://localhost:5173
echo - Backend: http://localhost:8000
echo - API Docs: http://localhost:8000/api/docs
echo - IPFS: http://localhost:8080
echo.
pause
