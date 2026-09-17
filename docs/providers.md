# Threat Intelligence Providers

## Provider Interface

All providers implement `app.threat_intel.provider.ThreatIntelProvider`.

Required:
- name, version
- capabilities property
- is_configured()
- lookup_url, lookup_domain, lookup_ip, lookup_hash, lookup_email

Return `ProviderResult` with verdict, confidence, categories, sources, checked_at, expires_at, provider_status.

## Built-in Providers

### mock
Deterministic offline provider for tests/demos. Always configured. Flags patterns like phish, malware, sbi-kyc-verify. Returns benign for example.com, google.com.

Capabilities: url, domain, ipv4, ipv6, md5, sha1, sha256

### static
Static URL/domain analysis without network:
- Domain age hints
- Suspicious TLD
- Punycode detection
- Typosquatting similarity
- Subdomain depth
- IP-based URLs
- URL shortening
- Credential-like paths
- Suspicious query parameters
- Encoded payload indicators

Verdicts: known_malicious / suspicious / benign / unknown

### google_safe_browsing
Adapter over `app.threat.providers.google_safe_browsing`. Requires `TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY`.

Capabilities: url, domain

When key absent → provider_status unavailable, never crashes.

### virustotal
Adapter over `app.threat.providers.virustotal`. Requires `TEXTSHIELD_VIRUSTOTAL_API_KEY`.

Capabilities: url, domain, ipv4, ipv6, md5, sha1, sha256

Rate limited: 4/min, 500/day default.

## Adding a Provider

1. Create `app/threat_intel/providers/my_provider.py`
2. Subclass `ThreatIntelProvider`, implement capabilities and lookups
3. Register via `ThreatIntelRegistry().register(MyProvider())`
4. Add config env var if needed

No provider-specific logic in core.

## Provider Health

GET /api/threat-intel/providers returns name, version, enabled, configured, capabilities.

## Failure Modes

- Missing API key → unavailable
- Network error / timeout → error result, pipeline continues
- Rate limited → skip or use cache
- Invalid response → error result

Never single point of failure.
