from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.pipeline.events import bus
from app.pipeline.orchestrator import create_analysis, execute_and_store
from app.reporting import comparison_for, report_markdown
from app.repositories.analyses import AnalysisRepository
from app.schemas.analysis import AnalysisCreated, AnalysisReport, AnalysisRequest, AnalysisSummary

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisCreated, status_code=202)
async def start_analysis(request: AnalysisRequest, background: BackgroundTasks) -> AnalysisCreated:
    requester = get_settings().default_requester
    analysis_id = create_analysis(request, requester)
    background.add_task(execute_and_store, analysis_id, request, requester)
    return AnalysisCreated(id=analysis_id, status="running", events_url=f"/api/analyses/{analysis_id}/events",
                           report_url=f"/api/analyses/{analysis_id}")


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(limit: int = Query(50, le=200), db: Session = Depends(get_db)) -> list[AnalysisSummary]:
    return [AnalysisSummary(id=a.id, title=a.title, idea_text=a.idea_text, status=a.status, capability_mode=a.capability_mode,
                            top_category=a.top_category, top_initiative_name=a.top_initiative_name, scenario_id=a.scenario_id,
                            created_at=a.created_at, duration_ms=a.duration_ms) for a in AnalysisRepository(db).list(limit)]


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> dict:
    a = AnalysisRepository(db).get(analysis_id)
    if a is None:
        raise HTTPException(404, "Analysis not found")
    events = [e.model_dump(mode="json") for e in bus.all(analysis_id)] or a.events
    return {"id": a.id, "status": a.status, "error": a.error, "request": a.request, "report": a.report, "events": events,
            "created_at": a.created_at, "completed_at": a.completed_at}


@router.get("/{analysis_id}/events")
async def stream_events(analysis_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    a = AnalysisRepository(db).get(analysis_id)
    if a is None:
        raise HTTPException(404, "Analysis not found")
    stored = list(a.events or [])

    async def gen():
        seq = 0
        while True:
            events, done, known = bus.since(analysis_id, seq)
            if not known:  # e.g. after a server restart: replay persisted events
                for ev in stored:
                    yield f"data: {json.dumps(ev)}\n\n"
                yield f"event: end\ndata: {json.dumps({'status': a.status})}\n\n"
                return
            for ev in events:
                seq = ev.seq + 1
                yield f"data: {ev.model_dump_json()}\n\n"
            if done and not events:
                yield "event: end\ndata: {\"status\": \"done\"}\n\n"
                return
            await asyncio.sleep(0.12)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})


def _report(analysis_id: str, db: Session) -> AnalysisReport:
    a = AnalysisRepository(db).get(analysis_id)
    if a is None:
        raise HTTPException(404, "Analysis not found")
    if a.report is None:
        raise HTTPException(409, f"Analysis is {a.status}")
    return AnalysisReport.model_validate(a.report)


@router.get("/{analysis_id}/comparison/{initiative_id}")
def comparison(analysis_id: str, initiative_id: str, db: Session = Depends(get_db)) -> dict:
    report = _report(analysis_id, db)
    result = comparison_for(report, initiative_id)
    if result is None:
        raise HTTPException(404, "Initiative not part of this analysis")
    return result


@router.get("/{analysis_id}/export", response_class=PlainTextResponse)
def export(analysis_id: str, db: Session = Depends(get_db)) -> PlainTextResponse:
    report = _report(analysis_id, db)
    return PlainTextResponse(report_markdown(report), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="idea-discovery-{analysis_id}.md"'})
