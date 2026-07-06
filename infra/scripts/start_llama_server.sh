#!/usr/bin/env bash
set -euo pipefail

LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
PRESET_FILE="/Users/dio/ActiveProject/my-project/infra/scripts/models.ini"

pids=$(lsof -ti tcp:8080 || true)
if [ -n "$pids" ]; then
  kill -9 $pids
fi

"$LLAMA_SERVER" \
  --models-preset "$PRESET_FILE" \
  --models-max 1 \
  --host 0.0.0.0 \
  --port 8080 \
  --jinja \
  > llama-router.log 2>&1