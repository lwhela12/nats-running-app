#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

cd "$API_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -e .[dev] >/dev/null

# Run DB migrations from repo root so alembic's relative paths resolve
cd "$ROOT_DIR"
alembic -c ops/migrations/alembic.ini upgrade head

# Start API
cd "$API_DIR"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
