"""Linguistic analysis: complexity, readability, tone, grammar quality,
formatting consistency and abuse signals (caps, emoji, punctuation,
repetition, template similarity markers).
"""

from __future__ import annotations

import re
from collections import Counter

_EMOJI = re.compile(
    r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", re.UNICODE)
_WORD = re.compile(r"[A-Za-z']+")
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")

_PROFESSIONAL_MARKERS = re.compile(
    r"\b(dear|regards|sincerely|please|kindly|reference|attached|agenda|"
    r"yours (truly|faithfully)|best regards|warm regards)\b", re.IGNORECASE)
_SLANG = re.compile(
    r"\b(hey+|yo\b|bro\b|dude|lmao|omg|plz|u r\b|gonna|wanna|lol)\b", re.IGNORECASE)


class LinguisticAnalyzer:
    """Extract style metrics; abuse flags are evidence, never verdicts."""

    def analyze(self, text: str) -> dict:
        raw = text or ""
        words = _WORD.findall(raw.lower())
        sentences = [s.strip() for s in _SENTENCE.findall(raw) if s.strip()]
        n_words = max(len(words), 1)
        n_sent = max(len(sentences), 1)
        avg_len = round(n_words / n_sent, 1)
        long_words = sum(1 for w in words if len(w) > 6)
        # Flesch-style readability proxy (syllable approx via vowel groups)
        syllables = sum(len(re.findall(r"[aeiouy]+", w)) or 1 for w in words)
        readability = round(max(0.0, min(100.0,
                                         206.835 - 1.015 * avg_len
                                         - 84.6 * (syllables / n_words))), 1)
        if avg_len <= 8:
            complexity = "Simple"
        elif avg_len <= 16:
            complexity = "Moderate"
        elif avg_len <= 25:
            complexity = "Complex"
        else:
            complexity = "Very Complex"
        letters = [c for c in raw if c.isalpha()]
        caps_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if letters else 0.0
        emoji_count = len(_EMOJI.findall(raw))
        repeated_punct = len(re.findall(r"([!?.,])\1{2,}", raw))
        counts = Counter(words)
        repeated_words = sum(1 for w, c in counts.items() if len(w) > 3 and c >= 4)
        professional = len(_PROFESSIONAL_MARKERS.findall(raw))
        slang = len(_SLANG.findall(raw))
        if professional >= 2 and slang == 0 and caps_ratio < 0.3:
            tone = "Professional"
        elif slang >= 2 or emoji_count >= 3:
            tone = "Casual"
        elif caps_ratio > 0.5 or repeated_punct >= 2:
            tone = "Aggressive"
        else:
            tone = "Neutral"
        # grammar quality heuristic: spacing/punctuation hygiene
        hygiene_issues = len(re.findall(r"\s{2,}|[a-z],[a-z]|\.[a-zA-Z]", raw))
        grammar = ("Good" if hygiene_issues <= 2 else
                   "Fair" if hygiene_issues <= 6 else "Poor")
        # formatting consistency: line-length variance + greeting/closing presence
        lines = [line for line in raw.splitlines() if line.strip()]
        greeting = bool(lines and re.match(r"(?i)^(dear|hello|hi|respected|greetings)", lines[0]))
        closing = bool(lines and re.search(r"(?i)(regards|sincerely|thank you|best|warm regards)", lines[-1]))
        formatting = ("Consistent" if greeting and closing else
                      "Partial" if greeting or closing else "Inconsistent")
        abuse = []
        if caps_ratio > 0.5 and len(letters) > 15:
            abuse.append(f"capitalization abuse ({caps_ratio:.0%} caps)")
        if emoji_count >= 3:
            abuse.append(f"emoji abuse ({emoji_count})")
        if repeated_punct:
            abuse.append(f"repeated punctuation ({repeated_punct})")
        if repeated_words:
            abuse.append(f"repeated words ({repeated_words})")
        # template similarity: generic placeholders suggest mass templates
        template_markers = len(re.findall(
            r"\{(name|amount|link|date)\}|<.*?>|\[.*?(click|link|here).*?\]",
            raw, re.IGNORECASE))
        if template_markers:
            abuse.append(f"template markers ({template_markers})")
        return {"sentence_complexity": complexity, "avg_sentence_length": avg_len,
                "readability": readability, "professional_tone": tone,
                "grammar_quality": grammar, "formatting": formatting,
                "capitalization_ratio": round(caps_ratio, 3),
                "emoji_count": emoji_count, "abuse_signals": abuse,
                "word_count": len(words), "sentence_count": len(sentences)}
