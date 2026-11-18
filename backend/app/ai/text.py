"""Text normalisation shared by keyword search, the concept lexicon and the local embedder."""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    """a an and are as at be been being but by can could do does for from had has have having how i if in into is it
    its it's let me more most my no not of on or our ours out over own so some such than that the their them then there
    these they this those through to too under up very was we were what when where which while who whom why will with
    would you your yours want wants build built building create make using use used across also any all each other
    new one two three via per within without about should help helps tool tools system systems platform solution based
    internal team teams company organisation organization us lets idea ideas need needs like just""".split()
)


def stem(token: str) -> str:
    """A deliberately small, predictable stemmer (no external dependency)."""
    t = token
    if len(t) <= 3:
        return t
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    for suf in ("sses", "xes", "ches", "shes", "zes"):
        if t.endswith(suf):
            return t[:-2]
    if t.endswith("ing") and len(t) > 5:
        t = t[:-3]
        return t[:-1] if len(t) > 3 and t[-1] == t[-2] else t
    if t.endswith("ed") and len(t) > 4 and not t.endswith("eed"):
        t = t[:-2]
        t = t[:-1] if len(t) > 3 and t[-1] == t[-2] else t
        return t[:-1] if len(t) > 3 and t.endswith("e") else t
    if t.endswith("s") and not t.endswith(("ss", "us", "is")):
        t = t[:-1]
    if len(t) > 3 and t.endswith("e") and not t.endswith(("ee", "ie")):
        t = t[:-1]
    return t


def normalize(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = text.replace("real-time", "real time").replace("e-mail", "email")
    return text


def tokens(text: str) -> list[str]:
    """Raw lowercase tokens (no stemming, stopwords kept)."""
    return _TOKEN_RE.findall(normalize(text))


def stemmed_tokens(text: str, drop_stopwords: bool = False) -> list[str]:
    out = []
    for tok in tokens(text):
        if drop_stopwords and tok in STOPWORDS:
            continue
        out.append(stem(tok))
    return out


def content_terms(text: str) -> list[str]:
    """Stemmed, stopword-free terms used for keyword (BM25) scoring."""
    return [t for t in stemmed_tokens(text, drop_stopwords=True) if len(t) > 1]


_NEGATION_RE = re.compile(
    r"\b(out of scope|not in scope|does not|do not|doesn't|don't|is not|isn't|no longer|not planned|no real[- ]time|"
    r"non[- ]goal|excluded|without|will not|won't|never|deferred to|defers|rather than|instead of|unlike)\b",
    re.IGNORECASE,
)


def strip_negated_sentences(text: str) -> str:
    """Remove sentences that describe what something does NOT do (e.g. "Out of scope: real-time
    scoring"), so they are not mistaken for capabilities."""
    sentences = re.split(r"(?<=[.!?;])\s+|\n+", text)
    return " ".join(s for s in sentences if not _NEGATION_RE.search(s))
