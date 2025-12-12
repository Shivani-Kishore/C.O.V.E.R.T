"""
Tests for AI Credibility Scoring Service
"""

import pytest
from datetime import datetime
from app.services.ai.credibility_scorer import CredibilityScorer


class TestCredibilityScorer:
    @pytest.fixture
    def scorer(self):
        return CredibilityScorer()

    @pytest.fixture
    def high_credibility_text(self):
        return """
        On January 15, 2024, I witnessed financial misconduct at Acme Corporation.
        The CFO, John Smith, approved fraudulent transactions totaling $2.5 million.

        I have documented evidence including:
        - Email correspondence from john.smith@acme.com
        - Bank transaction records showing suspicious transfers
        - Meeting minutes from the board meeting on 01/10/2024

        The transactions were routed through offshore accounts in the Cayman Islands.
        Account numbers: 123456789, 987654321.

        I can provide additional documentation if needed.
        """

    @pytest.fixture
    def low_credibility_text(self):
        return """
        BAD COMPANY!!! THEY ARE EVIL!!!

        Everything is wrong and terrible. They do bad things.
        I think maybe something happened but I'm not sure when.

        EVERYONE SHOULD KNOW ABOUT THIS!!!
        """

    @pytest.fixture
    def spam_text(self):
        return """
        BUY NOW!!! CLICK HERE!!! http://spam.com http://scam.com http://fake.com

        URGENT!!! ACT NOW!!! LIMITED TIME OFFER!!!

        Visit our website http://spam.com for more information!!!
        """

    def test_score_high_credibility_report(self, scorer, high_credibility_text):
        result = scorer.score_report(high_credibility_text)

        assert 'credibility_score' in result
        assert 'confidence' in result
        assert 'risk_level' in result
        assert 'flags' in result
        assert 'reasoning' in result

        # High credibility text should score well
        assert result['credibility_score'] >= 0.6
        assert result['confidence'] >= 0.5
        assert result['risk_level'] in ['low', 'medium']

    def test_score_low_credibility_report(self, scorer, low_credibility_text):
        result = scorer.score_report(low_credibility_text)

        # Low credibility text should score poorly
        assert result['credibility_score'] <= 0.5
        assert len(result['flags']) > 0
        assert 'emotional_content' in result['flags'] or 'subjective_language' in result['flags']

    def test_score_spam_report(self, scorer, spam_text):
        result = scorer.score_report(spam_text)

        # Spam should score very low
        assert result['credibility_score'] <= 0.4
        assert 'spam_indicators' in result['flags'] or 'excessive_caps' in result['flags']

    def test_specificity_scoring(self, scorer):
        specific_text = "On 2024-01-15, John Doe (john@example.com) transferred $100,000"
        vague_text = "Someone did something bad sometime"

        specific_features = {'date_count': 1, 'email_count': 1, 'number_count': 2, 'has_specific_details': 1}
        vague_features = {'date_count': 0, 'email_count': 0, 'number_count': 0, 'has_specific_details': 0}

        specific_score = scorer._score_specificity(specific_features)
        vague_score = scorer._score_specificity(vague_features)

        assert specific_score > vague_score
        assert specific_score >= 0.6

    def test_objectivity_scoring(self, scorer):
        objective_features = {'sentiment_polarity': 0.1, 'sentiment_subjectivity': 0.3}
        subjective_features = {'sentiment_polarity': 0.8, 'sentiment_subjectivity': 0.9}

        objective_score = scorer._score_objectivity(objective_features)
        subjective_score = scorer._score_objectivity(subjective_features)

        assert objective_score > subjective_score

    def test_structure_scoring(self, scorer):
        structured_features = {
            'is_structured': 1,
            'paragraph_count': 5,
            'word_count': 500
        }
        unstructured_features = {
            'is_structured': 0,
            'paragraph_count': 1,
            'word_count': 30
        }

        structured_score = scorer._score_structure(structured_features)
        unstructured_score = scorer._score_structure(unstructured_features)

        assert structured_score > unstructured_score

    def test_evidence_scoring(self, scorer):
        with_evidence = {'is_document': 1}
        without_evidence = {'is_document': 0}

        metadata_with = {'file_size': 5000000}
        metadata_without = {}

        with_score = scorer._score_evidence(with_evidence, metadata_with)
        without_score = scorer._score_evidence(without_evidence, metadata_without)

        assert with_score > without_score

    def test_emotional_language_detection(self, scorer):
        emotional_features = {
            'exclamation_count': 10,
            'sentiment_subjectivity': 0.9,
            'sentiment_polarity': 0.8
        }
        neutral_features = {
            'exclamation_count': 0,
            'sentiment_subjectivity': 0.3,
            'sentiment_polarity': 0.1
        }

        emotional_penalty = scorer._detect_emotional_language(emotional_features)
        neutral_penalty = scorer._detect_emotional_language(neutral_features)

        assert emotional_penalty < neutral_penalty
        assert emotional_penalty < 0

    def test_vagueness_detection(self, scorer):
        vague_features = {
            'has_specific_details': 0,
            'word_count': 30,
            'lexical_diversity': 0.2
        }
        specific_features = {
            'has_specific_details': 1,
            'word_count': 500,
            'lexical_diversity': 0.7
        }

        vague_penalty = scorer._detect_vagueness(vague_features)
        specific_penalty = scorer._detect_vagueness(specific_features)

        assert vague_penalty < specific_penalty
        assert vague_penalty < 0

    def test_spam_indicators_detection(self, scorer):
        spam_text = "BUY NOW!!! http://spam.com http://fake.com CLICK HERE!!!"
        normal_text = "This is a normal report about corporate misconduct."

        spam_features = {'uppercase_ratio': 0.5, 'url_count': 10}
        normal_features = {'uppercase_ratio': 0.1, 'url_count': 1}

        spam_penalty = scorer._detect_spam_indicators(spam_features, spam_text)
        normal_penalty = scorer._detect_spam_indicators(normal_features, normal_text)

        assert spam_penalty < normal_penalty
        assert spam_penalty < -0.3

    def test_risk_level_determination(self, scorer):
        features = {}

        assert scorer._determine_risk_level(0.8, features) == 'low'
        assert scorer._determine_risk_level(0.6, features) == 'medium'
        assert scorer._determine_risk_level(0.4, features) == 'high'
        assert scorer._determine_risk_level(0.2, features) == 'critical'

    def test_flag_collection(self, scorer):
        features = {
            'word_count': 30,
            'has_specific_details': 0,
            'uppercase_ratio': 0.4
        }

        flags = scorer._collect_flags(features, 0.2, 0.2, -0.4, -0.4)

        assert len(flags) > 0
        assert 'very_short' in flags
        assert 'no_specific_details' in flags
        assert 'excessive_caps' in flags

    def test_reasoning_generation(self, scorer):
        reasoning = scorer._generate_reasoning(0.8, 0.7, 0.7, 0.7, [])

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert 'credibility' in reasoning.lower()

    def test_confidence_calculation(self, scorer):
        rich_features = {f'feature_{i}': i for i in range(20)}
        poor_features = {'feature_1': 1}

        rich_metadata = {'file_size': 5000, 'file_type': 'pdf'}
        poor_metadata = None

        rich_confidence = scorer._calculate_confidence(rich_features, rich_metadata)
        poor_confidence = scorer._calculate_confidence(poor_features, poor_metadata)

        assert rich_confidence > poor_confidence
        assert 0 <= rich_confidence <= 1
        assert 0 <= poor_confidence <= 1

    def test_score_with_metadata(self, scorer, high_credibility_text):
        metadata = {
            'file_size': 10000000,
            'file_type': 'pdf',
            'submission_timestamp': datetime.now(),
            'anonymous': True,
            'visibility': 'moderated'
        }

        result = scorer.score_report(high_credibility_text, metadata)

        assert result['credibility_score'] > 0
        assert result['confidence'] > 0

    def test_component_scores(self, scorer, high_credibility_text):
        result = scorer.score_report(high_credibility_text)

        assert 'component_scores' in result
        components = result['component_scores']

        assert 'specificity' in components
        assert 'objectivity' in components
        assert 'structure' in components
        assert 'evidence' in components
        assert 'complexity' in components

        # All component scores should be in valid range
        for score in components.values():
            assert 0 <= score <= 1
