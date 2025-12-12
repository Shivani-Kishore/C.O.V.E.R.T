"""
C.O.V.E.R.T - Credibility Scoring Service

ML-powered credibility assessment for whistleblower reports.
Uses ensemble of heuristics and ML models to score report credibility.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from app.services.ai.feature_extractor import feature_extractor

logger = logging.getLogger(__name__)


class CredibilityScorer:
    """
    Assess credibility of whistleblower reports using ML and heuristics

    Scoring considers:
    - Text quality and coherence
    - Specificity of claims (dates, names, numbers)
    - Linguistic patterns (objectivity, structure)
    - Metadata signals (file attachments, timing)
    - Historical patterns (if available)
    """

    def __init__(self):
        self.weights = self._initialize_weights()
        self.ml_model = None  # Placeholder for future ML model

    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize feature weights for credibility scoring"""
        return {
            # Positive credibility signals
            'specificity': 0.20,          # Specific details (dates, numbers, names)
            'objectivity': 0.15,          # Neutral, objective language
            'structure': 0.15,            # Well-organized, coherent
            'evidence': 0.20,             # File attachments, documentation
            'complexity': 0.10,           # Appropriate complexity (not too simple/complex)

            # Negative credibility signals
            'emotional': -0.10,           # Overly emotional language
            'vagueness': -0.15,           # Vague, non-specific claims
            'inconsistency': -0.10,       # Inconsistent information
            'spam_indicators': -0.15,     # Spam-like patterns
        }

    def score_report(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Score a report's credibility

        Args:
            text: Report content (title + description)
            metadata: Optional metadata dict

        Returns:
            Dict containing:
            - credibility_score: 0.0-1.0 (higher = more credible)
            - confidence: 0.0-1.0 (how confident in the score)
            - risk_level: 'low', 'medium', 'high', 'critical'
            - flags: List of detected issues
            - reasoning: Human-readable explanation
        """
        try:
            # Extract features
            features = feature_extractor.extract_features(text, metadata)

            # Calculate component scores
            specificity_score = self._score_specificity(features)
            objectivity_score = self._score_objectivity(features)
            structure_score = self._score_structure(features)
            evidence_score = self._score_evidence(features, metadata)
            complexity_score = self._score_complexity(features)

            # Detect negative signals
            emotional_penalty = self._detect_emotional_language(features)
            vagueness_penalty = self._detect_vagueness(features)
            spam_penalty = self._detect_spam_indicators(features, text)

            # Combine scores
            raw_score = (
                specificity_score * self.weights['specificity'] +
                objectivity_score * self.weights['objectivity'] +
                structure_score * self.weights['structure'] +
                evidence_score * self.weights['evidence'] +
                complexity_score * self.weights['complexity'] +
                emotional_penalty * abs(self.weights['emotional']) +
                vagueness_penalty * abs(self.weights['vagueness']) +
                spam_penalty * abs(self.weights['spam_indicators'])
            )

            # Normalize to 0-1 range
            credibility_score = max(0.0, min(1.0, raw_score))

            # Calculate confidence based on feature availability
            confidence = self._calculate_confidence(features, metadata)

            # Determine risk level
            risk_level = self._determine_risk_level(credibility_score, features)

            # Collect flags
            flags = self._collect_flags(
                features,
                specificity_score,
                objectivity_score,
                emotional_penalty,
                spam_penalty
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                credibility_score,
                specificity_score,
                objectivity_score,
                structure_score,
                flags
            )

            return {
                'credibility_score': round(credibility_score, 3),
                'confidence': round(confidence, 3),
                'risk_level': risk_level,
                'flags': flags,
                'reasoning': reasoning,
                'component_scores': {
                    'specificity': round(specificity_score, 3),
                    'objectivity': round(objectivity_score, 3),
                    'structure': round(structure_score, 3),
                    'evidence': round(evidence_score, 3),
                    'complexity': round(complexity_score, 3),
                }
            }

        except Exception as e:
            logger.error(f"Credibility scoring failed: {e}")
            return {
                'credibility_score': 0.5,
                'confidence': 0.1,
                'risk_level': 'medium',
                'flags': ['scoring_error'],
                'reasoning': 'Unable to assess credibility due to processing error'
            }

    def _score_specificity(self, features: Dict) -> float:
        """Score based on specific details (dates, numbers, names)"""
        score = 0.0

        # Presence of specific details
        if features.get('date_count', 0) > 0:
            score += 0.3
        if features.get('number_count', 0) > 0:
            score += 0.2
        if features.get('email_count', 0) > 0:
            score += 0.2
        if features.get('url_count', 0) > 0:
            score += 0.2

        # Multiple specific details
        if features.get('has_specific_details', 0) == 1:
            score += 0.1

        return min(1.0, score)

    def _score_objectivity(self, features: Dict) -> float:
        """Score based on objective, neutral language"""
        score = 0.5  # Neutral baseline

        # Sentiment indicators
        polarity = abs(features.get('sentiment_polarity', 0))
        if polarity < 0.2:  # Near-neutral sentiment
            score += 0.3
        elif polarity > 0.6:  # Strong sentiment
            score -= 0.2

        # Subjectivity
        subjectivity = features.get('sentiment_subjectivity', 0.5)
        if subjectivity < 0.4:  # Objective
            score += 0.2
        elif subjectivity > 0.7:  # Very subjective
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _score_structure(self, features: Dict) -> float:
        """Score based on document structure and organization"""
        score = 0.0

        # Well-structured document
        if features.get('is_structured', 0) == 1:
            score += 0.4

        # Multiple paragraphs
        paragraphs = features.get('paragraph_count', 0)
        if paragraphs >= 2:
            score += 0.2
        elif paragraphs >= 4:
            score += 0.3

        # Appropriate length (not too short, not too long)
        word_count = features.get('word_count', 0)
        if 100 <= word_count <= 2000:
            score += 0.3
        elif word_count < 50:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _score_evidence(self, features: Dict, metadata: Optional[Dict]) -> float:
        """Score based on supporting evidence (files, documentation)"""
        score = 0.0

        if not metadata:
            return score

        # File attachment
        if metadata.get('file_size', 0) > 0:
            score += 0.5

            # Bonus for documents (vs just images)
            if features.get('is_document', 0) == 1:
                score += 0.3
            elif features.get('is_video', 0) == 1:
                score += 0.2

        return min(1.0, score)

    def _score_complexity(self, features: Dict) -> float:
        """Score based on appropriate linguistic complexity"""
        score = 0.5

        # Lexical diversity
        diversity = features.get('lexical_diversity', 0.5)
        if 0.4 <= diversity <= 0.8:  # Good range
            score += 0.3
        elif diversity < 0.2:  # Too repetitive
            score -= 0.2

        # Average word length
        avg_word_len = features.get('avg_word_length', 5)
        if 4 <= avg_word_len <= 7:  # Appropriate complexity
            score += 0.2
        elif avg_word_len > 10:  # Overly complex
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _detect_emotional_language(self, features: Dict) -> float:
        """Detect overly emotional language (negative signal)"""
        penalty = 0.0

        # Excessive punctuation
        exclamations = features.get('exclamation_count', 0)
        if exclamations > 3:
            penalty -= 0.3

        # High subjectivity
        subjectivity = features.get('sentiment_subjectivity', 0.5)
        if subjectivity > 0.8:
            penalty -= 0.2

        # Extreme sentiment
        polarity = abs(features.get('sentiment_polarity', 0))
        if polarity > 0.7:
            penalty -= 0.2

        return max(-1.0, penalty)

    def _detect_vagueness(self, features: Dict) -> float:
        """Detect vague, non-specific claims (negative signal)"""
        penalty = 0.0

        # No specific details
        if features.get('has_specific_details', 0) == 0:
            penalty -= 0.3

        # Very short report
        word_count = features.get('word_count', 0)
        if word_count < 50:
            penalty -= 0.4
        elif word_count < 100:
            penalty -= 0.2

        # Low lexical diversity (repetitive)
        diversity = features.get('lexical_diversity', 0.5)
        if diversity < 0.3:
            penalty -= 0.2

        return max(-1.0, penalty)

    def _detect_spam_indicators(self, features: Dict, text: str) -> float:
        """Detect spam-like patterns (negative signal)"""
        penalty = 0.0

        # Excessive uppercase
        uppercase_ratio = features.get('uppercase_ratio', 0)
        if uppercase_ratio > 0.3:
            penalty -= 0.4

        # Excessive URLs
        url_count = features.get('url_count', 0)
        if url_count > 5:
            penalty -= 0.3

        # Repetitive phrases
        words = text.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                penalty -= 0.3

        return max(-1.0, penalty)

    def _calculate_confidence(self, features: Dict, metadata: Optional[Dict]) -> float:
        """Calculate confidence in the credibility score"""
        confidence = 0.5  # Base confidence

        # More features = higher confidence
        feature_count = len([v for v in features.values() if v != 0])
        if feature_count > 15:
            confidence += 0.2
        elif feature_count > 10:
            confidence += 0.1

        # Metadata available
        if metadata:
            confidence += 0.2

        # Sufficient text length
        word_count = features.get('word_count', 0)
        if word_count > 100:
            confidence += 0.1

        return min(1.0, confidence)

    def _determine_risk_level(self, score: float, features: Dict) -> str:
        """Determine risk level based on credibility score"""
        if score >= 0.75:
            return 'low'
        elif score >= 0.5:
            return 'medium'
        elif score >= 0.25:
            return 'high'
        else:
            return 'critical'

    def _collect_flags(
        self,
        features: Dict,
        specificity: float,
        objectivity: float,
        emotional: float,
        spam: float
    ) -> List[str]:
        """Collect warning flags for moderator review"""
        flags = []

        if specificity < 0.3:
            flags.append('low_specificity')
        if objectivity < 0.3:
            flags.append('subjective_language')
        if emotional < -0.3:
            flags.append('emotional_content')
        if spam < -0.3:
            flags.append('spam_indicators')

        if features.get('word_count', 0) < 50:
            flags.append('very_short')
        if features.get('has_specific_details', 0) == 0:
            flags.append('no_specific_details')
        if features.get('uppercase_ratio', 0) > 0.3:
            flags.append('excessive_caps')

        return flags

    def _generate_reasoning(
        self,
        score: float,
        specificity: float,
        objectivity: float,
        structure: float,
        flags: List[str]
    ) -> str:
        """Generate human-readable reasoning for the score"""
        if score >= 0.75:
            base = "Report shows strong credibility indicators"
        elif score >= 0.5:
            base = "Report shows moderate credibility"
        elif score >= 0.25:
            base = "Report shows low credibility indicators"
        else:
            base = "Report shows critical credibility concerns"

        details = []
        if specificity >= 0.6:
            details.append("contains specific details")
        if objectivity >= 0.6:
            details.append("uses objective language")
        if structure >= 0.6:
            details.append("well-structured")

        if flags:
            flag_text = ", ".join(flags[:3])  # Show top 3 flags
            details.append(f"flags: {flag_text}")

        if details:
            return f"{base}: {'; '.join(details)}"
        return base


# Global instance
credibility_scorer = CredibilityScorer()
