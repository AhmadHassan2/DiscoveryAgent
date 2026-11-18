"""Stage 8-9: multi-dimensional overlap analysis and classification.

SCORING METHOD (a transparent ranking heuristic — NOT a calibrated probability)
------------------------------------------------------------------------------
Each dimension is scored 0-1 by comparing lexicon concepts (weighted by specificity) found in the
idea against those found in the initiative's own fields and source evidence, blended with embedding
cosine similarity where noted:

  objective     35%  coverage of the idea's problem-domain concepts by the initiative (70%)
                     + embedding similarity of idea vs initiative objective/description (30%)
  capabilities  30%  coverage of the idea's functional capabilities by the initiative
  scope         15%  symmetric (Jaccard) overlap of domain+capability concepts — penalises
                     initiatives much broader or narrower than the idea
  users         10%  coverage of the idea's target user groups (skipped if not stated)
  technology    10%  coverage of the idea's technologies (skipped if not stated)

Dimensions without enough information are excluded and the weights re-normalised.

Classification requires BOTH objective and capability alignment for strong categories, so keyword
or embedding similarity alone can never produce a duplicate verdict:

  near_duplicate   objective >= 0.80, capabilities >= 0.80, overall >= 0.75
  strong_overlap   objective >= 0.60, capabilities >= 0.55, overall >= 0.55
  partial_overlap  (objective >= 0.55 and overall >= 0.33) or
                   (capabilities >= 0.45 and objective >= 0.35 and overall >= 0.38)
  related          objective >= 0.30 or (overall >= 0.25 and objective >= 0.15)
  otherwise        no significant match
"""
from __future__ import annotations

from dataclasses import dataclass

from app.ai.embeddings import cosine, get_embedder
from app.ai.lexicon import CONCEPT_BY_ID, concepts_by_facet, extract_concepts
from app.ai.text import strip_negated_sentences
from app.pipeline.correlate import Candidate
from app.schemas.analysis import CATEGORY_LABELS, CATEGORY_RANK, DimensionScore, IdeaInput, IdeaUnderstanding, OverlapCategory

WEIGHTS = {"objective": 0.35, "capabilities": 0.30, "scope": 0.15, "users": 0.10, "technology": 0.10}
DIMENSION_LABELS = {"objective": "Business objective", "capabilities": "Core capabilities", "scope": "Scope",
                    "users": "Target users", "technology": "Technology"}

THRESHOLDS = {
    "near_duplicate": {"objective": 0.80, "capabilities": 0.80, "overall": 0.75},
    "strong_overlap": {"objective": 0.60, "capabilities": 0.55, "overall": 0.55},
}

SCORING_METHOD = {
    "type": "weighted multi-dimension ranking heuristic",
    "calibrated_probability": False,
    "weights": WEIGHTS,
    "thresholds": {
        "near_duplicate": "objective >= 0.80 AND capabilities >= 0.80 AND overall >= 0.75",
        "strong_overlap": "objective >= 0.60 AND capabilities >= 0.55 AND overall >= 0.55",
        "partial_overlap": "(objective >= 0.55 AND overall >= 0.33) OR (capabilities >= 0.45 AND objective >= 0.35 AND overall >= 0.38)",
        "related": "objective >= 0.30 OR (overall >= 0.25 AND objective >= 0.15)",
    },
    "notes": "Scores rank candidates and explain the classification. They are not statistically calibrated probabilities of duplication.",
}

GENERIC = 0.45  # concepts at or below this weight are too generic to be shown as shared capabilities


def _w(cid: str) -> float:
    return CONCEPT_BY_ID[cid].weight


def coverage(a: set[str], b: set[str]) -> float | None:
    total = sum(_w(c) for c in a)
    if total == 0:
        return None
    return sum(_w(c) for c in a & b) / total


def blended_coverage(a: set[str], struct: set[str], everything: set[str]) -> float | None:
    """Coverage against the initiative's own description (60%) and all evidence (40%)."""
    c1, c2 = coverage(a, struct), coverage(a, everything)
    if c1 is None:
        return None
    return 0.6 * c1 + 0.4 * (c2 or 0.0)


def jaccard(a: set[str], b: set[str]) -> float | None:
    union = a | b
    total = sum(_w(c) for c in union)
    if total == 0:
        return None
    return sum(_w(c) for c in a & b) / total


def _emb_norm(sim: float) -> float:
    return max(0.0, min(1.0, (sim - 0.10) / 0.55))


def _label_list(ids, min_weight: float = GENERIC) -> list[str]:
    ids = [c for c in ids if _w(c) > min_weight and CONCEPT_BY_ID[c].facet in ("domain", "capability")]
    return [CONCEPT_BY_ID[c].label for c in sorted(ids, key=lambda c: -_w(c))]


@dataclass
class Profile:
    name: str
    structured_text: str  # the initiative's own description of itself
    evidence_text: str  # retrieved/linked record text
    users_text: str
    tech_text: str
    features: list[str]
    embedding: list[float] | None


def build_profile(c: Candidate) -> Profile:
    ev_text = strip_negated_sentences(" ".join(f"{e.record.title}. {e.record.content}" for e in c.evidence.values()))
    if c.kind == "initiative" and c.initiative is not None:
        i = c.initiative
        structured = strip_negated_sentences(" ".join([i.name + ".", i.description, i.business_objective + ".", ". ".join(i.core_features or []) + "."]))
        return Profile(i.name, structured, ev_text, " ".join(i.target_users or []), " ".join(i.technologies or []),
                       list(i.core_features or []), i.embedding)
    first = next(iter(c.evidence.values())).record
    return Profile(first.title, ev_text, ev_text, ev_text, ev_text, [], None)


@dataclass
class OverlapResult:
    category: OverlapCategory
    overall: float
    dimensions: list[DimensionScore]
    shared: list[str]
    idea_only: list[str]
    initiative_only: list[str]
    rationale: str


def classify(obj: float, cap: float, overall: float) -> OverlapCategory:
    if obj >= 0.80 and cap >= 0.80 and overall >= 0.75:
        return OverlapCategory.near_duplicate
    if obj >= 0.60 and cap >= 0.55 and overall >= 0.55:
        return OverlapCategory.strong_overlap
    if (obj >= 0.55 and overall >= 0.33) or (cap >= 0.45 and obj >= 0.35 and overall >= 0.38):
        return OverlapCategory.partial_overlap
    if obj >= 0.30 or (overall >= 0.25 and obj >= 0.15):
        return OverlapCategory.related
    return OverlapCategory.no_significant_match


def analyse(idea: IdeaInput, understanding: IdeaUnderstanding, idea_embedding: list[float], c: Candidate) -> OverlapResult:
    profile = build_profile(c)
    idea_concepts = set(understanding.concept_ids) or set(extract_concepts(idea.full_text()))
    i_f = concepts_by_facet(idea_concepts)

    p_struct = set(extract_concepts(profile.structured_text))
    p_all = p_struct | set(extract_concepts(profile.evidence_text))
    p_f = concepts_by_facet(p_all)
    p_struct_f = concepts_by_facet(p_struct)

    embedder = get_embedder()
    p_emb = profile.embedding or embedder.embed([profile.structured_text])[0]
    emb_sim = cosine(idea_embedding, p_emb)

    dims: dict[str, tuple[float | None, str]] = {}

    # Objective -------------------------------------------------------------------------------------
    cov_dom = blended_coverage(i_f["domain"], p_struct_f["domain"], p_f["domain"])
    if cov_dom is None:
        # Text similarity alone is weak evidence: discount it.
        obj = 0.6 * _emb_norm(emb_sim)
        dims["objective"] = (obj, f"No known problem domain detected in the idea; estimated from text similarity only ({emb_sim:.2f}), discounted.")
    else:
        obj = 0.7 * cov_dom + 0.3 * _emb_norm(emb_sim)
        shared_dom = _label_list(i_f["domain"] & p_f["domain"], 0.0)
        missing_dom = _label_list(i_f["domain"] - p_f["domain"], 0.0)
        txt = f"Shared problem domain: {', '.join(shared_dom) or 'none'}."
        if missing_dom:
            txt += f" Not addressed: {', '.join(missing_dom)}."
        dims["objective"] = (obj, txt)

    # Capabilities ------------------------------------------------------------------------------------
    cap_ids = i_f["capability"]
    cov_cap = blended_coverage(cap_ids, p_struct_f["capability"], p_f["capability"])
    cap_weight = sum(_w(x) for x in cap_ids)
    if cov_cap is None:
        cap = obj * 0.85
        dims["capabilities"] = (cap, "No distinct capabilities detected in the idea; estimated from objective alignment.")
    else:
        cap = cov_cap if cap_weight >= 0.9 else 0.5 * cov_cap + 0.5 * obj * 0.85
        shared_cap = _label_list(cap_ids & p_f["capability"], 0.0)
        missing_cap = _label_list(cap_ids - p_f["capability"], 0.0)
        txt = f"Shared capabilities: {', '.join(shared_cap) or 'none'}."
        if missing_cap:
            txt += f" Idea capabilities without evidence in this initiative: {', '.join(missing_cap)}."
        dims["capabilities"] = (cap, txt)

    # Scope -------------------------------------------------------------------------------------------
    i_func = i_f["domain"] | i_f["capability"]
    p_func = p_struct_f["domain"] | p_struct_f["capability"]
    jac = jaccard({x for x in i_func if _w(x) > GENERIC}, {x for x in p_func if _w(x) > GENERIC})
    scope = None if jac is None else min(1.0, jac / 0.6)
    broader = _label_list(p_func - i_func)
    dims["scope"] = (scope, ("Initiative also covers: " + ", ".join(broader[:4]) + ".") if broader else "Similar breadth of scope.")

    # Users ---------------------------------------------------------------------------------------------
    i_users = concepts_by_facet(extract_concepts(idea.target_users or "")).get("user") or i_f["user"]
    p_users = concepts_by_facet(extract_concepts(profile.users_text + " " + profile.structured_text))["user"]
    if not i_users:
        dims["users"] = (None, "Target users not stated in the idea — not scored.")
    elif not p_users:
        dims["users"] = (None, "Initiative target users unknown — not scored.")
    else:
        u = coverage(i_users, p_users) or 0.0
        dims["users"] = (u, f"Idea users: {', '.join(CONCEPT_BY_ID[x].label for x in i_users)}; initiative users: {', '.join(CONCEPT_BY_ID[x].label for x in p_users)}.")

    # Technology -------------------------------------------------------------------------------------------
    i_tech = concepts_by_facet(extract_concepts(idea.technologies or "")).get("tech") or i_f["tech"]
    p_tech = concepts_by_facet(extract_concepts(profile.tech_text + " " + profile.evidence_text))["tech"]
    if not i_tech:
        dims["technology"] = (None, "Technologies not stated in the idea — not scored.")
    else:
        t = coverage(i_tech, p_tech) or 0.0
        shared_t = [CONCEPT_BY_ID[x].label for x in i_tech & p_tech]
        dims["technology"] = (t, f"Shared technology: {', '.join(shared_t) or 'none'}.")

    # Overall --------------------------------------------------------------------------------------------
    num = sum(WEIGHTS[k] * v for k, (v, _) in dims.items() if v is not None)
    den = sum(WEIGHTS[k] for k, (v, _) in dims.items() if v is not None)
    overall = num / den if den else 0.0
    category = classify(obj, cap, overall)
    no_functional_signal = not (i_f["domain"] or i_f["capability"])
    if no_functional_signal and CATEGORY_RANK[category] > CATEGORY_RANK[OverlapCategory.related]:
        # Guardrail: without any recognised domain or capability, similarity cannot justify overlap claims.
        category = OverlapCategory.related

    # Feature-level comparison (initiative features are retrieved facts; idea side from concepts)
    shared_features, other_features = [], []
    idea_caps = {x for x in i_f["capability"] if _w(x) > GENERIC}
    idea_doms = {x for x in i_f["domain"] if _w(x) >= 0.9}
    for feat in profile.features:
        ff = concepts_by_facet(extract_concepts(feat))
        feat_caps = {x for x in ff["capability"] if _w(x) > GENERIC}
        # A feature is "shared" when it delivers one of the idea's capabilities; features without any
        # capability concept fall back to a specific shared problem domain.
        is_shared = bool(feat_caps & idea_caps) if feat_caps else bool({x for x in ff["domain"] if _w(x) >= 0.9} & idea_doms)
        (shared_features if is_shared else other_features).append(feat)
    shared = shared_features or _label_list(i_func & (p_f["domain"] | p_f["capability"]))
    idea_only = _label_list(i_func - (p_f["domain"] | p_f["capability"]))
    initiative_only = other_features or _label_list((p_struct_f["domain"] | p_struct_f["capability"]) - i_func)[:5]

    dimension_models = [DimensionScore(name=k, label=DIMENSION_LABELS[k], weight=WEIGHTS[k],
                                       score=None if v is None else round(v, 3), explanation=e)
                        for k, (v, e) in dims.items()]
    rationale = _rationale(category, obj, cap, overall)
    return OverlapResult(category, round(overall, 3), dimension_models, shared[:8], idea_only[:6], initiative_only[:6], rationale)


def _rationale(cat: OverlapCategory, obj: float, cap: float, overall: float) -> str:
    base = f"objective {obj:.2f}, capabilities {cap:.2f}, overall {overall:.2f}"
    if cat == OverlapCategory.near_duplicate:
        return f"Classified as {CATEGORY_LABELS[cat]}: the business objective and core capabilities both align very closely ({base})."
    if cat == OverlapCategory.strong_overlap:
        return f"Classified as {CATEGORY_LABELS[cat]}: the business objective and most core capabilities align ({base})."
    if cat == OverlapCategory.partial_overlap:
        if obj >= 0.55 and cap < 0.55:
            return f"Classified as {CATEGORY_LABELS[cat]}: same problem area, but the core capabilities differ ({base})."
        return f"Classified as {CATEGORY_LABELS[cat]}: some capabilities overlap, but objectives or scope differ ({base})."
    if cat == OverlapCategory.related:
        return f"Classified as {CATEGORY_LABELS[cat]}: shares some terminology or a broader domain, but solves a different problem ({base})."
    return f"No significant overlap ({base})."
