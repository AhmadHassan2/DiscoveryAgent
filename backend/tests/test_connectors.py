"""Connector search, normalisation, permission filtering and failure isolation."""
import asyncio

from app.ai.embeddings import get_embedder
from app.connectors.registry import all_connectors
from app.pipeline.retrieve import search_all
from app.schemas.records import ConnectorSearchRequest, ConnectorStatus, SearchQuery, SourceSystem
from app.security.access import MockPermissionFilter, Principal


def _req(text: str) -> ConnectorSearchRequest:
    return ConnectorSearchRequest(queries=[SearchQuery(text=text)], query_embedding=get_embedder().embed([text])[0], limit=10)


def test_keyword_and_semantic_search_return_normalized_records():
    jira = all_connectors()[SourceSystem.jira]
    results = jira.search(_req("automated vulnerability scanner for repositories"))
    keys = [r.external_key for r in results]
    assert "SEC-284" in keys
    top = results[0]
    assert top.source == SourceSystem.jira and top.url.startswith("https://jira.northbridge.example/")
    assert top.updated_at.tzinfo is not None
    assert top.keyword_score > 0 or top.semantic_score > 0


def test_semantic_retrieval_finds_records_without_shared_keywords():
    # "SAST" never appears in this query, but the SecureGuard repo is still retrieved semantically.
    gh = all_connectors()[SourceSystem.github]
    results = gh.search(_req("tool that flags insecure code and suggests patches"))
    assert any(r.external_key == "northbridge-appsec/secureguard-scanner" for r in results)


def test_permission_filter_hides_restricted_records():
    conf = all_connectors()[SourceSystem.confluence]
    raw = conf.search(_req("identity access request platform consolidation"))
    allowed, hidden = MockPermissionFilter().filter(raw, Principal(id="t"))
    assert any(r.acl.classification == "restricted" for r in raw)
    assert hidden >= 1 and all(r.acl.classification != "restricted" for r in allowed)
    insider = Principal(id="t", groups=frozenset({"all-employees", "ma-integration-core"}))
    _, hidden_insider = MockPermissionFilter().filter(raw, insider)
    assert hidden_insider == 0


def test_fetch_related_follows_cross_references():
    sn = all_connectors()[SourceSystem.servicenow]
    keys = [r.external_key for r in sn.fetch_related(["accessflow", "APP0004417"])]
    assert {"APP0004417", "KB0012873", "CHG0039921"} <= set(keys)


def test_connector_failure_is_isolated():
    connectors = list(all_connectors().values())
    started, done = [], []
    results = asyncio.run(search_all(connectors, _req("vulnerability scanning"), Principal(id="t"), {"sharepoint"},
                                     started.append, done.append))
    by_source = {r.source: r for r in results}
    assert by_source[SourceSystem.sharepoint].status == ConnectorStatus.error
    assert by_source[SourceSystem.jira].status == ConnectorStatus.ok and by_source[SourceSystem.jira].records
    assert len(started) == len(done) == len(connectors)


def test_connector_health_reports_counts():
    h = all_connectors()[SourceSystem.confluence].health()
    assert h.record_count > 0 and h.read_only and h.mode == "mock"
