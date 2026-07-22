#!/bin/bash
# M4-fixed — tableau central avec correction du bug timestamps (Unix epoch vs relatif).
# Identique à slurm_m4_central_table.sh mais outdir = central_table_seed${N}_fixed.
# À lancer après le fix oracle.py + eval_evimo_m1_decoupled.py (commit présent).
#SBATCH --job-name=m4_fixed
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

# === Cluster NUS SoC (i0002573) ===
REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo_filtered_2805/eval}
MASK_ROOT=${MASK_ROOT:-/home/i/i0002573/arthur_ipal/datasets/evimo_full/eval}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/evimo/evimo_val.txt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
MS_DECOUPLED=${MS_DECOUPLED:-$MS_MODEL/checkpoints/v4-full-run1/best.pt}
SEED=${SEED:-}
if [ -n "$SEED" ]; then
    MS_COUPLED_SUP=${MS_COUPLED_SUP:-results_coupled/m2_seed${SEED}/ms_final.pt}
    MS_COUPLED_SELFSUP=${MS_COUPLED_SELFSUP:-results_coupled/m3_seed${SEED}/ms_final.pt}
    OUTDIR=${OUTDIR:-results/central_table_seed${SEED}_fixed}
else
    MS_COUPLED_SUP=${MS_COUPLED_SUP:-results_coupled/m2/ms_final.pt}
    MS_COUPLED_SELFSUP=${MS_COUPLED_SELFSUP:-results_coupled/m3/ms_final.pt}
    OUTDIR=${OUTDIR:-results/central_table_fixed}
fi
# ================

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

EXTRA=""
[ -f "$MS_DECOUPLED" ]        && EXTRA="$EXTRA --ms_decoupled $MS_DECOUPLED"
[ -f "$MS_COUPLED_SUP" ]      && EXTRA="$EXTRA --ms_coupled_sup $MS_COUPLED_SUP"
[ -f "$MS_COUPLED_SELFSUP" ]  && EXTRA="$EXTRA --ms_coupled_selfsup $MS_COUPLED_SELFSUP"

SEED_ARG=""
[ -n "$SEED" ] && SEED_ARG="--seed $SEED"

python -u evals/eval_evs/eval_evimo_central_table.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --mask_root "$MASK_ROOT" \
    --ms_config "$MS_CONFIG" \
    --outdir "$OUTDIR" \
    $SEED_ARG \
    $EXTRA
