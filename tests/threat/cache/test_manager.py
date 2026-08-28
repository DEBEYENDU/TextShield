from app.threat.cache.manager import CacheManager
from app.threat.cache.models import CacheRecord

def test_create_read():
    mgr = CacheManager(max_size=10)
    rec = CacheRecord(ioc_type="url", normalized_value="https://example.com", provider_name="test")
    created = mgr.create(rec)
    fetched = mgr.read(created.cache_id)
    assert fetched is not None
    assert fetched.normalized_value == "https://example.com"

def test_lookup_by_ioc():
    mgr = CacheManager()
    rec = CacheRecord(ioc_type="url", normalized_value="https://a.com")
    mgr.create(rec)
    res = mgr.lookup_by_ioc("url", "https://a.com")
    assert len(res) == 1

def test_delete():
    mgr = CacheManager()
    rec = CacheRecord(ioc_type="url", normalized_value="https://b.com")
    created = mgr.create(rec)
    ok = mgr.delete(created.cache_id)
    assert ok is True
    assert mgr.read(created.cache_id) is None

def test_statistics():
    mgr = CacheManager()
    mgr.create(CacheRecord(ioc_type="url", normalized_value="https://c.com"))
    stats = mgr.get_statistics()
    assert stats["cache_size"] >= 1
