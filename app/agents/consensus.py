"""Consensus engine: merge threat/trust/confidence, resolve conflicts.

Weighted by relevance × confidence. Conflict rule: when the ML verdict
says Spam but two or more high-relevance agents report legitimate with
low phishing/fraud risk, consensus downgrades to Likely Legitimate with
an explicit conflict note (and vice versa for lone-wolf high-risk agents
against a calm ML verdict — flagged for manual review instead).
"""

from __future__ import annotations


def _weight(report: dict) -> float:
    return max(float(report.get("relevance", 0.0))
               * float(report.get("confidence", 0.0)), 1e-6)


class ConsensusEngine:
    """Deterministic opinion merger with explainable conflict handling."""

    engine_version = "1.0.0"

    def reach_consensus(self, agent_reports: list[dict],
                        ml_label: str = "", ml_confidence: float = 0.0) -> dict:
        total_w = sum(_weight(r) for r in agent_reports) or 1e-6
        risk = sum(r.get("risk_score", 0.0) * _weight(r)
                   for r in agent_reports) / total_w
        trust = sum(r.get("trust_score", 0.0) * _weight(r)
                    for r in agent_reports) / total_w
        confidence = sum(r.get("confidence", 0.0) * _weight(r)
                         for r in agent_reports) / total_w
        risk, trust = round(risk, 3), round(trust, 3)
        confidence = round(confidence, 3)

        legit_votes = [r["name"] for r in agent_reports
                       if r.get("trust_score", 0.0) >= 0.6
                       and r.get("relevance", 0.0) >= 0.4]
        threat_votes = [r["name"] for r in agent_reports
                        if r.get("risk_score", 0.0) >= 0.5
                        and r.get("relevance", 0.0) >= 0.3]
        conflicts: list[str] = []
        if ml_label == "SPAM" and len(legit_votes) >= 2 and not threat_votes:
            conflicts.append(
                f"ML says Spam but {', '.join(legit_votes)} find legitimate "
                f"patterns with no threat corroboration.")
        lone_wolves = [r["name"] for r in agent_reports
                       if r.get("risk_score", 0.0) >= 0.7
                       and r.get("relevance", 0.0) < 0.3]
        if ml_label == "HAM" and lone_wolves and not threat_votes:
            conflicts.append(
                f"Low-relevance agents ({', '.join(lone_wolves)}) raise risk "
                f"against a calm ML verdict — manual review advised.")

        if risk >= 0.65:
            consensus, band = "Likely Malicious", "High"
        elif risk >= 0.4:
            consensus, band = ("Possibly Malicious", "Medium") \
                if trust < 0.6 else ("Uncertain — conflicting signals", "Medium")
        elif trust >= 0.6:
            consensus, band = "Likely Legitimate", "Low"
        elif conflicts and "ML says Spam" in conflicts[0]:
            consensus, band = "Likely Legitimate (contested)", "Low"
        else:
            consensus, band = "Likely Legitimate", "Low"
        if conflicts and band == "Low" and "contested" not in consensus \
                and ml_label == "SPAM":
            consensus = "Likely Legitimate (contested)"

        return {
            "consensus": consensus,
            "overall_risk": band,
            "risk_score": risk,
            "trust_score": trust,
            "confidence": confidence,
            "legit_votes": legit_votes,
            "threat_votes": threat_votes,
            "conflicts": conflicts,
            "ml_label": ml_label,
            "ml_confidence": round(float(ml_confidence), 3),
            "engine_version": self.engine_version,
        }


consensus_engine = ConsensusEngine()
