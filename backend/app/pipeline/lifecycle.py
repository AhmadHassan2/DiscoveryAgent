"""Lifecycle intelligence: derive an initiative's stage from explicit source statuses and activity.

Rules (explainable, in priority order):
  1. ServiceNow lifecycle (Operational/Live -> deployed, Retired -> retired) is authoritative.
  2. Explicit stop signals (Jira "Won't Do"/"Cancelled", page status "Stopped", archived repository) -> abandoned.
  3. Explicit hold signals (Jira "On Hold") -> paused.
  4. Stage declared on documents (page/deck status: Research, Proof of concept, In development, Live).
  5. Jira/GitHub activity indicates work is happening but does not define the stage on its own.
  6. The Initiative Index status is used only when no source states a stage.
Activity recency is evaluated separately: active-looking stages with no activity for > 12 months
are flagged as possibly stale; > 6 months as possibly paused.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from app.db.models import Initiative
from app.schemas.analysis import LifecycleAssessment, LifecycleStage
from app.schemas.records import NormalizedRecord, SOURCE_LABELS

STAGE_LABELS = {
    LifecycleStage.proposed: "Proposed",
    LifecycleStage.research: "Research",
    LifecycleStage.proof_of_concept: "Proof of concept",
    LifecycleStage.active_development: "Active development",
    LifecycleStage.deployed: "Deployed",
    LifecycleStage.paused: "Paused",
    LifecycleStage.abandoned: "Abandoned",
    LifecycleStage.retired: "Retired",
    LifecycleStage.unknown: "Unknown",
}

_DOC_STAGE = {
    "research": LifecycleStage.research, "discovery": LifecycleStage.research,
    "proof of concept": LifecycleStage.proof_of_concept, "poc": LifecycleStage.proof_of_concept,
    "pilot": LifecycleStage.active_development, "pilot rollout": LifecycleStage.active_development,
    "in development": LifecycleStage.active_development, "active development": LifecycleStage.active_development,
    "live": LifecycleStage.deployed, "operational": LifecycleStage.deployed, "active process": LifecycleStage.deployed, "active": LifecycleStage.deployed,
    "stopped": LifecycleStage.abandoned, "cancelled": LifecycleStage.abandoned, "abandoned": LifecycleStage.abandoned,
    "retired": LifecycleStage.retired, "paused": LifecycleStage.paused, "on hold": LifecycleStage.paused,
    "proposed": LifecycleStage.proposed, "draft": LifecycleStage.proposed,
}
_JIRA_STOP = {"won't do", "cancelled", "abandoned", "closed - abandoned"}
_JIRA_HOLD = {"on hold", "paused", "blocked"}
_JIRA_ACTIVE = {"in progress", "in development", "in review", "research"}


def _days(now: datetime, dt: datetime | None) -> int | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def assess(records: list[NormalizedRecord], initiative: Initiative | None, now: datetime | None = None,
           registered_status: str | None = None) -> LifecycleAssessment:
    now = now or datetime.now(timezone.utc)
    signals: list[str] = []
    caveats: list[str] = []
    explicit: list[tuple[LifecycleStage, int, str]] = []  # (stage, authority, signal)

    for r in records:
        status = (r.source_status or "").strip()
        s = status.lower()
        where = f"{SOURCE_LABELS[r.source.value]} {r.external_key}"
        if r.source.value == "servicenow" and r.record_type in ("catalog_item", "application"):
            if s in ("operational", "live"):
                explicit.append((LifecycleStage.deployed, 100, f"{where} is '{status}' in ServiceNow"))
            elif s == "retired":
                explicit.append((LifecycleStage.retired, 100, f"{where} is 'Retired' in ServiceNow"))
        elif r.source.value == "jira":
            if s in _JIRA_STOP:
                explicit.append((LifecycleStage.abandoned, 80, f"Jira {r.external_key} closed as '{status}'"))
            elif s in _JIRA_HOLD:
                explicit.append((LifecycleStage.paused, 80, f"Jira {r.external_key} is '{status}'"))
            elif s in _JIRA_ACTIVE:
                signals.append(f"Jira {r.external_key} is '{status}'")
            elif s == "done":
                signals.append(f"Jira {r.external_key} is 'Done'")
        elif r.source.value == "github":
            if r.metadata.get("archived"):
                explicit.append((LifecycleStage.abandoned, 70, f"Repository {r.external_key} is archived"))
            elif r.record_type == "repository":
                commits = r.metadata.get("commits_last_30_days")
                if commits:
                    signals.append(f"{commits} commits in the last 30 days in {r.external_key}")
        elif r.source.value in ("confluence", "sharepoint") and s:
            stage = _DOC_STAGE.get(s)
            if stage:
                explicit.append((stage, 60, f"{where} states status '{status}'"))

    stage = LifecycleStage.unknown
    confidence = "low"
    if registered_status is not None:
        stage = LifecycleStage.proposed
        signals.append(f"Registered idea with status '{registered_status}'")
        confidence = "high"
    elif explicit:
        top_authority = max(a for _, a, _ in explicit)
        top = [(st, sig) for st, a, sig in explicit if a == top_authority]
        stage = Counter(st for st, _ in top).most_common(1)[0][0]
        signals = [sig for st, _, sig in explicit if st == stage] + signals
        agreeing = len([1 for st, _, _ in explicit if st == stage])
        confidence = "high" if agreeing >= 2 or top_authority >= 80 else "medium"
        conflicting = {st for st, _, _ in explicit if st != stage}
        if conflicting:
            caveats.append("Sources disagree on status: " + ", ".join(sorted(STAGE_LABELS[c] for c in conflicting)) + " also reported")
    elif initiative is not None:
        try:
            stage = LifecycleStage(initiative.status)
        except ValueError:
            stage = LifecycleStage.unknown
        signals.append(f"Initiative Index lists status '{STAGE_LABELS.get(stage, initiative.status)}' (not confirmed by a retrieved source record)")
        confidence = "low"

    dates = [r.updated_at for r in records if r.updated_at]
    last = max(dates) if dates else None
    days = _days(now, last)
    if days is not None:
        signals.append(f"Most recent activity {days} days ago")
        if stage in (LifecycleStage.active_development, LifecycleStage.proof_of_concept, LifecycleStage.research, LifecycleStage.proposed):
            if days > 365:
                caveats.append("No recorded activity for over 12 months — the initiative may be stale or abandoned")
                confidence = "low"
            elif days > 180:
                caveats.append("No recorded activity for over 6 months — the initiative may be paused")
                confidence = "low" if confidence == "low" else "medium"
        if stage == LifecycleStage.abandoned and days > 365:
            signals.append("Inactive for more than a year")
    if initiative is not None and stage != LifecycleStage.unknown and initiative.status != stage.value and registered_status is None:
        caveats.append(f"Initiative Index lists '{STAGE_LABELS.get(LifecycleStage(initiative.status), initiative.status)}', which differs from the source evidence")

    return LifecycleAssessment(stage=stage, label=STAGE_LABELS[stage], confidence=confidence, last_activity_at=last,
                               days_since_activity=days, signals=signals[:6], caveats=caveats)
