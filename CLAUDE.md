# CLAUDE.md — C.O.V.E.R.T Project Context

## What is this project?

**C.O.V.E.R.T** (Chain for Open and VERified Testimonies) is a decentralised whistleblowing platform.
Reporters submit encrypted evidence → stored on IPFS → committed on-chain → reviewed and moderated by the community.
COV tokens (non-transferable) enforce skin-in-the-game staking. Reputation scores and soul-bound badges control access.

**This is a B.Tech Final Year Project** — deployed on Base Sepolia testnet, not mainnet.

---

## Architecture

```
Frontend (React + Vite + Tailwind)  →  Backend (FastAPI + PostgreSQL)
         ↕                                      ↕
    Blockchain (Base Sepolia)              IPFS (Pinata / dev IndexedDB)
    5 Solidity contracts (Foundry)
```

| Layer | Tech | Hosting |
|-------|------|---------|
| Frontend | React 18, TypeScript, Vite 5, Tailwind, Zustand, ethers.js 6 | **Vercel** (`https://covert-chi.vercel.app`) |
| Backend | Python 3.12, FastAPI 0.109, SQLAlchemy 2 (async), asyncpg, Alembic | **Railway** (PostgreSQL + release-phase migrations) |
| Contracts | Solidity 0.8.20, Foundry (Forge), OpenZeppelin 5.x | **Base Sepolia** (chain ID 84532) |
| IPFS | Pinata API (production) or IndexedDB fallback (dev mode) | Pinata |

---

## Deployed Contract Addresses (Base Sepolia — chain 84532)

```
CommitmentRegistry: 0x5147e66507b0797E1E39FC7C052e465176D9bF1E
DailyAnchor:        0x5D55b7C08e45F467eE1F3F212663cE6eb9ef6428
COVCredits:         0x6ea581d247A8A43BC8544b788f9e100895099903
CovertBadges:       0x81ec2Fe3467535fd8e3A8a5bc00Bc226f2fedda4
CovertProtocol:     0x5B7AB21B2656BD187c3B544937eac9f36d901CbA
```

Deployer/Admin: `0x8A3d8B336dbb3eF591838e280d4e91c572044B38`

### Testnet Role Assignments (via GrantRolesTestnet.s.sol)

| Address | Role |
|---------|------|
| `0xc1a6EDea015AdcE9f56E84DA1C81E11b654E8cf1` | Reviewer 1 (REVIEWER_ROLE + REVIEWER_BADGE) |
| `0x52e0ec9dcfF2FF7082927414cEe58F4Aac976C03` | Reviewer 2 (REVIEWER_ROLE + REVIEWER_BADGE) |
| `0xa429C534cF66A83bFbFFF1163ce4e7c4f907f136` | Moderator 1 (MODERATOR_ROLE + MODERATOR_BADGE) |
| `0xE06C3F820586b4e31C001565b4eB9D18fBB0C0C7` | Moderator 2 (MODERATOR_ROLE + MODERATOR_BADGE) |

All accounts are in the same MetaMask wallet (different derived accounts).

---

## Directory Structure

```
/
├── frontend/                     # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/                # 9 page components (dashboards, submit, etc.)
│   │   ├── components/           # 20+ reusable components
│   │   │   ├── reporter/         # ReportSubmissionForm.tsx (key file)
│   │   │   ├── reviewer/         # Review-specific components
│   │   │   ├── layout/           # AppLayout, navigation
│   │   │   └── common/           # Shared UI components
│   │   ├── services/             # web3.ts, encryption.ts, ipfs.ts, protocol.ts
│   │   ├── stores/               # Zustand stores (report, covBalance, reviewDecision, walletSession)
│   │   ├── hooks/                # useWeb3.ts, useRoleAccess.ts
│   │   ├── types/                # TypeScript interfaces
│   │   ├── config/               # roles.ts (dev-mode address→role mapping)
│   │   └── App.tsx               # Router — unified /dashboard with role-based rendering
│   ├── .env                      # Local dev env vars (VITE_* prefixed)
│   └── package.json
│
├── backend/                      # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/v1/               # 11 router files (reports, auth, rbac, moderation, etc.)
│   │   ├── models/               # 8 SQLAlchemy models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # 20+ service modules (report, reputation, blockchain, etc.)
│   │   │   ├── ai/               # Rule-based credibility scoring
│   │   │   ├── dms/              # Dead Man's Switch
│   │   │   └── zkp/              # ZKP verification (stub)
│   │   ├── security/             # Input validation, middleware
│   │   ├── core/                 # config.py, database.py
│   │   └── main.py               # FastAPI app entry point
│   ├── alembic/versions/         # 12 migration files
│   ├── requirements.txt          # Python dependencies
│   ├── runtime.txt               # python-3.12.7 (for Railway)
│   └── Procfile                  # release: alembic upgrade head; web: uvicorn
│
├── contracts/                    # Solidity + Foundry
│   ├── src/                      # 5 contracts
│   │   ├── CommitmentRegistry.sol
│   │   ├── COVCredits.sol        # Non-transferable ERC20, WELCOME_GRANT=30, stakes burn/mint
│   │   ├── CovertBadges.sol      # Soul-bound ERC721, 6 badge types, BADGE_MANAGER_ROLE
│   │   ├── CovertProtocol.sol    # Core: reports, staking, review, finalization
│   │   └── DailyAnchor.sol       # Merkle root anchoring
│   ├── script/                   # Forge deployment scripts
│   │   ├── Deploy.s.sol          # Deploy all 5 contracts
│   │   ├── GrantRoles.s.sol      # Local Anvil role setup
│   │   └── GrantRolesTestnet.s.sol  # Base Sepolia: grants roles + mints badges
│   ├── deployments/              # base-sepolia.json, localhost.json
│   ├── .env                      # PRIVATE_KEY, role addresses, RPC URLs
│   └── foundry.toml
│
├── docs/                         # 14 comprehensive documentation files
│   └── PROJECT_BIBLE.md          # Master reference (update this with changes)
│
├── CLAUDE.md                     # THIS FILE — Claude Code context
└── docker-compose.yml            # Local dev: postgres, redis, ipfs, anvil
```

---

## Key Concepts & Flows

### Report Submission Flow (CRITICAL — recently fixed)

The submission order is **backend-first, blockchain-second** to prevent COV token loss:

1. Frontend encrypts report (AES-256-GCM)
2. Upload encrypted blob to IPFS → get CID
3. **Submit to backend** (POST /api/v1/reports) — **without tx_hash** (tx_hash is optional)
4. **Blockchain commit** (CovertProtocol.createReport) — locks COV as stake
5. Update backend with tx_hash (POST /api/v1/reports/{id}/commit)

If step 4 fails, the report is saved in the DB but **no COV is locked** — safe.
The old flow did blockchain-first which caused COV to be locked even when the backend rejected the report.

### Role-Based Dashboard Routing

`useRoleAccess` hook in `frontend/src/hooks/useRoleAccess.ts`:
- **Production (VITE_DEV_MODE=false):** Checks on-chain badges via `protocolService.getUserState()` → `BadgeType.REVIEWER_BADGE (4)` or `MODERATOR_BADGE (5)`
- **Dev mode (VITE_DEV_MODE=true):** Uses hardcoded Hardhat/Anvil addresses in `config/roles.ts`

`App.tsx` → `DashboardPage` renders:
- `isModerator` → `ProtocolModeratorDashboard`
- `isReviewer` → `ReviewerDashboard`
- default → `ReporterDashboard`

### Authentication

SIWE (Sign-In with Ethereum) — implemented in `useWeb3.ts`:
1. Frontend fetches nonce from `GET /api/v1/auth/nonce?address=...`
2. User signs EIP-4361 message with wallet
3. Frontend sends to `POST /api/v1/auth/verify` → gets JWT
4. JWT stored in `localStorage('token')` → sent as `Authorization: Bearer` header
5. On disconnect, JWT is removed

### COV Token Economy

- **Welcome grant:** 30 COV per wallet (one-time, `claimWelcome()`)
- **Report stake:** 10 COV (public) / 6 COV (private) — burned on lock, minted back on finalization
- **Support:** 1 COV, **Challenge:** 3 COV, **Appeal:** 8 COV
- All COV is non-transferable (soul-bound)
- Tokens locked = burned from balance + tracked in `lockedBalance`
- Settlement: mint back to user (honest) or to treasury (slashed)

### Reputation System

Tiers: New (0-19), Regular (20-79), Trusted (80-199), Power (200+)
Reviewer eligibility: rep >= 50, account age >= 30 days, no recent slashes, < 3 strikes

---

## Important Configuration

### Frontend .env (Vite — values baked at build time)
```
VITE_API_URL=http://localhost:8000        # Vercel: set to Railway backend URL
VITE_RPC_URL=https://sepolia.base.org
VITE_CHAIN_ID=84532
VITE_DEV_MODE=false                       # true = uses hardcoded role addresses + IndexedDB IPFS
VITE_COVERT_PROTOCOL_ADDRESS=0x5B7AB21B2656BD187c3B544937eac9f36d901CbA
VITE_COV_CREDITS_ADDRESS=0x6ea581d247A8A43BC8544b788f9e100895099903
VITE_COVERT_BADGES_ADDRESS=0x81ec2Fe3467535fd8e3A8a5bc00Bc226f2fedda4
# IPFS: needs VITE_PINATA_API_KEY + VITE_PINATA_API_SECRET for production uploads
```

### Backend config.py
- CORS: Always includes `https://covert-chi.vercel.app` via validator
- JWT: HS256, 7-day expiry
- CHAIN_ID: Configurable (must include 84532 for Base Sepolia)
- DB valid_chain constraint: `(137, 42161, 80001, 421613, 31337, 84532)`

### Contracts .env
```
PRIVATE_KEY=0x...                          # Deployer private key (has DEFAULT_ADMIN_ROLE)
REVIEWER_ADDRESS_1=0xc1a6EDea...
REVIEWER_ADDRESS_2=0x52e0ec9d...
MODERATOR_ADDRESS_1=0xa429C534...
MODERATOR_ADDRESS_2=0xE06C3F82...
```

---

## Common Commands

```bash
# Frontend
cd frontend && npm run dev                 # Local dev server (port 5173)
cd frontend && npm run build               # Production build

# Backend
cd backend && uvicorn app.main:app --reload --port 8000
cd backend && alembic upgrade head         # Run migrations
cd backend && alembic revision --autogenerate -m "description"  # New migration

# Contracts
cd contracts && forge build                # Compile
cd contracts && forge test                 # Run tests
cd contracts && forge script script/Deploy.s.sol --rpc-url https://sepolia.base.org --broadcast
cd contracts && forge script script/GrantRolesTestnet.s.sol --rpc-url https://sepolia.base.org --broadcast

# Docker (local dev)
docker-compose up -d                       # Start postgres, redis, ipfs, anvil
```

---

## Known Issues & Gotchas

1. **Windows path with spaces:** The project lives at `e:\COVERT\C.O.V.E.R.T` — bash sometimes chokes on the path. Use `cd /e/COVERT/C.O.V.E.R.T` in bash.

2. **CORS on 500 errors:** FastAPI's CORSMiddleware doesn't add headers on unhandled exceptions. A global exception handler in `main.py` catches these and returns a proper JSON response with CORS headers.

3. **`/reputation/wallet/` endpoint 500:** May fail if `user_reputation` table doesn't exist yet — run `alembic upgrade head` on Railway.

4. **IPFS uploads require Pinata keys:** Set `VITE_PINATA_API_KEY` and `VITE_PINATA_API_SECRET` in Vercel env vars, OR use `VITE_DEV_MODE=true` for IndexedDB fallback.

5. **Vite env vars are baked at build time:** Changing them in Vercel dashboard requires a redeploy.

6. **chain_id DB constraint:** The `reports` table has a CHECK constraint limiting valid chain IDs. Updated to include `84532` (Base Sepolia) — needs an Alembic migration to take effect on Railway.

7. **tx_hash is now optional:** Backend accepts reports without tx_hash (set later via `/{id}/commit`). This is by design — the submission flow does backend-first to prevent COV lock on failed submissions.

8. **Forge scripts on Windows:** Use single-line commands (no `\` line continuation in PowerShell). Scripts directory is `contracts/script/` (not `scripts/`).

9. **CovertBadges vs CovertProtocol roles:** Both are needed. CovertProtocol roles (AccessControl) gate on-chain actions. CovertBadges (SBT) gate frontend dashboard routing. `GrantRolesTestnet.s.sol` does both.

---

## Files You'll Touch Most Often

| File | What it does |
|------|-------------|
| `frontend/src/components/reporter/ReportSubmissionForm.tsx` | Report submission flow (encrypt → IPFS → backend → blockchain) |
| `frontend/src/hooks/useWeb3.ts` | Wallet connection, SIWE auth, commitReport, claimWelcome |
| `frontend/src/hooks/useRoleAccess.ts` | Role detection (badge-based or dev-mode) |
| `frontend/src/services/protocol.ts` | Smart contract interaction wrappers |
| `frontend/src/App.tsx` | Routes and dashboard rendering |
| `backend/app/api/v1/reports.py` | Report CRUD endpoints |
| `backend/app/api/v1/auth.py` | SIWE nonce + verify endpoints |
| `backend/app/api/v1/rbac.py` | On-chain role verification middleware |
| `backend/app/models/report.py` | Report SQLAlchemy model |
| `backend/app/core/config.py` | Settings, CORS, DB config |
| `contracts/src/CovertProtocol.sol` | Core contract (reports, staking, finalization) |
| `contracts/src/COVCredits.sol` | Token contract (welcome grant, lock/unlock) |
| `contracts/script/GrantRolesTestnet.s.sol` | Grant roles + mint badges on Base Sepolia |

---

## Update Rules

**When making changes to this project:**
1. Update this `CLAUDE.md` if architectural decisions, deployment details, or key flows change
2. Update `docs/PROJECT_BIBLE.md` with the same changes (it's the comprehensive reference)
3. Never commit `.env` files or private keys
4. Test on Base Sepolia before considering mainnet

*Last updated: 2026-03-25*
