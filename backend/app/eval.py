"""Evaluation harness shared by scripts/run_eval.py and the test-suite."""
from __future__ import annotations

from pathlib import Path

import yaml

from app.pipeline.orchestrator import analyze_sync
from app.schemas.analysis import CATEGORY_RANK, AnalysisRequest, IdeaInput, OverlapCategory

CASES_PATH = Path(__file__).resolve().parent.parent / "tests" / "eval" / "cases.yaml"


def load_cases() -> list[dict]:
    return yaml.safe_load(CASES_PATH.read_text())


async def evaluate_case(case: dict) -> tuple[bool, list[str], str]:
    report = await analyze_sync(AnalysisRequest(idea=IdeaInput(description=case["idea"])))
    notes: list[str] = []
    initiatives = [m for m in report.matches if m.kind != "registered_idea"]
    by_name = {m.name: m for m in report.matches}
    top = initiatives[0] if initiatives else None
    summary = f"top={top.name if top else None} ({top.category.value if top else '-'})"

    if case.get("expect_top"):
        if not top or top.name != case["expect_top"]:
            notes.append(f"expected top {case['expect_top']}")
        elif CATEGORY_RANK[top.category] < CATEGORY_RANK[OverlapCategory(case["min_category"])]:
            notes.append(f"category {top.category.value} below {case['min_category']}")
        if case.get("lifecycle") and top and top.name == case["expect_top"] and top.lifecycle.stage.value != case["lifecycle"]:
            notes.append(f"lifecycle {top.lifecycle.stage.value} != {case['lifecycle']}")
    for name, ceiling in (case.get("max_category") or {}).items():
        m = by_name.get(name)
        if m and CATEGORY_RANK[m.category] > CATEGORY_RANK[OverlapCategory(ceiling)]:
            notes.append(f"{name} classified {m.category.value} (max {ceiling})")
    if case.get("max_overall_category") and report.matches:
        if CATEGORY_RANK[report.verdict.category] > CATEGORY_RANK[OverlapCategory(case["max_overall_category"])]:
            notes.append(f"verdict {report.verdict.category.value} exceeds {case['max_overall_category']}")
    if case.get("no_match"):
        if CATEGORY_RANK[report.verdict.category] >= CATEGORY_RANK[OverlapCategory.partial_overlap]:
            notes.append(f"expected no significant match, got {report.verdict.category.value}")
    return not notes, notes, summary
