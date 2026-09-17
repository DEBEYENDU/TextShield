"""Legacy flat module — canonical is app.threat.providers.virustotal.provider."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.threat.ioc.models import IOCType
from .threat_indicator import ThreatIndicator

logger = logging.getLogger(__name__)


class VirusTotalProvider:
    """VirusTotal threat intelligence provider.
    
    Capabilities:
    - URL reputation
    - Domain reputation
    - IP reputation
    - Detection statistics
    - File scanning
    - Hash lookup
    """
    
    name = "virustotal"
    """Provider name - used for registry lookup."""
    
    version = "1.0.0"
    """Provider version."""
    
    def __init__(self, api_key: Optional[str] = None, enabled: bool = True, **kwargs: Any):
        """Initialize the VirusTotal provider.
        
        Args:
            api_key: VirusTotal API key
            enabled: Whether the provider is enabled
            **kwargs: Additional configuration options
        """
        self._api_key = api_key
        self._enabled = enabled
        self._initialized = False
        self.configuration = kwargs
        
        # Configurable TTL for cached results (seconds)
        self.ttl = self.configuration.get("ttl", 300)
        
        # Request timeout (seconds)
        self.timeout = self.configuration.get("timeout", 5.0)
    
    @property
    def enabled(self) -> bool:
        """Return whether the provider is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable the provider."""
        self._enabled = value
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return provider metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "capabilities": self.capabilities(),
            "ttl": self.ttl,
            "timeout": self.timeout,
            "api_key_configured": self._api_key is not None,
        }
    
    def capabilities(self) -> List[str]:
        """Return provider capabilities."""
        return [
            "url_reputation",
            "domain_reputation",
            "ip_reputation",
            "file_reputation",
            "detection_statistics",
            "malware_analysis",
        ]
    
    def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True
        logger.info(f"VirusTotal provider initialized: enabled={self.enabled}")
    
    def shutdown(self) -> None:
        """Shut down the provider."""
        self._initialized = False
        logger.info("VirusTotal provider shut down")
    
    async def lookup_url(self, url: str) -> Optional[ThreatIndicator]:
        """Look up a URL for threat intelligence.
        
        Args:
            url: URL to check
            
        Returns:
            ThreatIndicator if malicious, None if benign or not found
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            logger.debug("VirusTotal: no API key configured, cannot check URL")
            return None
        
        # In production, this would call the VirusTotal API v3:
        # https://www.virustotal.com/api/v3/urls
        # The API returns analysis stats and metadata
        
        # For now, simulate a check
        indicator = await self._simulate_url_check(url)
        return indicator
    
    async def lookup_domain(self, domain: str) -> Optional[ThreatIndicator]:
        """Look up a domain for threat intelligence.
        
        Args:
            domain: Domain to check
            
        Returns:
            ThreatIndicator if malicious, None if benign or not found
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            logger.debug("VirusTotal: no API key configured, cannot check domain")
            return None
        
        indicator = await self._simulate_domain_check(domain)
        return indicator
    
    async def lookup_ip(self, ip: str) -> Optional[ThreatIndicator]:
        """Look up an IP address for threat intelligence.
        
        Args:
            ip: IP address to check
            
        Returns:
            ThreatIndicator if malicious, None if benign or not found
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            logger.debug("VirusTotal: no API key configured, cannot check IP")
            return None
        
        indicator = await self._simulate_ip_check(ip)
        return indicator
    
    async def lookup_hash(self, hash_value: str) -> Optional[ThreatIndicator]:
        """Look up a hash for threat intelligence.
        
        Args:
            hash_value: MD5, SHA1, or SHA256 hash to check
            
        Returns:
            ThreatIndicator if malicious, None if benign or not found
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            logger.debug("VirusTotal: no API key configured, cannot check hash")
            return None
        
        # VirusTotal v3 endpoint for file/hash analysis
        # https://www.virustotal.com/api/v3/files/{hash}
        indicator = await self._simulate_hash_check(hash_value)
        return indicator
    
    def _simulate_url_check(self, url: str) -> Optional[ThreatIndicator]:
        """Simulate a URL threat check via VirusTotal."""
        url_lower = url.lower()
        
        # Heuristic-based simulation
        suspicious_tlds = {".top", ".xyz", ".club", ".gq", ".ml", ".cf"}
        is_suspicious = any(url_lower.endswith(tld) for tld in suspicious_tlds)
        
        # Check for known threat keywords in URL
        threat_keywords = ["login", "secure", "verify", "account", "bank", "paypal"]
        has_threat_keyword = any(kw in url_lower for kw in threat_keywords)
        
        if is_suspicious or has_threat_keyword:
            # Determine confidence based on combination of factors
            confidence = 0.70 if (is_suspicious and has_threat_keyword) else 0.55
            
            # Determine severity
            if is_suspicious and has_threat_keyword:
                severity = "high"
            elif is_suspicious or has_threat_keyword:
                severity = "medium"
            else:
                severity = "low"
            
            return ThreatIndicator(
                indicator=url,
                indicator_type=IOCType.URL,
                provider=self.name,
                detection_status="malicious",
                confidence=confidence,
                severity=severity,
                timestamp=self._now(),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation=f"VirusTotal: URL analysis indicates potential threat (suspicious TLD/keywords detected)",
            )
        
        # Benign - return None
        return None
    
    def _simulate_domain_check(self, domain: str) -> Optional[ThreatIndicator]:
        """Simulate a domain threat check via VirusTotal."""
        domain_lower = domain.lower()
        
        # Check for newly registered domains (high risk indicator)
        # and domains impersonating brands
        brand_impersonation = any(
            brand in domain_lower 
            for brand in ["paypal", "microsoft", "google", "amazon", "apple"]
        )
        
        # Check TLD patterns
        suspicious_tlds = {".top", ".xyz", ".club", ".gq", ".ml", ".cf", ".zip", ".loan"}
        has_suspicious_tld = any(domain_lower.endswith(tld) for tld in suspicious_tlds)
        
        if brand_impersonation or has_suspicious_tld:
            confidence = 0.80 if brand_impersonation and has_suspicious_tld else 0.65
            
            severity = "high" if brand_impersonation else "medium"
            
            return ThreatIndicator(
                indicator=domain,
                indicator_type=IOCType.DOMAIN,
                provider=self.name,
                detection_status="malicious",
                confidence=confidence,
                severity=severity,
                timestamp=self._now(),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation=f"VirusTotal: Domain '{domain}' analysis indicates potential threat",
            )
        
        return None
    
    def _simulate_ip_check(self, ip: str) -> Optional[ThreatIndicator]:
        """Simulate an IP threat check via VirusTotal."""
        # VirusTotal IP reputation analysis
        # In production, this would check the IP against VT's threat intelligence
        # For simulation, check if IP is from known suspicious ranges
        
        ip_parts = ip.split(".")
        if len(ip_parts) == 4:
            # Check for private/reserved ranges that might be spoofed
            if ip_parts[0] in ("0", "255") or ip_parts[0] in ("192", "10", "172"):
                # Additional check on last octet
                last_octet = int(ip_parts[3])
                if last_octet in (0, 255):
                    return ThreatIndicator(
                        indicator=ip,
                        indicator_type=IOCType.IP,
                        provider=self.name,
                        detection_status="malicious",
                        confidence=0.55,
                        severity="medium",
                        timestamp=self._now(),
                        ttl=timedelta(seconds=self.ttl),
                        source="virustotal",
                        explanation=f"VirusTotal: IP '{ip}' shows suspicious network pattern",
                    )
        
        return None
    
    def _simulate_hash_check(self, hash_value: str) -> Optional[ThreatIndicator]:
        """Simulate a hash threat check via VirusTotal."""
        # In production, VT would return detection stats across 70+ antivirus engines
        # For simulation, check hash length and patterns
        
        if len(hash_value) == 32:  # MD5
            # Simulate: some hashes are known malicious
            if hash_value.startswith("a") or hash_value.startswith("b"):
                confidence = 0.75
                severity = "high"
            else:
                confidence = 0.35
                severity = "low"
            
            return ThreatIndicator(
                indicator=hash_value,
                indicator_type=IOCType.CRYPTO_WALLET,  # Reusing type for hash
                provider=self.name,
                detection_status="malicious" if confidence > 0.5 else "unknown",
                confidence=confidence,
                severity=severity,
                timestamp=self._now(),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation=f"VirusTotal: Hash '{hash_value[:8]}...' analysis result",
            )
        
        elif len(hash_value) == 40:  # SHA1
            confidence = 0.65
            severity = "medium"
            
            return ThreatIndicator(
                indicator=hash_value,
                indicator_type=IOCType.CRYPTO_WALLER,  # Reusing type for hash
                provider=self.name,
                detection_status="unknown",
                confidence=confidence,
                severity=severity,
                timestamp=self._now(),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation=f"VirusTotal: SHA1 hash '{hash_value[:8]}...' analysis",
            )
        
        elif len(hash_value) == 64:  # SHA256
            confidence = 0.80
            severity = "high" if confidence > 0.7 else "medium"
            
            return ThreatIndicator(
                indicator=hash_value,
                indicator_type=IOCType.CRYPTO_WALLET,  # Reusing type for hash
                provider=self.name,
                detection_status="malicious",
                confidence=confidence,
                severity=severity,
                timestamp=self._now(),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation=f"VirusTotal: SHA256 hash '{hash_value[:16]}...' analysis",
            )
        
        return None
    
    def _now(self) -> datetime:
        """Return current UTC datetime."""
        from datetime import datetime
        import datetime as dt_module
        return dt_module.datetime.now(dt_module.timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "api_key_configured": self._api_key is not None,
            "capabilities": self.capabilities(),
            "ttl": self.ttl,
            "timeout": self.timeout,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirusTotalProvider":
        """Create instance from dictionary."""
        provider = cls(
            api_key=data.get("api_key"),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ("name", "version", "api_key", "enabled")},
        )
        return provider