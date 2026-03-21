# C.O.V.E.R.T Database Schema

## Overview

This document defines the complete PostgreSQL database schema for the C.O.V.E.R.T platform. The schema is designed with privacy, security, and scalability in mind.

## Database Configuration

```sql
-- Database: covert_platform
-- Encoding: UTF8
-- Locale: en_US.UTF-8
-- Timezone: UTC
```

## Schema Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   reports   │────▶│  moderations │────▶│ moderators  │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────┐     ┌──────────────┐
│ report_logs │     │   disputes   │
└─────────────┘     └──────────────┘
       │                    │
       │                    ▼
       │            ┌──────────────┐
       │            │  jury_votes  │
       │            └──────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  anchors    │     │ zkp_nullifiers│
└─────────────┘     └──────────────┘
```

## Table Definitions

### 1. reports

Primary table for storing encrypted whistleblower reports.

```sql
CREATE TABLE reports (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Blockchain Integration
    commitment_hash VARCHAR(66) NOT NULL UNIQUE,  -- Keccak256 hash on blockchain
    transaction_hash VARCHAR(66),                 -- Ethereum transaction hash
    block_number BIGINT,                          -- Block where commitment was made
    chain_id INTEGER NOT NULL,                    -- 137 (Polygon), 42161 (Arbitrum), etc.
    
    -- IPFS Storage
    ipfs_cid VARCHAR(100) NOT NULL UNIQUE,        -- Content Identifier for encrypted blob
    ipfs_gateway_url TEXT,                        -- Full IPFS gateway URL
    
    -- Encrypted Metadata (stored on-chain/IPFS)
    encrypted_category VARCHAR(500),              -- Encrypted category
    encrypted_title VARCHAR(1000),                -- Encrypted title
    encrypted_summary TEXT,                       -- Encrypted summary
    encrypted_file_hash VARCHAR(100),             -- Hash of encrypted file
    
    -- Report Metadata
    file_size BIGINT NOT NULL,                    -- Size of encrypted blob in bytes
    file_type VARCHAR(50),                        -- MIME type (encrypted)
    submission_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Privacy Settings
    visibility VARCHAR(20) NOT NULL DEFAULT 'moderated',  -- 'private', 'moderated', 'public'
    anonymous BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'under_review', 'verified', 'rejected', 'disputed'
    verification_score DECIMAL(3,2),                -- AI credibility score (0.00-1.00)
    risk_level VARCHAR(20),                         -- 'low', 'medium', 'high', 'critical'
    
    -- Reporter Identity (Anonymous)
    reporter_nullifier VARCHAR(66) UNIQUE,          -- ZKP nullifier (prevents double reporting)
    reporter_commitment VARCHAR(66),                -- ZKP commitment (proves humanity)
    burner_address VARCHAR(42),                     -- Temporary Ethereum address (optional)
    
    -- Temporal Protection
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMP,
    
    -- Dead Man's Switch
    dms_enabled BOOLEAN DEFAULT FALSE,
    dms_trigger_date TIMESTAMP,
    dms_released BOOLEAN DEFAULT FALSE,
    
    -- Soft Delete
    deleted_at TIMESTAMP,
    deletion_reason TEXT,
    
    -- Constraints
    CONSTRAINT valid_visibility CHECK (visibility IN ('private', 'moderated', 'public')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'under_review', 'verified', 'rejected', 'disputed', 'archived')),
    CONSTRAINT valid_risk CHECK (risk_level IN ('low', 'medium', 'high', 'critical') OR risk_level IS NULL),
    CONSTRAINT valid_score CHECK (verification_score >= 0.00 AND verification_score <= 1.00),
    CONSTRAINT commitment_format CHECK (commitment_hash ~ '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT valid_chain CHECK (chain_id IN (137, 42161, 80001, 421613))  -- Polygon, Arbitrum, testnets
);

-- Indexes
CREATE INDEX idx_reports_status ON reports(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_reports_visibility ON reports(visibility) WHERE deleted_at IS NULL;
CREATE INDEX idx_reports_timestamp ON reports(submission_timestamp DESC);
CREATE INDEX idx_reports_chain ON reports(chain_id, block_number);
CREATE INDEX idx_reports_nullifier ON reports(reporter_nullifier) WHERE reporter_nullifier IS NOT NULL;
CREATE INDEX idx_reports_dms ON reports(dms_trigger_date) WHERE dms_enabled = TRUE AND dms_released = FALSE;
CREATE INDEX idx_reports_commitment ON reports(commitment_hash);
CREATE INDEX idx_reports_ipfs ON reports(ipfs_cid);

-- Triggers
CREATE TRIGGER update_reports_timestamp
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

### 2. moderations

Tracks moderation actions and decisions.

```sql
CREATE TABLE moderations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    moderator_id UUID REFERENCES moderators(id) ON DELETE SET NULL,
    
    -- Moderation Action
    action VARCHAR(50) NOT NULL,  -- 'review_started', 'request_info', 'verified', 'rejected', 'escalated'
    decision VARCHAR(20),          -- 'accept', 'reject', 'need_info', 'escalate'
    
    -- Encrypted Notes (only moderator can decrypt)
    encrypted_notes TEXT,
    notes_encryption_key_hash VARCHAR(66),  -- Hash of key used (for key rotation)
    
    -- AI-Assisted Fields
    ai_recommendation VARCHAR(20),          -- AI suggested action
    ai_confidence DECIMAL(3,2),             -- AI confidence score
    ai_flags JSONB,                         -- Array of AI-detected issues
    
    -- Decision Reasoning
    rejection_reason TEXT,
    verification_evidence TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Moderation Metrics
    time_spent_seconds INTEGER,            -- Time moderator spent reviewing
    
    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('review_started', 'request_info', 'verified', 'rejected', 'escalated')),
    CONSTRAINT valid_decision CHECK (decision IN ('accept', 'reject', 'need_info', 'escalate') OR decision IS NULL),
    CONSTRAINT valid_ai_confidence CHECK (ai_confidence >= 0.00 AND ai_confidence <= 1.00)
);

-- Indexes
CREATE INDEX idx_moderations_report ON moderations(report_id);
CREATE INDEX idx_moderations_moderator ON moderations(moderator_id);
CREATE INDEX idx_moderations_action ON moderations(action);
CREATE INDEX idx_moderations_created ON moderations(created_at DESC);
CREATE INDEX idx_moderations_pending ON moderations(completed_at) WHERE completed_at IS NULL;
```

### 3. moderators

Moderator accounts and reputation tracking.

```sql
CREATE TABLE moderators (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Blockchain Identity
    wallet_address VARCHAR(42) NOT NULL UNIQUE,
    
    -- Reputation Metrics
    reputation_score INTEGER NOT NULL DEFAULT 0,
    tier VARCHAR(20) NOT NULL DEFAULT 'bronze',    -- 'bronze', 'silver', 'gold', 'platinum'
    total_reviews INTEGER NOT NULL DEFAULT 0,
    accurate_reviews INTEGER NOT NULL DEFAULT 0,
    disputed_reviews INTEGER NOT NULL DEFAULT 0,
    
    -- Activity Tracking
    last_active_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    suspension_until TIMESTAMP,
    suspension_reason TEXT,
    
    -- Specialization
    expertise_areas JSONB,                         -- Array of category specializations
    preferred_categories TEXT[],
    
    -- Performance Metrics
    average_review_time_seconds INTEGER,
    consistency_score DECIMAL(3,2),
    
    -- Privacy
    public_key TEXT,                               -- For encrypted communications
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_tier CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum')),
    CONSTRAINT valid_address CHECK (wallet_address ~ '^0x[a-fA-F0-9]{40}$'),
    CONSTRAINT valid_consistency CHECK (consistency_score >= 0.00 AND consistency_score <= 1.00)
);

-- Indexes
CREATE INDEX idx_moderators_wallet ON moderators(wallet_address);
CREATE INDEX idx_moderators_reputation ON moderators(reputation_score DESC);
CREATE INDEX idx_moderators_tier ON moderators(tier);
CREATE INDEX idx_moderators_active ON moderators(is_active, last_active_at);
```

### 4. report_logs

Audit trail for all report-related events.

```sql
CREATE TABLE report_logs (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    actor_id UUID,                                 -- Could be moderator_id or null for system
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL,               -- 'created', 'status_changed', 'accessed', 'modified', 'deleted'
    event_data JSONB,                              -- Additional event context
    
    -- Change Tracking
    old_value TEXT,
    new_value TEXT,
    field_changed VARCHAR(100),
    
    -- Context
    ip_address_hash VARCHAR(64),                   -- Hashed IP for privacy
    user_agent_hash VARCHAR(64),                   -- Hashed user agent
    
    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'created', 'status_changed', 'accessed', 'modified', 
        'deleted', 'moderation_started', 'moderation_completed',
        'disputed', 'released', 'dms_triggered'
    ))
);

-- Indexes
CREATE INDEX idx_report_logs_report ON report_logs(report_id, created_at DESC);
CREATE INDEX idx_report_logs_event ON report_logs(event_type);
CREATE INDEX idx_report_logs_timestamp ON report_logs(created_at DESC);

-- Partitioning by month (for scalability)
-- CREATE TABLE report_logs_y2024m01 PARTITION OF report_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 5. anchors

Daily Merkle root anchors for tamper-proof timestamping.

```sql
CREATE TABLE anchors (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Blockchain Data
    merkle_root VARCHAR(66) NOT NULL UNIQUE,       -- Root hash anchored on-chain
    transaction_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    chain_id INTEGER NOT NULL,
    
    -- Anchor Metadata
    anchor_date DATE NOT NULL UNIQUE,              -- One anchor per day
    report_count INTEGER NOT NULL DEFAULT 0,       -- Number of reports in this anchor
    
    -- Merkle Tree Data
    merkle_tree JSONB,                             -- Full tree structure (optional)
    leaf_hashes TEXT[],                            -- Array of commitment hashes
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    anchored_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_merkle_root CHECK (merkle_root ~ '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT valid_chain_anchor CHECK (chain_id IN (137, 42161, 80001, 421613))
);

-- Indexes
CREATE INDEX idx_anchors_date ON anchors(anchor_date DESC);
CREATE INDEX idx_anchors_block ON anchors(chain_id, block_number);
CREATE INDEX idx_anchors_root ON anchors(merkle_root);
```

### 6. zkp_nullifiers

Prevents double-reporting while maintaining anonymity.

```sql
CREATE TABLE zkp_nullifiers (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- ZKP Data
    nullifier VARCHAR(66) NOT NULL UNIQUE,         -- Unique nullifier from ZK proof
    commitment VARCHAR(66) NOT NULL,               -- Original commitment
    
    -- Usage Tracking
    first_used_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP NOT NULL DEFAULT NOW(),
    usage_count INTEGER NOT NULL DEFAULT 1,
    
    -- Rate Limiting
    daily_report_count INTEGER NOT NULL DEFAULT 1,
    last_daily_reset DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Associated Report
    report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT valid_nullifier CHECK (nullifier ~ '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT valid_commitment CHECK (commitment ~ '^0x[a-fA-F0-9]{64}$')
);

-- Indexes
CREATE INDEX idx_zkp_nullifiers_nullifier ON zkp_nullifiers(nullifier);
CREATE INDEX idx_zkp_nullifiers_commitment ON zkp_nullifiers(commitment);
CREATE INDEX idx_zkp_nullifiers_daily ON zkp_nullifiers(last_daily_reset, daily_report_count);
```

### 7. disputes

Dispute resolution system for challenged moderations.

```sql
CREATE TABLE disputes (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    moderation_id UUID NOT NULL REFERENCES moderations(id) ON DELETE CASCADE,
    disputer_id UUID REFERENCES moderators(id) ON DELETE SET NULL,
    
    -- Blockchain Integration
    dispute_contract_id BIGINT,                    -- ID in DisputeManager contract
    transaction_hash VARCHAR(66),
    
    -- Dispute Details
    reason TEXT NOT NULL,
    evidence_ipfs_cid VARCHAR(100),                -- Additional evidence on IPFS
    
    -- Jury Selection
    jury_size INTEGER NOT NULL DEFAULT 5,
    selected_jurors UUID[],                        -- Array of moderator IDs
    
    -- Voting
    votes_for INTEGER NOT NULL DEFAULT 0,
    votes_against INTEGER NOT NULL DEFAULT 0,
    votes_abstain INTEGER NOT NULL DEFAULT 0,
    
    -- Stakes
    disputer_stake DECIMAL(18, 6),                 -- ETH/MATIC staked
    total_stake DECIMAL(18, 6),
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending', -- 'pending', 'jury_selected', 'voting', 'resolved', 'slashed'
    resolution VARCHAR(20),                        -- 'upheld', 'overturned', 'inconclusive'
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    voting_deadline TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_dispute_status CHECK (status IN ('pending', 'jury_selected', 'voting', 'resolved', 'slashed')),
    CONSTRAINT valid_resolution CHECK (resolution IN ('upheld', 'overturned', 'inconclusive') OR resolution IS NULL)
);

-- Indexes
CREATE INDEX idx_disputes_report ON disputes(report_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_deadline ON disputes(voting_deadline) WHERE status = 'voting';
```

### 8. jury_votes

Individual jury votes in dispute resolution.

```sql
CREATE TABLE jury_votes (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    juror_id UUID NOT NULL REFERENCES moderators(id) ON DELETE CASCADE,
    
    -- Vote Data
    vote VARCHAR(10) NOT NULL,                     -- 'for', 'against', 'abstain'
    encrypted_rationale TEXT,                      -- Encrypted explanation
    
    -- Blockchain Proof
    vote_commitment VARCHAR(66),                   -- Commitment before reveal
    vote_signature VARCHAR(132),                   -- Signed vote
    
    -- Timestamps
    committed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revealed_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_vote CHECK (vote IN ('for', 'against', 'abstain')),
    CONSTRAINT unique_juror_per_dispute UNIQUE (dispute_id, juror_id)
);

-- Indexes
CREATE INDEX idx_jury_votes_dispute ON jury_votes(dispute_id);
CREATE INDEX idx_jury_votes_juror ON jury_votes(juror_id);
```

### 9. sessions

User session management for authenticated access.

```sql
CREATE TABLE sessions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Session Data
    session_token VARCHAR(128) NOT NULL UNIQUE,
    wallet_address VARCHAR(42),
    moderator_id UUID REFERENCES moderators(id) ON DELETE CASCADE,
    
    -- ZKP Authentication
    zkp_proof JSONB,                               -- Zero-knowledge proof data
    nullifier_used VARCHAR(66),
    
    -- Session Metadata
    ip_address_hash VARCHAR(64),
    user_agent_hash VARCHAR(64),
    
    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Security
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_expiration CHECK (expires_at > created_at)
);

-- Indexes
CREATE INDEX idx_sessions_token ON sessions(session_token) WHERE revoked = FALSE;
CREATE INDEX idx_sessions_wallet ON sessions(wallet_address) WHERE revoked = FALSE;
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE revoked = FALSE;
CREATE INDEX idx_sessions_cleanup ON sessions(expires_at) WHERE revoked = FALSE OR expires_at < NOW();
```

### 10. notifications

Event notifications for users and moderators.

```sql
CREATE TABLE notifications (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Recipient
    recipient_id UUID,                             -- Could be moderator_id
    recipient_address VARCHAR(42),                 -- Or wallet address
    
    -- Notification Content
    type VARCHAR(50) NOT NULL,                     -- 'report_status', 'moderation_assigned', 'dispute_created', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Related Entities
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    moderation_id UUID REFERENCES moderations(id) ON DELETE CASCADE,
    dispute_id UUID REFERENCES disputes(id) ON DELETE CASCADE,
    
    -- Status
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    -- Delivery
    delivery_method VARCHAR(20) DEFAULT 'in_app',  -- 'in_app', 'email', 'webhook'
    delivered BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_notification_type CHECK (type IN (
        'report_status', 'moderation_assigned', 'moderation_completed',
        'dispute_created', 'dispute_resolved', 'reputation_changed',
        'dms_triggered', 'system_alert'
    ))
);

-- Indexes
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, read, created_at DESC);
CREATE INDEX idx_notifications_address ON notifications(recipient_address, read, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(created_at DESC) WHERE read = FALSE;
CREATE INDEX idx_notifications_expires ON notifications(expires_at) WHERE expires_at IS NOT NULL;
```

## Helper Functions

### Timestamp Update Trigger

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Reputation Score Calculation

```sql
CREATE OR REPLACE FUNCTION calculate_reputation_score(moderator_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total INTEGER;
    accurate INTEGER;
    disputed INTEGER;
    score INTEGER;
BEGIN
    SELECT total_reviews, accurate_reviews, disputed_reviews
    INTO total, accurate, disputed
    FROM moderators
    WHERE id = moderator_id;
    
    IF total = 0 THEN
        RETURN 0;
    END IF;
    
    -- Score formula: (accurate * 10) - (disputed * 20)
    score := (accurate * 10) - (disputed * 20);
    
    RETURN GREATEST(0, score);
END;
$$ LANGUAGE plpgsql;
```

### Daily Nullifier Reset

```sql
CREATE OR REPLACE FUNCTION reset_daily_nullifiers()
RETURNS void AS $$
BEGIN
    UPDATE zkp_nullifiers
    SET daily_report_count = 0,
        last_daily_reset = CURRENT_DATE
    WHERE last_daily_reset < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;
```

## Views

### Active Reports View

```sql
CREATE VIEW active_reports AS
SELECT 
    r.id,
    r.commitment_hash,
    r.ipfs_cid,
    r.status,
    r.visibility,
    r.verification_score,
    r.submission_timestamp,
    COUNT(m.id) as moderation_count,
    MAX(m.created_at) as last_moderation
FROM reports r
LEFT JOIN moderations m ON r.id = m.report_id
WHERE r.deleted_at IS NULL
GROUP BY r.id;
```

### Moderator Performance View

```sql
CREATE VIEW moderator_performance AS
SELECT 
    m.id,
    m.wallet_address,
    m.reputation_score,
    m.tier,
    m.total_reviews,
    CASE 
        WHEN m.total_reviews > 0 
        THEN ROUND((m.accurate_reviews::DECIMAL / m.total_reviews) * 100, 2)
        ELSE 0
    END as accuracy_percentage,
    m.average_review_time_seconds,
    m.last_active_at
FROM moderators m
WHERE m.is_active = TRUE;
```

### Pending Moderations View

```sql
CREATE VIEW pending_moderations AS
SELECT 
    r.id as report_id,
    r.commitment_hash,
    r.status,
    r.verification_score,
    r.risk_level,
    r.submission_timestamp,
    m.id as moderation_id,
    m.ai_recommendation,
    m.ai_confidence,
    mod.wallet_address as moderator_address
FROM reports r
LEFT JOIN moderations m ON r.id = m.report_id AND m.completed_at IS NULL
LEFT JOIN moderators mod ON m.moderator_id = mod.id
WHERE r.status IN ('pending', 'under_review')
AND r.deleted_at IS NULL
ORDER BY r.submission_timestamp ASC;
```

## Initial Data Seeds

### Default Moderator Tiers Configuration

```sql
-- Insert default tier thresholds (stored in a config table if needed)
-- Bronze: 0-99 points
-- Silver: 100-499 points
-- Gold: 500-999 points
-- Platinum: 1000+ points
```

## Migrations

### Migration 001: Initial Schema

```sql
-- This file contains all CREATE TABLE statements above
```

### Migration 002: Add Indexes

```sql
-- This file contains all CREATE INDEX statements above
```

### Migration 003: Add Views

```sql
-- This file contains all CREATE VIEW statements above
```

## Backup Strategy

### Daily Backups

```bash
# Full database backup
pg_dump -U postgres covert_platform > backup_$(date +%Y%m%d).sql

# Encrypted backup
pg_dump -U postgres covert_platform | gpg -e -r admin@covert.io > backup_$(date +%Y%m%d).sql.gpg
```

### Retention Policy

- Daily backups: Keep for 7 days
- Weekly backups: Keep for 1 month
- Monthly backups: Keep for 1 year

## Performance Considerations

### Connection Pooling

```python
# Example with SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/covert_platform",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### Query Optimization

- Use prepared statements
- Implement proper indexing
- Avoid SELECT *
- Use EXPLAIN ANALYZE for slow queries
- Implement query result caching (Redis)

## Security Measures

1. **Encryption at Rest**: Enable PostgreSQL transparent data encryption
2. **SSL Connections**: Require SSL for all database connections
3. **Role-Based Access**: Separate read/write roles
4. **Audit Logging**: Enable pgAudit extension
5. **Regular Updates**: Keep PostgreSQL version current

## Monitoring Queries

### Active Connections

```sql
SELECT count(*) FROM pg_stat_activity;
```

### Slow Queries

```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Database Size

```sql
SELECT pg_size_pretty(pg_database_size('covert_platform'));
```

### Table Sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Cleanup Jobs

### Delete Expired Sessions

```sql
DELETE FROM sessions
WHERE expires_at < NOW()
OR (revoked = TRUE AND revoked_at < NOW() - INTERVAL '30 days');
```

### Archive Old Reports

```sql
-- Move reports older than 2 years to archive table
INSERT INTO reports_archive
SELECT * FROM reports
WHERE submission_timestamp < NOW() - INTERVAL '2 years'
AND deleted_at IS NOT NULL;

DELETE FROM reports
WHERE submission_timestamp < NOW() - INTERVAL '2 years'
AND deleted_at IS NOT NULL;
```

---

**Note**: This schema is designed for PostgreSQL 14+. Adjust syntax for other versions or databases as needed.
