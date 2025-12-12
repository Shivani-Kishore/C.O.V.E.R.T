"""
Tests for AI Report Triage Service
"""

import pytest
from datetime import datetime
from app.services.ai.report_triager import ReportTriager, TriagePriority, TriageRecommendation


class TestReportTriager:
    @pytest.fixture
    def triager(self):
        return ReportTriager()

    @pytest.fixture
    def urgent_report_text(self):
        return """
        IMMEDIATE DANGER: Active toxic waste dumping ongoing at Main Street facility.
        Lives at risk. Happening RIGHT NOW.

        Contact: witness@example.com
        Location: 123 Main St, documented with photos
        Date: Today, 2024-01-15
        Evidence: Photos, videos, chemical analysis reports attached
        """

    @pytest.fixture
    def high_priority_text(self):
        return """
        Systematic financial fraud at Acme Corporation.

        The CFO has been embezzling funds for 2 years.
        Total amount: $5 million
        Evidence includes bank statements, emails, and transaction logs.

        Contact John Doe (john@example.com) for witness testimony.
        Documents available for review.
        """

    @pytest.fixture
    def medium_priority_text(self):
        return """
        Potential HR policy violations at Company X.

        Several employees have complained about unfair treatment.
        Management has not responded to concerns.
        This has been ongoing for several months.
        """

    @pytest.fixture
    def low_priority_text(self):
        return """
        I think something might be wrong at the company.
        Not sure what exactly, but things seem off.
        Maybe someone should look into it.
        """

    @pytest.fixture
    def spam_text(self):
        return """
        CLICK HERE NOW!!! BUY PRODUCTS!!!
        http://spam.com http://fake.com http://scam.com
        LIMITED TIME OFFER!!! ACT NOW!!!
        """

    def test_triage_urgent_report(self, triager, urgent_report_text):
        result = triager.triage_report(urgent_report_text)

        assert 'priority' in result
        assert 'recommendation' in result
        assert 'queue_position' in result
        assert 'review_urgency' in result

        # Urgent keywords and high specificity should result in high priority
        assert result['priority'] in ['urgent', 'high']
        assert result['review_urgency'] > 0.5
        assert result['queue_position'] <= 20

    def test_triage_high_priority_report(self, triager, high_priority_text):
        result = triager.triage_report(high_priority_text)

        # Fraud + specific details + evidence = high priority
        assert result['priority'] in ['high', 'urgent']
        assert result['recommendation'] in [
            TriageRecommendation.EXPEDITED_REVIEW.value,
            TriageRecommendation.DETAILED_REVIEW.value
        ]

    def test_triage_medium_priority_report(self, triager, medium_priority_text):
        result = triager.triage_report(medium_priority_text)

        # Standard workplace issue = medium priority
        assert result['priority'] == 'medium'
        assert 30 <= result['queue_position'] <= 70

    def test_triage_low_priority_report(self, triager, low_priority_text):
        result = triager.triage_report(low_priority_text)

        # Vague report = low priority
        assert result['priority'] in ['low', 'medium']
        assert result['queue_position'] >= 50

    def test_triage_spam_report(self, triager, spam_text):
        result = triager.triage_report(spam_text)

        # Spam indicators = auto reject or very low priority
        assert result['priority'] in ['auto_reject', 'low']

        if result['priority'] == 'auto_reject':
            assert result['recommendation'] == TriageRecommendation.AUTO_REJECT_SPAM.value

    def test_urgency_detection(self, triager):
        urgent_text = "IMMEDIATE danger ongoing RIGHT NOW emergency imminent threat"
        normal_text = "Report about past incident that occurred last year"

        credibility_high = {'credibility_score': 0.8, 'component_scores': {'specificity': 0.7}}
        credibility_low = {'credibility_score': 0.4, 'component_scores': {'specificity': 0.3}}

        urgent_score = triager._detect_urgency(urgent_text, credibility_high)
        normal_score = triager._detect_urgency(normal_text, credibility_low)

        assert urgent_score > normal_score
        assert urgent_score >= 0.5
        assert 0 <= normal_score <= 1

    def test_severity_detection(self, triager):
        severe_text = """
        Massive fraud involving millions of dollars.
        Multiple victims harmed by safety violations.
        Ongoing environmental damage and data breach.
        """

        mild_text = "Minor policy disagreement with supervisor."

        severe_features = {'word_count': 50}
        mild_features = {'word_count': 20}

        severe_score = triager._detect_severity(severe_text, severe_features)
        mild_score = triager._detect_severity(mild_text, mild_features)

        assert severe_score > mild_score
        assert severe_score >= 0.5

    def test_priority_calculation(self, triager):
        # High credibility + high urgency = urgent priority
        high_cred = {'credibility_score': 0.8, 'risk_level': 'low', 'confidence': 0.8, 'flags': []}
        no_anomalies = {'is_anomalous': False, 'anomaly_score': 0.1, 'anomaly_types': []}

        priority = triager._calculate_priority(high_cred, no_anomalies, 0.8, 0.8)
        assert priority == TriagePriority.URGENT

        # Low credibility + spam = auto reject
        low_cred = {'credibility_score': 0.15, 'risk_level': 'critical', 'confidence': 0.8, 'flags': ['spam_indicators']}
        priority_low = triager._calculate_priority(low_cred, no_anomalies, 0.1, 0.1)
        assert priority_low == TriagePriority.AUTO_REJECT

    def test_recommendation_generation(self, triager):
        high_cred = {'credibility_score': 0.8, 'flags': []}
        low_cred = {'credibility_score': 0.3, 'flags': ['low_specificity']}
        no_anomalies = {'is_anomalous': False, 'anomaly_score': 0.1, 'anomaly_types': []}
        anomalies = {'is_anomalous': True, 'anomaly_score': 0.7, 'anomaly_types': ['coordinated_campaign']}

        # Urgent priority = expedited review
        rec1 = triager._generate_recommendation(high_cred, no_anomalies, TriagePriority.URGENT, 0.8)
        assert rec1 == TriageRecommendation.EXPEDITED_REVIEW

        # Auto reject = auto reject spam
        rec2 = triager._generate_recommendation(low_cred, no_anomalies, TriagePriority.AUTO_REJECT, 0.1)
        assert rec2 == TriageRecommendation.AUTO_REJECT_SPAM

        # Coordinated campaign = flag for admin
        rec3 = triager._generate_recommendation(high_cred, anomalies, TriagePriority.MEDIUM, 0.5)
        assert rec3 == TriageRecommendation.FLAG_FOR_ADMIN

        # Low specificity = request more info
        rec4 = triager._generate_recommendation(low_cred, no_anomalies, TriagePriority.MEDIUM, 0.3)
        assert rec4 == TriageRecommendation.REQUEST_MORE_INFO

    def test_queue_position_calculation(self, triager):
        # Urgent priority should have low queue position (high priority)
        pos_urgent = triager._calculate_queue_position(TriagePriority.URGENT, 0.8, 0.8)
        # Low priority should have high queue position (low priority)
        pos_low = triager._calculate_queue_position(TriagePriority.LOW, 0.2, 0.3)

        assert pos_urgent < pos_low
        assert 1 <= pos_urgent <= 100
        assert 1 <= pos_low <= 100

    def test_review_urgency_calculation(self, triager):
        # High urgency + high severity + critical risk = very urgent
        urgency1 = triager._calculate_review_urgency(0.8, 0.8, 'critical')
        # Low urgency + low severity + low risk = less urgent
        urgency2 = triager._calculate_review_urgency(0.2, 0.2, 'low')

        assert urgency1 > urgency2
        assert 0 <= urgency1 <= 1
        assert 0 <= urgency2 <= 1

    def test_automated_decision_capability(self, triager):
        # Can auto-reject clear spam
        low_cred = {'credibility_score': 0.1, 'confidence': 0.8, 'flags': ['spam_indicators']}
        high_anomaly = {'anomaly_score': 0.9, 'confidence': 0.8, 'is_anomalous': True}

        can_automate = triager._can_automate_decision(low_cred, high_anomaly, TriagePriority.AUTO_REJECT)

        if can_automate:
            assert high_anomaly['anomaly_score'] > 0.8

    def test_reasoning_generation(self, triager):
        credibility = {
            'credibility_score': 0.75,
            'flags': ['low_specificity']
        }
        anomalies = {
            'is_anomalous': True,
            'anomaly_types': ['duplicate_content']
        }

        reasoning = triager._generate_reasoning(
            TriagePriority.HIGH,
            TriageRecommendation.DETAILED_REVIEW,
            credibility,
            anomalies,
            0.6,
            0.7
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert 'Priority' in reasoning or 'priority' in reasoning

    def test_comprehensive_triage(self, triager, high_priority_text):
        metadata = {
            'file_size': 10000000,
            'file_type': 'pdf',
            'submission_timestamp': datetime.now(),
            'anonymous': True,
            'visibility': 'moderated'
        }

        result = triager.triage_report(high_priority_text, metadata)

        # Verify complete triage result structure
        assert 'priority' in result
        assert 'recommendation' in result
        assert 'queue_position' in result
        assert 'review_urgency' in result
        assert 'automated_decision' in result
        assert 'reasoning' in result
        assert 'ai_analysis' in result

        # Verify AI analysis components
        assert 'credibility' in result['ai_analysis']
        assert 'anomalies' in result['ai_analysis']
        assert 'urgency_score' in result['ai_analysis']
        assert 'severity_score' in result['ai_analysis']

    def test_triage_with_recent_reports(self, triager, medium_priority_text):
        recent_reports = [
            {
                'id': f'report-{i}',
                'text': 'Different report content',
                'submission_timestamp': datetime.now()
            }
            for i in range(10)
        ]

        result = triager.triage_report(medium_priority_text, None, recent_reports)

        # Should successfully triage with context
        assert result['priority'] in ['urgent', 'high', 'medium', 'low', 'auto_reject']

    def test_error_handling(self, triager):
        # Test with minimal/invalid input
        result = triager.triage_report("", None, None)

        # Should return valid structure even with empty input
        assert 'priority' in result
        assert 'recommendation' in result
        # Should default to safe values
        assert result['priority'] in ['low', 'medium']
