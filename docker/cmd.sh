#!/bin/sh
set -e
exec python -m uvicorn resume_tailor.api.app:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8765}"
