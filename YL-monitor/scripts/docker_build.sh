#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

IMAGE_TAG="${1:-yl-monitor:local}"

echo "🏗️  Building image: ${IMAGE_TAG}"
docker build -t "${IMAGE_TAG}" .
echo "✅ Done"

