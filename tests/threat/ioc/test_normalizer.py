from app.threat.ioc.normalizer import Normalizer
from app.threat.ioc.models import IOCType

def test_normalize_url():
    v = Normalizer.normalize("HTTPS://Google.COM//path/", IOCType.URL)
    assert v == "https://google.com/path"

def test_normalize_domain():
    v = Normalizer.normalize("Example.COM.", IOCType.DOMAIN)
    assert v == "example.com"

def test_normalize_email():
    v = Normalizer.normalize("Test@Example.COM", IOCType.EMAIL)
    assert v == "test@example.com"

def test_normalize_phone():
    v = Normalizer.normalize("+1 (555) 123-4567", IOCType.PHONE)
    assert v == "+15551234567"

def test_remove_trailing_punct():
    v = Normalizer.normalize("https://example.com.", IOCType.URL)
    assert v.endswith("https://example.com")
