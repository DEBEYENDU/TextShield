"""Evidence model — understanding WITHOUT classification.

Produces an evidence summary (threat indicators vs legitimacy indicators)
that downstream reasoning consumes. No verdict is produced here.
"""

from __future__ import annotations


class EvidenceModel:
    """Assemble the evidence summary from engine outputs."""

    def build(self, threat: dict, legitimacy: dict) -> dict:
        threat_items = [
            {"indicator": i["indicator"], "severity": i.get("severity", "low"),
             "evidence": i.get("evidence", "")}
            for i in threat.get("indicators", [])
        ]
        trust_items = [
            {"indicator": i["indicator"], "evidence": i.get("evidence", "")}
            for i in legitimacy.get("indicators", [])
        ]
        t_score = float(threat.get("threat_score", 0.0))
        l_score = float(legitimacy.get("trust_score", 0.0))
        if t_score > l_score + 0.25:
            lean = "threat-leaning"
        elif l_score > t_score + 0.25:
            lean = "trust-leaning"
        else:
            lean = "mixed"
        lines = ["Threat Indicators:"]
        lines += [f"  - {i['indicator']}: {i['evidence']}" for i in threat_items] or ["  (none)"]
        lines += ["Legitimacy Indicators:"]
        lines += [f"  - {i['indicator']}: {i['evidence']}" for i in trust_items] or ["  (none)"]
        return {
            "threat_indicators": threat_items,
            "legitimacy_indicators": trust_items,
            "threat_score": t_score,
            "trust_score": l_score,
            "evidence_lean": lean,
            "summary_text": "\n".join(lines),
        }


evidence_model = EvidenceModel()
