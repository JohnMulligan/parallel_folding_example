#!/bin/bash
#SBATCH --job-name=dihedral
#SBATCH --partition=scavenge
#SBATCH --time=01:00:00
#SBATCH --export=ALL
#SBATCH --mail-user=jcm10@rice.edu
#SBATCH --mail-type=ALL

module load GCCcore/8.3.0
module load Python/3.7.2

python3 main.py $1 $SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_COUNT $2
