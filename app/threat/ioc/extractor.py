from __future__ import annotations

import re
import string
from typing import Dict, List, Optional, Set, Tuple

from .providers.threat_indicator import ThreatIndicator, IOCType


class IOCExtractor:
    """Extracts Indicators of Compromise from text messages."""
    
    # URL patterns
    URL_PATTERN = re.compile(
        r'(?:(?:https?|ftp)://)'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)?', re.IGNORECASE)
    
    # Domain patterns (without protocol)
    DOMAIN_PATTERN = re.compile(
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?', re.IGNORECASE)
    
    # IP address patterns
    IPV4_PATTERN = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
    IPV6_PATTERN = re.compile(r'\b([0-9a-fA-F:]*:[0-9a-fA-F:]*)\b')
    
    # Email pattern
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    
    # Cryptocurrency wallet pattern (basic)
    CRYPTO_WALLET_PATTERN = re.compile(
        r'[123456789khmj][a-zA-Z0-9]{25,39}|0x[a-fA-F0-9]{40}')
    
    # Phone pattern (basic international)
    PHONE_PATTERN = re.compile(r'\+\d{1,3}[\s\-]?\d{1,14}')
    
    # URL shortener patterns
    URL_SHORTENERS = {'bit.ly', 'goo.gl', 't.co', 'ow.ly', 're brand.ly', 'tinyurl.com', 'is.gd'}
    
    def __init__(self):
        self._extracted: Dict[IOCType, List[str]] = {
            IOCType.URL: [],
            IOCType.DOMAIN: [],
            IOCType.IP: [],
            IOCType.EMAIL: [],
            IOCType.CRYPTO_WALLET: [],
            IOCType.PHONE: [],
        }
    
    def extract(self, text: str) -> Dict[IOCType, List[str]]:
        """Extract all IOCs from the given text."""
        self._extracted = {
            IOCType.URL: [],
            IOCType.DOMAIN: [],
            IOCType.IP: [],
            IOCType.EMAIL: [],
            IOCType.CRYPTO_WALLET: [],
            IOCType.PHONE: [],
        }
        
        # Extract URLs
        urls = self._extract_urls(text)
        self._extracted[IOCType.URL] = urls
        
        # Extract domains from URLs and directly
        domains = set()
        for url in urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    domains.add(parsed.netloc.lower())
            except Exception:
                pass
        direct_domains = self._extract_domains(text)
        domains.update(direct_domains)
        self._extracted[IOCType.DOMAIN] = list(domains)
        
        # Extract IPs
        ips = set()
        for match in self.IPV4_PATTERN.finditer(text):
            ips.add(match.group(1))
        for match in self.IPV6_PATTERN.finditer(text):
            ips.add(match.group(1))
        self._extracted[IOCType.IP] = list(ips)
        
        # Extract emails
        emails = self.EMAIL_PATTERN.findall(text)
        self._extracted[IOCType.EMAIL] = emails
        
        # Extract crypto wallets
        crypto = self.CRYPTO_WALLET_PATTERN.findall(text)
        self._extracted[IOCType.CRYPTO_WALLET] = crypto
        
        # Extract phones
        phones = self.PHONE_PATTERN.findall(text)
        self._extracted[IOCType.PHONE] = phones
        
        return self._extracted
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        matches = self.URL_PATTERN.finditer(text)
        urls = [match.group(0) for match in matches]
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for url in urls:
            if url.lower() not in seen:
                seen.add(url.lower())
                unique.append(url)
        return unique
    
    def _extract_domains(self, text: str) -> List[str]:
        """Extract domains from text (without protocol)."""
        matches = self.DOMAIN_PATTERN.finditer(text)
        domains = [match.group(0).lower() for match in matches]
        # Deduplicate
        seen = set()
        unique = []
        for domain in domains:
            if domain not in seen:
                seen.add(domain)
                unique.append(domain)
        return unique
    
    def get_counts(self) -> Dict[str, int]:
        """Get count of each IOC type."""
        return {ioctype.value: len(iocs) for ioctype, iocls in self._extracted.items() for iocs in [iocls]}
    
    def clear(self) -> None:
        """Clear all extracted IOCs."""
        self._extracted = {
            IOCType.URL: [],
            IOCType.DOMAIN: [],
            IOCType.IP: [],
            IOCType.EMAIL: [],
            IOCType.CRYPTO_WALLET: [],
            IOCType.PHONE: [],
        }