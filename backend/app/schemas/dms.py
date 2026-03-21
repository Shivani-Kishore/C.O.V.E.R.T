"""
C.O.V.E.R.T - Dead Man's Switch Schemas

Pydantic models for DMS API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ===== DMS Configuration =====

class DMSCreate(BaseModel):
    """Request to create a Dead Man's Switch"""
    report_id: str = Field(..., description="Report UUID")
    reporter_nullifier: str = Field(..., min_length=66, max_length=66)
    reporter_commitment: Optional[str] = Field(None, min_length=66, max_length=66)
    trigger_type: str = Field(default="time_based", pattern="^(time_based|activity_based|manual|emergency)$")
    trigger_date: datetime = Field(..., description="Trigger date/time")
    inactivity_days: Optional[int] = Field(None, ge=1, le=365)
    auto_release_public: bool = True
    auto_pin_ipfs: bool = True
    notify_contacts: bool = False
    encrypted_contacts: Optional[Dict[str, Any]] = None


class DMSUpdate(BaseModel):
    """Request to update DMS configuration"""
    trigger_date: Optional[datetime] = None
    inactivity_days: Optional[int] = Field(None, ge=1, le=365)
    auto_release_public: Optional[bool] = None
    auto_pin_ipfs: Optional[bool] = None
    notify_contacts: Optional[bool] = None
    encrypted_contacts: Optional[Dict[str, Any]] = None


class DMSResponse(BaseModel):
    """DMS configuration response"""
    id: str
    report_id: str
    trigger_type: str
    trigger_date: datetime
    status: str
    last_check_in: Optional[datetime] = None
    check_in_count: int
    auto_release_public: bool
    auto_pin_ipfs: bool
    released_at: Optional[datetime] = None
    created_at: datetime


# ===== Check-In =====

class DMSCheckInRequest(BaseModel):
    """Request to check in to DMS"""
    dms_id: str = Field(..., description="DMS UUID")
    reporter_nullifier: str = Field(..., min_length=66, max_length=66)
    zkp_proof: Optional[Dict[str, Any]] = None
    proof_of_life: Optional[str] = Field(None, max_length=200)
    extend_trigger_date: Optional[datetime] = None
    extension_reason: Optional[str] = Field(None, max_length=500)


class DMSCheckInResponse(BaseModel):
    """Check-in response"""
    success: bool
    dms_id: str
    check_in_timestamp: datetime
    next_trigger_date: datetime
    check_in_count: int
    days_until_trigger: int


# ===== Release =====

class DMSReleaseRequest(BaseModel):
    """Manual release trigger request"""
    dms_id: str = Field(..., description="DMS UUID")
    reporter_nullifier: str = Field(..., min_length=66, max_length=66)
    zkp_proof: Optional[Dict[str, Any]] = None
    release_reason: Optional[str] = Field(None, max_length=500)


class DMSReleaseResponse(BaseModel):
    """Release response"""
    success: bool
    dms_id: str
    report_id: str
    released_at: datetime
    release_transaction_hash: Optional[str] = None
    release_ipfs_cid: Optional[str] = None
    notifications_sent: int


# ===== Cancellation =====

class DMSCancelRequest(BaseModel):
    """Request to cancel DMS"""
    dms_id: str = Field(..., description="DMS UUID")
    reporter_nullifier: str = Field(..., min_length=66, max_length=66)
    zkp_proof: Optional[Dict[str, Any]] = None
    cancellation_reason: Optional[str] = Field(None, max_length=500)


class DMSCancelResponse(BaseModel):
    """Cancellation response"""
    success: bool
    dms_id: str
    cancelled_at: datetime
    message: str


# ===== Emergency Override =====

class DMSEmergencyOverrideRequest(BaseModel):
    """Admin emergency override request"""
    dms_id: str = Field(..., description="DMS UUID")
    admin_wallet: str = Field(..., min_length=42, max_length=42)
    override_action: str = Field(..., pattern="^(release|cancel|extend)$")
    override_reason: str = Field(..., min_length=10, max_length=1000)
    extend_until: Optional[datetime] = None


class DMSEmergencyOverrideResponse(BaseModel):
    """Emergency override response"""
    success: bool
    dms_id: str
    action: str
    override_at: datetime
    override_by: str


# ===== Status and Statistics =====

class DMSStatusResponse(BaseModel):
    """DMS status response"""
    id: str
    report_id: str
    status: str
    trigger_date: datetime
    days_until_trigger: int
    last_check_in: Optional[datetime] = None
    check_in_count: int
    release_attempts: int
    is_active: bool


class DMSStatistics(BaseModel):
    """DMS system statistics"""
    total_active: int
    total_triggered: int
    total_released: int
    total_cancelled: int
    pending_triggers_24h: int
    pending_triggers_7d: int
    avg_check_in_frequency_days: float
    total_check_ins_today: int
    total_releases_today: int


# ===== Watchdog Status =====

class WatchdogStatusResponse(BaseModel):
    """Watchdog service status"""
    service_name: str
    is_active: bool
    last_heartbeat: datetime
    total_checks: int
    triggers_found: int
    releases_attempted: int
    releases_succeeded: int
    releases_failed: int
    avg_check_duration_ms: int
    queue_size: int
    check_interval_seconds: int


# ===== Release Logs =====

class DMSReleaseLogResponse(BaseModel):
    """Release log entry"""
    id: int
    dms_id: str
    attempt_number: int
    attempt_timestamp: datetime
    action_type: str
    action_success: bool
    transaction_hash: Optional[str] = None
    ipfs_cid: Optional[str] = None
    error_message: Optional[str] = None


class DMSReleaseLogsResponse(BaseModel):
    """List of release logs"""
    dms_id: str
    total_logs: int
    logs: List[DMSReleaseLogResponse]
