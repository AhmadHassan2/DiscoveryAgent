"""End-to-end pipeline: demo cases A-G, false-positive prevention, failures and AI fallback."""
import pytest

from app.ai.provider import LLMAssessmentBatch, LLMError, LLMMatchAssessment
from app.pipeline import orchestrator
from app.pipeline.orchestrator import analyze_sync
from app.schemas.analysis import CATEGORY_RANK, AnalysisRequest, CapabilityMode, IdeaInput, LifecycleStage, OverlapCategory
from app.schemas.records import SourceSystem
from app.seed.dataset import DEMO_SCENARIOS

STRONG = CATEGORY_RANK[OverlapCategory.strong_overlap]


async def run(description: str, **kw):
    return await analyze_sync(AnalysisRequest(idea=IdeaInput(description=description), **kw))


@pytest.mark.parametrize("scenario", DEMO_SCENARIOS, ids=[s["id"] for s in DEMO_SCENARIOS])
async def test_demo_scenarios(scenario):
    report = await analyze_sync(AnalysisRequest(idea=IdeaInput(**scenario["idea"])))
    exp = scenario["expected"]
    initiatives = [m for m in report.matches if m.kind == "initiative"]
    by_name = {m.name: m for m in report.matches}
    if exp.get("top_match"):
        assert initiatives and initiatives[0].name == exp["top_match"]
    if exp.get("top_match") is None and "top_match" in exp:
        assert report.verdict.category in (OverlapCategory.no_significant_match, OverlapCategory.related)
    if exp.get("category") == "strong_overlap_or_higher":
        assert CATEGORY_RANK[initiatives[0].category] >= STRONG
    elif exp.get("category") == "partial_overlap":
        assert report.verdict.category == OverlapCategory.partial_overlap
    for name in exp.get("matches_include", []):
        assert name in by_name
    for name in exp.get("not_duplicate", []):
        if name in by_name:
            assert CATEGORY_RANK[by_name[name].category] < STRONG
    if exp.get("lifecycle"):
        assert initiatives[0].lifecycle.stage == LifecycleStage(exp["lifecycle"])


async def test_strong_duplicate_has_multi_source_evidence_owner_and_action():
    r = await run("We want to build an AI-powered cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes.")
    sg = r.matches[0]
    assert sg.name == "SecureGuard AI"
    assert {SourceSystem.confluence, SourceSystem.jira, SourceSystem.github} <= set(sg.sources_with_evidence)
    assert sg.owner and sg.owner.name == "Priya Raman" and sg.owner.provenance_record_id
    assert sg.lifecycle.stage == LifecycleStage.active_development
    assert r.verdict.primary_recommendation.type == "contact_owner"
    assert r.verdict.requires_acknowledgement
    # every evidence item points at a real retrieved/linked record
    assert all(e.url.startswith("https://") for e in sg.evidence)


async def test_partial_overlap_explains_difference():
    r = await run("Build an AI fraud detection system that scores card transactions in real time and blocks suspicious payments before they settle.")
    cl = next(m for m in r.matches if m.name.startswith("CaseLens"))
    assert cl.category == OverlapCategory.partial_overlap
    assert any("real-time" in x.lower() for x in cl.idea_only_capabilities)
    assert r.verdict.primary_recommendation.type == "scope_discussion"


async def test_no_match_is_qualified_and_offers_registration():
    r = await run("An app that calculates the carbon footprint of employee business travel and suggests lower-emission alternatives.")
    assert r.verdict.category in (OverlapCategory.no_significant_match, OverlapCategory.related)
    assert r.verdict.primary_recommendation.type == "register_idea"
    assert "does not prove" in r.verdict.summary or any("not prove" in lim for lim in r.limitations)


async def test_keyword_overlap_alone_does_not_create_duplicate():
    r = await run("A security awareness quiz for new employees during their first week.")
    for m in r.matches:
        if m.name in ("SecureGuard AI", "Onboarding Buddy"):
            assert CATEGORY_RANK[m.category] < STRONG


async def test_connector_failure_continues_and_warns():
    r = await run("Automate internal access requests with manager approval.", simulate_failures=[SourceSystem.servicenow])
    sn = next(s for s in r.sources if s.source == SourceSystem.servicenow)
    assert sn.status == "error"
    assert r.totals.sources_failed == 1
    assert any("not comprehensive" in lim for lim in r.limitations)
    assert r.matches and r.matches[0].name == "AccessFlow"  # still found through Confluence evidence
    assert all(e.source != SourceSystem.servicenow for e in r.matches[0].evidence)  # never fetched from a failed source


async def test_source_selection_limits_search():
    r = await run("AI vulnerability scanner for code repositories", sources=[SourceSystem.jira, SourceSystem.github])
    assert {s.source for s in r.sources} == {SourceSystem.jira, SourceSystem.github}
    assert any("excluded" in lim for lim in r.limitations)


class FailingLLM:
    name, model = "fake", "fake-model"

    def structured(self, *a, **k):
        raise LLMError("gateway unavailable")


class FabricatingLLM:
    name, model = "fake", "fake-model"

    def structured(self, prompt, schema, max_tokens=4000):
        if schema is LLMAssessmentBatch:
            return LLMAssessmentBatch(assessments=[
                LLMMatchAssessment(initiative_id="INIT-001", category="no_significant_match", explanation="Claims no overlap.",
                                   shared_functionality=[], differences=[], reuse_opportunities=[],
                                   cited_record_ids=["jira:SEC-284", "jira:FAKE-999"]),
            ])
        raise LLMError("understanding unavailable")


async def test_llm_failure_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setattr(orchestrator, "get_llm", lambda: FailingLLM())
    r = await run("AI-powered scanner that finds vulnerabilities in repositories and recommends fixes")
    assert r.capability_mode == CapabilityMode.degraded
    assert r.matches[0].name == "SecureGuard AI"
    assert any("failed" in w for w in r.warnings)


async def test_llm_output_is_validated_against_evidence_and_rules(monkeypatch):
    monkeypatch.setattr(orchestrator, "get_llm", lambda: FabricatingLLM())
    r = await run("AI-powered scanner that finds vulnerabilities in repositories and recommends fixes")
    sg = next(m for m in r.matches if m.initiative_id == "INIT-001")
    # LLM tried to downgrade by 4 levels: rule-based category is kept
    assert CATEGORY_RANK[sg.category] >= STRONG and sg.llm_adjustment
    assert "FAKE-999" not in sg.explanation and "jira:SEC-284" in sg.explanation
    assert any("Dropped 1 AI citation" in w for w in r.warnings)


async def test_deterministic_results_are_repeatable():
    a = await run("Detect public storage buckets and overly permissive IAM roles across AWS accounts.")
    b = await run("Detect public storage buckets and overly permissive IAM roles across AWS accounts.")
    assert [(m.name, m.category, m.overall_score) for m in a.matches] == [(m.name, m.category, m.overall_score) for m in b.matches]
