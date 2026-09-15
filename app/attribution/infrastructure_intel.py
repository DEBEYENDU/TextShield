"""Infrastructure intelligence layer."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import InfrastructureNode
from app.threat_intel.extractor import extract_iocs
from app.graph.normalization import normalize_domain, normalize_url, normalize_email
from app.core.logging import get_logger

logger = get_logger(__name__)


class InfrastructureIntel:
    def __init__(self):
        self._nodes: Dict[str, InfrastructureNode] = {}

    def ingest_message(self, message_id: str, text: str) -> List[InfrastructureNode]:
        iocs = extract_iocs(text)
        nodes = []
        for ioc in iocs:
            norm = ioc.normalized_value
            if ioc.ioc_type == "domain":
                norm = normalize_domain(norm)
            elif ioc.ioc_type == "url":
                norm = normalize_url(norm)
            elif ioc.ioc_type == "email":
                norm = normalize_email(norm)
            node_id = f"{ioc.ioc_type}:{norm}"
            node = self._nodes.get(node_id)
            if not node:
                node = InfrastructureNode(
                    id=node_id,
                    type=ioc.ioc_type,
                    normalized_value=norm,
                    display_value=ioc.original_value,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    usage_count=1
                )
                self._nodes[node_id] = node
            else:
                node.usage_count += 1
                node.last_seen = datetime.utcnow()
            nodes.append(node)
        logger.debug("Infrastructure nodes ingested for %s: %d", message_id, len(nodes))
        return nodes

    def get_node(self, node_id: str) -> InfrastructureNode | None:
        return self._nodes.get(node_id)

    def link_to_actor(self, node_id: str, actor_id: str):
        node = self._nodes.get(node_id)
        if node and actor_id not in node.associated_actors:
            node.associated_actors.append(actor_id)

    def list_nodes(self) -> List[InfrastructureNode]:
        return list(self._nodes.values())
