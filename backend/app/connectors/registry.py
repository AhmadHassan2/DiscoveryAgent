"""Connector registry: the single place where mock connectors would be swapped for live ones."""
from __future__ import annotations

from functools import lru_cache

from app.connectors.base import SourceConnector
from app.connectors.sources import (
    ConfluenceConnector,
    GitHubConnector,
    IdeaRegistryConnector,
    JiraConnector,
    ServiceNowConnector,
    SharePointConnector,
    TeamsConnector,
)
from app.schemas.records import SourceSystem


@lru_cache(maxsize=1)
def all_connectors() -> dict[SourceSystem, SourceConnector]:
    connectors: list[SourceConnector] = [
        ConfluenceConnector(), JiraConnector(), GitHubConnector(), SharePointConnector(),
        TeamsConnector(), ServiceNowConnector(), IdeaRegistryConnector(),
    ]
    return {c.source: c for c in connectors}


def get_connectors(selected: list[SourceSystem] | None = None) -> list[SourceConnector]:
    registry = all_connectors()
    if not selected:
        return list(registry.values())
    return [registry[s] for s in selected if s in registry]
