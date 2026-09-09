"""Entity extraction over the RFC-001 taxonomy.

Reuses the battle-tested SemanticPipeline extractors (emails, urls, phones,
money, dates, times, accounts, tracking, organizations, people, locations)
and adds RFC-specific structure: banks, government departments, companies,
websites/domains, job titles, universities, recruiters, package values.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.semantic.semantic_pipeline import SemanticPipeline

_JOB_TITLE_RE = re.compile(
    r"\b(?:software engineer|data analyst|hr manager|accountant|sales executive|"
    r"customer support|delivery boy|driver|teacher|nurse|doctor|manager|analyst|"
    r"developer|designer|consultant|officer|clerk|assistant|supervisor|technician|"
    r"intern|trainee|executive|associate|specialist|coordinator)\b",
    re.IGNORECASE,
)
_UNIVERSITY_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z&.'-]*(?:\s+[A-Z][A-Za-z&.'-]*){0,4}\s+"
    r"(?:University|College|Institute of [A-Za-z ]+|IIT|NIT|IIM|School of [A-Za-z ]+))\b"
)
_GOVT_DEPT_RE = re.compile(
    r"\b(?:Ministry of [A-Za-z ]+|Department of [A-Za-z ]+|Municipal Corporation|"
    r"Income Tax Department|Passport Office|RTO|Election Commission|Police |"
    r"Cyber Crime Cell|Revenue Department|GST|CBDT|EPFO|UIDAI)\b",
    re.IGNORECASE,
)
_RECRUITER_RE = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s*\|\s*)?(?:HR|Recruiter|Talent Acquisition|"
    r"Hiring Manager)(?:\s*\|\s*[A-Z][A-Za-z&., ]+)?\b"
)

_pipeline: SemanticPipeline | None = None


def _pipeline_instance() -> SemanticPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = SemanticPipeline()
    return _pipeline


class EntityExtractor:
    """Extract structured entities; store grouped by RFC category."""

    def extract(self, text: str, sender: str = "") -> dict:
        text = text or ""
        try:
            raw = _pipeline_instance().extract_entities(text, sender=sender)
        except Exception:
            raw = []
        grouped: dict[str, list] = {
            "organizations": [], "people": [], "banks": [],
            "government_departments": [], "companies": [], "websites": [],
            "domains": [], "urls": [], "phone_numbers": [], "email_addresses": [],
            "money": [], "dates": [], "times": [], "package_values": [],
            "locations": [], "job_titles": [], "universities": [],
            "recruiters": [],
        }
        seen: set[tuple[str, str]] = set()

        def add(category: str, value: str, confidence: float = 0.8):
            value = (value or "").strip()
            if not value or (category, value.lower()) in seen:
                return
            seen.add((category, value.lower()))
            grouped[category].append({"value": value, "confidence": confidence})

        for entity in raw:
            etype = getattr(entity, "type", "")
            value = getattr(entity, "value", "")
            conf = float(getattr(entity, "confidence", 0.7) or 0.7)
            if etype == "email":
                add("email_addresses", value, conf)
            elif etype == "url":
                add("urls", value, conf)
                try:
                    host = urlparse(value if "://" in value else "http://" + value).hostname or ""
                    if host:
                        add("domains", host.lower(), conf)
                        add("websites", host.lower(), conf)
                except Exception:
                    pass
            elif etype == "phone":
                add("phone_numbers", value, conf)
            elif etype == "money":
                add("money", value, conf)
            elif etype == "date":
                add("dates", value, conf)
            elif etype == "time":
                add("times", value, conf)
            elif etype == "bank":
                add("banks", value, conf)
            elif etype == "company":
                add("companies", value, conf)
            elif etype == "organization":
                add("organizations", value, conf)
            elif etype == "person":
                add("people", value, conf)
            elif etype == "location":
                add("locations", value, conf)
            elif etype in {"account_number", "tracking_number"}:
                add("package_values", value, conf)
        for match in _GOVT_DEPT_RE.finditer(text):
            add("government_departments", match.group(0).strip(), 0.8)
        for match in _UNIVERSITY_RE.finditer(text):
            candidate = match.group(0).strip()
            if len(candidate) < 80:
                add("universities", candidate, 0.75)
        for match in _JOB_TITLE_RE.finditer(text):
            add("job_titles", match.group(0).strip(), 0.7)
        for match in _RECRUITER_RE.finditer(text):
            add("recruiters", match.group(0).strip(), 0.7)
        total = sum(len(v) for v in grouped.values())
        grouped["total_count"] = total
        return grouped


entity_extractor = EntityExtractor()
