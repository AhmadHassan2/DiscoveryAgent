"""Evaluation set: free-form phrasings (not the demo prompts) with expected matches/classifications."""
import pytest

from app.eval import evaluate_case, load_cases

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
async def test_eval_case(case):
    ok, notes, summary = await evaluate_case(case)
    assert ok, f"{summary}: {notes}"
