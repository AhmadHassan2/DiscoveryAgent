"""Contracts for idea analysis requests, progress events and reports."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.records import SourceSystem


class IdeaInput(BaseModel):
    description: str = Field(min_length=10, max_length=5000)
    title: str | None = Field(default=None, max_length=300)
    business_problem: str | None = Field(default=None, max_length=3000)
    proposed_functionality: str | None = Field(default=None, max_length=3000)
    target_users: str | None = Field(default=None, max_length=1000)
    department: str | None = Field(default=None, max_length=120)
    team: str | None = Field(default=None, max_length=120)
    technologies: str | None = Field(default=None, max_length=1000)

    def full_text(self) -> str:
        parts = [self.title, self.description, self.business_problem, self.proposed_functionality,
                 f"Target users: {self.target_users}" if self.target_users else None,
                 f"Technologies: {self.technologies}" if self.technologies else None]
        return "\n".join(p for p in parts if p)


class AnalysisRequest(BaseModel):
    idea: IdeaInput
    sources: list[SourceSystem] | None = None  # None = all enabled sources
    scenario_id: str | None = None
    simulate_failures: list[SourceSystem] = Field(default_factory=list)


class OverlapCategory(str, Enum):
    near_duplicate = "near_duplicate"
    strong_overlap = "strong_overlap"
    partial_overlap = "partial_overlap"
    related = "related"
    no_significant_match = "no_significant_match"


CATEGORY_RANK = {
    OverlapCategory.near_duplicate: 4,
    OverlapCategory.strong_overlap: 3,
    OverlapCategory.partial_overlap: 2,
    OverlapCategory.related: 1,
    OverlapCategory.no_significant_match: 0,
}

CATEGORY_LABELS = {
    OverlapCategory.near_duplicate: "Near-duplicate",
    OverlapCategory.strong_overlap: "Strong overlap",
    OverlapCategory.partial_overlap: "Partial overlap",
    OverlapCategory.related: "Related but different",
    OverlapCategory.no_significant_match: "No significant match",
}


class LifecycleStage(str, Enum):
    proposed = "proposed"
    research = "research"
    proof_of_concept = "proof_of_concept"
    active_development = "active_development"
    deployed = "deployed"
    paused = "paused"
    abandoned = "abandoned"
    retired = "retired"
    unknown = "unknown"


class CapabilityMode(str, Enum):
    full = "full"  # LLM available and used
    deterministic = "deterministic"  # no LLM configured (demo mode)
    degraded = "degraded"  # LLM configured but failed; deterministic fallback used


class IdeaUnderstanding(BaseModel):
    summary: str
    objective: str
    capabilities: list[str]
    target_users: list[str]
    technologies: list[str]
    alternative_terms: list[str]
    search_queries: list[str]
    concepts: list[str] = Field(default_factory=list, description="Concept labels detected by the lexicon")
    concept_ids: list[str] = Field(default_factory=list)
    generated_by: str = "deterministic"


class DimensionScore(BaseModel):
    name: str
    label: str
    weight: float
    score: float | None  # None = insufficient information
    explanation: str


class EvidenceItem(BaseModel):
    record_id: str
    source: SourceSystem
    source_label: str
    record_type: str
    external_key: str
    title: str
    url: str
    snippet: str
    author: str | None = None
    owner: str | None = None
    source_status: str | None = None
    updated_at: datetime
    matched: bool = Field(description="True if retrieved by the search; False if pulled in via a cross-reference")
    match_reason: str | None = None
    link_reason: str | None = None
    keyword_score: float = 0.0
    semantic_score: float = 0.0


class OwnerInfo(BaseModel):
    name: str
    email: str | None = None
    role: str | None = None
    team: str | None = None
    provenance: str
    provenance_record_id: str | None = None


class LifecycleAssessment(BaseModel):
    stage: LifecycleStage
    label: str
    confidence: str  # high | medium | low
    last_activity_at: datetime | None
    days_since_activity: int | None
    signals: list[str]
    caveats: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    type: str  # contact_owner | evaluate_existing | request_reuse | scope_discussion | extend_initiative | register_idea | review_history | proceed
    label: str
    detail: str
    priority: int = 1
    target_initiative_id: str | None = None


class InitiativeMatch(BaseModel):
    initiative_id: str
    name: str
    kind: str = "initiative"  # initiative | registered_idea | unindexed
    department: str | None = None
    team: str | None = None
    description: str | None = None
    business_objective: str | None = None
    core_features: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    owner: OwnerInfo | None = None
    lifecycle: LifecycleAssessment
    category: OverlapCategory
    category_label: str
    overall_score: float
    retrieval_score: float
    dimensions: list[DimensionScore]
    shared_capabilities: list[str]
    idea_only_capabilities: list[str]
    initiative_only_capabilities: list[str]
    reusable_components: list[str] = Field(default_factory=list)
    explanation: str
    explanation_generated_by: str = "deterministic"
    llm_adjustment: str | None = None
    evidence: list[EvidenceItem]
    sources_with_evidence: list[SourceSystem]
    recommendations: list[Recommendation]
    related_initiatives: list[dict[str, str]] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)


class SourceSearchSummary(BaseModel):
    source: SourceSystem
    label: str
    status: str
    records_found: int
    duration_ms: int
    error: str | None = None
    filtered_by_permissions: int = 0
    mode: str = "mock"


class Verdict(BaseModel):
    category: OverlapCategory
    category_label: str
    headline: str
    summary: str
    primary_recommendation: Recommendation
    can_register: bool
    requires_acknowledgement: bool


class AnalysisTotals(BaseModel):
    sources_requested: int
    sources_searched: int
    sources_failed: int
    queries_executed: int
    records_retrieved: int
    unique_records: int
    initiatives_identified: int
    relevant_initiatives: int


class AnalysisReport(BaseModel):
    analysis_id: str
    created_at: datetime
    completed_at: datetime
    duration_ms: int
    idea: IdeaInput
    understanding: IdeaUnderstanding
    capability_mode: CapabilityMode
    llm_provider: str
    embedding_provider: str
    data_mode: str = "mock"
    sources: list[SourceSearchSummary]
    totals: AnalysisTotals
    verdict: Verdict
    matches: list[InitiativeMatch]
    unlinked_evidence: list[EvidenceItem]
    limitations: list[str]
    warnings: list[str]
    scoring_method: dict[str, Any]


class ProgressEvent(BaseModel):
    seq: int
    stage: str
    status: str  # started | completed | failed | info
    label: str
    detail: str | None = None
    source: SourceSystem | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    at: datetime


class AnalysisSummary(BaseModel):
    id: str
    title: str | None
    idea_text: str
    status: str
    capability_mode: str | None
    top_category: str | None
    top_initiative_name: str | None
    scenario_id: str | None
    created_at: datetime
    duration_ms: int | None


class AnalysisCreated(BaseModel):
    id: str
    status: str
    events_url: str
    report_url: str
