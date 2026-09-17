"""Agent registry: plugin-style registration, no code changes for new agents."""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.specialists import ALL_AGENTS


class AgentRegistry:
    """Maps agent names to agent classes; supports runtime plugins."""

    def __init__(self):
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(self, agent_cls: type[BaseAgent]) -> type[BaseAgent]:
        self._agents[agent_cls.name] = agent_cls
        return agent_cls

    def unregister(self, name: str) -> bool:
        return self._agents.pop(name, None) is not None

    def get(self, name: str) -> type[BaseAgent] | None:
        return self._agents.get(name)

    def names(self) -> list[str]:
        return sorted(self._agents)

    def instantiate(self, llm_client=None,
                    only: list[str] | None = None) -> list[BaseAgent]:
        selected = [n for n in self.names() if only is None or n in only]
        return [self._agents[name](llm_client=llm_client) for name in selected]

    def __len__(self) -> int:
        return len(self._agents)


def register(agent_cls: type[BaseAgent]) -> type[BaseAgent]:
    """Decorator for plugin agents: ``@register class HealthcareAgent(...)``."""
    default_registry.register(agent_cls)
    return agent_cls


default_registry = AgentRegistry()
for _cls in ALL_AGENTS:
    default_registry.register(_cls)
