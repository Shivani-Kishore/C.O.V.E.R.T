# C.O.V.E.R.T - Setup Instructions

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- Foundry (for smart contracts)

### Installation

1. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

2. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Install Smart Contract Dependencies**
```bash
cd contracts
forge install
```

### Configuration

1. **Frontend Environment**
Create `frontend/.env`:
```env
VITE_COMMITMENT_REGISTRY_ADDRESS=
VITE_DAILY_ANCHOR_ADDRESS=
VITE_API_URL=http://localhost:8000
```

2. **Backend Environment**
Create `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/covert
SECRET_KEY=your-secret-key-here
COMMITMENT_REGISTRY_ADDRESS=
DAILY_ANCHOR_ADDRESS=
```

3. **Contracts Environment**
Create `contracts/.env`:
```env
PRIVATE_KEY=your-deployer-private-key
RPC_URL=http://localhost:8545
```

### Running the Application

1. **Start PostgreSQL Database**
```bash
# Using Docker
docker-compose up -d postgres
```

2. **Run Database Migrations**
```bash
cd backend
alembic upgrade head
```

3. **Start Backend Server**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

4. **Start Frontend Development Server**
```bash
cd frontend
npm run dev
```

5. **Deploy Smart Contracts (Local)**
```bash
# Start Anvil in a separate terminal
anvil

# Deploy contracts
cd contracts
forge script script/Deploy.s.sol:DeployLocalScript --rpc-url http://localhost:8545 --broadcast
```

### Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Features Implemented

### Week 1: Project Setup
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Smart Contracts: Foundry + Solidity

### Week 2: Basic Encryption & Storage
- Client-side AES-256-GCM encryption
- IPFS multi-provider upload with fallback
- Database models for reports and moderation
- Encryption service tests

### Week 3: Smart Contract Development
- CommitmentRegistry contract for report commitments
- DailyAnchor contract for merkle root anchoring
- Comprehensive test suites with fuzzing
- Web3 integration (frontend and backend)
- Wallet connection UI

### Week 4: Reporter Dashboard
- Multi-step report submission form
- File upload with drag-and-drop
- Encrypted IPFS upload
- Blockchain commitment transaction
- Reports listing with filters
- Status tracking and analytics
- Reporter dashboard with stats

## Project Structure

```
C.O.V.E.R.T/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/      # AppLayout
│   │   │   └── reporter/    # Report components
│   │   ├── pages/           # Dashboard, Submit, etc.
│   │   ├── services/        # Encryption, IPFS, Web3
│   │   ├── hooks/           # useWeb3
│   │   ├── stores/          # Zustand stores
│   │   └── types/           # TypeScript types
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Database models
│   │   └── schemas/         # Pydantic schemas
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── contracts/
│   ├── src/                 # Solidity contracts
│   ├── script/              # Deployment scripts
│   └── test/                # Contract tests
└── claude_docs/             # Documentation
```

## Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd backend
pytest
```

### Smart Contract Tests
```bash
cd contracts
forge test
```

## Troubleshooting

### Frontend won't start
- Run `npm install` to ensure all dependencies are installed
- Check that port 5173 is not in use
- Verify `.env` file exists with correct values

### Backend errors
- Ensure PostgreSQL is running
- Run database migrations: `alembic upgrade head`
- Check DATABASE_URL in `.env`

### Smart contract deployment fails
- Ensure Anvil is running on port 8545
- Verify PRIVATE_KEY in contracts/.env
- Check RPC_URL is correct

## Next Steps

Week 5 and beyond will implement:
- Moderator dashboard and review system
- AI-assisted content analysis
- Dispute resolution mechanism
- Enhanced privacy features
- Production deployment configuration
