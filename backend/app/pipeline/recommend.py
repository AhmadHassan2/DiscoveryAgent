"""Stage 11-12: recommended next actions."""
from __future__ import annotations

from app.schemas.analysis import CATEGORY_RANK, InitiativeMatch, LifecycleStage, OverlapCategory, Recommendation

STRONG = {OverlapCategory.near_duplicate, OverlapCategory.strong_overlap}


def for_match(m: InitiativeMatch) -> list[Recommendation]:
    owner = m.owner.name if m.owner else "the owning team"
    team = f" ({m.team})" if m.team else ""
    stage = m.lifecycle.stage
    recs: list[Recommendation] = []
    reuse = ", ".join(m.reusable_components[:3])

    if m.kind == "registered_idea":
        if m.category in STRONG or m.category == OverlapCategory.partial_overlap:
            recs.append(Recommendation(type="contact_owner", label=f"Contact {owner}, who registered a similar idea",
                                       detail="Another employee has already registered a similar idea. Consider joining forces before either idea proceeds.",
                                       target_initiative_id=m.initiative_id))
        return recs

    if m.category in STRONG:
        if stage == LifecycleStage.deployed:
            recs.append(Recommendation(type="evaluate_existing", label=f"Evaluate {m.name} before building anything",
                                       detail=f"{m.name} is already deployed. Check whether it meets your needs, or request an enhancement from {owner}{team}.",
                                       target_initiative_id=m.initiative_id))
            recs.append(Recommendation(type="contact_owner", label=f"Talk to {owner} about gaps", priority=2,
                                       detail="If the deployed service misses something, an enhancement request is usually faster than a new build.",
                                       target_initiative_id=m.initiative_id))
        elif stage in (LifecycleStage.abandoned, LifecycleStage.retired):
            recs.append(Recommendation(type="review_history", label=f"Find out why {m.name} was {m.lifecycle.label.lower()}",
                                       detail=f"A similar initiative was tried before and stopped. Read its findings and speak to {owner} so you don't repeat the same issues.",
                                       target_initiative_id=m.initiative_id))
            if reuse:
                recs.append(Recommendation(type="request_reuse", label="Reuse its artefacts", priority=2,
                                           detail=f"Reusable work from the earlier initiative: {reuse}.", target_initiative_id=m.initiative_id))
        elif stage == LifecycleStage.paused:
            recs.append(Recommendation(type="contact_owner", label=f"Ask {owner} about restarting {m.name}",
                                       detail="The initiative is paused. Restarting or extending it may be cheaper than starting again.",
                                       target_initiative_id=m.initiative_id))
        else:
            recs.append(Recommendation(type="contact_owner", label=f"Contact {owner}{team} before starting",
                                       detail=f"{m.name} is in {m.lifecycle.label.lower()} and covers most of your idea. Agree with the team whether to join, extend or reuse it.",
                                       target_initiative_id=m.initiative_id))
            recs.append(Recommendation(type="extend_initiative", label=f"Propose extending {m.name}", priority=2,
                                       detail="If your requirements differ slightly, propose them as an extension of the existing scope.",
                                       target_initiative_id=m.initiative_id))
            if reuse:
                recs.append(Recommendation(type="request_reuse", label="Request access to reusable components", priority=3,
                                           detail=f"Available components: {reuse}.", target_initiative_id=m.initiative_id))
    elif m.category == OverlapCategory.partial_overlap:
        recs.append(Recommendation(type="scope_discussion", label=f"Compare scope with {owner}",
                                   detail=f"{m.name} covers part of your idea. Agree where the boundary sits so the two efforts complement each other.",
                                   target_initiative_id=m.initiative_id))
        if reuse:
            recs.append(Recommendation(type="request_reuse", label="Look at reusable components", priority=2,
                                       detail=f"Possibly reusable: {reuse}.", target_initiative_id=m.initiative_id))
    elif m.category == OverlapCategory.related:
        recs.append(Recommendation(type="awareness", label=f"Note: {m.name} is related", priority=3,
                                   detail="Different problem, but related terminology or domain. Optional: check for reusable components or expertise.",
                                   target_initiative_id=m.initiative_id))
    return recs


def primary(matches: list[InitiativeMatch]) -> Recommendation:
    top = next((m for m in matches if m.kind != "registered_idea"), matches[0] if matches else None)
    if top and CATEGORY_RANK[top.category] >= CATEGORY_RANK[OverlapCategory.partial_overlap] and top.recommendations:
        return top.recommendations[0]
    if matches and matches[0].kind == "registered_idea" and matches[0].category in STRONG and matches[0].recommendations:
        return matches[0].recommendations[0]
    return Recommendation(type="register_idea", label="Register your idea and proceed through normal approval",
                          detail="No significant overlap was found in the sources searched. Register the idea so others can find it, then follow your normal approval process.")
