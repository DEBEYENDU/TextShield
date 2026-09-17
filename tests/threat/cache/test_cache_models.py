from app.threat.cache.models import CacheRecord
from datetime import datetime, timezone, timedelta

def test_cache_record_expiration():
    rec = CacheRecord(ttl=1)
    rec.expiration_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    assert rec.is_expired() is True

def test_to_dict():
    rec = CacheRecord(ioc_type="url", normalized_value="https://example.com")
    d = rec.to_dict()
    assert d["ioc_type"] == "url"
    assert d["normalized_value"] == "https://example.com"
