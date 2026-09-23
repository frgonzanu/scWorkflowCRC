from pathlib import Path

import pandas as pd


frames = []
seen_samples = set()

for filename in snakemake.input:
    path = Path(filename)
    sample = path.parent.name

    if sample in seen_samples:
        raise ValueError(f"Duplicate STAR count input for sample {sample}")
    seen_samples.add(sample)

    table = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=["gene", "unstranded", "strand_plus", "strand_minus"],
        dtype={"gene": str},
    )

    table = table.loc[
        ~table["gene"].str.startswith("N_"),
        ["gene", "unstranded"],
    ]

    if table["gene"].duplicated().any():
        duplicated = table.loc[
            table["gene"].duplicated(), "gene"
        ].head().tolist()
        raise ValueError(
            f"Duplicate gene IDs in {path}: {duplicated}"
        )

    frame = (
        table.rename(columns={"unstranded": sample})
        .set_index("gene")
    )
    frames.append(frame)

matrix = pd.concat(frames, axis=1, join="outer").fillna(0)
matrix = matrix.astype(int)
matrix.index.name = "gene"

output_path = Path(snakemake.output[0])
output_path.parent.mkdir(parents=True, exist_ok=True)
matrix.to_csv(output_path, sep="\t")

log_path = Path(snakemake.log[0])
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(
    "\n".join(
        [
            f"samples\t{matrix.shape[1]}",
            f"genes\t{matrix.shape[0]}",
            f"output\t{output_path}",
        ]
    ) + "\n",
    encoding="utf-8",
)
