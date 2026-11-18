# Idea Discovery: Enterprise Idea Discovery & Validation Agent (PoC)

Idea Discovery checks whether an idea already exists before anyone starts building it. An employee describes the idea in plain English. The agent then:

- searches Confluence, Jira, GitHub Enterprise, SharePoint, Teams, ServiceNow and the Idea Registry
- groups the records it finds into initiatives
- classifies how much each initiative overlaps with the idea, citing the evidence
- identifies the owner and lifecycle stage of each initiative
- recommends what to do next: contact the owning team, evaluate an existing service, reuse components, or register the idea

> **Proof of concept.** All enterprise systems are simulated by mock connectors over synthetic data for a fictional organisation, *Northbridge Financial*. The search, correlation, scoring and analysis are fully implemented. Only the source systems are simulated.

## Quick start (macOS, native, no Docker needed)

Prerequisites:
- Python 3.11+
- Node 20+ with pnpm
- PostgreSQL 15+ running locally, with the **pgvector** extension (`brew install postgresql@17 pgvector`)

```bash
make setup      # creates backend/.venv, installs Python + Node dependencies
make db         # createdb idea_discovery
make seed       # loads the synthetic dataset (also happens automatically on first API start)
make dev        # API on http://localhost:8000, web app on http://localhost:3000
```

Open **http://localhost:3000**. The API docs are at **http://localhost:8000/docs**.

If you'd rather run the two servers in separate terminals:

```bash
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
cd frontend && pnpm dev
```

| Command | Purpose |
|---|---|
| `make reset` | Drop all data (history, registered ideas) and re-seed. Run this before a demo. |
| `make test` | Backend test suite (66 tests, isolated SQLite database) |
| `make eval` | Evaluation report over 24 free-form ideas |
| `make scenarios` | Print the result of every demo scenario |
| `make build` | Frontend type-check, lint and production build |

### Docker (optional)

`docker compose up --build` starts pgvector Postgres, the API and the web app. The database is exposed on port 5433, so it won't clash with a local Postgres.

## Configuration

Copy `.env.example` to `.env` (in the repo root or `backend/`). Every setting is optional.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://localhost:5432/idea_discovery` | PostgreSQL with pgvector |
| `LLM_PROVIDER` | `auto` | `auto`, `anthropic`, `openai_compatible` or `none` |
| `ANTHROPIC_API_KEY` | — | Enables Claude through the official `anthropic` SDK |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Claude model |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | — | Any OpenAI-compatible endpoint, such as an internal LLM gateway |
| `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` | — | Remote embedding model (OpenAI-compatible `/embeddings`) |
| `MOCK_CONNECTOR_LATENCY_MS` | `350` | Simulated network latency of mock connectors (labelled as simulated; `0` disables it) |
| `FAIL_SOURCES` | — | Force sources to fail, e.g. `sharepoint`, to demonstrate degraded behaviour |

**AI modes.** The UI always shows which mode produced a result:
- **Deterministic demo mode:** no LLM is configured. A rule-based concept lexicon plus a local embedder produces repeatable results.
- **Full:** the LLM enriches the idea understanding and reviews the top matches.
- **Degraded:** an LLM is configured but failed during the run. The rule-based results are shown with a warning.

### Using Claude (Sonnet 5.5)

Set `ANTHROPIC_API_KEY` in `.env`, or log in with the `ant` CLI (`ant auth login`), then restart the API. The top bar will show `AI: claude-sonnet-5-5`.

The request includes server-side refusal fallbacks (`fallbacks: "default"`). Every LLM output is checked against a schema and against the rules: the AI can move a category by at most one level, and any citation that doesn't match a retrieved record is dropped.

> A Claude Code subscription login cannot be reused by this app. The app needs an Anthropic API credential.

## Repository layout

```
backend/   FastAPI + SQLAlchemy + pgvector — connectors, pipeline, API, seed data, tests
frontend/  Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
ARCHITECTURE.md  design, data flow, scoring, security, path to production
DEMO_GUIDE.md    step-by-step presentation script
```

## What is real and what is simulated

| Functional | Simulated |
|---|---|
| Hybrid retrieval (BM25 + pgvector cosine, fused with RRF) | The source systems themselves (Confluence, Jira, …). Mock connectors read synthetic records from Postgres. |
| Concurrent connector fan-out, timeouts, failure isolation | Network latency (configurable, labelled) |
| Cross-source correlation via labels, keys, links and mentions | Enterprise SSO identity: a placeholder principal is used |
| 5-dimension overlap scoring, classification guardrails, lifecycle inference | Source ACLs: per-record ACL metadata is synthetic |
| Live SSE progress, reports, history, export, audit log | |
| Idea Registry with duplicate-registration check, re-discoverable ideas | |
| Claude / OpenAI-compatible LLM integration with validation and fallback | |

See **ARCHITECTURE.md** for limitations and the path to production, and **DEMO_GUIDE.md** for the presentation script.
