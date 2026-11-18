"""Run the evaluation set (tests/eval/cases.yaml) and print accuracy per case."""
import asyncio
import os
import sys

os.environ.setdefault("MOCK_CONNECTOR_LATENCY_MS", "0")
os.environ.setdefault("LLM_PROVIDER", "none")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eval import evaluate_case, load_cases  # noqa: E402


async def main():
    cases = load_cases()
    passed = 0
    for case in cases:
        ok, notes, summary = await evaluate_case(case)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} {case['id']:22} {summary}" + ("" if ok else f"  <- {'; '.join(notes)}"))
    print(f"\n{passed}/{len(cases)} cases passed ({passed / len(cases):.0%})")
    return passed == len(cases)


sys.exit(0 if asyncio.run(main()) else 1)
