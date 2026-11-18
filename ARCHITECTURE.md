# Architecture

## Overview

```
 Next.js (App Router, shadcn/ui)                        FastAPI
 ┌──────────────────────────┐   REST + SSE    ┌──────────────────────────────────────────────┐
 │ Dashboard · Submit       │ ─────────────▶  │ api/        analyses · ideas · catalog        │
 │ Live search · Results    │ ◀─ progress ─── │ pipeline/   orchestrator (deterministic)      │
 │ Compare · Print/export   │                 │   understand → retrieve → correlate → overlap │
 │ Registry · Sources/graph │                 │   → lifecycle → (LLM review) → recommend      │
 │ Demo · History           │                 │ connectors/ SourceConnector interface (R/O)   │
 └──────────────────────────┘                 │   Confluence Jira GitHub SharePoint Teams     │
                                              │   ServiceNow (mock)  IdeaRegistry (local)     │
                                              │ ai/         lexicon · embeddings · LLM        │
                                              │ security/   PermissionFilter · Principal      │
                                              └───────────────┬──────────────────────────────┘
                                                              │ SQLAlchemy
                                              PostgreSQL 17 + pgvector (vector(384) columns)
                                              initiatives · source_records · ideas · analyses · audit_log
```

The orchestration is deliberately a fixed, deterministic pipeline rather than a multi-agent framework. Each stage is testable, results are repeatable for demos, and the LLM only *enriches* stages; it never controls the flow.

## Pipeline stages

| # | Stage | Module | What actually happens |
|---|---|---|---|
| 1-2 | Understand idea, generate queries | `pipeline/understand.py` | The domain concept lexicon finds objective, capability, user and technology concepts, plus alternative terminology. Up to 9 queries are built. If an LLM is configured, it adds a summary, synonyms and queries; concepts are re-derived from the LLM's terminology. |
| 3-4 | Search connectors concurrently | `pipeline/retrieve.py` | `asyncio.gather` across connectors, each with its own timeout and try/except. A permission filter is applied to every result set. Per-source start and finish events are emitted. |
| 5 | Normalise / dedupe | `correlate.dedupe` | A record returned for several queries is merged, keeping its best scores. |
| 6 | Correlate into initiatives | `pipeline/correlate.py` | Only source-native evidence is used, in priority order: shared project label, registered key, explicit link, key mention, alias in title, alias in body. Linked but unretrieved records are then pulled in through `fetch_related`, but **only from healthy sources**. Unlinked records are never merged by guesswork. |
| 7 | Hybrid ranking | `connectors/mock_base.py`, `scoring.py` | BM25 over title, labels and body with concept-expanded query terms, plus pgvector cosine (`<=>`), fused with reciprocal rank fusion. |
| 8-9 | Overlap analysis | `pipeline/overlap.py` | 5-dimension scoring with classification guardrails (see below). Sentences that state what a project does *not* do ("Out of scope: real-time scoring") are stripped before concepts are extracted. |
| 10 | Lifecycle | `pipeline/lifecycle.py` | Explicit statuses by authority: ServiceNow lifecycle, then stop and hold signals (Jira "Won't Do", archived repo, Jira "On Hold"), then the stage declared on documents. Jira and GitHub activity confirms but doesn't define the stage. Recency caveats are added (over 6 months: possibly paused; over 12 months: stale). |
| 11 | Optional LLM review | `orchestrator._apply_llm` | The top 5 matches are sent with evidence wrapped in `<retrieved_record>` tags. The output is schema-validated, citations are checked against retrieved IDs, and the category can move by at most one level. |
| 12 | Recommendations and report | `pipeline/recommend.py`, `orchestrator` | Actions depend on category and lifecycle. The verdict, coverage, limitations, warnings and scoring method are included. The report is persisted with its event trace and audit entry. |

### Overlap scoring (a ranking heuristic, not a probability)

| Dimension | Weight | Calculation |
|---|---|---|
| Business objective | 35% | Coverage of the idea's domain concepts by the initiative (60% own description, 40% evidence) × 0.7, plus normalised embedding cosine × 0.3 |
| Core capabilities | 30% | Coverage of the idea's capability concepts |
| Scope | 15% | Weighted Jaccard over domain and capability concepts; penalises much broader or narrower scope |
| Target users | 10% | Coverage of user-group concepts. Skipped if the idea doesn't state any. |
| Technology | 10% | Coverage of technology concepts. Skipped if the idea doesn't state any. |

Classification needs **both** objective and capability alignment to reach the strong categories:

- **Near-duplicate:** objective ≥ 0.80, capabilities ≥ 0.80 and overall ≥ 0.75
- **Strong overlap:** objective ≥ 0.60, capabilities ≥ 0.55 and overall ≥ 0.55
- **Partial overlap:** the domain matches but capabilities differ, or capabilities partly overlap
- **Related:** some objective alignment

There is also a guardrail for ideas with no recognised domain or capability concepts: they can never be classified above Related, whatever their text similarity. Lifecycle never changes the score; it only changes the recommendation.

### Semantic understanding without an LLM

`ai/lexicon.py` holds about 100 weighted concepts, each with alternative enterprise terminology. For example, *SAST*, *static analysis* and *secure code analysis* are one concept; *late feed*, *figures can be trusted* and *schema drift* are another. `LocalConceptEmbedder` feature-hashes concepts and stemmed terms into 384 dimensions. This is an explainable approximation of semantic similarity, not a learned model. With an embedding endpoint configured, the remote model is used instead, with automatic local fallback.

Accuracy is measured by `tests/eval/cases.yaml`: 24 free-form ideas phrased differently from the demo prompts, including false-positive guards. All 24 pass in deterministic mode. New domains need lexicon entries, or a real embedding model.

## Data model

- **`initiatives`:** the *Initiative Index*, a correlated catalogue (in production, built by a scheduled indexing job). It holds name, aliases, correlation keys (labels, Jira epics, repos, catalogue numbers), objective, features, users, technologies, reusable components and an embedding.
- **`source_records`:** normalised records with `labels`, `links`, `extra` metadata, `acl` and an embedding. Records carry no hidden project ID; correlation uses only source-native references.
- **`ideas`:** the Idea Registry, with related initiatives and any acknowledged overlap.
- **`analyses`:** request, final report JSON, event trace, capability mode, and the top category for history.
- **`audit_log`:** who searched what, which sources were searched or failed, and the outcome.

## Connector contract

```python
class SourceConnector(ABC):           # read-only by design: no write methods exist
    source: SourceSystem; mode: "mock" | "live"; read_only = True
    def search(self, request: ConnectorSearchRequest) -> list[NormalizedRecord]
    def fetch_related(self, keys: list[str]) -> list[NormalizedRecord]
    def health(self) -> ConnectorHealth
```

To add a real integration, implement the class with the system's approved read-only API (for example Confluence CQL, Jira JQL, GitHub search or the ServiceNow Table API), map the responses into `NormalizedRecord`, and register it in `connectors/registry.py`. The pipeline doesn't change.

## Security posture: what the PoC does and doesn't do

Implemented:
- Read-only connector interface.
- Per-record ACL metadata, with a `PermissionFilter` applied after retrieval and during expansion. Restricted records are hidden and counted in the limitations. Restricted content is redacted in the Source Explorer.
- Teams indexing is limited to channels flagged `authorized_for_indexing`. Private chats are not modelled and are never searched.
- Retrieved content is treated as untrusted data: it's delimited in prompts, outputs are schema-validated, citations are verified, and LLM category changes are bounded.
- Secrets come only from environment variables. All data is synthetic, and URLs use the reserved `.example` domain.
- An audit log covers every search and registration.

**Not implemented (required for production):**
- Authentication and SSO: every request runs as a placeholder principal. There is **no production-grade authorisation**.
- Real per-user security trimming against each source's permission model.
- Data retention policies, PII handling, rate limiting and encryption at rest beyond Postgres defaults.

## Path to production

1. Add SSO (OIDC or SAML) and map the user to a `Principal` with group memberships.
2. Replace mock connectors with service-account read-only integrations using delegated or security-trimmed queries, plus incremental indexing.
3. Build the Initiative Index with a scheduled correlation job, and give initiative owners a curation UI.
4. Use an enterprise embedding model and LLM gateway (both already pluggable). Re-run the evaluation set and extend it with labelled internal cases.
5. Add monitoring, rate limits, retention rules and data-protection review. Treat the Idea Registry as a system of record, with workflow states.
