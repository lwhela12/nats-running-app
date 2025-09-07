#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WEB_DIR="$ROOT_DIR/apps/web"

cd "$WEB_DIR"

# Ensure API base exists
if [ ! -f .env.local ]; then
  echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
fi

npm install >/dev/null
exec npx next dev -p 3000

