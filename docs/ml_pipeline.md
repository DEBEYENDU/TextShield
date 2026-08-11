# TextShield — ML Pipeline

## 1. Overview

The machine-learning pipeline converts raw messages into a SPAM/HAM verdict
with a calibrated probability. It is deliberately classical and transparent:
**TF-IDF features → linear model**, because interpretability, small-data
robustness and speed on a laptop matter more than state-of-the-art accuracy.

```
raw text
  → preprocess (lowercase, whitespace, placeholder masking)
  → TF-IDF (word + bigram, sublinear tf, min_df=2)
  → classifier (predict_proba)
  → {label: SPAM|HAM, probability}
```

## 2. Preprocessing (`app/ml/preprocess.py`)

Text is normalized **conservatively** — spam-relevant signals are preserved:

| Transformation | Detail |
|---|---|
| lowercase | `"HURRY NOW!"` → `"hurry now!"` |
| URL masking | `https://bit.ly/x` → `[URL]` |
| Email masking | `bob@x.org` → `[EMAIL]` |
| Phone masking | `+91 98765 43210` → `[PHONE]` |
| Money masking | `Rs.50,000`, `$200`, `₹999` → `[MONEY]` |
| punctuation | exclamations collapsed to at most 2 (`!!!` → `!!`) |
| whitespace | multiple spaces/newlines → single space |

Masking keeps *presence* signals (e.g. "the message contains a URL/money/phone")
learnable by the model while preventing the classifier from memorizing
specific scam URLs. The raw text remains fully available to the indicator
engine and URL analyzer.

## 3. Feature extraction (`app/ml/features.py`)

`TfidfVectorizer` configuration:

```
lowercase=False        # already normalized
ngram_range=(1, 2)     # words + bigrams
min_df=2               # drop nearly-unique tokens (noise)
max_df=0.95            # drop tokens in >95% of docs
sublinear_tf=True      # tf -> 1 + log(tf)
strip_accents=ascii
```

The **same vectorizer instance** is saved and reused at inference time
(train/serve consistency). Vocabulary is capped by these settings; with the
UCI dataset (~5.5k rows) this yields ~8–9k features — trouble-free for linear
models.

## 4. Model comparison (`scripts/train_model.py`)

Three estimators are trained and compared on the identical stratified split:

1. **Multinomial Naive Bayes** — strong baseline on word-count features.
2. **Logistic Regression** — `max_iter=2000`, L2 regularization.
3. **Linear SVM** — `LinearSVC` wrapped in `CalibratedClassifierCV`
   (`cv=3`, sigmoid) so it produces real probabilities.

Selection criterion (documented in the script):

```
rank = (F1_spam, precision_spam, accuracy)
```

i.e. primarily **F1 on the spam class**, tie-broken by **spam precision**
(fewer false positives on legitimate mail), then accuracy.

## 5. Artifacts (`models/`)

| File | Content |
|---|---|
| `spam_classifier.joblib` | chosen estimator (fitted) |
| `tfidf_vectorizer.joblib` | fitted TF-IDF vectorizer |
| `model_metadata.json` | algorithm, trained_at, dataset sizes, metrics, three-model comparison, label mapping |
| `evaluation_report.json` | held-out test report incl. confusion matrix |
| `confusion_matrix.png` | optional if matplotlib installed |

## 6. Evaluation (`scripts/evaluate_model.py`)

Prints `classification_report`, confusion matrix (ham/spam ordering) and
writes JSON. Reference result on the bundled sample dataset:

| Algorithm | Acc | Prec(spam) | Rec(spam) | F1(spam) |
|---|---|---|---|---|
| MNB | 0.943 | 1.000 | 0.812 | 0.897 |
| LR | 0.849 | 1.000 | 0.500 | 0.667 |
| **LinearSVM** | **0.962** | **0.938** | **0.938** | **0.938** |

*These numbers move with dataset size — adding the UCI dataset (5,574 rows)
typically lifts F1 to ~0.97–0.99.*

## 7. Inference path (`app/ml/classifier.py`)

`SpamClassifier.predict(raw_text)`:

1. `normalize_text` (same function as training).
2. `vectorizer.transform([text])` (same instance).
3. `estimator.predict_proba` → probability per class.
4. `P(label=spam) >= 0.5` → SPAM; confidence = probability of the *predicted*
   class (rounded to 4 decimals).

The classifier is a stateless, pre-trained asset: no retraining at runtime,
no dependence on RAG/LLM modules.