"""
C.O.V.E.R.T - Report Pydantic Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ReportCreate(BaseModel):
    """Schema for creating a new report"""
    cid: str = Field(..., min_length=46, max_length=100, description="IPFS CID")
    cid_hash: str = Field(..., min_length=64, max_length=66, description="SHA256 hash of CID")
    tx_hash: str = Field(..., min_length=66, max_length=66, description="Blockchain transaction hash")
    category: str = Field(..., description="Report category")
    visibility: int = Field(..., ge=0, le=2, description="0=private, 1=moderated, 2=public")
    size_bytes: int = Field(..., gt=0, description="Size of encrypted data")

    @field_validator("cid")
    @classmethod
    def validate_cid(cls, v: str) -> str:
        if not v.startswith("bafy"):
            raise ValueError("Invalid IPFS CID format")
        return v

    @field_validator("tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: str) -> str:
        if not v.startswith("0x"):
            raise ValueError("Transaction hash must start with 0x")
        return v


class ReportCommit(BaseModel):
    """Schema for blockchain commitment update"""
    tx_hash: str = Field(..., min_length=66, max_length=66)
    block_number: Optional[int] = None


class ReportResponse(BaseModel):
    """Schema for report response"""
    id: str
    cid: str
    cid_hash: Optional[str] = None
    tx_hash: str
    category: str
    status: str
    visibility: int
    size_bytes: Optional[int] = None
    verification_score: Optional[float] = None
    risk_level: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    message: Optional[str] = None

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    """Schema for report list item"""
    id: str
    cid: str
    cid_hash: Optional[str] = None
    tx_hash: str
    category: str
    status: str
    visibility: int
    size_bytes: Optional[int] = None
    verification_score: Optional[float] = None
    risk_level: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Schema for paginated report list response"""
    items: List[ReportListItem]
    total: int
    limit: int
    offset: int


class ReportStatusUpdate(BaseModel):
    """Schema for status update"""
    status: str = Field(..., description="New status value")
    reason: Optional[str] = None
