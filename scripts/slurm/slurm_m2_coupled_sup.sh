#!/bin/bash
# M2 — entraînement COUPLÉ supervisé (MS + DEVO, loss pose + masque GT). Long (jusqu'à 3 j).
# Produit results_coupled/m2/ms_final.pt (à rebrancher dans le tableau central M4).
#SBATCH --job-name=m2_coupled_sup
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
DATAPATH=${DATAPATH:-/home/i/i0002573/arthur_ipal/datasets/evimo_full}       # racine EVIMO (chemins train_sequences du yaml MS partent d'ici)
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
MS_WEIGHTS=${MS_WEIGHTS:-$MS_MODEL/checkpoints/v4-full-run1/best.pt}
MS_CONFIG=${MS_CONFIG:-$MS_MODEL/configs/convlstm_v4_full.yaml}
STEPS=${STEPS:-20000}
FREEZE=${FREEZE:-5000}
N_FRAMES=${N_FRAMES:-15}
# Nommage seed-aware : SEED= vide (défaut) -> results_coupled/m2/ (run initial préservé)
# SEED=N -> results_coupled/m2_seed$N/  (runs du sweep de variance)
SEED=${SEED:-}
if [ -n "$SEED" ]; then
    OUTDIR=${OUTDIR:-results_coupled/m2_seed${SEED}}
    SEED_ARG="--seed $SEED"
else
    OUTDIR=${OUTDIR:-results_coupled/m2}
    SEED_ARG=""
fi
# ================

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate devofou
cd "$REPO_DEVO"
export PYTHONPATH=$REPO_DEVO:$PYTHONPATH
export PYTHONUNBUFFERED=1
mkdir -p logs

# EvimoClipDataset lazy (mmap voxel cache + depth/mask on-demand, LRU 2 par worker).
# -> peut charger les 40 seqs du yaml MS sans OOM.
# -u = unbuffered stdout/stderr (voir les step logs en temps réel dans le fichier SLURM).
# log_every=2 (défaut 20) le temps de valider que le training tourne vraiment.
python -u train_coupled.py \
    --log_every 2 \
    --dataset evimo --datapath "$DATAPATH" \
    --devo_weights "$DEVO_WEIGHTS" \
    --ms_weights "$MS_WEIGHTS" \
    --ms_config "$MS_CONFIG" \
    --outdir "$OUTDIR" \
    --provide_gt_mask \
    $SEED_ARG \
    --n_frames "$N_FRAMES" --steps "$STEPS" --freeze_devo_steps "$FREEZE"
