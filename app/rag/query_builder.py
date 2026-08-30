"""Query builder: convert Semantic Engine output into optimized semantic search queries.

Converts detected topics, entities, intent, behavior, communication goal, context,
and extracted keywords into multiple retrieval queries rather than a single query.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional

from app.semantic.semantic_models import SemanticFeatures


@dataclass
class QuerySpec:
    """A search query with its type and associated metadata."""

    query: str
    query_type: str  # "primary", "intent", "behavior", "entity", "context"
    boost: float = 1.0
    weight: float = 1.0


@dataclass
class QueryBuilderResult:
    """Result of building queries from semantic features."""

    primary: QuerySpec
    intent: QuerySpec
    behavior: QuerySpec
    entity: QuerySpec
    context: QuerySpec
    all_queries: List[QuerySpec] = field(default_factory=list)

    @property
    def queries(self) -> List[QuerySpec]:
        """Get all queries as a list."""
        queries = [self.primary]
        if self.intent is not None:
            queries.append(self.intent)
        if self.behavior is not None:
            queries.append(self.behavior)
        if self.entity is not None:
            queries.append(self.entity)
        if self.context is not None:
            queries.append(self.context)
        return queries


class QueryBuilder:
    """Builds multiple optimized semantic search queries from semantic engine output."""

    def __init__(self, semantic_features: SemanticFeatures):
        self.semantic = semantic_features
        self.keywords: Set[str] = self._extract_keywords()
        self.entities: Set[str] = self._extract_entities()
        self.topics: Set[str] = self._extract_topics()
        self.intent: Optional[str] = self._detect_intent()
        self.behavior: Optional[str] = self._detect_behavior()

    def _extract_keywords(self) -> Set[str]:
        """Extract meaningful keywords from semantic features."""
        keywords: Set[str] = set()
        # Extract from topic names
        for topic in getattr(self.semantic, "topic_names", []):
            words = topic.lower().split()
            keywords.update(words)
        # Add behavioral pattern keywords if present
        behavioral_patterns = getattr(self.semantic, "behavioral_patterns", [])
        for pattern in behavioral_patterns:
            keywords.add(pattern.lower())
        return keywords

    def _extract_entities(self) -> Set[str]:
        """Extract named entities from semantic features."""
        entities: Set[str] = set()
        for entity in getattr(self.semantic, "entities", []):
            entities.add(entity.lower())
        return entities

    def _extract_topics(self) -> Set[str]:
        """Extract topic labels from semantic features."""
        return set(getattr(self.semantic, "topic_names", []))

    def _detect_intent(self) -> Optional[str]:
        """Detect the primary intent from semantic features."""
        return getattr(self.semantic, "intent", None)

    def _detect_behavior(self) -> Optional[str]:
        """Detect the primary behavioral pattern from semantic features."""
        behavioral_patterns = getattr(self.semantic, "behavioral_patterns", [])
        if behavioral_patterns:
            return behavioral_patterns[0].lower()
        return None

    def build(self) -> QueryBuilderResult:
        """Build all query types from the semantic features."""
        # Primary query: broad semantic search using topics and keywords
        primary_query = self._build_primary_query()

        # Intent-based query
        intent_query = self._build_intent_query()

        # Behavior-based query
        behavior_query = self._build_behavior_query()

        # Entity query
        entity_query = self._build_entity_query()

        # Context query
        context_query = self._build_context_query()

        all_queries = [
            primary_query,
            intent_query,
            behavior_query,
            entity_query,
            context_query,
        ]

        return QueryBuilderResult(
            primary=primary_query,
            intent=intent_query,
            behavior=behavior_query,
            entity=entity_query,
            context=context_query,
            all_queries=all_queries,
        )

    def _build_primary_query(self) -> QuerySpec:
        """Build the primary semantic query."""
        # Combine topics and keywords for broad coverage
        query_parts = list(self.topics) + list(self.keywords)
        if not query_parts:
            query_parts = ["scam", "phishing", "fraud"]

        query = " ".join(query_parts)
        return QuerySpec(
            query=query,
            query_type="primary",
            boost=1.0,
            weight=1.0,
        )

    def _build_intent_query(self) -> QuerySpec:
        """Build the intent-based query."""
        if not self.intent:
            # Fall back to primary query pattern
            return QuerySpec(
                query="scam phishing fraud",
                query_type="intent",
                boost=0.5,
                weight=0.5,
            )

        # Build query around detected intent with related terms
        intent_queries = {
            "urgency": "urgent time-sensitive pressure immediate",
            "authority": "authority impersonation official claim",
            "fear": "fear threat threat coercion",
            "reward": "reward prize offer benefit",
            "curiosity": "curiosity mystery intriguing",
            "scarcity": "scarcity limited exclusive",
            "reciprocity": "reciprocity favor gift",
            "trust_building": "trust building rapport",
            "social_proof": "social proof consensus majority",
            "pressure": "pressure coercion force",
            "personalization": "personalized personalized",
        }

        related = intent_queries.get(self.intent, self.intent)

        return QuerySpec(
            query=f"{self.intent} {related}",
            query_type="intent",
            boost=1.2,
            weight=1.0,
        )

    def _build_behavior_query(self) -> QuerySpec:
        """Build the behavior-based query."""
        if not self.behavior:
            return QuerySpec(
                query="scam fraud deceptive",
                query_type="behavior",
                boost=0.5,
                weight=0.5,
            )

        behavior_queries = {
            "urgency": "urgency pressure time-sensitive immediate",
            "authority": "authority impersonation official",
            "fear": "fear threat danger",
            "reward": "reward prize benefit",
            "curiosity": "curiosity intriguing mysterious",
            "scarcity": "scarcity limited exclusive",
            "reciprocity": "reciprocity favor gift",
            "trust_building": "trust building rapport",
            "social_proof": "social proof consensus",
            "pressure": "pressure coercion force",
            "personalization": "personalized personalized",
        }

        related = behavior_queries.get(self.behavior, self.behavior)

        return QuerySpec(
            query=f"{self.behavior} {related}",
            query_type="behavior",
            boost=1.1,
            weight=1.0,
        )

    def _build_entity_query(self) -> QuerySpec:
        """Build the entity-based query."""
        if not self.entities:
            return QuerySpec(
                query="scam fraud",
                query_type="entity",
                boost=0.5,
                weight=0.5,
            )

        # Use the most relevant entities to build query
        entity_str = " ".join(sorted(self.entities)[:3])
        return QuerySpec(
            query=f"{entity_str} scam fraud",
            query_type="entity",
            boost=1.1,
            weight=1.0,
        )

    def _build_context_query(self) -> QuerySpec:
        """Build the context-based query."""
        context_parts = []

        # Add communication goal if available
        communication_goal = getattr(self.semantic, "communication_goal", "")
        if communication_goal:
            context_parts.append(communication_goal.lower())

        # Add language if available
        language = getattr(self.semantic, "language", "en-us")
        if language:
            context_parts.append(language)

        # Add any additional context from semantic features
        additional_context = getattr(self.semantic, "additional_context", "")
        if additional_context:
            context_parts.append(additional_context.lower())

        if not context_parts:
            context_parts = ["communication", "message", "notification"]

        query = " ".join(context_parts)
        return QuerySpec(
            query=query,
            query_type="context",
            boost=0.8,
            weight=0.8,
        )


def build_queries_from_semantic(
    semantic_features: SemanticFeatures,
) -> QueryBuilderResult:
    """Convenience function to build all queries from semantic features."""
    builder = QueryBuilder(semantic_features)
    return builder.build()
