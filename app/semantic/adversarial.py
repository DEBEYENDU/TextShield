"""Adversarial robustness testing utilities."""

from __future__ import annotations
import random
import string


def obfuscate_text(text: str, level: float = 0.1) -> str:
    chars = list(text)
    n_changes = max(1, int(len(chars) * level))
    indices = random.sample(range(len(chars)), min(n_changes, len(chars)))
    for i in indices:
        if chars[i].isalpha():
            chars[i] = random.choice(string.ascii_lowercase)
    return ''.join(chars)


def test_robustness(pipeline, text: str, trials: int = 5):
    results = []
    for _ in range(trials):
        obf = obfuscate_text(text, 0.05)
        try:
            res = pipeline.analyze(message=obf, message_type="text", include_embeddings=False)
            results.append(res.language)
        except Exception:
            results.append("error")
    return results
