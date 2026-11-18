from sqlalchemy import text

from app.db.models import Base
from app.db.session import get_engine


def init_db(drop: bool = False) -> None:
    engine = get_engine()
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    if drop:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
