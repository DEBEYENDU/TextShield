from app.threat.ioc.engine import IOCEngine

def test_engine_extract():
    engine = IOCEngine()
    text = "Visit https://example.com and email test@example.com, IP 1.2.3.4"
    iocs = engine.extract(text)
    types = {ioc.type.value for ioc in iocs}
    assert "url" in types
    assert "email" in types
    assert "ipv4" in types

def test_engine_deduplication():
    engine = IOCEngine()
    text = "https://example.com https://example.com"
    iocs = engine.extract(text)
    urls = [i for i in iocs if i.type.value == "url"]
    assert len(urls) == 1
    assert urls[0].occurrence_count == 2

def test_engine_validate():
    engine = IOCEngine()
    from app.threat.ioc.models import IOCType
    res = engine.validate_ioc("https://example.com", IOCType.URL)
    assert res["valid"] is True
    res2 = engine.validate_ioc("not url", IOCType.URL)
    assert res2["valid"] is False
