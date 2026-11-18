"""Comparison view and exportable Markdown report."""
from __future__ import annotations

from app.schemas.analysis import AnalysisReport


def comparison_for(report: AnalysisReport, initiative_id: str) -> dict | None:
    m = next((x for x in report.matches if x.initiative_id == initiative_id), None)
    if m is None:
        return None
    idea = report.idea
    u = report.understanding
    return {
        "analysis_id": report.analysis_id,
        "idea": {
            "title": idea.title or u.summary, "description": idea.description, "objective": u.objective,
            "capabilities": u.capabilities, "target_users": u.target_users, "technologies": u.technologies,
            "department": idea.department, "generated_by": u.generated_by,
        },
        "initiative": m.model_dump(mode="json"),
        "rows": [
            {"aspect": "Business objective", "idea": u.objective, "initiative": m.business_objective or m.description},
            {"aspect": "Target users", "idea": ", ".join(u.target_users) or "Not specified", "initiative": ", ".join(m.target_users) or "Unknown"},
            {"aspect": "Technologies", "idea": ", ".join(u.technologies) or "Not specified", "initiative": ", ".join(m.technologies) or "Unknown"},
            {"aspect": "Department", "idea": idea.department or "Not specified", "initiative": m.department or "Unknown"},
        ],
        "shared": m.shared_capabilities,
        "idea_only": m.idea_only_capabilities,
        "initiative_only": m.initiative_only_capabilities,
        "capability_mode": report.capability_mode.value,
    }


def report_markdown(r: AnalysisReport) -> str:
    L: list[str] = []
    L.append(f"# Idea Validation Report — {r.idea.title or r.understanding.summary}")
    L.append("")
    L.append(f"*Analysis {r.analysis_id} · {r.completed_at:%Y-%m-%d %H:%M UTC} · data mode: **{r.data_mode}** (synthetic) · AI mode: **{r.capability_mode.value}** ({r.llm_provider})*")
    L.append("")
    L.append("## Idea")
    L.append(r.idea.description)
    L.append("")
    L.append(f"**Objective (interpreted):** {r.understanding.objective}  ")
    L.append(f"**Capabilities:** {', '.join(r.understanding.capabilities) or '—'}  ")
    L.append(f"**Alternative terminology searched:** {', '.join(r.understanding.alternative_terms) or '—'}")
    L.append("")
    L.append("## Verdict")
    L.append(f"**{r.verdict.category_label}.** {r.verdict.headline}")
    L.append("")
    L.append(r.verdict.summary)
    L.append("")
    L.append(f"**Recommended action:** {r.verdict.primary_recommendation.label}. {r.verdict.primary_recommendation.detail}")
    L.append("")
    L.append("## Search coverage")
    L.append("| Source | Status | Records |")
    L.append("|---|---|---|")
    for s in r.sources:
        L.append(f"| {s.label} | {s.status}{' — ' + s.error if s.error else ''} | {s.records_found} |")
    L.append("")
    L.append(f"{r.totals.records_retrieved} records retrieved, {r.totals.initiatives_identified} candidate initiatives, {r.totals.relevant_initiatives} relevant.")
    L.append("")
    if r.matches:
        L.append("## Related initiatives")
        for m in r.matches:
            L.append(f"### {m.name} — {m.category_label} (score {m.overall_score:.2f})")
            owner = f"{m.owner.name} ({m.owner.role}; source: {m.owner.provenance})" if m.owner else "Unknown"
            L.append(f"- **Department / team:** {m.department or '—'} / {m.team or '—'}")
            L.append(f"- **Owner:** {owner}")
            L.append(f"- **Lifecycle:** {m.lifecycle.label} (confidence {m.lifecycle.confidence}); last activity {m.lifecycle.days_since_activity} days ago")
            L.append(f"- **Assessment ({m.explanation_generated_by}):** {m.explanation}")
            if m.shared_capabilities:
                L.append(f"- **Shared:** {'; '.join(m.shared_capabilities)}")
            if m.idea_only_capabilities:
                L.append(f"- **Only in your idea:** {'; '.join(m.idea_only_capabilities)}")
            if m.initiative_only_capabilities:
                L.append(f"- **Only in the initiative:** {'; '.join(m.initiative_only_capabilities)}")
            if m.reusable_components:
                L.append(f"- **Reusable components:** {'; '.join(m.reusable_components)}")
            for rec in m.recommendations:
                L.append(f"- **Next step:** {rec.label}. {rec.detail}")
            L.append("- **Evidence (retrieved facts):**")
            for e in m.evidence:
                L.append(f"  - [{e.source_label}] [{e.title}]({e.url}) — {e.source_status or 'n/a'}, updated {e.updated_at:%Y-%m-%d}{' (linked)' if not e.matched else ''}")
            if m.uncertainty:
                L.append(f"- **Uncertainty:** {' '.join(m.uncertainty)}")
            L.append("")
    L.append("## Limitations")
    for lim in r.limitations:
        L.append(f"- {lim}")
    L.append("")
    L.append("## Scoring method")
    L.append("Scores are a weighted ranking heuristic (objective 35%, capabilities 30%, scope 15%, users 10%, technology 10%). They are **not** calibrated probabilities.")
    return "\n".join(L)
