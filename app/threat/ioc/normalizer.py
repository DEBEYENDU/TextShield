from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from .models import IOCType


class Normalizer:
    TRAILING_PUNCT = ".,;:!?)]}\"'`"

    @staticmethod
    def normalize(value: str, ioc_type: IOCType) -> str:
        if not value:
            return value
        v = value.strip()
        # Remove trailing punctuation
        v = v.rstrip(Normalizer.TRAILING_PUNCT)
        v = v.lstrip("(")
        # Unicode safe: keep as is, lower for case-insensitive types
        if ioc_type in (IOCType.URL, IOCType.DOMAIN, IOCType.EMAIL):
            v = v.lower()
        if ioc_type == IOCType.URL:
            return Normalizer._normalize_url(v)
        if ioc_type == IOCType.DOMAIN:
            return Normalizer._normalize_domain(v)
        if ioc_type == IOCType.EMAIL:
            return Normalizer._normalize_email(v)
        if ioc_type in (IOCType.IPV4, IOCType.IPV6, IOCType.IP):
            return v
        if ioc_type == IOCType.PHONE:
            return Normalizer._normalize_phone(v)
        return v

    @staticmethod
    def _normalize_url(url: str) -> str:
        # Add scheme if missing
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
            url = 'http://' + url
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            # Remove duplicate slashes in path
            path = re.sub(r'/+', '/', parsed.path)
            # Rebuild
            normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
            # Remove trailing slash if not root
            if normalized.endswith('/') and len(normalized) > len(scheme) + 3:
                normalized = normalized.rstrip('/')
            return normalized
        except Exception:
            return url.lower()

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        domain = domain.lower()
        domain = domain.rstrip('.')
        # Remove port if present
        domain = domain.split(':')[0]
        return domain

    @staticmethod
    def _normalize_email(email: str) -> str:
        # Canonicalize: trim, lower
        local, _, domain = email.partition('@')
        # Keep local as is but lower for consistency
        return f"{local.lower()}@{domain.lower()}"

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        # Keep + and digits
        digits = re.sub(r'[^\d+]', '', phone)
        # Ensure single leading +
        if digits.startswith('+'):
            digits = '+' + re.sub(r'\D', '', digits[1:])
        else:
            digits = re.sub(r'\D', '', digits)
        return digits
