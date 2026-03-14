#!/bin/bash
set -e
cd /media/talino/data/MASL/rcc_repast4py
export MPLBACKEND=Agg
PYTHON=".venv/bin/python3"
CFG="--config config/scenario_params.yaml"
OUTDIR="docs/report/figures/scenarios/multiseed"
mkdir -p "$OUTDIR"

for SEED in $(seq 1 20); do
  for SEX in M F; do
    for TX in None TKI ICI ICI+TKI; do
      TAG="${SEX}_${TX}_${SEED}"
      mpirun --allow-run-as-root -n 1 $PYTHON run.py $CFG --sex $SEX --treatment "$TX" --max-steps 300 --seed $SEED --quiet 2>/dev/null || true
      cp logs/simulation_log.csv "$OUTDIR/${TAG}.csv"
    done
  done
  echo "Seed $SEED/20 done"
done
echo "=== ALL 160 RUNS COMPLETE ==="
