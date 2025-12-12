"""
C.O.V.E.R.T - AI Analysis Schemas

Pydantic models for AI analysis API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ===== Credibility Analysis =====

class CredibilityAnalysisRequest(BaseModel):
    """Request for credibility analysis"""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10, max_length=50000)
    file_size: Optional[int] = Field(None, ge=0)
    file_type: Optional[str] = None
    submission_timestamp: Optional[datetime] = None
    anonymous: bool = True
    visibility: Optional[str] = 'moderated'


class CredibilityAnalysisResponse(BaseModel):
    """Response from credibility analysis"""
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: str = Field(..., pattern='^(low|medium|high|critical)$')
    flags: List[str]
    reasoning: str
    component_scores: Dict[str, float]


# ===== Anomaly Detection =====

class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection"""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10, max_length=50000)
    submission_timestamp: Optional[datetime] = None
    file_size: Optional[int] = Field(None, ge=0)
    check_patterns: bool = True


class AnomalyDetectionResponse(BaseModel):
    """Response from anomaly detection"""
    is_anomalous: bool
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    anomaly_types: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, Any]


# ===== Triage Analysis =====

class TriageAnalysisRequest(BaseModel):
    """Request for triage analysis"""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10, max_length=50000)
    file_size: Optional[int] = Field(None, ge=0)
    file_type: Optional[str] = None
    submission_timestamp: Optional[datetime] = None
    anonymous: bool = True
    visibility: Optional[str] = 'moderated'
    include_patterns: bool = True


class TriageAnalysisResponse(BaseModel):
    """Response from triage analysis"""
    priority: str = Field(..., pattern='^(urgent|high|medium|low|auto_reject)$')
    recommendation: str
    queue_position: int = Field(..., ge=1, le=100)
    review_urgency: float = Field(..., ge=0.0, le=1.0)
    automated_decision: bool
    reasoning: str
    ai_analysis: Dict[str, Any]


# ===== Batch Analysis =====

class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    report_ids: List[str] = Field(..., min_items=1, max_items=50)
    analysis_types: List[str] = Field(
        default=['credibility', 'anomalies', 'triage'],
        description="Types of analysis to perform"
    )


class BatchAnalysisResponse(BaseModel):
    """Response from batch analysis"""
    total_analyzed: int
    results: List[Dict[str, Any]]


# ===== Feature Extraction =====

class FeatureExtractionRequest(BaseModel):
    """Request for feature extraction"""
    text: str = Field(..., min_length=1, max_length=50000)
    metadata: Optional[Dict[str, Any]] = None


class FeatureExtractionResponse(BaseModel):
    """Response from feature extraction"""
    features: Dict[str, Any]
    feature_count: int
