#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
source scripts/conda.sh
conda_executable="$(find_conda)"
environment_path="$PWD/.conda-env"
if [[ ! -x "$environment_path/bin/python" ]]; then
  "$conda_executable" create --prefix "$environment_path" --override-channels -c conda-forge python=3.11 pip -y
fi
"$conda_executable" run --no-capture-output -p "$environment_path" python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)'
if [[ "$(uname -s)" == "Darwin" ]]; then
  "$conda_executable" install --prefix "$environment_path" --override-channels -c conda-forge llvm-openmp -y
fi
"$conda_executable" run --no-capture-output -p "$environment_path" python -m pip install -c constraints.txt ./aizynfinder -e .
"$conda_executable" run --no-capture-output -p "$environment_path" python -m pip check
echo 'Downloading public assets. Attribution and terms: docs/MODEL_DATA_SOURCES.md'
"$conda_executable" run --no-capture-output -p "$environment_path" python -m explorer.download
"$conda_executable" run --no-capture-output -p "$environment_path" python -m explorer.setup_accessibility
"$conda_executable" run --no-capture-output -p "$environment_path" python -m explorer.diagnose
echo 'Setup complete. Start the app with ./run.sh.'
