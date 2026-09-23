# SLURM profile

This profile targets the current Snakemake executor-plugin architecture.

Create the SLURM-enabled Snakemake environment:

```bash
conda env create -f profiles/slurm/environment.yml
conda activate gse97693-snakemake-slurm
```

Before running, edit `profiles/slurm/config.yaml` and replace:

```yaml
slurm_account: "CHANGE_ME"
slurm_partition: "CHANGE_ME"
```

Then run from the repository root:

```bash
snakemake \
  --profile profiles/slurm \
  --resources ena_conn=4
```

FASTQ/reference downloads are `localrule`s and are therefore kept off SLURM compute jobs.

The profile requests 40 GB for STAR alignment and 55 GB for index generation.
