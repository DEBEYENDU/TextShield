from app.threat.cache.models import CacheRecord
from app.threat.cache.serializer import CacheSerializer

def test_json_roundtrip():
    recs = [CacheRecord(ioc_type="url", normalized_value="https://x.com")]
    s = CacheSerializer.to_json(recs)
    back = CacheSerializer.from_json(s)
    assert len(back) == 1
    assert back[0].normalized_value == "https://x.com"
