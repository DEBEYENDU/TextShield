"""Dataset preparation pipeline.

Merges every CSV in ``data/raw/`` into a single cleaned dataset:

* generic column auto-detection (text column / label column)
* empty row removal
* duplicate removal
* label normalization (spam/1 -> spam, ham/0 -> ham)
* class distribution report
* stratified 80/20 train/test split (deterministic seed)

Usage:
    python scripts/prepare_dataset.py [--raw DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.model_selection import train_test_split

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
RANDOM_SEED = 42

TEXT_COLUMN_NAMES = ("text", "message", "sms", "message_text", "body", "v2", "content")
LABEL_COLUMN_NAMES = ("label", "class", "type", "category", "spam", "v1", "target")
SPAM_WORDS = {"spam", "1", "yes", "true", "spamming"}
HAM_WORDS = {"ham", "0", "no", "false", "legit", "legitimate", "not_spam"}


def find_column(columns: list[str], names: tuple[str, ...]) -> str | None:
    lowered = {c.lower() for c in columns}
    for name in names:
        if name in lowered:
            return columns[list(lowered).index(name)]
    return None


def load_dataset_file(path: Path) -> pd.DataFrame:
    """Load a single CSV and normalize to (text, label)."""
    df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    if df.empty or len(df.columns) < 2:
        raise ValueError(f"{path.name}: file has no usable rows/columns")

    text_col = find_column(list(df.columns), TEXT_COLUMN_NAMES)
    label_col = find_column(list(df.columns), LABEL_COLUMN_NAMES)
    if text_col is None or label_col is None:
        # fallback heuristic: last column holds the label
        label_col = df.columns[-1]
        text_col = df.columns[0]
        print(f"  [!] {path.name}: columns not auto-detected, using "
              f"'{text_col}' (text) and '{label_col}' (label).")

    out = pd.DataFrame(
        {"text": df[text_col].astype(str).str.strip(), "label": df[label_col].astype(str).str.strip()}
    )
    return out


def normalize_labels(labels: pd.Series) -> pd.Series:
    mapped = labels.str.lower().map(
        lambda v: "spam" if v in SPAM_WORDS else ("ham" if v in HAM_WORDS else None)
    )
    unknown = mapped.isna().sum()
    if unknown:
        bad = labels[mapped.isna()].unique()[:5]
        print(f"  [!] dropping {unknown} rows with unknown labels: {list(bad)}")
    return mapped


def prepare(
    raw_dir: Path = RAW_DIR,
    out_dir: Path = OUT_DIR,
    seed: int = RANDOM_SEED,
) -> dict:
    """Main preparation routine. Returns a summary dict of the outcome."""
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV datasets found in {raw_dir}. See data/README.md."
        )

    frames = []
    for path in csv_files:
        print(f"[+] loading {path.name}")
        frame = load_dataset_file(path)
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)

    print(f"[+] raw rows                : {len(df)}")
    df = df.dropna(subset=["text", "label"])
    df["text"] = df["text"].str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df["text"].str.len() > 0]
    print(f"[+] after empty-row removal : {len(df)}")

    df["label"] = normalize_labels(df["label"])
    df = df.dropna(subset=["label"])
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    print(f"[+] after deduplication     : {len(df)}")

    df["label"] = pd.Categorical(df["label"], categories=["ham", "spam"])
    distribution = df["label"].value_counts().to_dict()
    print("[+] class distribution:")
    for label, count in distribution.items():
        print(f"      {label:>6} : {count} ({count / len(df) * 100:.1f}%)")

    train, test = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=seed
    )
    train = train.sort_values("label").reset_index(drop=True)
    test = test.sort_values("label").reset_index(drop=True)

    df.to_csv(out_dir / "dataset.csv", index=False)
    train.to_csv(out_dir / "train.csv", index=False)
    test.to_csv(out_dir / "test.csv", index=False)

    info = {
        "source_files": [p.name for p in csv_files],
        "total_rows": int(len(df)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "distribution": distribution,
        "random_seed": seed,
    }
    (out_dir / "dataset_info.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )

    print(f"[+] wrote data/processed/dataset.csv ({len(df)} rows)")
    print(f"[+] wrote data/processed/train.csv   ({len(train)} rows)")
    print(f"[+] wrote data/processed/test.csv    ({len(test)} rows)")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare TextShield datasets")
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    prepare(args.raw, args.out)


if __name__ == "__main__":
    main()