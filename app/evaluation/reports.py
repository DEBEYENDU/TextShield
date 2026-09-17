"""Report generation: HTML, JSON, Markdown and CSV from a run record."""

from __future__ import annotations

import csv
import io
import json

from app.evaluation import confusion as confusion_mod
from app.evaluation import metrics as metrics_mod


def summarize_run(run: dict) -> dict:
    """Full metrics summary for a run (shared by all renderers)."""
    records = [r for r in run.get("records", []) if r.get("predicted") != "ERROR"]
    y_true = [r.get("expected", "") for r in records]
    y_pred = [r.get("predicted", "") for r in records]
    y_score = [float(r.get("spam_score", 0.5) or 0.5) for r in records]
    summary = {
        "run_id": run.get("run_id"),
        "fingerprint_id": run.get("fingerprint_id"),
        "n_samples": len(records),
        "metrics": metrics_mod.classification_metrics(y_true, y_pred, y_score),
        "confusion": confusion_mod.confusion_matrix(records),
        "false_positives": confusion_mod.false_positives(records),
        "false_negatives": confusion_mod.false_negatives(records),
        "per_category": metrics_mod.per_category_accuracy(records),
        "per_agent": metrics_mod.per_agent_accuracy(records),
        "calibration": metrics_mod.confidence_calibration(records),
        "timing": metrics_mod.timing_stats(records),
    }
    return summary


def to_json(run: dict) -> str:
    return json.dumps({"summary": summarize_run(run), "records": run.get("records", [])},
                      indent=1, default=str)


def to_markdown(run: dict) -> str:
    s = summarize_run(run)
    m = s["metrics"]
    lines = [
        f"# Evaluation Report — `{s['run_id']}`",
        "",
        f"Fingerprint `{s['fingerprint_id']}` · {s['n_samples']} samples",
        "",
        "## Metrics",
        "",
        f"- Accuracy: **{m['accuracy']}** · Precision: **{m['precision']}** · "
        f"Recall: **{m['recall']}** · F1: **{m['f1']}**",
        f"- ROC-AUC: **{m['roc_auc']}** · Balanced accuracy: **{m['balanced_accuracy']}**",
        f"- FPR: **{m['false_positive_rate']}** · FNR: **{m['false_negative_rate']}**",
        "",
        "## Confusion Matrix (rows=actual, cols=predicted)",
        "",
        "|  | HAM | SPAM |",
        "|--|-----|------|",
        f"| HAM | {s['confusion']['matrix'][0][0]} | {s['confusion']['matrix'][0][1]} |",
        f"| SPAM | {s['confusion']['matrix'][1][0]} | {s['confusion']['matrix'][1][1]} |",
        "",
        f"## False Positives ({s['false_positives']['count']})",
        "",
    ]
    for key, val in s["false_positives"]["by_message_type"].items():
        lines.append(f"- {key}: {val['count']}")
    lines += ["", f"## False Negatives ({s['false_negatives']['count']})", ""]
    for key, val in s["false_negatives"]["by_threat_family"].items():
        lines.append(f"- {key}: {val['count']}")
    lines += ["", "## Per-Category Accuracy", ""]
    for key, val in s["per_category"].items():
        lines.append(f"- {key}: {val['accuracy']} ({val['correct']}/{val['total']})")
    if s["per_agent"]:
        lines += ["", "## Per-Agent Accuracy", ""]
        for key, val in s["per_agent"].items():
            lines.append(f"- {key}: {val['accuracy']}")
    lines += ["",
              f"Calibration ECE: **{s['calibration']['expected_calibration_error']}** · "
              f"Avg inference: **{s['timing']['avg_ms']} ms**"]
    return "\n".join(lines) + "\n"


def to_csv(run: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "expected", "predicted", "confidence", "message_type",
                     "collection", "difficulty", "threat_score", "trust_score",
                     "risk_level", "inference_ms"])
    for r in run.get("records", []):
        writer.writerow([r.get("id"), r.get("expected"), r.get("predicted"),
                         r.get("confidence"), r.get("message_type"),
                         r.get("collection"), r.get("difficulty"),
                         r.get("threat_score"), r.get("trust_score"),
                         r.get("risk_level"), r.get("inference_ms")])
    return buf.getvalue()


def to_html(run: dict) -> str:
    s = summarize_run(run)
    m = s["metrics"]
    cm = s["confusion"]["matrix"]
    fp_rows = "".join(
        f"<tr><td>{k}</td><td>{v['count']}</td></tr>"
        for k, v in s["false_positives"]["by_message_type"].items()) or "<tr><td colspan=2>none</td></tr>"
    fn_rows = "".join(
        f"<tr><td>{k}</td><td>{v['count']}</td></tr>"
        for k, v in s["false_negatives"]["by_threat_family"].items()) or "<tr><td colspan=2>none</td></tr>"
    cat_rows = "".join(
        f"<tr><td>{k}</td><td>{v['accuracy']}</td><td>{v['correct']}/{v['total']}</td></tr>"
        for k, v in s["per_category"].items())
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Evaluation {s['run_id']}</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:2em auto}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:4px 10px}}.m{{background:#f6f8fa;padding:1em}}</style>
</head><body>
<h1>Evaluation Report — {s['run_id']}</h1>
<p>Fingerprint <code>{s['fingerprint_id']}</code> · {s['n_samples']} samples</p>
<div class="m">Accuracy <b>{m['accuracy']}</b> · Precision <b>{m['precision']}</b> ·
Recall <b>{m['recall']}</b> · F1 <b>{m['f1']}</b> · ROC-AUC <b>{m['roc_auc']}</b> ·
FPR <b>{m['false_positive_rate']}</b> · FNR <b>{m['false_negative_rate']}</b> ·
ECE <b>{s['calibration']['expected_calibration_error']}</b> ·
avg inference <b>{s['timing']['avg_ms']} ms</b></div>
<h2>Confusion matrix</h2>
<table><tr><th></th><th>HAM</th><th>SPAM</th></tr>
<tr><th>HAM</th><td>{cm[0][0]}</td><td>{cm[0][1]}</td></tr>
<tr><th>SPAM</th><td>{cm[1][0]}</td><td>{cm[1][1]}</td></tr></table>
<h2>False positives by message type</h2><table>{fp_rows}</table>
<h2>False negatives by threat family</h2><table>{fn_rows}</table>
<h2>Per-category accuracy</h2><table><tr><th>category</th><th>acc</th><th>n</th></tr>{cat_rows}</table>
</body></html>"""
