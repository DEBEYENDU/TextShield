"""Conversation pattern analysis: greeting→request→pressure flow, question
load, imperative ratio and call-to-action presence.
"""

from __future__ import annotations

import re

_GREETING = re.compile(r"(?i)^(dear|hello|hi|hey|respected|greetings|good (morning|evening|afternoon))\b")
_QUESTION = re.compile(r"\?")
_IMPERATIVE = re.compile(
    r"(?im)^(?:please |kindly |do not |don't |never |click |tap |send |share |pay |"
    r"transfer |verify |confirm |call |download |install |open |enter |submit |reply |visit )")
_CTA = re.compile(
    r"(?i)(click (here|below|the link)|tap (here|below)|call now|reply (now|today)|"
    r"visit .* (link|website)|scan.*qr|download.*(app|file)|register (now|here))")
_CLOSING = re.compile(r"(?i)(regards|sincerely|thank you|best wishes|warm regards|yours)")


class ConversationAnalyzer:
    """Describe conversational structure and pressure flow."""

    def analyze(self, text: str) -> dict:
        raw = text or ""
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", raw) if s.strip()]
        n_sent = max(len(sentences), 1)
        has_greeting = bool(lines and _GREETING.search(lines[0]))
        has_closing = bool(lines and _CLOSING.search(" ".join(lines[-2:])))
        questions = len(_QUESTION.findall(raw))
        imperatives = len(_IMPERATIVE.findall(raw))
        imperative_ratio = round(imperatives / n_sent, 3)
        ctas = sorted({_m.group(0)[:45] for _m in _CTA.finditer(raw)})
        # pressure flow: request appears after greeting without context building
        flow = "Direct"
        if has_greeting and imperatives == 0 and questions == 0:
            flow = "Informational"
        elif imperatives >= 2 and not has_greeting:
            flow = "Abrupt Demand"
        elif has_greeting and imperatives >= 1 and len(sentences) <= 4:
            flow = "Greeting-to-Demand"
        elif questions >= 2:
            flow = "Interrogative"
        if "Abrupt Demand" in flow or imperative_ratio > 0.5 or len(ctas) >= 2:
            pressure_flow = "High"
        elif imperative_ratio > 0.25 or ctas:
            pressure_flow = "Medium"
        else:
            pressure_flow = "Low"
        return {"has_greeting": has_greeting, "has_closing": has_closing,
                "question_count": questions, "imperative_count": imperatives,
                "imperative_ratio": imperative_ratio,
                "call_to_actions": ctas, "flow": flow,
                "pressure_flow": pressure_flow,
                "sentence_count": len(sentences)}
