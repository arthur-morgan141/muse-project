#!/usr/bin/env bash
set -e

# ==============================================================================
# Production Launcher for Meta Muse
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if [ -f "${PROJECT_ROOT}/.venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/.venv/bin/activate"
fi

export MUSE_ENV="production"
export MUSE_LOG_LEVEL="INFO"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"

exec python3 -m muse.cli "$@"
