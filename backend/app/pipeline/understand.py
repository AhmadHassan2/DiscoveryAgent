"""Stage 1-2: understand the idea and generate search queries."""
from __future__ import annotations

import re

from app.ai.lexicon import CONCEPT_BY_ID, alternative_terms, concepts_by_facet, extract_concepts, labels
from app.ai.provider import LLMError, LLMProvider, LLMUnderstanding
from app.schemas.analysis import IdeaInput, IdeaUnderstanding


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0] if parts else text.strip()


def _split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in re.split(r"[,;/\n]| and ", value) if v.strip()]


def deterministic_understanding(idea: IdeaInput) -> IdeaUnderstanding:
    text = idea.full_text()
    found = extract_concepts(text)
    facets = concepts_by_facet(found)
    ranked = sorted(found, key=lambda c: -CONCEPT_BY_ID[c].weight * (1 + 0.2 * found[c]))

    objective = _first_sentence(idea.business_problem) if idea.business_problem else _first_sentence(idea.description)
    capability_labels = labels(facets["capability"]) or labels(facets["domain"])
    users = _split_list(idea.target_users) or labels(facets["user"])
    tech = _split_list(idea.technologies) or labels(facets["tech"])
    alt = alternative_terms(found)

    queries: list[str] = [idea.description.strip()[:300]]
    if idea.title:
        queries.append(idea.title)
    specific = [c for c in ranked if CONCEPT_BY_ID[c].facet in ("domain", "capability") and CONCEPT_BY_ID[c].weight >= 0.6]
    for cid in specific[:4]:
        queries.append(CONCEPT_BY_ID[cid].label)
    for term in alt[:3]:
        queries.append(term)
    seen: set[str] = set()
    deduped = [q for q in queries if not (q.lower() in seen or seen.add(q.lower()))]

    return IdeaUnderstanding(
        summary=_first_sentence(idea.description),
        objective=objective,
        capabilities=capability_labels[:8],
        target_users=users[:6],
        technologies=tech[:8],
        alternative_terms=alt,
        search_queries=deduped[:9],
        concepts=labels(found)[:16],
        concept_ids=sorted(found),
        generated_by="deterministic",
    )


UNDERSTAND_PROMPT = """Analyse this proposed internal idea so we can search internal systems (Confluence, Jira, GitHub, SharePoint, Teams, ServiceNow) for similar initiatives.

<idea>
{idea}
</idea>

Return the business objective, core capabilities, target users, technologies, alternative terminology other teams might use for the same thing (e.g. synonyms, industry terms, acronyms), and 3-6 short search queries."""


def llm_understanding(idea: IdeaInput, llm: LLMProvider, base: IdeaUnderstanding) -> IdeaUnderstanding:
    """Enrich the deterministic understanding with the LLM. Concepts are re-derived from the
    LLM's alternative terminology, which is how the LLM improves semantic recall."""
    out: LLMUnderstanding = llm.structured(UNDERSTAND_PROMPT.format(idea=idea.full_text()), LLMUnderstanding, max_tokens=2000)
    enriched_text = " ".join([idea.full_text(), out.objective, " ".join(out.capabilities), " ".join(out.alternative_terms)])
    found = extract_concepts(enriched_text)
    queries = [idea.description.strip()[:300]] + out.search_queries[:6] + base.search_queries[1:4]
    seen: set[str] = set()
    queries = [q for q in queries if q and not (q.lower() in seen or seen.add(q.lower()))]
    alt = list(dict.fromkeys(out.alternative_terms + base.alternative_terms))
    return IdeaUnderstanding(
        summary=out.summary, objective=out.objective, capabilities=out.capabilities[:8],
        target_users=out.target_users[:6] or base.target_users, technologies=out.technologies[:8] or base.technologies,
        alternative_terms=alt[:14], search_queries=queries[:10], concepts=labels(found)[:16], concept_ids=sorted(found),
        generated_by=f"llm:{llm.model}",
    )


def understand(idea: IdeaInput, llm: LLMProvider | None) -> tuple[IdeaUnderstanding, str | None]:
    """Returns (understanding, llm_error)."""
    base = deterministic_understanding(idea)
    if llm is None:
        return base, None
    try:
        return llm_understanding(idea, llm, base), None
    except (LLMError, Exception) as exc:  # never let the LLM break the pipeline
        return base, str(exc)
