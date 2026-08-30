"""Semantic Understanding Engine — package root.

Converts a message into a rich, neutral semantic representation:

* normalized text + language
* contextual domains with confidence
* semantic topics with confidence
* extracted entities (structured)
* semantic features (counts/booleans, NOT spam indicators)
* embeddings (message / sentences / subject / body)

The engine NEVER classifies. It is independent of RAG, LLMs and the
spam classifier; downstream phases (intent, behavior, decision,
explainability) consume :class:`SemanticAnalysisResult`.
"""

from __future__ import annotations
