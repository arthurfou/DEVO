#!/bin/bash
# M4 — tableau central : vanilla / oracle / appris découplé / couplé sup / couplé auto-sup.
# À LANCER APRÈS M1 (checkpoint découplé) et M2/M3 (checkpoints couplés). Éval rapide.
# Les lignes sans checkpoint fourni sont marquées "—".
#SBATCH --job-name=m4_central_table
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

# === À ÉDITER ===
REPO_DEVO=${REPO_DEVO:-$HOME/IPAL/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-$HOME/IPAL/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-$HOME/IPAL/arthur_ipal/datasets/evimo/eval}
MASK_ROOT=${MASK_ROOT:-$HOME/IPAL/arthur_ipal/datasets/evimo_full/eval}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/evimo/evimo_val.txt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
MS_DECOUPLED=${MS_DECOUPLED:-$MS_MODEL/checkpoints/v4-full-run1/best.pt}
MS_COUPLED_SUP=${MS_COUPLED_SUP:-results_coupled/m2/ms_final.pt}
MS_COUPLED_SELFSUP=${MS_COUPLED_SELFSUP:-results_coupled/m3/ms_final.pt}
OUTDIR=${OUTDIR:-results/central_table}
# ================

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devo
cd "$REPO_DEVO"
mkdir -p logs

# Construit les args optionnels seulement si le checkpoint existe (sinon la ligne = "—").
EXTRA=""
[ -f "$MS_DECOUPLED" ]        && EXTRA="$EXTRA --ms_decoupled $MS_DECOUPLED"
[ -f "$MS_COUPLED_SUP" ]      && EXTRA="$EXTRA --ms_coupled_sup $MS_COUPLED_SUP"
[ -f "$MS_COUPLED_SELFSUP" ]  && EXTRA="$EXTRA --ms_coupled_selfsup $MS_COUPLED_SELFSUP"

python evals/eval_evs/eval_evimo_central_table.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --mask_root "$MASK_ROOT" \
    --ms_config "$MS_CONFIG" \
    --outdir "$OUTDIR" \
    $EXTRA
