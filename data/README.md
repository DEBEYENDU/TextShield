# Dataset Guide

All training data lives in this directory:

```
data/
├── raw/        <- place raw CSV datasets here (never committed as large files)
├── processed/  <- output of scripts/prepare_dataset.py (git-ignored)
└── README.md
```

## Expected CSV format

The pipeline is generic. Any CSV in `data/raw/` with a **text column** and a
**label column** is accepted:

```csv
text,label
"Congratulations! You have won a prize.","spam"
"Are we meeting at 5 PM?","ham"
```

* Labels must be `spam` (or `1`, `spam`) and `ham` (or `0`, `ham`).
* The prepare script auto-detects columns by header name:
  * text column: `text`, `message`, `sms`, `body`, `v2` (UCI), ...
  * label column: `label`, `type`, `class`, `category`, `v1` (UCI), `spam`, ...
* `data/raw/sample_sms_dataset.csv` is included for immediate testing.

## Included sample dataset

* File: `data/raw/sample_sms_dataset.csv`
* Rows: 264 (78 spam / 186 ham)
* Contents: curated messages typed in the style of real SMS/phishing and
  everyday conversation, including Indian-English examples (₹, KYC, UPI,
  Aadhaar, lakh).
* Purpose: lets you run the full pipeline **immediately**. It is a small
  curated sample, **not** a benchmark.

## Recommended public dataset (documented source)

For better accuracy, download the classic **UCI SMS Spam Collection** and
place it in `data/raw/`:

* **Name:** SMS Spam Collection v.1
* **Source (official):** https://archive.ics.uci.edu/ml/datasets/sms+spam+collection
  (mirror: https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset)
* **File name:** `spam.csv` (put it in `data/raw/`)
* **Rows:** 5,574 (13.4% spam)
* **Columns:** `v1` (label), `v2` (message) - supported by the auto-detector.

> Citation (from the UCI page): Almeida, T.A., Gómez Hidalgo, J.M.,
> Yamakami, A. (2011). "Contributions to the study of SMS spam filtering:
> new collection and results." ACM DocEng 2011.

## Prepare the dataset

```bash
# merges every CSV in data/raw/, cleans, deduplicates, splits
python scripts/prepare_dataset.py
```

Outputs written to `data/processed/`:

* `dataset.csv` - full cleaned dataset
* `train.csv` - stratified 80% split
* `test.csv` - stratified 20% split
* `dataset_info.json` - class distribution, sizes, sources

## Warnings

* Do **not** commit large downloaded datasets to the repository.
* The prepare script is deterministic (stable shuffle seed), so repeated
  runs produce identical splits.