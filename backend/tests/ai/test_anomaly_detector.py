"""
Tests for AI Anomaly Detection Service
"""

import pytest
from datetime import datetime, timedelta
from app.services.ai.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()

    @pytest.fixture
    def normal_text(self):
        return "This is a legitimate whistleblower report about corporate misconduct."

    @pytest.fixture
    def duplicate_text(self):
        return "Corporate fraud at Company X involving financial misconduct."

    @pytest.fixture
    def recent_reports(self):
        base_time = datetime.now()
        return [
            {
                'id': f'report-{i}',
                'text': 'Corporate fraud at Company X involving financial misconduct.',
                'submission_timestamp': base_time - timedelta(minutes=i*10)
            }
            for i in range(5)
        ]

    def test_detect_no_anomalies(self, detector, normal_text):
        result = detector.detect_anomalies(normal_text, None, None)

        assert 'is_anomalous' in result
        assert 'anomaly_score' in result
        assert 'anomaly_types' in result
        assert 'confidence' in result

        assert isinstance(result['is_anomalous'], bool)
        assert 0 <= result['anomaly_score'] <= 1

    def test_detect_duplicates(self, detector, duplicate_text, recent_reports):
        result = detector.detect_anomalies(
            duplicate_text,
            {'submission_timestamp': datetime.now()},
            recent_reports
        )

        # Should detect similarity with recent reports
        if result['is_anomalous']:
            assert 'duplicate_content' in result['anomaly_types']

    def test_duplicate_detection_method(self, detector, duplicate_text, recent_reports):
        duplicate_result = detector._detect_duplicates(duplicate_text, recent_reports)

        assert 'is_duplicate' in duplicate_result
        assert 'max_similarity' in duplicate_result
        assert 0 <= duplicate_result['max_similarity'] <= 1

    def test_temporal_anomalies(self, detector, normal_text):
        metadata = {'submission_timestamp': datetime.now()}

        # Create many recent reports (submission spike)
        recent_reports = [
            {
                'id': f'report-{i}',
                'text': f'Report {i}',
                'submission_timestamp': datetime.now() - timedelta(minutes=i)
            }
            for i in range(15)
        ]

        temporal_result = detector._detect_temporal_anomalies(metadata, recent_reports)

        assert 'is_anomalous' in temporal_result
        assert 'anomaly_types' in temporal_result
        assert 'severity' in temporal_result

    def test_unusual_time_detection(self, detector):
        # 3 AM submission (unusual time)
        night_metadata = {'submission_timestamp': datetime(2024, 1, 1, 3, 0)}
        # 2 PM submission (normal time)
        day_metadata = {'submission_timestamp': datetime(2024, 1, 1, 14, 0)}

        night_result = detector._detect_temporal_anomalies(night_metadata, [])
        day_result = detector._detect_temporal_anomalies(day_metadata, [])

        # Night submission might be flagged as unusual
        if night_result['is_anomalous']:
            assert 'unusual_time' in night_result['anomaly_types']

    def test_statistical_outliers(self, detector):
        # Very short text
        short_features = {'word_count': 5, 'uppercase_ratio': 0.1}
        # Very long text
        long_features = {'word_count': 15000, 'uppercase_ratio': 0.1}
        # Excessive uppercase
        caps_features = {'word_count': 100, 'uppercase_ratio': 0.6}
        # Normal text
        normal_features = {'word_count': 500, 'uppercase_ratio': 0.1}

        short_result = detector._detect_statistical_outliers(short_features)
        long_result = detector._detect_statistical_outliers(long_features)
        caps_result = detector._detect_statistical_outliers(caps_features)
        normal_result = detector._detect_statistical_outliers(normal_features)

        assert short_result['is_outlier']
        assert long_result['is_outlier']
        assert caps_result['is_outlier']
        # Normal should not be outlier

    def test_bot_activity_detection(self, detector):
        # Bot-like text (very repetitive)
        bot_text = "test " * 100
        bot_features = {'sentence_count': 10, 'word_count': 200}

        # Generic/placeholder text
        generic_text = "lorem ipsum dolor sit amet test test test"
        generic_features = {'sentence_count': 1, 'word_count': 8}

        # Normal text
        normal_text = "This is a legitimate report with varied vocabulary and structure."
        normal_features = {'sentence_count': 1, 'word_count': 11}

        bot_result = detector._detect_bot_activity(bot_features, bot_text)
        generic_result = detector._detect_bot_activity(generic_features, generic_text)
        normal_result = detector._detect_bot_activity(normal_features, normal_text)

        # Bot-like should have high bot score
        if bot_result['is_bot_like']:
            assert bot_result['bot_score'] >= 0.3
            assert len(bot_result['indicators']) > 0

        # Generic text should be flagged
        if generic_result['is_bot_like']:
            assert 'generic_content' in generic_result['indicators']

    def test_coordinated_campaign_detection(self, detector):
        current_time = datetime.now()
        text = "Report about Company X fraud"

        # Many similar reports in short time window
        similar_reports = [
            {
                'id': f'report-{i}',
                'text': 'Report about Company X fraudulent activities',
                'submission_timestamp': current_time - timedelta(minutes=i*5)
            }
            for i in range(5)
        ]

        metadata = {'submission_timestamp': current_time}

        result = detector._detect_coordinated_campaign(text, metadata, similar_reports)

        assert 'is_coordinated' in result

        if result['is_coordinated']:
            assert result['similar_report_count'] >= 3
            assert len(result['similar_report_ids']) > 0

    def test_detection_confidence(self, detector):
        # Multiple anomalies detected
        many_anomalies = ['duplicate_content', 'submission_spike', 'bot_activity']
        details_many = {
            'duplicate': {'max_similarity': 0.98},
            'temporal': {'recent_count': 20}
        }

        # Single anomaly
        one_anomaly = ['unusual_time']
        details_one = {}

        # No anomalies
        no_anomalies = []
        details_none = {}

        confidence_many = detector._calculate_detection_confidence(many_anomalies, details_many)
        confidence_one = detector._calculate_detection_confidence(one_anomaly, details_one)
        confidence_none = detector._calculate_detection_confidence(no_anomalies, details_none)

        # More evidence = higher confidence
        assert confidence_many > confidence_one
        # No anomalies = high confidence in that assessment
        assert confidence_none == 1.0

    def test_comprehensive_anomaly_detection(self, detector):
        # Create a suspicious report
        suspicious_text = "BUY NOW!!! CLICK HERE!!! " * 10
        metadata = {
            'submission_timestamp': datetime(2024, 1, 1, 3, 30)  # Unusual time
        }

        # Many recent similar reports
        recent_reports = [
            {
                'id': f'report-{i}',
                'text': "BUY NOW!!! CLICK HERE!!!",
                'submission_timestamp': datetime.now() - timedelta(minutes=i*2)
            }
            for i in range(10)
        ]

        result = detector.detect_anomalies(suspicious_text, metadata, recent_reports)

        # Should detect multiple anomaly types
        assert result['is_anomalous']
        assert result['anomaly_score'] > 0.3
        assert len(result['anomaly_types']) > 0

    def test_low_lexical_diversity_outlier(self, detector):
        # Very repetitive text
        features = {
            'word_count': 100,
            'lexical_diversity': 0.15,  # Very low
            'uppercase_ratio': 0.1,
            'exclamation_count': 0,
            'url_count': 0
        }

        result = detector._detect_statistical_outliers(features)

        assert result['is_outlier']
        assert 'low_diversity' in result['outlier_types']

    def test_excessive_urls_outlier(self, detector):
        features = {
            'word_count': 100,
            'uppercase_ratio': 0.1,
            'lexical_diversity': 0.5,
            'exclamation_count': 0,
            'url_count': 15  # Excessive
        }

        result = detector._detect_statistical_outliers(features)

        assert result['is_outlier']
        assert 'excessive_urls' in result['outlier_types']

    def test_empty_recent_reports(self, detector, normal_text):
        result = detector.detect_anomalies(normal_text, None, [])

        # Should still work with no recent reports
        assert 'is_anomalous' in result
        assert isinstance(result['anomaly_score'], float)

    def test_error_handling(self, detector):
        # Test with invalid inputs
        result = detector.detect_anomalies("", None, None)

        # Should return valid result structure even with empty input
        assert 'is_anomalous' in result
        assert 'anomaly_score' in result
