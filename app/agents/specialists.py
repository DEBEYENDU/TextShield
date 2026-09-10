"""Seven specialized security agents (RFC-005).

Each agent reads the shared AgentContext and reports domain findings with
relevance-weighted risk/trust. Deterministic — no LLM required.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.context import AgentContext


def _evidence_list(items: list, limit: int = 4) -> list[str]:
    out = []
    for item in items or []:
        if isinstance(item, dict):
            label = str(item.get("indicator", item.get("technique",
                             item.get("persona", item.get("value", "")))))
            ev = str(item.get("evidence", ""))[:50]
            out.append(f"{label}: {ev}" if ev else label)
        else:
            out.append(str(item)[:60])
        if len(out) >= limit:
            break
    return out


class RecruitmentAgent(BaseAgent):
    name = "RecruitmentAgent"
    prompt_file = "recruitment.md"

    def assess(self, ctx: AgentContext) -> dict:
        text = ctx.text.lower()
        findings: list[str] = []
        relevance = 0.15
        risk, trust = 0.05, 0.5
        if ctx.category in {"Recruitment", "Educational Announcement"}:
            relevance = 0.95
            findings.append(f"message type matches recruitment domain ({ctx.category})")
        recruiters = ctx.entity_values("recruiters") + ctx.entity_values("companies")
        jobs = ctx.entity_values("job_titles")
        if recruiters or jobs:
            relevance = max(relevance, 0.8)
            findings.append(f"hiring entities: {', '.join((recruiters + jobs)[:3])}")
        scam_markers = [w for w in ("registration charge", "pay to apply",
                                    "advance", "share otp", "send otp")
                        if w in text]
        if "fee" in text and "no fee" not in text:
            scam_markers.append("fee demand")
        if scam_markers and relevance >= 0.5:
            risk = 0.85
            trust = 0.1
            findings.append(f"hiring-scam markers: {', '.join(scam_markers)}")
            action = "Do not pay any fee; verify the recruiter on the company site."
            reasoning = ("Recruitment context with advance-fee/credential demands "
                         "matches hiring-scam patterns.")
        elif relevance >= 0.5:
            trust = 0.85
            risk = 0.08
            findings.append("no fee demands, no credential requests in hiring flow")
            action = "Proceed normally; verify venue and interviewer identity."
            reasoning = ("Campus/HR communication with expected workflow and no "
                         "extraction demands.")
        else:
            action = "No recruitment relevance."
            reasoning = "No hiring signals; agent abstains."
            trust = 0.5
        return {"relevance": relevance, "findings": findings, "risk_score": risk,
                "trust_score": trust, "recommended_action": action,
                "reasoning": reasoning}


class BankingAgent(BaseAgent):
    name = "BankingAgent"
    prompt_file = "banking.md"

    def assess(self, ctx: AgentContext) -> dict:
        text = ctx.text.lower()
        findings: list[str] = []
        relevance = 0.15
        banks = ctx.entity_values("banks")
        if ctx.category in {"Bank Notification", "OTP / Authentication",
                            "Payment Confirmation", "Invoice"}:
            relevance = 0.9
            findings.append(f"banking message type ({ctx.category})")
        if banks:
            relevance = max(relevance, 0.85)
            findings.append(f"bank entities: {', '.join(banks[:3])}")
        if any(k in text for k in ("upi", "otp", "kyc", "neft", "imps", "balance",
                                   "bank details", "new account", "transfer",
                                   "invoice", "refund")):
            relevance = max(relevance, 0.6)
        danger = [w for w in ("share the otp", "share your otp", "share this otp",
                              "send otp", "otp shown", "enter otp",
                              "verify at http",
                              "bit.ly", "tinyurl", "account blocked",
                              "suspended", "kyc pending", "bank details changed",
                              "details have changed", "new account",
                              "grant remote access", "remote access",
                              "anydesk", "teamviewer")
                  if w in text]
        if danger and relevance >= 0.5:
            risk, trust = 0.88, 0.08
            findings.append(f"banking-fraud markers: {', '.join(danger)}")
            action = "Never share OTP; verify only in the official bank app."
            reasoning = ("Banking context combined with credential harvesting and "
                         "suspension threats matches KYC/UPI fraud.")
        elif relevance >= 0.5:
            risk, trust = 0.1, 0.85
            findings.append("routine transaction record, no extraction demands")
            action = "No action needed; routine notification."
            reasoning = "Transaction alert consistent with expected banking workflow."
        else:
            risk, trust = 0.05, 0.5
            action = "No banking relevance."
            reasoning = "No banking signals; agent abstains."
        return {"relevance": relevance, "findings": findings, "risk_score": risk,
                "trust_score": trust, "recommended_action": action,
                "reasoning": reasoning}


class GovernmentAgent(BaseAgent):
    name = "GovernmentAgent"
    prompt_file = "government.md"

    def assess(self, ctx: AgentContext) -> dict:
        text = ctx.text.lower()
        findings: list[str] = []
        relevance = 0.12
        depts = ctx.entity_values("government_departments")
        if ctx.category == "Government Advisory":
            relevance = 0.9
            findings.append("government advisory message type")
        if depts:
            relevance = max(relevance, 0.85)
            findings.append(f"departments: {', '.join(depts[:3])}")
        if any(k in text for k in ("rbi", "npci", "cert-in", "income tax",
                                   "aadhaar", "pan", "ministry")):
            relevance = max(relevance, 0.7)
            findings.append("regulator/identity references present")
        coercion = [w for w in ("pay penalty now", "share otp", "arrest",
                                "account frozen", "immediate payment")
                    if w in text]
        if coercion and relevance >= 0.4:
            risk, trust = 0.85, 0.1
            findings.append(f"official-impersonation markers: {', '.join(coercion)}")
            action = "Verify on the official .gov.in portal; never pay via links."
            reasoning = ("Government framing with coercive payment/OTP demands "
                         "matches official-impersonation fraud.")
        elif relevance >= 0.5:
            risk, trust = 0.08, 0.88
            findings.append("circular-style notice, no coercion")
            action = "Follow the published helpline or portal if action is needed."
            reasoning = "Advisory consistent with official circular patterns."
        else:
            risk, trust = 0.05, 0.5
            action = "No government relevance."
            reasoning = "No government signals; agent abstains."
        return {"relevance": relevance, "findings": findings, "risk_score": risk,
                "trust_score": trust, "recommended_action": action,
                "reasoning": reasoning}


class PhishingAgent(BaseAgent):
    name = "PhishingAgent"
    prompt_file = "phishing.md"

    def assess(self, ctx: AgentContext) -> dict:
        findings: list[str] = []
        fams = ctx.threat_families()
        phish_fams = {"credential_harvesting", "suspicious_url", "impersonation",
                      "typosquatting", "homograph", "sensitive_info_request",
                      "credential_request", "remote_access_request",
                      "malware_delivery", "attachment_abuse", "macro_documents"}
        hits = sorted(fams & phish_fams)
        urls = ctx.entity_values("urls")
        relevance = 0.25 + 0.25 * bool(urls) + 0.15 * min(len(hits), 3)
        relevance = min(0.95, relevance)
        if hits:
            findings.append(f"phishing families: {', '.join(hits)}")
        if urls:
            findings.append(f"suspicious links: {', '.join(urls[:2])}")
        if ctx.profile.get("credential_requests"):
            findings.append("credential request detected")
            relevance = min(0.95, relevance + 0.2)
        risk = min(0.95, 0.15 + 0.3 * len(hits) + (0.2 if urls else 0.0))
        trust = round(max(0.05, 0.6 - 0.25 * len(hits)), 3)
        if hits or urls:
            action = "Do not click or enter credentials; open the site manually."
            reasoning = (f"{len(hits)} phishing signal families with "
                         f"{len(urls)} link(s) indicate credential harvesting.")
        else:
            risk = 0.08
            action = "No phishing indicators."
            reasoning = "No credential-harvesting or URL-abuse signals."
        return {"relevance": round(relevance, 3), "findings": findings,
                "risk_score": round(risk, 3), "trust_score": trust,
                "recommended_action": action, "reasoning": reasoning}


class FraudAgent(BaseAgent):
    name = "FraudAgent"
    prompt_file = "fraud.md"

    def assess(self, ctx: AgentContext) -> dict:
        findings: list[str] = []
        fams = ctx.threat_families()
        fraud_fams = {"lottery", "investment_scam", "crypto_scam", "reward_bait",
                      "scarcity", "prize_claim", "money_transfer", "romance_scam",
                      "refund_scam", "advance_fee", "remote_access_request",
                      "urgency"}
        hits = sorted(fams & fraud_fams)
        money = ctx.entity_values("money")
        relevance = 0.2 + 0.15 * min(len(hits), 3) + 0.2 * bool(money)
        relevance = min(0.95, relevance)
        if hits:
            findings.append(f"fraud families: {', '.join(hits)}")
        if money:
            findings.append(f"money references: {', '.join(money[:2])}")
        base_names = ctx.indicator_names()
        if any("lottery" in b or "prize" in b or "investment" in b for b in base_names):
            findings.append("prize/investment lure language")
            relevance = min(0.95, relevance + 0.25)
        risk = min(0.95, 0.12 + 0.3 * len(hits))
        trust = round(max(0.05, 0.6 - 0.25 * len(hits)), 3)
        if hits:
            action = "Do not pay fees or transfer funds; verify the offer independently."
            reasoning = (f"{len(hits)} financial-fraud families indicate an "
                         f"advance-fee or fake-return scheme.")
        else:
            risk = 0.08
            action = "No fraud indicators."
            reasoning = "No lottery/investment/refund lure signals."
        return {"relevance": round(relevance, 3), "findings": findings,
                "risk_score": round(risk, 3), "trust_score": trust,
                "recommended_action": action, "reasoning": reasoning}


class BehaviorAgent(BaseAgent):
    name = "BehaviorAgent"
    prompt_file = "social_engineering.md"

    def assess(self, ctx: AgentContext) -> dict:
        bp = ctx.behavior_profile or {}
        findings: list[str] = []
        triggers = bp.get("psychological_triggers", [])
        personas = bp.get("social_engineering", [])
        manip = float(bp.get("manipulation_score", 0.0))
        urg = (bp.get("urgency", {}) or {}).get("level", "Low")
        relevance = min(0.9, 0.3 + 0.15 * len(triggers) + 0.2 * bool(personas)
                        + (0.2 if urg in {"High", "Critical"} else 0.0))
        if triggers:
            findings.append(f"triggers: {', '.join(triggers[:5])}")
        if personas:
            findings.append(f"personas: {', '.join(personas[:3])}")
        if urg in {"High", "Critical"}:
            findings.append(f"urgency level {urg}")
        findings.append(f"manipulation {bp.get('manipulation_level', 'Minimal')} "
                        f"({manip}), style {bp.get('communication_style', 'Neutral')}")
        risk = round(min(0.95, manip * 0.8 + (0.25 if urg in {'High', 'Critical'} else 0.0)
                         + 0.1 * bool(personas)), 3)
        trust = round(max(0.05, 0.75 - manip), 3)
        if manip >= 0.35 or personas:
            action = "Treat requests skeptically; verify through official channels."
            reasoning = ("Behavioral pressure (manipulation "
                         f"{manip}, urgency {urg}) with "
                         f"{len(personas)} persona(s) indicates social engineering.")
        else:
            action = "Communication style is calm and routine."
            reasoning = "No significant manipulation or pressure signals."
        return {"relevance": round(relevance, 3), "findings": findings,
                "risk_score": risk, "trust_score": trust,
                "recommended_action": action, "reasoning": reasoning}


class LegitimacyAgent(BaseAgent):
    name = "LegitimacyAgent"
    prompt_file = "legitimacy.md"

    def assess(self, ctx: AgentContext) -> dict:
        legitimacy = ctx.legitimacy or {}
        indicators = legitimacy.get("indicators", [])
        trust_evidence = _evidence_list(indicators)
        known_orgs = (ctx.graph_verdict or {}).get("known_organizations", [])
        relevance = min(0.9, 0.35 + 0.1 * len(indicators) + 0.2 * bool(known_orgs))
        findings = trust_evidence[:4]
        if known_orgs:
            findings.append(f"known organizations: {', '.join(known_orgs[:3])}")
        base_trust = float(ctx.profile.get("trust_score", 0.5))
        # absence-of-harm alone is not legitimacy: cap when no positive
        # institutional marker (named org, formal structure, workflow) exists
        positive_markers = [i for i in indicators
                            if not str(i.get("indicator", "")).startswith("no_")]
        if not positive_markers and not known_orgs:
            relevance = min(relevance, 0.35)
            base_trust = min(base_trust, 0.55)
        trust = round(min(0.95, 0.3 + 0.5 * base_trust + 0.1 * bool(known_orgs)), 3)
        risk = round(max(0.05, 0.5 - 0.5 * base_trust), 3)
        if base_trust >= 0.6:
            action = "Institutional markers present; proceed normally."
            reasoning = (f"Trust score {base_trust} with "
                         f"{len(indicators)} legitimacy indicators.")
        else:
            action = "Few legitimacy markers; verify sender independently."
            reasoning = "Weak institutional evidence; legitimacy not established."
        return {"relevance": round(relevance, 3), "findings": findings,
                "risk_score": risk, "trust_score": trust,
                "recommended_action": action, "reasoning": reasoning}


ALL_AGENTS = [
    RecruitmentAgent,
    BankingAgent,
    GovernmentAgent,
    PhishingAgent,
    FraudAgent,
    BehaviorAgent,
    LegitimacyAgent,
]
