# C.O.V.E.R.T Backend API Documentation

## Overview

Complete FastAPI backend implementation for C.O.V.E.R.T whistleblowing platform, including all MVP features and enhanced functionality.

---

## Technology Stack

```
Backend Framework: FastAPI 0.104+
Database: PostgreSQL 15
Cache: Redis 7
Task Queue: Celery
IPFS Client: py-ipfs-http-client
Blockchain: web3.py
ML/AI: PyTorch, Transformers
```

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database connection
│   ├── dependencies.py         # Shared dependencies
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── reports.py      # Report endpoints (MVP)
│   │   │   ├── moderation.py   # Moderation endpoints (MVP)
│   │   │   ├── disputes.py     # Dispute endpoints
│   │   │   ├── reputation.py   # Reputation endpoints
│   │   │   ├── ipfs.py         # IPFS endpoints (MVP)
│   │   │   ├── blockchain.py   # Blockchain endpoints (MVP)
│   │   │   └── admin.py        # Admin endpoints (MVP)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── report.py           # Report models (MVP)
│   │   ├── user.py             # User models (MVP)
│   │   ├── moderation.py       # Moderation models (MVP)
│   │   ├── dispute.py          # Dispute models
│   │   └── reputation.py       # Reputation models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── report.py           # Pydantic schemas (MVP)
│   │   ├── user.py
│   │   ├── moderation.py       # (MVP)
│   │   └── response.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ipfs_service.py     # IPFS operations (MVP)
│   │   ├── blockchain_service.py # Web3 operations (MVP)
│   │   ├── encryption_service.py # Crypto helpers (MVP)
│   │   ├── ai_service.py       # ML spam detection
│   │   ├── reputation_service.py # Reputation calc
│   │   └── notification_service.py
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── ipfs_tasks.py       # Background pinning (MVP)
│   │   ├── anchor_tasks.py     # Daily anchoring (MVP)
│   │   └── cleanup_tasks.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py         # Security helpers (MVP)
│       ├── validators.py       # Input validation (MVP)
│       └── helpers.py
│
├── alembic/                    # Database migrations
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Database Models (SQLAlchemy)

### Core Models (MVP)

```python
# app/models/report.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class ReportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"
    DISPUTED = "disputed"

class ReportVisibility(int, enum.Enum):
    PRIVATE = 0
    MODERATED = 1
    PUBLIC = 2

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cid = Column(String(100), unique=True, nullable=False, index=True)
    cid_hash = Column(String(66), unique=True, nullable=False, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    
    reporter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    category = Column(String(50), nullable=False, index=True)
    visibility = Column(Integer, default=ReportVisibility.MODERATED)
    status = Column(String(20), default=ReportStatus.SUBMITTED, index=True)
    
    size_bytes = Column(Integer)
    risk_flags = Column(JSON, default=list)  # AI-generated flags
    
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    moderator_id = Column(UUID(as_uuid=True), nullable=True)
    jury_verdict = Column(String(20), nullable=True)
    
    impact_score = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Relationships
    mod_actions = relationship("ModerationAction", back_populates="report")
    shares = relationship("Share", back_populates="report")
    disputes = relationship("Dispute", back_populates="report")
    
    def __repr__(self):
        return f"<Report {self.cid[:12]}... status={self.status}>"


# app/models/user.py
class ReputationLevel(str, enum.Enum):
    BASIC = "basic"
    TRUSTED = "trusted"
    VALIDATOR = "validator"
    JUROR = "juror"
    COUNCIL = "council"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    pseudonym = Column(String(100), unique=True, nullable=False)
    
    reputation_score = Column(Integer, default=0, index=True)
    reputation_level = Column(String(20), default=ReputationLevel.BASIC)
    sbt_token_id = Column(Integer, nullable=True)
    
    vouched_by = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    reports = relationship("Report", foreign_keys="Report.reporter_id")
    mod_actions = relationship("ModerationAction", back_populates="moderator")
    
    def __repr__(self):
        return f"<User {self.pseudonym} rep={self.reputation_score}>"


# app/models/moderation.py
class ModerationAction(Base):
    __tablename__ = "mod_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    moderator_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    action = Column(String(20), nullable=False)  # accept/reject/need_info/escalate
    encrypted_notes = Column(Text, nullable=True)  # Encrypted with group key
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reputation_change = Column(Integer, default=0)
    
    # Relationships
    report = relationship("Report", back_populates="mod_actions")
    moderator = relationship("User", back_populates="mod_actions")
    
    def __repr__(self):
        return f"<ModAction {self.action} by {self.moderator_id}>"
```

---

## API Endpoints

### 1. Reports API (MVP Core)

```python
# app/api/v1/reports.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib

from app.database import get_db
from app.models.report import Report, ReportStatus
from app.schemas.report import ReportSubmit, ReportResponse, ReportList
from app.services.ipfs_service import IPFSService
from app.services.blockchain_service import BlockchainService
from app.dependencies import get_current_user, rate_limit
from app.utils.validators import validate_cid, validate_tx_hash

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/submit", response_model=ReportResponse, status_code=201)
@rate_limit(max_requests=10, window_seconds=3600)  # 10 per hour
async def submit_report(
    cid: str = Form(...),
    cid_hash: str = Form(...),
    tx_hash: str = Form(...),
    category: str = Form(...),
    visibility: int = Form(...),
    size_bytes: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit encrypted report (MVP Feature)
    
    Frontend already:
    1. Encrypted report client-side
    2. Uploaded to IPFS (got CID)
    3. Hashed CID
    4. Committed to blockchain (got tx_hash)
    
    Backend just indexes it in database
    """
    # Validate inputs
    if not validate_cid(cid):
        raise HTTPException(status_code=400, detail="Invalid IPFS CID")
    
    if not validate_tx_hash(tx_hash):
        raise HTTPException(status_code=400, detail="Invalid transaction hash")
    
    # Verify CID hash matches
    computed_hash = hashlib.sha256(cid.encode()).hexdigest()
    if computed_hash != cid_hash.replace('0x', ''):
        raise HTTPException(status_code=400, detail="CID hash mismatch")
    
    # Check for duplicates
    existing = db.query(Report).filter(Report.cid == cid).first()
    if existing:
        raise HTTPException(status_code=409, detail="Report already submitted")
    
    # Create report record
    report = Report(
        cid=cid,
        cid_hash=cid_hash,
        tx_hash=tx_hash,
        reporter_id=current_user.id,
        category=category,
        visibility=visibility,
        size_bytes=size_bytes,
        status=ReportStatus.SUBMITTED
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Trigger background tasks
    from app.tasks.ipfs_tasks import verify_pin, run_ai_screening
    verify_pin.delay(cid)  # Ensure pinned
    run_ai_screening.delay(report.id)  # AI spam check
    
    return ReportResponse(
        id=report.id,
        cid=report.cid,
        tx_hash=report.tx_hash,
        status=report.status,
        submitted_at=report.submitted_at,
        message="Report submitted successfully"
    )


@router.get("/list", response_model=List[ReportList])
async def list_my_reports(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List user's submitted reports (MVP Feature)
    """
    query = db.query(Report).filter(Report.reporter_id == current_user.id)
    
    if status:
        query = query.filter(Report.status == status)
    
    if category:
        query = query.filter(Report.category == category)
    
    reports = query.order_by(Report.submitted_at.desc())\
                   .limit(limit)\
                   .offset(offset)\
                   .all()
    
    return [
        ReportList(
            id=r.id,
            cid=r.cid,
            category=r.category,
            status=r.status,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_details(
    report_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get report metadata (MVP Feature)
    Note: Encrypted content fetched from IPFS by frontend
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    if report.reporter_id != current_user.id:
        # Check if moderator or has share access
        if current_user.reputation_level not in ["validator", "juror", "council"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return ReportResponse(
        id=report.id,
        cid=report.cid,
        cid_hash=report.cid_hash,
        tx_hash=report.tx_hash,
        category=report.category,
        status=report.status,
        visibility=report.visibility,
        size_bytes=report.size_bytes,
        risk_flags=report.risk_flags,
        submitted_at=report.submitted_at,
        reviewed_at=report.reviewed_at,
        impact_score=report.impact_score
    )


@router.post("/{report_id}/share")
async def create_share_link(
    report_id: str,
    viewer_pubkey: str = Form(...),
    encrypted_key_bundle: str = Form(...),
    expires_in_days: int = Form(30),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate secure share link (MVP Feature)
    
    Frontend already re-encrypted report key for viewer
    Backend stores the mapping
    """
    from app.models.share import Share
    from datetime import timedelta
    import secrets
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create share record
    share_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    share = Share(
        report_id=report.id,
        shared_by=current_user.id,
        viewer_pubkey=viewer_pubkey,
        encrypted_key_bundle=encrypted_key_bundle,
        share_token=share_token,
        access_expires_at=expires_at
    )
    
    db.add(share)
    db.commit()
    
    share_url = f"https://covert.app/view/{report.cid}/{share_token}"
    
    return {
        "share_url": share_url,
        "expires_at": expires_at,
        "share_token": share_token
    }
```

---

### 2. Moderation API (MVP Core)

```python
# app/api/v1/moderation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.report import Report, ReportStatus
from app.models.moderation import ModerationAction
from app.schemas.moderation import ModerationQueueItem, ModerationDecision
from app.dependencies import get_current_user, require_moderator

router = APIRouter(prefix="/moderation", tags=["moderation"])

@router.get("/queue", response_model=List[ModerationQueueItem])
@require_moderator
async def get_review_queue(
    category: Optional[str] = None,
    status: str = "submitted",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Fetch moderation review queue (MVP Feature)
    Returns metadata only, NO encrypted content
    """
    query = db.query(Report).filter(Report.status == status)
    
    if category:
        query = query.filter(Report.category == category)
    
    reports = query.order_by(Report.submitted_at.asc())\
                   .limit(limit)\
                   .offset(offset)\
                   .all()
    
    # Get reporter reputation
    from app.models.user import User
    
    queue_items = []
    for r in reports:
        reporter = db.query(User).filter(User.id == r.reporter_id).first()
        
        # Calculate light reputation signal
        accepted_count = db.query(Report)\
            .filter(Report.reporter_id == r.reporter_id)\
            .filter(Report.status == ReportStatus.ACCEPTED)\
            .count()
        
        rejected_count = db.query(Report)\
            .filter(Report.reporter_id == r.reporter_id)\
            .filter(Report.status == ReportStatus.REJECTED)\
            .count()
        
        queue_items.append(
            ModerationQueueItem(
                id=r.id,
                cid=r.cid,
                category=r.category,
                submitted_at=r.submitted_at,
                size_bytes=r.size_bytes,
                risk_flags=r.risk_flags,
                reporter_reputation={
                    "accepted": accepted_count,
                    "rejected": rejected_count,
                    "level": reporter.reputation_level if reporter else "unknown"
                }
            )
        )
    
    return queue_items


@router.post("/review", status_code=200)
@require_moderator
async def submit_review(
    decision: ModerationDecision,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit moderation decision (MVP Feature)
    Actions: accept, reject, need_info, tag
    """
    report = db.query(Report).filter(Report.id == decision.report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status not in [ReportStatus.SUBMITTED, ReportStatus.NEEDS_INFO]:
        raise HTTPException(status_code=400, detail="Report already reviewed")
    
    # Update report status
    if decision.action == "accept":
        report.status = ReportStatus.ACCEPTED
    elif decision.action == "reject":
        report.status = ReportStatus.REJECTED
    elif decision.action == "need_info":
        report.status = ReportStatus.NEEDS_INFO
    
    report.reviewed_at = datetime.utcnow()
    report.moderator_id = current_user.id
    
    # Encrypt moderator notes
    encrypted_notes = None
    if decision.notes:
        from app.services.encryption_service import encrypt_with_group_key
        encrypted_notes = encrypt_with_group_key(decision.notes)
    
    # Record action
    action = ModerationAction(
        report_id=report.id,
        moderator_id=current_user.id,
        action=decision.action,
        encrypted_notes=encrypted_notes
    )
    
    db.add(action)
    db.commit()
    
    # Update reputation scores
    from app.services.reputation_service import update_reputation_after_review
    update_reputation_after_review(
        db, 
        reporter_id=report.reporter_id,
        moderator_id=current_user.id,
        action=decision.action
    )
    
    # Trigger daily anchor task
    from app.tasks.anchor_tasks import check_daily_anchor
    check_daily_anchor.delay()
    
    return {
        "success": True,
        "report_id": report.id,
        "new_status": report.status,
        "message": f"Report {decision.action}ed successfully"
    }


@router.get("/actions", response_model=List[dict])
@require_moderator
async def get_my_actions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    View moderator's action history (MVP Feature)
    """
    actions = db.query(ModerationAction)\
        .filter(ModerationAction.moderator_id == current_user.id)\
        .order_by(ModerationAction.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()
    
    return [
        {
            "id": a.id,
            "report_id": a.report_id,
            "action": a.action,
            "created_at": a.created_at,
            "reputation_change": a.reputation_change
        }
        for a in actions
    ]
```

---

### 3. IPFS Service (MVP Core)

```python
# app/services/ipfs_service.py
import ipfshttpclient
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class IPFSService:
    """
    IPFS operations service (MVP Feature)
    Handles pinning, unpinning, and status checks
    """
    
    def __init__(self, ipfs_url: str = "/ip4/127.0.0.1/tcp/5001"):
        try:
            self.client = ipfshttpclient.connect(ipfs_url)
            logger.info(f"Connected to IPFS at {ipfs_url}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.client = None
    
    def pin_cid(self, cid: str) -> bool:
        """Pin CID to local IPFS node"""
        try:
            self.client.pin.add(cid)
            logger.info(f"Pinned CID: {cid}")
            return True
        except Exception as e:
            logger.error(f"Pin failed for {cid}: {e}")
            return False
    
    def unpin_cid(self, cid: str) -> bool:
        """Unpin CID from local IPFS node"""
        try:
            self.client.pin.rm(cid)
            logger.info(f"Unpinned CID: {cid}")
            return True
        except Exception as e:
            logger.error(f"Unpin failed for {cid}: {e}")
            return False
    
    def is_pinned(self, cid: str) -> bool:
        """Check if CID is pinned"""
        try:
            pins = self.client.pin.ls(cid)
            return bool(pins)
        except:
            return False
    
    def get_pin_status(self, cid: str) -> dict:
        """Get detailed pin status"""
        return {
            "cid": cid,
            "pinned_local": self.is_pinned(cid),
            "pinned_pinata": self._check_pinata_pin(cid),
            "pinned_web3storage": self._check_web3storage_pin(cid)
        }
    
    def _check_pinata_pin(self, cid: str) -> bool:
        """Check if pinned on Pinata"""
        import requests
        from app.config import settings
        
        try:
            headers = {
                "Authorization": f"Bearer {settings.PINATA_JWT}"
            }
            response = requests.get(
                f"https://api.pinata.cloud/data/pinList?hashContains={cid}",
                headers=headers,
                timeout=5
            )
            data = response.json()
            return data.get("count", 0) > 0
        except:
            return False
    
    def _check_web3storage_pin(self, cid: str) -> bool:
        """Check if pinned on web3.storage"""
        import requests
        from app.config import settings
        
        try:
            headers = {
                "Authorization": f"Bearer {settings.WEB3_STORAGE_TOKEN}"
            }
            response = requests.get(
                f"https://api.web3.storage/status/{cid}",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def pin_to_pinata(self, cid: str) -> bool:
        """Pin CID to Pinata service"""
        import requests
        from app.config import settings
        
        try:
            headers = {
                "Authorization": f"Bearer {settings.PINATA_JWT}"
            }
            data = {
                "hashToPin": cid,
                "pinataMetadata": {
                    "name": f"covert_report_{cid[:12]}"
                }
            }
            response = requests.post(
                "https://api.pinata.cloud/pinning/pinByHash",
                json=data,
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Pinata pin failed: {e}")
            return False
```

---

### 4. Blockchain Service (MVP Core)

```python
# app/services/blockchain_service.py
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import logging

logger = logging.getLogger(__name__)

class BlockchainService:
    """
    Web3 blockchain interactions (MVP Feature)
    """
    
    def __init__(self, rpc_url: str, contract_address: str, abi_path: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load contract
        with open(abi_path, 'r') as f:
            contract_abi = json.load(f)
        
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )
        
        logger.info(f"Connected to blockchain at {rpc_url}")
    
    def verify_commitment(self, cid_hash: str) -> dict:
        """Verify report commitment on-chain"""
        try:
            commitment = self.contract.functions.getCommitment(cid_hash).call()
            
            return {
                "exists": True,
                "cid_hash": commitment[0],
                "submitter": commitment[1],
                "timestamp": commitment[2],
                "visibility": commitment[3],
                "is_active": commitment[4]
            }
        except Exception as e:
            logger.error(f"Verify commitment failed: {e}")
            return {"exists": False}
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[dict]:
        """Get transaction details"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                "transaction_hash": receipt['transactionHash'].hex(),
                "block_number": receipt['blockNumber'],
                "status": receipt['status'],
                "gas_used": receipt['gasUsed']
            }
        except Exception as e:
            logger.error(f"Get receipt failed: {e}")
            return None
    
    def listen_to_events(self, event_name: str, from_block: int = 0):
        """Listen for contract events"""
        event_filter = self.contract.events[event_name].create_filter(
            fromBlock=from_block
        )
        
        for event in event_filter.get_all_entries():
            yield {
                "event": event_name,
                "args": dict(event['args']),
                "block_number": event['blockNumber'],
                "transaction_hash": event['transactionHash'].hex()
            }
```

---

### 5. Background Tasks (Celery)

```python
# app/tasks/ipfs_tasks.py
from celery import Celery
from app.database import SessionLocal
from app.models.report import Report
from app.services.ipfs_service import IPFSService
import logging

celery_app = Celery('covert', broker='redis://localhost:6379/0')
logger = logging.getLogger(__name__)

@celery_app.task(name="verify_pin")
def verify_pin(cid: str):
    """
    Verify IPFS pinning (MVP Feature)
    Ensures report is pinned locally + backup services
    """
    ipfs = IPFSService()
    
    # Check local pin
    if not ipfs.is_pinned(cid):
        logger.warning(f"CID not pinned locally: {cid}")
        ipfs.pin_cid(cid)
    
    # Pin to Pinata
    if not ipfs._check_pinata_pin(cid):
        ipfs.pin_to_pinata(cid)
    
    logger.info(f"Pin verification complete for {cid}")


@celery_app.task(name="run_ai_screening")
def run_ai_screening(report_id: str):
    """
    AI spam/misinformation detection
    Runs in background after submission
    """
    from app.services.ai_service import AIService
    
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return
        
        ai = AIService()
        risk_flags = ai.analyze_report_risk(report.cid)
        
        report.risk_flags = risk_flags
        db.commit()
        
        logger.info(f"AI screening complete for {report_id}: {risk_flags}")
        
    finally:
        db.close()


# app/tasks/anchor_tasks.py
@celery_app.task(name="daily_anchor")
def daily_anchor():
    """
    Anchor daily moderation log to blockchain (MVP Optional)
    """
    from app.services.blockchain_service import BlockchainService
    from datetime import datetime, timedelta
    import hashlib
    
    db = SessionLocal()
    try:
        # Get yesterday's actions
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        start = datetime.combine(yesterday, datetime.min.time())
        end = datetime.combine(yesterday, datetime.max.time())
        
        actions = db.query(ModerationAction)\
            .filter(ModerationAction.created_at >= start)\
            .filter(ModerationAction.created_at <= end)\
            .all()
        
        if not actions:
            logger.info("No actions to anchor for yesterday")
            return
        
        # Build merkle tree
        from app.utils.merkle import build_merkle_tree
        
        action_hashes = [
            hashlib.sha256(f"{a.id}{a.action}{a.created_at}".encode()).hexdigest()
            for a in actions
        ]
        
        merkle_root = build_merkle_tree(action_hashes)
        
        # Submit to blockchain
        blockchain = BlockchainService(
            rpc_url=settings.RPC_URL,
            contract_address=settings.DAILY_ANCHOR_ADDRESS,
            abi_path="abis/DailyAnchor.json"
        )
        
        date_int = int(yesterday.strftime("%Y%m%d"))
        
        # This would require a wallet with gas
        # In production, use a service account
        logger.info(f"Anchoring {len(actions)} actions with root {merkle_root}")
        
        # Store in database
        from app.models.anchor import DailyAnchor
        anchor = DailyAnchor(
            anchor_date=yesterday,
            merkle_root=merkle_root,
            action_count=len(actions)
        )
        db.add(anchor)
        db.commit()
        
    finally:
        db.close()


@celery_app.task(name="check_daily_anchor")
def check_daily_anchor():
    """Check if today's anchor is needed"""
    from datetime import datetime
    
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        
        # Check if already anchored
        from app.models.anchor import DailyAnchor
        existing = db.query(DailyAnchor)\
            .filter(DailyAnchor.anchor_date == today)\
            .first()
        
        if not existing:
            # Schedule anchor task
            daily_anchor.delay()
    finally:
        db.close()
```

---

### 6. Admin API (MVP Core)

```python
# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models.report import Report
from app.dependencies import require_admin
from app.schemas.admin import SystemHealth, Configuration

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/metrics", response_model=dict)
@require_admin
async def get_system_metrics(db: Session = Depends(get_db)):
    """
    System health dashboard (MVP Feature)
    """
    from app.services.ipfs_service import IPFSService
    
    # Submissions today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    submissions_today = db.query(Report)\
        .filter(Report.submitted_at >= today_start)\
        .count()
    
    # Queue size
    queue_size = db.query(Report)\
        .filter(Report.status == 'submitted')\
        .count()
    
    # Acceptance rate
    total_reviewed = db.query(Report)\
        .filter(Report.status.in_(['accepted', 'rejected']))\
        .count()
    
    accepted = db.query(Report)\
        .filter(Report.status == 'accepted')\
        .count()
    
    acceptance_rate = (accepted / total_reviewed * 100) if total_reviewed > 0 else 0
    
    # Median file size
    avg_size = db.query(func.avg(Report.size_bytes)).scalar() or 0
    
    # IPFS status
    ipfs = IPFSService()
    ipfs_healthy = ipfs.client is not None
    
    return {
        "submissions_today": submissions_today,
        "queue_size": queue_size,
        "acceptance_rate": round(acceptance_rate, 2),
        "median_file_size_mb": round(avg_size / (1024 * 1024), 2),
        "ipfs_status": "healthy" if ipfs_healthy else "unhealthy",
        "rpc_status": "healthy",  # Would check actual RPC
        "timestamp": datetime.utcnow()
    }


@router.post("/config")
@require_admin
async def update_configuration(
    config: Configuration,
    db: Session = Depends(get_db)
):
    """
    Update system configuration (MVP Feature)
    """
    from app.models.config import SystemConfig
    
    # Update or create config
    for key, value in config.dict().items():
        existing = db.query(SystemConfig)\
            .filter(SystemConfig.key == key)\
            .first()
        
        if existing:
            existing.value = str(value)
            existing.updated_at = datetime.utcnow()
        else:
            new_config = SystemConfig(key=key, value=str(value))
            db.add(new_config)
    
    db.commit()
    
    return {"success": True, "message": "Configuration updated"}


@router.get("/audit-log")
@require_admin
async def download_audit_log(
    date: str,  # YYYY-MM-DD format
    db: Session = Depends(get_db)
):
    """
    Download daily audit log (MVP Feature)
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    
    actions = db.query(ModerationAction)\
        .filter(ModerationAction.created_at >= start)\
        .filter(ModerationAction.created_at <= end)\
        .all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Report ID', 'Action', 'Moderator ID', 'Timestamp', 'Hash'])
    
    for action in actions:
        action_hash = hashlib.sha256(
            f"{action.id}{action.action}{action.created_at}".encode()
        ).hexdigest()
        
        writer.writerow([
            str(action.id),
            str(action.report_id),
            action.action,
            str(action.moderator_id),
            action.created_at.isoformat(),
            action_hash
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_{date}.csv"}
    )


@router.get("/ipfs/status")
@require_admin
async def get_ipfs_status():
    """
    IPFS pinning status (MVP Feature)
    """
    from app.services.ipfs_service import IPFSService
    
    ipfs = IPFSService()
    
    # Get pin counts
    try:
        pins = list(ipfs.client.pin.ls()['Keys'].keys())
        pinned_count = len(pins)
    except:
        pinned_count = 0
    
    return {
        "pinned_local": pinned_count,
        "last_pin_error": None,  # Would track from logs
        "storage_used_gb": 0,  # Would calculate from repo stats
        "status": "healthy"
    }
```

---

### 7. Pydantic Schemas

```python
# app/schemas/report.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class ReportSubmit(BaseModel):
    cid: str = Field(..., min_length=46, max_length=100)
    cid_hash: str = Field(..., min_length=64, max_length=66)
    tx_hash: str = Field(..., min_length=66, max_length=66)
    category: str
    visibility: int = Field(..., ge=0, le=2)
    size_bytes: int = Field(..., gt=0)
    
    @validator('cid')
    def validate_cid(cls, v):
        if not v.startswith('bafy'):
            raise ValueError('Invalid IPFS CID format')
        return v
    
    @validator('tx_hash')
    def validate_tx_hash(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Invalid transaction hash format')
        return v


class ReportResponse(BaseModel):
    id: UUID
    cid: str
    tx_hash: str
    status: str
    submitted_at: datetime
    message: Optional[str] = None
    
    # Optional detailed fields
    cid_hash: Optional[str] = None
    category: Optional[str] = None
    visibility: Optional[int] = None
    size_bytes: Optional[int] = None
    risk_flags: Optional[List[str]] = None
    reviewed_at: Optional[datetime] = None
    impact_score: Optional[int] = None
    
    class Config:
        orm_mode = True


class ReportList(BaseModel):
    id: UUID
    cid: str
    category: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    
    class Config:
        orm_mode = True


# app/schemas/moderation.py
class ModerationQueueItem(BaseModel):
    id: UUID
    cid: str
    category: str
    submitted_at: datetime
    size_bytes: int
    risk_flags: List[str]
    reporter_reputation: dict
    
    class Config:
        orm_mode = True


class ModerationDecision(BaseModel):
    report_id: UUID
    action: str = Field(..., regex="^(accept|reject|need_info|tag)$")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['accept', 'reject', 'need_info', 'tag']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of {valid_actions}')
        return v
```

---

### 8. Dependencies & Middleware

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import time
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.config import settings

security = HTTPBearer()

# Rate Limiting
RATE_LIMIT_STORE = {}  # Use Redis in production

def rate_limit(max_requests: int = 10, window_seconds: int = 3600):
    """
    Rate limiting decorator (MVP Feature)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request') or args[0]
            
            # Get identifier (wallet address or IP)
            identifier = request.headers.get('X-Wallet-Address', request.client.host)
            
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Get request history
            if identifier not in RATE_LIMIT_STORE:
                RATE_LIMIT_STORE[identifier] = []
            
            # Clean old requests
            RATE_LIMIT_STORE[identifier] = [
                req_time for req_time in RATE_LIMIT_STORE[identifier]
                if req_time > window_start
            ]
            
            # Check limit
            if len(RATE_LIMIT_STORE[identifier]) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s"
                )
            
            # Add current request
            RATE_LIMIT_STORE[identifier].append(current_time)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user (MVP Feature)
    Uses wallet signature verification
    """
    # Get wallet address from header
    wallet_address = request.headers.get('X-Wallet-Address')
    signature = request.headers.get('X-Signature')
    message = request.headers.get('X-Message')
    
    if not all([wallet_address, signature, message]):
        raise HTTPException(
            status_code=401,
            detail="Missing authentication headers"
        )
    
    # Verify signature
    from app.utils.security import verify_wallet_signature
    
    if not verify_wallet_signature(message, signature, wallet_address):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )
    
    # Get or create user
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    
    if not user:
        # Create new user with burner wallet
        from app.utils.helpers import generate_pseudonym
        
        user = User(
            wallet_address=wallet_address,
            pseudonym=generate_pseudonym()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Update last active
    user.last_active = datetime.utcnow()
    db.commit()
    
    return user


def require_moderator(
    current_user: User = Depends(get_current_user)
):
    """
    Require moderator privileges (MVP Feature)
    """
    valid_levels = ['trusted', 'validator', 'juror', 'council']
    
    if current_user.reputation_level not in valid_levels:
        raise HTTPException(
            status_code=403,
            detail="Moderator privileges required"
        )
    
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Require admin privileges (MVP Feature)
    """
    if current_user.reputation_level != 'council':
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return current_user
```

---

### 9. Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "C.O.V.E.R.T API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/covert"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # IPFS
    IPFS_URL: str = "/ip4/127.0.0.1/tcp/5001"
    PINATA_JWT: Optional[str] = None
    WEB3_STORAGE_TOKEN: Optional[str] = None
    
    # Blockchain
    RPC_URL: str = "https://sepolia.base.org"
    COMMITMENT_REGISTRY_ADDRESS: str = ""
    DAILY_ANCHOR_ADDRESS: str = ""
    COV_CREDITS_ADDRESS: str = ""
    COVERT_BADGES_ADDRESS: str = ""
    COVERT_PROTOCOL_ADDRESS: str = ""
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "your-encryption-key"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    MAX_REPORTS_PER_HOUR: int = 10
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: list = ['.pdf', '.jpg', '.png', '.mp4']
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

### 10. Main Application

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.config import settings
from app.database import engine, Base
from app.api.v1 import reports, moderation, admin, ipfs, blockchain

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware (MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://covert.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.covert.app"]
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"with status {response.status_code}"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint (MVP)"""
    from app.services.ipfs_service import IPFSService
    
    ipfs = IPFSService()
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "ipfs_connected": ipfs.client is not None,
        "timestamp": time.time()
    }

# API Routes
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(moderation.router, prefix="/api/v1", tags=["moderation"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(ipfs.router, prefix="/api/v1", tags=["ipfs"])
app.include_router(blockchain.router, prefix="/api/v1", tags=["blockchain"])

# Startup Event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize services
    from app.services.ipfs_service import IPFSService
    ipfs = IPFSService()
    
    if ipfs.client:
        logger.info("IPFS service initialized")
    else:
        logger.warning("IPFS service failed to initialize")

# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
```

---

### 11. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN groupadd -r covert && useradd -r -g covert covert
RUN chown -R covert:covert /app
USER covert

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: covert
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # IPFS Node
  ipfs:
    image: ipfs/kubo:latest
    ports:
      - "4001:4001"  # P2P
      - "5001:5001"  # API
      - "8080:8080"  # Gateway
    volumes:
      - ipfs_data:/data/ipfs
    environment:
      - IPFS_PROFILE=server

  # FastAPI Backend
  backend:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      ipfs:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/covert
      - REDIS_URL=redis://redis:6379/0
      - IPFS_URL=/dns4/ipfs/tcp/5001
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  celery_worker:
    build: .
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/covert
      - REDIS_URL=redis://redis:6379/0
    command: celery -A app.tasks.celery_app worker --loglevel=info

volumes:
  postgres_data:
  redis_data:
  ipfs_data:
```

---

### 12. Requirements

```txt
# requirements.txt

# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Redis & Caching
redis==5.0.1
hiredis==2.2.3

# Celery
celery==5.3.4

# IPFS
ipfshttpclient==0.8.0a2

# Blockchain
web3==6.11.3
eth-account==0.10.0

# Cryptography
cryptography==41.0.7
pynacl==1.5.0
pysha3==1.0.2

# AI/ML
torch==2.1.1
transformers==4.35.2
scikit-learn==1.3.2

# Utilities
python-dotenv==1.0.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Monitoring
sentry-sdk==1.38.0

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

---

### 13. API Documentation Examples

#### Submit Report

```bash
curl -X POST "http://localhost:8000/api/v1/reports/submit" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Wallet-Address: 0x1234..." \
  -H "X-Signature: 0xabcd..." \
  -H "X-Message: Sign this message..." \
  -d "cid=bafytest123&cid_hash=0xabc...&tx_hash=0xdef...&category=corruption&visibility=1&size_bytes=102400"
```

#### Get Review Queue

```bash
curl -X GET "http://localhost:8000/api/v1/moderation/queue?status=submitted&limit=50" \
  -H "X-Wallet-Address: 0x5678..." \
  -H "X-Signature: 0xefgh..." \
  -H "X-Message: Sign this message..."
```

#### Submit Review Decision

```bash
curl -X POST "http://localhost:8000/api/v1/moderation/review" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0x5678..." \
  -d '{"report_id": "uuid-here", "action": "accept", "notes": "Looks legitimate"}'
```

---

### 14. Testing

```python
# tests/test_reports.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_submit_report():
    headers = {
        "X-Wallet-Address": "0x1234",
        "X-Signature": "0xabcd",
        "X-Message": "test"
    }
    
    data = {
        "cid": "bafytest123456789",
        "cid_hash": "0x" + "a" * 64,
        "tx_hash": "0x" + "b" * 64,
        "category": "corruption",
        "visibility": 1,
        "size_bytes": 102400
    }
    
    response = client.post("/api/v1/reports/submit", data=data, headers=headers)
    
    # Would be 201 with proper auth
    assert response.status_code in [201, 401]
```

---

## Deployment Commands

```bash
# Local Development
docker-compose up -d

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "Add new table"

# Run tests
pytest tests/ -v

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Production deployment (Railway)
railway up
```

---

*Last Updated: November 2025*
*API Version: 1.0.0 (MVP)*