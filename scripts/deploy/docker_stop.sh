#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

COMPOSE_BIN="docker compose"
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker-compose"
fi

echo "🛑 Stopping containers..."
${COMPOSE_BIN} down
echo "✅ Done"

