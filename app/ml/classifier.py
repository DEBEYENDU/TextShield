"""Trained spam/ham classifier wrapper.

The classifier is a scikit-learn pipeline trained by
``scripts/train_model.py`` and persisted with joblib.

Responsibilities
----------------
* load model + TF-IDF vectorizer + label mapping from disk
* predict ``SPAM`` / ``HAM`` with a probability score

This module is the *primary* classification authority. It never relies
on the LLM or the RAG system, and it degrades to None (with a clear
error) if the model files are missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.features import build_tfidf_vectorizer
from app.ml.preprocess import normalize_text

logger = get_logger(__name__)

SPAM = "SPAM"
HAM = "HAM"


@dataclass(frozen=True)
class Prediction:
    label: str
    probability: float  # probability of the *predicted* class (0..1)

    @property
    def is_spam(self) -> bool:
        return self.label == SPAM


class SpamClassifier:
    """Loads and applies the saved ML model."""

    def __init__(
        self,
        model_path: Path | None = None,
        vectorizer_path: Path | None = None,
        metadata_path: Path | None = None,
    ) -> None:
        self.model_path = model_path or settings.MODEL_PATH
        self.vectorizer_path = vectorizer_path or settings.VECTORIZER_PATH
        self.metadata_path = metadata_path or settings.MODEL_METADATA_PATH
        self._model = None
        self._vectorizer = None
        self._metadata: dict | None = None

    # ------------------------------------------------------------- loading
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> bool:
        """Load model assets from disk. Returns False (and logs) on failure."""
        try:
            if not (self.model_path.exists() and self.vectorizer_path.exists()):
                logger.warning(
                    "Model files missing: %s / %s",
                    self.model_path,
                    self.vectorizer_path,
                )
                return False
            self._model = joblib.load(self.model_path)
            self._vectorizer = joblib.load(self.vectorizer_path)
            self._metadata = {}
            if self.metadata_path.exists():
                import json

                self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            logger.info("Classifier loaded (algorithm=%s)", self.algorithm_name)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load classifier: %s", exc)
            self._model = None
            return False

    def ensure_loaded(self) -> None:
        if not self.is_loaded and not self.load():
            raise RuntimeError(
                "ML model not available. Run `python scripts/train_model.py` first."
            )

    @property
    def algorithm_name(self) -> str:
        if not self._metadata:
            return "unknown"
        return self._metadata.get("algorithm", "unknown")

    # ----------------------------------------------------------- prediction
    def predict(self, raw_text: str) -> Prediction:
        """Classify a raw message into SPAM / HAM with probability."""
        self.ensure_loaded()
        normalized = normalize_text(raw_text)
        vector = self._vectorizer.transform([normalized])

        proba = self._probabilities(vector)[0]
        spam_prob = proba[self._spam_index()]
        label = SPAM if spam_prob >= 0.5 else HAM
        probability = spam_prob if label == SPAM else 1.0 - spam_prob
        return Prediction(label=label, probability=round(float(probability), 4))

    def _probabilities(self, vector):
        if self._model is None:
            raise RuntimeError("Model not loaded")
        if hasattr(self._model, "predict_proba"):
            return self._model.predict_proba(vector)
        if hasattr(self._model, "decision_function"):
            # Fallback: sigmoid scaling of decision scores (not used for
            # the selected model, but keeps arbitrary estimators working).
            import numpy as np

            scores = self._model.decision_function(vector)
            return np.vstack([1 - scores, scores]).T
        raise RuntimeError("Unsupported estimator: no predict_proba")

    def _spam_index(self) -> int:
        labels = list(self._model.classes_)
        if labels[0] != "ham":
            labels = sorted(labels)
        return labels.index("spam")

    # ------------------------------------------------------------ utilities
    @staticmethod
    def default_vectorizer(**overrides):
        """Fresh TF-IDF vectorizer (used mainly for training)."""
        return build_tfidf_vectorizer(**overrides)


classifier = SpamClassifier()