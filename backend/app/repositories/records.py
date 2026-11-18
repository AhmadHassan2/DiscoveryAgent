from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import Float, cast, func, literal, or_, select
from sqlalchemy.orm import Session

from app.ai.embeddings import cosine
from app.db.models import Idea, Initiative, SourceRecord


def cosine_distance(column, vector: list[float]):
    """pgvector cosine distance (`<=>`) between a vector column and a query vector."""
    from pgvector.sqlalchemy import Vector

    from app.config import get_settings

    query = cast(literal("[" + ",".join(f"{v:.6f}" for v in vector) + "]"), Vector(get_settings().embedding_dimensions))
    return column.op("<=>", return_type=Float)(query)


class RecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_source(self, source: str) -> list[SourceRecord]:
        return list(self.db.scalars(select(SourceRecord).where(SourceRecord.source == source).order_by(SourceRecord.updated_at.desc())))

    def list_all(self) -> list[SourceRecord]:
        return list(self.db.scalars(select(SourceRecord)))

    def get(self, record_id: str) -> SourceRecord | None:
        return self.db.get(SourceRecord, record_id)

    def count_by_source(self) -> dict[str, int]:
        rows = self.db.execute(select(SourceRecord.source, func.count()).group_by(SourceRecord.source)).all()
        return {s: c for s, c in rows}

    def semantic_search(self, source: str, vector: list[float], k: int) -> list[tuple[SourceRecord, float]]:
        """Top-k records of one source by cosine similarity (pgvector when on PostgreSQL)."""
        if self.db.get_bind().dialect.name == "postgresql":
            distance = cosine_distance(SourceRecord.embedding, vector)
            rows = self.db.execute(
                select(SourceRecord, distance.label("d"))
                .where(SourceRecord.source == source, SourceRecord.embedding.is_not(None))
                .order_by(distance)
                .limit(k)
            ).all()
            return [(r, 1.0 - float(d)) for r, d in rows]
        records = self.list_by_source(source)
        scored = [(r, cosine(vector, r.embedding)) for r in records if r.embedding]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def find_related(self, keys: Iterable[str], aliases: Iterable[str] = ()) -> list[SourceRecord]:
        """Records that reference any of the given correlation keys (labels, external keys, links)."""
        keys = {k for k in keys if k}
        lowered = {k.lower() for k in keys}
        out: list[SourceRecord] = []
        for rec in self.list_all():
            if rec.external_key in keys or rec.external_key.split("#")[0] in keys:
                out.append(rec)
                continue
            if lowered & {lbl.lower() for lbl in (rec.labels or [])}:
                out.append(rec)
                continue
            if keys & set(rec.links or []):
                out.append(rec)
        return out


class InitiativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Initiative]:
        return list(self.db.scalars(select(Initiative).order_by(Initiative.name)))

    def get(self, initiative_id: str) -> Initiative | None:
        return self.db.get(Initiative, initiative_id)


class IdeaRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, q: str | None = None, status: str | None = None) -> list[Idea]:
        stmt = select(Idea).order_by(Idea.created_at.desc())
        if status:
            stmt = stmt.where(Idea.status == status)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func.lower(Idea.title).like(like), func.lower(Idea.description).like(like),
                                  func.lower(func.coalesce(Idea.department, "")).like(like),
                                  func.lower(Idea.submitted_by).like(like)))
        return list(self.db.scalars(stmt))

    def get(self, idea_id: str) -> Idea | None:
        return self.db.get(Idea, idea_id)

    def next_id(self) -> str:
        ids = [i for i in self.db.scalars(select(Idea.id))]
        nums = [int(i.split("-")[1]) for i in ids if i.startswith("IDEA-") and i.split("-")[1].isdigit()]
        return f"IDEA-{(max(nums) + 1 if nums else 1):04d}"

    def semantic_search(self, vector: list[float], k: int) -> list[tuple[Idea, float]]:
        if self.db.get_bind().dialect.name == "postgresql":
            distance = cosine_distance(Idea.embedding, vector)
            rows = self.db.execute(select(Idea, distance.label("d")).where(Idea.embedding.is_not(None)).order_by(distance).limit(k)).all()
            return [(r, 1.0 - float(d)) for r, d in rows]
        scored = [(i, cosine(vector, i.embedding)) for i in self.list() if i.embedding]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]
