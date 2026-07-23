#!/bin/bash
#SBATCH --job-name=eds_table
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=8:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/eds}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
VAL_SPLIT=${VAL_SPLIT:-splits/eds/eds_val.txt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
MS_DECOUPLED=${MS_DECOUPLED:-$MS_MODEL/checkpoints/v4-full-run1/best.pt}
MS_COUPLED_SUP=${MS_COUPLED_SUP:-results_coupled/m2/ms_final.pt}
MS_COUPLED_SELFSUP=${MS_COUPLED_SELFSUP:-results_coupled/m3/ms_final.pt}
SEED=${SEED:-1234}
OUTDIR=${OUTDIR:-results/eds_central_table}

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
mkdir -p logs

EXTRA=""
[ -f "$MS_DECOUPLED" ]        && EXTRA="$EXTRA --ms_decoupled $MS_DECOUPLED"
[ -f "$MS_COUPLED_SUP" ]      && EXTRA="$EXTRA --ms_coupled_sup $MS_COUPLED_SUP"
[ -f "$MS_COUPLED_SELFSUP" ]  && EXTRA="$EXTRA --ms_coupled_selfsup $MS_COUPLED_SELFSUP"

python -u evals/eval_evs/eval_eds_central_table.py \
    --datapath "$DATAPATH" \
    --weights "$DEVO_WEIGHTS" \
    --val_split "$VAL_SPLIT" \
    --ms_config "$MS_CONFIG" \
    --seed "$SEED" \
    --outdir "$OUTDIR" \
    $EXTRA
