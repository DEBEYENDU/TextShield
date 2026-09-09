"""TextShield v3.0 — Enterprise Document Ingestion Engine (RFC-002).

Modular, incremental, fault-tolerant pipeline that converts Markdown, PDF,
TXT, HTML and DOCX documents into normalized, validated, chunked, embedded
and indexed knowledge for the existing RAG engine.

Does NOT modify ML models, the RAG reasoning engine, or frontend behavior.
"""

from __future__ import annotations

__version__ = "3.0.0"
__rfc__ = "RFC-002"

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".pdf", ".txt", ".html", ".htm", ".docx"}

PIPELINE_STAGES = [
    "discover",
    "parse",
    "clean",
    "metadata",
    "validate",
    "deduplicate",
    "chunk",
    "embed",
    "index",
    "manifest",
]
