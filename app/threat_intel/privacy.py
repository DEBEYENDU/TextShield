"""Privacy policy for external threat-intel sharing.

Rules: only the IOC itself (URL/domain/hash/IP) may leave the system —
never the full message, email body or conversation. Emails/phones hash
before sharing unless explicitly allowed; unknown IOC types are blocked.
"""

from __future__ import annotations

import hashlib

from app.threat_intel.exceptions import PrivacyViolationError
from app.threat_intel.models import IOC

# IOC types safe to share verbatim with external providers.
_SHAREABLE_VERBATIM = {"url", "domain", "ipv4", "ipv6", "md5", "sha1",
                       "sha256"}
# Types shared only as irreversible hashes.
_SHAREABLE_HASHED = {"email", "phone"}


class PrivacyPolicy:
    """Gatekeeper between IOCs and external providers."""

    def __init__(self, allow_external: bool = True,
                 allow_pii_hashes: bool = True):
        self.allow_external = allow_external
        self.allow_pii_hashes = allow_pii_hashes
        self.blocked_count = 0

    def shareable_value(self, ioc: IOC) -> str:
        """Return the external-safe representation, or raise."""
        if not self.allow_external:
            self.blocked_count += 1
            raise PrivacyViolationError("external lookups disabled")
        if ioc.ioc_type in _SHAREABLE_VERBATIM:
            return ioc.normalized_value
        if ioc.ioc_type in _SHAREABLE_HASHED:
            if not self.allow_pii_hashes:
                self.blocked_count += 1
                raise PrivacyViolationError(
                    f"{ioc.ioc_type} sharing disabled by policy")
            digest = hashlib.sha256(
                ioc.normalized_value.lower().encode()).hexdigest()
            return f"{ioc.ioc_type}-hash:{digest[:32]}"
        self.blocked_count += 1
        raise PrivacyViolationError(
            f"ioc type '{ioc.ioc_type}' is never shared externally")

    def check(self, ioc: IOC) -> bool:
        try:
            self.shareable_value(ioc)
            return True
        except PrivacyViolationError:
            return False

    def stats(self) -> dict:
        return {"allow_external": self.allow_external,
                "blocked_count": self.blocked_count}
