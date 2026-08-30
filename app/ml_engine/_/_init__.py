"""TextShield ML Engine — Phase 11.

Classical machine learning models for spam/phishing/fraud detection.

Models:
- Logistic Regression
- Linear SVM
- Random Forest
- XGBoost (optional)
- Naive Bayes

Models are one signal among many — combined by the Decision Engine (Phase 12).

All models produce:
- Probabilities (spam / ham)
- Confidence scores
- Feature importance (where applicable)
"""

from __future__ import annotations

import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.manifold import MDS
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

# ---------------------------------------------------------------------------
# Base class for all ML models
# ---------------------------------------------------------------------------

class BaseMLModel(ABC, BaseEstimator, ClassifierMixin):
    """Abstract base class for all TextShield ML models."""
    
    name: str = "base_ml_model"
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseMLModel":
        """Train the model on feature matrix X and labels y."""
        pass
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return class probabilities for X."""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return class predictions for X."""
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Return feature importance dict, or None if not applicable."""
        pass
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model accuracy and return metrics dict."""
        y_pred = self.predict(X)
        precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average="weighted")
        acc = accuracy_score(y, y_pred)
        cm = confusion_matrix(y, y_pred).tolist()
        return {
            "accuracy": float(acc),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "confusion_matrix": cm,
        }

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, type] = {}

def register_model(name: str, model_class: type) -> None:
    """Register an ML model class in the global registry."""
    MODEL_REGISTRY[name] = model_class

def get_model(name: str, **kwargs: Any) -> BaseMLModel:
    """Factory function to instantiate an ML model by name."""
    model_class = MODEL_REGISTRY.get(name)
    if model_class is None:
        raise ValueError(
            f"Unknown ML model: {name}. Available: {list(MODEL_REGISTRY.keys())}"
        )
    return model_class(**kwargs)

# ---------------------------------------------------------------------------
# Concrete model implementations
# ---------------------------------------------------------------------------

class LogisticRegressionModel(BaseMLModel):
    """Logistic Regression classifier with L2 regularization."""
    name = "logistic_regression"
    
    def __init__(self, C: float = 1.0, max_iter: int = 100, random_state: int = 42):
        self.model = LogisticRegression(C=C, max_iter=max_iter, random_state=random_state, solver="lbfgs")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionModel":
        self.model.fit(X, y)
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        coef = self.model.coef_[0]
        return {f"feat_{i}": float(abs(c)) for i, c in enumerate(coef)}

class LinearSVMModel(BaseMLModel):
    """Linear Support Vector Machine classifier."""
    name = "linear_svm"
    
    def __init__(self, C: float = 1.0, max_iter: int = 100, random_state: int = 42):
        from sklearn.svm import LinearSVC
        self.model = LinearSVC(C=C, max_iter=max_iter, random_state=random_state, dual="auto")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearSVMModel":
        self.model.fit(X, y)
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        from scipy.special import expit
        decision = self.model.decision_function(X)
        probs = expit(decision)
        return np.column_stack([1 - probs, probs])
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        coef = np.abs(self.model.coef_[0])
        return {f"feat_{i}": float(c) for i, c in enumerate(coef)}

class RandomForestModel(BaseMLModel):
    """Random Forest classifier."""
    name = "random_forest"
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 10, random_state: int = 42, min_samples_split: int = 2):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            min_samples_split=min_samples_split,
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestModel":
        self.model.fit(X, y)
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        importances = self.model.feature_importances_
        return {f"feat_{i}": float(imp) for i, imp in enumerate(importances)}

class NaiveBayesModel(BaseMLModel):
    """Naive Bayes classifier."""
    name = "naive_bayes"
    
    def __init__(self, var_smoothing: float = 1e-9):
        self.model = GaussianNB(var_smoothing=var_smoothing)
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "NaiveBayesModel":
        self.model.fit(X, y)
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        return None

# Register all models
register_model("logistic_regression", LogisticRegressionModel)
register_model("linear_svm", LinearSVMModel)
register_model("random_forest", RandomForestModel)
register_model("naive_bayes", NaiveBayesModel)

# ---------------------------------------------------------------------------
# Feature extraction and pipeline
# ---------------------------------------------------------------------------

class MLFeatureExtractor:
    """Transforms text features into numeric feature vectors using TF-IDF."""
    
    def __init__(self, max_features: int = 5000, ngram_range: tuple = (1, 2)):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words="english",
            lowercase=True,
        )
        self.fitted = False
    
    def fit(self, texts: List[str]) -> "MLFeatureExtractor":
        self.vectorizer.fit(texts)
        self.fitted = True
        return self
    
    def transform(self, texts: List[str]) -> np.ndarray:
        if not self.fitted:
            raise ValueError("Vectorizer must be fitted before transform.")
        return self.vectorizer.transform(texts).toarray()

def extract_text_features(
    semantic_fea
