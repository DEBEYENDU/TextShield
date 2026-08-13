"""Tests for the utils package."""
from __future__ import annotations

import os

import pytest

from app.utils.date_utils import parse_iso, utc_now_iso, utc_now_ms
from app.utils.file_utils import ensure_dir, is_within, read_json, write_json
from app.utils.response import error, success
from app.utils.text_utils import mask_secret, sha256, slugify, truncate
from app.utils.validation import ensure_length, has_content, is_within_bounds


class TestFileUtils:
    def test_ensure_dir_creates(self, tmp_path):
        target = tmp_path / "a" / "b"
        result = ensure_dir(target)
        assert result == target and target.exists()

    def test_write_read_json_roundtrip(self, tmp_path):
        path = tmp_path / "payload.json"
        assert write_json(path, {"a": 1}) is True
        assert read_json(path) == {"a": 1}

    def test_read_json_missing_returns_default(self, tmp_path):
        assert read_json(tmp_path / "nope.json", default=[]) == []

    def test_read_json_corrupt_returns_default(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        assert read_json(path, default=None) is None

    def test_is_within(self, tmp_path):
        assert is_within(tmp_path, tmp_path / "x" / "y")
        assert not is_within(tmp_path, tmp_path.parent)


class TestTextUtils:
    def test_sha256_deterministic(self):
        assert sha256("abc") == sha256("abc")
        assert len(sha256("abc")) == 64

    def test_truncate(self):
        assert truncate("hello world", 20) == "hello world"
        result = truncate("a " * 50, 10)
        assert result.endswith("...") and len(result) <= 10

    def test_mask_secret(self):
        assert mask_secret("supersecret123") == "*" * 10 + "t123"
        assert mask_secret("") == ""
        assert mask_secret(None) == ""

    def test_slugify(self):
        assert slugify("Risk Level - HIGH/1") == "risk_level_high_1"


class TestValidation:
    def test_ensure_length(self):
        assert ensure_length(None, 5)
        assert ensure_length("abc", 5)
        assert not ensure_length("abcdef", 5)

    def test_has_content(self):
        assert has_content("", "  x  ")
        assert not has_content("", "  ", None)

    def test_is_within_bounds(self):
        assert is_within_bounds(0.5, 0.0, 1.0)
        assert not is_within_bounds(1.5, 0.0, 1.0)


class TestResponse:
    def test_success(self):
        payload = success({"x": 1}, message="ok")
        assert payload["success"] is True and payload["data"] == {"x": 1}

    def test_error(self):
        payload = error("boom", code="db_error")
        assert payload["success"] is False
        assert payload["error"]["code"] == "db_error"


class TestDateUtils:
    def test_utc_now_iso(self):
        stamp = utc_now_iso()
        assert "+00:00" in stamp or stamp.endswith("Z") or "UTC" in stamp

    def test_parse_iso_roundtrip(self):
        stamp = utc_now_iso()
        parsed = parse_iso(stamp)
        assert parsed is not None
        assert parse_iso("not-a-date") is None

    def test_utc_now_ms(self):
        assert isinstance(utc_now_ms(), int)
