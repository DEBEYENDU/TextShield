# TextShield v4.0 — Continuous Evaluation & Learning (RFC-006)

Systematic quality measurement without automatic retraining. The framework
collects high-quality evidence (records, regressions, feedback, drift) for
future, human-gated retraining.

## Architecture

```text
data/eval/*.json ─▶ DatasetManager ─▶ EvaluationEngine ─▶ run record
     (10 collections)     (validate/filter)    (full pipeline   data/eval/runs/
                                                per sample)          *.json
        │                       │                      │
        │                       ▼                      ▼
        │                 versioning            metrics · confusion
        │                 (fingerprint)         (FP/FN groups, per-agent,
        │                                       calibration, timing)
        ▼                       ▼                      ▼
BenchmarkRunner ──────── CLI (benchmark/evaluate/regression/feedback/reports)
        │                       │
        ▼                       ▼
reports (HTML/JSON/MD/CSV)   dashboard /api/evaluation/*
        │
        ▼
regression compare ─▶ CI gate (fail past threshold)
drift snapshots ────▶ PSI flags
feedback store ─────▶ review queue ─▶ training candidates (manual gate)
```

## Metrics definitions

Accuracy, precision, recall, F1 (SPAM-positive), ROC-AUC
(Mann-Whitney), balanced accuracy, FPR, FNR, specificity, per-category
and per-agent accuracy, expected calibration error (5-bin ECE), avg/p50/
max inference time.

## Dataset format

```json
{"id": "bank-01", "message": "...", "expected_label": "HAM",
 "message_type": "Bank Notification", "intent": "Notify",
 "difficulty": "easy", "source": "synthetic", "notes": "..."}
```

Collections live in `data/eval/*.json`; legacy v4 benchmarks import via
`DatasetManager.import_legacy_benchmarks()`.

## Benchmark execution

```bash
python app/evaluation/cli/benchmark.py                          # all
python app/evaluation/cli/benchmark.py --dataset banking --export html
python app/evaluation/cli/evaluate.py --dataset fraud --with-agents
python app/evaluation/cli/regression.py --old run-a --new run-b --threshold 0.02
python app/evaluation/cli/feedback.py --message "..." --verdict false_positive
python app/evaluation/cli/reports.py --run run-a --export markdown
```

## Regression workflow

Every module change: re-run benchmarks → `regression.py --old/--new`
→ improved/regressed/unchanged per sample → CI fails past the threshold
(default 2%).

## Feedback lifecycle

Analyst marks (correct/incorrect/FP/FN/needs_review) → prioritized
review queue (FN first) → resolve with notes → `export_training_candidates`
produces relabel suggestions for human-gated retraining. Nothing retrains
automatically — by design.
