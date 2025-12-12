"""
C.O.V.E.R.T - AI Analysis API Endpoints

Endpoints for AI-powered report analysis including:
- Credibility scoring
- Anomaly detection
- Automated triage
- Feature extraction
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.ai_analysis import (
    CredibilityAnalysisRequest,
    CredibilityAnalysisResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    TriageAnalysisRequest,
    TriageAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse
)
from app.services.ai import (
    credibility_scorer,
    anomaly_detector,
    report_triager,
    feature_extractor
)
from app.models.report import Report
from app.models.moderation import Moderation
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/analyze/credibility", response_model=CredibilityAnalysisResponse)
async def analyze_credibility(
    request: CredibilityAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze report credibility using ML models

    Scores credibility based on:
    - Text quality and coherence
    - Specificity of claims
    - Linguistic patterns
    - Metadata signals

    Returns credibility score (0-1), risk level, and flags
    """
    try:
        # Combine title and description
        text = f"{request.title}\n\n{request.description}"

        # Prepare metadata
        metadata = {
            'file_size': request.file_size,
            'file_type': request.file_type,
            'submission_timestamp': request.submission_timestamp,
            'anonymous': request.anonymous,
            'visibility': request.visibility,
        }

        # Run credibility analysis
        result = credibility_scorer.score_report(text, metadata)

        return CredibilityAnalysisResponse(
            credibility_score=result['credibility_score'],
            confidence=result['confidence'],
            risk_level=result['risk_level'],
            flags=result['flags'],
            reasoning=result['reasoning'],
            component_scores=result['component_scores']
        )

    except Exception as e:
        logger.error(f"Credibility analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Credibility analysis failed")


@router.post("/analyze/anomalies", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in report submission

    Checks for:
    - Duplicate/similar content
    - Temporal anomalies (submission spikes)
    - Bot/spam activity
    - Coordinated campaigns

    Returns anomaly score and detected patterns
    """
    try:
        text = f"{request.title}\n\n{request.description}"

        metadata = {
            'submission_timestamp': request.submission_timestamp,
            'file_size': request.file_size,
        }

        # Get recent reports for pattern analysis
        recent_reports = None
        if request.check_patterns:
            stmt = select(Report).order_by(desc(Report.created_at)).limit(100)
            result = await db.execute(stmt)
            recent_db_reports = result.scalars().all()

            recent_reports = [
                {
                    'id': str(r.id),
                    'text': f"{r.encrypted_title or ''} {r.encrypted_summary or ''}",
                    'submission_timestamp': r.submission_timestamp
                }
                for r in recent_db_reports
            ]

        # Run anomaly detection
        result = anomaly_detector.detect_anomalies(text, metadata, recent_reports)

        return AnomalyDetectionResponse(
            is_anomalous=result['is_anomalous'],
            anomaly_score=result['anomaly_score'],
            anomaly_types=result['anomaly_types'],
            confidence=result['confidence'],
            details=result['details']
        )

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail="Anomaly detection failed")


@router.post("/analyze/triage", response_model=TriageAnalysisResponse)
async def triage_report(
    request: TriageAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform automated triage and prioritization

    Combines credibility scoring, anomaly detection, and urgency analysis
    to determine:
    - Review priority (urgent/high/medium/low)
    - Recommended action
    - Queue position
    - Review urgency

    Returns complete triage analysis
    """
    try:
        text = f"{request.title}\n\n{request.description}"

        metadata = {
            'file_size': request.file_size,
            'file_type': request.file_type,
            'submission_timestamp': request.submission_timestamp,
            'anonymous': request.anonymous,
            'visibility': request.visibility,
        }

        # Get recent reports for pattern analysis
        recent_reports = None
        if request.include_patterns:
            stmt = select(Report).order_by(desc(Report.created_at)).limit(50)
            result = await db.execute(stmt)
            recent_db_reports = result.scalars().all()

            recent_reports = [
                {
                    'id': str(r.id),
                    'text': f"{r.encrypted_title or ''} {r.encrypted_summary or ''}",
                    'submission_timestamp': r.submission_timestamp
                }
                for r in recent_db_reports
            ]

        # Run triage analysis
        result = report_triager.triage_report(text, metadata, recent_reports)

        return TriageAnalysisResponse(
            priority=result['priority'],
            recommendation=result['recommendation'],
            queue_position=result['queue_position'],
            review_urgency=result['review_urgency'],
            automated_decision=result['automated_decision'],
            reasoning=result['reasoning'],
            ai_analysis=result['ai_analysis']
        )

    except Exception as e:
        logger.error(f"Triage analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Triage analysis failed")


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def batch_analyze_reports(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform batch analysis on multiple reports

    Useful for:
    - Re-analyzing existing reports
    - Pattern detection across multiple submissions
    - Queue optimization

    Returns analysis for all requested reports
    """
    try:
        results = []

        for report_id in request.report_ids:
            # Fetch report from database
            stmt = select(Report).where(Report.id == report_id)
            result = await db.execute(stmt)
            report = result.scalar_one_or_none()

            if not report:
                logger.warning(f"Report {report_id} not found")
                continue

            # Prepare text and metadata
            text = f"{report.encrypted_title or ''}\n\n{report.encrypted_summary or ''}"
            metadata = {
                'file_size': report.file_size,
                'file_type': report.file_type,
                'submission_timestamp': report.submission_timestamp,
                'anonymous': report.anonymous,
                'visibility': report.visibility.value if report.visibility else None,
            }

            # Run analysis based on request
            analysis = {}

            if 'credibility' in request.analysis_types:
                cred = credibility_scorer.score_report(text, metadata)
                analysis['credibility'] = cred

            if 'anomalies' in request.analysis_types:
                anom = anomaly_detector.detect_anomalies(text, metadata)
                analysis['anomalies'] = anom

            if 'triage' in request.analysis_types:
                triage = report_triager.triage_report(text, metadata)
                analysis['triage'] = triage

            results.append({
                'report_id': str(report_id),
                'analysis': analysis
            })

        return BatchAnalysisResponse(
            total_analyzed=len(results),
            results=results
        )

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Batch analysis failed")


@router.get("/stats/queue")
async def get_queue_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered queue statistics

    Returns:
    - Count by priority level
    - Average credibility scores
    - Anomaly detection stats
    - Queue health metrics
    """
    try:
        # Get pending reports
        stmt = select(Report).where(Report.status == 'pending')
        result = await db.execute(stmt)
        pending_reports = result.scalars().all()

        if not pending_reports:
            return {
                'total_pending': 0,
                'by_priority': {},
                'avg_credibility': 0.0,
                'anomaly_rate': 0.0
            }

        # Analyze all pending reports
        priority_counts = {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0, 'auto_reject': 0}
        total_credibility = 0.0
        anomaly_count = 0

        for report in pending_reports[:50]:  # Analyze first 50
            text = f"{report.encrypted_title or ''} {report.encrypted_summary or ''}"
            metadata = {
                'file_size': report.file_size,
                'submission_timestamp': report.submission_timestamp,
            }

            triage = report_triager.triage_report(text, metadata)
            priority_counts[triage['priority']] += 1

            if triage['ai_analysis'].get('credibility'):
                total_credibility += triage['ai_analysis']['credibility']['credibility_score']

            if triage['ai_analysis'].get('anomalies', {}).get('is_anomalous'):
                anomaly_count += 1

        analyzed_count = min(50, len(pending_reports))

        return {
            'total_pending': len(pending_reports),
            'analyzed_sample': analyzed_count,
            'by_priority': priority_counts,
            'avg_credibility': round(total_credibility / analyzed_count, 3) if analyzed_count > 0 else 0.0,
            'anomaly_rate': round(anomaly_count / analyzed_count, 3) if analyzed_count > 0 else 0.0,
        }

    except Exception as e:
        logger.error(f"Queue statistics failed: {e}")
        raise HTTPException(status_code=500, detail="Queue statistics failed")


@router.get("/models/status")
async def get_model_status():
    """
    Get AI model status and health

    Returns information about loaded models and their status
    """
    return {
        'credibility_scorer': {
            'status': 'active',
            'version': '1.0.0',
            'type': 'heuristic_ensemble'
        },
        'anomaly_detector': {
            'status': 'active',
            'version': '1.0.0',
            'type': 'pattern_based'
        },
        'feature_extractor': {
            'status': 'active',
            'version': '1.0.0',
            'nlp_enabled': False  # Can be upgraded to BERT
        },
        'report_triager': {
            'status': 'active',
            'version': '1.0.0',
            'type': 'rule_based_ml'
        }
    }
