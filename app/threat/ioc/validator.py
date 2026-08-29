from __future__ import annotations

import re
import ipaddress

from .models import IOCType


class Validator:
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
    DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
    URL_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s<>"\']+$')
    PHONE_REGEX = re.compile(r'^\+?\d{7,15}$')

    @staticmethod
    def validate(value: str, ioc_type: IOCType) -> bool:
        if ioc_type == IOCType.URL:
            return Validator._validate_url(value)
        if ioc_type in (IOCType.DOMAIN,):
            return Validator._validate_domain(value)
        if ioc_type in (IOCType.IPV4, IOCType.IPV6, IOCType.IP):
            return Validator._validate_ip(value)
        if ioc_type == IOCType.EMAIL:
            return Validator._validate_email(value)
        if ioc_type == IOCType.PHONE:
            return Validator._validate_phone(value)
        if ioc_type == IOCType.URL_SHORTENER:
            return Validator._validate_url(value)
        return True

    @staticmethod
    def _validate_url(url: str) -> bool:
        try:
            if not Validator.URL_REGEX.match(url):
                return False
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def _validate_domain(domain: str) -> bool:
        try:
            return bool(Validator.DOMAIN_REGEX.match(domain))
        except Exception:
            return False

    @staticmethod
    def _validate_ip(ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_email(email: str) -> bool:
        try:
            return bool(Validator.EMAIL_REGEX.match(email))
        except Exception:
            return False

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        # Normalize to digits only
        digits = re.sub(r'\D', '', phone)
        if phone.startswith('+'):
            digits = '+' + digits.lstrip('+')
        return bool(Validator.PHONE_REGEX.match(digits))
