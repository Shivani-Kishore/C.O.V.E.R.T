"""
C.O.V.E.R.T - Anomaly Detection Service

Detects unusual patterns in reports that may indicate:
- Coordinated campaigns (similar reports submitted together)
- Spam/bot activity
- Duplicate submissions
- Suspicious behavioral patterns
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from app.services.ai.feature_extractor import feature_extractor

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detect anomalous patterns in whistleblower reports

    Detection strategies:
    - Text similarity (duplicate/near-duplicate detection)
    - Temporal patterns (submission spikes, coordinated timing)
    - Behavioral patterns (same source, bot-like activity)
    - Statistical outliers (unusual feature values)
    """

    def __init__(self):
        self.similarity_threshold = 0.85  # Text similarity for duplicates
        self.spike_threshold = 3.0  # Standard deviations for spike detection
        self.coordination_window = timedelta(hours=1)  # Time window for coordination
        self.history_cache = defaultdict(list)  # Cache recent submissions

    def detect_anomalies(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        recent_reports: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Detect anomalies in a report

        Args:
            text: Report content
            metadata: Report metadata
            recent_reports: List of recent reports for pattern analysis

        Returns:
            Dict containing:
            - is_anomalous: Boolean
            - anomaly_score: 0.0-1.0 (higher = more anomalous)
            - anomaly_types: List of detected anomaly types
            - details: Additional information about anomalies
        """
        anomalies = []
        details = {}
        anomaly_score = 0.0

        try:
            # Extract features for analysis
            features = feature_extractor.extract_features(text, metadata)

            # 1. Duplicate detection
            if recent_reports:
                duplicate_result = self._detect_duplicates(text, recent_reports)
                if duplicate_result['is_duplicate']:
                    anomalies.append('duplicate_content')
                    anomaly_score += 0.4
                    details['duplicate'] = duplicate_result

            # 2. Temporal anomalies
            if recent_reports and metadata:
                temporal_result = self._detect_temporal_anomalies(metadata, recent_reports)
                if temporal_result['is_anomalous']:
                    anomalies.extend(temporal_result['anomaly_types'])
                    anomaly_score += temporal_result['severity']
                    details['temporal'] = temporal_result

            # 3. Statistical outliers
            outlier_result = self._detect_statistical_outliers(features)
            if outlier_result['is_outlier']:
                anomalies.append('statistical_outlier')
                anomaly_score += 0.2
                details['outlier'] = outlier_result

            # 4. Bot/spam indicators
            bot_result = self._detect_bot_activity(features, text)
            if bot_result['is_bot_like']:
                anomalies.append('bot_activity')
                anomaly_score += 0.3
                details['bot'] = bot_result

            # 5. Coordinated campaign detection
            if recent_reports:
                campaign_result = self._detect_coordinated_campaign(text, metadata, recent_reports)
                if campaign_result['is_coordinated']:
                    anomalies.append('coordinated_campaign')
                    anomaly_score += 0.5
                    details['campaign'] = campaign_result

            # Normalize score
            anomaly_score = min(1.0, anomaly_score)

            return {
                'is_anomalous': len(anomalies) > 0,
                'anomaly_score': round(anomaly_score, 3),
                'anomaly_types': anomalies,
                'details': details,
                'confidence': self._calculate_detection_confidence(anomalies, details)
            }

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                'is_anomalous': False,
                'anomaly_score': 0.0,
                'anomaly_types': ['detection_error'],
                'details': {'error': str(e)},
                'confidence': 0.1
            }

    def _detect_duplicates(self, text: str, recent_reports: List[Dict]) -> Dict:
        """Detect duplicate or near-duplicate reports"""
        max_similarity = 0.0
        most_similar_id = None

        for report in recent_reports:
            if 'text' not in report:
                continue

            similarity = feature_extractor.compute_similarity(text, report['text'])

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_id = report.get('id')

        is_duplicate = max_similarity >= self.similarity_threshold

        return {
            'is_duplicate': is_duplicate,
            'max_similarity': round(max_similarity, 3),
            'similar_report_id': most_similar_id if is_duplicate else None,
            'threshold': self.similarity_threshold
        }

    def _detect_temporal_anomalies(
        self,
        metadata: Dict,
        recent_reports: List[Dict]
    ) -> Dict:
        """Detect unusual temporal patterns"""
        anomalies = []
        severity = 0.0

        if 'submission_timestamp' not in metadata:
            return {'is_anomalous': False, 'anomaly_types': [], 'severity': 0.0}

        current_time = metadata['submission_timestamp']
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))

        # Count recent submissions in time window
        recent_count = 0
        for report in recent_reports:
            if 'submission_timestamp' not in report:
                continue

            report_time = report['submission_timestamp']
            if isinstance(report_time, str):
                report_time = datetime.fromisoformat(report_time.replace('Z', '+00:00'))

            time_diff = abs((current_time - report_time).total_seconds())
            if time_diff <= self.coordination_window.total_seconds():
                recent_count += 1

        # Submission spike detection
        if recent_count > 10:  # More than 10 submissions in 1 hour
            anomalies.append('submission_spike')
            severity += 0.3

        # Unusual time detection (3 AM - 5 AM)
        if 3 <= current_time.hour <= 5:
            anomalies.append('unusual_time')
            severity += 0.1

        # Rapid submission detection (same source)
        # This would require nullifier checking in production
        # For now, just flag high volume
        if recent_count > 20:
            anomalies.append('high_volume')
            severity += 0.2

        return {
            'is_anomalous': len(anomalies) > 0,
            'anomaly_types': anomalies,
            'severity': severity,
            'recent_count': recent_count,
            'time_window_hours': self.coordination_window.total_seconds() / 3600
        }

    def _detect_statistical_outliers(self, features: Dict) -> Dict:
        """Detect statistical outliers in feature values"""
        outliers = []

        # Very long or very short text
        word_count = features.get('word_count', 0)
        if word_count < 10:
            outliers.append('extremely_short')
        elif word_count > 10000:
            outliers.append('extremely_long')

        # Unusual uppercase ratio
        uppercase_ratio = features.get('uppercase_ratio', 0)
        if uppercase_ratio > 0.5:
            outliers.append('excessive_uppercase')

        # Unusual punctuation
        exclamations = features.get('exclamation_count', 0)
        if exclamations > 10:
            outliers.append('excessive_punctuation')

        # Very low lexical diversity (copy-paste spam)
        diversity = features.get('lexical_diversity', 0.5)
        if diversity < 0.2 and word_count > 50:
            outliers.append('low_diversity')

        # Unusual URL count
        urls = features.get('url_count', 0)
        if urls > 10:
            outliers.append('excessive_urls')

        return {
            'is_outlier': len(outliers) > 0,
            'outlier_types': outliers,
            'feature_stats': {
                'word_count': word_count,
                'uppercase_ratio': uppercase_ratio,
                'lexical_diversity': diversity,
            }
        }

    def _detect_bot_activity(self, features: Dict, text: str) -> Dict:
        """Detect bot-like submission patterns"""
        bot_score = 0.0
        indicators = []

        # Perfect patterns (too regular)
        sentence_count = features.get('sentence_count', 0)
        word_count = features.get('word_count', 0)

        if sentence_count > 0:
            words_per_sentence = word_count / sentence_count
            # Suspiciously consistent sentence length
            if 19.5 <= words_per_sentence <= 20.5:
                bot_score += 0.2
                indicators.append('uniform_sentence_length')

        # Template-like structure
        if text.count('\n') > word_count / 20:  # Many line breaks
            bot_score += 0.1
            indicators.append('template_structure')

        # Excessive repetition
        words = text.split()
        if len(words) > 20:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.2:  # Single word > 20% of content
                bot_score += 0.3
                indicators.append('excessive_repetition')

        # Generic/placeholder text
        generic_phrases = ['lorem ipsum', 'test test', 'example text', 'placeholder']
        text_lower = text.lower()
        for phrase in generic_phrases:
            if phrase in text_lower:
                bot_score += 0.4
                indicators.append('generic_content')
                break

        is_bot_like = bot_score >= 0.3

        return {
            'is_bot_like': is_bot_like,
            'bot_score': round(bot_score, 3),
            'indicators': indicators
        }

    def _detect_coordinated_campaign(
        self,
        text: str,
        metadata: Optional[Dict],
        recent_reports: List[Dict]
    ) -> Dict:
        """Detect coordinated submission campaigns"""
        if not recent_reports or not metadata:
            return {'is_coordinated': False}

        current_time = metadata.get('submission_timestamp')
        if not current_time:
            return {'is_coordinated': False}

        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))

        # Find similar reports in time window
        similar_count = 0
        similar_ids = []

        for report in recent_reports:
            if 'text' not in report or 'submission_timestamp' not in report:
                continue

            report_time = report['submission_timestamp']
            if isinstance(report_time, str):
                report_time = datetime.fromisoformat(report_time.replace('Z', '+00:00'))

            time_diff = abs((current_time - report_time).total_seconds())

            # Within coordination window
            if time_diff <= self.coordination_window.total_seconds():
                similarity = feature_extractor.compute_similarity(text, report['text'])

                # Similar content (not exact duplicates, but related)
                if 0.4 <= similarity < 0.8:
                    similar_count += 1
                    similar_ids.append(report.get('id'))

        # Coordinated if 3+ similar reports in window
        is_coordinated = similar_count >= 3

        return {
            'is_coordinated': is_coordinated,
            'similar_report_count': similar_count,
            'similar_report_ids': similar_ids[:5],  # First 5
            'time_window_hours': self.coordination_window.total_seconds() / 3600
        }

    def _calculate_detection_confidence(
        self,
        anomalies: List[str],
        details: Dict
    ) -> float:
        """Calculate confidence in anomaly detection"""
        if not anomalies:
            return 1.0  # High confidence in no anomalies

        confidence = 0.5  # Base confidence

        # Multiple detection methods agree
        if len(anomalies) >= 2:
            confidence += 0.2

        # Strong signals in details
        if 'duplicate' in details:
            if details['duplicate'].get('max_similarity', 0) > 0.95:
                confidence += 0.2

        if 'temporal' in details:
            if details['temporal'].get('recent_count', 0) > 15:
                confidence += 0.1

        return min(1.0, confidence)


# Global instance
anomaly_detector = AnomalyDetector()
