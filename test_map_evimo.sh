#!/bin/bash
#SBATCH --job-name=devo_map_evimo
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=2:00:00
#SBATCH --output=results/evimo_evs/%j.log

RUN_NAME=${1:-map_test}
DATE=$(date +%Y-%m-%d)
OUTDIR=results/evimo_evs/${DATE}_${RUN_NAME}

source ~/miniconda3/etc/profile.d/conda.sh
conda activate devofou

cd /home/i/i0002573/arthur_ipal/DEVO
export PYTHONPATH=/home/i/i0002573/arthur_ipal/DEVO:$PYTHONPATH

mkdir -p results/evimo_evs

python evals/eval_evs/eval_evimo_evs.py \
    --datapath /home/i/i0002573/arthur_ipal/datasets/evimo_filtered_2805/eval \
    --weights /home/i/i0002573/test_perso/DEVO/DEVO.pth \
    --val_split splits/evimo/evimo_val.txt \
    --map_path ${OUTDIR}/map.ply \
    --expname ${RUN_NAME}

mv results/evimo_evs/${SLURM_JOB_ID}.log ${OUTDIR}/run.log
