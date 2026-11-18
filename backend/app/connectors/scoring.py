"""Keyword (BM25) scoring and rank fusion used by connectors."""
from __future__ import annotations

import math
from collections import Counter

from app.ai.text import content_terms


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.4, b: float = 0.75):
        self.k1, self.b = k1, b
        self.doc_terms = [Counter(content_terms(d)) for d in docs]
        self.doc_len = [sum(c.values()) for c in self.doc_terms]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 1.0
        df: Counter[str] = Counter()
        for c in self.doc_terms:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query_terms: dict[str, float]) -> list[float]:
        scores = []
        for terms, length in zip(self.doc_terms, self.doc_len):
            s = 0.0
            for term, qw in query_terms.items():
                tf = terms.get(term)
                if not tf:
                    continue
                idf = self.idf.get(term, 0.0)
                s += qw * idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * length / (self.avgdl or 1)))
            scores.append(s)
        return scores


def weighted_query_terms(primary: list[str], expansion: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for text in primary:
        for t in content_terms(text):
            out[t] = max(out.get(t, 0.0), 1.0)
    for text in expansion:
        for t in content_terms(text):
            out[t] = max(out.get(t, 0.0), 0.5)
    return out


def rrf(rank: int | None, k: int = 60) -> float:
    return 0.0 if rank is None else 1.0 / (k + rank + 1)
