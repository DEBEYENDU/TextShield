from __future__ import annotations

import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)


class BaseMLModel(ABC, BaseEstimator, ClassifierMixin):
    name: str = "base_ml_model"

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseMLModel": ...

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray: ...

    @abstractmethod
    def get_feature_importance(self) -> Optional[Dict[str, float]]: ...

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        y_pred = self.predict(X)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y, y_pred, average="weighted"
        )
        acc = accuracy_score(y, y_pred)
        cm = confusion_matrix(y, y_pred).tolist()
        return {
            "accuracy": float(acc),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "confusion_matrix": cm,
        }


MODEL_REGISTRY: Dict[str, type] = {}


def register_model(name: str, model_class: type) -> None:
    MODEL_REGISTRY[name] = model_class


def get_model(name: str, **kwargs: Any) -> BaseMLModel:
    model_class = MODEL_REGISTRY.get(name)
    if model_class is None:
        raise ValueError(
            f"Unknown ML model: {name}. Available: {list(MODEL_REGISTRY.keys())}"
        )
    return model_class(**kwargs)


class LogisticRegressionModel(BaseMLModel):
    name = "logistic_regression"

    def __init__(self, C: float = 1.0, max_iter: int = 100, random_state: int = 42):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        from sklearn.linear_model import LogisticRegression

        self.model = LogisticRegression(
            C=C, max_iter=max_iter, random_state=random_state, solver="lbfgs"
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionModel":
        self.model.fit(X, y)
        self.classes_ = np.unique(y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        coef = self.model.coef_[0]
        return {f"feat_{i}": float(abs(c)) for i, c in enumerate(coef)}


class LinearSVMModel(BaseMLModel):
    name = "linear_svm"

    def __init__(self, C: float = 1.0, max_iter: int = 100, random_state: int = 42):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        from sklearn.svm import LinearSVC

        self.model = LinearSVC(
            C=C, max_iter=max_iter, random_state=random_state, dual="auto"
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearSVMModel":
        self.model.fit(X, y)
        self.classes_ = np.unique(y)
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
    name = "random_forest"

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
        min_samples_split: int = 2,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.min_samples_split = min_samples_split
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            min_samples_split=min_samples_split,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestModel":
        self.model.fit(X, y)
        self.classes_ = np.unique(y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        importances = self.model.feature_importances_
        return {f"feat_{i}": float(imp) for i, imp in enumerate(importances)}


class NaiveBayesModel(BaseMLModel):
    name = "naive_bayes"

    def __init__(self, var_smoothing: float = 1e-9):
        self.var_smoothing = var_smoothing
        from sklearn.naive_bayes import GaussianNB

        self.model = GaussianNB(var_smoothing=var_smoothing)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NaiveBayesModel":
        self.model.fit(X, y)
        self.classes_ = np.unique(y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        return None


register_model("logistic_regression", LogisticRegressionModel)
register_model("linear_svm", LinearSVMModel)
register_model("random_forest", RandomForestModel)
register_model("naive_bayes", NaiveBayesModel)


class MLFeatureExtractor:
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
    semantic_features: Dict[str, Any],
    intent_analysis: Optional[Dict[str, Any]] = None,
    behavior_analysis: Optional[Dict[str, Any]] = None,
    rag_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    parts: List[str] = []
    topic_names = semantic_features.get("topic_names", [])
    if topic_names:
        parts.append(f"topics: {' '.join(topic_names)}")
    entities = semantic_features.get("entities", [])
    if entities:
        parts.append(f"entities: {' '.join(entities)}")
    intent = semantic_features.get("intent", "")
    if intent:
        parts.append(f"intent: {intent}")
    behavioral_patterns = semantic_features.get("behavioral_patterns", [])
    if behavioral_patterns:
        parts.append(f"behaviors: {' '.join(behavioral_patterns)}")
    communication_goal = semantic_features.get("communication_goal", "")
    if communication_goal:
        parts.append(f"goal: {communication_goal}")
    if intent_analysis is not None:
        primary = intent_analysis.get("primary_intent", "")
        if primary:
            parts.append(f"primary_intent: {primary}")
        secondary = intent_analysis.get("secondary_intents", [])
        if secondary:
            parts.append(f"secondary_intents: {' '.join(secondary)}")
    if behavior_analysis is not None:
        b_patterns = behavior_analysis.get("behavioral_patterns", [])
        if b_patterns:
            parts.append(f"behaviors: {' '.join(b_patterns)}")
        communication_style = behavior_analysis.get("communication_style", "")
        if communication_style:
            parts.append(f"communication_style: {communication_style}")
        urgency_level = behavior_analysis.get("urgency_level", "")
        if urgency_level:
            parts.append(f"urgency_level: {urgency_level}")
    if rag_results:
        summaries: List[str] = []
        for chunk in rag_results[:3]:
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "")
            category = metadata.get("category", "")
            if content:
                summaries.append(content[:100])
            if source:
                summaries.append(f"source:{source}")
            if category:
                summaries.append(f"category:{category}")
        parts.append(f"rag_evidence: {' '.join(summaries)}")
    return {"text": " . ".join(parts)}


def train_ml_pipeline(
    X_texts: List[str],
    y_labels: List[str],
    model_names: Optional[List[str]] = None,
    cv_folds: int = 5,
) -> Dict[str, Any]:
    if model_names is None:
        model_names = list(MODEL_REGISTRY.keys())
    extractor = MLFeatureExtractor()
    X_vectors = extractor.fit(X_texts).transform(X_texts)
    label_set = sorted(set(y_labels))
    label_to_idx: Dict[str, int] = {label: i for i, label in enumerate(label_set)}
    y_idx = np.array([label_to_idx[label] for label in y_labels])
    results: Dict[str, Any] = {
        "label_to_idx": label_to_idx,
        "idx_to_label": {i: l for i, l in label_to_idx.items()},
        "models": {},
        "extractor": extractor,
        "best_model": None,
        "best_score": -1.0,
    }
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    for name in model_names:
        if name not in MODEL_REGISTRY:
            print(f"Warning: Unknown model '{name}', skipping.")
            continue
        model = get_model(name)
        scores = cross_val_score(model, X_vectors, y_idx, cv=skf, scoring="accuracy")
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        model.fit(X_vectors, y_idx)
        y_pred = model.predict(X_vectors)
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_idx, y_pred, average="weighted"
        )
        model_result = {
            "cross_val_mean_accuracy": mean_score,
            "cross_val_std_accuracy": std_score,
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "model": model,
        }
        results["models"][name] = model_result
        if mean_score > results["best_score"]:
            results["best_score"] = mean_score
            results["best_model"] = name
    return results


def predict_ml(
    text_or_features: str,
    model_name: str = "logistic_regression",
    extractor: Optional[MLFeatureExtractor] = None,
    trained_model: Optional[BaseMLModel] = None,
) -> Dict[str, Any]:
    from sklearn.feature_extraction.text import TfidfVectorizer

    if trained_model is None:
        trained_model = get_model(model_name)
    if extractor is None:
        vec = (
            TfidfVectorizer(max_features=100, ngram_range=(1, 1))
            .fit([text_or_features])
            .transform([text_or_features])
            .toarray()
        )
    else:
        vec = extractor.transform([text_or_features])
    vec = np.asarray(vec, dtype=np.float64)
    model_proba = trained_model.predict_proba(vec)[0]
    classes = trained_model.classes_
    pred_idx = int(np.argmax(model_proba))
    prediction = classes[pred_idx] if pred_idx < len(classes) else "unknown"
    confidence = float(np.max(model_proba))
    fi = trained_model.get_feature_importance()
    if fi is None:
        fi = {}
    return {
        "probabilities": {
            classes[i]: float(model_proba[i]) for i in range(len(classes))
        },
        "confidence": confidence,
        "feature_importance": fi,
        "prediction": prediction,
    }


def evaluate_ml(
    y_true: List[str], y_pred: List[str], labels: Optional[List[str]] = None
) -> Dict[str, float]:
    from sklearn.metrics import (
        accuracy_score,
        precision_recall_fscore_support,
        confusion_matrix as sk_cm,
    )

    if labels is None:
        labels = sorted(set(y_true + y_pred))
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", labels=labels
    )
    cm = sk_cm(y_true, y_pred, labels=labels).tolist()
    return {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "confusion_matrix": cm,
    }
