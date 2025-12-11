# C.O.V.E.R.T System Architecture
## Detailed Technical Design Document

---

## 🏛️ High-Level Architecture

### Layer Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Web App    │  │  PWA Mobile  │  │  Public Verifier   │   │
│  │  (React)    │  │  (React)     │  │  (Static Site)     │   │
│  └─────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                              ↕
┌────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Client-Side Encryption (AES-GCM, Web Crypto API)      │  │
│  │  Key Management (Shamir, Social Recovery)               │  │
│  │  Metadata Scrubbing (EXIF, Timestamps)                  │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────┬──────────────────┬─────────────────────────┐
│   BLOCKCHAIN     │   STORAGE        │   APPLICATION           │
│   LAYER          │   LAYER          │   LAYER                 │
│                  │                  │                         │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌────────────────────┐ │
│ │Smart Contracts│ │ │ IPFS (Kubo) │ │ │ FastAPI Backend    │ │
│ │ - Commitment │ │ │ - Encrypted  │ │ │ - Workflow Engine  │ │
│ │ - Reputation │ │ │   Reports    │ │ │ - Status Tracking  │ │
│ │ - Governance │ │ │ - Evidence   │ │ │ - API Gateway      │ │
│ └──────────────┘ │ └──────────────┘ │ └────────────────────┘ │
│        ↕         │        ↕         │          ↕              │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌────────────────────┐ │
│ │ Base Sepolia │ │ │Pinata/Web3   │ │ │ PostgreSQL         │ │
│ │   (Testnet)  │ │ │ Storage      │ │ │ - Reports Index    │ │
│ └──────────────┘ │ └──────────────┘ │ │ - User Pseudonyms  │ │
│                  │                  │ │ - Mod Actions      │ │
│                  │                  │ └────────────────────┘ │
└──────────────────┴──────────────────┴─────────────────────────┘
                              ↕
┌────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Reputation   │  │  DAO Voting  │  │  Jury Selection   │   │
│  │ System (SBT) │  │  (Quadratic) │  │  (VRF-based)      │   │
│  └──────────────┘  └──────────────┘  └───────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### 1. Report Submission Flow

```
┌──────────┐
│ Reporter │
└─────┬────┘
      │ 1. Fill Form (Title, Category, Description, Files)
      ↓
┌─────────────────┐
│ Browser (React) │
└────────┬────────┘
         │ 2. Generate Random AES Key (256-bit)
         │ 3. Encrypt Report + Files (AES-GCM)
         │ 4. Scrub Metadata (EXIF, Timestamps)
         │ 5. Pad to Fixed Size Blocks
         ↓
┌─────────────────────────┐
│ IPFS Client (In-Browser)│
└────────┬────────────────┘
         │ 6. Upload Encrypted Blob
         │ 7. Receive CID (bafy...)
         ↓
┌─────────────────────┐
│ Crypto Module       │
└────────┬────────────┘
         │ 8. Hash CID → cidHash (SHA-256)
         │ 9. Store Key in Local Storage (encrypted)
         ↓
┌──────────────────────┐
│ Smart Contract       │
│ (CommitmentRegistry) │
└────────┬─────────────┘
         │ 10. Call commit(cidHash, visibility)
         │ 11. Emit SubmissionEvent
         │ 12. Return Transaction Hash
         ↓
┌─────────────────────┐
│ Backend API         │
│ (FastAPI)           │
└────────┬────────────┘
         │ 13. Listen to Event
         │ 14. Insert into reports table
         │ 15. Status = "submitted"
         ↓
┌─────────────────────┐
│ Reporter Dashboard  │
└─────────────────────┘
    Display: "Report Submitted Successfully"
    Show: CID, TxHash, Timestamp
```

### 2. Moderation Review Flow

```
┌───────────┐
│ Moderator │
└─────┬─────┘
      │ 1. Load Review Queue (from DB)
      ↓
┌──────────────────┐
│ Moderator Console│
└────────┬─────────┘
         │ 2. View Report Card (Metadata Only)
         │    - Category, Timestamp, Size
         │    - Risk Flags (AI-generated)
         │    - Reporter Pseudonym Reputation
         ↓
┌────────────────────┐
│ Decision Logic     │
└────────┬───────────┘
         │ 3. Choose Action:
         │    - Accept
         │    - Reject
         │    - Need More Info
         │    - Escalate to Jury
         ↓
┌─────────────────────────┐
│ Backend API             │
└────────┬────────────────┘
         │ 4. Record Action in mod_actions table
         │ 5. Encrypt Moderator Notes (Group Key)
         │ 6. Update Report Status
         ↓
┌──────────────────────────┐
│ Reputation System        │
└────────┬─────────────────┘
         │ 7. Update Reporter Reputation Score
         │ 8. Update Moderator Reputation
         │ 9. Mint/Update Reputation SBT (if threshold)
         ↓
┌──────────────────────────┐
│ Notification Service     │
└────────┬─────────────────┘
         │ 10. Emit Status Change Event
         │ 11. Update Reporter Dashboard
         ↓
┌──────────────────────────┐
│ Daily Anchor (Optional)  │
└──────────────────────────┘
    12. Hash all day's actions
    13. Store merkle root on-chain
```

### 3. Dispute Resolution Flow

```
┌──────────────┐
│ Disputer     │
│ (Reporter or │
│  Community)  │
└──────┬───────┘
       │ 1. Challenge Moderator Decision
       ↓
┌──────────────────────┐
│ Smart Contract       │
│ (DisputeResolution)  │
└──────┬───────────────┘
       │ 2. Emit DisputeCreated Event
       │ 3. Lock Disputer's Reputation Stake
       ↓
┌──────────────────────┐
│ VRF (Chainlink)      │
└──────┬───────────────┘
       │ 4. Request Random Number
       │ 5. Select 7 Jurors (Reputation-Weighted)
       ↓
┌──────────────────────┐
│ Jury Notification    │
└──────┬───────────────┘
       │ 6. Notify Selected Jurors (On-Chain Events)
       │ 7. Jurors Stake Reputation to Accept
       ↓
┌──────────────────────┐
│ Encrypted Case Data  │
└──────┬───────────────┘
       │ 8. Share Report Key (Re-Encrypted for Jurors)
       │ 9. Jurors Review Anonymously
       ↓
┌──────────────────────┐
│ Private Voting       │
│ (Commit-Reveal)      │
└──────┬───────────────┘
       │ 10. Commit Phase (Hash Vote + Salt)
       │ 11. Reveal Phase (Submit Vote + Salt)
       │ 12. Tally Votes (Majority Wins)
       ↓
┌──────────────────────┐
│ Outcome Execution    │
└──────┬───────────────┘
       │ 13. If Disputer Wins:
       │     - Revert Moderator Decision
       │     - Slash Moderator Reputation
       │     - Return Disputer Stake + Reward
       │ 14. If Moderator Wins:
       │     - Slash Disputer Stake
       │     - Reward Moderator + Jurors
       ↓
┌──────────────────────┐
│ State Update         │
└──────────────────────┘
    15. Update Report Status
    16. Record Verdict on-chain
    17. Update All Reputation Scores
```

---

## 🗄️ Database Schema (PostgreSQL)

### Core Tables

```sql
-- Users (Pseudonymous)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT UNIQUE NOT NULL,  -- Burner wallet
    pseudonym TEXT UNIQUE NOT NULL,        -- Generated random name
    reputation_score INTEGER DEFAULT 0,
    reputation_level TEXT DEFAULT 'basic', -- basic|trusted|validator|juror|council
    sbt_token_id BIGINT,                   -- Reputation SBT ID
    vouched_by UUID REFERENCES users(id),  -- Sponsor
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Reports Index (No Plaintext Content)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cid TEXT NOT NULL,                     -- IPFS CID
    cid_hash TEXT UNIQUE NOT NULL,         -- SHA-256 of CID (on-chain)
    tx_hash TEXT UNIQUE NOT NULL,          -- Blockchain tx
    reporter_id UUID REFERENCES users(id),
    category TEXT NOT NULL,                -- corruption|harassment|fraud|etc
    visibility TEXT DEFAULT 'public',      -- public|moderated|restricted
    status TEXT DEFAULT 'submitted',       -- submitted|reviewing|accepted|rejected|disputed
    size_bytes INTEGER,
    risk_flags JSONB DEFAULT '[]',         -- AI-generated flags
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    moderator_id UUID REFERENCES users(id),
    jury_verdict TEXT,                     -- If disputed
    impact_score INTEGER DEFAULT 0,        -- Community-assessed impact
    view_count INTEGER DEFAULT 0
);

-- Moderation Actions (Encrypted Notes)
CREATE TABLE mod_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id),
    moderator_id UUID REFERENCES users(id),
    action TEXT NOT NULL,                  -- accept|reject|need_info|escalate
    encrypted_notes TEXT,                  -- Encrypted with group key
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reputation_change INTEGER DEFAULT 0
);

-- Disputes
CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id),
    disputer_id UUID REFERENCES users(id),
    challenged_action_id UUID REFERENCES mod_actions(id),
    stake_amount INTEGER NOT NULL,         -- Reputation staked
    status TEXT DEFAULT 'open',            -- open|voting|resolved
    jury_members JSONB,                    -- Array of juror IDs
    verdict TEXT,                          -- uphold|overturn
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Votes (Commit-Reveal)
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID REFERENCES disputes(id),
    juror_id UUID REFERENCES users(id),
    commit_hash TEXT NOT NULL,             -- Hash(vote + salt)
    reveal_vote TEXT,                      -- uphold|overturn (revealed later)
    reveal_salt TEXT,
    committed_at TIMESTAMPTZ DEFAULT NOW(),
    revealed_at TIMESTAMPTZ,
    UNIQUE(dispute_id, juror_id)
);

-- Reputation Events (Audit Trail)
CREATE TABLE reputation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    event_type TEXT NOT NULL,              -- report_validated|vote_correct|slashed
    amount INTEGER NOT NULL,               -- +/- reputation
    reason TEXT,
    related_report_id UUID REFERENCES reports(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Share Access (Selective Disclosure)
CREATE TABLE shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id),
    shared_by UUID REFERENCES users(id),
    viewer_pubkey TEXT NOT NULL,           -- Viewer's public key
    encrypted_key_bundle TEXT NOT NULL,    -- Report key re-encrypted
    access_granted_at TIMESTAMPTZ DEFAULT NOW(),
    access_expires_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0
);

-- Daily Anchors (Optional Integrity)
CREATE TABLE daily_anchors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anchor_date DATE UNIQUE NOT NULL,
    merkle_root TEXT NOT NULL,             -- Hash of day's actions
    tx_hash TEXT UNIQUE NOT NULL,          -- On-chain anchor tx
    action_count INTEGER,
    anchored_at TIMESTAMPTZ DEFAULT NOW()
);

-- Metrics (Privacy-Safe, Coarse Granularity)
CREATE TABLE metrics_daily (
    metric_date DATE PRIMARY KEY,
    submissions_count INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    disputed_count INTEGER DEFAULT 0,
    avg_review_time_hours NUMERIC,
    active_moderators INTEGER,
    active_reporters INTEGER
);

-- Indexes for Performance
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_category ON reports(category);
CREATE INDEX idx_reports_reporter ON reports(reporter_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_users_reputation ON users(reputation_score DESC);
CREATE INDEX idx_mod_actions_report ON mod_actions(report_id);
```

---

## 🔐 Encryption Architecture

### Key Hierarchy

```
┌──────────────────────────────────────────────────┐
│           MASTER ENTROPY SOURCE                   │
│  (User's Wallet Seed / Hardware RNG)             │
└────────────────┬─────────────────────────────────┘
                 │
    ┌────────────┴────────────┬─────────────────────┐
    │                         │                     │
    ↓                         ↓                     ↓
┌─────────────┐     ┌──────────────────┐    ┌──────────────┐
│ Report Keys │     │ Identity Keys    │    │ Recovery Key │
│ (Per Report)│     │ (Per Pseudonym)  │    │ (Shamir 3/5) │
└─────────────┘     └──────────────────┘    └──────────────┘
     │                       │                       │
     │ AES-256-GCM          │ Ed25519 Signing       │ Split 5 Ways
     │                       │                       │
     ↓                       ↓                       ↓
[Encrypted      [Anonymous           [Guardian 1]
 Report Blob]    Attestations]       [Guardian 2]
                                     [Guardian 3]
                                     [Guardian 4]
                                     [Guardian 5]
```

### Encryption Workflow

#### 1. Report Encryption (Client-Side)

```javascript
// Pseudocode
async function encryptReport(reportData, files) {
  // 1. Generate random report key
  const reportKey = crypto.getRandomValues(new Uint8Array(32));
  
  // 2. Serialize report data
  const plaintext = JSON.stringify({
    title: reportData.title,
    category: reportData.category,
    description: reportData.description,
    timestamp: fuzzTimestamp(Date.now()), // +/- random hours
    files: await processFiles(files)
  });
  
  // 3. Pad to fixed size blocks (prevent size analysis)
  const paddedData = padTo64KB(plaintext);
  
  // 4. Encrypt with AES-GCM (authenticated encryption)
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv },
    reportKey,
    new TextEncoder().encode(paddedData)
  );
  
  // 5. Package encrypted blob
  const encryptedBlob = {
    version: 1,
    iv: arrayBufferToBase64(iv),
    ciphertext: arrayBufferToBase64(ciphertext),
    authTag: extractAuthTag(ciphertext) // Already in GCM output
  };
  
  return { encryptedBlob, reportKey };
}

// 2. Store Key Securely (Multiple Options)
async function storeReportKey(reportKey, cid) {
  // Option A: Local storage (encrypted with wallet)
  const walletKey = await deriveKeyFromWallet();
  const encryptedKey = await encryptWithWallet(reportKey, walletKey);
  localStorage.setItem(`key_${cid}`, encryptedKey);
  
  // Option B: Shamir secret sharing (recovery)
  const shares = shamirSplit(reportKey, 3, 5); // 3-of-5
  await distributeToGuardians(shares);
  
  // Option C: Encrypted backup to IPFS (for sharing)
  const keyBackup = await encryptForPublicKey(reportKey, userPublicKey);
  const keyCID = await ipfs.add(keyBackup);
  
  return { localKey: encryptedKey, recoveryCID: keyCID };
}
```

#### 2. Selective Disclosure (Sharing)

```javascript
async function shareReportAccess(cid, reportKey, viewerPublicKey) {
  // 1. Re-encrypt report key for viewer
  const viewerKey = await importPublicKey(viewerPublicKey);
  const encryptedKeyBundle = await crypto.subtle.encrypt(
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    viewerKey,
    reportKey
  );
  
  // 2. Store share record (DB + blockchain)
  await db.shares.insert({
    report_cid: cid,
    viewer_pubkey: viewerPublicKey,
    encrypted_key_bundle: arrayBufferToBase64(encryptedKeyBundle),
    access_expires_at: Date.now() + (30 * 24 * 60 * 60 * 1000) // 30 days
  });
  
  // 3. Generate secure share link
  const shareToken = generateSecureToken();
  return `https://covert.app/view/${cid}/${shareToken}`;
}
```

#### 3. Moderator Group Encryption

```javascript
// Moderators share a group key (rotated monthly)
async function encryptModeratorNotes(notes, groupKey) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv },
    groupKey,
    new TextEncoder().encode(notes)
  );
  
  return {
    iv: arrayBufferToBase64(iv),
    ciphertext: arrayBufferToBase64(ciphertext)
  };
}

// Key rotation (when moderator removed)
async function rotateModeratorGroupKey() {
  const newKey = crypto.getRandomValues(new Uint8Array(32));
  
  // Re-encrypt all active notes with new key
  const activeNotes = await db.mod_actions.find({ status: 'active' });
  for (const note of activeNotes) {
    const decrypted = await decrypt(note.encrypted_notes, oldKey);
    const reEncrypted = await encrypt(decrypted, newKey);
    await db.mod_actions.update(note.id, { encrypted_notes: reEncrypted });
  }
  
  // Distribute new key to active moderators
  await distributeGroupKey(newKey, activeModerators);
}
```

---

## 🌐 IPFS Integration Architecture

### Storage Strategy

```
┌────────────────────────────────────────────────┐
│         IPFS Storage Architecture              │
└────────────────────────────────────────────────┘

Primary Node: Kubo (Docker Container)
├── Local Dev: http://localhost:5001
├── Testnet: Self-hosted on Railway
└── Mainnet: Distributed cluster (3+ nodes)

Pinning Services (Redundancy):
├── Pinata (1GB free tier) - Primary backup
├── web3.storage (Free unlimited) - Secondary backup
└── IPFS Cluster (Self-managed) - Tertiary backup

Content Addressing:
├── CIDv1 (base32) - Default format
├── Content Chunking - 256KB blocks
└── Deduplication - Automatic via IPFS

Access Patterns:
├── Public Gateway - ipfs.io/ipfs/{CID}
├── Private Gateway - covert.app/ipfs/{CID}
└── Direct Fetch - ipfs.get(CID) via JS client
```

### Pinning Workflow

```javascript
// Multi-tier pinning for redundancy
async function uploadToIPFS(encryptedBlob) {
  // 1. Upload to local Kubo node
  const localResult = await localIPFS.add(encryptedBlob);
  console.log('Local CID:', localResult.cid.toString());
  
  // 2. Pin to Pinata (retry logic)
  try {
    const pinataResult = await pinata.pinByHash(localResult.cid.toString(), {
      pinataMetadata: {
        name: `report_${Date.now()}`,
        keyvalues: { encrypted: 'true', version: '1' }
      }
    });
    console.log('Pinata pinned:', pinataResult.IpfsHash);
  } catch (error) {
    console.error('Pinata failed, trying web3.storage...');
    await web3Storage.put([encryptedBlob]);
  }
  
  // 3. Record pinning status in DB
  await db.ipfs_pins.insert({
    cid: localResult.cid.toString(),
    pinned_local: true,
    pinned_pinata: pinataResult?.IpfsHash ? true : false,
    pinned_web3storage: true,
    pinned_at: new Date()
  });
  
  return localResult.cid.toString();
}

// Garbage collection (remove old unpinned data)
async function pruneOldContent() {
  const threshold = Date.now() - (90 * 24 * 60 * 60 * 1000); // 90 days
  
  const oldReports = await db.reports.find({
    status: 'rejected',
    submitted_at: { $lt: threshold }
  });
  
  for (const report of oldReports) {
    await localIPFS.pin.rm(report.cid);
    await pinata.unpin(report.cid);
    console.log(`Unpinned ${report.cid}`);
  }
}
```

---

## 🔗 Smart Contract Architecture

### Contract Hierarchy

```
┌───────────────────────────────────────┐
│      ProxyAdmin (OpenZeppelin)        │
│  (Upgradeable Contract Management)    │
└─────────────┬─────────────────────────┘
              │
    ┌─────────┴──────────┬──────────────────┐
    │                    │                  │
    ↓                    ↓                  ↓
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ Commitment  │  │ Reputation   │  │ Governance   │
│ Registry    │  │ SBT (ERC721) │  │ DAO          │
└──────┬──────┘  └──────┬───────┘  └──────┬───────┘
       │                │                  │
       │ Emits Events   │ Mints SBTs       │ Voting
       │                │                  │
       └────────────────┴──────────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ↓                       ↓
    ┌──────────────┐        ┌──────────────┐
    │ Dispute      │        │ Daily Anchor │
    │ Resolution   │        │ (Optional)   │
    └──────────────┘        └──────────────┘
```

### Gas Optimization Strategies

1. **Use Events Instead of Storage**: Emit events for audit trail
2. **Batch Operations**: Daily anchor aggregates all actions
3. **Layer 2**: Deploy on Base Sepolia (cheaper than L1)
4. **Minimal On-Chain Data**: Store only hashes, not content
5. **Upgradeable Proxies**: Fix bugs without redeployment

---

## 📡 API Architecture (FastAPI)

### Endpoint Categories

```
├── /api/v1/reports
│   ├── POST /submit          - Submit encrypted report
│   ├── GET /list             - List user's reports
│   ├── GET /{id}             - Get report metadata
│   └── POST /{id}/share      - Generate share link
│
├── /api/v1/moderation
│   ├── GET /queue            - Fetch review queue
│   ├── POST /review          - Submit review decision
│   ├── GET /actions          - Moderator action history
│   └── POST /rotate-key      - Rotate group key
│
├── /api/v1/disputes
│   ├── POST /create          - Initiate dispute
│   ├── GET /{id}             - Get dispute details
│   ├── POST /{id}/vote       - Submit jury vote (commit)
│   └── POST /{id}/reveal     - Reveal vote (reveal phase)
│
├── /api/v1/reputation
│   ├── GET /score            - Get user reputation
│   ├── GET /leaderboard      - Top contributors (anonymous)
│   └── GET /events           - Reputation change history
│
├── /api/v1/ipfs
│   ├── POST /pin             - Pin CID to IPFS
│   ├── GET /status/{cid}     - Check pin status
│   └── DELETE /unpin/{cid}   - Unpin old content
│
├── /api/v1/blockchain
│   ├── GET /events           - Query contract events
│   ├── POST /anchor          - Trigger daily anchor
│   └── GET /verify/{cid}     - Verify on-chain commitment
│
└── /api/v1/admin
    ├── GET /metrics          - System health dashboard
    ├── POST /config          - Update configuration
    └── GET /audit-log        - Download audit trail
```

### API Security

```python
# Rate limiting (Redis-backed)
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/v1/reports/submit")
@limiter.limit("10/hour")  # 10 submissions per hour
async def submit_report(request: Request):
    pass

# Wallet signature verification
from eth_account.messages import encode_defunct
from web3 import Web3

def verify_wallet_signature(message: str, signature: str, address: str):
    w3 = Web3()
    message_hash = encode_defunct(text=message)
    recovered = w3.eth.account.recover_message(message_hash, signature=signature)
    return recovered.lower() == address.lower()

# CORS (restrict to frontend domain)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://covert.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 🧪 Testing Strategy

### Test Pyramid

```
        /\
       /  \
      / E2E \          5% (Playwright, full user flows)
     /______\
    /        \
   / Integration\     35% (API + DB + Smart Contracts)
  /____________\
 /              \
/  Unit Tests    \   60% (Pure functions, crypto, logic)
/________________\
```

### Key Test Scenarios

1. **Encryption Tests**:
   - Encrypt → Decrypt → Verify integrity
   - Key derivation from wallet
   - Shamir secret sharing (3-of-5 recovery)

2. **Smart Contract Tests**:
   - Fuzz testing (Foundry)
   - Gas usage benchmarks
   - Access control (only moderators can review)

3. **API Tests**:
   - Rate limiting enforcement
   - Signature verification
   - IPFS pinning retries

4. **Integration Tests**:
   - Full submission flow (UI → API → IPFS → Blockchain)
   - Dispute resolution (Create → Jury → Vote → Resolve)

---

## 📈 Scaling Considerations

### Horizontal Scaling

```
Load Balancer (Nginx)
        │
   ┌────┴────┬────────┬────────┐
   │         │        │        │
Backend 1  Backend 2  Backend 3  Backend N
   │         │        │        │
   └─────────┴────────┴────────┘
              │
        Shared Redis
              │
        PostgreSQL (Primary + Replicas)
```

### Vertical Optimization
- Database connection pooling (50-100 connections)
- Redis caching for hot data (reports status, reputation)
- CDN for static assets (CloudFlare free tier)
- IPFS gateway caching

---

## 🎯 Complete MVP Feature Mapping

### Reporter Dashboard (MVP Core)

All features from COVERT MVP.pdf included:

```
Reporter Features:
├── New Report
│   ├── Form (title, category, description, files)
│   ├── Client-side encryption before upload
│   ├── IPFS upload with progress bar
│   └── Blockchain commitment transaction
│
├── My Submissions
│   ├── Status: Submitted/In Review/Accepted/Rejected/Needs Info
│   ├── Display: Time, CID, Transaction Hash
│   └── Filter by status and category
│
├── Report Details (Safe View)
│   ├── Local decrypted copy view
│   ├── Timestamps (submission, review)
│   ├── Moderator requests display
│   └── Transaction verification
│
├── Share Access (Optional)
│   ├── Generate secure link
│   ├── Add viewer's public key
│   ├── Encrypted key re-encryption
│   └── Access expiration management
│
├── Notifications (Basic)
│   ├── In-app status change alerts
│   ├── Browser notifications
│   └── Future: Email/Telegram integration
│
└── Safety Tips
    ├── Avoid personal info checklist
    ├── EXIF scrubbing guide
    ├── Burner wallet instructions
    └── Private network (Tor) setup
```

### Moderator Console (MVP Core)

All features from COVERT MVP.pdf included:

```
Moderator Features:
├── Review Queue
│   ├── Incoming reports list
│   ├── Minimal info display (category, time, size)
│   ├── Risk flags from AI
│   └── Priority sorting
│
├── Filters & Search
│   ├── Filter by category
│   ├── Filter by time range
│   ├── Filter by status
│   └── Search by CID/Transaction Hash
│
├── Report Card (Moderation View)
│   ├── Metadata display only
│   ├── Encrypted attachments list
│   ├── Add encrypted moderator notes
│   └── View reporter reputation signal
│
├── Decisions
│   ├── Accept button (signed & logged)
│   ├── Reject button (with reason)
│   ├── Needs More Info (requester ping)
│   ├── Tag system (urgency, category)
│   └── All actions hash-anchored daily
│
├── Requester Ping
│   ├── Send standardized "need more info" request
│   ├── Appears on reporter dashboard
│   └── No identity exchange
│
├── Activity Log
│   ├── View recent actions
│   ├── Daily hash anchoring on-chain
│   └── Audit trail download
│
└── Light Reputation Signal
    ├── Reporter pseudonym indicator
    ├── Prior accepted vs rejected count
    └── No identity revelation
```

### Operator Dashboard (MVP Core)

All features from COVERT MVP.pdf included:

```
Operator Features:
├── System Health
│   ├── Submissions today count
│   ├── Queue size monitoring
│   ├── Acceptance rate percentage
│   ├── Median file size tracking
│   └── RPC/IPFS status indicators
│
├── Configuration
│   ├── File size limits (default 100MB)
│   ├── Rate limits per user type
│   ├── Allowed categories management
│   ├── Submission window (on/off)
│   └── Maintenance mode toggle
│
├── IPFS Pinning & Storage
│   ├── Pinned/unpinned items count
│   ├── Retry pin failed items
│   ├── Last pin errors display
│   └── Storage capacity monitoring
│
├── Key & Policy Management
│   ├── Rotate moderator group key
│   ├── Past notes remain readable
│   ├── Toggle share-link policy
│   └── Emergency key recovery
│
├── Audit & Anchoring
│   ├── Latest moderation log hash
│   ├── Anchor status (last block/time)
│   ├── Download signed daily logs
│   └── Verify log integrity
│
├── User Management (Minimal)
│   ├── Add/remove moderators
│   ├── Set roles (basic/trusted/validator)
│   ├── Lock accounts for abuse
│   └── No user identity data stored
│
└── Metrics (Privacy-Safe)
    ├── Day-level charts only
    ├── Export CSV with differential privacy noise
    ├── Feed transparency page
    └── Anonymized statistics only
```

---

## 📊 Data Storage Strategy (MVP)

### From COVERT MVP.pdf - Complete Implementation

#### A) On-Chain (Blockchain)

**Goal**: Public, tamper-proof proof that "a report existed at time X"

**What We Store** (minimal, privacy-safe):
```solidity
struct Commitment {
    bytes32 cidHash;        // Hash of IPFS CID (privacy layer)
    uint8 visibility;       // 0=private, 1=shareable, 2=public
    address submitter;      // Burner wallet address
    uint256 timestamp;      // Block timestamp
    bool isActive;          // Deletion flag
}
```

**Contracts** (MVP):
1. **CommitmentRegistry** (MUST-HAVE)
   - Records report commitments
   - Emits SubmissionEvent
   - Verifiable by anyone

2. **DailyAnchor** (OPTIONAL but recommended)
   - Posts one hash per day
   - Aggregates all moderation actions
   - Proves log wasn't changed later

**Why This Approach**:
- ✅ Minimal gas costs (Layer 2)
- ✅ Maximum privacy (only hashes)
- ✅ Permanent auditability
- ✅ Censorship resistant

#### B) Off-Chain (IPFS)

**Goal**: Store actual encrypted report content

**What We Store**:
```json
{
  "version": 1,
  "encrypted_payload": {
    "iv": "base64_initialization_vector",
    "ciphertext": "base64_encrypted_data",
    "auth_tag": "base64_authentication_tag"
  },
  "encrypted_content": {
    "title": "encrypted",
    "category": "encrypted",
    "description": "encrypted",
    "created_time": "fuzzy_timestamp",
    "attachments": [
      {
        "filename": "encrypted",
        "mime_type": "encrypted",
        "size_padded": 65536,
        "content": "base64_encrypted_file"
      }
    ]
  },
  "share_bundles": []  // Optional selective disclosure
}
```

**Storage Locations**:
1. **Primary**: Kubo local node (Docker)
2. **Backup 1**: Pinata (1GB free tier)
3. **Backup 2**: web3.storage (unlimited free)

**Why IPFS**:
- ✅ Decentralized (no single point of failure)
- ✅ Content-addressed (CID = hash of content)
- ✅ Durable with pinning
- ✅ Free/cheap hosting options

#### C) Database (PostgreSQL/Supabase)

**Goal**: Fast queries, workflow management, NO plaintext content

**What We Store** (Index & Metadata Only):
```sql
-- Core tables from MVP spec
reports (
    cid TEXT,                    -- IPFS content ID
    cid_hash TEXT,               -- SHA-256 of CID (matches on-chain)
    tx_hash TEXT,                -- Blockchain transaction
    status TEXT,                 -- submitted/review/accepted/rejected/needs_info
    visibility INTEGER,          -- 0/1/2
    reporter_pseudo TEXT,        -- Opaque pseudonym
    size_bytes INTEGER,          -- File size
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP
)

mod_actions (
    report_cid TEXT,
    moderator_pseudo TEXT,
    action TEXT,                 -- accept/reject/need_info/tag
    encrypted_notes TEXT,        -- Encrypted with mod group key
    created_at TIMESTAMP
)

shares (
    report_cid TEXT,
    viewer_pubkey TEXT,
    encrypted_key_bundle TEXT,   -- Report key re-encrypted for viewer
    access_granted_at TIMESTAMP,
    access_expires_at TIMESTAMP,
    access_count INTEGER
)

metrics_daily (
    metric_date DATE,
    submissions_count INTEGER,
    accepted_count INTEGER,
    rejected_count INTEGER,
    avg_review_time_hours NUMERIC
)
```

**Why Database**:
- ✅ Fast UI loading (moderator queue)
- ✅ Status tracking
- ✅ Analytics (privacy-preserving)
- ✅ No sensitive data at rest

---

## 🔄 Complete Submission Flow (MVP)

### Step-by-Step from COVERT MVP.pdf

#### 1. User Fills Form
```javascript
// Frontend component
<ReportForm>
  <Input name="title" maxLength={200} />
  <Select name="category" options={CATEGORIES} />
  <Textarea name="description" maxLength={5000} />
  <FileUpload accept=".jpg,.png,.pdf,.mp4" maxSize={100MB} />
  <Select name="visibility" options={['Private', 'Moderated', 'Public']} />
  <Button>Submit Encrypted Report</Button>
</ReportForm>
```

#### 2. Generate Fresh Encryption Key
```javascript
const reportKey = crypto.getRandomValues(new Uint8Array(32));
console.log('Generated AES-256 key:', reportKey);
```

#### 3. Encrypt Report Locally
```javascript
async function encryptReport(formData, files) {
  const reportData = {
    title: formData.title,
    category: formData.category,
    description: formData.description,
    timestamp: fuzzyTimestamp(),  // +/- random hours
    attachments: await processFiles(files)
  };
  
  // Serialize
  const plaintext = JSON.stringify(reportData);
  
  // Pad to 64KB blocks (prevent size analysis)
  const padded = padToBlockSize(plaintext, 65536);
  
  // Encrypt with AES-GCM
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encryptedData = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv },
    await importKey(reportKey),
    new TextEncoder().encode(padded)
  );
  
  return {
    iv: arrayBufferToBase64(iv),
    ciphertext: arrayBufferToBase64(encryptedData),
    authTag: extractAuthTag(encryptedData)
  };
}
```

#### 4. Upload to IPFS
```javascript
const encryptedBlob = await encryptReport(formData, files);

const ipfsResult = await ipfs.add(JSON.stringify(encryptedBlob), {
  pin: true,
  progress: (bytes) => updateProgressBar(bytes)
});

const cid = ipfsResult.cid.toString();
console.log('IPFS CID:', cid);
```

#### 5. Create Hash Fingerprints
```javascript
// Hash the CID for on-chain privacy
const cidHash = await sha256(cid);

// Store key locally (encrypted with wallet)
const walletKey = await deriveKeyFromWallet();
const encryptedKey = await encryptKeyWithWallet(reportKey, walletKey);
localStorage.setItem(`key_${cid}`, encryptedKey);
```

#### 6. Call Smart Contract
```javascript
const contract = new ethers.Contract(
  COMMITMENT_REGISTRY_ADDRESS,
  COMMITMENT_ABI,
  wallet
);

const tx = await contract.commit(
  cidHash,
  formData.visibility,
  { gasLimit: 100000 }
);

const receipt = await tx.wait();
console.log('Transaction hash:', receipt.transactionHash);
```

#### 7. Update Database
```javascript
// Backend API receives blockchain event
await db.reports.insert({
  cid: cid,
  cid_hash: cidHash,
  tx_hash: receipt.transactionHash,
  status: 'submitted',
  visibility: formData.visibility,
  reporter_pseudo: generatePseudonym(walletAddress),
  size_bytes: encryptedBlob.length,
  submitted_at: new Date()
});
```

#### Result Display
```javascript
<SuccessMessage>
  ✅ Report Submitted Successfully!
  
  📋 Details:
  - IPFS CID: {cid}
  - Blockchain Tx: {txHash}
  - Status: Submitted
  - Time: {timestamp}
  
  🔐 Your report is encrypted and secure.
  Only you can decrypt it with your wallet.
</SuccessMessage>
```

---

## 🔍 Complete Retrieval Flow (MVP)

### A) Reporter Reading Own Report

```javascript
async function viewOwnReport(cid) {
  // 1. Fetch encrypted blob from IPFS
  const encryptedBlob = await ipfs.cat(cid);
  
  // 2. Get report key from local storage
  const encryptedKey = localStorage.getItem(`key_${cid}`);
  const walletKey = await deriveKeyFromWallet();
  const reportKey = await decryptKeyWithWallet(encryptedKey, walletKey);
  
  // 3. Decrypt in browser
  const decrypted = await crypto.subtle.decrypt(
    { 
      name: 'AES-GCM', 
      iv: base64ToArrayBuffer(encryptedBlob.iv) 
    },
    await importKey(reportKey),
    base64ToArrayBuffer(encryptedBlob.ciphertext)
  );
  
  // 4. Remove padding
  const unpadded = removePadding(decrypted);
  
  // 5. Parse and display
  const reportData = JSON.parse(new TextDecoder().decode(unpadded));
  
  // 6. Verify integrity (hash CID, check on-chain)
  const computedCidHash = await sha256(cid);
  const onChainHash = await contract.getCommitment(cid);
  
  if (computedCidHash !== onChainHash) {
    throw new Error('Report has been tampered with!');
  }
  
  return reportData;
}
```

### B) Moderator Viewing Metadata

```javascript
async function loadModeratorQueue() {
  // Fetch from database (NO decryption)
  const queue = await api.get('/api/v1/moderation/queue', {
    params: {
      status: 'submitted',
      limit: 50,
      orderBy: 'submitted_at_desc'
    }
  });
  
  // Display metadata only
  return queue.map(report => ({
    id: report.cid,
    category: report.category,
    submittedAt: report.submitted_at,
    sizeBytes: report.size_bytes,
    riskFlags: report.risk_flags,  // AI-generated
    reporterReputation: report.reporter_reputation_signal
  }));
}
```

### C) Trusted Person with Share Link

```javascript
async function viewSharedReport(cid, shareToken) {
  // 1. Verify share token
  const shareInfo = await api.get(`/api/v1/reports/${cid}/share/${shareToken}`);
  
  if (!shareInfo.valid || shareInfo.expired) {
    throw new Error('Share link invalid or expired');
  }
  
  // 2. Fetch encrypted blob from IPFS
  const encryptedBlob = await ipfs.cat(cid);
  
  // 3. Get encrypted key bundle for this viewer
  const encryptedKeyBundle = shareInfo.encrypted_key_bundle;
  
  // 4. Decrypt key bundle with viewer's private key
  const viewerPrivateKey = await wallet.getPrivateKey();
  const reportKey = await crypto.subtle.decrypt(
    { name: 'RSA-OAEP' },
    viewerPrivateKey,
    base64ToArrayBuffer(encryptedKeyBundle)
  );
  
  // 5. Decrypt report (same as reporter)
  const reportData = await decryptWithKey(encryptedBlob, reportKey);
  
  // 6. Track access
  await api.post(`/api/v1/reports/${cid}/share/${shareToken}/access`);
  
  return reportData;
}
```

---

## 🛡️ Tamper-Proof Verification (MVP)

### Public Verification Page

```javascript
// Anyone can verify a report exists without seeing content
async function verifyReport(cidOrTxHash) {
  let cid, txHash;
  
  // Determine input type
  if (cidOrTxHash.startsWith('bafy')) {
    cid = cidOrTxHash;
    // Compute expected hash
    const computedHash = await sha256(cid);
    
    // Check on-chain
    const commitment = await contract.getCommitmentByCidHash(computedHash);
    
    if (!commitment.exists) {
      return { verified: false, reason: 'No on-chain commitment found' };
    }
    
    return {
      verified: true,
      submittedAt: new Date(commitment.timestamp * 1000),
      submitter: commitment.submitter,
      visibility: commitment.visibility,
      txHash: commitment.txHash
    };
    
  } else if (cidOrTxHash.startsWith('0x')) {
    txHash = cidOrTxHash;
    
    // Fetch transaction details
    const tx = await provider.getTransaction(txHash);
    const receipt = await provider.getTransactionReceipt(txHash);
    
    // Parse event logs
    const event = receipt.logs.find(log => 
      log.topics[0] === SUBMISSION_EVENT_TOPIC
    );
    
    if (!event) {
      return { verified: false, reason: 'No submission event in transaction' };
    }
    
    // Decode event data
    const decoded = contract.interface.parseLog(event);
    
    return {
      verified: true,
      cidHash: decoded.args.cidHash,
      submittedAt: new Date(decoded.args.timestamp * 1000),
      blockNumber: receipt.blockNumber
    };
  }
  
  return { verified: false, reason: 'Invalid input format' };
}
```

---

## 🎨 UI/UX Components (MVP)

### Technology Stack from MVP
- **Frontend**: HTML + Tailwind CSS + HTMX + Alpine.js
- **Web3**: Minimal vanilla JS + ethers.js
- **Crypto**: Web Crypto API (native browser)
- **IPFS**: ipfs-http-client library

### Key UI Components

```html
<!-- Reporter Dashboard -->
<div class="dashboard">
  <!-- New Report Card -->
  <div class="card">
    <h2>Submit New Report</h2>
    <form hx-post="/api/v1/reports/submit" hx-encoding="multipart/form-data">
      <input type="text" name="title" placeholder="Report Title" required />
      <select name="category" required>
        <option value="corruption">Corruption</option>
        <option value="harassment">Harassment</option>
        <option value="fraud">Fraud</option>
        <option value="safety">Safety Violation</option>
      </select>
      <textarea name="description" rows="6"></textarea>
      <input type="file" multiple accept=".jpg,.pdf,.png" />
      <select name="visibility">
        <option value="0">Private</option>
        <option value="1">Community Moderated</option>
        <option value="2">Public</option>
      </select>
      <button type="submit" class="btn-primary">
        🔒 Encrypt & Submit
      </button>
    </form>
  </div>
  
  <!-- My Submissions -->
  <div class="card">
    <h2>My Submissions</h2>
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Category</th>
          <th>Status</th>
          <th>CID</th>
          <th>Tx Hash</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody hx-get="/api/v1/reports/list" hx-trigger="load">
        <!-- Populated dynamically -->
      </tbody>
    </table>
  </div>
</div>

<!-- Moderator Console -->
<div class="moderator-console">
  <!-- Review Queue -->
  <div class="card">
    <h2>Review Queue</h2>
    <div class="filters">
      <select name="category">
        <option value="">All Categories</option>
        <option value="corruption">Corruption</option>
        <option value="harassment">Harassment</option>
      </select>
      <select name="status">
        <option value="submitted">Submitted</option>
        <option value="needs_info">Needs Info</option>
      </select>
      <input type="search" placeholder="Search by CID..." />
    </div>
    
    <div class="queue-list" hx-get="/api/v1/moderation/queue" hx-trigger="every 30s">
      <!-- Report cards populated here -->
    </div>
  </div>
  
  <!-- Report Card -->
  <div class="report-card">
    <div class="metadata">
      <p><strong>Category:</strong> Corruption</p>
      <p><strong>Submitted:</strong> 2024-01-15 10:30 UTC</p>
      <p><strong>Size:</strong> 2.5 MB</p>
      <p><strong>Risk Flags:</strong> None</p>
      <p><strong>Reporter Rep:</strong> 3 accepted, 0 rejected</p>
    </div>
    
    <div class="actions">
      <button class="btn-success" hx-post="/api/v1/moderation/accept">
        ✅ Accept
      </button>
      <button class="btn-danger" hx-post="/api/v1/moderation/reject">
        ❌ Reject
      </button>
      <button class="btn-warning" hx-post="/api/v1/moderation/need-info">
        ℹ️ Need More Info
      </button>
      <button class="btn-secondary" hx-post="/api/v1/moderation/tag">
        🏷️ Add Tag
      </button>
    </div>
    
    <textarea placeholder="Encrypted moderator notes (optional)"></textarea>
  </div>
</div>

<!-- Operator Dashboard -->
<div class="operator-dashboard">
  <!-- System Health Tiles -->
  <div class="metrics-grid">
    <div class="metric-card">
      <h3>Submissions Today</h3>
      <p class="metric-value" hx-get="/api/v1/admin/metrics/submissions" hx-trigger="every 60s">
        42
      </p>
    </div>
    
    <div class="metric-card">
      <h3>Queue Size</h3>
      <p class="metric-value">15</p>
    </div>
    
    <div class="metric-card">
      <h3>Acceptance Rate</h3>
      <p class="metric-value">85%</p>
    </div>
    
    <div class="metric-card">
      <h3>IPFS Status</h3>
      <p class="status-indicator">🟢 Healthy</p>
    </div>
  </div>
  
  <!-- Configuration Panel -->
  <div class="card">
    <h2>Configuration</h2>
    <form hx-post="/api/v1/admin/config">
      <label>Max File Size (MB)</label>
      <input type="number" name="max_file_size" value="100" />
      
      <label>Rate Limit (per hour)</label>
      <input type="number" name="rate_limit" value="10" />
      
      <label>Submission Window</label>
      <select name="submission_enabled">
        <option value="true">Open</option>
        <option value="false">Closed</option>
      </select>
      
      <button type="submit">Update Config</button>
    </form>
  </div>
</div>
```

---

## 🧪 Testing Coverage (MVP)

### Unit Tests

```python
# test_encryption.py
def test_encrypt_decrypt_report():
    """Test AES-GCM encryption round-trip"""
    report = {"title": "Test", "description": "Test report"}
    key = generate_key()
    
    encrypted = encrypt_report(report, key)
    decrypted = decrypt_report(encrypted, key)
    
    assert decrypted == report

def test_padding():
    """Test data padding to block size"""
    data = b"short data"
    padded = pad_to_block_size(data, 65536)
    
    assert len(padded) == 65536
    assert unpad(padded) == data

# test_smart_contracts.py (Foundry)
function testCommitReport() public {
    bytes32 cidHash = keccak256("bafy...");
    uint8 visibility = 1;
    
    vm.prank(reporter);
    commitmentRegistry.commit(cidHash, visibility);
    
    (bool exists, address submitter, uint256 timestamp) = 
        commitmentRegistry.getCommitment(cidHash);
    
    assertTrue(exists);
    assertEq(submitter, reporter);
}

# test_api.py
async def test_submit_report(client):
    """Test report submission endpoint"""
    report_data = {
        "cid": "bafytest123",
        "cid_hash": "0xabc...",
        "tx_hash": "0xdef...",
        "visibility": 1
    }
    
    response = await client.post("/api/v1/reports/submit", json=report_data)
    
    assert response.status_code == 201
    assert "id" in response.json()
```

---

## 📚 Additional Documentation Files Needed

Based on your requirements, here are the critical MD files that should exist:

1. ✅ **PROJECT_OVERVIEW.md** - Created (comprehensive)