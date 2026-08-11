"""Evaluate the saved TextShield model against the held-out test set.

Prints a full classification report, confusion matrix and saves a
machine-readable evaluation report to ``models/evaluation_report.json``.

Usage:
    python scripts/evaluate_model.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from app.core.config import settings
from app.ml.features import prepare_corpus

DATA_DIR = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the saved TextShield model")
    parser.add_argument("--test", type=Path, default=DATA_DIR / "test.csv")
    args = parser.parse_args()

    if not (settings.MODEL_PATH.exists() and settings.VECTORIZER_PATH.exists()):
        raise SystemExit(
            "Model files not found. Run `python scripts/train_model.py` first."
        )

    model = joblib.load(settings.MODEL_PATH)
    vectorizer = joblib.load(settings.VECTORIZER_PATH)
    test = pd.read_csv(args.test)
    test = test[test["label"].isin(["ham", "spam"])]

    x_test = vectorizer.transform(prepare_corpus(test["text"].tolist()))
    y_true = test["label"].to_numpy()
    y_pred = model.predict(x_test)

    print("=" * 62)
    print("TextShield - model evaluation on held-out test set")
    print("=" * 62)
    print(classification_report(y_true, y_pred, digits=4))

    cm = confusion_matrix(y_true, y_pred, labels=["ham", "spam"])
    print("Confusion matrix (rows=actual, cols=predicted)")
    print(f"{'':>10}{'HAM':>8}{'SPAM':>8}")
    print(f"{'HAM':>10}{cm[0][0]:>8}{cm[0][1]:>8}")
    print(f"{'SPAM':>10}{cm[1][0]:>8}{cm[1][1]:>8}")

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=["spam"], average=None, zero_division=0
    )
    report = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_spam": round(float(precision[0]), 4),
        "recall_spam": round(float(recall[0]), 4),
        "f1_spam": round(float(f1[0]), 4),
        "test_rows": int(len(test)),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y_true, y_pred, digits=4, output_dict=True
        ),
    }
    settings.MODEL_METRICS_PATH.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"\n[+] saved evaluation report -> {settings.MODEL_METRICS_PATH}")


if __name__ == "__main__":
    main()