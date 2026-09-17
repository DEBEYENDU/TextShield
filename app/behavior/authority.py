"""Social-engineering persona detection (15 impersonation roles).

Identifies WHO the sender claims to be (CEO, bank rep, courier executive,
…). A claimed persona is context — legitimacy is decided downstream by
combining persona with trust/threat evidence, never here.
"""

from __future__ import annotations

import re

# persona -> [(phrase, weight)]
_PERSONA_PHRASES: dict[str, list[tuple[str, float]]] = {
    "CEO Fraud": [
        ("this is the ceo", 1.7), ("managing director", 1.2),
        ("on behalf of the ceo", 1.6), ("board has decided", 1.2),
        ("confidential acquisition", 1.5), ("keep this between us", 1.3),
        ("i am in a meeting.*transfer", 1.5),
    ],
    "Bank Representative": [
        ("bank manager speaking", 1.5), ("from .*bank.*verification", 1.2),
        ("your relationship manager", 1.4), ("branch manager", 1.1),
        ("bank official", 1.2), ("kyc department", 1.3),
    ],
    "Courier Executive": [
        ("delivery executive", 1.4), ("courier partner", 1.2),
        ("customs officer", 1.4), ("parcel.*held", 1.1),
        ("logistics team", 1.1),
    ],
    "Government Official": [
        ("income tax officer", 1.5), ("government official", 1.3),
        ("ministry representative", 1.4), ("municipal officer", 1.3),
        ("gazetted officer", 1.4),
    ],
    "Police": [
        ("cyber crime.*officer", 1.6), ("police (station|headquarters)", 1.3),
        ("sub-inspector", 1.4), ("fir has been filed", 1.4),
        ("police verification", 1.2),
    ],
    "Income Tax": [
        ("income tax department", 1.4), ("tax notice", 1.2),
        ("assessment officer", 1.4), ("refund.*income tax", 1.1),
        ("tds.*mismatch", 1.3),
    ],
    "Customer Support": [
        ("support executive", 1.3), ("customer care", 1.0),
        ("helpdesk", 1.1), ("service executive", 1.2),
        ("your service request", 1.1),
    ],
    "HR": [
        ("hr department", 1.2), ("human resources", 1.2),
        ("talent acquisition", 1.3), ("hiring manager", 1.3),
    ],
    "Recruiter": [
        ("i am a recruiter", 1.5), ("placement consultant", 1.4),
        ("staffing agency", 1.3), ("job consultancy", 1.3),
    ],
    "Friend": [
        ("it's me your friend", 1.4), ("old friend", 1.1),
        ("remember me.*school", 1.3), ("long time no see", 1.1),
    ],
    "Family": [
        ("your (son|daughter|nephew|niece|cousin)", 1.3),
        ("beta.*help", 1.2), ("mummy.*papa", 1.2), ("family emergency", 1.2),
    ],
    "Tech Support": [
        ("microsoft.*technician", 1.6), ("apple support", 1.4),
        ("security engineer", 1.2), ("your device is infected", 1.4),
        ("windows.*support", 1.3), ("remote.*technician", 1.3),
    ],
    "Marketplace Buyer": [
        ("interested in your (listing|product|ad)", 1.4),
        ("olx buyer", 1.4), ("will pay extra for shipping", 1.5),
        ("send me.*upi.*advance", 1.4),
    ],
    "Marketplace Seller": [
        ("selling.*urgent.*shifting", 1.3), ("half price.*today only", 1.4),
        ("genuine buyer.*token amount", 1.3), ("advance.*booking.*product", 1.2),
    ],
    "Impersonation": [
        ("on behalf of", 1.2), ("authorized representative", 1.3),
        ("acting manager", 1.2), ("official account", 1.0),
    ],
}

_COMPILED = {k: [(re.compile(p, re.IGNORECASE | re.DOTALL), w) for p, w in v]
             for k, v in _PERSONA_PHRASES.items()}


class AuthorityDetector:
    """Detect claimed sender personas with confidence and evidence."""

    def detect(self, text: str) -> dict:
        lowered = text or ""
        personas: list[dict] = []
        for persona, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                found = pattern.findall(lowered)
                if found:
                    total += weight * (1.0 + 0.2 * (len(found) - 1))
                    snippet = found[0] if isinstance(found[0], str) else found[0][0]
                    hits.append(" ".join(str(snippet).split())[:50])
            if total >= 1.0:
                personas.append({"persona": persona,
                                 "confidence": round(min(0.95, 0.40 + 0.18 * total), 3),
                                 "evidence": hits[:3], "score": round(total, 2)})
        personas.sort(key=lambda p: -p["score"])
        return {"personas": personas,
                "names": [p["persona"] for p in personas],
                "count": len(personas)}
