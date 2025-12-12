"""
C.O.V.E.R.T - Report Triage Service

Automated triage and prioritization of reports for moderator review.
Combines credibility scoring, anomaly detection, and risk assessment.
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from app.services.ai.credibility_scorer import credibility_scorer
from app.services.ai.anomaly_detector import anomaly_detector
from app.services.ai.feature_extractor import feature_extractor

logger = logging.getLogger(__name__)


class TriagePriority(str, Enum):
    """Report triage priority levels"""
    URGENT = "urgent"          # Immediate review required
    HIGH = "high"              # Priority review
    MEDIUM = "medium"          # Standard queue
    LOW = "low"                # Lower priority
    AUTO_REJECT = "auto_reject"  # Likely spam/invalid


class TriageRecommendation(str, Enum):
    """Recommended moderation actions"""
    EXPEDITED_REVIEW = "expedited_review"
    STANDARD_REVIEW = "standard_review"
    DETAILED_REVIEW = "detailed_review"
    FLAG_FOR_ADMIN = "flag_for_admin"
    REQUEST_MORE_INFO = "request_more_info"
    AUTO_REJECT_SPAM = "auto_reject_spam"


class ReportTriager:
    """
    Automated report triage and prioritization

    Triage considers:
    - Credibility score (higher = more trustworthy)
    - Risk level (from credibility assessment)
    - Anomaly detection (spam, duplicates, coordinated)
    - Content urgency (keywords, severity indicators)
    - Reporter history (if available)
    """

    def __init__(self):
        self.urgent_keywords = [
            'imminent', 'immediate', 'danger', 'threat', 'emergency',
            'life-threatening', 'ongoing', 'active', 'right now'
        ]
        self.high_severity_keywords = [
            'fraud', 'corruption', 'bribery', 'embezzlement',
            'sexual harassment', 'discrimination', 'safety violation',
            'environmental', 'public health', 'data breach'
        ]

    def triage_report(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        recent_reports: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Perform automated triage on a report

        Args:
            text: Report content (title + description)
            metadata: Report metadata
            recent_reports: Recent reports for pattern analysis

        Returns:
            Dict containing:
            - priority: TriagePriority enum
            - recommendation: TriageRecommendation enum
            - queue_position: Suggested position in queue (1-100)
            - review_urgency: 0.0-1.0 (how urgent is review)
            - automated_decision: Whether AI can make decision
            - reasoning: Human-readable explanation
            - ai_analysis: Full AI analysis results
        """
        try:
            # Run AI analysis
            credibility = credibility_scorer.score_report(text, metadata)
            anomalies = anomaly_detector.detect_anomalies(text, metadata, recent_reports)
            features = feature_extractor.extract_features(text, metadata)

            # Detect urgency
            urgency_score = self._detect_urgency(text, credibility)

            # Detect content severity
            severity_score = self._detect_severity(text, features)

            # Calculate overall priority
            priority = self._calculate_priority(
                credibility,
                anomalies,
                urgency_score,
                severity_score
            )

            # Generate recommendation
            recommendation = self._generate_recommendation(
                credibility,
                anomalies,
                priority,
                urgency_score
            )

            # Calculate queue position (1-100, lower = higher priority)
            queue_position = self._calculate_queue_position(
                priority,
                urgency_score,
                credibility['credibility_score']
            )

            # Calculate review urgency
            review_urgency = self._calculate_review_urgency(
                urgency_score,
                severity_score,
                credibility['risk_level']
            )

            # Determine if automated decision possible
            automated_decision = self._can_automate_decision(
                credibility,
                anomalies,
                priority
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                priority,
                recommendation,
                credibility,
                anomalies,
                urgency_score,
                severity_score
            )

            return {
                'priority': priority.value,
                'recommendation': recommendation.value,
                'queue_position': queue_position,
                'review_urgency': round(review_urgency, 3),
                'automated_decision': automated_decision,
                'reasoning': reasoning,
                'ai_analysis': {
                    'credibility': credibility,
                    'anomalies': anomalies,
                    'urgency_score': round(urgency_score, 3),
                    'severity_score': round(severity_score, 3),
                }
            }

        except Exception as e:
            logger.error(f"Report triage failed: {e}")
            return {
                'priority': TriagePriority.MEDIUM.value,
                'recommendation': TriageRecommendation.STANDARD_REVIEW.value,
                'queue_position': 50,
                'review_urgency': 0.5,
                'automated_decision': False,
                'reasoning': 'Triage error - defaulting to manual review',
                'ai_analysis': {'error': str(e)}
            }

    def _detect_urgency(self, text: str, credibility: Dict) -> float:
        """Detect urgency indicators in report content"""
        urgency = 0.0
        text_lower = text.lower()

        # Urgent keywords
        urgent_count = sum(1 for keyword in self.urgent_keywords if keyword in text_lower)
        if urgent_count > 0:
            urgency += min(0.5, urgent_count * 0.2)

        # High credibility + specific details = more urgent
        if credibility['credibility_score'] > 0.7:
            if credibility['component_scores'].get('specificity', 0) > 0.6:
                urgency += 0.2

        # Time-sensitive language
        time_phrases = ['today', 'tomorrow', 'this week', 'soon', 'quickly']
        if any(phrase in text_lower for phrase in time_phrases):
            urgency += 0.1

        return min(1.0, urgency)

    def _detect_severity(self, text: str, features: Dict) -> float:
        """Detect severity indicators in report content"""
        severity = 0.3  # Base severity
        text_lower = text.lower()

        # High severity keywords
        severity_count = sum(1 for keyword in self.high_severity_keywords if keyword in text_lower)
        if severity_count > 0:
            severity += min(0.4, severity_count * 0.15)

        # Evidence of harm
        harm_indicators = ['victim', 'injured', 'damaged', 'loss', 'harm', 'abuse']
        if any(indicator in text_lower for indicator in harm_indicators):
            severity += 0.2

        # Financial indicators
        money_indicators = ['million', 'billion', 'dollars', '$', 'payment', 'transaction']
        if any(indicator in text_lower for indicator in money_indicators):
            severity += 0.1

        return min(1.0, severity)

    def _calculate_priority(
        self,
        credibility: Dict,
        anomalies: Dict,
        urgency: float,
        severity: float
    ) -> TriagePriority:
        """Calculate triage priority level"""

        # Auto-reject criteria
        if anomalies['is_anomalous']:
            if 'bot_activity' in anomalies['anomaly_types']:
                return TriagePriority.AUTO_REJECT
            if anomalies['anomaly_score'] > 0.8:
                return TriagePriority.AUTO_REJECT

        if credibility['credibility_score'] < 0.2 and credibility['confidence'] > 0.7:
            if 'spam_indicators' in credibility['flags']:
                return TriagePriority.AUTO_REJECT

        # Urgent priority
        if urgency > 0.6 and credibility['credibility_score'] > 0.5:
            return TriagePriority.URGENT

        if severity > 0.7 and credibility['credibility_score'] > 0.6:
            return TriagePriority.URGENT

        # High priority
        if credibility['risk_level'] == 'low' and credibility['credibility_score'] > 0.7:
            return TriagePriority.HIGH

        if severity > 0.6 or urgency > 0.5:
            return TriagePriority.HIGH

        # Low priority
        if credibility['credibility_score'] < 0.4:
            return TriagePriority.LOW

        if anomalies['anomaly_score'] > 0.5:
            return TriagePriority.LOW

        # Default: Medium priority
        return TriagePriority.MEDIUM

    def _generate_recommendation(
        self,
        credibility: Dict,
        anomalies: Dict,
        priority: TriagePriority,
        urgency: float
    ) -> TriageRecommendation:
        """Generate moderation recommendation"""

        # Auto-reject spam
        if priority == TriagePriority.AUTO_REJECT:
            return TriageRecommendation.AUTO_REJECT_SPAM

        # Expedited review for urgent reports
        if priority == TriagePriority.URGENT:
            return TriageRecommendation.EXPEDITED_REVIEW

        # Flag for admin if anomalies detected
        if anomalies['is_anomalous'] and anomalies['anomaly_score'] > 0.6:
            if 'coordinated_campaign' in anomalies['anomaly_types']:
                return TriageRecommendation.FLAG_FOR_ADMIN

        # Detailed review for complex cases
        if priority == TriagePriority.HIGH:
            if credibility['credibility_score'] > 0.7:
                return TriageRecommendation.DETAILED_REVIEW

        # Request more info for low credibility
        if credibility['credibility_score'] < 0.4:
            if 'low_specificity' in credibility['flags']:
                return TriageRecommendation.REQUEST_MORE_INFO

        # Standard review
        return TriageRecommendation.STANDARD_REVIEW

    def _calculate_queue_position(
        self,
        priority: TriagePriority,
        urgency: float,
        credibility: float
    ) -> int:
        """Calculate suggested queue position (1-100)"""

        # Base position by priority
        base_positions = {
            TriagePriority.URGENT: 5,
            TriagePriority.HIGH: 20,
            TriagePriority.MEDIUM: 50,
            TriagePriority.LOW: 75,
            TriagePriority.AUTO_REJECT: 100,
        }

        position = base_positions[priority]

        # Adjust by urgency and credibility
        if priority != TriagePriority.AUTO_REJECT:
            urgency_adjustment = (urgency - 0.5) * 10
            credibility_adjustment = (credibility - 0.5) * 10
            position -= (urgency_adjustment + credibility_adjustment)

        return max(1, min(100, int(position)))

    def _calculate_review_urgency(
        self,
        urgency: float,
        severity: float,
        risk_level: str
    ) -> float:
        """Calculate how urgent moderator review is needed"""
        review_urgency = 0.5  # Base

        # Urgency score
        review_urgency += urgency * 0.3

        # Severity score
        review_urgency += severity * 0.2

        # Risk level
        risk_weights = {'low': 0.0, 'medium': 0.1, 'high': 0.2, 'critical': 0.3}
        review_urgency += risk_weights.get(risk_level, 0.1)

        return min(1.0, review_urgency)

    def _can_automate_decision(
        self,
        credibility: Dict,
        anomalies: Dict,
        priority: TriagePriority
    ) -> bool:
        """Determine if AI can make automated decision"""

        # Can auto-reject clear spam
        if priority == TriagePriority.AUTO_REJECT:
            if anomalies['anomaly_score'] > 0.8 and anomalies.get('confidence', 0) > 0.7:
                return True

        # Cannot automate for most cases (human review required)
        return False

    def _generate_reasoning(
        self,
        priority: TriagePriority,
        recommendation: TriageRecommendation,
        credibility: Dict,
        anomalies: Dict,
        urgency: float,
        severity: float
    ) -> str:
        """Generate human-readable reasoning for triage decision"""

        parts = []

        # Priority reasoning
        parts.append(f"Priority: {priority.value}")

        # Credibility
        cred_score = credibility['credibility_score']
        parts.append(f"Credibility: {cred_score:.2f}")

        # Key factors
        factors = []
        if urgency > 0.5:
            factors.append(f"urgent (score: {urgency:.2f})")
        if severity > 0.6:
            factors.append(f"severe (score: {severity:.2f})")
        if anomalies['is_anomalous']:
            factors.append(f"anomalies detected: {', '.join(anomalies['anomaly_types'][:2])}")
        if credibility['flags']:
            factors.append(f"flags: {', '.join(credibility['flags'][:2])}")

        if factors:
            parts.append(f"Key factors: {'; '.join(factors)}")

        # Recommendation
        parts.append(f"Recommendation: {recommendation.value}")

        return " | ".join(parts)


# Global instance
report_triager = ReportTriager()
