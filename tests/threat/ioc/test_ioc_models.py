import pytest
from app.threat.ioc.models import IOCType, ExtractedIOC, ValidationStatus

def test_ioc_type_values():
    assert IOCType.URL.value == "url"
    assert IOCType.DOMAIN.value == "domain"
    assert IOCType.IPV4.value == "ipv4"

def test_extracted_ioc_to_dict():
    ioc = ExtractedIOC(
        type=IOCType.URL,
        original_value="HTTPS://Google.COM",
        normalized_value="https://google.com",
        confidence=0.9,
        validation_status=ValidationStatus.VALID,
        extractor_name="url_extractor"
    )
    d = ioc.to_dict()
    assert d["type"] == "url"
    assert d["original_value"] == "HTTPS://Google.COM"
    assert d["normalized_value"] == "https://google.com"
    assert d["confidence"] == 0.9

def test_extracted_ioc_from_dict():
    data = {
        "type": "email",
        "original_value": "test@example.com",
        "normalized_value": "test@example.com",
        "confidence": 0.8,
        "validation_status": "valid",
        "extractor_name": "email_extractor"
    }
    ioc = ExtractedIOC.from_dict(data)
    assert ioc.type == IOCType.EMAIL
    assert ioc.original_value == "test@example.com"
