"""Cross-source evidence grouping and lifecycle status handling."""
from datetime import datetime, timedelta, timezone

from app.connectors.mock_base import to_normalized
from app.db.session import SessionLocal
from app.pipeline.correlate import correlate
from app.pipeline.lifecycle import assess
from app.repositories.records import InitiativeRepository, RecordRepository
from app.schemas.analysis import LifecycleStage


def _all():
    with SessionLocal() as db:
        return [to_normalized(r) for r in RecordRepository(db).list_all()], InitiativeRepository(db).list()


def test_secureguard_records_across_sources_form_one_initiative():
    records, initiatives = _all()
    sg = [r for r in records if r.id in {
        "confluence:APPSEC-1042", "jira:SEC-284", "github:northbridge-appsec/secureguard-scanner",
        "sharepoint:SP-SECENG-031", "teams:appsec-guild-0091"}]
    candidates, unlinked = correlate(sg, initiatives)
    assert len(candidates) == 1 and not unlinked
    cand = candidates[0]
    assert cand.initiative.name == "SecureGuard AI"
    assert {r.source.value for r in cand.matched_records} == {"confluence", "jira", "github", "sharepoint", "teams"}
    # The SharePoint deck has no label; it is linked only because it mentions the Jira key.
    assert "SEC-284" in cand.evidence["sharepoint:SP-SECENG-031"].reason


def test_records_without_cross_references_are_not_merged_by_guesswork():
    records, initiatives = _all()
    hackathon = [r for r in records if r.id == "teams:ai-community-0412"]
    candidates, unlinked = correlate(hackathon, initiatives)
    assert not candidates and [r.id for r in unlinked] == ["teams:ai-community-0412"]


def test_similar_names_are_not_merged():
    records, initiatives = _all()
    sentinels = [r for r in records if "sentinel" in r.title.lower()]
    candidates, _ = correlate(sentinels, initiatives)
    names = {c.initiative.name for c in candidates}
    assert {"Pipeline Sentinel", "API Sentinel"} <= names


def _records_for(name):
    records, initiatives = _all()
    cands, _ = correlate(records, initiatives)
    c = next(c for c in cands if c.initiative and c.initiative.name == name)
    return [e.record for e in c.evidence.values()], c.initiative


def test_abandoned_project_detected_from_explicit_signals():
    recs, init = _records_for("DocuMind Contract Clause Extractor")
    life = assess(recs, init)
    assert life.stage == LifecycleStage.abandoned and life.confidence == "high"
    assert life.days_since_activity > 365


def test_deployed_solution_detected_from_servicenow():
    recs, init = _records_for("AccessFlow")
    life = assess(recs, init)
    assert life.stage == LifecycleStage.deployed
    assert any("ServiceNow" in s for s in life.signals)


def test_paused_and_retired_statuses():
    recs, init = _records_for("Vendor Risk Questionnaire Automation")
    assert assess(recs, init).stage == LifecycleStage.paused
    recs, init = _records_for("Interview Scheduling Bot")
    assert assess(recs, init).stage == LifecycleStage.retired


def test_stale_active_project_is_flagged_not_reported_as_ongoing():
    recs, init = _records_for("Pipeline Sentinel")
    future = datetime.now(timezone.utc) + timedelta(days=500)
    life = assess(recs, init, now=future)
    assert life.confidence == "low"
    assert any("12 months" in c for c in life.caveats)
