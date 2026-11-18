"""Common connector interface.

Every source system (mock or real) implements `SourceConnector`. Connectors are READ-ONLY by
design: the interface exposes search and lookup operations only — there is no write method.
The pipeline depends only on this interface, so a mock connector can be swapped for an
approved API-based integration without changing the core search pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.schemas.records import ConnectorHealth, ConnectorSearchRequest, NormalizedRecord, SourceSystem


class ConnectorUnavailableError(RuntimeError):
    """Raised when a source system cannot be reached (network, auth, outage)."""


class SourceConnector(ABC):
    source: ClassVar[SourceSystem]
    display_name: ClassVar[str]
    description: ClassVar[str] = ""
    mode: ClassVar[str] = "mock"  # "mock" | "live"
    read_only: ClassVar[bool] = True

    @abstractmethod
    def search(self, request: ConnectorSearchRequest) -> list[NormalizedRecord]:
        """Search the source and return normalised records with retrieval scores."""

    @abstractmethod
    def fetch_related(self, keys: list[str]) -> list[NormalizedRecord]:
        """Return records that reference any of the given keys (cross-reference expansion)."""

    @abstractmethod
    def health(self) -> ConnectorHealth:
        """Report availability and index statistics."""
