"""Mock connectors for each simulated enterprise system.

To integrate a real system, implement `SourceConnector` (see base.py) with the system's
approved read-only API, map responses into `NormalizedRecord`, and register it in
`registry.py` in place of the mock.
"""
from __future__ import annotations

from datetime import timezone

from sqlalchemy import func, select

from app.connectors.base import SourceConnector
from app.connectors.mock_base import MIN_SEMANTIC, MockDatabaseConnector
from app.connectors.scoring import BM25, weighted_query_terms
from app.db.models import Idea
from app.db.session import SessionLocal
from app.repositories.records import IdeaRepository
from app.schemas.records import (
    AccessControl,
    ConnectorHealth,
    ConnectorSearchRequest,
    ConnectorStatus,
    NormalizedRecord,
    SourceSystem,
)


class ConfluenceConnector(MockDatabaseConnector):
    source = SourceSystem.confluence
    display_name = "Confluence"
    description = "Research reports, technical proposals, architecture documents, PoC findings and roadmaps."


class JiraConnector(MockDatabaseConnector):
    source = SourceSystem.jira
    display_name = "Jira"
    description = "Epics, stories and tasks with statuses, assignees and linked issues."


class GitHubConnector(MockDatabaseConnector):
    source = SourceSystem.github
    display_name = "GitHub Enterprise"
    description = "Repository metadata, READMEs and pull requests (project-level evidence; source code is not searched)."


class SharePointConnector(MockDatabaseConnector):
    source = SourceSystem.sharepoint
    display_name = "SharePoint"
    description = "Project presentations, business cases, innovation proposals and research findings."


class TeamsConnector(MockDatabaseConnector):
    source = SourceSystem.teams
    display_name = "Microsoft Teams"
    description = "Posts in standard project channels explicitly authorised for indexing. Private chats are never searched."


class ServiceNowConnector(MockDatabaseConnector):
    source = SourceSystem.servicenow
    display_name = "ServiceNow"
    description = "Deployed applications (CMDB), service catalogue items, change records and knowledge articles."


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def idea_to_record(idea: Idea) -> NormalizedRecord:
    content = " ".join(p for p in [idea.description, idea.business_problem, idea.proposed_functionality,
                                   f"Target users: {idea.target_users}" if idea.target_users else None,
                                   f"Technologies: {idea.technologies}" if idea.technologies else None] if p)
    return NormalizedRecord(
        id=f"idea_registry:{idea.id}", source=SourceSystem.idea_registry, record_type="registered_idea",
        external_key=idea.id, title=idea.title, content=content, url=f"/registry?idea={idea.id}",
        author=idea.submitted_by, owner=idea.submitted_by, source_status=idea.status,
        created_at=_aware(idea.created_at), updated_at=_aware(idea.updated_at), labels=[], links=list(idea.related_initiative_ids or []),
        metadata={"department": idea.department, "team": idea.team, "submitted_by": idea.submitted_by,
                  "related_initiative_ids": idea.related_initiative_ids or []},
        acl=AccessControl(),
    )


class IdeaRegistryConnector(SourceConnector):
    """Searches ideas registered through this application (this one is a real, local source)."""

    source = SourceSystem.idea_registry
    display_name = "Idea Registry"
    description = "Ideas submitted and registered through Idea Discovery."
    mode = "local"

    def search(self, request: ConnectorSearchRequest) -> list[NormalizedRecord]:
        with SessionLocal() as db:
            repo = IdeaRepository(db)
            ideas = repo.list()
            if not ideas:
                return []
            bm25 = BM25([f"{i.title} {i.title} {i.description} {i.business_problem or ''} {i.proposed_functionality or ''}" for i in ideas])
            kw = bm25.score(weighted_query_terms([q.text for q in request.queries], request.expansion_terms))
            max_kw = max(kw) or 1.0
            sem = {i.id: s for i, s in repo.semantic_search(request.query_embedding, k=20)} if request.query_embedding else {}
            out = []
            for idx, idea in enumerate(ideas):
                kw_norm = kw[idx] / max_kw if max_kw else 0.0
                sim = sem.get(idea.id, 0.0)
                if kw_norm < 0.25 and sim < MIN_SEMANTIC + 0.05:
                    continue
                rec = idea_to_record(idea)
                rec.keyword_score, rec.semantic_score = round(kw_norm, 4), round(sim, 4)
                rec.fused_score = round(0.5 * kw_norm + 0.5 * sim, 5) / 20
                out.append(rec)
            out.sort(key=lambda r: -(r.keyword_score + r.semantic_score))
            return out[: request.limit]

    def fetch_related(self, keys: list[str]) -> list[NormalizedRecord]:
        return []

    def health(self) -> ConnectorHealth:
        with SessionLocal() as db:
            count = db.scalar(select(func.count()).select_from(Idea)) or 0
            last = db.scalar(select(func.max(Idea.updated_at)))
        return ConnectorHealth(source=self.source, display_name=self.display_name, status=ConnectorStatus.ok, mode=self.mode,
                               record_count=count, record_types={"registered_idea": count}, last_indexed_at=_aware(last),
                               description=self.description)
