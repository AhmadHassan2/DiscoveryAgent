"""Keyword/semantic building blocks: stemming, lexicon, negation handling and embeddings."""
from app.ai.embeddings import LocalConceptEmbedder, cosine
from app.ai.lexicon import concept_set
from app.ai.text import content_terms, stem, strip_negated_sentences


def test_stemming_is_consistent_across_inflections():
    assert stem("vulnerabilities") == stem("vulnerability")
    assert stem("scans") == stem("scanning") == stem("scan")
    assert stem("arrived") == stem("arrive")


def test_content_terms_drop_stopwords():
    assert "the" not in content_terms("Scan the repositories for issues")


def test_different_terminology_maps_to_same_concepts():
    a = concept_set("static application security testing (SAST)")
    b = concept_set("secure code analysis of our codebase")
    assert "code_scanning" in a and "code_scanning" in b


def test_operations_language_maps_to_data_quality():
    assert "data_quality" in concept_set("a source file arrived late or half empty so the numbers are wrong")
    assert "data_quality" in concept_set("freshness and schema drift checks on warehouse tables")


def test_negated_scope_statements_are_removed():
    text = "CaseLens summarises cases. Out of scope: real-time transaction scoring. It drafts SAR narratives."
    cleaned = strip_negated_sentences(text)
    assert "real-time" not in cleaned and "SAR" in cleaned
    assert "realtime_detection" not in concept_set(cleaned)


def test_local_embedder_is_deterministic_and_semantic():
    e = LocalConceptEmbedder()
    q = e.embed_one("automatically scan code repositories for vulnerabilities")
    assert q == e.embed_one("automatically scan code repositories for vulnerabilities")
    near = e.embed_one("static application security testing with remediation suggestions")
    far = e.embed_one("summarise fraud investigation cases for investigators")
    assert cosine(q, near) > cosine(q, far) + 0.2
