"""Embedding providers.

* `RemoteEmbeddingProvider` calls an OpenAI-compatible `/embeddings` endpoint (e.g. an
  enterprise LLM gateway).
* `LocalConceptEmbedder` is deterministic and offline: it feature-hashes stemmed terms plus
  lexicon concepts into a fixed-size vector. Texts that use different vocabulary for the same
  concept share concept features, which gives useful (though approximate) semantic similarity.
"""
from __future__ import annotations

import hashlib
import logging
import math
from functools import lru_cache
from typing import Protocol

from app.ai.lexicon import CONCEPT_BY_ID, extract_concepts
from app.ai.text import content_terms
from app.config import get_settings

log = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    name: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _bucket(feature: str, dim: int) -> tuple[int, float]:
    digest = hashlib.md5(feature.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "little") % dim
    sign = 1.0 if digest[4] & 1 else -1.0
    return idx, sign


class LocalConceptEmbedder:
    name = "local-concept-hash-v1"

    def __init__(self, dimensions: int = 384, concept_weight: float = 2.5, term_weight: float = 0.35):
        self.dimensions = dimensions
        self.concept_weight = concept_weight
        self.term_weight = term_weight

    def embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for cid, count in extract_concepts(text).items():
            concept = CONCEPT_BY_ID[cid]
            weight = self.concept_weight * concept.weight * (1.0 + math.log(count))
            idx, sign = _bucket("c:" + cid, self.dimensions)
            vec[idx] += sign * weight
        term_counts: dict[str, int] = {}
        for term in content_terms(text):
            term_counts[term] = term_counts.get(term, 0) + 1
        for term, count in term_counts.items():
            idx, sign = _bucket("t:" + term, self.dimensions)
            vec[idx] += sign * self.term_weight * (1.0 + math.log(count))
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class RemoteEmbeddingProvider:
    def __init__(self, base_url: str, api_key: str | None, model: str, dimensions: int):
        from openai import OpenAI

        self.name = f"remote:{model}"
        self.dimensions = dimensions
        self._model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-required", timeout=30.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts, dimensions=self.dimensions)
        return [list(d.embedding) for d in resp.data]


class FallbackEmbeddingProvider:
    """Uses the remote provider when available; falls back to the local embedder on error."""

    def __init__(self, primary: EmbeddingProvider | None, fallback: LocalConceptEmbedder):
        self.primary = primary
        self.fallback = fallback
        self.dimensions = fallback.dimensions
        self.last_used = fallback.name

    @property
    def name(self) -> str:
        return self.primary.name if self.primary else self.fallback.name

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.primary is not None:
            try:
                out = self.primary.embed(texts)
                self.last_used = self.primary.name
                return out
            except Exception as exc:  # pragma: no cover - network dependent
                log.warning("Remote embedding failed, using local embedder: %s", exc)
        self.last_used = self.fallback.name
        return self.fallback.embed(texts)


@lru_cache(maxsize=1)
def get_embedder() -> FallbackEmbeddingProvider:
    s = get_settings()
    local = LocalConceptEmbedder(dimensions=s.embedding_dimensions)
    primary = None
    if s.remote_embeddings_enabled:
        primary = RemoteEmbeddingProvider(s.embedding_base_url, s.embedding_api_key, s.embedding_model, s.embedding_dimensions)  # type: ignore[arg-type]
    return FallbackEmbeddingProvider(primary, local)


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
