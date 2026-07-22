#!/bin/bash
#SBATCH --job-name=preprocess_datasets
#SBATCH --partition=cpu-long
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=6:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
DATASET_BASE=${DATASET_BASE:-/home/i/i0002573/arthur_ipal/datasets}

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

# EDS
if [ -d "$DATASET_BASE/eds/00_peanuts_dark" ]; then
  echo "=== Preprocessing EDS ==="
  python scripts/pp_eds.py --indir "$DATASET_BASE/eds" --outdir "$DATASET_BASE/eds"
else
  echo "SKIP EDS: data not found"
fi

# TUM-VIE
if [ -d "$DATASET_BASE/tumvie/mocap-shake/left_images" ]; then
  echo "=== Preprocessing TUM-VIE ==="
  python scripts/pp_tumvie.py --indir "$DATASET_BASE/tumvie" --camId 0
else
  echo "SKIP TUM-VIE: data not found or not structured correctly"
fi

# VECtor
if [ -f "$DATASET_BASE/vector/0_calib/left_event_camera_intrinsic_results.yaml" ]; then
  echo "=== Preprocessing VECtor ==="
  python scripts/pp_vector.py --indir "$DATASET_BASE/vector" --outdir "$DATASET_BASE/vector"
else
  echo "SKIP VECtor: calibration not found"
fi

# MVSEC
if [ -f "$DATASET_BASE/mvsec/indoor_flying1_data.hdf5" ] && [ -f "$DATASET_BASE/mvsec/indoor_flying1_gt.hdf5" ]; then
  echo "=== Preprocessing MVSEC ==="
  python scripts/pp_mvsec.py --indir "$DATASET_BASE/mvsec"
else
  echo "SKIP MVSEC: GT HDF5 files missing (rate-limited, retry downloads)"
fi

echo "ALL PREPROCESSING DONE"
