# C.O.V.E.R.T Environment Variables Configuration

## Overview

This document provides a complete reference for all environment variables used across the C.O.V.E.R.T platform. Variables are organized by service and environment (development, staging, production).

## Table of Contents

1. [Frontend Variables](#frontend-variables)
2. [Backend Variables](#backend-variables)
3. [Smart Contract Variables](#smart-contract-variables)
4. [Shared Variables](#shared-variables)
5. [Environment-Specific Configurations](#environment-specific-configurations)
6. [Security Best Practices](#security-best-practices)

---

## Frontend Variables

### `.env` (Development)

```bash
# App Configuration
VITE_APP_NAME=C.O.V.E.R.T
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development

# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws

# Blockchain Configuration
VITE_CHAIN_ID=80001  # Polygon Mumbai Testnet
VITE_CHAIN_NAME=Mumbai
VITE_RPC_URL=https://rpc-mumbai.maticvigil.com
VITE_BLOCK_EXPLORER=https://mumbai.polygonscan.com

# Smart Contract Addresses (Testnet)
VITE_COMMITMENT_REGISTRY_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
VITE_DAILY_ANCHOR_ADDRESS=0x123456789abcdef123456789abcdef123456789a
VITE_REPUTATION_SBT_ADDRESS=0xabcdef123456789abcdef123456789abcdef1234
VITE_DISPUTE_MANAGER_ADDRESS=0x9876543210fedcba9876543210fedcba98765432
VITE_DAO_ADDRESS=0x1111111111111111111111111111111111111111

# IPFS Configuration
VITE_IPFS_GATEWAY=https://nftstorage.link/ipfs
VITE_IPFS_API_URL=https://api.nft.storage
VITE_NFT_STORAGE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Get from nft.storage

# Encryption Settings
VITE_ENCRYPTION_ALGORITHM=AES-256-GCM
VITE_KEY_DERIVATION=PBKDF2
VITE_PBKDF2_ITERATIONS=100000

# Feature Flags
VITE_ENABLE_ZKP=true
VITE_ENABLE_AI_CREDIBILITY=true
VITE_ENABLE_DISPUTES=true
VITE_ENABLE_DAO=false
VITE_ENABLE_ANALYTICS=true

# Analytics (Optional)
VITE_GOOGLE_ANALYTICS_ID=
VITE_SENTRY_DSN=

# Development Tools
VITE_ENABLE_DEVTOOLS=true
VITE_MOCK_BLOCKCHAIN=false
VITE_MOCK_IPFS=false

# Rate Limiting
VITE_MAX_FILE_SIZE=10485760  # 10MB in bytes
VITE_MAX_FILES_PER_REPORT=5
VITE_RATE_LIMIT_REPORTS_PER_DAY=10

# UI Configuration
VITE_THEME=light
VITE_DEFAULT_LANGUAGE=en
VITE_ENABLE_ANIMATIONS=true
```

### `.env.production` (Production)

```bash
# App Configuration
VITE_APP_ENV=production
VITE_API_BASE_URL=https://api.covert.io/api
VITE_WS_URL=wss://api.covert.io/ws

# Blockchain Configuration (Mainnet)
VITE_CHAIN_ID=137  # Polygon Mainnet
VITE_CHAIN_NAME=Polygon
VITE_RPC_URL=https://polygon-rpc.com
VITE_BLOCK_EXPLORER=https://polygonscan.com

# Smart Contract Addresses (Mainnet)
VITE_COMMITMENT_REGISTRY_ADDRESS=0x...  # Deploy and update
VITE_DAILY_ANCHOR_ADDRESS=0x...
VITE_REPUTATION_SBT_ADDRESS=0x...
VITE_DISPUTE_MANAGER_ADDRESS=0x...
VITE_DAO_ADDRESS=0x...

# IPFS Configuration
VITE_IPFS_GATEWAY=https://nftstorage.link/ipfs
VITE_IPFS_API_URL=https://api.nft.storage
VITE_NFT_STORAGE_API_KEY=${NFT_STORAGE_API_KEY}  # From secrets

# Feature Flags
VITE_ENABLE_DEVTOOLS=false
VITE_MOCK_BLOCKCHAIN=false
VITE_MOCK_IPFS=false

# Analytics
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
VITE_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## Backend Variables

### `.env` (Development)

```bash
# Application Settings
APP_NAME=C.O.V.E.R.T API
APP_ENV=development
APP_DEBUG=true
APP_VERSION=1.0.0
APP_HOST=0.0.0.0
APP_PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ENCRYPTION_KEY=your-encryption-key-32-bytes-exactly!!!

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=true

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/covert_dev
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=false  # Set to true for SQL logging

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Blockchain Configuration
WEB3_PROVIDER_URL=https://rpc-mumbai.maticvigil.com
CHAIN_ID=80001
PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef  # For backend tx signing

# Smart Contract Addresses
COMMITMENT_REGISTRY_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
DAILY_ANCHOR_ADDRESS=0x123456789abcdef123456789abcdef123456789a
REPUTATION_SBT_ADDRESS=0xabcdef123456789abcdef123456789abcdef1234
DISPUTE_MANAGER_ADDRESS=0x9876543210fedcba9876543210fedcba98765432

# IPFS Configuration
IPFS_API_URL=https://api.nft.storage/upload
IPFS_GATEWAY_URL=https://nftstorage.link/ipfs
NFT_STORAGE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI/ML Configuration
AI_MODEL_PATH=/models
HUGGINGFACE_MODEL=distilbert-base-uncased
TORCH_HOME=/tmp/torch
TRANSFORMERS_CACHE=/tmp/transformers
AI_BATCH_SIZE=8
AI_MAX_LENGTH=512
AI_CONFIDENCE_THRESHOLD=0.7

# Celery Configuration (Async Tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@covert.io
SMTP_TLS=true

# Monitoring & Logging
LOG_LEVEL=INFO
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_STORAGE=redis://localhost:6379/3

# File Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,doc,docx,txt
UPLOAD_TEMP_DIR=/tmp/uploads

# Zero-Knowledge Proofs
ZKP_PROVING_KEY_PATH=/zkp/proving_key.zkey
ZKP_VERIFICATION_KEY_PATH=/zkp/verification_key.json
ZKP_WASM_PATH=/zkp/circuit.wasm
ZKP_CIRCUIT_NAME=humanity_proof

# Feature Flags
ENABLE_AI_MODERATION=true
ENABLE_AUTOMATIC_ANCHORING=true
ENABLE_DISPUTE_RESOLUTION=true
ENABLE_FEDERATED_LEARNING=false
ENABLE_HOMOMORPHIC_ENCRYPTION=false

# Testing
TESTING=false
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/covert_test
```

### `.env.production` (Production)

```bash
# Application Settings
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# Security (Use secrets management)
SECRET_KEY=${SECRET_KEY}  # From AWS Secrets Manager / Vault
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# CORS Settings
CORS_ORIGINS=https://covert.io,https://www.covert.io
CORS_ALLOW_CREDENTIALS=true

# Database Configuration (Production)
DATABASE_URL=${DATABASE_URL}  # From secrets
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
DATABASE_ECHO=false

# Redis Configuration
REDIS_URL=${REDIS_URL}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_MAX_CONNECTIONS=100

# Blockchain Configuration (Mainnet)
WEB3_PROVIDER_URL=https://polygon-rpc.com
CHAIN_ID=137
PRIVATE_KEY=${PRIVATE_KEY}  # From secrets

# Monitoring
LOG_LEVEL=WARNING
SENTRY_DSN=${SENTRY_DSN}
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.01

# Rate Limiting (Stricter in production)
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# Feature Flags
ENABLE_AI_MODERATION=true
ENABLE_AUTOMATIC_ANCHORING=true
```

---

## Smart Contract Variables

### `foundry.toml`

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.20"
optimizer = true
optimizer_runs = 200
via_ir = true

[profile.production]
optimizer_runs = 999999
via_ir = true

[rpc_endpoints]
mumbai = "${MUMBAI_RPC_URL}"
polygon = "${POLYGON_RPC_URL}"
arbitrum_goerli = "${ARBITRUM_GOERLI_RPC_URL}"
arbitrum = "${ARBITRUM_RPC_URL}"

[etherscan]
mumbai = { key = "${POLYGONSCAN_API_KEY}" }
polygon = { key = "${POLYGONSCAN_API_KEY}" }
arbitrum = { key = "${ARBISCAN_API_KEY}" }
```

### `.env` (Contracts)

```bash
# Network Configuration
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_GOERLI_RPC_URL=https://goerli-rollup.arbitrum.io/rpc
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Deployment Keys
DEPLOYER_PRIVATE_KEY=0x...  # Testnet deployer
MAINNET_DEPLOYER_PRIVATE_KEY=${MAINNET_DEPLOYER_PRIVATE_KEY}  # From secrets

# Explorer API Keys
POLYGONSCAN_API_KEY=YOUR_POLYGONSCAN_API_KEY
ARBISCAN_API_KEY=YOUR_ARBISCAN_API_KEY

# Chainlink VRF (for disputes)
VRF_COORDINATOR_MUMBAI=0x7a1BaC17Ccc5b313516C5E16fb24f7659aA5ebed
VRF_KEY_HASH_MUMBAI=0x4b09e658ed251bcafeebbc69400383d49f344ace09b9576fe248bb02c003fe9f
VRF_SUBSCRIPTION_ID=12345

# Gas Settings
GAS_PRICE_GWEI=50
GAS_LIMIT=8000000

# Contract Verification
VERIFY_CONTRACTS=true
VERIFY_DELAY=30  # seconds to wait before verification
```

---

## Shared Variables

### Common Across All Services

```bash
# Environment
NODE_ENV=development  # development | staging | production
TZ=UTC

# Logging
LOG_FORMAT=json  # json | text
LOG_TIMESTAMP=true

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090

# Health Checks
HEALTH_CHECK_INTERVAL=30  # seconds
```

---

## Environment-Specific Configurations

### Development Environment

**Purpose**: Local development and testing

**Characteristics**:
- Verbose logging
- Hot reloading enabled
- Mock services optional
- Debug tools enabled
- Testnet blockchain
- Local databases

**File**: `.env.development`

### Staging Environment

**Purpose**: Pre-production testing

**Characteristics**:
- Production-like setup
- Test data allowed
- Monitoring enabled
- Testnet blockchain (initially)
- Cloud databases
- Performance testing

**File**: `.env.staging`

```bash
APP_ENV=staging
APP_DEBUG=false
DATABASE_URL=${STAGING_DATABASE_URL}
REDIS_URL=${STAGING_REDIS_URL}
CORS_ORIGINS=https://staging.covert.io
SENTRY_ENVIRONMENT=staging
```

### Production Environment

**Purpose**: Live system

**Characteristics**:
- Minimal logging
- All optimizations enabled
- No debug tools
- Mainnet blockchain
- Managed databases
- Full monitoring
- Secrets from vault

**File**: `.env.production`

---

## Docker Compose Variables

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  frontend:
    env_file:
      - ./frontend/.env
    environment:
      - NODE_ENV=${NODE_ENV:-development}

  backend:
    env_file:
      - ./backend/.env
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/covert_dev
      - REDIS_URL=redis://redis:6379/0

  db:
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=covert_dev

  redis:
    environment:
      - REDIS_PASSWORD=

  ipfs:
    environment:
      - IPFS_PATH=/data/ipfs
```

---

## Security Best Practices

### 1. Never Commit Secrets

**Add to `.gitignore`**:
```gitignore
# Environment files
.env
.env.local
.env.production
.env.staging
.env.*.local

# Secrets
secrets/
*.pem
*.key
*.p12

# Credentials
credentials.json
service-account.json
```

### 2. Use Environment-Specific Files

```bash
# Development
.env.development

# Staging
.env.staging

# Production (never commit this!)
.env.production
```

### 3. Template Files for Team

**`.env.example`** (Safe to commit):
```bash
# App Configuration
VITE_APP_NAME=C.O.V.E.R.T
VITE_API_BASE_URL=http://localhost:8000/api

# Blockchain (Use testnet for development)
VITE_CHAIN_ID=80001
VITE_RPC_URL=https://rpc-mumbai.maticvigil.com

# Secrets (DO NOT commit actual values)
SECRET_KEY=generate-your-own-secret-key
JWT_SECRET_KEY=generate-your-own-jwt-secret
ENCRYPTION_KEY=exactly-32-bytes-for-aes-256!!
PRIVATE_KEY=your-ethereum-private-key-here

# API Keys
NFT_STORAGE_API_KEY=get-from-https://nft.storage
POLYGONSCAN_API_KEY=get-from-https://polygonscan.com
```

### 4. Secrets Management

**Development**: Use `.env` files locally
**Production**: Use secrets management service

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id covert/prod/database

# HashiCorp Vault
vault kv get secret/covert/production

# Kubernetes Secrets
kubectl get secret covert-secrets -o yaml
```

### 5. Environment Variable Validation

**Backend (Pydantic Settings)**:
```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "C.O.V.E.R.T"
    app_env: str
    secret_key: str
    database_url: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v

settings = Settings()
```

**Frontend (Vite)**:
```typescript
// frontend/src/config.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  chainId: Number(import.meta.env.VITE_CHAIN_ID) || 80001,
  // ...
} as const;

// Validation
if (!config.apiUrl) {
  throw new Error('VITE_API_BASE_URL is required');
}
```

### 6. Key Rotation

**Regular rotation schedule**:
- JWT Secret: Every 90 days
- Encryption Keys: Every 180 days
- API Keys: Every 365 days
- Database Passwords: Every 90 days

**Rotation script**:
```bash
#!/bin/bash
# scripts/rotate-secrets.sh

# Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# Update in secrets manager
aws secretsmanager update-secret \
  --secret-id covert/prod/jwt-secret \
  --secret-string "$NEW_SECRET"

# Trigger rolling deployment
kubectl rollout restart deployment/covert-api
```

---

## Environment Variable Checklist

### Pre-Deployment Checklist

- [ ] All secrets are stored in secrets manager
- [ ] `.env.production` is not committed to git
- [ ] Environment variables are documented
- [ ] Validation is implemented for critical vars
- [ ] Default values are sensible
- [ ] Production uses strong secrets (min 32 chars)
- [ ] Database connections use SSL
- [ ] Redis has password protection
- [ ] CORS origins are restricted
- [ ] Debug mode is disabled in production
- [ ] Rate limits are configured
- [ ] Monitoring is enabled
- [ ] Backup credentials are secured

### Development Setup Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Generate local secrets
- [ ] Configure database connection
- [ ] Set up IPFS credentials
- [ ] Configure blockchain RPC
- [ ] Test all services start correctly

---

## Quick Reference

### Generate Secrets

```bash
# Generate 32-byte secret
openssl rand -hex 32

# Generate JWT secret
openssl rand -base64 32

# Generate encryption key (exactly 32 bytes)
openssl rand -base64 32 | head -c 32
```

### Validate Environment

```bash
# Check all required variables are set
./scripts/check-env.sh

# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Test Redis connection
redis-cli -u $REDIS_URL ping
```

---

This comprehensive environment variable configuration ensures secure, maintainable, and well-documented configuration management across all C.O.V.E.R.T services.
