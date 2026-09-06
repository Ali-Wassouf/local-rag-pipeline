#!/usr/bin/env bash
# Local RAG — one-time environment setup for Apple Silicon.
# Run this yourself. Do not delegate it to a coding agent: it installs system
# services and downloads several GB of model weights.

set -euo pipefail

echo "==> Homebrew packages"
# Postgres is NOT here — it runs in Docker Compose (see docker-compose.yml).
# Ollama must be native: Docker on macOS has no Metal access, so a
# containerised Ollama would run CPU-only.
# node@22 is required alongside the system node: brew's pnpm needs Node >=22.13
# to run at all, so pnpm is invoked against this keg-only install (see justfile)
# rather than replacing whatever node the system already has.
brew install ollama uv pnpm just node@22
brew services start ollama

echo "==> Waiting for Ollama"
for i in {1..30}; do
  curl -sf http://localhost:11434/api/tags >/dev/null && break
  sleep 1
done

echo "==> Pulling models"
# Tags move. Verify against https://ollama.com/library before trusting these.
ollama pull qwen3:8b
ollama pull qwen3-embedding:0.6b

echo "==> Creating generation model with an explicit context window"
# Ollama's default num_ctx is small. RAG prompts overflow it silently and drop
# the front of the context, which looks like the model ignoring your sources.
cat > /tmp/Modelfile.rag <<'EOF'
FROM qwen3:8b
PARAMETER num_ctx 8192
PARAMETER num_batch 512
PARAMETER temperature 0.2
EOF
ollama create rag-gen -f /tmp/Modelfile.rag

echo "==> Configuring Ollama for a 16GB machine"
# Only one model resident at a time; unload quickly so the embedder does not
# sit in memory competing with generation.
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_KEEP_ALIVE 60s
brew services restart ollama

echo "==> Waiting for Ollama to come back up"
for i in {1..30}; do
  curl -sf http://localhost:11434/api/tags >/dev/null && break
  sleep 1
done

echo "==> Verifying embedding dimension"
RESP=$(curl -s http://localhost:11434/api/embed \
  -d '{"model":"qwen3-embedding:0.6b","input":"dimension probe"}')

DIM=$(printf '%s' "$RESP" | python3 -c '
import sys, json
try:
    print(len(json.load(sys.stdin)["embeddings"][0]))
except Exception:
    print("0")
')

if [ "$DIM" = "0" ]; then
  echo "!!! Could not read an embedding. Raw response:"
  echo "$RESP"
  exit 1
fi

echo "    embedder returns ${DIM} dimensions"
if [ "$DIM" != "1024" ]; then
  echo "!!! Expected 1024 to match Vector(1024) in the schema."
  echo "!!! Either pick a 1024-dim embedder or change the migration BEFORE indexing."
  exit 1
fi

echo "==> Reranker (downloads on first use, not via Ollama)"
uv pip install --system sentence-transformers
python3 - <<'EOF'
from sentence_transformers import CrossEncoder
CrossEncoder("BAAI/bge-reranker-base")
print("    reranker cached")
EOF

echo
echo "Done. Sanity check:"
echo "  ollama list"
echo "  ollama run rag-gen 'reply with just: ok'"
echo
echo "Postgres runs in Docker, not here:"
echo "  docker compose up -d"
echo "  psql postgresql://rag:rag@localhost:5432/rag -c 'SELECT 1'"
