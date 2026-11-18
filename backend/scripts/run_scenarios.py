"""Run every demo scenario through the real pipeline and print a compact summary."""
import asyncio
import os
import sys

os.environ.setdefault("MOCK_CONNECTOR_LATENCY_MS", "0")
os.environ.setdefault("LLM_PROVIDER", "none")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.orchestrator import analyze_sync  # noqa: E402
from app.schemas.analysis import AnalysisRequest, IdeaInput  # noqa: E402
from app.seed.dataset import DEMO_SCENARIOS  # noqa: E402


async def main(extra: list[str]):
    items = [(s["id"], IdeaInput(**s["idea"])) for s in DEMO_SCENARIOS] + [(f"adhoc-{i}", IdeaInput(description=t)) for i, t in enumerate(extra)]
    for sid, idea in items:
        r = await analyze_sync(AnalysisRequest(idea=idea))
        print(f"\n=== {sid}: {r.verdict.category.value} | {r.verdict.headline}")
        print(f"    records={r.totals.records_retrieved} unique={r.totals.unique_records} candidates={r.totals.initiatives_identified}")
        for m in r.matches:
            dims = " ".join(f"{d.name[:3]}={d.score if d.score is None else round(d.score,2)}" for d in m.dimensions)
            print(f"  - {m.name[:40]:40} {m.category.value:20} {m.overall_score:.2f} [{dims}] {m.lifecycle.label} srcs={len(m.sources_with_evidence)} ev={len(m.evidence)} owner={m.owner.name if m.owner else None}")


asyncio.run(main(sys.argv[1:]))
