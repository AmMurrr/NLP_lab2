#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-qwen2.5:0.5b}"
FASTAPI_PORT="${FASTAPI_PORT:-8000}"

cleanup() {
  if [[ -n "${OLLAMA_PID:-}" ]]; then
    kill "$OLLAMA_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ollama serve >/tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

for _ in $(seq 1 60); do
  if curl -sSf http://127.0.0.1:11434/api/tags >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -sSf http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "Ollama server did not start in time" >&2
  exit 1
fi

if ! ollama list | awk '{print $1}' | grep -Fx "$MODEL_NAME" >/dev/null 2>&1; then
  echo "Pulling model: $MODEL_NAME"
  ollama pull "$MODEL_NAME"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "$FASTAPI_PORT"
