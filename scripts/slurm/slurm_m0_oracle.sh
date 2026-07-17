#!/bin/bash
# M0 — gate décisif : DEVO vanilla vs masque oracle GT -> delta ATE (voir ../../../RECAP_M0_M4.md).
# À LANCER EN PREMIER. Éval rapide (pas d'entraînement).
#SBATCH --job-name=m0_oracle
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

# === Cluster NUS SoC (i0002573) — chemins ; surchargables via --export=ALL,VAR=... ===
REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo_filtered_2805/eval}   # scènes preprocessées (evs.npy, gt_stamped.txt)
MASK_ROOT=${MASK_ROOT:-/home/i/i0002573/arthur_ipal/datasets/evimo_full/eval}          # npz EVIMO (mask+meta)
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/evimo/evimo_val.txt}
THICKEN=${THICKEN:-2}
# =========================================================================

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

python evals/eval_evs/eval_evimo_m0_oracle.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --mask_root "$MASK_ROOT" \
    --thicken_radius "$THICKEN"
