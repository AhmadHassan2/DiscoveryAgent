"""API contract tests, idea registration and search history."""


def test_health_and_catalog(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["data_mode"] == "mock" and h["llm_provider"] == "deterministic"
    s = client.get("/api/sources").json()
    assert len(s["sources"]) == 7 and s["total_records"] > 50
    projects = client.get("/api/projects").json()
    assert len(projects) >= 25
    detail = client.get("/api/projects/INIT-001").json()
    assert detail["owner_name"] == "Priya Raman" and len(detail["records"]) >= 5
    assert client.get("/api/projects/NOPE").status_code == 404
    stats = client.get("/api/stats").json()
    assert stats["initiatives"] >= 25 and stats["departments"] >= 10
    graph = client.get("/api/graph").json()
    assert any(n["type"] == "initiative" for n in graph["nodes"]) and graph["edges"]
    assert len(client.get("/api/demo/scenarios").json()) >= 5


def test_restricted_records_are_redacted_in_source_explorer(client):
    recs = client.get("/api/sources/confluence/records").json()
    restricted = [r for r in recs if r["restricted"]]
    assert restricted and all(r["content"] == "" for r in restricted)


def test_analysis_lifecycle_history_comparison_and_export(client):
    created = client.post("/api/analyses", json={"idea": {"description": "AI cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes"}})
    assert created.status_code == 202
    aid = created.json()["id"]
    body = client.get(f"/api/analyses/{aid}").json()
    assert body["status"] == "completed" and body["report"]["matches"][0]["name"] == "SecureGuard AI"
    stages = {e["stage"] for e in body["events"]}
    assert {"understand", "queries", "search:jira", "search:github", "correlate", "analyze", "report"} <= stages
    events = client.get(f"/api/analyses/{aid}/events").text
    assert "search:confluence" in events
    assert any(a["id"] == aid for a in client.get("/api/analyses").json())
    comp = client.get(f"/api/analyses/{aid}/comparison/INIT-001").json()
    assert comp["shared"] and comp["rows"]
    md = client.get(f"/api/analyses/{aid}/export")
    assert md.status_code == 200 and "SecureGuard AI" in md.text and "not** calibrated" in md.text


def test_validation_errors(client):
    assert client.post("/api/analyses", json={"idea": {"description": "short"}}).status_code == 422


def test_register_new_idea_then_rediscover_it(client):
    idea = {"title": "Business travel carbon tracker",
            "description": "An app that calculates the carbon footprint of employee business travel and suggests lower-emission alternatives when booking flights and hotels.",
            "department": "Operations"}
    res = client.post("/api/ideas", json={"idea": idea, "submitted_by": "test.user@northbridge.example"})
    assert res.status_code == 201, res.text
    new_id = res.json()["id"]
    assert res.json()["status"] == "registered"
    assert any(i["id"] == new_id for i in client.get("/api/ideas", params={"q": "carbon"}).json())
    # A paraphrased search now discovers the registered idea
    created = client.post("/api/analyses", json={"idea": {"description": "Tool to measure CO2 emissions from staff flights and hotel stays"}})
    report = client.get(f"/api/analyses/{created.json()['id']}").json()["report"]
    match = next(m for m in report["matches"] if m["initiative_id"] == new_id)
    assert match["kind"] == "registered_idea" and match["category"] in ("strong_overlap", "near_duplicate")


def test_duplicate_registration_requires_acknowledgement(client):
    idea = {"description": "We want to build an AI-powered cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes."}
    blocked = client.post("/api/ideas", json={"idea": idea})
    assert blocked.status_code == 409
    assert blocked.json()["overlapping"][0]["name"] == "SecureGuard AI"
    ok = client.post("/api/ideas", json={"idea": idea, "acknowledge_overlap": True, "analysis_id": blocked.json()["analysis_id"],
                                         "acknowledgement_note": "Spoke to Priya; we will extend SecureGuard."})
    assert ok.status_code == 201
    body = ok.json()
    assert body["status"] == "registered_with_overlap" and "INIT-001" in body["acknowledged_overlap"]["initiatives"]


def test_audit_log_records_searches(client):
    client.post("/api/analyses", json={"idea": {"description": "Synthetic monitoring of partner API latency"}})
    actions = {a["action"] for a in client.get("/api/audit").json()}
    assert {"analysis.started", "analysis.completed"} <= actions
