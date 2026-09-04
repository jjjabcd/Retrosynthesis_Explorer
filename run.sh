#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
source scripts/conda.sh
conda_executable="$(find_conda)"
if [[ ! -x "$PWD/.conda-env/bin/python" ]]; then echo 'Run ./setup.sh first.' >&2; exit 1; fi
exec "$conda_executable" run --no-capture-output -p "$PWD/.conda-env" python -m explorer.launcher "$@"
