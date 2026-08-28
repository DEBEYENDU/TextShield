# IOC Extraction Engine

## Architecture
- `models.py`: IOCType enum, ExtractedIOC dataclass
- `base.py`: BaseExtractor interface
- `registry.py`: ExtractorRegistry for pluggable extractors
- `normalizer.py`: Normalization rules
- `validator.py`: Validation logic
- `engine.py`: Orchestrates extraction, normalization, validation, deduplication
- `extractors/`: URL, Domain, IP, Email, Phone, Short URL

## Supported IOC Types
- URL
- Domain
- IPv4 / IPv6
- Email
- Phone
- URL Shortener

## Normalization Rules
- Lowercase URLs/domains/emails
- Remove trailing punctuation
- Canonicalize scheme
- Remove duplicate slashes
- Phone digits only with leading +

## Validation Rules
- URL syntax via urllib.parse
- IP via ipaddress module
- Email regex
- Domain regex
- Phone length check

## Examples
```python
from app.threat.ioc.engine import IOCEngine
engine = IOCEngine()
iocs = engine.extract("Visit https://Example.COM and email me@test.com")
```

## Extension Guide
Create a new extractor subclassing `BaseExtractor`, implement `name`, `ioc_type`, `supports`, `extract`. Register via `registry.register(extractor)`.
