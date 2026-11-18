// Typed API contracts mirroring backend/app/schemas (Pydantic).

export type SourceSystem = "confluence" | "jira" | "github" | "sharepoint" | "teams" | "servicenow" | "idea_registry";
export type OverlapCategory = "near_duplicate" | "strong_overlap" | "partial_overlap" | "related" | "no_significant_match";
export type LifecycleStage =
  | "proposed" | "research" | "proof_of_concept" | "active_development" | "deployed" | "paused" | "abandoned" | "retired" | "unknown";
export type CapabilityMode = "full" | "deterministic" | "degraded";

export interface IdeaInput {
  description: string;
  title?: string | null;
  business_problem?: string | null;
  proposed_functionality?: string | null;
  target_users?: string | null;
  department?: string | null;
  team?: string | null;
  technologies?: string | null;
}

export interface AnalysisRequest {
  idea: IdeaInput;
  sources?: SourceSystem[] | null;
  scenario_id?: string | null;
  simulate_failures?: SourceSystem[];
}

export interface IdeaUnderstanding {
  summary: string;
  objective: string;
  capabilities: string[];
  target_users: string[];
  technologies: string[];
  alternative_terms: string[];
  search_queries: string[];
  concepts: string[];
  concept_ids: string[];
  generated_by: string;
}

export interface DimensionScore { name: string; label: string; weight: number; score: number | null; explanation: string }

export interface EvidenceItem {
  record_id: string;
  source: SourceSystem;
  source_label: string;
  record_type: string;
  external_key: string;
  title: string;
  url: string;
  snippet: string;
  author?: string | null;
  owner?: string | null;
  source_status?: string | null;
  updated_at: string;
  matched: boolean;
  match_reason?: string | null;
  link_reason?: string | null;
  keyword_score: number;
  semantic_score: number;
}

export interface OwnerInfo { name: string; email?: string | null; role?: string | null; team?: string | null; provenance: string; provenance_record_id?: string | null }

export interface LifecycleAssessment {
  stage: LifecycleStage;
  label: string;
  confidence: "high" | "medium" | "low";
  last_activity_at?: string | null;
  days_since_activity?: number | null;
  signals: string[];
  caveats: string[];
}

export interface Recommendation { type: string; label: string; detail: string; priority: number; target_initiative_id?: string | null }

export interface InitiativeMatch {
  initiative_id: string;
  name: string;
  kind: "initiative" | "registered_idea" | "unindexed";
  department?: string | null;
  team?: string | null;
  description?: string | null;
  business_objective?: string | null;
  core_features: string[];
  target_users: string[];
  technologies: string[];
  owner?: OwnerInfo | null;
  lifecycle: LifecycleAssessment;
  category: OverlapCategory;
  category_label: string;
  overall_score: number;
  retrieval_score: number;
  dimensions: DimensionScore[];
  shared_capabilities: string[];
  idea_only_capabilities: string[];
  initiative_only_capabilities: string[];
  reusable_components: string[];
  explanation: string;
  explanation_generated_by: string;
  llm_adjustment?: string | null;
  evidence: EvidenceItem[];
  sources_with_evidence: SourceSystem[];
  recommendations: Recommendation[];
  related_initiatives: { id: string; name: string; reason: string }[];
  uncertainty: string[];
}

export interface SourceSearchSummary {
  source: SourceSystem; label: string; status: string; records_found: number; duration_ms: number;
  error?: string | null; filtered_by_permissions: number; mode: string;
}

export interface Verdict {
  category: OverlapCategory; category_label: string; headline: string; summary: string;
  primary_recommendation: Recommendation; can_register: boolean; requires_acknowledgement: boolean;
}

export interface AnalysisReport {
  analysis_id: string;
  created_at: string;
  completed_at: string;
  duration_ms: number;
  idea: IdeaInput;
  understanding: IdeaUnderstanding;
  capability_mode: CapabilityMode;
  llm_provider: string;
  embedding_provider: string;
  data_mode: string;
  sources: SourceSearchSummary[];
  totals: {
    sources_requested: number; sources_searched: number; sources_failed: number; queries_executed: number;
    records_retrieved: number; unique_records: number; initiatives_identified: number; relevant_initiatives: number;
  };
  verdict: Verdict;
  matches: InitiativeMatch[];
  unlinked_evidence: EvidenceItem[];
  limitations: string[];
  warnings: string[];
  scoring_method: Record<string, unknown>;
}

export interface ProgressEvent {
  seq: number;
  stage: string;
  status: "started" | "completed" | "failed" | "info";
  label: string;
  detail?: string | null;
  source?: SourceSystem | null;
  data: Record<string, unknown>;
  at: string;
}

export interface AnalysisEnvelope {
  id: string;
  status: "running" | "completed" | "failed";
  error?: string | null;
  request: AnalysisRequest;
  report: AnalysisReport | null;
  events: ProgressEvent[];
  created_at: string;
  completed_at?: string | null;
}

export interface AnalysisSummary {
  id: string; title?: string | null; idea_text: string; status: string; capability_mode?: string | null;
  top_category?: OverlapCategory | null; top_initiative_name?: string | null; scenario_id?: string | null;
  created_at: string; duration_ms?: number | null;
}

export interface RegisteredIdea {
  id: string; title: string; description: string; business_problem?: string | null; proposed_functionality?: string | null;
  target_users?: string | null; department?: string | null; team?: string | null; technologies?: string | null;
  submitted_by: string; status: string; analysis_id?: string | null;
  related_initiatives: { id: string; name: string; type: string; owner?: string | null; status?: string }[];
  acknowledged_overlap?: { initiatives: string[]; note?: string | null; acknowledged_at: string } | null;
  created_at: string; updated_at: string;
}

export interface RegistrationBlocked { detail: string; analysis_id: string; overlapping: { id: string; name: string; category: OverlapCategory; owner?: string | null }[] }

export interface ConnectorHealth {
  source: SourceSystem; display_name: string; status: "ok" | "error" | "timeout" | "disabled"; mode: string; read_only: boolean;
  record_count: number; record_types: Record<string, number>; last_indexed_at?: string | null; description: string; error?: string | null;
}

export interface SourcesOverview { data_mode: string; sources: ConnectorHealth[]; total_records: number }

export interface SourceRecordRow {
  id: string; source: SourceSystem; record_type: string; external_key: string; title: string; content: string; url: string;
  author?: string | null; owner?: string | null; source_status?: string | null; updated_at: string; labels: string[]; links: string[];
  metadata: Record<string, unknown>; acl: Record<string, unknown>; initiative_id?: string | null; link_reason?: string | null; restricted: boolean;
}

export interface InitiativeSummary {
  id: string; name: string; department: string; team: string; owner_name?: string | null; status: LifecycleStage;
  description: string; last_activity_at: string; created_at: string; record_count: number; sources: SourceSystem[];
}

export interface InitiativeDetail extends InitiativeSummary {
  aliases: string[]; business_objective: string; core_features: string[]; target_users: string[]; technologies: string[];
  reusable_components: string[]; notes?: string | null; owner_email?: string | null;
  records: (SourceRecordRow & { link_reason: string })[];
  related: { id: string; name: string; type: string; reason: string }[];
}

export interface GraphNode { id: string; label: string; type: "initiative" | "team" | "person" | "record" | "idea"; group?: string | null; meta: Record<string, unknown> }
export interface GraphEdge { source: string; target: string; type: string }
export interface GraphResponse { nodes: GraphNode[]; edges: GraphEdge[] }

export interface StatsResponse {
  initiatives: number; records: number; sources: number; departments: number; registered_ideas: number; analyses_run: number;
  duplicates_flagged: number; by_status: Record<string, number>; by_department: Record<string, number>; by_source: Record<string, number>;
}

export interface DemoScenario { id: string; case: string; title: string; summary: string; idea: IdeaInput; expected: Record<string, unknown> }

export interface HealthResponse {
  status: string; database: string; llm_provider: string; llm_model?: string | null; embedding_provider: string; data_mode: string;
  failing_sources: string[]; version: string;
}

export interface Comparison {
  analysis_id: string;
  idea: { title: string; description: string; objective: string; capabilities: string[]; target_users: string[]; technologies: string[]; department?: string | null; generated_by: string };
  initiative: InitiativeMatch;
  rows: { aspect: string; idea: string; initiative: string }[];
  shared: string[];
  idea_only: string[];
  initiative_only: string[];
  capability_mode: CapabilityMode;
}
