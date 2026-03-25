# C.O.V.E.R.T — Complete Project Reference

**Chain for Open and VERified Testimonies**

A decentralised whistleblowing protocol that combines client-side encryption, IPFS storage, on-chain commitment tracking, and a stake-based moderation system to protect anonymous reporters while incentivising honest review.

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [User Roles & Lifecycle](#4-user-roles--lifecycle)
5. [COV Token Economy](#5-cov-token-economy)
6. [Reputation System](#6-reputation-system)
7. [Report Lifecycle](#7-report-lifecycle)
8. [Smart Contracts](#8-smart-contracts)
9. [Backend API](#9-backend-api)
10. [Frontend Application](#10-frontend-application)
11. [Database Schema](#11-database-schema)
12. [Encryption & Privacy](#12-encryption--privacy)
13. [Dead Man's Switch (DMS)](#13-dead-mans-switch-dms)
14. [AI Analysis Services](#14-ai-analysis-services)
15. [Environment & Configuration](#15-environment--configuration)
16. [Deployment & Production](#16-deployment--production)
17. [Development Setup & Scripts](#17-development-setup--scripts)
18. [Implementation Status](#18-implementation-status)
19. [Production Readiness Checklist](#19-production-readiness-checklist)

---

## 1. Platform Overview

### Purpose
C.O.V.E.R.T enables anonymous whistleblowers to submit encrypted evidence reports that are stored on IPFS, committed to the blockchain, and assessed through a multi-tier review process. The protocol uses economic incentives (COV token staking) and reputation scoring to align participant behaviour.

### Core Principles
- **Reporter anonymity** — ZKP-based identity, burner wallets, no on-chain link to real identity
- **Evidence immutability** — IPFS content addressing + on-chain commitment hash
- **Skin in the game** — All participants stake COV tokens; honest behaviour is rewarded, dishonesty is penalised
- **Decentralised moderation** — Multi-tier review (Reviewer → Moderator) with consensus requirements
- **Tamper-proof audit trail** — Daily Merkle anchors for moderation logs

### Participant Roles
| Role | Access | On-Chain Gate |
|------|--------|---------------|
| Reporter (User) | Submit reports, support/challenge, appeal | Any wallet with COV balance |
| Reviewer | Assess reports (REVIEW_PASSED / NEEDS_EVIDENCE / REJECT_SPAM) | `REVIEWER_ROLE` on CovertProtocol |
| Protocol Moderator | Finalize reports, settle stakes, mark malicious actors | `MODERATOR_ROLE` on CovertProtocol |
| Automation Worker | Auto-grant/revoke REVIEWER_ROLE based on rep thresholds | `AUTOMATION_ROLE` on CovertProtocol |

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ Reporter  │  │ Reviewer │  │ Moderator  │  │  Landing Page │  │
│  │ Dashboard │  │Dashboard │  │ Dashboard  │  │               │  │
│  └─────┬─────┘  └─────┬────┘  └─────┬──────┘  └───────────────┘  │
│        │              │              │                            │
│  ┌─────┴──────────────┴──────────────┴──────────┐                │
│  │  Services: web3 · protocol · encryption · ipfs│                │
│  │  Stores:   report · covBalance · reviewDecision│               │
│  │  Hooks:    useWeb3 · useRoleAccess             │               │
│  └──────────────────────┬────────────────────────┘                │
└─────────────────────────┼────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
     ┌────────────┐ ┌──────────┐ ┌──────────┐
     │  Backend   │ │  IPFS    │ │ Blockchain│
     │ (FastAPI)  │ │ Gateway  │ │  (EVM)   │
     └─────┬──────┘ └──────────┘ └─────┬────┘
           │                           │
     ┌─────┴──────┐          ┌─────────┴─────────────────────┐
     │ PostgreSQL │          │ Smart Contracts (Solidity)     │
     │  + Redis   │          │ CommitmentRegistry             │
     └────────────┘          │ DailyAnchor                    │
                             │ COVCredits                     │
                             │ CovertBadges                   │
                             │ CovertProtocol                 │
                             └────────────────────────────────┘
```

### Data Flow
1. **Report Submission:** Frontend encrypts (AES-256-GCM) → uploads to IPFS → saves metadata in backend DB (without tx_hash) → commits hash on-chain (locks COV stake) → updates backend with tx_hash → stores evidence key. **Backend-first order prevents COV tokens being locked when the backend rejects the report.**
2. **Review:** Reviewer fetches reports from chain (or DB fallback) → decrypts evidence using stored key → sets on-chain review decision → syncs to DB
3. **Moderation:** Moderator fetches reviewed reports → flags malicious actors → finalizes on-chain (settles stakes) → backend applies reputation deltas
4. **Cross-Dashboard Updates:** `CustomEvent` dispatch + 30-60s polling for cross-tab/cross-user synchronisation

---

## 3. Tech Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool & dev server |
| Tailwind CSS | 3.x | Utility-first styling |
| Zustand | 4.x | State management (with localStorage persistence) |
| ethers.js | 6.x | Blockchain interaction |
| react-router-dom | 6.x | Client-side routing |
| react-hot-toast | — | Toast notifications |
| @headlessui/react | — | Accessible UI primitives |
| @heroicons/react | — | Icon library |

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime |
| FastAPI | 0.109.0 | Async API framework |
| SQLAlchemy | 2.0.25 | Async ORM |
| asyncpg | 0.30.0 | PostgreSQL async driver |
| Alembic | 1.13.1 | Database migrations |
| Web3.py | >=6.17.0 | Blockchain interaction |
| Pydantic | 2.9.2 | Request/response validation |
| Redis | 5.0.1 | Caching |
| Celery | 5.3.4 | Task queue |
| Uvicorn | 0.27.0 | ASGI server |
| NLTK / TextBlob | — | AI credibility scoring |
| Sentry | 1.39.2 | Error monitoring |

### Smart Contracts
| Technology | Version | Purpose |
|-----------|---------|---------|
| Solidity | ^0.8.20 | Smart contract language |
| Foundry (Forge) | latest | Build, test, deploy framework |
| OpenZeppelin | 5.x | AccessControl, ERC721, Pausable, ReentrancyGuard |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL (async via asyncpg) |
| Cache | Redis |
| File Storage | IPFS (local / NFT.Storage / web3.storage / Pinata) |
| Blockchain | EVM-compatible (Base, Ethereum, Polygon) |
| Local Dev Chain | Anvil (Foundry) |

---

## 4. User Roles & Lifecycle

### 4.1 Reporter (User)

**How to become one:** Connect any EVM wallet. Claim 30 COV welcome grant.

**Actions:**
- Submit encrypted reports (public: 10 COV stake, private: 6 COV)
- Support other reports (1 COV stake)
- Challenge other reports (3 COV stake) — mutually exclusive with support on same report
- Appeal reviewer decisions (8 COV bond)
- View public report feed
- Track own submissions

**Restrictions:**
- Cannot support AND challenge the same report
- Cannot review or finalize own reports
- Cannot mark self as malicious
- Rate-limited to 10 report submissions per hour

### 4.2 Reviewer

**How to become one:**
- **Dev mode:** Hardhat/Anvil accounts 2 (`0x3C44...`) and 4 (`0x15d3...`) are pre-assigned
- **Production:** Must meet ALL eligibility requirements:
  - Reputation score ≥ 50
  - Account age ≥ 30 days
  - No slashing in the last 30 days
  - Fewer than 3 active strikes (30-day rolling window)
- `REVIEWER_ROLE` is granted on-chain by `AUTOMATION_ROLE` (or admin)
- Role admin for REVIEWER_ROLE is `AUTOMATION_ROLE` (not DEFAULT_ADMIN)

**Actions:**
- All reporter actions
- Set review decision on reports: `REVIEW_PASSED`, `NEEDS_EVIDENCE`, `REJECT_SPAM`
- View evidence files (via decryption key)
- Save review notes (auto-saved, debounced 2s)
- Batch submit decisions for multiple reports
- Track accuracy stats (decisions vs. final labels)

**Restrictions:**
- Cannot hold `MODERATOR_ROLE` simultaneously (mutual exclusivity enforced on-chain)
- Cannot review own reports
- Penalised if decision contradicts moderator's final label (mismatch penalty)
- Penalised if decision overturned by successful appeal (-5 rep + slash)

**Keyboard Shortcuts (ReviewerDashboard):**
- `P` → REVIEW_PASSED
- `N` → NEEDS_EVIDENCE
- `R` → REJECT_SPAM
- `Escape` → Deselect report

### 4.3 Protocol Moderator

**How to become one:**
- **Dev mode:** Hardhat/Anvil accounts 3, 6, 9 are pre-assigned
- **Production:** Granted `MODERATOR_ROLE` by `DEFAULT_ADMIN_ROLE` holder
- Reputation score ≥ 90 (backend threshold for seeding)

**Actions:**
- All reporter actions
- Finalize reports with a final label:
  - `CORROBORATED` — Report confirmed legitimate
  - `NEEDS_EVIDENCE` — Insufficient evidence
  - `DISPUTED` — Conflicting signals
  - `FALSE_OR_MANIPULATED` — Report is false/spam
- Set appeal outcome: `APPEAL_WON`, `APPEAL_LOST`, `APPEAL_ABUSIVE`
- Mark individual supporters/challengers as malicious (stakes slashed + strike)
- View flagged wallets (wallets with active strikes)
- View reviewer candidates (wallets meeting eligibility)
- Save moderation notes per report
- Batch finalize multiple reports

**Restrictions:**
- Cannot hold `REVIEWER_ROLE` simultaneously
- Cannot finalize own reports
- Minimum 2 moderators required per report for consensus (configurable)

### 4.4 Automation Worker

**How it works:**
- Backend service with `AUTOMATION_PRIVATE_KEY` configured
- Holds `AUTOMATION_ROLE` on CovertProtocol
- Endpoint: `POST /api/v1/reputation/sync-reviewer-roles`
- Scans all wallets with rep ≥ 50 → auto-grants `REVIEWER_ROLE`
- Scans existing reviewers with rep < 50 → auto-revokes `REVIEWER_ROLE`

### 4.5 Dev/Test Account Mapping (Hardhat/Anvil)

| Account | Address | Role | Initial Rep | Initial COV |
|---------|---------|------|-------------|-------------|
| 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | User | 0 | 30 |
| 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | User | 0 | 30 |
| 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | Reviewer | 50 | 30 |
| 3 | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` | Moderator | 90 | 30 |
| 4 | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` | Reviewer | 50 | 30 |
| 5 | `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` | User | 0 | 30 |
| 6 | `0x976EA74026E726554dB657fA54763abd0C3a0aa9` | Moderator | 90 | 30 |
| 7 | `0x14dC79964da2C08b23698B3D3cc7Ca32193d9955` | User | 0 | 30 |
| 8 | `0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f` | User | 0 | 30 |
| 9 | `0xa0Ee7A142d267C1f36714E4a8F75612F20a79720` | Moderator | 90 | 30 |

---

## 5. COV Token Economy

### Token Properties
- **Name:** COV Credits
- **Symbol:** COV
- **Decimals:** 18
- **Max Supply:** 100,000,000 COV
- **Transferability:** Non-transferable (soul-bound to wallet). All `transfer()`, `approve()`, `transferFrom()` revert.
- **Minting:** Only `MINTER_ROLE` holders (deployer + CovertProtocol contract)
- **Burning:** Only `BURNER_ROLE` holders (deployer + CovertProtocol contract)
- **Pausable:** `PAUSER_ROLE` can pause minting/granting (burn always works)

### Token Distribution
| Event | Amount | Condition |
|-------|--------|-----------|
| Welcome grant | 30 COV | One-time per wallet (`grantWelcome()` / `claimWelcome()`) |
| Protocol rewards | Variable | Minted by protocol for honest participation |

### Staking Costs
| Action | COV Cost | Lock Duration |
|--------|----------|---------------|
| Submit public report | 10 COV | Until finalization |
| Submit private report | 6 COV | Until finalization |
| Support a report | 1 COV | Until finalization |
| Challenge a report | 3 COV | Until finalization |
| Appeal a decision | 8 COV | Until appeal resolution |

### Stake Settlement (on Finalization)

**Report Stake:**
| Final Label | Reporter Outcome |
|-------------|------------------|
| CORROBORATED | Returned |
| NEEDS_EVIDENCE | Returned |
| DISPUTED | Returned |
| FALSE_OR_MANIPULATED | **Slashed to treasury** |

**Supporter Stakes:**
| Final Label | Supporter Outcome |
|-------------|-------------------|
| CORROBORATED | Returned |
| NEEDS_EVIDENCE | Returned |
| DISPUTED | Returned |
| FALSE_OR_MANIPULATED | **Slashed to treasury** |

**Challenger Stakes:**
| Condition | Challenger Outcome |
|-----------|--------------------|
| Not marked malicious | Returned |
| Marked malicious by moderator | **Slashed to treasury** |

**Appeal Bond (8 COV):**
| Appeal Outcome | Reporter Gets | Treasury Gets |
|----------------|--------------|---------------|
| APPEAL_WON | 8 COV (full return) | 0 |
| APPEAL_LOST | 4 COV (half return) | 4 COV |
| APPEAL_ABUSIVE | 0 | 8 COV (full slash) |

### Locking Mechanism
Credits are **burned** when locked (removed from user balance) and tracked in `lockedBalance`. On settlement, credits are **minted** back to the user (return) or to the treasury (slash). This prevents double-spending of locked tokens.

---

## 6. Reputation System

### Tier Thresholds

| Tier | Rep Score Range | Label |
|------|----------------|-------|
| Tier 0 | 0 – 19 | New |
| Tier 1 | 20 – 79 | Regular |
| Tier 2 | 80 – 199 | Trusted |
| Tier 3 | 200+ | Power |

### Rep Deltas per Final Label

**Reporter:**
| Final Label | Base Delta | With Slash | With Malicious Flag | Total |
|-------------|-----------|------------|---------------------|-------|
| CORROBORATED | +8 | — | — | +8 |
| NEEDS_EVIDENCE | 0 | — | — | 0 |
| DISPUTED | -2 | — | — | -2 |
| FALSE_OR_MANIPULATED | -10 | -5 | — | -15 |
| FALSE_OR_MANIPULATED + malicious | -10 | -5 | -5 | -20 + strike |

**Supporter:**
| Final Label | Base Delta | With Slash |
|-------------|-----------|------------|
| CORROBORATED | +1 | — |
| FALSE_OR_MANIPULATED | -2 | -5 (total: -7) |
| Others | 0 | — |

**Challenger:**
| Final Label | Delta |
|-------------|-------|
| FALSE_OR_MANIPULATED | +2 |
| DISPUTED | +2 |
| NEEDS_EVIDENCE | +1 |
| CORROBORATED | -2 |

**Appeal Effects (additive on reporter):**
| Appeal Outcome | Delta | Additional |
|---------------|-------|------------|
| APPEAL_WON | +2 | — |
| APPEAL_LOST | 0 | — |
| APPEAL_ABUSIVE | -5 | Slash + strike |

### Penalties
| Type | Delta | Additional Effects |
|------|-------|-------------------|
| Slash penalty | -5 | Records `last_slash_at` |
| Malicious flag | -5 | Adds strike |
| Reviewer appeal penalty (APPEAL_WON) | -5 | Slash |
| Reviewer mismatch penalty | -5 | Slash (when reviewer decision contradicts moderator label) |

### Strike System
- Rolling 30-day window
- Counter resets when previous window expires
- 3+ active strikes blocks reviewer eligibility
- Tracked per wallet in `user_reputation.strikes`

### Reviewer Eligibility Requirements
All must be met simultaneously:
1. Reputation score ≥ 50
2. Account age ≥ 30 days
3. No slashing in last 30 days (`last_slash_at`)
4. Fewer than 3 active strikes in 30-day window

---

## 7. Report Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SUBMIT    │────▶│   REVIEW     │────▶│  MODERATE    │────▶│  FINALIZED   │
│             │     │              │     │              │     │              │
│ • Encrypt   │     │ • Reviewer   │     │ • Moderator  │     │ • Stakes     │
│ • IPFS      │     │   decision   │     │   final label│     │   settled    │
│ • DB save   │     │ • Support/   │     │ • Appeal     │     │ • Rep deltas │
│ • On-chain  │     │   Challenge  │     │   outcome    │     │   applied    │
│ • Key store │     │              │     │ • Malicious  │     │              │
└─────────────┘     └──────┬───────┘     │   flags      │     └──────────────┘
                           │             └──────────────┘
                    ┌──────┴───────┐
                    │   APPEAL     │
                    │ (Optional)   │
                    │ 8 COV bond   │
                    └──────────────┘
```

### Step 1: Report Submission
1. Reporter fills form (category, title, description, files, visibility)
2. Frontend generates AES-256-GCM encryption key
3. Report data encrypted with padding (64KB blocks for size obfuscation)
4. Fuzzy timestamp applied (±24h random offset for privacy)
5. Encrypted blob uploaded to IPFS → receives CID
6. CID hash computed: `keccak256(CID)`
7. On-chain: `CovertProtocol.createReport(visibility, contentHash)` — locks stake (10 or 6 COV)
8. Backend: `POST /api/v1/reports` with CID, hash, tx_hash, category, visibility, size
9. Evidence key stored: `POST /api/v1/reports/by-hash/{hash}/evidence-key` (only for PUBLIC/MODERATED)
10. Key also stored locally in encrypted form (localStorage)

### Step 2: Community Engagement (Optional)
- **Support:** Any user stakes 1 COV + reason hash → on-chain `support()`
- **Challenge:** Any user stakes 3 COV + reason hash → on-chain `challenge()`
- Mutual exclusivity: cannot support AND challenge same report
- Reporter cannot support/challenge own report

### Step 3: Reviewer Assessment
1. Reviewer fetches reports from chain (or DB fallback)
2. Decrypts evidence using stored AES key (fetched from backend)
3. Sets decision on-chain: `setReviewDecision(reportId, decision)`
4. Syncs decision to backend via `PATCH /api/v1/reports/by-hash/{hash}/status`
5. Decision stored in both chain and DB (`review_decision` column)

### Step 4: Appeal (Optional)
1. Reporter sees rejected/disputed decision
2. Generates `appealReasonHash = keccak256("appeal:" + hash + ":" + timestamp)`
3. On-chain: `appeal(reportId, appealReasonHash)` — locks 8 COV bond
4. Requires prior reviewer decision

### Step 5: Moderation & Finalization
1. Moderator reviews report + reviewer decision + community signals
2. Optionally marks specific challengers as malicious: `markMalicious(reportId, actor, true)`
3. Selects final label and appeal outcome
4. On-chain: `finalizeReport(reportId, finalLabel, appealOutcome)` — settles ALL stakes
5. Backend: `POST /api/v1/reports/by-hash/{hash}/finalize` — applies reputation deltas
6. Reviewer penalty applied if decision mismatches final label
7. Reviewer penalty applied if appeal outcome = APPEAL_WON
8. `covert:reports-updated` event dispatched for cross-dashboard sync

---

## 8. Smart Contracts

### 8.1 COVCredits (`contracts/src/COVCredits.sol`)

**Inherits:** `AccessControl`, `Pausable`

Non-transferable fungible credits. ERC20-like interface but all transfer/approve functions revert.

**Constants:**
- `WELCOME_GRANT` = 30 COV (30 × 10¹⁸ wei)
- `MAX_SUPPLY` = 100,000,000 COV
- `MINTER_ROLE`, `BURNER_ROLE`, `PAUSER_ROLE` (bytes32)

**State:**
- `balances[address]` — credit balance
- `welcomeClaimed[address]` — one-time grant flag
- `totalSupply` — total credits in circulation

**Key Functions:**
| Function | Access | Description |
|----------|--------|-------------|
| `grantWelcome(user)` | MINTER_ROLE | One-time 30 COV grant per user |
| `mint(to, amount)` | MINTER_ROLE | Mint arbitrary amount (bypasses welcomeClaimed) |
| `burn(from, amount)` | BURNER_ROLE | Burn credits (works even when paused) |
| `balanceOf(account)` | public view | Get balance |
| `pause()` / `unpause()` | PAUSER_ROLE | Pause/resume minting |

**Constructor grants:** `DEFAULT_ADMIN_ROLE`, `MINTER_ROLE`, `BURNER_ROLE`, `PAUSER_ROLE` to admin.

### 8.2 CovertBadges (`contracts/src/CovertBadges.sol`)

**Inherits:** `ERC721("COVERT Badge", "CBADGE")`, `AccessControl`

Soul-bound (non-transferable) NFT badges.

**Badge Types (enum):**
- `TIER_0_NEW` (0), `TIER_1_REGULAR` (1), `TIER_2_TRUSTED` (2), `TIER_3_POWER` (3)
- `REVIEWER_BADGE` (4), `MODERATOR_BADGE` (5)

**Key Functions:**
| Function | Access | Description |
|----------|--------|-------------|
| `mintBadge(user, badgeType)` | BADGE_MANAGER_ROLE | One per type per user |
| `setBadgeActive(user, type, active)` | BADGE_MANAGER_ROLE | Activate/deactivate without burning |
| `isBadgeActive(user, type)` | view | Check if badge exists and active |
| `getUserBadges(user)` | view | Returns all 6 badge types with status |

**Soul-bound enforcement:** `_update()` override blocks all transfers (from ≠ 0). `approve()` and `setApprovalForAll()` revert.

### 8.3 CovertProtocol (`contracts/src/CovertProtocol.sol`)

**Inherits:** `AccessControl`, `ReentrancyGuard`

Main protocol orchestrator. Manages reports, reviews, appeals, and stake settlement.

**Immutable References:** `COVCredits covCredits`, `CovertBadges covBadges`

**Roles:**
- `REVIEWER_ROLE` — Can set review decisions. Admin: `AUTOMATION_ROLE`
- `MODERATOR_ROLE` — Can finalize reports. Admin: `DEFAULT_ADMIN_ROLE`
- `AUTOMATION_ROLE` — Can grant/revoke REVIEWER_ROLE. Admin: `DEFAULT_ADMIN_ROLE`
- **Mutual exclusivity:** Cannot hold both REVIEWER_ROLE and MODERATOR_ROLE

**Enums:**
- `Visibility`: PUBLIC (0), PRIVATE (1)
- `ReviewerDecision`: NONE (0), NEEDS_EVIDENCE (1), REVIEW_PASSED (2), REJECT_SPAM (3)
- `FinalLabel`: UNREVIEWED (0), NEEDS_EVIDENCE (1), CORROBORATED (2), DISPUTED (3), FALSE_OR_MANIPULATED (4)
- `AppealOutcome`: NONE (0), APPEAL_WON (1), APPEAL_LOST (2), APPEAL_ABUSIVE (3)

**Report Struct:**
```solidity
struct Report {
    address reporter;
    Visibility visibility;
    bytes32 contentHash;
    FinalLabel finalLabel;
    ReviewerDecision reviewDecision;
    uint64 createdAt, reviewedAt, finalizedAt;
    bool hasAppeal;
    bytes32 appealReasonHash;
    uint256 lockedReportStake, lockedAppealBond;
}
```

**Core Functions:**

| Function | Access | Stakes | Description |
|----------|--------|--------|-------------|
| `claimWelcome()` | any | — | Claim 30 COV |
| `createReport(visibility, contentHash)` | any | 10/6 COV locked | Submit report |
| `support(reportId, reasonHash)` | any (not reporter) | 1 COV locked | Support report |
| `challenge(reportId, reasonHash)` | any (not reporter) | 3 COV locked | Challenge report |
| `setReviewDecision(reportId, decision)` | REVIEWER_ROLE | — | Set initial assessment |
| `appeal(reportId, appealReasonHash)` | reporter only | 8 COV locked | Appeal decision |
| `markMalicious(reportId, actor, bool)` | MODERATOR_ROLE | — | Flag actor |
| `finalizeReport(reportId, label, appeal)` | MODERATOR_ROLE | Settles all | Finalize & settle |

**View Functions:**
- `getReport(id)`, `getSupporters(id)`, `getChallengers(id)`
- `getSupporterCount(id)`, `getChallengerCount(id)`

### 8.4 CommitmentRegistry (`contracts/src/CommitmentRegistry.sol`)

Legacy contract for tamper-proof report commitments.

**Functions:**
- `commit(cidHash, visibility)` — Store commitment (one-time per hash)
- `deactivate(cidHash)` — Soft-delete (only original submitter)
- `getCommitment(cidHash)` — Read commitment
- `isActive(cidHash)` — Check active status

### 8.5 DailyAnchor (`contracts/src/DailyAnchor.sol`)

Anchors daily moderation Merkle roots on-chain.

**Events:** `AnchorSubmitted`, `OperatorAdded`, `OperatorRemoved`, `OwnershipTransferred`

**Errors:** `UnauthorizedOperator`, `AnchorAlreadyExists`, `OnlyOwner`, `ZeroAddress`

**Functions:**
- `submitAnchor(date, merkleRoot, actionCount)` — One per date (YYYYMMDD format)
- `verifyProof(date, proof[], leaf)` — Verify Merkle inclusion
- `addOperator(addr)` / `removeOperator(addr)` — Manage authorized submitters (zero-address check on add)
- `transferOwnership(newOwner)` — Transfer contract ownership (zero-address check)

### 8.6 Deployment Scripts

**`script/Deploy.s.sol`** — Full deployment:
1. Deploy CommitmentRegistry, DailyAnchor
2. Deploy COVCredits(deployer), CovertBadges(deployer)
3. Deploy CovertProtocol(deployer, treasury, covCredits, covBadges)
4. Grant MINTER_ROLE + BURNER_ROLE on COVCredits → CovertProtocol
5. Grant BADGE_MANAGER_ROLE on CovertBadges → automation wallet
6. Grant AUTOMATION_ROLE on CovertProtocol → automation wallet
7. Save deployment addresses to `deployments/{network}.json` and `.env`

**Private key handling:** Both `DeployLocalScript` and `DeployScript` use `vm.envOr("PRIVATE_KEY", <anvil-default>)` so the Anvil key is never required in production — set `PRIVATE_KEY` in the environment to override.

**Supported networks:** localhost (31337), base-sepolia (84532), base-mainnet (8453), sepolia (11155111), mainnet (1), polygon (137), polygon-mumbai (80001)

**`script/GrantRoles.s.sol`** — Dev role assignment:
- Deployer key loaded via `vm.envOr("PRIVATE_KEY", <anvil-default>)` inside `run()` (not a compile-time constant)
- REVIEWER_ROLE → accounts 2, 4
- MODERATOR_ROLE → accounts 3, 6, 9
- Revoke MODERATOR_ROLE from deployer (account 0)
- Mint SBT badges (REVIEWER_BADGE, MODERATOR_BADGE)

**`script/Reset.s.sol`** — Dev reset:
- Burns all existing COV from 10 test accounts
- Mints 30 COV to each account
- Re-grants REVIEWER_ROLE and MODERATOR_ROLE (idempotent)

---

## 9. Backend API

### Base URL: `/api/v1`

### 9.1 Reports (`/api/v1/reports`)

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/` | Submit new report | X-Wallet-Address |
| GET | `/` | List user's reports | X-Wallet-Address |
| GET | `/public` | List public reports | None |
| GET | `/all` | List all reports (reviewer/moderator) | None (frontend-gated) |
| GET | `/by-hash/{hash}` | Get report by commitment hash | None |
| PATCH | `/by-hash/{hash}/status` | Update status (sync on-chain decision) | None |
| POST | `/by-hash/{hash}/finalize` | Finalize + apply rep changes | None |
| POST | `/by-hash/{hash}/evidence-key` | Store AES-256 decryption key | Reporter only |
| GET | `/by-hash/{hash}/evidence-key` | Get decryption key | None (frontend-gated) |
| GET | `/{id}` | Get report by ID | Reporter only |
| DELETE | `/{id}` | Soft-delete report | Reporter only |
| POST | `/{id}/commit` | Update blockchain info | Reporter only |
| GET | `/{id}/status` | Get report status | None |

**Finalize Request Body:**
```json
{
  "status": "verified|rejected|disputed",
  "final_label": "CORROBORATED|NEEDS_EVIDENCE|DISPUTED|FALSE_OR_MANIPULATED",
  "reporter": "0x...",
  "appeal_outcome": "APPEAL_WON|APPEAL_LOST|APPEAL_ABUSIVE|null",
  "supporters": ["0x...", ...],
  "challengers": ["0x...", ...],
  "malicious_wallets": ["0x...", ...],
  "review_decision": "REVIEW_PASSED|NEEDS_EVIDENCE|REJECT_SPAM"
}
```

**Side Effects:**
- Applies reputation deltas to reporter, all supporters, all challengers
- Penalises reviewer if decision mismatches final label (-5 slash)
- Penalises reviewer if appeal outcome = APPEAL_WON (-5 slash)

### 9.2 Reputation (`/api/v1/reputation`)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/wallet/{address}` | Get wallet reputation |
| GET | `/reviewer-eligibility/{address}` | Check reviewer eligibility |
| GET | `/stats/{moderator_id}` | Get moderator stats |
| GET | `/leaderboard` | Top users by rep (limit, tier filter) |
| GET | `/flagged` | Wallets with active strikes |
| GET | `/reviewer-candidates` | Users meeting reviewer bar |
| GET | `/tiers` | Tier definitions + rep effect tables |
| POST | `/sync-reviewer-roles` | Auto-grant/revoke REVIEWER_ROLE |
| POST | `/dev-reset` | Reseed test account rep (dev only) |

### 9.3 ZKP (`/api/v1/zkp`)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/verify` | Verify ZK proof |
| POST | `/check-nullifier` | Check nullifier uniqueness |
| GET | `/rate-limit/{nullifier}` | Check rate limit |
| POST | `/submit-nullifier` | Register nullifier |
| GET | `/health` | ZKP system health |

### 9.4 Dead Man's Switch (`/api/v1/dms`)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/create` | Create DMS for report |
| POST | `/checkin` | Reporter check-in (prevents trigger) |
| POST | `/release` | Manual release |
| POST | `/cancel` | Cancel DMS |
| POST | `/emergency-override` | Admin override (release/cancel/extend) |
| GET | `/status/{dms_id}` | Get DMS status |
| GET | `/report/{report_id}` | Get DMS by report |
| GET | `/statistics` | System-wide stats |
| GET | `/watchdog/status` | Watchdog health |
| POST | `/watchdog/manual-trigger` | Force check cycle |
| GET | `/logs/{dms_id}` | Release logs |

### 9.5 Moderation Notes (`/api/v1/moderation/notes`)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/{report_id}` | Get notes for report |
| POST | `/{report_id}` | Create/update note (upsert) |
| DELETE | `/{report_id}` | Delete note by moderator_address |

### 9.6 AI Analysis (`/api/v1/ai`)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/analyze/credibility` | Score report credibility (0-1) |
| POST | `/analyze/anomalies` | Detect duplicates, bots, campaigns |
| POST | `/analyze/triage` | Priority classification |
| POST | `/analyze/batch` | Batch analysis |

### 9.7 Dev (`/api/v1/dev`) — Development Only

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/reset-all` | Clear all DB tables + reseed rep scores |

Enabled only when `DEBUG=true` or `ENVIRONMENT=development`.

Clears (in order): moderation_notes, moderation_logs, moderations, zkp_nullifiers, dms_messages, dms_channels, reports, user_reputation, moderators. Then calls `reputation_service.seed_dev_accounts()` to reseed rep scores.

---

## 10. Frontend Application

### 10.1 Routing

```
/                     → LandingPage (standalone, no layout)
/dashboard            → Dynamic: Moderator | Reviewer | Reporter dashboard
/submit               → SubmitReport (4-step form)
/my-reports           → MySubmissions (report list with filters)
/report/:id           → Report detail page
*                     → Redirect to /dashboard
```

Dashboard routing is role-based:
- `isModerator` → ProtocolModeratorDashboard
- `isReviewer` → ReviewerDashboard
- else → ReporterDashboard

### 10.2 Pages

**LandingPage** — Marketing page with animated blockchain canvas, feature showcase, "How It Works" timeline, CTA buttons.

**ReporterDashboard** — Public report feed with expandable cards showing support/challenge counts, evidence viewer, and staking buttons. Balance check before staking (1 COV support, 3 COV challenge). Shows 3 reports max to unauthenticated users.

**SubmitReport** — 4-step form: (1) Report Details, (2) Attachments, (3) Privacy/Visibility, (4) Review & Submit. Handles full encrypt → IPFS → blockchain → backend pipeline.

**ReviewerDashboard** — Tabbed interface: Queue, My Reviews, Accuracy, Community. Filters by decision status, sort by age/support count. Keyboard shortcuts (P/N/R). Batch decisions. Streak counter (localStorage). Eligibility panel with checklist. Accuracy tracking against final labels.

**ProtocolModeratorDashboard** — Tabbed interface: Queue, Appeals, Flagged, Reviewers, Audit Log. Filters by reviewer decision and appeal status. Confirmation modal with stake settlement preview and rep impact preview. Batch finalization. Flagged wallets tab. Reviewer candidates tab.

### 10.3 Key Components

| Component | Purpose |
|-----------|---------|
| `AppLayout` | Top nav with brand, links, dev toolbar, mobile menu |
| `WalletButton` | MetaMask connect/disconnect with balance display |
| `ProfileButton` | Role badge, rep score, COV balance, tier, badges |
| `DashboardWelcome` | One-time role-specific onboarding panel |
| `EvidenceViewer` | Fetch key → retrieve IPFS → decrypt → show files |
| `PlatformInfoPanel` | Slide-over drawer with protocol guide |
| `ReportSubmissionForm` | 4-step encrypted report submission |
| `FileUpload` | Drag-drop file upload with encryption badges |
| `MySubmissions` | Report list with filters, delete, appeal |
| `ReportCard` | Expandable report card with status badges |

### 10.4 Services

**web3Service** (`services/web3.ts`) — MetaMask connection, network switching, CommitmentRegistry + DailyAnchor interaction. Dev-mode simulation for local testing. All async functions wrapped in try/catch with `[web3]` console prefix — read functions return safe defaults (null/0/false), write functions re-throw.

**protocolService** (`services/protocol.ts`) — CovertProtocol + COVCredits + CovertBadges interaction. All report lifecycle on-chain operations. All async functions wrapped in try/catch with `[protocol]` console prefix.

**encryptionService** (`services/encryption.ts`) — AES-256-GCM encryption/decryption. 64KB block padding. PBKDF2 key derivation. Key storage in localStorage. All async functions wrapped in try/catch with `[encryption]` console prefix — `retrieveKey()` returns null on error, others re-throw.

**ipfsService** (`services/ipfs.ts`) — Upload to NFT.Storage / web3.storage / local IPFS. Dev-mode IndexedDB fallback. Retry with exponential backoff.

### 10.5 State Management (Zustand + localStorage)

| Store | Key | Purpose |
|-------|-----|---------|
| `reportStore` | `covert-reports-v3` | Report list, draft, submission progress, filters |
| `covBalanceStore` | `covert-cov-balances-v2` | Per-wallet COV balances |
| `reviewDecisionStore` | `covert-review-decisions-v1` | Vote tallies, settlement tracking |
| `walletSessionStore` | `covert-wallet-session-v1` | 24h wallet session persistence |

### 10.6 Hooks

**`useWeb3`** — Wallet connection, session restoration, network switching, report commitment. Auto-claims welcome grant. Configures web3Service and protocolService with contract addresses from env vars.

**`useRoleAccess`** — Determines reviewer/moderator status from on-chain badges (prod) or address config (dev). Syncs COV balance. Fetches reputation. Polls every 60s. Listens for `covert:rep-refresh` events.

### 10.7 Cross-Dashboard Synchronisation

| Mechanism | Interval | Scope |
|-----------|----------|-------|
| `covert:reports-updated` CustomEvent | On action | Same tab |
| `covert:rep-refresh` CustomEvent | On action | Same tab |
| MySubmissions polling | 30 seconds | Reports list |
| useRoleAccess polling | 60 seconds | Rep + balance |
| Visibility gate | `document.visibilityState === 'visible'` | All polling |

---

## 11. Database Schema

### Tables

**`reports`** — Main report storage
- `id` (UUID PK), `commitment_hash` (unique), `transaction_hash`, `block_number`, `chain_id`
- `ipfs_cid` (unique), `encrypted_category`, `encrypted_title`, `encrypted_summary`
- `file_size`, `file_type`, `visibility` (enum), `status` (enum), `anonymous` (bool)
- `verification_score` (0.00-1.00), `risk_level` (enum)
- `reporter_nullifier`, `reporter_commitment`, `burner_address`
- `evidence_key` (AES-256 hex), `reviewer_address`, `review_decision` (string)
- `dms_enabled`, `dms_trigger_date`, `dms_released`
- `created_at`, `updated_at`, `deleted_at` (soft delete)

**`report_logs`** — Audit trail
- `report_id` (FK), `actor_id`, `event_type` (enum), `event_data` (JSONB)
- `field_changed`, `old_value`, `new_value`

**`user_reputation`** — Wallet reputation
- `wallet_address` (unique), `reputation_score`, `tier` (tier_0–tier_3)
- `strikes`, `last_strike_at`, `last_slash_at`, `account_created_at`

**`moderators`** — Moderator profiles
- `wallet_address` (unique), `reputation_score`, `tier` (bronze–platinum)
- `total_reviews`, `accurate_reviews`, `disputed_reviews`
- `is_active`, `suspension_until`, `expertise_areas` (JSONB)

**`moderations`** — Moderation actions
- `report_id` (FK), `moderator_id` (FK), `action`, `decision`
- `encrypted_notes`, `ai_recommendation`, `ai_confidence`

**`moderation_notes`** — Free-text notes per (report, moderator)
- `report_id`, `moderator_address`, `content`
- Unique constraint on (report_id, moderator_address)

**`zkp_nullifiers`** — Anti-double-reporting
- `nullifier` (unique), `commitment`, `usage_count`, `daily_report_count`

**`anchors`** — Daily Merkle roots
- `merkle_root`, `transaction_hash`, `anchor_date`, `report_count`

**`dead_mans_switches`** — DMS configuration
- `report_id` (FK unique), `trigger_type`, `trigger_date`, `status`
- `auto_release_public`, `auto_pin_ipfs`, `notify_contacts`

**`dms_check_ins`** — Check-in records
**`dms_release_logs`** — Release attempt logs

### Migrations (Alembic)
1. `001` — Initial reports schema
2. `002` — Moderators + moderations
3. `003` — Drop reputation token_id
4. `004` — User reputation table
5. `005` — Moderation notes
6. `006` — Drop reporter_nullifier unique constraint
7. `007` — Add evidence_key column
8. `008` — Dead Man's Switch tables
9. `009` — Reviewer address + review_decision columns

---

## 12. Encryption & Privacy

### Client-Side Encryption Pipeline
1. **Key generation:** `crypto.getRandomValues()` → 256-bit AES key
2. **Padding:** Report data padded to 64KB blocks with random bytes (size obfuscation)
3. **Encryption:** AES-256-GCM with 12-byte IV, producing ciphertext + 16-byte auth tag
4. **Timestamp fuzzing:** ±24 hour random offset on submission timestamp
5. **IPFS upload:** Encrypted blob uploaded (CID is content-addressed hash of ciphertext)

### Key Management
- **Reporter:** Holds raw AES key. Encrypted with wallet-derived key (PBKDF2 from wallet signature), stored in localStorage.
- **Evidence Key API:** Reporter can store hex key via `POST /evidence-key`. Reviewers/moderators fetch via `GET /evidence-key`.
- **Decryption:** Evidence viewer fetches key from API → retrieves encrypted blob from IPFS → decrypts in-browser.
- **Private reports:** No evidence key shared. Only reporter can decrypt.

### Privacy Guarantees
- No plaintext on server or chain — only encrypted blobs on IPFS
- CID hash on chain reveals nothing about content
- Reporter nullifier provides unlinkable identity across reports
- Burner wallet pattern available for on-chain privacy
- Fuzzy timestamps prevent temporal correlation

---

## 13. Dead Man's Switch (DMS)

### Purpose
Automatic release mechanism for reports if the reporter becomes unable to check in (incapacitation, coercion, etc.).

### Trigger Types
- `TIME_BASED` — Release at specific date/time
- `ACTIVITY_BASED` — Release after N days of inactivity
- `MANUAL` — Reporter-triggered release
- `EMERGENCY` — Admin override

### Lifecycle
1. Reporter creates DMS: `POST /api/v1/dms/create` with trigger_date
2. Reporter periodically checks in: `POST /api/v1/dms/checkin` (resets timer, can extend trigger_date)
3. If trigger_date passes without check-in:
   - Watchdog service detects trigger
   - Report visibility → PUBLIC
   - Optional: Pin to IPFS, post blockchain notification, send contact notifications
4. Reporter can manually release or cancel at any time

### Status Flow
`ACTIVE` → `TRIGGERED` → `RELEASED` (or `FAILED`)
`ACTIVE` → `CANCELLED`
`ACTIVE` → `EXTENDED` → (back to normal monitoring)

### Configuration
- `auto_release_public`: Make report PUBLIC on trigger (default: true)
- `auto_pin_ipfs`: Pin to IPFS on release (default: true)
- `notify_contacts`: Send encrypted contact notifications (default: false)
- `max_retry_attempts`: 3
- `retry_delay_minutes`: 30

---

## 14. AI Analysis Services

### Credibility Scorer
- Scores report text on: quality, claim specificity, linguistic patterns, metadata
- Returns: `credibility_score` (0-1), `confidence` (0-1), `risk_level`, `flags[]`, `reasoning`

### Anomaly Detector
- Detects: duplicate content, temporal submission spikes, bot-like patterns, coordinated campaigns

### Report Triager
- Priority classification: `urgent`, `high`, `medium`, `low`, `auto_reject`
- Uses: text analysis, submission patterns, metadata signals

### Feature Extractor
- Extracts features from report text for ML pipelines

**Note:** Current AI services use rule-based heuristics (TextBlob, NLTK). No external LLM API calls.

---

## 15. Environment & Configuration

### Root `.env` Variables

```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Backend
SECRET_KEY=your-secret-key-here
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+asyncpg://covert_user:covert_password@localhost:5432/covert_db
REDIS_URL=redis://localhost:6379/0

# IPFS
IPFS_API_URL=/ip4/127.0.0.1/tcp/5001
IPFS_GATEWAY_URL=http://localhost:8080
PINATA_API_KEY=
WEB3_STORAGE_TOKEN=

# Blockchain
RPC_URL=http://localhost:8545
CHAIN_ID=31337
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Contract Addresses (fill after deployment)
COMMITMENT_REGISTRY_ADDRESS=0x...
DAILY_ANCHOR_ADDRESS=0x...
COV_CREDITS_ADDRESS=0x...
COVERT_BADGES_ADDRESS=0x...
COVERT_PROTOCOL_ADDRESS=0x...

# Automation
AUTOMATION_PRIVATE_KEY=  # For reviewer role management

# Frontend (Vite)
VITE_DEV_MODE=true
VITE_API_URL=http://localhost:8000
VITE_RPC_URL=http://localhost:8545
VITE_CHAIN_ID=31337
VITE_COMMITMENT_REGISTRY_ADDRESS=0x...
VITE_DAILY_ANCHOR_ADDRESS=0x...
VITE_COV_CREDITS_ADDRESS=0x...
VITE_COVERT_BADGES_ADDRESS=0x...
VITE_COVERT_PROTOCOL_ADDRESS=0x...
VITE_IPFS_GATEWAY=http://localhost:8080

# Rate Limiting
RATE_LIMIT_SUBMISSIONS=10
RATE_LIMIT_GENERAL=100

# File Upload
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.pdf,.mp4,.zip
```

### Frontend Config (`frontend/src/config.ts`)

All frontend environment variables are read in a single centralised file and imported elsewhere:

```typescript
export const API_BASE = import.meta.env.VITE_API_URL || '';
export const IS_DEV = import.meta.env.VITE_DEV_MODE === 'true';
export const CHAIN_ID = import.meta.env.VITE_CHAIN_ID || '84532';
export const RPC_URL = import.meta.env.VITE_RPC_URL || '';
export const IPFS_GATEWAY = import.meta.env.VITE_IPFS_GATEWAY || 'https://nftstorage.link/ipfs';
```

**No `localhost` fallbacks in frontend code.** If `VITE_API_URL` is unset, `API_BASE` defaults to `''` (same-origin), ensuring production deployments never accidentally hit localhost.

### Backend Config (`backend/app/core/config.py`)
- CORS origins: `http://localhost:5173`, `http://localhost:3000`, `https://covert-chi.vercel.app`
- CORS validator always appends `https://covert-chi.vercel.app` even if overridden by env var
- Global exception handler in `main.py` ensures CORS headers appear on 500 errors
- JWT: HS256, 7-day expiry (SIWE-based authentication)
- DB pool: size=20, max_overflow=40, pre_ping=true
- GZip compression for responses > 1000 bytes
- `@validator("SECRET_KEY")` — raises `ValueError` if default key is used when `ENVIRONMENT=production`
- Dev-only endpoints (e.g. `/dev-reset`) require **both** `DEBUG=true` **and** `ENVIRONMENT=development` (AND logic)

### Foundry Config (`contracts/foundry.toml`)
- Solidity 0.8.20, optimizer 200 runs, EVM target: paris
- Remappings: forge-std, @openzeppelin/contracts
- RPC endpoints for localhost, sepolia, base_sepolia, base

---

## 16. Deployment & Production

### Smart Contracts

**Local (Anvil):**
```bash
cd contracts
anvil                                                    # Start local chain
forge script script/Deploy.s.sol --rpc-url localhost --broadcast
forge script script/GrantRoles.s.sol --rpc-url localhost --broadcast
```

**Testnet (Base Sepolia) — CURRENTLY DEPLOYED:**
```bash
cd contracts
forge script script/Deploy.s.sol --tc DeployScript --rpc-url https://sepolia.base.org --broadcast
forge script script/GrantRolesTestnet.s.sol --rpc-url https://sepolia.base.org --broadcast
```

Deployed addresses saved in `contracts/deployments/base-sepolia.json`:
```
CommitmentRegistry: 0x5147e66507b0797E1E39FC7C052e465176D9bF1E
DailyAnchor:        0x5D55b7C08e45F467eE1F3F212663cE6eb9ef6428
COVCredits:         0x6ea581d247A8A43BC8544b788f9e100895099903
CovertBadges:       0x81ec2Fe3467535fd8e3A8a5bc00Bc226f2fedda4
CovertProtocol:     0x5B7AB21B2656BD187c3B544937eac9f36d901CbA
```

`GrantRolesTestnet.s.sol` grants both AccessControl roles on CovertProtocol AND mints SBT badges on CovertBadges for 2 reviewers and 2 moderators.

Testnet wallet addresses configured in `contracts/.env`:
| Env Var | Address | Role |
|---------|---------|------|
| REVIEWER_ADDRESS_1 | `0xc1a6EDea015AdcE9f56E84DA1C81E11b654E8cf1` | Reviewer |
| REVIEWER_ADDRESS_2 | `0x52e0ec9dcfF2FF7082927414cEe58F4Aac976C03` | Reviewer |
| MODERATOR_ADDRESS_1 | `0xa429C534cF66A83bFbFFF1163ce4e7c4f907f136` | Moderator |
| MODERATOR_ADDRESS_2 | `0xE06C3F820586b4e31C001565b4eB9D18fBB0C0C7` | Moderator |

**Mainnet (Base):**
```bash
forge script script/Deploy.s.sol --rpc-url $BASE_RPC_URL --broadcast --verify
```

After deployment, update `.env` with contract addresses from `deployments/{network}.json`.

### Backend — CURRENTLY DEPLOYED ON RAILWAY

**Local:**
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head           # Run all migrations
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Railway deployment:**
- `Procfile` runs `release: alembic upgrade head` before starting the web process
- `runtime.txt` specifies `python-3.12.7`
- DATABASE_URL configured as Railway env var
- CORS always includes `https://covert-chi.vercel.app`

**Production considerations:**
- Set `ENVIRONMENT=production`, `DEBUG=false`
- Use a real `SECRET_KEY` (the app will refuse to start if the default key is used in production)
- Configure CORS for production domain
- Set up PostgreSQL with proper credentials
- Configure Redis for caching/rate limiting
- Set up Sentry DSN for error monitoring
- Run behind a reverse proxy (nginx/Caddy)
- Use HTTPS
- Set `AUTOMATION_PRIVATE_KEY` for reviewer role automation

**Startup resilience:** `init_db()` retries up to 10 times with linear backoff (capped at 30s) when PostgreSQL isn't ready, avoiding crashes on platforms like Railway where the database may start after the app.

**Chain ID:** `report_service.py` reads `chain_id` from `settings.CHAIN_ID` (not hardcoded to 31337), so the backend works on any target chain without code changes.

### Frontend — CURRENTLY DEPLOYED ON VERCEL

**Production URL:** `https://covert-chi.vercel.app`

```bash
cd frontend
npm install
npm run build                  # Production build
# Serve dist/ folder
```

**Vercel deployment:**
- Auto-deploys from `main` branch
- All `VITE_*` env vars must be set in Vercel dashboard (baked at build time)
- Requires redeploy after changing env vars

**Production considerations:**
- Set `VITE_DEV_MODE=false`
- Update all `VITE_*` contract addresses for target network
- Update `VITE_API_URL` for production backend (Railway URL)
- Update `VITE_RPC_URL` for production RPC (currently `https://sepolia.base.org`)
- Update `VITE_CHAIN_ID` (currently `84532` for Base Sepolia)
- Set `VITE_PINATA_API_KEY` and `VITE_PINATA_API_SECRET` for IPFS uploads

### Authentication & Access Control (Status)
- [x] **SIWE (EIP-4361) authentication implemented** — frontend signs message, backend verifies and issues JWT
- [x] **Backend RBAC implemented** — `rbac.py` verifies on-chain roles for reviewer/moderator endpoints
- [x] **JWT-based auth** — `get_current_wallet` dependency extracts wallet from JWT
- [ ] Evidence key endpoint currently checks reporter ownership but not JWT auth
- [ ] Some endpoints still accept `X-Wallet-Address` header as fallback

---

## 17. Development Setup & Scripts

### Prerequisites
- Node.js 18+, npm
- Python 3.10+, pip
- PostgreSQL 14+
- Redis 7+
- Foundry (forge, anvil, cast)
- MetaMask browser extension

### Quick Start

```bash
# 1. Start local blockchain
cd contracts && anvil

# 2. Deploy contracts (new terminal)
cd contracts
forge script script/Deploy.s.sol --rpc-url localhost --broadcast
forge script script/GrantRoles.s.sol --rpc-url localhost --broadcast

# 3. Start backend (new terminal)
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Start frontend (new terminal)
cd frontend
npm install && npm run dev
```

### Dev Reset (Full State Wipe)

**Step 1 — DB Reset:** Navigate to `http://localhost:8000/api/docs` → `POST /api/v1/dev/reset-all`

This clears all DB tables and reseeds rep scores (users=0, reviewers=50, moderators=90).

**Step 2 — On-chain Reset:**
```bash
cd contracts
forge script script/Reset.s.sol --rpc-url http://localhost:8545 --broadcast
```

This burns all COV balances and mints 30 COV to each of the 10 test accounts, then re-grants on-chain roles.

### MetaMask Setup for Local Dev
1. Add network: RPC URL `http://localhost:8545`, Chain ID `31337`
2. Import test accounts using Anvil private keys
3. Account 0 is deployer/admin, 2/4 are reviewers, 3/6/9 are moderators

---

## 18. Implementation Status

### Fully Implemented
- Client-side AES-256-GCM encryption with padding
- IPFS upload (local, NFT.Storage, web3.storage, Pinata, dev-mode IndexedDB)
- On-chain commitment tracking (CommitmentRegistry)
- COV token system (mint, burn, welcome grant, non-transferable)
- Soul-bound badge NFTs (CovertBadges)
- Full report lifecycle on-chain (create, support, challenge, review, appeal, finalize)
- Stake locking and settlement (burn-on-lock, mint-on-return/slash)
- Role-based access control with mutual exclusivity
- Reputation system with tiers, deltas, slashing, strikes
- Reviewer eligibility checks
- Multi-dashboard UI (Reporter, Reviewer, Moderator)
- Evidence viewer with in-browser decryption
- Review decision syncing (on-chain → DB)
- Moderation notes (auto-saved, per report + moderator)
- Batch review decisions and batch finalization
- Cross-dashboard polling (30s reports, 60s rep/balance)
- Support/challenge balance checks before staking
- Reviewer penalty on appeal won
- Reviewer penalty on decision mismatch
- Report appeal UI
- Dev reset endpoint (DB + on-chain)
- DMS data models and API endpoints
- AI analysis endpoints (rule-based)
- Daily Merkle anchoring (DailyAnchor contract)
- **SIWE (Sign-In with Ethereum) authentication** — JWT-based, wallet signature verified
- **Backend RBAC** — on-chain role verification for reviewer/moderator endpoints (`rbac.py`)
- **Safe submission flow** — backend-first, blockchain-second (prevents COV lock on failed submissions)
- **Base Sepolia deployment** — all 5 contracts deployed with role grants + badge minting
- **Vercel frontend deployment** with CORS auto-configured
- **Railway backend deployment** with Procfile and release-phase Alembic migrations
- **Department routing** for corroborated reports

### Partially Implemented / In Progress
- **DMS Watchdog:** Background worker models and service stubs exist, but no actual background task runner (Celery worker not configured)
- **ZKP Verification:** Backend endpoint exists but verifier is a stub (always returns valid in dev)
- **AI Analysis:** Rule-based heuristics only, no ML model integration
- **Reviewer Role Automation:** Backend endpoint exists (`POST /sync-reviewer-roles`), blockchain service has methods, but no scheduled execution

### Not Yet Implemented
- **WebSocket real-time updates:** Currently using polling (30-60s intervals)
- **Rate limiting enforcement:** Configuration exists but not wired to Redis
- **Notification system:** DMS contact notifications are stub implementations
- **Governance / voting:** No on-chain governance mechanism
- **Dispute resolution workflow:** Beyond appeal, no formal dispute resolution
- **Reporter reward distribution:** No automatic COV rewards for reporters post-finalization
- **Multi-moderator consensus tracking:** REVIEW_REQUIREMENTS.minModerators=2 defined but not enforced on-chain
- **Badge tier auto-promotion:** Tier badges defined but not automatically minted based on rep score changes

---

## 19. Production Readiness Checklist

### Security (Critical)
- [x] Implement wallet signature verification (EIP-4361 / Sign-In with Ethereum) — `useWeb3.ts` + `auth.py`
- [x] Add backend RBAC middleware (verify on-chain roles for protected endpoints) — `rbac.py`
- [ ] Audit evidence-key endpoint (currently no auth beyond reporter ownership)
- [ ] Audit all PATCH/POST/DELETE endpoints for proper auth
- [ ] Rate limiting via Redis (currently config-only)
- [ ] Input sanitisation (bleach, python-magic for file validation)
- [ ] Smart contract audit (professional audit firm)
- [x] Foundry scripts use `vm.envOr()` — Anvil key is only a fallback, never required
- [x] `SECRET_KEY` validator blocks default value in production
- [x] Dev-reset endpoint uses AND logic (both DEBUG + ENVIRONMENT must match)
- [x] DailyAnchor: `transferOwnership()` + zero-address checks added
- [x] `.env` removed from git tracking

### Code Quality (Completed)
- [x] Centralised frontend config (`frontend/src/config.ts`) — all env vars read in one place
- [x] Eliminated all hardcoded `localhost:8000` fallbacks from frontend
- [x] `chain_id` in `report_service.py` reads from `settings.CHAIN_ID` (not hardcoded 31337)
- [x] Database `init_db()` retries up to 10× with backoff for Railway-style cold starts
- [x] `web3.ts` — all 6 async functions wrapped in try/catch with safe defaults
- [x] `encryption.ts` — all 7 async functions wrapped in try/catch with safe defaults
- [x] `protocol.ts` — all async functions wrapped in try/catch

### Infrastructure
- [ ] Production PostgreSQL with connection pooling
- [ ] Redis for rate limiting + caching
- [ ] HTTPS everywhere (TLS certificates)
- [ ] Reverse proxy (nginx/Caddy) with security headers
- [x] CORS restricted to production domains — Vercel origin always included via validator
- [ ] Environment variable management (Vault, AWS SSM, etc.)
- [ ] Container orchestration (Docker Compose / Kubernetes)
- [ ] CI/CD pipeline (build, test, deploy)

### Blockchain
- [ ] Production RPC provider (Alchemy, Infura, QuickNode)
- [ ] Contract verification on block explorer (Basescan)
- [ ] Multisig for admin/treasury wallet
- [ ] AUTOMATION_PRIVATE_KEY in secure storage (not .env)
- [ ] Gas estimation and fee management
- [ ] Event indexing (subgraph or custom indexer)

### IPFS / Storage
- [ ] Production pinning service (Pinata, web3.storage)
- [ ] Pin redundancy (multiple providers)
- [ ] CID garbage collection policy
- [ ] Backup strategy for encrypted blobs

### Monitoring
- [ ] Sentry DSN configured for error tracking
- [ ] Prometheus metrics exported
- [ ] Uptime monitoring for backend, IPFS gateway, RPC
- [ ] Alerting for DMS watchdog failures
- [ ] Blockchain event monitoring (missed finalisations)

### Data
- [ ] Database backups and point-in-time recovery
- [ ] Alembic migration testing on production schema
- [ ] Data retention policy
- [ ] GDPR / data deletion compliance

### Testing
- [ ] Unit tests for backend services
- [ ] Integration tests for API endpoints
- [ ] Smart contract test suite (already exists in Foundry)
- [ ] Frontend E2E tests
- [ ] Load testing for API endpoints
- [ ] Chaos testing for DMS reliability

---

*Last updated: 2026-03-25. Major updates: SIWE authentication, backend RBAC, safe submission flow (backend-first), Base Sepolia deployment with role grants + badge minting, Railway/Vercel deployment, CORS fixes, tx_hash made optional, chain_id constraint updated.*
