from app.threat.ioc.extractors.url import URLExtractor
from app.threat.ioc.extractors.domain import DomainExtractor
from app.threat.ioc.extractors.ip import IPExtractor
from app.threat.ioc.extractors.email import EmailExtractor
from app.threat.ioc.extractors.phone import PhoneExtractor

def test_url_extractor():
    ext = URLExtractor()
    text = "Visit https://Example.COM/path, it's great."
    iocs = ext.extract(text)
    assert len(iocs) == 1
    assert iocs[0].normalized_value == "https://example.com/path"
    assert iocs[0].type.value == "url"

def test_domain_extractor():
    ext = DomainExtractor()
    text = "Go to example.com now."
    iocs = ext.extract(text)
    assert len(iocs) >= 1
    assert any(ioc.normalized_value == "example.com" for ioc in iocs)

def test_ip_extractor():
    ext = IPExtractor()
    text = "IP 192.168.1.1 is internal"
    iocs = ext.extract(text)
    assert len(iocs) >= 1
    assert any(ioc.normalized_value == "192.168.1.1" for ioc in iocs)

def test_email_extractor():
    ext = EmailExtractor()
    text = "Contact test@example.com"
    iocs = ext.extract(text)
    assert len(iocs) == 1
    assert iocs[0].normalized_value == "test@example.com"

def test_phone_extractor():
    ext = PhoneExtractor()
    text = "Call +1 555 123 4567"
    iocs = ext.extract(text)
    assert len(iocs) == 1
    assert iocs[0].normalized_value == "+15551234567"
