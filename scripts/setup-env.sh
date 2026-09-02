#!/usr/bin/env bash
# Local RAG — one-time environment setup for Apple Silicon.
# Run this yourself. Do not delegate it to a coding agent: it installs system
# services and downloads several GB of model weights.

set -euo pipefail

echo "==> Homebrew packages"
brew install ollama postgresql@16 pgvector uv pnpm just
brew services start ollama
brew services start postgresql@16

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

echo "==> Verifying embedding dimension"
DIM=$(curl -sf http://localhost:11434/api/embed \
  -d '{"model":"qwen3-embedding:0.6b","input":"dimension probe"}' \
  | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["embeddings"][0]))')

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
echo "  psql postgres -c 'SELECT 1'"
