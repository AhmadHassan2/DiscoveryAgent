"""Mock connector backed by the synthetic records stored in the local database.

The mock performs a real hybrid search (BM25 keyword scoring + vector similarity via pgvector)
over the synthetic records for its source system. Only the *source system* is simulated — the
retrieval itself is genuine. An optional, clearly-labelled simulated network latency can be
configured with MOCK_CONNECTOR_LATENCY_MS (set 0 to disable).
"""
from __future__ import annotations

from collections import Counter
from datetime import timezone

from sqlalchemy import func, select

from app.connectors.base import SourceConnector
from app.connectors.scoring import BM25, rrf, weighted_query_terms
from app.db.models import SourceRecord
from app.db.session import SessionLocal
from app.repositories.records import RecordRepository
from app.schemas.records import (
    AccessControl,
    ConnectorHealth,
    ConnectorSearchRequest,
    ConnectorStatus,
    NormalizedRecord,
)

MIN_SEMANTIC = 0.22
MIN_KEYWORD_NORM = 0.18


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def to_normalized(rec: SourceRecord) -> NormalizedRecord:
    return NormalizedRecord(
        id=rec.id, source=rec.source, record_type=rec.record_type, external_key=rec.external_key,
        title=rec.title, content=rec.content, url=rec.url, author=rec.author, owner=rec.owner,
        source_status=rec.source_status, created_at=_aware(rec.created_at), updated_at=_aware(rec.updated_at),
        labels=list(rec.labels or []), links=list(rec.links or []), metadata=dict(rec.extra or {}),
        acl=AccessControl(**(rec.acl or {})),
    )


class MockDatabaseConnector(SourceConnector):
    """Shared implementation; subclasses only declare the source and descriptions."""

    def _records(self, db) -> list[SourceRecord]:
        return RecordRepository(db).list_by_source(self.source.value)

    def search(self, request: ConnectorSearchRequest) -> list[NormalizedRecord]:
        with SessionLocal() as db:
            records = self._records(db)
            if not records:
                return []
            docs = [f"{r.title} {r.title} {' '.join(r.labels or [])} {r.content}" for r in records]
            bm25 = BM25(docs)
            primary = [q.text for q in request.queries]
            kw_scores = bm25.score(weighted_query_terms(primary, request.expansion_terms))
            max_kw = max(kw_scores) or 1.0
            kw_rank = {records[i].id: rank for rank, i in enumerate(sorted(range(len(records)), key=lambda i: -kw_scores[i])) if kw_scores[i] > 0}

            sem: dict[str, float] = {}
            if request.query_embedding:
                for rec, sim in RecordRepository(db).semantic_search(self.source.value, request.query_embedding, k=max(request.limit * 2, 20)):
                    sem[rec.id] = sim
            sem_rank = {rid: rank for rank, rid in enumerate(sorted(sem, key=lambda r: -sem[r]))}

            # Which individual queries matched each record (for explainability)
            per_query_terms = {q.text: weighted_query_terms([q.text], []) for q in request.queries}

            results: list[NormalizedRecord] = []
            for i, rec in enumerate(records):
                kw_norm = kw_scores[i] / max_kw if max_kw else 0.0
                sim = sem.get(rec.id, 0.0)
                if kw_norm < MIN_KEYWORD_NORM and sim < MIN_SEMANTIC:
                    continue
                n = to_normalized(rec)
                n.keyword_score = round(kw_norm, 4)
                n.semantic_score = round(sim, 4)
                n.fused_score = round(rrf(kw_rank.get(rec.id)) + rrf(sem_rank.get(rec.id)) + 0.02 * kw_norm + 0.02 * sim, 5)
                rec_terms = set(bm25.doc_terms[i])
                n.matched_queries = [q for q, terms in per_query_terms.items() if rec_terms & set(terms)][:5]
                results.append(n)
            results.sort(key=lambda r: -r.fused_score)
            return results[: request.limit]

    def fetch_related(self, keys: list[str]) -> list[NormalizedRecord]:
        with SessionLocal() as db:
            return [to_normalized(r) for r in RecordRepository(db).find_related(keys) if r.source == self.source.value]

    def health(self) -> ConnectorHealth:
        with SessionLocal() as db:
            rows = db.execute(select(SourceRecord.record_type).where(SourceRecord.source == self.source.value)).all()
            last = db.scalar(select(func.max(SourceRecord.updated_at)).where(SourceRecord.source == self.source.value))
        types = Counter(r[0] for r in rows)
        return ConnectorHealth(
            source=self.source, display_name=self.display_name, status=ConnectorStatus.ok, mode=self.mode,
            record_count=sum(types.values()), record_types=dict(types), last_indexed_at=_aware(last), description=self.description,
        )
