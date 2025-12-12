"""
C.O.V.E.R.T - Feature Extraction Service

Extracts features from reports for ML analysis including:
- Text embeddings (BERT/DistilBERT)
- Linguistic features (readability, sentiment, complexity)
- Structural features (length, format, metadata)
- Temporal features (submission patterns)
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
from textblob import TextBlob

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract ML features from whistleblower reports"""

    def __init__(self):
        self.sentiment_analyzer = None
        self._initialize_nlp()

    def _initialize_nlp(self):
        """Initialize NLP models (lazy loading for performance)"""
        try:
            import transformers
            self.bert_tokenizer = None
            self.bert_model = None
            logger.info("NLP models will be loaded on first use")
        except ImportError:
            logger.warning("transformers not available, using basic features only")

    def extract_features(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive features from report text

        Args:
            text: Report content (title + description)
            metadata: Optional metadata (file_size, submission_time, etc.)

        Returns:
            Dictionary of extracted features
        """
        features = {}

        # Text-based features
        features.update(self._extract_text_features(text))

        # Linguistic features
        features.update(self._extract_linguistic_features(text))

        # Sentiment features
        features.update(self._extract_sentiment_features(text))

        # Structural features
        features.update(self._extract_structural_features(text))

        # Metadata features
        if metadata:
            features.update(self._extract_metadata_features(metadata))

        return features

    def _extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract basic text statistics"""
        words = text.split()
        sentences = text.split('.')

        return {
            'text_length': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_word_ratio': len(set(words)) / len(words) if words else 0,
        }

    def _extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic complexity features"""

        # Count specific linguistic patterns
        question_marks = text.count('?')
        exclamation_marks = text.count('!')
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0

        # Lexical diversity (type-token ratio)
        words = text.lower().split()
        lexical_diversity = len(set(words)) / len(words) if words else 0

        # Count numbers and dates
        numbers = len(re.findall(r'\d+', text))
        dates = len(re.findall(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', text))

        # Count URLs and emails
        urls = len(re.findall(r'https?://\S+', text))
        emails = len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))

        return {
            'question_count': question_marks,
            'exclamation_count': exclamation_marks,
            'uppercase_ratio': uppercase_ratio,
            'lexical_diversity': lexical_diversity,
            'number_count': numbers,
            'date_count': dates,
            'url_count': urls,
            'email_count': emails,
            'has_specific_details': 1 if (numbers > 0 or dates > 0 or emails > 0) else 0,
        }

    def _extract_sentiment_features(self, text: str) -> Dict[str, Any]:
        """Extract sentiment and emotional features"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            return {
                'sentiment_polarity': polarity,  # -1 (negative) to 1 (positive)
                'sentiment_subjectivity': subjectivity,  # 0 (objective) to 1 (subjective)
                'is_neutral': 1 if abs(polarity) < 0.1 else 0,
                'is_objective': 1 if subjectivity < 0.3 else 0,
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment_polarity': 0.0,
                'sentiment_subjectivity': 0.5,
                'is_neutral': 1,
                'is_objective': 0,
            }

    def _extract_structural_features(self, text: str) -> Dict[str, Any]:
        """Extract document structure features"""

        # Count paragraphs
        paragraphs = len([p for p in text.split('\n\n') if p.strip()])

        # Count bullet points and lists
        bullet_points = len(re.findall(r'^\s*[-*•]\s', text, re.MULTILINE))
        numbered_lists = len(re.findall(r'^\s*\d+\.\s', text, re.MULTILINE))

        # Check for headers (all caps words)
        headers = len(re.findall(r'^[A-Z\s]{3,}$', text, re.MULTILINE))

        # Check for quotes
        quotes = text.count('"') + text.count("'")

        return {
            'paragraph_count': paragraphs,
            'bullet_point_count': bullet_points,
            'numbered_list_count': numbered_lists,
            'header_count': headers,
            'quote_count': quotes,
            'is_structured': 1 if (paragraphs > 1 or bullet_points > 0 or numbered_lists > 0) else 0,
        }

    def _extract_metadata_features(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from report metadata"""
        features = {}

        # File size features
        if 'file_size' in metadata:
            file_size = metadata['file_size']
            features['file_size'] = file_size
            features['file_size_log'] = np.log10(file_size + 1)
            features['has_large_file'] = 1 if file_size > 10_000_000 else 0  # 10MB

        # Temporal features
        if 'submission_timestamp' in metadata:
            ts = metadata['submission_timestamp']
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))

            features['hour_of_day'] = ts.hour
            features['day_of_week'] = ts.weekday()
            features['is_weekend'] = 1 if ts.weekday() >= 5 else 0
            features['is_business_hours'] = 1 if 9 <= ts.hour <= 17 else 0

        # File type features
        if 'file_type' in metadata:
            file_type = metadata['file_type'].lower()
            features['is_document'] = 1 if file_type in ['pdf', 'doc', 'docx', 'txt'] else 0
            features['is_image'] = 1 if file_type in ['jpg', 'jpeg', 'png', 'gif'] else 0
            features['is_video'] = 1 if file_type in ['mp4', 'avi', 'mov'] else 0

        # Anonymity features
        if 'anonymous' in metadata:
            features['is_anonymous'] = 1 if metadata['anonymous'] else 0

        if 'visibility' in metadata:
            visibility = metadata['visibility']
            features['visibility_private'] = 1 if visibility == 'private' else 0
            features['visibility_public'] = 1 if visibility == 'public' else 0

        return features

    def extract_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Extract BERT embeddings for text

        Note: This is a placeholder. In production, you would:
        1. Load a pre-trained BERT model
        2. Tokenize the text
        3. Generate embeddings
        4. Return the embedding vector

        For now, returns None (can be implemented when needed)
        """
        if not self.bert_model:
            logger.debug("BERT embeddings not enabled, skipping")
            return None

        # TODO: Implement actual BERT embedding extraction
        # from transformers import AutoTokenizer, AutoModel
        # tokens = self.bert_tokenizer(text, return_tensors='pt', truncation=True)
        # with torch.no_grad():
        #     outputs = self.bert_model(**tokens)
        #     embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        # return embedding

        return None

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two text snippets

        Uses basic word overlap for now, can be upgraded to embedding similarity
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


# Global instance
feature_extractor = FeatureExtractor()
