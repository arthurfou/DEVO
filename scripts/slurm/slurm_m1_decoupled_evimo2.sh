#!/bin/bash
# M1 — baseline suppression apprise découplée sur EVIMO2 : DEVO + convlstm entraîné séparément (+ oracle).
# Éval rapide (pas d'entraînement).
#SBATCH --job-name=m1_decoupled_evimo2
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo2/eval_preprocessed}
MASK_ROOT=${MASK_ROOT:-/home/i/i0002573/arthur_ipal/datasets/evimo2/evimo1_format}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/evimo2/evimo2_val.txt}
MS_WEIGHTS=${MS_WEIGHTS:-$MS_MODEL/checkpoints/evimo2-run1/best.pt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_evimo2.yaml}

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

python evals/eval_evs/eval_evimo2_m1_decoupled.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --mask_root "$MASK_ROOT" \
    --ms_weights "$MS_WEIGHTS" \
    --ms_config "$MS_CONFIG" \
    --with_oracle
