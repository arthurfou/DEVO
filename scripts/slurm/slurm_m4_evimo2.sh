#!/bin/bash
# M4 EVIMO2 — tableau central (vanilla / oracle / M1 / M2 / M3).
#SBATCH --job-name=m4_evimo2
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo2/eval_preprocessed}
MASK_ROOT=${MASK_ROOT:-/home/i/i0002573/arthur_ipal/datasets/evimo2/evimo1_format}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/evimo2/evimo2_val.txt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_evimo2.yaml}
MS_DECOUPLED=${MS_DECOUPLED:-$MS_MODEL/checkpoints/evimo2-run1/best.pt}
MS_COUPLED_SUP=${MS_COUPLED_SUP:-results_coupled/m2_evimo2/ms_final.pt}
MS_COUPLED_SELFSUP=${MS_COUPLED_SELFSUP:-results_coupled/m3_evimo2/ms_final.pt}
OUTDIR=${OUTDIR:-results/central_table_evimo2}
SEED=${SEED:-1234}

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

EXTRA=""
[ -f "$MS_DECOUPLED" ]        && EXTRA="$EXTRA --ms_decoupled $MS_DECOUPLED"
[ -f "$MS_COUPLED_SUP" ]      && EXTRA="$EXTRA --ms_coupled_sup $MS_COUPLED_SUP"
[ -f "$MS_COUPLED_SELFSUP" ]  && EXTRA="$EXTRA --ms_coupled_selfsup $MS_COUPLED_SELFSUP"

python -u evals/eval_evs/eval_evimo2_central_table.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --mask_root "$MASK_ROOT" \
    --ms_config "$MS_CONFIG" \
    --outdir "$OUTDIR" \
    --seed "$SEED" \
    $EXTRA
