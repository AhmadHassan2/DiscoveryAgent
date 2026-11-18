# Idea Discovery — local development commands
PY := backend/.venv/bin/python
DB ?= idea_discovery

.PHONY: setup db seed reset backend frontend dev test eval scenarios build

setup:            ## Install backend (venv) and frontend dependencies
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -q --upgrade pip
	backend/.venv/bin/pip install -q -r backend/requirements.txt
	cd frontend && pnpm install
	@test -f frontend/.env.local || cp frontend/.env.example frontend/.env.local

db:               ## Create the local PostgreSQL database (pgvector is enabled on first start)
	-createdb $(DB)

seed:             ## Seed synthetic data (no-op if already seeded)
	cd backend && .venv/bin/python -m app.seed.seed

reset:            ## Drop all data (history, registered ideas) and re-seed
	cd backend && .venv/bin/python -m app.seed.seed --reset

backend:          ## Run the API on :8000
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:         ## Run the web app on :3000
	cd frontend && pnpm dev

dev:              ## Run backend and frontend together
	$(MAKE) -j2 backend frontend

test:             ## Backend test-suite (isolated SQLite database)
	cd backend && .venv/bin/python -m pytest -q

eval:             ## Evaluation set report
	cd backend && .venv/bin/python scripts/run_eval.py

scenarios:        ## Print results of every demo scenario
	cd backend && .venv/bin/python scripts/run_scenarios.py

build:            ## Type-check, lint and build the frontend
	cd frontend && npx tsc --noEmit && pnpm lint && pnpm build
