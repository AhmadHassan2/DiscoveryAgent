"""Test configuration: an isolated SQLite database seeded with the synthetic dataset.

Set TEST_DATABASE_URL to run the suite against PostgreSQL/pgvector instead.
"""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="idea-discovery-tests-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["MOCK_CONNECTOR_LATENCY_MS"] = "0"
os.environ["LLM_PROVIDER"] = "none"
os.environ["FAIL_SOURCES"] = ""
os.environ["AUTO_SEED"] = "true"

import pytest  # noqa: E402

from app.db.session import SessionLocal, configure_engine  # noqa: E402
from app.seed.seed import seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    configure_engine(os.environ["DATABASE_URL"])
    seed(reset=True)
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(autouse=True)
def _remove_ideas_registered_during_test():
    """Keep tests independent: drop ideas registered by a test once it finishes."""
    yield
    from app.db.models import Idea
    from app.seed.dataset import SEED_IDEAS

    seeded = {i["id"] for i in SEED_IDEAS}
    with SessionLocal() as db:
        for idea in db.query(Idea).all():
            if idea.id not in seeded:
                db.delete(idea)
        db.commit()
