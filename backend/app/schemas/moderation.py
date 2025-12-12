"""
C.O.V.E.R.T - Moderation Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ModerationQueueItem(BaseModel):
    """Schema for moderation queue item"""
    id: str
    cid: str
    cid_hash: str
    category: str
    status: str
    visibility: int
    size_bytes: int
    verification_score: Optional[float] = None
    risk_level: Optional[str] = None
    submitted_at: datetime
    # NO encrypted content - moderators only see metadata

    model_config = {"from_attributes": True}


class ModerationDecisionCreate(BaseModel):
    """Schema for creating moderation decision"""
    report_id: str = Field(..., description="Report ID")
    decision: str = Field(..., description="accept, reject, need_info, escalate")
    encrypted_notes: Optional[str] = Field(None, description="Encrypted moderator notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    time_spent_seconds: Optional[int] = Field(None, description="Time spent reviewing")


class ModerationResponse(BaseModel):
    """Schema for moderation response"""
    id: str
    report_id: str
    moderator_id: Optional[str]
    action: str
    decision: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    time_spent_seconds: Optional[int]

    model_config = {"from_attributes": True}


class ModerationHistoryItem(BaseModel):
    """Schema for moderation history item"""
    id: str
    report_id: str
    action: str
    decision: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    time_spent_seconds: Optional[int]

    model_config = {"from_attributes": True}


class ModeratorStats(BaseModel):
    """Schema for moderator statistics"""
    moderator_id: str
    wallet_address: str
    reputation_score: int
    tier: str
    total_reviews: int
    accurate_reviews: int
    disputed_reviews: int
    accuracy_rate: float
    period_days: int
    reviews_in_period: int
    decisions: Dict[str, int]
    average_review_time_seconds: int
    is_active: bool
    is_suspended: bool


class ModeratorCreate(BaseModel):
    """Schema for creating moderator"""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    public_key: Optional[str] = None


class ModeratorResponse(BaseModel):
    """Schema for moderator response"""
    id: str
    wallet_address: str
    reputation_score: int
    tier: str
    total_reviews: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class QueueSummary(BaseModel):
    """Schema for queue summary"""
    total_pending: int
    by_risk_level: Dict[str, int]
    by_category: Dict[str, int]
    average_wait_time_hours: float
    oldest_report_age_hours: float
