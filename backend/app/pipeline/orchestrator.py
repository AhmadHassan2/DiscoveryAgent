"""Deterministic orchestration of the idea-validation pipeline.

    understand -> generate queries -> search connectors (concurrently) -> normalise/dedupe
    -> correlate into initiatives -> expand cross-references -> hybrid rank -> overlap analysis
    -> lifecycle -> (optional) LLM assessment -> recommendations -> report

Every stage emits a real progress event, streamed to the UI over SSE. Counts in events come
from actual connector results.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

from app.ai.embeddings import get_embedder
from app.ai.provider import LLMAssessmentBatch, LLMError, LLMProvider, get_llm
from app.config import get_settings
from app.connectors.registry import all_connectors, get_connectors
from app.db.models import Analysis, Idea, Initiative
from app.db.session import SessionLocal
from app.pipeline import lifecycle as lifecycle_mod
from app.pipeline import recommend
from app.pipeline.correlate import Candidate, correlate, dedupe, expand
from app.pipeline.events import bus
from app.pipeline.overlap import SCORING_METHOD, analyse
from app.pipeline.retrieve import search_all
from app.pipeline.understand import understand
from app.repositories.analyses import AuditRepository
from app.repositories.records import InitiativeRepository
from app.schemas.analysis import (
    CATEGORY_LABELS,
    CATEGORY_RANK,
    AnalysisReport,
    AnalysisRequest,
    AnalysisTotals,
    CapabilityMode,
    EvidenceItem,
    InitiativeMatch,
    LifecycleStage,
    OverlapCategory,
    OwnerInfo,
    SourceSearchSummary,
    Verdict,
)
from app.schemas.records import SOURCE_LABELS, ConnectorResult, ConnectorSearchRequest, NormalizedRecord, SearchQuery, SourceSystem
from app.security.access import default_principal

log = logging.getLogger(__name__)

MAX_MATCHES = 8
MAX_RELATED = 3
LLM_MAX_CANDIDATES = 5
SOURCE_AUTHORITY = {"servicenow": 0, "jira": 1, "github": 2, "confluence": 3, "sharepoint": 4, "teams": 5, "idea_registry": 6}


# ----------------------------------------------------------------------------------- helpers
def _evidence_item(rec: NormalizedRecord, matched: bool, reason: str | None) -> EvidenceItem:
    snippet = rec.content if len(rec.content) <= 260 else rec.content[:257].rsplit(" ", 1)[0] + "…"
    match_reason = None
    if matched:
        bits = []
        if rec.keyword_score >= 0.18:
            bits.append(f"keyword match {rec.keyword_score:.2f}")
        if rec.semantic_score >= 0.22:
            bits.append(f"semantic similarity {rec.semantic_score:.2f}")
        match_reason = "Retrieved by search (" + ", ".join(bits) + ")" if bits else "Retrieved by search"
    return EvidenceItem(
        record_id=rec.id, source=rec.source, source_label=SOURCE_LABELS[rec.source.value], record_type=rec.record_type,
        external_key=rec.external_key, title=rec.title, url=rec.url, snippet=snippet, author=rec.author, owner=rec.owner,
        source_status=rec.source_status, updated_at=rec.updated_at, matched=matched, match_reason=match_reason,
        link_reason=reason, keyword_score=rec.keyword_score, semantic_score=rec.semantic_score,
    )


def _derive_owner(c: Candidate) -> OwnerInfo | None:
    """Owner comes ONLY from source records (with provenance), falling back to the Initiative Index."""
    init = c.initiative
    records = [e.record for e in c.evidence.values()]
    if c.kind == "registered_idea":
        r = records[0]
        return OwnerInfo(name=r.owner or "Unknown", role="Idea submitter", team=r.metadata.get("team"),
                         provenance=f"Idea Registry {r.external_key}", provenance_record_id=r.id)
    priorities = [
        (lambda r: r.source.value == "servicenow" and r.record_type in ("catalog_item", "application") and (r.metadata.get("service_owner") or r.owner), "Service owner"),
        (lambda r: r.source.value == "jira" and r.record_type == "epic" and r.owner, "Jira epic owner"),
        (lambda r: r.source.value == "github" and r.record_type == "repository" and (r.metadata.get("maintainers") or r.owner), "Repository maintainer"),
        (lambda r: r.source.value == "confluence" and r.owner, "Confluence page owner"),
        (lambda r: r.source.value == "sharepoint" and r.owner, "Document owner"),
    ]
    for pred, role in priorities:
        for r in sorted(records, key=lambda r: r.updated_at, reverse=True):
            if pred(r):
                name = r.metadata.get("service_owner") or (r.metadata.get("maintainers") or [None])[0] or r.owner
                email = init.owner_email if init and init.owner_name == name else None
                return OwnerInfo(name=name, email=email, role=role, team=init.team if init else None,
                                 provenance=f"{SOURCE_LABELS[r.source.value]} {r.external_key}", provenance_record_id=r.id)
    if init and init.owner_name:
        return OwnerInfo(name=init.owner_name, email=init.owner_email, role="Initiative owner", team=init.team,
                         provenance="Initiative Index (not confirmed by a retrieved record)")
    return None


def _match_name(c: Candidate) -> str:
    if c.initiative:
        return c.initiative.name
    return next(iter(c.evidence.values())).record.title


# ----------------------------------------------------------------------------------- LLM step
def _llm_prompt(understanding_text: str, matches: list[InitiativeMatch]) -> str:
    blocks = []
    for m in matches:
        facts = [f"Initiative ID: {m.initiative_id}", f"Name: {m.name}", f"Department: {m.department or 'unknown'}",
                 f"Lifecycle (derived): {m.lifecycle.label}", f"Description: {m.description or 'n/a'}",
                 f"Objective: {m.business_objective or 'n/a'}", f"Features: {'; '.join(m.core_features) or 'n/a'}",
                 f"Rule-based category: {m.category.value} (objective/capability scores: "
                 + ", ".join(f"{d.name}={d.score}" for d in m.dimensions) + ")"]
        recs = "\n".join(
            f'<retrieved_record id="{e.record_id}" source="{e.source_label}" key="{e.external_key}">\n{e.title}\n{e.snippet}\n</retrieved_record>'
            for e in m.evidence[:5]
        )
        blocks.append("<initiative>\n" + "\n".join(facts) + "\n" + recs + "\n</initiative>")
    return (
        "An employee proposed the idea below. For EACH initiative, assess how much it overlaps with the idea. "
        "Use only the provided evidence. Categories: near_duplicate, strong_overlap, partial_overlap, related, no_significant_match. "
        "A shared domain with different core functionality is partial_overlap or related, not a duplicate. "
        "Cite only record IDs that appear in the retrieved_record tags.\n\n"
        f"<idea>\n{understanding_text}\n</idea>\n\n" + "\n\n".join(blocks)
    )


def _apply_llm(llm: LLMProvider, idea_text: str, matches: list[InitiativeMatch], warnings: list[str]) -> None:
    targets = [m for m in matches if m.kind != "unindexed"][:LLM_MAX_CANDIDATES]
    if not targets:
        return
    batch = llm.structured(_llm_prompt(idea_text, targets), LLMAssessmentBatch, max_tokens=6000)
    by_id = {m.initiative_id: m for m in targets}
    dropped = 0
    for a in batch.assessments:
        m = by_id.get(a.initiative_id)
        if m is None:
            continue
        valid_ids = {e.record_id for e in m.evidence}
        cited = [c for c in a.cited_record_ids if c in valid_ids]
        dropped += len(a.cited_record_ids) - len(cited)
        try:
            llm_cat = OverlapCategory(a.category)
        except ValueError:
            llm_cat = m.category
        if llm_cat != m.category:
            if abs(CATEGORY_RANK[llm_cat] - CATEGORY_RANK[m.category]) <= 1:
                m.llm_adjustment = f"AI review adjusted the category from {CATEGORY_LABELS[m.category]} to {CATEGORY_LABELS[llm_cat]}."
                m.category, m.category_label = llm_cat, CATEGORY_LABELS[llm_cat]
            else:
                m.llm_adjustment = (f"AI review suggested {CATEGORY_LABELS[llm_cat]}, which differs from the rule-based result by more than "
                                    f"one level. The rule-based {CATEGORY_LABELS[m.category]} is kept.")
        text = a.explanation.strip()
        if a.differences:
            text += " Key differences: " + "; ".join(a.differences[:4]) + "."
        if a.reuse_opportunities:
            text += " Reuse opportunities: " + "; ".join(a.reuse_opportunities[:3]) + "."
        if cited:
            text += " [Evidence: " + ", ".join(cited) + "]"
        m.explanation = text
        m.explanation_generated_by = f"llm:{llm.model}"
    if dropped:
        warnings.append(f"Dropped {dropped} AI citation(s) that did not match retrieved records.")


# ----------------------------------------------------------------------------------- pipeline
async def run_analysis(analysis_id: str, request: AnalysisRequest, requester: str) -> AnalysisReport:
    started = time.perf_counter()
    created_at = datetime.now(timezone.utc)
    settings = get_settings()
    emit = lambda *a, **k: bus.emit(analysis_id, *a, **k)  # noqa: E731
    warnings: list[str] = []
    llm = get_llm()
    llm_failed = False

    # 1-2. Understand idea --------------------------------------------------------------------
    emit("understand", "started", "Understanding idea",
         "Using " + (f"{llm.name} ({llm.model})" if llm else "deterministic concept analysis"))
    understanding, llm_err = await asyncio.to_thread(understand, request.idea, llm)
    if llm_err:
        llm_failed = True
        warnings.append(f"AI idea analysis failed; deterministic analysis used instead ({llm_err[:160]}).")
    emit("understand", "completed", "Understanding idea", understanding.objective,
         data={"concepts": understanding.concepts[:8], "capabilities": understanding.capabilities[:6]})
    emit("queries", "completed", "Generating search terms", f"{len(understanding.search_queries)} queries, {len(understanding.alternative_terms)} alternative terms",
         data={"queries": understanding.search_queries, "alternative_terms": understanding.alternative_terms})

    embedder = get_embedder()
    idea_vec = (await asyncio.to_thread(embedder.embed, [request.idea.full_text() + " " + " ".join(understanding.alternative_terms)]))[0]

    # 3-4. Search connectors concurrently -----------------------------------------------------
    connectors = get_connectors(request.sources)
    search_req = ConnectorSearchRequest(
        queries=[SearchQuery(text=q, kind="primary" if i == 0 else "expansion") for i, q in enumerate(understanding.search_queries)],
        expansion_terms=understanding.alternative_terms, query_embedding=idea_vec, limit=10,
    )

    def on_start(src: SourceSystem) -> None:
        emit(f"search:{src.value}", "started", f"Searching {SOURCE_LABELS[src.value]}", source=src)

    def on_done(res: ConnectorResult) -> None:
        label = f"Searching {SOURCE_LABELS[res.source.value]}"
        if res.status.value == "ok":
            detail = f"{len(res.records)} relevant record(s) in {res.duration_ms} ms"
            if res.filtered_by_permissions:
                detail += f"; {res.filtered_by_permissions} hidden by access controls"
            emit(f"search:{res.source.value}", "completed", label, detail, source=res.source,
                 data={"records": len(res.records), "filtered": res.filtered_by_permissions, "duration_ms": res.duration_ms})
        else:
            emit(f"search:{res.source.value}", "failed", label, res.error, source=res.source, data={"duration_ms": res.duration_ms})

    forced = {s.value for s in request.simulate_failures}
    results = await search_all(connectors, search_req, default_principal(requester), forced, on_start, on_done)
    ok_results = [r for r in results if r.status.value == "ok"]
    failed = [r for r in results if r.status.value != "ok"]
    raw_records = [rec for r in ok_results for rec in r.records]

    # 5-6. Normalise, dedupe and correlate -------------------------------------------------
    emit("correlate", "started", "Correlating records", f"{len(raw_records)} records from {len(ok_results)} source(s)")
    records = dedupe(raw_records)
    with SessionLocal() as db:
        initiatives = InitiativeRepository(db).list()
        idea_rows = {i.id: i for i in db.query(Idea).all()}
    candidates, unlinked = correlate(records, initiatives)
    # Expand: pull linked records via connectors that are up (never from failed sources)
    keys = sorted({k for c in candidates if c.initiative for k in (c.initiative.correlation_keys or [])})
    healthy = [c for c in connectors if c.source in {r.source for r in ok_results} and c.source != SourceSystem.idea_registry]
    related_lists = await asyncio.gather(*(asyncio.to_thread(c.fetch_related, keys) for c in healthy)) if keys else []
    from app.security.access import MockPermissionFilter

    related_allowed, _ = MockPermissionFilter().filter([r for lst in related_lists for r in lst], default_principal(requester))
    expand(candidates, related_allowed, initiatives)
    linked = sum(1 for c in candidates for e in c.evidence.values() if not e.matched)
    emit("correlate", "completed", "Correlating records",
         f"{len(records)} unique records grouped into {len(candidates)} candidate initiative(s); {linked} linked record(s) added via cross-references",
         data={"unique_records": len(records), "candidates": len(candidates), "linked_records": linked, "unlinked": len(unlinked)})

    # 7-10. Rank, analyse overlap, lifecycle ---------------------------------------------------
    emit("analyze", "started", "Analyzing project overlap", f"Scoring {len(candidates)} candidate(s) on 5 dimensions")
    matches: list[InitiativeMatch] = []
    now = datetime.now(timezone.utc)
    for c in sorted(candidates, key=lambda c: -c.retrieval_score):
        result = analyse(request.idea, understanding, idea_vec, c)
        recs = [e.record for e in c.evidence.values()]
        idea_row = idea_rows.get(c.key) if c.kind == "registered_idea" else None
        life = lifecycle_mod.assess(recs, c.initiative, now=now, registered_status=idea_row.status if idea_row else None)
        init = c.initiative
        evidence = sorted((_evidence_item(e.record, e.matched, e.reason) for e in c.evidence.values()),
                          key=lambda e: (not e.matched, SOURCE_AUTHORITY[e.source.value], -e.semantic_score))
        uncertainty = list(life.caveats)
        sources = sorted({e.source for e in evidence}, key=lambda s: SOURCE_AUTHORITY[s.value])
        if len(sources) == 1 and c.kind == "initiative":
            uncertainty.append("Evidence found in a single source only.")
        if c.kind == "unindexed":
            uncertainty.append("Not in the Initiative Index; grouped only by cross-references between records.")
        owner = _derive_owner(c)
        if owner is None:
            uncertainty.append("No owner could be identified from the available records.")
        m = InitiativeMatch(
            initiative_id=c.key, name=_match_name(c), kind=c.kind,
            department=init.department if init else (idea_row.department if idea_row else None),
            team=init.team if init else (idea_row.team if idea_row else None),
            description=init.description if init else (idea_row.description if idea_row else recs[0].content[:400]),
            business_objective=init.business_objective if init else None,
            core_features=list(init.core_features or []) if init else [],
            target_users=list(init.target_users or []) if init else [],
            technologies=list(init.technologies or []) if init else [],
            owner=owner, lifecycle=life, category=result.category, category_label=CATEGORY_LABELS[result.category],
            overall_score=result.overall, retrieval_score=c.retrieval_score, dimensions=result.dimensions,
            shared_capabilities=result.shared, idea_only_capabilities=result.idea_only, initiative_only_capabilities=result.initiative_only,
            reusable_components=list(init.reusable_components or []) if init else [],
            explanation=_deterministic_explanation(c, result, life.label), evidence=evidence, sources_with_evidence=sources,
            recommendations=[], uncertainty=uncertainty,
        )
        matches.append(m)

    matches = [m for m in matches if m.category != OverlapCategory.no_significant_match]
    matches.sort(key=_rank_key)
    strongish = [m for m in matches if CATEGORY_RANK[m.category] >= 2]
    related = [m for m in matches if m.category == OverlapCategory.related][:MAX_RELATED]
    matches = (strongish + related)[:MAX_MATCHES]
    emit("analyze", "completed", "Analyzing project overlap",
         f"{len(strongish)} initiative(s) with partial or stronger overlap; {len(related)} related",
         data={"top": [{"name": m.name, "category": m.category.value, "score": m.overall_score} for m in matches[:5]]})

    # Optional LLM review ----------------------------------------------------------------------
    if llm and matches:
        emit("ai_review", "started", "AI review of top matches", f"{llm.name} ({llm.model})")
        try:
            await asyncio.to_thread(_apply_llm, llm, request.idea.full_text(), matches, warnings)
            emit("ai_review", "completed", "AI review of top matches", "Explanations generated; categories validated against rules")
        except (LLMError, Exception) as exc:
            llm_failed = True
            warnings.append(f"AI review failed; rule-based explanations shown ({str(exc)[:160]}).")
            emit("ai_review", "failed", "AI review of top matches", "Fell back to rule-based explanations")
        matches.sort(key=_rank_key)

    # 11-12. Recommendations and report ------------------------------------------------------
    emit("report", "started", "Preparing results")
    _link_related(matches, idea_rows)
    for m in matches:
        m.recommendations = recommend.for_match(m)
    top_cat = matches[0].category if matches else OverlapCategory.no_significant_match
    primary = recommend.primary(matches)
    capability_mode = CapabilityMode.deterministic if llm is None else (CapabilityMode.degraded if llm_failed else CapabilityMode.full)

    limitations = _limitations(results, connectors, capability_mode, unlinked)
    totals = AnalysisTotals(
        sources_requested=len(connectors), sources_searched=len(ok_results), sources_failed=len(failed),
        queries_executed=len(search_req.queries) * len(ok_results), records_retrieved=len(raw_records), unique_records=len(records),
        initiatives_identified=len(candidates), relevant_initiatives=len([m for m in matches if CATEGORY_RANK[m.category] >= 2]),
    )
    verdict = _verdict(top_cat, matches, primary, failed)
    llm_name, llm_model = (llm.name, llm.model) if llm else ("deterministic", None)
    completed = datetime.now(timezone.utc)
    report = AnalysisReport(
        analysis_id=analysis_id, created_at=created_at, completed_at=completed, duration_ms=int((time.perf_counter() - started) * 1000),
        idea=request.idea, understanding=understanding, capability_mode=capability_mode,
        llm_provider=f"{llm_name}:{llm_model}" if llm_model else llm_name, embedding_provider=embedder.last_used,
        data_mode="mock",
        sources=[SourceSearchSummary(source=r.source, label=SOURCE_LABELS[r.source.value], status=r.status.value, records_found=len(r.records),
                                     duration_ms=r.duration_ms, error=r.error, filtered_by_permissions=r.filtered_by_permissions, mode=r.mode)
                 for r in results],
        totals=totals, verdict=verdict, matches=matches,
        unlinked_evidence=[_evidence_item(r, True, "No cross-reference to a known initiative") for r in sorted(unlinked, key=lambda r: -r.fused_score)[:5]],
        limitations=limitations, warnings=warnings, scoring_method=SCORING_METHOD,
    )
    emit("report", "completed", "Preparing results", verdict.headline, data={"category": top_cat.value})
    return report


def _rank_key(m: InitiativeMatch):
    # Category first; within a category, real initiatives before registered ideas, then score.
    return (-CATEGORY_RANK[m.category], m.kind == "registered_idea", -m.overall_score)


def _deterministic_explanation(c: Candidate, result, stage_label: str) -> str:
    name = _match_name(c)
    parts = []
    if c.kind == "registered_idea":
        parts.append(f"'{name}' is an idea already registered in the Idea Registry.")
    else:
        parts.append(f"{name} is in {stage_label.lower()} according to the source evidence.")
    if result.shared:
        parts.append("Overlapping functionality: " + "; ".join(result.shared[:4]) + ".")
    if result.idea_only:
        parts.append("Your idea also covers " + ", ".join(result.idea_only[:3]).lower() + ", with no evidence of this in the initiative.")
    if result.initiative_only and c.kind == "initiative":
        parts.append("The initiative also includes: " + "; ".join(result.initiative_only[:3]) + ".")
    parts.append(result.rationale)
    return " ".join(parts)


def _link_related(matches: list[InitiativeMatch], idea_rows: dict[str, Idea]) -> None:
    ids = {m.initiative_id for m in matches}
    for m in matches:
        rel = []
        for other in matches:
            if other is m or CATEGORY_RANK[other.category] < 2 or CATEGORY_RANK[m.category] < 2:
                continue
            if other.kind == "registered_idea":
                continue
            rel.append({"id": other.initiative_id, "name": other.name, "reason": "Also overlaps with this idea; the two teams may want to coordinate"})
        for idea in idea_rows.values():
            if m.initiative_id in (idea.related_initiative_ids or []) and idea.id not in ids:
                rel.append({"id": idea.id, "name": idea.title, "reason": f"Registered idea {idea.id} references this initiative"})
        m.related_initiatives = rel[:5]


def _limitations(results: list[ConnectorResult], connectors, mode: CapabilityMode, unlinked) -> list[str]:
    lim = [
        "Results come from simulated (mock) enterprise systems populated with synthetic data. They are not connected to live Confluence, Jira, GitHub, SharePoint, Teams or ServiceNow.",
        "Only the sources listed were searched. Initiatives that are documented elsewhere, or not documented at all, cannot be found.",
        "No match does not prove that no similar work exists. It means none was found in the sources searched.",
        "Similarity scores are ranking heuristics, not calibrated probabilities.",
    ]
    searched = {c.source for c in connectors}
    skipped = [SOURCE_LABELS[s.value] for s in all_connectors() if s not in searched]
    if skipped:
        lim.insert(1, "Sources excluded from this search: " + ", ".join(skipped) + ".")
    failed = [SOURCE_LABELS[r.source.value] for r in results if r.status.value != "ok"]
    if failed:
        lim.insert(0, "Search not comprehensive: " + ", ".join(failed) + " could not be searched (unavailable).")
    hidden = sum(r.filtered_by_permissions for r in results)
    if hidden:
        lim.append(f"{hidden} record(s) were hidden because you are not authorised to see them, so related restricted work may exist.")
    if mode == CapabilityMode.deterministic:
        lim.append("AI analysis ran in deterministic demo mode (no LLM configured). Explanations are rule-based.")
    elif mode == CapabilityMode.degraded:
        lim.append("The configured LLM failed during this analysis. Rule-based results are shown, with reduced capability.")
    lim.append("Teams content is limited to project channels authorised for indexing. Private conversations are never searched.")
    return lim


def _verdict(top: OverlapCategory, matches: list[InitiativeMatch], primary, failed) -> Verdict:
    lead = matches[0] if matches else None
    caveat = " Some sources were unavailable, so this result may be incomplete." if failed else ""
    if top in (OverlapCategory.near_duplicate, OverlapCategory.strong_overlap) and lead:
        stage = lead.lifecycle.stage
        if stage == LifecycleStage.deployed:
            headline = f"An existing deployed solution already covers this idea: {lead.name}"
        elif stage in (LifecycleStage.abandoned, LifecycleStage.retired):
            headline = f"This idea was tried before: {lead.name} ({lead.lifecycle.label.lower()})"
        else:
            headline = f"{lead.name} already covers most of this idea"
        if lead.kind == "registered_idea":
            headline = f"A similar idea is already registered: {lead.name}"
        summary = (f"{lead.category_label} with {lead.name}"
                   + (f" ({lead.department})" if lead.department else "")
                   + f". Lifecycle: {lead.lifecycle.label}. Evidence from {len(lead.sources_with_evidence)} source(s). "
                   "Talk to the existing team before starting separate development." + caveat)
    elif top == OverlapCategory.partial_overlap and lead:
        headline = f"Partial overlap with {lead.name}. Related work exists, but it doesn't fully cover your idea"
        summary = "Some functionality overlaps, but the core scope differs. Agree the boundary with the existing team and reuse what you can." + caveat
    elif top == OverlapCategory.related and lead:
        headline = "No significant overlap found. Some related initiatives exist"
        summary = ("The initiatives found share terminology or a broad domain but solve different problems. "
                   "You can register the idea and proceed through the normal approval process." + caveat)
    else:
        headline = "No significant overlap found in the sources searched"
        summary = ("No initiative matching this idea was found in the available sources. That does not prove none exists. "
                   "Register the idea so others can find it, and proceed through the normal approval process." + caveat)
    return Verdict(category=top, category_label=CATEGORY_LABELS[top], headline=headline, summary=summary,
                   primary_recommendation=primary, can_register=True,
                   requires_acknowledgement=top in (OverlapCategory.near_duplicate, OverlapCategory.strong_overlap))


# ----------------------------------------------------------------------------------- persistence wrapper
async def execute_and_store(analysis_id: str, request: AnalysisRequest, requester: str) -> None:
    started = time.perf_counter()
    try:
        report = await run_analysis(analysis_id, request, requester)
        with SessionLocal() as db:
            a = db.get(Analysis, analysis_id)
            if a:
                a.status = "completed"
                a.report = report.model_dump(mode="json")
                a.capability_mode = report.capability_mode.value
                a.top_category = report.verdict.category.value
                a.top_initiative_name = report.matches[0].name if report.matches else None
                a.completed_at = report.completed_at
                a.duration_ms = report.duration_ms
                a.events = [e.model_dump(mode="json") for e in bus.all(analysis_id)]
                db.commit()
            AuditRepository(db).log(requester, "analysis.completed", {
                "sources_searched": [s.source.value for s in report.sources if s.status == "ok"],
                "sources_failed": [s.source.value for s in report.sources if s.status != "ok"],
                "records_retrieved": report.totals.records_retrieved, "top_category": report.verdict.category.value,
                "capability_mode": report.capability_mode.value,
            }, analysis_id=analysis_id, duration_ms=(time.perf_counter() - started) * 1000)
        bus.emit(analysis_id, "done", "completed", "Analysis complete", data={"analysis_id": analysis_id})
    except Exception as exc:  # pragma: no cover - surfaced to the UI
        log.exception("Analysis %s failed", analysis_id)
        with SessionLocal() as db:
            a = db.get(Analysis, analysis_id)
            if a:
                a.status = "failed"
                a.error = str(exc)
                a.events = [e.model_dump(mode="json") for e in bus.all(analysis_id)]
                db.commit()
        bus.emit(analysis_id, "done", "failed", "Analysis failed", detail=str(exc))
    finally:
        bus.close(analysis_id)


def create_analysis(request: AnalysisRequest, requester: str) -> str:
    analysis_id = uuid.uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(Analysis(id=analysis_id, idea_text=request.idea.description, title=request.idea.title, request=request.model_dump(mode="json"),
                        status="running", scenario_id=request.scenario_id, requested_by=requester, created_at=datetime.now(timezone.utc), events=[]))
        db.commit()
        AuditRepository(db).log(requester, "analysis.started", {"sources": [s.value for s in (request.sources or [])] or "all",
                                                                "scenario_id": request.scenario_id}, analysis_id=analysis_id)
    bus.open(analysis_id)
    return analysis_id


async def analyze_sync(request: AnalysisRequest, requester: str | None = None) -> AnalysisReport:
    """Run an analysis to completion (used by tests, registration checks and the CLI)."""
    requester = requester or get_settings().default_requester
    analysis_id = create_analysis(request, requester)
    await execute_and_store(analysis_id, request, requester)
    with SessionLocal() as db:
        a = db.get(Analysis, analysis_id)
        if a is None or a.report is None:
            raise RuntimeError(a.error if a else "analysis missing")
        return AnalysisReport.model_validate(a.report)
