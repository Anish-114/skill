import logging
import os
import re
import threading
from typing import Optional, List
import numpy as np

# Suppress hub warnings and prefer cached offline files
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

logger = logging.getLogger(__name__)


class VectorMatcher:
    """
    Singleton service providing semantic vector embeddings and similarity computations.
    Uses sentence-transformers ('all-MiniLM-L6-v2') by default, caching the model in memory.
    Falls back gracefully to TF-IDF & token overlap matching if the transformer model
    fails to load or runs in low-resource environments.
    """
    _instance: Optional["VectorMatcher"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "VectorMatcher":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VectorMatcher, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._model = None
        self._load_attempted = False
        self._use_fallback = False
        self._initialized = True

    def _load_model(self) -> None:
        """Attempt to load sentence-transformers model once."""
        if self._load_attempted:
            return

        with self._lock:
            if self._load_attempted:
                return
            try:
                logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2')...")
                from sentence_transformers import SentenceTransformer
                # Try loading from local cached weights first to avoid DNS delays in restricted environments
                try:
                    self._model = SentenceTransformer("all-MiniLM-L6-v2", model_kwargs={"local_files_only": True})
                except Exception:
                    self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._use_fallback = False
                logger.info("SentenceTransformer('all-MiniLM-L6-v2') loaded successfully.")
            except Exception as exc:
                logger.warning(
                    f"Unable to load SentenceTransformer ('{exc}'). "
                    f"Engaging fallback TF-IDF & token similarity engine."
                )
                self._model = None
                self._use_fallback = True
            finally:
                self._load_attempted = True

    def compute_semantic_match(self, profile_text: str, opportunity_text: str) -> float:
        """
        Compute semantic similarity between student profile text and opportunity text.
        
        Returns:
            float: Score strictly bounded between 0.0 and 100.0.
        """
        # Input validation & sanitization
        if not profile_text or not profile_text.strip():
            return 0.0
        if not opportunity_text or not opportunity_text.strip():
            return 0.0

        p_clean = profile_text.strip()
        o_clean = opportunity_text.strip()

        self._load_model()

        # Primary Path: sentence-transformers neural embeddings
        if self._model is not None and not self._use_fallback:
            try:
                embeddings = self._model.encode(
                    [p_clean, o_clean],
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                # Cosine similarity between normalized vectors is dot product
                cosine_sim = float(np.dot(embeddings[0], embeddings[1]))
                # Scale from [-1.0, 1.0] to [0.0, 100.0]
                scaled_score = max(0.0, min(100.0, cosine_sim * 100.0))
                return round(scaled_score, 2)
            except Exception as exc:
                logger.warning(f"Transformer inference encountered error: {exc}. Falling back to TF-IDF.")

        # Secondary Path: TF-IDF vector cosine similarity
        return self._compute_tfidf_match(p_clean, o_clean)

    def _compute_tfidf_match(self, text1: str, text2: str) -> float:
        """Fallback TF-IDF matcher using scikit-learn."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                lowercase=True
            )
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            score = max(0.0, min(100.0, sim * 100.0))
            return round(score, 2)
        except Exception as exc:
            logger.warning(f"TF-IDF matching failed: {exc}. Falling back to token overlap.")
            return self._compute_token_overlap(text1, text2)

    def _compute_token_overlap(self, text1: str, text2: str) -> float:
        """Tertiary fallback: Jaccard token overlap."""
        tokens1 = set(re.findall(r"\w+", text1.lower()))
        tokens2 = set(re.findall(r"\w+", text2.lower()))

        # Remove very common stopwords
        stopwords = {"and", "the", "in", "to", "of", "a", "is", "for", "with", "on", "as"}
        tokens1 = tokens1 - stopwords
        tokens2 = tokens2 - stopwords

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        if union == 0:
            return 0.0

        jaccard_score = (intersection / union) * 100.0
        return round(max(0.0, min(100.0, jaccard_score)), 2)


# Module-level singleton instance & helper
_matcher = VectorMatcher()


def compute_semantic_match(profile_text: str, opportunity_text: str) -> float:
    """Convenience module function for computing semantic match score (0.0 to 100.0)."""
    return _matcher.compute_semantic_match(profile_text, opportunity_text)
