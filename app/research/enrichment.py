"""Enrichment layer for research."""

from __future__ import annotations
from .models import KnowledgeItem

class EnrichmentEngine:
    def enrich(self, item: KnowledgeItem) -> KnowledgeItem:
        item.attributes["enriched"] = True
        return item
