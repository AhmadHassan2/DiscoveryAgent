"""Stage 5-6: normalise, de-duplicate and correlate records into initiatives.

Records are linked to initiatives only through *source-native* evidence, in priority order:

  1. shared project label / component / repository topic registered for an initiative
  2. the record's own key (Jira key, repo name, catalogue number) registered for an initiative
  3. an explicit link to a registered key (e.g. Jira epic -> repository)
  4. a textual mention of a registered key (e.g. "Jira: SEC-284")
  5. the initiative name or alias in the record title
  6. the initiative name or alias in the record body

Records that cannot be linked by any of these rules are never merged by guesswork. Connected
groups of unlinked records become "unindexed" candidates; isolated ones are reported as
unlinked evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.db.models import Initiative
from app.schemas.records import NormalizedRecord, SourceSystem


@dataclass
class EvidenceLink:
    record: NormalizedRecord
    matched: bool
    reason: str


@dataclass
class Candidate:
    key: str
    kind: str  # initiative | registered_idea | unindexed
    initiative: Initiative | None = None
    evidence: dict[str, EvidenceLink] = field(default_factory=dict)

    @property
    def matched_records(self) -> list[NormalizedRecord]:
        return [e.record for e in self.evidence.values() if e.matched]

    @property
    def retrieval_score(self) -> float:
        scores = sorted((r.fused_score for r in self.matched_records), reverse=True)
        return round(sum(s * w for s, w in zip(scores, (1.0, 0.5, 0.3, 0.2, 0.1))), 5)


def dedupe(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    """Merge duplicate hits for the same record (e.g. returned for several queries)."""
    by_id: dict[str, NormalizedRecord] = {}
    for rec in records:
        existing = by_id.get(rec.id)
        if existing is None:
            by_id[rec.id] = rec.model_copy()
            continue
        existing.keyword_score = max(existing.keyword_score, rec.keyword_score)
        existing.semantic_score = max(existing.semantic_score, rec.semantic_score)
        existing.fused_score = max(existing.fused_score, rec.fused_score)
        existing.matched_queries = list(dict.fromkeys(existing.matched_queries + rec.matched_queries))
    return list(by_id.values())


class InitiativeMatcher:
    def __init__(self, initiatives: list[Initiative]):
        self.initiatives = {i.id: i for i in initiatives}
        self.key_index: dict[str, str] = {}
        self.alias_patterns: list[tuple[re.Pattern[str], str, str]] = []
        for i in initiatives:
            for key in i.correlation_keys or []:
                self.key_index[key.lower()] = i.id
            for name in [i.name, *(i.aliases or [])]:
                self.alias_patterns.append((re.compile(r"(?<![\w-])" + re.escape(name.lower()) + r"(?![\w-])"), i.id, name))
        self.mention_keys = [(k, iid) for k, iid in self.key_index.items() if ("-" in k or "/" in k) and len(k) >= 5]

    def assign(self, rec: NormalizedRecord) -> tuple[str, str] | None:
        if rec.source == SourceSystem.idea_registry:
            return None
        for label in rec.labels:
            iid = self.key_index.get(label.lower())
            if iid:
                return iid, f"Shares the project label '{label}'"
        base_key = rec.external_key.split("#")[0].lower()
        if base_key in self.key_index:
            return self.key_index[base_key], f"Record key {rec.external_key.split('#')[0]} is registered to this initiative"
        for link in rec.links:
            iid = self.key_index.get(link.lower().replace("conf:", ""))
            if iid:
                return iid, f"Links to {link}"
        body = f"{rec.title} {rec.content}".lower()
        for key, iid in self.mention_keys:
            if re.search(r"(?<![\w-])" + re.escape(key) + r"(?![\w-])", body):
                return iid, f"Mentions {key.upper() if '-' in key and '/' not in key else key}"
        title = rec.title.lower()
        for pattern, iid, name in self.alias_patterns:
            if pattern.search(title):
                return iid, f"Title references '{name}'"
        for pattern, iid, name in self.alias_patterns:
            if pattern.search(rec.content.lower()):
                return iid, f"Content references '{name}'"
        return None


def _union_find_groups(records: list[NormalizedRecord]) -> list[list[NormalizedRecord]]:
    parent = {r.id: r.id for r in records}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_key = {r.external_key.split("#")[0].lower(): r.id for r in records}
    for r in records:
        targets = {l.lower() for l in r.links}
        body = f"{r.title} {r.content}".lower()
        for key, rid in by_key.items():
            if rid == r.id:
                continue
            if key in targets or (len(key) >= 5 and key in body):
                parent[find(r.id)] = find(rid)
    groups: dict[str, list[NormalizedRecord]] = {}
    for r in records:
        groups.setdefault(find(r.id), []).append(r)
    return list(groups.values())


def correlate(records: list[NormalizedRecord], initiatives: list[Initiative]) -> tuple[list[Candidate], list[NormalizedRecord]]:
    """Group retrieved records into candidates. Returns (candidates, unlinked_records)."""
    matcher = InitiativeMatcher(initiatives)
    candidates: dict[str, Candidate] = {}
    unassigned: list[NormalizedRecord] = []
    for rec in records:
        if rec.source == SourceSystem.idea_registry:
            candidates[rec.id] = Candidate(key=rec.external_key, kind="registered_idea",
                                           evidence={rec.id: EvidenceLink(rec, True, "Registered idea")})
            continue
        assignment = matcher.assign(rec)
        if assignment is None:
            unassigned.append(rec)
            continue
        iid, reason = assignment
        cand = candidates.setdefault(iid, Candidate(key=iid, kind="initiative", initiative=matcher.initiatives[iid]))
        cand.evidence[rec.id] = EvidenceLink(rec, True, reason)

    unlinked: list[NormalizedRecord] = []
    for group in _union_find_groups(unassigned):
        if len(group) >= 2:
            key = f"UNINDEXED-{sorted(r.id for r in group)[0]}"
            candidates[key] = Candidate(key=key, kind="unindexed",
                                        evidence={r.id: EvidenceLink(r, True, "Cross-referenced by other unindexed records") for r in group})
        else:
            unlinked.extend(group)
    return list(candidates.values()), unlinked


def expand(candidates: list[Candidate], related_records: list[NormalizedRecord], initiatives: list[Initiative]) -> None:
    """Attach linked records (not directly retrieved) to their initiatives as supporting evidence."""
    matcher = InitiativeMatcher(initiatives)
    by_init = {c.key: c for c in candidates if c.kind == "initiative"}
    for rec in related_records:
        assignment = matcher.assign(rec)
        if not assignment:
            continue
        iid, reason = assignment
        cand = by_init.get(iid)
        if cand and rec.id not in cand.evidence:
            cand.evidence[rec.id] = EvidenceLink(rec, False, reason)
