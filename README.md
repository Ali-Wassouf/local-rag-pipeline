# Local RAG Pipeline

A local, single-user Retrieval-Augmented Generation pipeline: upload books,
reports, manuals, slide decks, or plain text; the pipeline extracts structure,
chunks and embeds it, and lets you ask grounded questions over it in a chat
UI with section-path citations. Everything — extraction, embedding, and
generation — runs on your own machine. No document content or query ever
leaves it.

See [`docs/plan.md`](docs/plan.md) for the full design and
[`docs/build-phases.md`](docs/build-phases.md) for what's built so far.
[`PRODUCT.md`](PRODUCT.md) has the durable product context.

## Requirements

Built and tested on **Apple Silicon macOS**. The setup script assumes
Homebrew and a Metal GPU (Ollama needs to run natively, not in Docker, to use
it — see below).

- macOS on Apple Silicon
- [Homebrew](https://brew.sh)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or
  another Docker Compose–compatible runtime) — this runs Postgres only
- ~10GB free disk for model weights

Everything else (Ollama, `uv`, `pnpm`, `just`, `node@22`) is installed by the
setup script below.

### Why isn't Ollama containerized too?

Only Postgres runs in Docker on purpose. Docker Desktop on macOS runs
containers inside a Linux VM with no Metal/GPU passthrough, so a
containerized Ollama would fall back to CPU-only inference. For an 8B
generation model on a 16GB Apple Silicon Mac, that's the difference between
usable interactive chat and a multi-second-per-token crawl — running Ollama
natively is what makes local generation viable on this hardware at all.

If you're moving this to a machine without that constraint (a Linux box with
an NVIDIA GPU passed through to Docker, for instance), containerizing Ollama
is fine there — it's a deployment-environment tradeoff, not a hard
architectural requirement. The backend and worker aren't containerized
either, for a different reason: at single-user scale with `just dev` already
giving hot-reload, containerizing them would trade away that simplicity for
isolation this project doesn't need.

## 1. One-time environment setup

```bash
./scripts/setup-env.sh
```

**Run this yourself — don't have an agent run it.** It installs system
services (via `brew`) and downloads several GB of model weights. It's safe
to re-run.

What it does:

1. Installs `ollama`, `uv`, `pnpm`, `just`, `node@22` via Homebrew and starts
   the Ollama service. (Postgres is *not* installed here — it runs in Docker,
   see step 2. Ollama runs natively rather than in Docker so it can use the
   Mac's GPU; a containerized Ollama on macOS has no Metal access and would
   fall back to CPU.)
2. Pulls the two models the pipeline uses from Ollama's registry:
   `qwen3:8b` (generation) and `qwen3-embedding:0.6b` (embedding, 1024
   dimensions — this must match the `Vector(1024)` column in the schema).
3. Creates a derived generation model, `rag-gen`, from `qwen3:8b` with an
   explicit `num_ctx 8192` — Ollama's default context window is small enough
   that a RAG prompt can silently overflow it and lose sources, which looks
   like the model ignoring your documents.
4. Sets `OLLAMA_MAX_LOADED_MODELS=1` and a short `OLLAMA_KEEP_ALIVE`, since
   embedding and generation share one Ollama process on a 16GB machine and
   should not both stay resident.
5. Verifies the embedder actually returns 1024-dimensional vectors.
6. Installs `sentence-transformers` and pre-downloads a cross-encoder
   reranker (`BAAI/bge-reranker-base`). This is prep for the hybrid
   search/reranking phase in `docs/build-phases.md`; the current pipeline
   doesn't call it yet.

Model tags on Ollama's registry can move — if a pull fails, check
[ollama.com/library](https://ollama.com/library) for the current tag.

## 2. Database

Postgres runs in Docker; the app and worker run natively.

```bash
just db-up
```

This starts `pgvector/pgvector:pg16` in Docker Compose
([`docker-compose.yml`](docker-compose.yml)) and waits for it to be ready.
On first boot, Postgres runs
[`scripts/init-extensions.sql`](scripts/init-extensions.sql), which creates
the three extensions the schema needs: `vector` (embeddings), `ltree`
(section tree paths), and `pg_trgm` (keyword search).

**How the tables get created:** the schema itself isn't in that SQL file —
it comes from Alembic. Run the migration:

```bash
just migrate
# equivalent to: cd backend && uv run alembic upgrade head
```

This applies [`backend/alembic/versions/05cb0d50e6ad_initial_schema.py`](backend/alembic/versions/05cb0d50e6ad_initial_schema.py),
a single migration that creates the full schema described in
[`docs/plan.md` §2](docs/plan.md) (projects, documents, sections, chunks,
embedding_runs, ingest_jobs, conversations, messages, message_citations,
and their indexes) against whatever's at `DATABASE_URL`. There's no ORM
`create_all()` path — migrations are the only way tables get created, and
`just db-up && just migrate` should give you a clean schema from zero.

## 3. Install app dependencies

```bash
cd backend && uv sync && cd ..
cd frontend && pnpm install && cd ..
```

(`uv run` in later steps will also sync automatically if you skip this, but
doing it explicitly here catches dependency errors early.)

`pnpm` (installed via Homebrew) needs Node ≥22.13, which is why setup
installed `node@22` as a separate, keg-only formula rather than replacing
your system Node. The `justfile` already puts it first on `PATH` for you; if
you run `pnpm` commands by hand outside `just`, prefix them:

```bash
PATH="/opt/homebrew/opt/node@22/bin:$PATH" pnpm install
```

## 4. Verify Ollama is up and dimensions match

```bash
just check-models
```

This fails loudly if Ollama isn't running, or if the embedder isn't
returning exactly 1024-dimensional vectors (which would silently break
retrieval against the `Vector(1024)` column).

## 5. Run everything

```bash
just dev
```

This runs three processes in parallel (backend API, ingest worker, frontend
dev server) and kills all three together on Ctrl-C:

- FastAPI backend — `http://localhost:8000`
- Ingest worker — a plain asyncio polling loop, no output unless a job fails
- Frontend (Vite) — `http://localhost:5173`

Open `http://localhost:5173`. CORS on the backend only allows that origin by
default (`backend/app/main.py`).

### Running pieces individually

```bash
# backend API
cd backend && uv run uvicorn app.main:app --reload --port 8000

# ingest worker (separate process so a long book ingest doesn't block chat)
cd backend && uv run python -m app.ingest.worker

# frontend
cd frontend && PATH="/opt/homebrew/opt/node@22/bin:$PATH" pnpm dev
```

### Sanity check

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl -X POST http://localhost:8000/documents -F "file=@/path/to/some.pdf"
```

## Configuration

Defaults in [`backend/app/core/config.py`](backend/app/core/config.py) match
the Docker Compose Postgres credentials, so nothing needs to be set for a
default local setup. To override, create `backend/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://rag:rag@localhost:5432/rag
STORAGE_DIR=./data/uploads
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
GENERATION_MODEL=rag-gen
WORKER_POLL_INTERVAL_SECONDS=1.0
```

The frontend reads the API origin from `VITE_API_BASE_URL` (defaults to
`http://localhost:8000`); set it in `frontend/.env` if you change the
backend port.

## Tests

```bash
just test
```

Runs `mypy --strict` and `pytest` on the backend, then `vitest` on the
frontend. Most backend tests hit a real Postgres (per project convention,
the database is never mocked — pgvector and ltree behavior is the thing
under test), so `just db-up && just migrate` first. Tests that need Ollama
skip gracefully if it isn't reachable.

## Troubleshooting

- **`just check-models` fails / embedder returns the wrong dimension** —
  re-run `ollama pull qwen3-embedding:0.6b`; if you swap embedding models,
  that's a migration plus a full re-index, never an in-place edit (see
  `CLAUDE.md`).
- **Ollama answers seem to ignore your documents** — check the model
  actually being called is `rag-gen` (has `num_ctx 8192`), not bare
  `qwen3:8b` with Ollama's small default context.
- **`pnpm install` / `pnpm dev` fails with an engine error** — you're on the
  system Node, not `node@22`; see the `PATH` prefix above.
- **Uploading a PDF fails as a "scanned document"** — this is by design: the
  character-count-per-page check rejects scanned PDFs (no OCR is planned).
- **Postgres extensions missing** — `init-extensions.sql` only runs on the
  *first* container boot against an empty volume. If you changed it after
  the volume already existed, run `docker compose down -v` (this deletes the
  data) and `just db-up` again, or apply the SQL manually.
