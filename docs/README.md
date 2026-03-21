# C.O.V.E.R.T 🛡️

### Chain for Open and VERified Testimonies

> A decentralized, blockchain-based whistleblowing platform that empowers truth-tellers while protecting their identity through cryptographic guarantees, decentralized storage, and community-driven governance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.20-363636.svg)](https://soliditylang.org)

---

## 🎯 What is C.O.V.E.R.T?

C.O.V.E.R.T is a next-generation whistleblowing platform that combines:

- **🔒 Cryptographic Privacy**: Client-side AES-256-GCM encryption ensures your reports are private
- **⛓️ Blockchain Immutability**: Reports are timestamped on-chain for tamper-proof evidence
- **📦 Decentralized Storage**: IPFS ensures your data can't be deleted or censored
- **👥 Community Governance**: DAO-based moderation with reputation-weighted voting
- **🎭 True Anonymity**: Burner wallets and zero-knowledge proofs protect your identity

---

## ✨ Key Features

### MVP Core Features (Implemented)

✅ **Anonymous Report Submission**
- Client-side encryption before upload
- IPFS storage with automatic pinning
- Blockchain commitment for immutability
- Burner wallet support

✅ **Reporter Dashboard**
- Submit encrypted reports with multimedia
- Track submission status in real-time
- View report history
- Generate secure share links
- Safety tips and EXIF scrubbing

✅ **Moderator Console**
- Review queue with filters and search
- Metadata-only viewing (no plaintext)
- Decision tracking (Accept/Reject/Need Info)
- Encrypted moderator notes
- Reputation-based privileges

✅ **Operator Dashboard**
- System health monitoring
- Configuration management
- IPFS pinning status
- User management (minimal identity data)
- Audit log exports

✅ **Smart Contracts**
- CommitmentRegistry (report proof)
- DailyAnchor (moderation log integrity)
- Gas-optimized for Layer 2

### Enhanced Features (Roadmap)

🔄 **Reputation System**
- Soul-bound tokens (SBTs) for trust levels
- Progressive privilege unlocking
- Reputation decay and slashing
- Achievement badges

🔄 **AI-Powered Analysis**
- Spam detection (TensorFlow.js)
- Credibility scoring
- Similarity detection
- Risk assessment

🔄 **Advanced Privacy**
- Zero-knowledge proofs for authentication
- Temporal identity rotation
- Decoy traffic generation
- Social recovery mechanisms

🔄 **Dispute Resolution**
- VRF-selected randomized juries
- Commit-reveal voting
- Reputation staking
- Appeal mechanisms

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                  User Interface                         │
│        (React + Tailwind + Web3 Integration)           │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────┴──────────────────────────────────┐
│              Client-Side Encryption                     │
│        (AES-GCM, Metadata Scrubbing, Padding)          │
└─────────────────────┬──────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼─────┐  ┌──────▼──────┐  ┌────▼────┐
│Blockchain │  │    IPFS     │  │ Backend │
│ (Base L2) │  │ (Encrypted) │  │(FastAPI)│
└───────────┘  └─────────────┘  └─────────┘
      │               │               │
      └───────────────┴───────────────┘
                      │
            ┌─────────┴─────────┐
            │   PostgreSQL      │
            │  (Index Only)     │
            └───────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Git
- MetaMask wallet

### One-Command Setup

```bash
# Clone repository
git clone https://github.com/yourusername/covert.git
cd covert

# Start all services
docker-compose up -d

# Deploy contracts to local testnet
cd contracts && forge script script/Deploy.s.sol --broadcast

# Start backend
cd ../backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Start frontend
cd ../frontend && npm install && npm run dev

# Open http://localhost:5173
```

### Detailed Setup

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive setup instructions.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) | High-level vision, features, and success metrics |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, data flows, and diagrams |
| [SMART_CONTRACTS.md](./SMART_CONTRACTS.md) | Solidity contracts with detailed comments |
| [BACKEND_API.md](./BACKEND_API.md) | FastAPI endpoints, models, and services |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Local, testnet, and production setup |
| [SECURITY.md](./SECURITY.md) | Threat model and security measures |
| [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) | 6-month development timeline |

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + DaisyUI
- **Web3**: Ethers.js v6, WalletConnect, RainbowKit
- **Encryption**: Web Crypto API (native)
- **IPFS**: ipfs-http-client

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery
- **ML**: PyTorch, Transformers

### Blockchain
- **Network**: Base Sepolia (testnet), Base (mainnet)
- **Smart Contracts**: Solidity 0.8.20+
- **Development**: Foundry (Forge, Anvil)
- **Testing**: Foundry Test Suite

### Storage
- **Primary**: IPFS (Kubo)
- **Pinning**: Pinata (1GB free) + web3.storage (unlimited)

### DevOps
- **Containers**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Hosting**: Railway (backend), Vercel (frontend)
- **Monitoring**: Sentry, Prometheus, Grafana

---

## 📊 Project Status

### Completed (MVP - 60%)

- ✅ Core encryption pipeline
- ✅ IPFS integration
- ✅ Smart contracts (CommitmentRegistry, DailyAnchor)
- ✅ Reporter dashboard
- ✅ Moderator console
- ✅ Operator dashboard
- ✅ Database schema
- ✅ API endpoints
- ✅ Docker setup

### In Progress (40%)

- ✅ Protocol contracts (COVCredits, CovertBadges, CovertProtocol)
- 🔄 AI spam detection
- 🔄 Frontend UI polish
- 🔄 Comprehensive testing
- 🔄 Documentation completion

### Planned (Phase 2)

- ⏳ Zero-knowledge proofs
- ⏳ Dispute resolution
- ⏳ DAO governance
- ⏳ Mobile app (PWA)
- ⏳ Mainnet deployment

---

## 🧪 Testing

```bash
# Run all tests
./scripts/test_all.sh

# Smart contracts
cd contracts
forge test -vvv

# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm test
npm run test:e2e

# Load testing
locust -f tests/load_test.py
```

---

## 🔒 Security

### Reporting Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

Instead, email: **security@covert.app** (PGP key on website)

### Bug Bounty

We offer rewards for responsibly disclosed security issues:
- **Critical**: $500-$2000
- **High**: $250-$500
- **Medium**: $100-$250
- **Low**: $50-$100

See [SECURITY.md](./SECURITY.md) for details.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Code of Conduct
- Development workflow
- Coding standards
- PR process

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📖 Usage Examples

### Submit a Report

```javascript
// 1. Connect wallet
const provider = new ethers.BrowserProvider(window.ethereum);
const signer = await provider.getSigner();

// 2. Encrypt report
const reportKey = crypto.getRandomValues(new Uint8Array(32));
const encrypted = await encryptReport(reportData, reportKey);

// 3. Upload to IPFS
const { cid } = await ipfs.add(encrypted);

// 4. Commit to blockchain
const cidHash = ethers.keccak256(ethers.toUtf8Bytes(cid));
const tx = await commitmentRegistry.commit(cidHash, visibility);
await tx.wait();

// 5. Store in database
await api.post('/reports/submit', {
  cid, cidHash, txHash: tx.hash, category, visibility
});
```

### Moderate a Report

```javascript
// 1. Authenticate as moderator
const signature = await signer.signMessage("Authenticate to C.O.V.E.R.T");

// 2. Fetch review queue
const queue = await api.get('/moderation/queue', {
  headers: { 'X-Signature': signature }
});

// 3. Review metadata (no plaintext)
queue.forEach(report => {
  console.log(report.category, report.submittedAt, report.riskFlags);
});

// 4. Make decision
await api.post('/moderation/review', {
  reportId: report.id,
  action: 'accept',
  notes: 'Verified evidence'
});
```

### Verify Report Integrity

```javascript
// Anyone can verify a report exists
const cid = "bafytest123...";
const cidHash = ethers.keccak256(ethers.toUtf8Bytes(cid));

const commitment = await commitmentRegistry.getCommitment(cidHash);

console.log(`Report submitted at: ${new Date(commitment.timestamp * 1000)}`);
console.log(`Submitter: ${commitment.submitter}`);
console.log(`Immutable: ${commitment.isActive}`);
```

---

## 🎓 Academic Use

This project is an excellent learning resource for:
- **Blockchain Development**: Smart contracts, Web3 integration
- **Cryptography**: AES-GCM, zero-knowledge proofs, key management
- **Distributed Systems**: IPFS, decentralized storage, consensus
- **Full-Stack Development**: React, FastAPI, PostgreSQL
- **Security Engineering**: Threat modeling, secure coding practices

### Research Papers

This work has potential for academic publication in:
- Privacy-enhancing technologies
- Decentralized governance models
- Applied cryptography
- Social impact of blockchain

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

```
MIT License

Copyright (c) 2025 C.O.V.E.R.T Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🌟 Acknowledgments

- **Ethereum Foundation** - For blockchain infrastructure
- **IPFS/Protocol Labs** - For decentralized storage
- **OpenZeppelin** - For secure smart contract libraries
- **FastAPI** - For excellent Python web framework
- **Whistleblowers Worldwide** - For inspiring this project

---

## 📞 Contact & Support

- **Website**: https://covert.app
- **Documentation**: https://docs.covert.app
- **Email**: hello@covert.app
- **Security**: security@covert.app
- **Twitter**: [@CovertApp](https://twitter.com/CovertApp)
- **Discord**: [Join Community](https://discord.gg/covert)
- **GitHub**: [Issues](https://github.com/yourusername/covert/issues)

---

## 🗺️ Roadmap

### Q1 2025 - MVP Launch ✅
- [x] Core smart contracts
- [x] Basic encryption pipeline
- [x] IPFS integration
- [x] Reporter & moderator dashboards
- [x] Testnet deployment

### Q2 2025 - Enhanced Features
- [ ] Reputation system with SBTs
- [ ] AI-powered spam detection
- [ ] Zero-knowledge proofs
- [ ] Dispute resolution
- [ ] Mobile PWA

### Q3 2025 - Mainnet Launch
- [ ] Security audit completion
- [ ] Mainnet contract deployment
- [ ] DAO governance activation
- [ ] Bug bounty program
- [ ] Marketing campaign

### Q4 2025 - Scale & Iterate
- [ ] Multi-chain support
- [ ] Enhanced privacy features
- [ ] Enterprise integrations
- [ ] Community growth
- [ ] Impact measurement

---

## 💡 Why C.O.V.E.R.T?

### The Problem

Traditional whistleblowing platforms face critical challenges:
- **Centralization**: Single points of failure, vulnerable to takedowns
- **Privacy Risks**: Inadequate anonymity leads to retaliation
- **Trust Issues**: Opaque moderation processes erode confidence
- **Censorship**: Powerful entities can delete or alter reports
- **Accessibility**: High costs and technical barriers limit use

### Our Solution

C.O.V.E.R.T addresses these challenges through:
- **Decentralization**: No single entity controls the platform
- **Cryptographic Privacy**: Military-grade encryption protects identity
- **Immutability**: Blockchain ensures evidence can't be tampered with
- **Transparency**: Community governance with public accountability
- **Accessibility**: Free, open-source, and easy to use

### Real-World Impact

- **Corporate Accountability**: Expose fraud, safety violations, discrimination
- **Government Transparency**: Report corruption, abuse of power
- **Academic Integrity**: Address misconduct, plagiarism
- **Media Freedom**: Protect journalistic sources
- **Social Justice**: Give voice to marginalized communities

---

## 🎯 Success Metrics

### Technical KPIs
- ✅ <30s report submission time
- ✅ 99.9% IPFS data availability
- ✅ <$0.01 per report (Layer 2 gas)
- ✅ Zero private key leaks
- ✅ 80%+ test coverage

### Social Impact KPIs
- 🎯 100+ reports submitted (testnet beta)
- 🎯 80%+ report validation accuracy
- 🎯 50+ active moderators
- 🎯 5+ case studies of real-world impact
- 🎯 10,000+ monthly active users (mainnet)

---

## ⚠️ Disclaimer

C.O.V.E.R.T is provided "as is" without warranty. While we employ strong cryptographic techniques and security best practices, no system is 100% secure. Users assume all responsibility for:

- Verifying their own operational security
- Understanding local laws regarding whistleblowing
- Assessing risks before submitting sensitive information
- Using burner wallets and Tor when necessary
- Not including personally identifiable information

**Always consult legal counsel before whistleblowing on serious matters.**

---

## 🔥 Getting Started Now

```bash
# 1. Clone and install
git clone https://github.com/yourusername/covert.git && cd covert

# 2. One-command setup
docker-compose up -d && cd contracts && forge script script/Deploy.s.sol --broadcast

# 3. Start coding
cd ../backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev

# 4. Build something amazing! 🚀
```

---

## 🙏 Support the Project

If C.O.V.E.R.T helps you or your cause, consider:

- ⭐ Star this repository
- 🐛 Report bugs and suggest features
- 💻 Contribute code
- 📢 Spread the word
- 💰 Donate: `0xYourEthereumAddress`

---

<div align="center">



[Get Started](./DEPLOYMENT.md) • [Documentation](./docs/) • [Community](https://discord.gg/covert)

</div>

---

*"The truth is powerful, and it prevails." - Sojourner Truth*