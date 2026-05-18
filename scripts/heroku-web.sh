#!/usr/bin/env bash
# Heroku web process: ephemeral disk — ingest must run on the same dyno that serves traffic.
# Skip ingest if chroma_db already populated (same dyno, no restart yet).
set -e
cd "$(dirname "$0")/.."

if [[ ! -d chroma_db ]] || [[ -z "$(ls -A chroma_db 2>/dev/null || true)" ]]; then
  echo "-----> No Chroma data in slug; running ingest.py"
  python ingest.py
else
  echo "-----> Chroma data present; skipping ingest"
fi

exec uvicorn app:app --host=0.0.0.0 --port="${PORT:?PORT must be set}"
