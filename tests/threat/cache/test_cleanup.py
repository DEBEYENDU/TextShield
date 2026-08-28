from app.threat.cache.manager import CacheManager
from app.threat.cache.models import CacheRecord
from app.threat.cache.cleanup import CacheCleanup
from datetime import datetime, timezone, timedelta

def test_remove_expired():
    mgr = CacheManager()
    rec = CacheRecord(ioc_type="url", normalized_value="https://old.com")
    created = mgr.create(rec)
    # force expire
    created.expiration_time = datetime.now(timezone.utc) - timedelta(seconds=1)
    cleanup = CacheCleanup(mgr)
    removed = cleanup.remove_expired()
    assert removed >= 1
