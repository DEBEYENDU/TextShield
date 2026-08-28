from app.threat.ioc.validator import Validator
from app.threat.ioc.models import IOCType

def test_validate_url():
    assert Validator.validate("https://example.com", IOCType.URL) is True
    assert Validator.validate("not a url", IOCType.URL) is False

def test_validate_ip():
    assert Validator.validate("192.168.1.1", IOCType.IPV4) is True
    assert Validator.validate("999.999.999.999", IOCType.IPV4) is False

def test_validate_email():
    assert Validator.validate("test@example.com", IOCType.EMAIL) is True
    assert Validator.validate("bad@", IOCType.EMAIL) is False

def test_validate_domain():
    assert Validator.validate("example.com", IOCType.DOMAIN) is True
    assert Validator.validate("-bad.com", IOCType.DOMAIN) is False

def test_validate_phone():
    assert Validator.validate("+15551234567", IOCType.PHONE) is True
    assert Validator.validate("123", IOCType.PHONE) is False
