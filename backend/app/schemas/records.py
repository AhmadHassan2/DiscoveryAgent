"""Normalised record contracts shared by every connector."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceSystem(str, Enum):
    confluence = "confluence"
    jira = "jira"
    github = "github"
    sharepoint = "sharepoint"
    teams = "teams"
    servicenow = "servicenow"
    idea_registry = "idea_registry"


SOURCE_LABELS: dict[str, str] = {
    "confluence": "Confluence",
    "jira": "Jira",
    "github": "GitHub Enterprise",
    "sharepoint": "SharePoint",
    "teams": "Microsoft Teams",
    "servicenow": "ServiceNow",
    "idea_registry": "Idea Registry",
}


class AccessControl(BaseModel):
    visibility: str = "internal"
    groups: list[str] = Field(default_factory=list)
    classification: str = "internal"
    authorized_for_indexing: bool = True


class NormalizedRecord(BaseModel):
    """A record from any source system, in one consistent shape."""

    id: str
    source: SourceSystem
    record_type: str
    external_key: str
    title: str
    content: str
    url: str
    author: str | None = None
    owner: str | None = None
    source_status: str | None = None
    created_at: datetime
    updated_at: datetime
    labels: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    acl: AccessControl = Field(default_factory=AccessControl)
    # Retrieval diagnostics (filled by the connector)
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    fused_score: float = 0.0
    matched_queries: list[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    text: str
    kind: str = "primary"  # primary | expansion | concept


class ConnectorSearchRequest(BaseModel):
    queries: list[SearchQuery]
    expansion_terms: list[str] = Field(default_factory=list)
    query_embedding: list[float] | None = None
    limit: int = 12


class ConnectorStatus(str, Enum):
    ok = "ok"
    error = "error"
    timeout = "timeout"
    disabled = "disabled"


class ConnectorResult(BaseModel):
    source: SourceSystem
    status: ConnectorStatus
    records: list[NormalizedRecord] = Field(default_factory=list)
    duration_ms: int = 0
    error: str | None = None
    filtered_by_permissions: int = 0
    mode: str = "mock"


class ConnectorHealth(BaseModel):
    source: SourceSystem
    display_name: str
    status: ConnectorStatus
    mode: str
    read_only: bool = True
    record_count: int = 0
    record_types: dict[str, int] = Field(default_factory=dict)
    last_indexed_at: datetime | None = None
    description: str = ""
    error: str | None = None
