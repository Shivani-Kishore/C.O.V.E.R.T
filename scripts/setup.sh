#!/bin/bash

# C.O.V.E.R.T Setup Script
# Automates the initial setup process

set -e

echo "🛡️  C.O.V.E.R.T Setup Script"
echo "================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

command -v node >/dev/null 2>&1 || { echo "❌ Node.js is not installed. Please install Node.js 18+"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python is not installed. Please install Python 3.11+"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Please install Docker"; exit 1; }
command -v forge >/dev/null 2>&1 || { echo "❌ Foundry is not installed. Please install Foundry"; exit 1; }

echo "✅ All prerequisites installed"
echo ""

# Copy environment files
echo "📝 Setting up environment files..."
cp -n .env.example .env || echo ".env already exists"
cp -n frontend/.env.example frontend/.env || echo "frontend/.env already exists"
cp -n backend/.env.example backend/.env || echo "backend/.env already exists"
cp -n contracts/.env.example contracts/.env || echo "contracts/.env already exists"
echo "✅ Environment files created"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d
echo "✅ Docker services started"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10
echo "✅ Services should be ready"
echo ""

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..
echo "✅ Backend setup complete"
echo ""

# Setup frontend
echo "⚛️  Setting up React frontend..."
cd frontend
npm install
cd ..
echo "✅ Frontend setup complete"
echo ""

# Setup smart contracts
echo "⛓️  Setting up smart contracts..."
cd contracts
forge install foundry-rs/forge-std
forge build
cd ..
echo "✅ Smart contracts setup complete"
echo ""

echo "================================"
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "2. Start frontend: cd frontend && npm run dev"
echo "3. Deploy contracts: cd contracts && forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast"
echo ""
echo "Access points:"
echo "- Frontend: http://localhost:5173"
echo "- Backend: http://localhost:8000"
echo "- API Docs: http://localhost:8000/api/docs"
echo "- IPFS: http://localhost:8080"
echo ""
