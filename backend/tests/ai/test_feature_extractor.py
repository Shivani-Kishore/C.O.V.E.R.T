"""
Tests for AI Feature Extraction Service
"""

import pytest
from datetime import datetime
from app.services.ai.feature_extractor import FeatureExtractor


class TestFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()

    @pytest.fixture
    def sample_text(self):
        return """
        Company X engaged in fraudulent activities on January 15, 2024.
        Evidence includes emails and financial documents showing illegal transactions.
        Contact me at whistleblower@example.com for more details.
        See documentation at https://evidence.example.com/docs
        """

    def test_extract_text_features(self, extractor, sample_text):
        features = extractor._extract_text_features(sample_text)

        assert 'text_length' in features
        assert 'word_count' in features
        assert 'sentence_count' in features
        assert 'avg_word_length' in features
        assert 'avg_sentence_length' in features
        assert 'unique_word_ratio' in features

        assert features['word_count'] > 0
        assert features['avg_word_length'] > 0

    def test_extract_linguistic_features(self, extractor, sample_text):
        features = extractor._extract_linguistic_features(sample_text)

        assert 'question_count' in features
        assert 'exclamation_count' in features
        assert 'uppercase_ratio' in features
        assert 'lexical_diversity' in features
        assert 'number_count' in features
        assert 'date_count' in features
        assert 'url_count' in features
        assert 'email_count' in features

        # Should detect email
        assert features['email_count'] >= 1
        # Should detect URL
        assert features['url_count'] >= 1
        # Should detect date
        assert features['date_count'] >= 1

    def test_extract_sentiment_features(self, extractor):
        positive_text = "This is wonderful and amazing!"
        negative_text = "This is terrible and horrible!"
        neutral_text = "The meeting is scheduled for Tuesday."

        pos_features = extractor._extract_sentiment_features(positive_text)
        neg_features = extractor._extract_sentiment_features(negative_text)
        neu_features = extractor._extract_sentiment_features(neutral_text)

        assert pos_features['sentiment_polarity'] > 0
        assert neg_features['sentiment_polarity'] < 0
        assert abs(neu_features['sentiment_polarity']) < 0.3

    def test_extract_structural_features(self, extractor):
        structured_text = """
        INTRODUCTION

        This is the first paragraph with important information.

        This is the second paragraph with more details.

        KEY POINTS:
        - Point one
        - Point two
        - Point three

        NUMBERED LIST:
        1. First item
        2. Second item
        """

        features = extractor._extract_structural_features(structured_text)

        assert 'paragraph_count' in features
        assert 'bullet_point_count' in features
        assert 'numbered_list_count' in features
        assert 'header_count' in features
        assert 'is_structured' in features

        assert features['paragraph_count'] >= 2
        assert features['bullet_point_count'] >= 3
        assert features['numbered_list_count'] >= 2
        assert features['is_structured'] == 1

    def test_extract_metadata_features(self, extractor):
        metadata = {
            'file_size': 15000000,  # 15MB
            'file_type': 'pdf',
            'submission_timestamp': datetime(2024, 1, 15, 14, 30),
            'anonymous': True,
            'visibility': 'moderated'
        }

        features = extractor._extract_metadata_features(metadata)

        assert 'file_size' in features
        assert 'file_size_log' in features
        assert 'has_large_file' in features
        assert 'hour_of_day' in features
        assert 'day_of_week' in features
        assert 'is_weekend' in features
        assert 'is_business_hours' in features
        assert 'is_document' in features

        assert features['file_size'] == 15000000
        assert features['has_large_file'] == 1
        assert features['is_document'] == 1
        assert features['is_business_hours'] == 1

    def test_extract_features_comprehensive(self, extractor, sample_text):
        metadata = {
            'file_size': 5000,
            'file_type': 'pdf',
            'submission_timestamp': datetime.now(),
        }

        features = extractor.extract_features(sample_text, metadata)

        # Should contain all feature categories
        assert 'text_length' in features
        assert 'sentiment_polarity' in features
        assert 'email_count' in features
        assert 'file_size' in features
        assert isinstance(features, dict)
        assert len(features) > 20  # Should have many features

    def test_compute_similarity(self, extractor):
        text1 = "Company engaged in fraud"
        text2 = "Company engaged in fraudulent activities"
        text3 = "The weather is nice today"

        # Similar texts
        similarity_12 = extractor.compute_similarity(text1, text2)
        # Different texts
        similarity_13 = extractor.compute_similarity(text1, text3)

        assert 0 <= similarity_12 <= 1
        assert 0 <= similarity_13 <= 1
        assert similarity_12 > similarity_13

    def test_empty_text_handling(self, extractor):
        features = extractor.extract_features("", None)

        assert features['text_length'] == 0
        assert features['word_count'] == 0

    def test_special_characters_handling(self, extractor):
        special_text = "Test !@#$%^&*() test 123"
        features = extractor.extract_features(special_text, None)

        assert features['word_count'] > 0
        assert features['number_count'] >= 1
