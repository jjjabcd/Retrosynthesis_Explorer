#!/bin/bash
set -euo pipefail

BASE_DIR="/data/rlawlsgurjh/work/gitlab/CUE/cue_vs/results/"

TARGET="6S89"
TARGET_COL="PI"
SCORE_COL="Proxy"
MODEL="CUE"
TRIAL="Trial_1"

SMILES_CSV="${BASE_DIR}${TARGET}/${MODEL}/${TRIAL}/${SCORE_COL}/${TARGET_COL}/06_sa_score_filtered.csv"
OUTPUT_DIR="${BASE_DIR}${TARGET}/${MODEL}/${TRIAL}/${SCORE_COL}/${TARGET_COL}/aizynthfinder/"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /data/rlawlsgurjh/miniconda3/etc/profile.d/conda.sh
conda activate aizynth-env

python "${SCRIPT_DIR}/run.py" \
    --config "${SCRIPT_DIR}/data/advanced_config.yml" \
    --smiles_csv "${SMILES_CSV}" \
    --output_dir "${OUTPUT_DIR}"