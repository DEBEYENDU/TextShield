"""Entity & Context Knowledge Graph (v4.0 / RFC-003).

Models entities (people, organizations, domains, URLs, banks, agencies,
campaigns, ...) and their relationships so TextShield reasons with context
instead of isolated words. Integrates with the understanding pipeline
(RFC-001), trust & threat scoring (RFC-002), RAG retrieval and LLM prompts.

Nothing here classifies: the graph produces contextual evidence only.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-003"

ENTITY_TYPES = [
    "PERSON", "ORGANIZATION", "BANK", "COLLEGE", "UNIVERSITY", "COMPANY",
    "GOVERNMENT", "WEBSITE", "DOMAIN", "URL", "EMAIL", "PHONE",
    "SOCIAL_MEDIA", "EVENT", "JOB_ROLE", "TECHNOLOGY", "MALWARE",
    "CAMPAIGN", "ATTACK_PATTERN", "SCAM", "PAYMENT_PLATFORM",
]

RELATIONSHIPS = [
    "WORKS_FOR", "PART_OF", "HOSTED_BY", "USES", "LINKS_TO", "MENTIONS",
    "TARGETS", "IMPERSONATES", "BELONGS_TO", "ASSOCIATED_WITH", "LOCATED_IN",
    "REGISTERED_TO", "REFERRED_BY", "ATTACKS", "DEFENDS", "REPORTS",
    "PUBLISHED_BY",
]

# Understanding-pipeline entity group -> graph entity type.
GROUP_TO_TYPE = {
    "people": "PERSON",
    "organizations": "ORGANIZATION",
    "banks": "BANK",
    "government_departments": "GOVERNMENT",
    "companies": "COMPANY",
    "websites": "WEBSITE",
    "domains": "DOMAIN",
    "urls": "URL",
    "email_addresses": "EMAIL",
    "phone_numbers": "PHONE",
    "universities": "UNIVERSITY",
    "recruiters": "PERSON",
    "job_titles": "JOB_ROLE",
    "package_values": "TECHNOLOGY",
    "money": "PAYMENT_PLATFORM",
    "dates": "EVENT",
    "times": "EVENT",
    "locations": "ORGANIZATION",
}
