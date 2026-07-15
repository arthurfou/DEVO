#!/bin/bash
# M2 — entraînement COUPLÉ supervisé (MS + DEVO, loss pose + masque GT). Long (jusqu'à 3 j).
# Produit results_coupled/m2/ms_final.pt (à rebrancher dans le tableau central M4).
#SBATCH --job-name=m2_coupled_sup
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=3-00:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

# === À ÉDITER ===
REPO_DEVO=${REPO_DEVO:-$HOME/IPAL/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-$HOME/IPAL/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-$HOME/IPAL/arthur_ipal/datasets/evimo_full/eval}  # racine npz EVIMO (events+depth+poses+mask)
DEVO_WEIGHTS=${DEVO_WEIGHTS:-DEVO.pth}
MS_WEIGHTS=${MS_WEIGHTS:-$MS_MODEL/checkpoints/v4-full-run1/best.pt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
OUTDIR=${OUTDIR:-results_coupled/m2}
STEPS=${STEPS:-20000}
FREEZE=${FREEZE:-5000}
N_FRAMES=${N_FRAMES:-15}
# ================

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devo
cd "$REPO_DEVO"
mkdir -p logs

python train_coupled.py \
    --dataset evimo --datapath "$DATAPATH" \
    --devo_weights "$DEVO_WEIGHTS" \
    --ms_weights "$MS_WEIGHTS" \
    --ms_config "$MS_CONFIG" \
    --outdir "$OUTDIR" \
    --provide_gt_mask \
    --n_frames "$N_FRAMES" --steps "$STEPS" --freeze_devo_steps "$FREEZE"
