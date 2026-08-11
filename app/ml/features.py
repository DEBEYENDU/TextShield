"""Feature extraction.

The primary feature representation is TF-IDF over normalized text
(character and word n-grams). The TF-IDF vectorizer used for training is
saved to disk and reused at inference time so train/serve stay consistent.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer

from app.ml.preprocess import normalize_text, tokenize


def build_tfidf_vectorizer(**overrides) -> TfidfVectorizer:
    """Create the TF-IDF vectorizer with project defaults.

    Keyword arguments override the defaults (useful for tests/experiments).
    """
    defaults: dict = {
        "lowercase": False,  # text is already normalized to lowercase
        "ngram_range": (1, 2),
        "min_df": 2,
        "max_df": 0.95,
        "sublinear_tf": True,
        "strip_accents": "ascii",
        "analyzer": "word",
    }
    defaults.update(overrides)
    return TfidfVectorizer(**defaults)


def prepare_corpus(texts: list[str], remove_stopwords: bool = False) -> list[str]:
    """Normalize a corpus so it matches the preprocessing at inference time.

    ``remove_stopwords`` is optional (off by default); see preprocess.tokenize.
    """
    if remove_stopwords:
        return [" ".join(tokenize(t, remove_stopwords=True)) for t in texts]
    return [normalize_text(t) for t in texts]