#!/bin/bash
set -e
# 清理临时缓存示例
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Cleaning cache under $ROOT/tmp if exists"
if [ -d "$ROOT/tmp" ]; then
  rm -rf "$ROOT/tmp/*" || true
fi
echo "done"
