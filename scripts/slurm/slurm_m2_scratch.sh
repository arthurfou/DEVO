#!/bin/bash
# M2-scratch — entraînement COUPLÉ supervisé avec MS initialisé ALÉATOIREMENT (pas de best.pt).
# Prior doux β·(mask_mean − 0.1)² pour éviter le collapse. 10k freeze + 40k total.
#SBATCH --job-name=m2_scratch
#SBATCH --partition=gpu-long
#SBATCH --gres=gpu:a100-40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=3-00:00:00
#SBATCH --output=logs/%x_%j.log
set -eo pipefail

# === Cluster NUS SoC (i0002573) ===
REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo_full}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
STEPS=${STEPS:-40000}
FREEZE=${FREEZE:-10000}
N_FRAMES=${N_FRAMES:-15}
SOFT_PRIOR_BETA=${SOFT_PRIOR_BETA:-0.5}
SOFT_PRIOR_TARGET=${SOFT_PRIOR_TARGET:-0.1}
OUTDIR=${OUTDIR:-results_coupled/m2_scratch}
# ================

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
    --outdir "$OUTDIR" \
    --provide_gt_mask \
    --soft_prior_beta "$SOFT_PRIOR_BETA" \
    --soft_prior_target "$SOFT_PRIOR_TARGET" \
    --n_frames "$N_FRAMES" --steps "$STEPS" --freeze_devo_steps "$FREEZE"
