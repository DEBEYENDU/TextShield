"""Train and compare spam/ham classifiers.

Algorithms compared:
    1. Multinomial Naive Bayes
    2. Logistic Regression
    3. Linear SVM (with calibrated probabilities)

Selection criteria (in order): F1-score on the spam class, then
precision on the spam class (lower false positives), then accuracy.

The winning pipeline (TF-IDF vectorizer + model) is saved with joblib
alongside a machine-readable metadata file.

Usage:
    python scripts/train_model.py [--train FILE] [--test FILE] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from app.ml.features import build_tfidf_vectorizer, prepare_corpus

DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
RANDOM_SEED = 42

ESTIMATORS = {
    "Multinomial Naive Bayes": MultinomialNB(),
    "Logistic Regression": LogisticRegression(max_iter=2000, random_state=RANDOM_SEED),
    "Linear SVM": CalibratedClassifierCV(
        LinearSVC(max_iter=5000, random_state=RANDOM_SEED),
        cv=3,
        method="sigmoid",
    ),
}


def load_split(train_file: Path, test_file: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load prepared train/test CSV files (falling back to an internal split)."""
    if train_file.exists() and test_file.exists():
        train = pd.read_csv(train_file)
        test = pd.read_csv(test_file)
        print(f"[+] using prepared split: train={len(train)} test={len(test)}")
        return train, test

    dataset_file = DATA_DIR / "dataset.csv"
    if not dataset_file.exists():
        print("[!] processed dataset not found - running prepare first...")
        from scripts.prepare_dataset import prepare

        prepare()
    df = pd.read_csv(dataset_file)
    train, test = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=RANDOM_SEED
    )
    print(f"[+] internal split: train={len(train)} test={len(test)}")
    return train, test


def evaluate(y_true, y_pred) -> dict:
    """Compute and return standard classification metrics."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=["spam"], average=None, zero_division=0
    )
    weighted_f1 = f1_score_weighted(y_true, y_pred)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_spam": round(float(precision[0]), 4),
        "recall_spam": round(float(recall[0]), 4),
        "f1_spam": round(float(f1[0]), 4),
        "f1_weighted": round(float(weighted_f1), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=["ham", "spam"]).tolist(),
    }


def f1_score_weighted(y_true, y_pred) -> float:
    from sklearn.metrics import f1_score

    return float(f1_score(y_true, y_pred, average="weighted", zero_division=0))


def fit_estimator(name: str, estimator, x_train, y_train, x_test, y_test) -> dict:
    start = time.perf_counter()
    estimator.fit(x_train, y_train)
    y_pred = estimator.predict(x_test)
    elapsed = round(time.perf_counter() - start, 2)
    metrics = evaluate(y_test, y_pred)
    metrics["training_seconds"] = elapsed
    print(f"  {name:<26} acc={metrics['accuracy']:.3f} "
          f"prec={metrics['precision_spam']:.3f} rec={metrics['recall_spam']:.3f} "
          f"F1(spam)={metrics['f1_spam']:.3f} ({elapsed}s)")
    return {"estimator": estimator, "metrics": metrics}


def select_best(results: dict[str, dict], label_names: list[str]) -> str:
    """Rank models by F1(spam), then precision(spam), then accuracy."""
    def rank_key(name: str):
        m = results[name]["metrics"]
        return (m["f1_spam"], m["precision_spam"], m["accuracy"])

    return max(results, key=rank_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TextShield classifiers")
    parser.add_argument("--train", type=Path, default=DATA_DIR / "train.csv")
    parser.add_argument("--test", type=Path, default=DATA_DIR / "test.csv")
    parser.add_argument("--out", type=Path, default=MODELS_DIR)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    train, test = load_split(args.train, args.test)

    # deterministic label order: ham=0, spam=1
    label_order = ["ham", "spam"]
    train = train[train["label"].isin(label_order)]
    test = test[test["label"].isin(label_order)]
    y_train = train["label"].to_numpy()
    y_test = test["label"].to_numpy()
    print(f"[+] labels: ham={int((y_train == 'ham').sum())} spam={int((y_train == 'spam').sum())} (train)")

    # ----------------------------- TF-IDF features
    corpus_train = prepare_corpus(train["text"].tolist())
    corpus_test = prepare_corpus(test["text"].tolist())
    vectorizer = build_tfidf_vectorizer()
    x_train = vectorizer.fit_transform(corpus_train)
    x_test = vectorizer.transform(corpus_test)
    print(f"[+] TF-IDF vocabulary size: {len(vectorizer.vocabulary_)}")

    # ----------------------------- train & compare
    results: dict[str, dict] = {}
    for name, estimator in ESTIMATORS.items():
        results[name] = fit_estimator(
            name, estimator, x_train, y_train, x_test, y_test
        )

    best_name = select_best(results, label_order)
    best = results[best_name]
    print(f"\n[+] Best model: {best_name} "
          f"(F1 spam: {best['metrics']['f1_spam']:.3f}, "
          f"precision spam: {best['metrics']['precision_spam']:.3f})")

    # ----------------------------- persist artifacts
    model_path = args.out / "spam_classifier.joblib"
    vectorizer_path = args.out / "tfidf_vectorizer.joblib"
    joblib.dump(best["estimator"], model_path)
    joblib.dump(vectorizer, vectorizer_path)
    print(f"[+] saved model      -> {model_path}")
    print(f"[+] saved vectorizer -> {vectorizer_path}")

    comparison = {
        name: {"metrics": results[name]["metrics"]} for name in results
    }
    metadata = {
        "algorithm": best_name,
        "model_file": str(model_path),
        "vectorizer_file": str(vectorizer_path),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
        },
        "label_mapping": {"ham": 0, "spam": 1},
        "classes": label_order,
        "tfidf": {
            "ngram_range": (1, 2),
            "min_df": 2,
            "max_df": 0.95,
            "sublinear_tf": True,
        },
        "selected_model": best_name,
        "metrics": best["metrics"],
        "comparison": comparison,
    }
    metadata_path = args.out / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[+] saved metadata   -> {metadata_path}")

    # ----------------------------- optional confusion matrix plot
    try:
        _save_confusion_plot(best["metrics"]["confusion_matrix"], best_name, args.out)
    except ImportError:
        print("[!] matplotlib not installed - skipping confusion matrix PNG")


def _save_confusion_plot(matrix: list, best_name: str, out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], ["HAM", "SPAM"])
    ax.set_yticks([0, 1], ["HAM", "SPAM"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(f"Confusion matrix - {best_name}")
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=110)
    print(f"[+] saved confusion matrix PNG -> models/confusion_matrix.png")


if __name__ == "__main__":
    main()