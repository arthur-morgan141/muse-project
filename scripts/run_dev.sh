#!/usr/bin/env bash
set -e

# ==============================================================================
# Development Launcher for Meta Muse
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if [ -f "${PROJECT_ROOT}/.venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/.venv/bin/activate"
fi

export MUSE_ENV="development"
export MUSE_LOG_LEVEL="DEBUG"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"

echo "=== [MUSE DEV ENVIRONMENT] ==="
echo "Project Root : ${PROJECT_ROOT}"
echo "Python Exec  : $(which python3)"
echo "Environment  : ${MUSE_ENV}"
echo "=============================="

exec python3 -m muse.cli "$@"
