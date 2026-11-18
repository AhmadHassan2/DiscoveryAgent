"""Seed (or reset) the database with the synthetic enterprise dataset.

    python -m app.seed.seed          # seed if empty
    python -m app.seed.seed --reset  # drop everything and re-seed
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.ai.embeddings import get_embedder
from app.db.init_db import init_db
from app.db.models import Idea, Initiative, SourceRecord
from app.db.session import SessionLocal
from app.seed.dataset import INITIATIVES, RECORDS, SEED_IDEAS, email

log = logging.getLogger(__name__)


def initiative_text(i: dict) -> str:
    return " ".join([i["name"], i["description"], i["business_objective"], " ".join(i["core_features"]),
                     " ".join(i["target_users"]), " ".join(i["technologies"])])


def record_text(r: dict) -> str:
    return f"{r['title']}. {r['content']}"


def idea_text(title: str, description: str, *extra: str | None) -> str:
    return " ".join(p for p in [title, description, *extra] if p)


def is_seeded() -> bool:
    with SessionLocal() as db:
        return (db.scalar(select(func.count()).select_from(Initiative)) or 0) > 0


def seed(reset: bool = False, now: datetime | None = None) -> dict[str, int]:
    init_db(drop=reset)
    if not reset and is_seeded():
        return {"skipped": 1}
    now = now or datetime.now(timezone.utc)
    embedder = get_embedder()

    def ago(days: int) -> datetime:
        return now - timedelta(days=days)

    with SessionLocal() as db:
        init_vecs = embedder.embed([initiative_text(i) for i in INITIATIVES])
        for i, vec in zip(INITIATIVES, init_vecs):
            db.add(Initiative(
                id=i["id"], name=i["name"], aliases=i["aliases"], correlation_keys=i["correlation_keys"],
                description=i["description"], department=i["department"], team=i["team"],
                owner_name=i["owner"], owner_email=email(i["owner"]) if i["owner"] else None,
                business_objective=i["business_objective"], core_features=i["core_features"],
                target_users=i["target_users"], technologies=i["technologies"], status=i["status"],
                created_at=ago(i["created_days_ago"]), last_activity_at=ago(i["last_activity_days_ago"]),
                reusable_components=i["reusable_components"], notes=i["notes"],
                related_initiative_ids=i.get("related_initiative_ids", []), embedding=vec,
            ))
        rec_vecs = embedder.embed([record_text(r) for r in RECORDS])
        for r, vec in zip(RECORDS, rec_vecs):
            db.add(SourceRecord(
                id=r["id"], source=r["source"], record_type=r["record_type"], external_key=r["external_key"],
                title=r["title"], content=r["content"], url=r["url"], author=r["author"], owner=r["owner"],
                source_status=r["source_status"], created_at=ago(r["created_days_ago"]), updated_at=ago(r["updated_days_ago"]),
                labels=r["labels"], links=r["links"], extra=r["extra"], acl=r["acl"], embedding=vec,
            ))
        idea_vecs = embedder.embed([idea_text(i["title"], i["description"]) for i in SEED_IDEAS])
        for i, vec in zip(SEED_IDEAS, idea_vecs):
            db.add(Idea(
                id=i["id"], title=i["title"], description=i["description"], department=i["department"], team=i["team"],
                submitted_by=i["submitted_by"], status=i["status"], related_initiative_ids=i["related_initiative_ids"],
                created_at=ago(i["days_ago"]), updated_at=ago(i["days_ago"]), embedding=vec,
            ))
        db.commit()
    return {"initiatives": len(INITIATIVES), "records": len(RECORDS), "ideas": len(SEED_IDEAS)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Idea Discovery synthetic dataset")
    parser.add_argument("--reset", action="store_true", help="Drop all tables and re-seed (removes registered ideas and history)")
    args = parser.parse_args()
    result = seed(reset=args.reset)
    if result.get("skipped"):
        print("Database already seeded. Use --reset to re-seed.")
    else:
        print(f"Seeded {result['initiatives']} initiatives, {result['records']} source records, {result['ideas']} registered ideas.")


if __name__ == "__main__":
    main()
