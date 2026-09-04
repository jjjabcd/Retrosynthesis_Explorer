#!/usr/bin/env bash
# Shared Conda discovery; source this file from the project root.
find_conda() {
  if [[ -n "${CONDA_EXE:-}" && -x "$CONDA_EXE" ]]; then printf '%s\n' "$CONDA_EXE"; return; fi
  if command -v conda >/dev/null 2>&1; then command -v conda; return; fi
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" /opt/homebrew/Caskroom/miniforge/base /opt/miniconda3 /opt/anaconda3; do
    if [[ -x "$base/bin/conda" ]]; then printf '%s\n' "$base/bin/conda"; return; fi
  done
  echo 'Conda was not found. Install Miniforge or Miniconda, then set CONDA_EXE or run from a Conda terminal.' >&2
  return 1
}
