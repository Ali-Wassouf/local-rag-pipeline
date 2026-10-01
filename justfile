set shell := ["bash", "-cu"]

# pnpm (brew) needs Node >=22.13; the system default node stays untouched.
node_bin := "/opt/homebrew/opt/node@22/bin"

default:
    @just --list

db-up:
    docker compose up -d db
    @echo "waiting for postgres..."
    @until docker compose exec -T db pg_isready -U rag -d rag >/dev/null 2>&1; do sleep 1; done
    @echo "postgres is ready"

migrate:
    cd backend && uv run alembic upgrade head

dev:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && uv run uvicorn app.main:app --reload --port 8000) &
    (cd backend && uv run python -m app.ingest.worker) &
    (cd frontend && PATH="{{node_bin}}:$PATH" pnpm dev) &
    wait

test:
    cd backend && uv run mypy app && uv run pytest
    cd frontend && PATH="{{node_bin}}:$PATH" pnpm test

backfill-summaries project_id="":
    cd backend && uv run python -m app.ingest.backfill_summaries {{ if project_id == "" { "" } else { "--project-id " + project_id } }}

check-models:
    curl -sf http://localhost:11434/api/tags >/dev/null || (echo "ollama is not running"; exit 1)
    @echo "ollama is up"
    curl -s http://localhost:11434/api/embed \
        -d '{"model":"qwen3-embedding:0.6b","input":"dimension probe"}' \
      | python3 -c 'import sys, json; d = json.load(sys.stdin)["embeddings"][0]; print(f"embedder returns {len(d)} dims"); raise SystemExit(0 if len(d) == 1024 else 1)'
