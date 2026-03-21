# C.O.V.E.R.T API Examples

## Overview

This document provides comprehensive working examples for all API endpoints in the C.O.V.E.R.T platform. Each example includes complete request/response payloads, authentication headers, error handling, and common use cases.

## Base URL

```
Development: http://localhost:8000/api
Production: https://api.covert.io/api
```

## Authentication

Most endpoints require authentication via JWT token obtained from wallet signature.

### Headers

```http
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Report Endpoints](#report-endpoints)
3. [Moderation Endpoints](#moderation-endpoints)
4. [Moderator Endpoints](#moderator-endpoints)
5. [Dispute Endpoints](#dispute-endpoints)
6. [Analytics Endpoints](#analytics-endpoints)
7. [Utility Endpoints](#utility-endpoints)
8. [WebSocket Events](#websocket-events)

---

## Authentication Endpoints

### 1. Request Authentication Challenge

Generate a message to sign with wallet.

**Endpoint**: `POST /auth/challenge`

**Request**:
```http
POST /api/auth/challenge HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response** (200 OK):
```json
{
  "challenge": "Sign this message to authenticate with C.O.V.E.R.T:\n\nTimestamp: 2024-01-15T10:30:00Z\nNonce: a1b2c3d4e5f6",
  "nonce": "a1b2c3d4e5f6",
  "expires_at": "2024-01-15T10:35:00Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'
```

### 2. Verify Signature & Login

Verify wallet signature and receive JWT token.

**Endpoint**: `POST /auth/verify`

**Request**:
```http
POST /api/auth/verify HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signature": "0x1234567890abcdef...",
  "nonce": "a1b2c3d4e5f6",
  "role": "reporter"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIweDc0MmQzNUNjNjYzNEMwNTMyOTI1YTNiODQ0QmM5ZTc1OTVmMGJFYiIsInJvbGUiOiJyZXBvcnRlciIsImV4cCI6MTcwNTMxNzAwMH0.xyz",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIweDc0MmQzNUNjNjYzNEMwNTMyOTI1YTNiODQ0QmM5ZTc1OTVmMGJFYiIsInR5cGUiOiJyZWZyZXNoIiwiZXhwIjoxNzA1OTAzNDAwfQ.abc",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "role": "reporter"
  }
}
```

**JavaScript Example**:
```javascript
const ethers = require('ethers');

async function login() {
  // Step 1: Get challenge
  const challengeRes = await fetch('http://localhost:8000/api/auth/challenge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      wallet_address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
    })
  });
  const { challenge, nonce } = await challengeRes.json();
  
  // Step 2: Sign challenge
  const signer = new ethers.Wallet(PRIVATE_KEY);
  const signature = await signer.signMessage(challenge);
  
  // Step 3: Verify signature
  const verifyRes = await fetch('http://localhost:8000/api/auth/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      wallet_address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
      signature,
      nonce,
      role: 'reporter'
    })
  });
  
  const { access_token } = await verifyRes.json();
  return access_token;
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid signature",
  "error_code": "INVALID_SIGNATURE"
}
```

### 3. Refresh Token

Get new access token using refresh token.

**Endpoint**: `POST /auth/refresh`

**Request**:
```http
POST /api/auth/refresh HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Report Endpoints

### 1. Submit Report

Submit a new whistleblower report.

**Endpoint**: `POST /reports/submit`

**Authentication**: Required (Reporter or Anonymous with ZKP)

**Request**:
```http
POST /api/reports/submit HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
  "commitment_hash": "0xa1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
  "transaction_hash": "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
  "encrypted_category": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y=",
  "encrypted_title": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96jq...",
  "encrypted_summary": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96jq...",
  "file_size": 2457600,
  "file_type": "application/pdf",
  "visibility": "moderated",
  "chain_id": 80001,
  "reporter_nullifier": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "zkp_proof": {
    "proof": "0x...",
    "public_signals": ["0x..."]
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "commitment_hash": "0xa1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
  "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
  "transaction_hash": "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
  "status": "pending",
  "visibility": "moderated",
  "submission_timestamp": "2024-01-15T10:30:00Z",
  "ipfs_gateway_url": "https://nftstorage.link/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
  "blockchain_explorer_url": "https://mumbai.polygonscan.com/tx/0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba"
}
```

**Python Example**:
```python
import requests
import json

def submit_report(access_token, encrypted_data, ipfs_cid, tx_hash):
    url = "http://localhost:8000/api/reports/submit"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "ipfs_cid": ipfs_cid,
        "commitment_hash": "0xa1b2c3d4...",
        "transaction_hash": tx_hash,
        "encrypted_category": encrypted_data["category"],
        "encrypted_title": encrypted_data["title"],
        "encrypted_summary": encrypted_data["summary"],
        "file_size": 2457600,
        "visibility": "moderated",
        "chain_id": 80001
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Commitment hash already exists",
  "error_code": "DUPLICATE_COMMITMENT",
  "existing_report_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Get Report by ID

Retrieve a specific report by its ID.

**Endpoint**: `GET /reports/{report_id}`

**Authentication**: Required

**Request**:
```http
GET /api/reports/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "commitment_hash": "0xa1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
  "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
  "ipfs_gateway_url": "https://nftstorage.link/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
  "transaction_hash": "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
  "block_number": 12345678,
  "chain_id": 80001,
  "status": "under_review",
  "visibility": "moderated",
  "verification_score": 0.87,
  "risk_level": "medium",
  "file_size": 2457600,
  "submission_timestamp": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:22:00Z",
  "moderations": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "action": "review_started",
      "created_at": "2024-01-15T14:00:00Z"
    }
  ],
  "timeline": [
    {
      "event": "submitted",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "event": "ai_analysis_completed",
      "timestamp": "2024-01-15T10:31:00Z",
      "data": {
        "credibility_score": 0.87,
        "risk_level": "medium"
      }
    },
    {
      "event": "assigned_to_moderator",
      "timestamp": "2024-01-15T14:00:00Z"
    }
  ]
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/reports/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. List Reports

Get paginated list of reports with filters.

**Endpoint**: `GET /reports`

**Query Parameters**:
- `status` (optional): Filter by status (pending, under_review, verified, rejected)
- `visibility` (optional): Filter by visibility (private, moderated, public)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `sort_by` (optional): Sort field (created_at, updated_at, verification_score)
- `sort_order` (optional): Sort order (asc, desc)

**Request**:
```http
GET /api/reports?status=pending&per_page=10&page=1&sort_by=submission_timestamp&sort_order=desc HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "commitment_hash": "0xa1b2c3d4...",
      "status": "pending",
      "verification_score": 0.87,
      "submission_timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "commitment_hash": "0xb2c3d4e5...",
      "status": "pending",
      "verification_score": 0.92,
      "submission_timestamp": "2024-01-15T09:15:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 10,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

### 4. Update Report Status

Update the status of a report (moderators only).

**Endpoint**: `PATCH /reports/{report_id}/status`

**Authentication**: Required (Moderator role)

**Request**:
```http
PATCH /api/reports/550e8400-e29b-41d4-a716-446655440000/status HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "status": "verified",
  "reason": "Report verified after thorough review. Evidence is credible and substantial."
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "verified",
  "updated_at": "2024-01-15T15:30:00Z",
  "updated_by": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

---

## Moderation Endpoints

### 1. Get Moderation Queue

Retrieve reports pending moderation.

**Endpoint**: `GET /moderator/queue`

**Authentication**: Required (Moderator role)

**Query Parameters**:
- `risk_level` (optional): Filter by risk (low, medium, high, critical)
- `category` (optional): Filter by category
- `limit` (optional): Number of items (default: 20)

**Request**:
```http
GET /api/moderator/queue?risk_level=high&limit=5 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "queue": [
    {
      "report_id": "550e8400-e29b-41d4-a716-446655440000",
      "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
      "status": "pending",
      "risk_level": "high",
      "verification_score": 0.65,
      "submission_timestamp": "2024-01-15T10:30:00Z",
      "waiting_time_hours": 5.5,
      "ai_recommendation": "accept",
      "ai_confidence": 0.78,
      "ai_flags": [
        "sensitive_content",
        "requires_human_review"
      ],
      "metadata": {
        "file_size": 2457600,
        "encrypted_category": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y="
      }
    }
  ],
  "total_pending": 47,
  "average_wait_time_hours": 3.2,
  "high_priority_count": 5
}
```

### 2. Submit Moderation Decision

Submit a moderation decision for a report.

**Endpoint**: `POST /moderator/decisions`

**Authentication**: Required (Moderator role)

**Request**:
```http
POST /api/moderator/decisions HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "accept",
  "encrypted_notes": "U2FsdGVkX1+encrypted_moderator_notes...",
  "verification_evidence": "Cross-referenced with public records. Sources appear credible.",
  "time_spent_seconds": 1200,
  "tags": ["verified", "high_impact"]
}
```

**Response** (201 Created):
```json
{
  "moderation_id": "770e8400-e29b-41d4-a716-446655440002",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "accept",
  "created_at": "2024-01-15T16:00:00Z",
  "reputation_change": 10,
  "new_reputation_score": 450
}
```

**TypeScript Example**:
```typescript
async function submitModerationDecision(
  reportId: string,
  decision: 'accept' | 'reject' | 'need_info',
  notes: string,
  token: string
) {
  const response = await fetch('http://localhost:8000/api/moderator/decisions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      report_id: reportId,
      decision,
      encrypted_notes: await encryptNotes(notes),
      time_spent_seconds: calculateTimeSpent()
    })
  });
  
  return await response.json();
}
```

---

## Moderator Endpoints

### 1. Get Moderator Profile

Retrieve moderator profile and statistics.

**Endpoint**: `GET /moderator/profile`

**Authentication**: Required (Moderator role)

**Request**:
```http
GET /api/moderator/profile HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "reputation_score": 450,
  "tier": "gold",
  "total_reviews": 120,
  "accurate_reviews": 108,
  "disputed_reviews": 3,
  "accuracy_rate": 0.90,
  "average_review_time_seconds": 1350,
  "consistency_score": 0.85,
  "expertise_areas": ["corruption", "fraud", "safety"],
  "badges": [
    {
      "type": "quick_reviewer",
      "earned_at": "2024-01-10T12:00:00Z"
    },
    {
      "type": "accurate_moderator",
      "earned_at": "2024-01-12T15:00:00Z"
    }
  ],
  "is_active": true,
  "last_active_at": "2024-01-15T16:00:00Z",
  "joined_at": "2023-12-01T10:00:00Z"
}
```

### 2. Get Moderator Statistics

Retrieve detailed moderation statistics.

**Endpoint**: `GET /moderator/statistics`

**Query Parameters**:
- `period` (optional): Time period (day, week, month, year, all)

**Request**:
```http
GET /api/moderator/statistics?period=month HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "period": "month",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "reviews_completed": 45,
  "reviews_by_decision": {
    "accepted": 32,
    "rejected": 10,
    "need_info": 3
  },
  "average_time_per_review_seconds": 1280,
  "fastest_review_seconds": 420,
  "slowest_review_seconds": 3600,
  "reviews_by_category": {
    "corruption": 20,
    "fraud": 15,
    "safety": 10
  },
  "reviews_by_risk_level": {
    "low": 15,
    "medium": 20,
    "high": 8,
    "critical": 2
  },
  "reputation_earned": 150,
  "disputes_received": 1,
  "disputes_upheld": 0
}
```

---

## Dispute Endpoints

### 1. Create Dispute

Create a dispute for a moderation decision.

**Endpoint**: `POST /disputes`

**Authentication**: Required (Moderator role)

**Request**:
```http
POST /api/disputes HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "moderation_id": "770e8400-e29b-41d4-a716-446655440002",
  "reason": "I believe the original decision was incorrect based on the following evidence...",
  "evidence_ipfs_cid": "QmXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx",
  "stake_amount": "0.1"
}
```

**Response** (201 Created):
```json
{
  "dispute_id": "990e8400-e29b-41d4-a716-446655440004",
  "moderation_id": "770e8400-e29b-41d4-a716-446655440002",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "stake_amount": "0.1",
  "jury_size": 5,
  "voting_deadline": "2024-01-22T16:00:00Z",
  "created_at": "2024-01-15T16:00:00Z",
  "blockchain_tx_hash": "0xabc123..."
}
```

### 2. Get Dispute Details

Retrieve dispute information and voting status.

**Endpoint**: `GET /disputes/{dispute_id}`

**Request**:
```http
GET /api/disputes/990e8400-e29b-41d4-a716-446655440004 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "dispute_id": "990e8400-e29b-41d4-a716-446655440004",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "moderation_id": "770e8400-e29b-41d4-a716-446655440002",
  "disputer": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "reason": "I believe the original decision was incorrect...",
  "status": "voting",
  "jury_size": 5,
  "selected_jurors": [
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
    "0x3333333333333333333333333333333333333333",
    "0x4444444444444444444444444444444444444444",
    "0x5555555555555555555555555555555555555555"
  ],
  "votes": {
    "for": 2,
    "against": 1,
    "abstain": 0,
    "pending": 2
  },
  "voting_deadline": "2024-01-22T16:00:00Z",
  "created_at": "2024-01-15T16:00:00Z",
  "stake_amount": "0.1",
  "total_stake": "0.5"
}
```

### 3. Submit Jury Vote

Submit a vote as a jury member.

**Endpoint**: `POST /disputes/{dispute_id}/vote`

**Authentication**: Required (Must be selected juror)

**Request**:
```http
POST /api/disputes/990e8400-e29b-41d4-a716-446655440004/vote HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "vote": "for",
  "encrypted_rationale": "U2FsdGVkX1+encrypted_reasoning...",
  "vote_commitment": "0xcommitment_hash..."
}
```

**Response** (201 Created):
```json
{
  "vote_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "dispute_id": "990e8400-e29b-41d4-a716-446655440004",
  "vote": "for",
  "committed_at": "2024-01-16T10:00:00Z",
  "reveal_deadline": "2024-01-22T16:00:00Z"
}
```

---

## Analytics Endpoints

### 1. Platform Statistics

Get overall platform statistics.

**Endpoint**: `GET /analytics/stats`

**Authentication**: Optional (public data)

**Request**:
```http
GET /api/analytics/stats HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "total_reports": 1247,
  "reports_by_status": {
    "pending": 47,
    "under_review": 23,
    "verified": 892,
    "rejected": 285
  },
  "reports_this_month": 156,
  "average_verification_time_hours": 8.5,
  "total_moderators": 45,
  "active_moderators": 32,
  "average_moderator_reputation": 385,
  "total_disputes": 12,
  "disputes_resolved": 10,
  "platform_uptime_percentage": 99.97
}
```

### 2. Report Trends

Get report submission trends over time.

**Endpoint**: `GET /analytics/trends`

**Query Parameters**:
- `period` (required): Time period (day, week, month, year)
- `metric` (optional): Metric to track (submissions, verifications, disputes)

**Request**:
```http
GET /api/analytics/trends?period=month&metric=submissions HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "period": "month",
  "metric": "submissions",
  "data": [
    {
      "date": "2024-01-01",
      "value": 42
    },
    {
      "date": "2024-01-02",
      "value": 38
    },
    {
      "date": "2024-01-03",
      "value": 51
    }
  ],
  "average": 45.7,
  "trend": "increasing",
  "percentage_change": 12.5
}
```

---

## Utility Endpoints

### 1. Health Check

Check API health status.

**Endpoint**: `GET /health`

**Request**:
```http
GET /api/health HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T16:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ipfs": "healthy",
    "blockchain": "healthy"
  },
  "uptime_seconds": 864000
}
```

### 2. Verify Blockchain Transaction

Verify a blockchain transaction.

**Endpoint**: `GET /utility/verify-tx/{tx_hash}`

**Request**:
```http
GET /api/utility/verify-tx/0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "tx_hash": "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
  "confirmed": true,
  "block_number": 12345678,
  "confirmations": 15,
  "timestamp": "2024-01-15T10:30:00Z",
  "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "to": "0xContractAddress",
  "status": "success"
}
```

---

## WebSocket Events

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleEvent(data);
};
```

### Events

#### Report Status Update

```json
{
  "type": "report_status_update",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "old_status": "pending",
  "new_status": "verified",
  "timestamp": "2024-01-15T16:00:00Z"
}
```

#### Moderation Assignment

```json
{
  "type": "moderation_assigned",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "moderator_id": "880e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2024-01-15T14:00:00Z"
}
```

#### Dispute Created

```json
{
  "type": "dispute_created",
  "dispute_id": "990e8400-e29b-41d4-a716-446655440004",
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T16:00:00Z"
}
```

---

## Error Responses

### Standard Error Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2024-01-15T16:00:00Z",
  "path": "/api/reports/submit",
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required or invalid |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `DUPLICATE_COMMITMENT` | 400 | Commitment already exists |
| `INVALID_SIGNATURE` | 401 | Wallet signature verification failed |
| `INSUFFICIENT_REPUTATION` | 403 | Not enough reputation to perform action |

---

## Rate Limiting

API requests are rate-limited per IP address and per authenticated user.

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705334400
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600
}
```

---

This comprehensive API documentation provides all the examples needed to integrate with the C.O.V.E.R.T platform successfully.
