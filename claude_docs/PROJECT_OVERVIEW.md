# C.O.V.E.R.T - Decentralized Whistleblowing Platform
## Complete Technical Documentation for BTech Major Project

---

## 🎯 Project Vision

C.O.V.E.R.T (Chain for Open and VERified Testimonies) is a blockchain-based anonymous whistleblowing platform that empowers truth-tellers while protecting their identity through cryptographic guarantees, decentralized storage, and community-driven governance.

---

## 🚀 Key Innovations & Unique Features

### 1. **Progressive Trust with Gamification**
- **Reputation NFTs**: Non-transferable soul-bound tokens (SBTs) representing user trust levels
- **Achievement System**: Unlock badges for milestones (first validated report, 10 helpful reviews, etc.)
- **Reputation Visualization**: Public leaderboards (anonymous pseudonyms) showing top contributors
- **Trust Score Algorithm**: Multi-factor scoring including report accuracy, peer calibration, and consistency

### 2. **AI-Powered Content Intelligence (Privacy-First)**
- **Local-First ML**: Run TensorFlow.js models in browser for spam detection
- **Similarity Detection**: Identify duplicate/related reports without revealing content
- **Risk Assessment**: Auto-tag reports by urgency/severity for prioritization
- **Language Detection & Translation**: Support multilingual submissions with privacy

### 3. **Enhanced Anonymity Layer**
- **Onion Routing Integration**: Optional Tor network support for submission
- **Metadata Scrubbing**: Automatic EXIF removal, timestamp fuzzing, file sanitization
- **Decoy Traffic**: Generate fake encrypted submissions to mask real ones
- **Temporal Obfuscation**: Batch submissions at random intervals to prevent timing attacks

### 4. **Social Recovery & Dead Man's Switch**
- **Guardian Network**: Split encryption keys using Shamir's Secret Sharing (3-of-5)
- **Automated Release**: Time-locked evidence release if user doesn't check-in
- **Emergency Broadcast**: Instant notification to trusted journalists/NGOs
- **Canary Tokens**: Embedded trackers alert if reports are accessed unexpectedly

### 5. **Verifiable Credentials & Context**
- **Anonymous Attestations**: Prove you're a domain expert (lawyer, doctor) via ZK proofs
- **Source Verification**: Link evidence to verified public data (public records, news)
- **Chain of Custody**: Immutable audit trail for evidence handling
- **Cross-Platform Verification**: Generate QR codes/links for third-party validation

### 6. **Community Engagement Features**
- **Discussion Threads**: Anonymous encrypted forums per report category
- **Whistleblower AMA**: Verified reporters can answer questions pseudonymously
- **Impact Tracking**: Show real-world outcomes (policy changes, investigations launched)
- **Collaborative Investigations**: Multiple whistleblowers can contribute to same case

### 7. **Legal & Compliance Tools**
- **Jurisdiction Selector**: Tailor privacy measures based on reporter location
- **Evidence Standards Guide**: Help format reports for legal admissibility
- **Lawyer Matching**: Connect to pro-bono legal aid via encrypted channels
- **Regulatory Compliance Templates**: Pre-filled forms for GDPR, SOX, etc.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  (React + Tailwind + HTMX + Progressive Web App)            │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   PRIVACY & CRYPTO LAYER                     │
│  (Web Crypto API, AES-GCM, Shamir Secret Sharing, ZK)      │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────┬──────────────────┬──────────────────────┐
│  BLOCKCHAIN      │   IPFS/STORAGE   │   BACKEND API        │
│  (Base Sepolia)  │   (Kubo/Pinata)  │   (FastAPI+Postgres) │
│  Smart Contracts │   Encrypted Data │   Workflow Engine    │
└──────────────────┴──────────────────┴──────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              GOVERNANCE & REPUTATION LAYER                   │
│       (DAO Voting, Jury Selection, Reputation NFTs)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 MVP Feature Scope (6-Month Timeline)

### Phase 1: Core Infrastructure (Weeks 1-8)
- ✅ Wallet integration (MetaMask, WalletConnect)
- ✅ Smart contract deployment (CommitmentRegistry, ReputationSBT)
- ✅ IPFS setup (local Kubo node + Pinata backup)
- ✅ Encryption pipeline (client-side AES-GCM)
- ✅ Basic FastAPI backend + Postgres schema
- ✅ Reporter dashboard (submit, view status)

### Phase 2: Moderation & Trust (Weeks 9-16)
- ✅ Moderator console (review queue, decisions)
- ✅ Reputation system (SBT minting, scoring algorithm)
- ✅ AI spam filter (TensorFlow.js in-browser)
- ✅ Dispute resolution (basic jury voting)
- ✅ Metadata scrubbing tools

### Phase 3: Advanced Features (Weeks 17-24)
- ✅ Social recovery (Shamir secret sharing)
- ✅ Dead man's switch (time-locked release)
- ✅ Share access (selective disclosure)
- ✅ Impact dashboard (public metrics)
- ✅ Mobile-responsive PWA
- ✅ Documentation + deployment

---

## 🛠️ Technology Stack (100% Free/Open Source)

### Frontend
- **Framework**: React 18 + Vite (fast builds)
- **Styling**: Tailwind CSS + DaisyUI (component library)
- **Interactivity**: HTMX (server-driven UI) + Alpine.js (lightweight JS)
- **Web3**: Ethers.js v6, WalletConnect v2, RainbowKit
- **Crypto**: Web Crypto API (native), TweetNaCl (fallback)
- **IPFS**: ipfs-http-client (JS library)
- **ML**: TensorFlow.js (spam detection), compromise.js (NLP)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0
- **Task Queue**: Celery + Redis (for anchoring, pinning)
- **API Docs**: Auto-generated Swagger/OpenAPI
- **Testing**: Pytest, Hypothesis (property testing)

### Blockchain
- **Network**: Base Sepolia (testnet, free ETH from faucet)
- **RPC**: Alchemy free tier (300M compute units/month)
- **Contracts**: Foundry (Solidity 0.8.20+)
- **Testing**: Forge (gas reports, fuzzing)
- **Deployment**: Hardhat scripts (backup)

### Storage
- **IPFS Node**: Kubo (Docker container, local dev)
- **Pinning**: Pinata free tier (1GB) + web3.storage backup
- **Database**: PostgreSQL (Railway/Render free tier)

### DevOps & Deployment
- **Version Control**: GitHub (Actions for CI/CD)
- **Containers**: Docker + Docker Compose
- **Hosting**: Railway (backend), Vercel/Netlify (frontend)
- **Monitoring**: Sentry (error tracking), Uptime Robot (health checks)
- **Secrets**: Doppler (free tier) or .env.local

### Security
- **Secrets Manager**: Mozilla SOPS + Age encryption
- **Key Derivation**: PBKDF2 / Argon2 (password hashing)
- **Rate Limiting**: FastAPI-Limiter (Redis-backed)
- **CORS**: FastAPI middleware

---

## 🎨 Unique Differentiators

### Why C.O.V.E.R.T Stands Out:

1. **True Anonymity**: Unlike WikiLeaks (centralized) or Signal (requires phone), we use burner wallets + ZK proofs
2. **Community Justice**: Reputation-weighted juries prevent moderator abuse (vs. centralized platforms)
3. **Unstoppable**: No single point of failure; data on IPFS, logic on blockchain
4. **Legally Aware**: Built-in guidance for jurisdiction-specific whistleblower protections
5. **Open Source**: Fully auditable code; community can fork/verify
6. **Student-Friendly**: Achievable with free tools; great for learning Web3, cryptography, and distributed systems

---

## 📊 Success Metrics

### Technical KPIs
- ✅ Report submission time < 30 seconds
- ✅ 99.9% IPFS data availability (via pinning redundancy)
- ✅ Zero private key leaks (audited smart contracts)
- ✅ < $0.01 per report submission (Layer 2 gas savings)

### Social Impact KPIs
- 🎯 100+ reports submitted (testnet beta)
- 🎯 80%+ report validation accuracy
- 🎯 50+ active moderators (reputation holders)
- 🎯 5+ case studies of real-world impact (blog posts)

---

## 🚧 Future Enhancements (Post-MVP)

1. **Mobile Apps**: React Native app with biometric auth
2. **Mainnet Launch**: Migrate to Ethereum L2 (Optimism/Arbitrum)
3. **DAO Treasury**: Fund bounties for high-impact reports
4. **Multi-Chain**: Support Polygon, Avalanche for cost optimization
5. **ZK Proofs**: Full implementation (currently simulated)
6. **Integration APIs**: Webhooks for NGOs/media orgs
7. **Encrypted Chat**: Built-in Signal protocol messaging
8. **Legal NFTs**: Mint proof-of-whistleblowing certificates

---

## 📚 Documentation Structure

This project includes the following detailed markdown files:

1. **PROJECT_OVERVIEW.md** (this file) - High-level vision
2. **ARCHITECTURE.md** - System design, data flows, diagrams
3. **SMART_CONTRACTS.md** - Solidity contracts with comments
4. **BACKEND_API.md** - FastAPI endpoints, database schemas
5. **FRONTEND_GUIDE.md** - React components, state management
6. **CRYPTOGRAPHY.md** - Encryption flows, key management
7. **REPUTATION_SYSTEM.md** - Scoring algorithm, SBT design
8. **DEPLOYMENT.md** - Step-by-step setup for local/testnet/production
9. **TESTING_STRATEGY.md** - Unit, integration, E2E test plans
10. **SECURITY_AUDIT.md** - Threat model, mitigation checklist
11. **USER_FLOWS.md** - UX journeys with mockups/wireframes
12. **API_REFERENCE.md** - Complete API documentation
13. **CONTRIBUTING.md** - Guidelines for future developers

---

## 🤝 Collaboration & Community

### Recommended Team Structure (4-5 students):
- **Blockchain Dev**: Smart contracts, wallet integration
- **Backend Dev**: FastAPI, database, IPFS pinning
- **Frontend Dev**: React UI, Web Crypto, HTMX
- **Security/Crypto**: Encryption, key management, audits
- **DevOps/Testing**: CI/CD, Docker, automated tests

### Development Philosophy:
- **Privacy by Default**: Encrypt first, ask questions later
- **Test-Driven**: Write tests before features
- **Document Everything**: Future you will thank present you
- **Fail Loudly**: Clear error messages over silent failures
- **Mobile-First**: Design for small screens first

---

## 📖 Learning Outcomes

By building C.O.V.E.R.T, you'll master:
- ✅ Blockchain development (Solidity, smart contracts)
- ✅ Decentralized storage (IPFS, content addressing)
- ✅ Applied cryptography (AES, secret sharing, hashing)
- ✅ Full-stack Web3 (React + FastAPI + Ethers.js)
- ✅ System design (distributed systems, threat modeling)
- ✅ DevOps (Docker, CI/CD, monitoring)
- ✅ Social impact tech (building for good)

---

## 🎓 Academic Justification

### Why This is an Excellent BTech Project:

1. **Multidisciplinary**: Combines blockchain, cryptography, web dev, AI/ML
2. **Novel Contribution**: Unique governance model with reputation SBTs
3. **Real-World Impact**: Addresses genuine societal problem
4. **Technical Depth**: Complex enough for graduate-level work
5. **Open Source**: Can contribute to academic community
6. **Scalable Scope**: Can demo MVP but discuss full vision
7. **Ethical Tech**: Demonstrates responsible innovation

### Research Paper Potential:
- "Decentralized Governance Models for Anonymous Reporting Systems"
- "Privacy-Preserving Reputation Systems Using Soul-Bound Tokens"
- "Cryptographic Techniques for Whistleblower Protection in Web3"

---

## 📞 Next Steps

1. ✅ Read all documentation files in order
2. ✅ Set up development environment (see DEPLOYMENT.md)
3. ✅ Run test suite to verify setup
4. ✅ Build Phase 1 features (weeks 1-8)
5. ✅ Weekly demos to track progress
6. ✅ Iterate based on user testing
7. ✅ Prepare presentation + demo video
8. ✅ Deploy to testnet and share with community

---

## 🌟 Final Thoughts

C.O.V.E.R.T isn't just a project—it's a movement toward transparent, accountable institutions. By building this, you're not only completing a degree requirement but potentially creating infrastructure that could protect truth-tellers worldwide.

**Let's build something that matters. Let's build C.O.V.E.R.T.** 🛡️

---

*Last Updated: November 2025*
*Version: 1.0.0 (MVP Specification)*
*License: MIT (Open Source)*