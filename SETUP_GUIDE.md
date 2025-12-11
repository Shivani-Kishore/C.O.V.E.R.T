# C.O.V.E.R.T Setup Guide

**Complete setup instructions for local development**

---

## Prerequisites

Ensure you have the following installed:

### Required Software
- **Node.js** 18+ and npm: [Download](https://nodejs.org/)
- **Python** 3.11+: [Download](https://www.python.org/)
- **Docker** and Docker Compose: [Download](https://www.docker.com/)
- **Git**: [Download](https://git-scm.com/)

### Install Foundry (for smart contracts)
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

Verify installations:
```bash
node --version  # Should be 18+
python --version  # Should be 3.11+
docker --version
forge --version
```

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/covert.git
cd C.O.V.E.R.T
```

### 2. Set Up Environment Variables

```bash
# Copy all example environment files
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
cp contracts/.env.example contracts/.env
```

### 3. Start Docker Services

```bash
# Start PostgreSQL, Redis, IPFS, and Anvil
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs -f
```

Wait for all services to be healthy (this may take 1-2 minutes).

### 4. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload
```

The backend should now be running at http://localhost:8000

### 5. Set Up Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend should now be running at http://localhost:5173

### 6. Set Up Smart Contracts

Open a new terminal:

```bash
cd contracts

# Install Foundry dependencies
forge install foundry-rs/forge-std

# Compile contracts
forge build

# Run tests
forge test -vvv

# Deploy to local Anvil
forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

After deployment, copy the contract addresses from the output and update:
- `backend/.env`: `COMMITMENT_REGISTRY_ADDRESS`, `DAILY_ANCHOR_ADDRESS`
- `frontend/.env`: `VITE_COMMITMENT_REGISTRY_ADDRESS`, `VITE_DAILY_ANCHOR_ADDRESS`

### 7. Verify Everything is Working

Access the following URLs in your browser:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **IPFS Gateway**: http://localhost:8080/ipfs/

---

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

```bash
# Find process using the port (example for port 5173)
# Windows:
netstat -ano | findstr :5173
# macOS/Linux:
lsof -i :5173

# Kill the process or change the port in the config
```

### Docker Services Not Starting

```bash
# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Start again
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Python Virtual Environment Issues

```bash
# Remove existing venv
rm -rf venv

# Recreate
python -m venv venv

# Reactivate and reinstall
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### Foundry Installation Issues

```bash
# Update Foundry
foundryup

# If still having issues, reinstall
rm -rf ~/.foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

---

## Development Workflow

### Starting Development

1. **Start Docker services**:
   ```bash
   docker-compose up -d
   ```

2. **Start backend** (in one terminal):
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Start frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

### Stopping Development

```bash
# Stop frontend/backend with Ctrl+C

# Stop Docker services
docker-compose down
```

---

## Next Steps

After successful setup, you can:

1. Read the [IMPLEMENTATION_ROADMAP.md](claude_docs/IMPLEMENTATION_ROADMAP.md) to understand Week 1 tasks
2. Explore the [ARCHITECTURE.md](claude_docs/ARCHITECTURE.md) to understand the system design
3. Review the [DATABASE_SCHEMA.md](claude_docs/DATABASE_SCHEMA.md) to set up the database
4. Start implementing Week 2 features (encryption and IPFS storage)

---

## Useful Commands

### Docker

```bash
# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Execute command in container
docker-compose exec postgres psql -U covert_user -d covert_db
```

### Backend

```bash
# Format code
black .

# Lint code
flake8

# Run tests
pytest -v --cov
```

### Frontend

```bash
# Lint code
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Smart Contracts

```bash
# Compile
forge build

# Test
forge test -vvv

# Format
forge fmt

# Gas report
forge test --gas-report
```

---

## Environment-Specific Setup

### Development
Already configured in `.env.example` files.

### Testnet (Base Sepolia)
Update `.env` files with:
```bash
RPC_URL=https://sepolia.base.org
CHAIN_ID=84532
```

### Production
See [DEPLOYMENT.md](claude_docs/DEPLOYMENT.md) for production setup.

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the documentation in `claude_docs/`
3. Open an issue on GitHub
4. Email: hello@covert.app

---

**Happy Coding!**
