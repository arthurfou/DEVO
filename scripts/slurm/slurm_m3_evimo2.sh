#!/bin/bash
# M3 EVIMO2 — entraînement COUPLÉ auto-supervisé (from weights M1 EVIMO2).
#SBATCH --job-name=m3_evimo2
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=3-00:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo2}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_evimo2.yaml}
MS_WEIGHTS=${MS_WEIGHTS:-$MS_MODEL/checkpoints/evimo2-run1/best.pt}
STEPS=${STEPS:-40000}
FREEZE=${FREEZE:-10000}
N_FRAMES=${N_FRAMES:-15}
SELFSUP_K=${SELFSUP_K:-3.0}
OUTDIR=${OUTDIR:-results_coupled/m3_evimo2}

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
export PYTHONUNBUFFERED=1
mkdir -p logs

python -u train_coupled.py \
    --log_every 2 \
    --dataset evimo --datapath "$DATAPATH" \
    --devo_weights "$DEVO_WEIGHTS" \
    --ms_config "$MS_CONFIG" \
    --ms_weights "$MS_WEIGHTS" \
    --outdir "$OUTDIR" \
    --selfsup --selfsup_k "$SELFSUP_K" \
    --n_frames "$N_FRAMES" --steps "$STEPS" --freeze_devo_steps "$FREEZE"
