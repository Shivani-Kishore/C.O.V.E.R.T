# C.O.V.E.R.T Deployment Guide

## Complete Setup Instructions for Local, Testnet, and Production

---

## Prerequisites

### Required Software

```bash
# Node.js 18+ and npm
node --version  # v18.0.0+
npm --version   # v9.0.0+

# Python 3.11+
python --version  # 3.11.0+

# Docker and Docker Compose
docker --version  # 20.10.0+
docker-compose --version  # 2.0.0+

# Git
git --version  # 2.30.0+

# PostgreSQL (if not using Docker)
psql --version  # 15.0+

# Foundry (for smart contracts)
forge --version  # Latest from foundry
```

---

## Part 1: Local Development Setup

### Step 1: Clone Repository

```bash
# Clone the project
git clone https://github.com/yourusername/covert.git
cd covert

# Project structure
covert/
├── frontend/           # React application
├── backend/            # FastAPI application
├── contracts/          # Solidity smart contracts
├── docs/              # Documentation
└── docker-compose.yml
```

### Step 2: Environment Variables

```bash
# Create .env files for each component

# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/covert
REDIS_URL=redis://localhost:6379/0
IPFS_URL=/ip4/127.0.0.1/tcp/5001
RPC_URL=https://sepolia.base.org
COMMITMENT_REGISTRY_ADDRESS=
DAILY_ANCHOR_ADDRESS=
SECRET_KEY=your-secret-key-change-this
ENCRYPTION_KEY=your-encryption-key-change-this
PINATA_JWT=your-pinata-jwt-optional
WEB3_STORAGE_TOKEN=your-web3storage-token-optional

# frontend/.env
VITE_API_URL=http://localhost:8000/api/v1
VITE_IPFS_GATEWAY=http://localhost:8080/ipfs
VITE_RPC_URL=https://sepolia.base.org
VITE_CHAIN_ID=84532
VITE_COMMITMENT_REGISTRY_ADDRESS=
VITE_COV_CREDITS_ADDRESS=
VITE_COVERT_BADGES_ADDRESS=
VITE_COVERT_PROTOCOL_ADDRESS=

# contracts/.env
PRIVATE_KEY=your-private-key-for-deployment
BASE_SEPOLIA_RPC=https://sepolia.base.org
ETHERSCAN_API_KEY=your-etherscan-api-key-optional
```

### Step 3: Start Infrastructure with Docker

```bash
# Start PostgreSQL, Redis, and IPFS
docker-compose up -d postgres redis ipfs

# Verify services are running
docker ps

# Check logs
docker-compose logs -f
```

### Step 4: Setup Smart Contracts

```bash
cd contracts

# Install Foundry if not installed
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install dependencies
forge install

# Compile contracts
forge build

# Run tests
forge test -vv

# Start local blockchain (Anvil)
anvil --chain-id 31337 --port 8545

# Deploy contracts (new terminal)
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url http://localhost:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Copy deployed addresses to .env files
# Look for "CommitmentRegistry deployed to: 0x..."
```

### Step 5: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

### Step 6: Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Application should be available at http://localhost:5173
```

### Step 7: Verify Installation

```bash
# Test API health
curl http://localhost:8000/health

# Test IPFS
curl http://localhost:5001/api/v0/version

# Test PostgreSQL
psql postgresql://postgres:password@localhost:5432/covert -c "SELECT 1;"

# Test Redis
redis-cli ping
```

---

## Part 2: Testnet Deployment (Base Sepolia)

### Step 1: Get Test ETH

```bash
# Visit Base Sepolia faucet
# https://www.coinbase.com/faucets/base-ethereum-goerli-faucet

# Or use Alchemy/QuickNode faucets
# You'll need ~0.5 test ETH for deployment and testing
```

### Step 2: Deploy Smart Contracts to Testnet

```bash
cd contracts

# Update contracts/.env with your private key
export PRIVATE_KEY=0xyourprivatekeyhere
export BASE_SEPOLIA_RPC=https://sepolia.base.org

# Deploy to Base Sepolia
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --private-key $PRIVATE_KEY

# Save deployed addresses
# Example output:
# CommitmentRegistry: 0x1234...
# DailyAnchor: 0x5678...
# COVCredits: 0x9abc...
# CovertBadges: 0xdef0...
# CovertProtocol: 0x1357...

# Update .env files with these addresses
```

### Step 3: Deploy Backend to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add PostgreSQL database
railway add postgresql

# Add Redis
railway add redis

# Set environment variables
railway variables set DATABASE_URL=<postgres-url>
railway variables set REDIS_URL=<redis-url>
railway variables set IPFS_URL=/dns4/ipfs.io/tcp/443/https
railway variables set RPC_URL=https://sepolia.base.org
railway variables set COMMITMENT_REGISTRY_ADDRESS=0x1234...

# Deploy
railway up

# Get deployment URL
railway domain

# Your API will be available at:
# https://covert-backend.railway.app
```

### Step 4: Setup IPFS Pinning Services

#### Pinata (1GB Free)

```bash
# Sign up at https://pinata.cloud
# Get JWT token from dashboard
# Add to Railway environment variables
railway variables set PINATA_JWT=your-jwt-token
```

#### Web3.Storage (Unlimited Free)

```bash
# Sign up at https://web3.storage
# Get API token
# Add to Railway environment variables
railway variables set WEB3_STORAGE_TOKEN=your-token
```

### Step 5: Deploy Frontend to Vercel/Netlify

#### Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Set environment variables in Vercel dashboard
# - VITE_API_URL=https://covert-backend.railway.app/api/v1
# - VITE_RPC_URL=https://sepolia.base.org
# - VITE_COMMITMENT_REGISTRY_ADDRESS=0x1234...

# Deploy to production
vercel --prod

# Your frontend will be at:
# https://covert.vercel.app
```

#### Netlify Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Initialize
cd frontend
netlify init

# Build
npm run build

# Deploy
netlify deploy --prod

# Set environment variables in Netlify dashboard
```

---

## Part 3: Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Cloudflare CDN                        │
│              (DDoS Protection, Caching)                  │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
    ┌─────▼──────┐         ┌─────▼──────┐
    │  Frontend  │         │  Backend   │
    │  (Vercel)  │         │ (Railway)  │
    └────────────┘         └─────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼────┐ ┌────▼─────┐ ┌───▼────┐
              │PostgreSQL│ │  Redis   │ │  IPFS  │
              │(Railway) │ │(Railway) │ │(Pinata)│
              └──────────┘ └──────────┘ └────────┘
```

### Step 1: Domain Setup

```bash
# Purchase domain (e.g., covert.app)
# Configure DNS in Cloudflare:

# Frontend
covert.app           A     76.76.21.21  (Vercel IP)
www.covert.app       CNAME covert.app

# API
api.covert.app       CNAME covert-backend.railway.app

# IPFS Gateway (optional)
ipfs.covert.app      CNAME gateway.pinata.cloud
```

### Step 2: SSL/TLS Setup

```bash
# Cloudflare handles SSL automatically
# Vercel provides SSL out of the box
# Railway provides SSL out of the box

# Verify SSL
curl -I https://covert.app
curl -I https://api.covert.app
```

### Step 3: Environment Variables (Production)

```bash
# Backend (Railway Production)
railway variables set NODE_ENV=production
railway variables set DEBUG=false
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set ENCRYPTION_KEY=$(openssl rand -hex 32)
railway variables set DATABASE_URL=<production-postgres>
railway variables set REDIS_URL=<production-redis>
railway variables set RPC_URL=https://mainnet.base.org  # Mainnet when ready
railway variables set SENTRY_DSN=your-sentry-dsn  # Error tracking

# Frontend (Vercel Production)
vercel env add VITE_API_URL production
# Value: https://api.covert.app/api/v1

vercel env add VITE_RPC_URL production
# Value: https://mainnet.base.org

vercel env add VITE_CHAIN_ID production
# Value: 8453  # Base mainnet
```

### Step 4: Database Backups

```bash
# Railway automatic backups (included)
# Manual backup script:

# Create backup script: scripts/backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL | gzip > backups/covert_$DATE.sql.gz

# Upload to S3 or similar
aws s3 cp backups/covert_$DATE.sql.gz s3://covert-backups/

# Keep last 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete

# Schedule with cron
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Step 5: Monitoring Setup

#### Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]

# Add to backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
    traces_sample_rate=0.1
)

# Frontend monitoring
npm install @sentry/react

# Add to frontend/src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-frontend-sentry-dsn",
  environment: "production"
});
```

#### Uptime Monitoring

```bash
# Use UptimeRobot (free)
# Monitor:
# - https://covert.app (frontend)
# - https://api.covert.app/health (backend API)
# - IPFS gateway availability

# Or use Betteruptime, Pingdom, etc.
```

### Step 6: Performance Optimization

```bash
# Frontend optimizations
cd frontend

# Build for production
npm run build

# Analyze bundle size
npm install -g source-map-explorer
source-map-explorer dist/assets/*.js

# Enable gzip/brotli compression (automatic in Vercel)

# Backend optimizations
# Add to backend requirements.txt:
gunicorn==21.2.0

# Update Procfile for Railway:
web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

---

## Part 4: CI/CD Setup

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy C.O.V.E.R.T

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
      
      - name: Run tests
        run: |
          cd contracts
          forge test -vv

  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test
      
      - name: Build
        run: |
          cd frontend
          npm run build

  deploy-backend:
    needs: [test-backend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    needs: [test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          cd frontend
          vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

## Part 5: Security Hardening

### Backend Security

```python
# Add security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS in production
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)

# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Database Security

```bash
# Encrypt database connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Rotate credentials monthly
railway variables set DATABASE_PASSWORD=$(openssl rand -base64 32)

# Enable audit logging
ALTER DATABASE covert SET log_statement = 'all';
```

### API Rate Limiting (Production)

```python
# Use Redis for distributed rate limiting
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

@app.on_event("startup")
async def startup():
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_client)

# Apply to routes
@app.post("/api/v1/reports/submit")
@limiter.limit("10/hour")
async def submit_report(...):
    pass
```

---

## Part 6: Disaster Recovery

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
# scripts/backup_all.sh

echo "Starting backup..."

# Database backup
pg_dump $DATABASE_URL | gzip > db_backup_$(date +%Y%m%d).sql.gz

# IPFS pins export
ipfs pin ls > ipfs_pins_$(date +%Y%m%d).txt

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz backend/.env frontend/.env

# Upload to S3
aws s3 sync . s3://covert-backups/$(date +%Y%m%d)/ \
  --exclude "*" \
  --include "*.sql.gz" \
  --include "*.txt" \
  --include "*.tar.gz"

echo "Backup complete!"
```

### Recovery Procedure

```bash
# Restore database
gunzip < db_backup_20240115.sql.gz | psql $DATABASE_URL

# Re-pin IPFS content
while read cid; do
  ipfs pin add $cid
done < ipfs_pins_20240115.txt

# Restore configuration
tar -xzf config_backup_20240115.tar.gz
```

---

## Part 7: Monitoring Dashboard

### Prometheus + Grafana Setup

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'covert-backend'
    static_configs:
      - targets: ['api.covert.app:8000']
  
  - job_name: 'ipfs'
    static_configs:
      - targets: ['localhost:5001']
```

---

## Part 8: Performance Testing

### Load Testing with Locust

```python
# tests/load_test.py
from locust import HttpUser, task, between

class CovertUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_reports(self):
        self.client.get("/api/v1/reports/list")
    
    @task(1)
    def submit_report(self):
        self.client.post("/api/v1/reports/submit", data={
            "cid": "bafytest123",
            "cid_hash": "0xabc...",
            "tx_hash": "0xdef...",
            "category": "corruption",
            "visibility": 1,
            "size_bytes": 102400
        })

# Run test
# locust -f tests/load_test.py --host=https://api.covert.app
```

---

## Part 9: Maintenance Procedures

### Weekly Maintenance

```bash
# Update dependencies
cd backend && pip list --outdated
cd frontend && npm outdated

# Check disk space
df -h

# Review logs
railway logs --tail 100

# Database vacuum
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# IPFS garbage collection
ipfs repo gc
```

### Monthly Maintenance

```bash
# Rotate encryption keys
python scripts/rotate_keys.py

# Security audit
npm audit
pip-audit

# Update SSL certificates (auto-renewed by Cloudflare)

# Review and archive old data
python scripts/archive_old_reports.py
```

---

## Part 10: Troubleshooting

### Common Issues

#### Issue 1: IPFS Connection Failed

```bash
# Check IPFS daemon
docker-compose logs ipfs

# Restart IPFS
docker-compose restart ipfs

# Test connection
curl http://localhost:5001/api/v0/version
```

#### Issue 2: Database Connection Timeout

```bash
# Check connection pool
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in backend/app/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from 5
    max_overflow=40
)
```

#### Issue 3: High Memory Usage

```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart backend celery_worker

# Scale down workers
railway scale backend --replicas 2
```

#### Issue 4: Smart Contract Call Failed

```bash
# Check gas price
cast gas-price --rpc-url https://sepolia.base.org

# Check wallet balance
cast balance 0xYourAddress --rpc-url https://sepolia.base.org

# Retry with higher gas
# Update transaction with higher maxFeePerGas
```

---

## Part 11: Cost Estimation

### Free Tier Setup (Testnet)

```
Service               | Free Tier           | Cost
----------------------|---------------------|-------
Railway (Backend)     | $5 credit/month     | $0
Vercel (Frontend)     | Unlimited           | $0
PostgreSQL (Railway)  | Included            | $0
Redis (Railway)       | Included            | $0
IPFS (Pinata)         | 1GB                 | $0
Web3.Storage          | Unlimited           | $0
Base Sepolia RPC      | Free                | $0
Cloudflare            | Free tier           | $0
Domain                | $10-15/year         | ~$1/mo
----------------------|---------------------|-------
TOTAL                                       | ~$1/mo
```

### Production Cost (Mainnet - Estimated)

```
Service               | Tier                | Monthly Cost
----------------------|---------------------|-------------
Railway Pro           | 8GB RAM, 4 vCPU     | $20
Vercel Pro            | Unlimited           | $0 (can stay free)
PostgreSQL            | 10GB                | Included
Redis                 | 256MB               | Included
IPFS Pinning          | 10GB                | $2 (Pinata)
RPC (Alchemy)         | 3M req/mo           | $0
Domain + SSL          | covert.app          | $1
Monitoring (Sentry)   | 10k events/mo       | $0
----------------------|---------------------|-------------
TOTAL                                       | ~$23/mo
```

---

## Part 12: Launch Checklist

### Pre-Launch

- [ ] All tests passing (contracts, backend, frontend)
- [ ] Smart contracts deployed and verified
- [ ] Security audit completed
- [ ] Documentation complete
- [ ] Backup procedures tested
- [ ] Monitoring configured
- [ ] Rate limiting enabled
- [ ] SSL certificates valid
- [ ] IPFS pinning services configured
- [ ] Error tracking (Sentry) configured

### Launch Day

- [ ] Deploy contracts to mainnet
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Update DNS records
- [ ] Enable CDN caching
- [ ] Monitor for errors
- [ ] Announce on social media
- [ ] Prepare support channels

### Post-Launch

- [ ] Monitor performance metrics
- [ ] Review error logs daily
- [ ] Collect user feedback
- [ ] Plan feature iterations
- [ ] Regular security updates

---

## Support & Resources

### Getting Help

- **Documentation**: https://docs.covert.app
- **GitHub Issues**: https://github.com/yourusername/covert/issues
- **Discord Community**: https://discord.gg/covert
- **Email Support**: support@covert.app

### Useful Links

- **Base Sepolia Faucet**: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
- **Alchemy Dashboard**: https://dashboard.alchemy.com
- **Railway Dashboard**: https://railway.app/dashboard
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Pinata Dashboard**: https://app.pinata.cloud

---

*Last Updated: November 2025*
*Deployment Version: 1.0.0*