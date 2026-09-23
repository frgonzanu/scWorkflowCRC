#!/usr/bin/env bash
set -euo pipefail

if ! command -v conda-lock >/dev/null 2>&1; then
    echo "conda-lock is required."
    echo "Install it, e.g.: conda install -c conda-forge conda-lock"
    exit 1
fi

mkdir -p locks

conda-lock lock \
  --platform linux-64 \
  --file environment.yml \
  --lockfile locks/environment.conda-lock.yml

conda-lock lock \
  --platform linux-64 \
  --file profiles/slurm/environment.yml \
  --lockfile locks/slurm.conda-lock.yml

for env in workflow/envs/*.yaml; do
    name="$(basename "$env" .yaml)"
    conda-lock lock \
      --platform linux-64 \
      --file "$env" \
      --lockfile "locks/${name}.conda-lock.yml"
done

echo "Lock files written to locks/"
