"""Contracts for registry, projects, sources, stats and demo endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.analysis import IdeaInput
from app.schemas.records import ConnectorHealth


class IdeaRegistration(BaseModel):
    idea: IdeaInput
    submitted_by: str | None = None
    analysis_id: str | None = Field(default=None, description="Reuse an existing overlap check")
    acknowledge_overlap: bool = False
    acknowledgement_note: str | None = Field(default=None, max_length=2000)


class RegisteredIdea(BaseModel):
    id: str
    title: str
    description: str
    business_problem: str | None
    proposed_functionality: str | None
    target_users: str | None
    department: str | None
    team: str | None
    technologies: str | None
    submitted_by: str
    status: str
    analysis_id: str | None
    related_initiatives: list[dict[str, Any]]
    acknowledged_overlap: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class RegistrationBlocked(BaseModel):
    detail: str
    analysis_id: str
    overlapping: list[dict[str, Any]]


class InitiativeSummary(BaseModel):
    id: str
    name: str
    department: str
    team: str
    owner_name: str | None
    status: str
    description: str
    last_activity_at: datetime
    created_at: datetime
    record_count: int
    sources: list[str]


class InitiativeDetail(InitiativeSummary):
    aliases: list[str]
    business_objective: str
    core_features: list[str]
    target_users: list[str]
    technologies: list[str]
    reusable_components: list[str]
    notes: str | None
    owner_email: str | None
    records: list[dict[str, Any]]
    related: list[dict[str, Any]]


class SourcesOverview(BaseModel):
    data_mode: str
    sources: list[ConnectorHealth]
    total_records: int


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # initiative | team | person | record | idea | department
    group: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class StatsResponse(BaseModel):
    initiatives: int
    records: int
    sources: int
    departments: int
    registered_ideas: int
    analyses_run: int
    duplicates_flagged: int
    by_status: dict[str, int]
    by_department: dict[str, int]
    by_source: dict[str, int]


class DemoScenario(BaseModel):
    id: str
    case: str
    title: str
    summary: str
    idea: IdeaInput
    expected: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    llm_model: str | None
    embedding_provider: str
    data_mode: str
    failing_sources: list[str]
    version: str = "0.1.0"
