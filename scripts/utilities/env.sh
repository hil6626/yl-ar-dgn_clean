#!/bin/bash
# Simple env loader for scripts
export AR_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "AR_PROJECT_ROOT=${AR_PROJECT_ROOT}"
