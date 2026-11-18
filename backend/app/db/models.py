"""SQLAlchemy ORM models.

`Initiative` is the *Initiative Index*: a correlated catalogue of known initiatives (in a
real deployment this would be maintained by a periodic indexing/correlation job).
`SourceRecord` holds normalised records mirrored from the (mock) source systems.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


class EmbeddingType(TypeDecorator):
    """pgvector `vector(n)` on PostgreSQL, JSON list elsewhere (SQLite in tests)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(get_settings().embedding_dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        return [float(v) for v in value]

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        return [float(v) for v in value]


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON, list[Any]: JSON}


class Initiative(Base):
    __tablename__ = "initiatives"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    aliases: Mapped[list[Any]] = mapped_column(JSON, default=list)
    correlation_keys: Mapped[list[Any]] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(String(120))
    team: Mapped[str] = mapped_column(String(120))
    owner_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_objective: Mapped[str] = mapped_column(Text)
    core_features: Mapped[list[Any]] = mapped_column(JSON, default=list)
    target_users: Mapped[list[Any]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[Any]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reusable_components: Mapped[list[Any]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_initiative_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingType, nullable=True)


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), index=True)
    record_type: Mapped[str] = mapped_column(String(60))
    external_key: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Source-native correlation hints: labels/components/topics, explicit links, mentions.
    labels: Mapped[list[Any]] = mapped_column(JSON, default=list)
    links: Mapped[list[Any]] = mapped_column(JSON, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    acl: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingType, nullable=True)


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    business_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_functionality: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_users: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    team: Mapped[str | None] = mapped_column(String(120), nullable=True)
    technologies: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), default="registered")
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_initiative_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    acknowledged_overlap: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingType, nullable=True)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idea_text: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    request: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="running")
    capability_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    top_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    top_initiative_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    events: Mapped[list[Any]] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(60))
    analysis_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("analyses.id"), nullable=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
