"""Tests for the preprocessing module."""
from __future__ import annotations

from app.ml.preprocess import (
    STOPWORDS,
    extract_emails,
    extract_phones,
    extract_urls,
    normalize_text,
    placeholder,
    tokenize,
)


def test_normalize_lowercases_and_collapses_whitespace():
    assert normalize_text("  HELLO   World  ") == "hello world"


def test_urls_replaced_with_placeholder():
    text = "Visit https://evil-site.xyz now or www.buy-now.top/free"
    normalized = normalize_text(text)
    assert "[URL]" in normalized
    assert "https://" not in normalized


def test_emails_and_phones_are_masked():
    text = "Contact support@phish.xyz or call +91 98765 43210"
    normalized = normalize_text(text)
    assert "[EMAIL]" in normalized
    assert "[PHONE]" in normalized
    assert "support@" not in normalized


def test_money_amounts_are_masked():
    text = "You won Rs.50,000 and $200 free!!"
    normalized = normalize_text(text)
    assert "[MONEY]" in normalized
    assert "50,000" not in normalized


def test_exclamations_preserved_but_capped():
    normalized = normalize_text("Hurry!!!! NOW!")
    assert normalized.count("!") < 6


def test_extract_urls():
    urls = extract_urls("See http://bit.ly/abc and https://example.com/x?q=1 foo@bar.com")
    assert len(urls) == 2
    assert urls[0] == "http://bit.ly/abc"
    assert urls[1] == "https://example.com/x?q=1"


def test_url_trailing_punctuation_stripped():
    urls = extract_urls("Click http://example.com/x.")
    assert urls == ["http://example.com/x"]


def test_extract_emails():
    emails = extract_emails("mail me at a.b_c@example.co.in or grab@x.org")
    assert "a.b_c@example.co.in" in emails


def test_extract_phones():
    phones = extract_phones("Call 91-98765-43210 or 1800 123 456 today")
    assert phones


def test_placeholder_keeps_indicator_information():
    # placeholders must survive so the classifier learns 'presence' signals
    normalized = normalize_text("WIN! FREE gift. Call 9876543210. pay Rs.499 via https://x.io")
    assert normalized == "win! free gift. call [PHONE]. pay [MONEY] via [URL]"


def test_optional_stopword_removal():
    # stop-word handling is optional and off by default
    tokens = tokenize("Hey, are we meeting at 5 PM today?")
    assert "are" in tokens and "we" in tokens
    tokens_stopped = tokenize("Hey, are we meeting at 5 PM today?", remove_stopwords=True)
    assert "are" not in tokens_stopped and "we" not in tokens_stopped
    assert "meeting" in tokens_stopped
    assert STOPWORDS  # the optional set is non-empty