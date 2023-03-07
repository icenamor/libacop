#PBS -S /bin/bash
#PBS -N build_lpg
#PBS -q ice
#PBS -l nodes=1
#PBS -l walltime=1:00:00,mem=1536mb
#PBS -m ea
#PBS -M fawcettc@cs.ubc.ca
#PBS -o cluster-out
#PBS -e cluster-out
cd $PBS_O_WORKDIR
./configure
make
