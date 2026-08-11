"""Input type detection and raw email parsing.

The UI declares an explicit input type, but the pipeline also supports
pasting a raw email (header + body) which is parsed with the stdlib
``email`` package so subject/sender/body are extracted automatically.
"""
from __future__ import annotations

from email import message_from_string
from email.header import decode_header
from email.utils import parseaddr

_RAW_EMAIL_MARKERS = ("from:", "subject:", "to:", "date:", "delivered-to:", "reply-to:")


def looks_like_raw_email(text: str) -> bool:
    """Heuristic: does the pasted content start with email headers?"""
    head = (text or "").strip().lower()
    if not head or len(head) < 10:
        return False
    lines = head.splitlines()
    if not lines:
        return False
    return any(
        line.strip().startswith(marker)
        for line in lines
        for marker in _RAW_EMAIL_MARKERS
    )


def _decode(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        text.decode(encoding or "utf-8", errors="replace")
        if isinstance(text, bytes)
        else text
        for text, encoding in parts
    )


def parse_raw_email(raw: str) -> dict:
    """Parse a raw email into {subject, sender, body}."""
    msg = message_from_string(raw)
    subject = _decode(msg.get("Subject", "")).strip()
    _, sender = parseaddr(msg.get("From", ""))
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        body = payload.decode("utf-8", errors="replace")
                    except Exception:
                        body = part.get_payload()
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                body = payload.decode("utf-8", errors="replace")
            except Exception:
                body = msg.get_payload()
        else:
            body = msg.get_payload() or ""
    return {"subject": subject, "sender": sender, "body": body.strip()}


def detect_input_type(text: str) -> str:
    """Return the detected message type: 'email' or 'text'.

    The UI declares an explicit input_type for its tabs; this detector is
    used as an upgrade path when users paste raw content (e.g. a complete
    email with headers into the generic text box).
    """
    if looks_like_raw_email(text):
        return "email"
    return "text"