from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Analysis, AuditLog


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, analysis_id: str) -> Analysis | None:
        return self.db.get(Analysis, analysis_id)

    def list(self, limit: int = 50) -> list[Analysis]:
        return list(self.db.scalars(select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)))

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Analysis)) or 0

    def count_flagged(self) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Analysis).where(Analysis.top_category.in_(["near_duplicate", "strong_overlap"]))
        ) or 0


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, actor: str, action: str, detail: dict, analysis_id: str | None = None, duration_ms: float | None = None) -> None:
        self.db.add(AuditLog(at=datetime.now(timezone.utc), actor=actor, action=action, analysis_id=analysis_id,
                             detail=detail, duration_ms=duration_ms))
        self.db.commit()

    def list(self, limit: int = 100) -> list[AuditLog]:
        return list(self.db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(limit)))
