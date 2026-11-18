from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedder
from app.config import get_settings
from app.db.models import Idea
from app.db.session import get_db
from app.pipeline.orchestrator import analyze_sync
from app.repositories.analyses import AnalysisRepository, AuditRepository
from app.repositories.records import IdeaRepository, InitiativeRepository
from app.schemas.analysis import CATEGORY_RANK, AnalysisReport, AnalysisRequest
from app.schemas.api import IdeaRegistration, RegisteredIdea, RegistrationBlocked

router = APIRouter(prefix="/api/ideas", tags=["idea registry"])


def _to_api(idea: Idea, db: Session) -> RegisteredIdea:
    inits = {i.id: i for i in InitiativeRepository(db).list()}
    ideas = {i.id: i for i in IdeaRepository(db).list()}
    related = []
    for rid in idea.related_initiative_ids or []:
        if rid in inits:
            related.append({"id": rid, "name": inits[rid].name, "type": "initiative", "owner": inits[rid].owner_name, "status": inits[rid].status})
        elif rid in ideas:
            related.append({"id": rid, "name": ideas[rid].title, "type": "registered_idea", "owner": ideas[rid].submitted_by, "status": ideas[rid].status})
    return RegisteredIdea(
        id=idea.id, title=idea.title, description=idea.description, business_problem=idea.business_problem,
        proposed_functionality=idea.proposed_functionality, target_users=idea.target_users, department=idea.department,
        team=idea.team, technologies=idea.technologies, submitted_by=idea.submitted_by, status=idea.status,
        analysis_id=idea.analysis_id, related_initiatives=related, acknowledged_overlap=idea.acknowledged_overlap,
        created_at=idea.created_at, updated_at=idea.updated_at,
    )


@router.get("", response_model=list[RegisteredIdea])
def list_ideas(q: str | None = Query(None, max_length=200), status: str | None = None, db: Session = Depends(get_db)):
    return [_to_api(i, db) for i in IdeaRepository(db).list(q=q, status=status)]


@router.get("/{idea_id}", response_model=RegisteredIdea)
def get_idea(idea_id: str, db: Session = Depends(get_db)):
    idea = IdeaRepository(db).get(idea_id)
    if idea is None:
        raise HTTPException(404, "Idea not found")
    return _to_api(idea, db)


@router.post("", response_model=RegisteredIdea, status_code=201, responses={409: {"model": RegistrationBlocked}})
async def register_idea(body: IdeaRegistration, db: Session = Depends(get_db)):
    settings = get_settings()
    submitter = body.submitted_by or settings.default_requester
    # Reuse an existing overlap check when it was run for the same idea; otherwise run one now.
    report: AnalysisReport | None = None
    if body.analysis_id:
        a = AnalysisRepository(db).get(body.analysis_id)
        if a and a.report and a.idea_text.strip() == body.idea.description.strip():
            report = AnalysisReport.model_validate(a.report)
    if report is None:
        report = await analyze_sync(AnalysisRequest(idea=body.idea), submitter)

    overlapping = [m for m in report.matches if CATEGORY_RANK[m.category] >= 3]
    if overlapping and not body.acknowledge_overlap:
        return JSONResponse(status_code=409, content=RegistrationBlocked(
            detail="This idea strongly overlaps with existing work. Review the matches and confirm you have contacted the owners before registering.",
            analysis_id=report.analysis_id,
            overlapping=[{"id": m.initiative_id, "name": m.name, "category": m.category.value, "owner": m.owner.name if m.owner else None}
                         for m in overlapping],
        ).model_dump())

    repo = IdeaRepository(db)
    now = datetime.now(timezone.utc)
    idea_in = body.idea
    text = " ".join(p for p in [idea_in.title, idea_in.description, idea_in.business_problem, idea_in.proposed_functionality] if p)
    related = [m.initiative_id for m in report.matches if CATEGORY_RANK[m.category] >= 2]
    idea = Idea(
        id=repo.next_id(), title=idea_in.title or idea_in.description[:80].rstrip() + ("…" if len(idea_in.description) > 80 else ""),
        description=idea_in.description, business_problem=idea_in.business_problem, proposed_functionality=idea_in.proposed_functionality,
        target_users=idea_in.target_users, department=idea_in.department, team=idea_in.team, technologies=idea_in.technologies,
        submitted_by=submitter, status="registered_with_overlap" if overlapping else "registered", analysis_id=report.analysis_id,
        related_initiative_ids=related,
        acknowledged_overlap={"initiatives": [m.initiative_id for m in overlapping], "note": body.acknowledgement_note,
                              "acknowledged_at": now.isoformat()} if overlapping else None,
        created_at=now, updated_at=now, embedding=get_embedder().embed([text])[0],
    )
    db.add(idea)
    db.commit()
    AuditRepository(db).log(submitter, "idea.registered", {"idea_id": idea.id, "overlap_acknowledged": bool(overlapping),
                                                           "related": related}, analysis_id=report.analysis_id)
    return _to_api(idea, db)
