from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ZKProofData(BaseModel):
    pi_a: List[str] = Field(..., description="Proof point A")
    pi_b: List[List[str]] = Field(..., description="Proof point B")
    pi_c: List[str] = Field(..., description="Proof point C")
    protocol: str = Field(..., description="Protocol name")
    curve: str = Field(..., description="Elliptic curve")


class ZKProofSubmission(BaseModel):
    proof: ZKProofData
    public_signals: List[str] = Field(..., description="Public inputs/outputs")


class ZKProofVerificationResponse(BaseModel):
    is_valid: bool
    commitment: Optional[str] = None
    nullifier_hash: Optional[str] = None
    error: Optional[str] = None


class ZKPNullifierInfo(BaseModel):
    id: int
    nullifier: str
    commitment: str
    first_used_at: datetime
    last_used_at: datetime
    usage_count: int
    daily_report_count: int
    last_daily_reset: datetime
    report_id: Optional[str] = None

    class Config:
        from_attributes = True


class ZKPRateLimitResponse(BaseModel):
    allowed: bool
    current_count: int
    limit: int
    reset_at: datetime
