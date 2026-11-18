from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyses, catalog, ideas
from app.config import get_settings
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    if settings.auto_seed:
        from app.seed.seed import is_seeded, seed

        if not is_seeded():
            logging.getLogger(__name__).info("Seeding synthetic dataset: %s", seed())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Idea Discovery API", version="0.1.0", lifespan=lifespan,
                  description="Enterprise Idea Discovery & Validation Agent (PoC). All enterprise data is synthetic.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(analyses.router)
    app.include_router(ideas.router)
    app.include_router(catalog.router)
    return app


app = create_app()
