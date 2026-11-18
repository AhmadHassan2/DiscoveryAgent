"""Sources, initiatives (projects), relationship graph, stats, demo scenarios, health and audit."""
from __future__ import annotations

import re
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.embeddings import cosine, get_embedder
from app.ai.provider import describe_llm
from app.config import get_settings
from app.connectors.mock_base import to_normalized
from app.connectors.registry import all_connectors
from app.db.models import Initiative
from app.db.session import get_db
from app.pipeline.correlate import InitiativeMatcher
from app.pipeline.lifecycle import STAGE_LABELS
from app.repositories.analyses import AnalysisRepository, AuditRepository
from app.repositories.records import IdeaRepository, InitiativeRepository, RecordRepository
from app.schemas.analysis import IdeaInput, LifecycleStage
from app.schemas.api import (
    DemoScenario,
    GraphEdge,
    GraphNode,
    GraphResponse,
    HealthResponse,
    InitiativeDetail,
    InitiativeSummary,
    SourcesOverview,
    StatsResponse,
)
from app.schemas.records import SOURCE_LABELS, ConnectorHealth, ConnectorStatus, SourceSystem
from app.seed.dataset import DEMO_SCENARIOS

router = APIRouter(prefix="/api", tags=["catalog"])


def _records_by_initiative(db: Session) -> dict[str, list]:
    initiatives = InitiativeRepository(db).list()
    matcher = InitiativeMatcher(initiatives)
    out: dict[str, list] = {i.id: [] for i in initiatives}
    for rec in RecordRepository(db).list_all():
        n = to_normalized(rec)
        if n.acl.classification == "restricted":
            continue
        a = matcher.assign(n)
        if a:
            out[a[0]].append((n, a[1]))
    return out


def _summary(i: Initiative, recs: list) -> InitiativeSummary:
    return InitiativeSummary(id=i.id, name=i.name, department=i.department, team=i.team, owner_name=i.owner_name, status=i.status,
                             description=i.description, last_activity_at=i.last_activity_at, created_at=i.created_at,
                             record_count=len(recs), sources=sorted({r.source.value for r, _ in recs}))


# ------------------------------------------------------------------------------------- sources
@router.get("/sources", response_model=SourcesOverview)
def sources() -> SourcesOverview:
    failing = get_settings().failed_source_set
    out = []
    for c in all_connectors().values():
        try:
            h = c.health()
            if c.source.value in failing:
                h.status, h.error = ConnectorStatus.error, "Simulated outage (FAIL_SOURCES)"
        except Exception as exc:
            h = ConnectorHealth(source=c.source, display_name=c.display_name, status=ConnectorStatus.error, mode=c.mode, error=str(exc))
        out.append(h)
    return SourcesOverview(data_mode="mock", sources=out, total_records=sum(h.record_count for h in out))


@router.get("/sources/{source}/records")
def source_records(source: SourceSystem, q: str | None = Query(None, max_length=200), db: Session = Depends(get_db)) -> list[dict]:
    if source == SourceSystem.idea_registry:
        from app.connectors.sources import idea_to_record

        recs = [idea_to_record(i) for i in IdeaRepository(db).list()]
    else:
        recs = [to_normalized(r) for r in RecordRepository(db).list_by_source(source.value)]
    matcher = InitiativeMatcher(InitiativeRepository(db).list())
    out = []
    for r in recs:
        if q and q.lower() not in f"{r.title} {r.content} {r.external_key}".lower():
            continue
        a = matcher.assign(r)
        restricted = r.acl.classification == "restricted"
        out.append({
            "id": r.id, "source": r.source.value, "record_type": r.record_type, "external_key": r.external_key,
            "title": "[Restricted record]" if restricted else r.title, "content": "" if restricted else r.content,
            "url": r.url, "author": r.author, "owner": r.owner, "source_status": r.source_status, "updated_at": r.updated_at,
            "labels": r.labels, "links": r.links, "metadata": {} if restricted else r.metadata, "acl": r.acl.model_dump(),
            "initiative_id": a[0] if a else None, "link_reason": a[1] if a else None, "restricted": restricted,
        })
    return out


# ------------------------------------------------------------------------------------- initiatives
@router.get("/projects", response_model=list[InitiativeSummary])
def projects(db: Session = Depends(get_db)) -> list[InitiativeSummary]:
    by_init = _records_by_initiative(db)
    return [_summary(i, by_init.get(i.id, [])) for i in InitiativeRepository(db).list()]


@router.get("/projects/{initiative_id}", response_model=InitiativeDetail)
def project(initiative_id: str, db: Session = Depends(get_db)) -> InitiativeDetail:
    repo = InitiativeRepository(db)
    i = repo.get(initiative_id)
    if i is None:
        raise HTTPException(404, "Initiative not found")
    by_init = _records_by_initiative(db)
    recs = by_init.get(i.id, [])
    related: list[dict] = []
    # Evidence-based relations: records of this initiative that mention another initiative (or vice versa)
    others = [o for o in repo.list() if o.id != i.id]
    for o in others:
        names = [o.name, *(o.aliases or [])]
        for rec, _ in recs:
            hit = next((n for n in names if re.search(r"(?<![\w-])" + re.escape(n.lower()) + r"(?![\w-])", rec.content.lower())), None)
            if hit:
                related.append({"id": o.id, "name": o.name, "type": "referenced", "reason": f"{SOURCE_LABELS[rec.source.value]} {rec.external_key} mentions '{hit}'"})
                break
        for rec, _ in by_init.get(o.id, []):
            hit = next((n for n in [i.name, *(i.aliases or [])] if re.search(r"(?<![\w-])" + re.escape(n.lower()) + r"(?![\w-])", rec.content.lower())), None)
            if hit and not any(r["id"] == o.id for r in related):
                related.append({"id": o.id, "name": o.name, "type": "referenced_by", "reason": f"{SOURCE_LABELS[rec.source.value]} {rec.external_key} mentions '{hit}'"})
                break
    for idea in IdeaRepository(db).list():
        if i.id in (idea.related_initiative_ids or []):
            related.append({"id": idea.id, "name": idea.title, "type": "registered_idea", "reason": f"Registered idea by {idea.submitted_by} references this initiative"})
    sims = sorted(((o, cosine(i.embedding, o.embedding)) for o in others if o.embedding), key=lambda x: -x[1])
    for o, s in sims[:2]:
        if s >= 0.45 and not any(r["id"] == o.id for r in related):
            related.append({"id": o.id, "name": o.name, "type": "similar", "reason": f"Similar objective (embedding similarity {s:.2f}) — inferred, not evidenced"})
    s = _summary(i, recs)
    return InitiativeDetail(
        **s.model_dump(), aliases=i.aliases or [], business_objective=i.business_objective, core_features=i.core_features or [],
        target_users=i.target_users or [], technologies=i.technologies or [], reusable_components=i.reusable_components or [],
        notes=i.notes, owner_email=i.owner_email,
        records=[{**r.model_dump(mode="json", exclude={"keyword_score", "semantic_score", "fused_score", "matched_queries"}), "link_reason": why} for r, why in recs],
        related=related,
    )


# ------------------------------------------------------------------------------------- graph
@router.get("/graph", response_model=GraphResponse)
def graph(include_records: bool = True, db: Session = Depends(get_db)) -> GraphResponse:
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    by_init = _records_by_initiative(db)
    for i in InitiativeRepository(db).list():
        nodes[i.id] = GraphNode(id=i.id, label=i.name, type="initiative", group=i.department, meta={"status": i.status})
        tid = f"team:{i.team}"
        nodes.setdefault(tid, GraphNode(id=tid, label=i.team, type="team", group=i.department))
        edges.append(GraphEdge(source=i.id, target=tid, type="owned_by_team"))
        if i.owner_name:
            pid = f"person:{i.owner_name}"
            nodes.setdefault(pid, GraphNode(id=pid, label=i.owner_name, type="person", group=i.department))
            edges.append(GraphEdge(source=pid, target=i.id, type="owns"))
            edges.append(GraphEdge(source=pid, target=tid, type="member_of"))
        if include_records:
            for rec, _ in by_init.get(i.id, []):
                nodes[rec.id] = GraphNode(id=rec.id, label=rec.title, type="record", group=rec.source.value,
                                          meta={"source": rec.source.value, "url": rec.url, "record_type": rec.record_type})
                edges.append(GraphEdge(source=i.id, target=rec.id, type="evidence"))
    for idea in IdeaRepository(db).list():
        nodes[idea.id] = GraphNode(id=idea.id, label=idea.title, type="idea", group=idea.department, meta={"status": idea.status})
        for rid in idea.related_initiative_ids or []:
            if rid in nodes:
                edges.append(GraphEdge(source=idea.id, target=rid, type="related_to"))
    return GraphResponse(nodes=list(nodes.values()), edges=edges)


# ------------------------------------------------------------------------------------- stats / demo / health
@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)) -> StatsResponse:
    inits = InitiativeRepository(db).list()
    by_source = RecordRepository(db).count_by_source()
    ideas = IdeaRepository(db).list()
    by_source["idea_registry"] = len(ideas)
    return StatsResponse(
        initiatives=len(inits), records=sum(v for k, v in by_source.items() if k != "idea_registry"), sources=len(all_connectors()),
        departments=len({i.department for i in inits}), registered_ideas=len(ideas), analyses_run=AnalysisRepository(db).count(),
        duplicates_flagged=AnalysisRepository(db).count_flagged(),
        by_status={STAGE_LABELS[LifecycleStage(k)]: v for k, v in Counter(i.status for i in inits).items()},
        by_department=dict(Counter(i.department for i in inits).most_common()), by_source=by_source,
    )


@router.get("/demo/scenarios", response_model=list[DemoScenario])
def demo_scenarios() -> list[DemoScenario]:
    return [DemoScenario(id=s["id"], case=s["case"], title=s["title"], summary=s["summary"], idea=IdeaInput(**s["idea"]), expected=s["expected"])
            for s in DEMO_SCENARIOS]


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = f"ok ({db.get_bind().dialect.name})"
    except Exception as exc:  # pragma: no cover
        db_status = f"error: {exc}"
    provider, model = describe_llm()
    return HealthResponse(status="ok" if db_status.startswith("ok") else "degraded", database=db_status, llm_provider=provider,
                          llm_model=model, embedding_provider=get_embedder().name, data_mode="mock",
                          failing_sources=sorted(get_settings().failed_source_set))


@router.get("/audit")
def audit(limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": a.id, "at": a.at, "actor": a.actor, "action": a.action, "analysis_id": a.analysis_id, "detail": a.detail,
             "duration_ms": a.duration_ms} for a in AuditRepository(db).list(limit)]
