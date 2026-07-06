#!/bin/bash
#SBATCH --job-name=devo_map_rpg
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=1:00:00
#SBATCH --output=results/rpg_evs/%j.log

RUN_NAME=${1:-map_test}
DATE=$(date +%Y-%m-%d)
OUTDIR=results/rpg_evs/${DATE}_${RUN_NAME}

source ~/miniconda3/etc/profile.d/conda.sh
conda activate devofou

cd /home/i/i0002573/arthur_ipal/DEVO
export PYTHONPATH=/home/i/i0002573/arthur_ipal/DEVO:$PYTHONPATH

python evals/eval_evs/eval_rpg_evs.py \
    --datapath /home/i/i0002573/arthur_ipal/datasets/rpg/rpg_dataset \
    --weights /home/i/i0002573/test_perso/DEVO/DEVO.pth \
    --val_split splits/rpg/rpg_val.txt \
    --map_path ${OUTDIR}/map.ply \
    --expname ${RUN_NAME}

mv results/rpg_evs/${SLURM_JOB_ID}.log ${OUTDIR}/run.log
