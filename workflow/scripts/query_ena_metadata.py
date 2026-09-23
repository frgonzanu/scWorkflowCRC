#!/usr/bin/env python3

import argparse
import csv
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

FIELDS = [
    "run_accession",
    "library_layout",
    "fastq_ftp",
    "fastq_md5",
    "fastq_bytes",
]


def read_accessions(path):
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    required = {"sample", "protocol"}
    if not rows:
        raise SystemExit(f"No accessions found in {path}")
    if not required.issubset(rows[0]):
        raise SystemExit(f"{path} must contain columns: sample, protocol")

    seen = set()
    for row in rows:
        sample = row["sample"].strip()
        protocol = row["protocol"].strip()

        if sample in seen:
            raise SystemExit(f"Duplicate accession: {sample}")
        seen.add(sample)

        if protocol not in {"tang", "smartseq2"}:
            raise SystemExit(
                f"Unsupported protocol for {sample}: {protocol!r}"
            )

    return rows


def https_url(value):
    value = value.strip()
    if value.startswith("https://"):
        return value
    if value.startswith("http://"):
        return "https://" + value[len("http://"):]
    if value.startswith("ftp://"):
        return "https://" + value[len("ftp://"):]
    return "https://" + value


def query_run(accession, timeout):
    params = urlencode(
        {
            "accession": accession,
            "result": "read_run",
            "fields": ",".join(FIELDS),
            "format": "tsv",
        }
    )
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?{params}"

    with urlopen(url, timeout=timeout) as response:
        text = response.read().decode("utf-8")

    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != 2:
        raise RuntimeError(
            f"Unexpected ENA response for {accession}: {len(lines)-1} rows"
        )

    row = next(csv.DictReader(lines, delimiter="\t"))

    urls = [https_url(x) for x in row["fastq_ftp"].split(";") if x]
    md5s = [x.strip().lower() for x in row["fastq_md5"].split(";") if x]

    if len(urls) != len(md5s):
        raise RuntimeError(
            f"ENA URL / MD5 count mismatch for {accession}: "
            f"{len(urls)} URLs vs {len(md5s)} MD5 hashes"
        )

    pairs = list(zip(urls, md5s))
    layout = row["library_layout"].strip().upper()

    if layout == "PAIRED":
        r1 = [
            item for item in pairs
            if urlparse(item[0]).path.endswith("_1.fastq.gz")
        ]
        r2 = [
            item for item in pairs
            if urlparse(item[0]).path.endswith("_2.fastq.gz")
        ]

        if len(r1) != 1 or len(r2) != 1:
            raise RuntimeError(
                f"Could not identify exactly one R1 and R2 FASTQ for "
                f"{accession}. ENA returned: {urls}"
            )

        return {
            "layout": "PAIRED",
            "r1_url": r1[0][0],
            "r1_md5": r1[0][1],
            "r2_url": r2[0][0],
            "r2_md5": r2[0][1],
        }

    if layout == "SINGLE":
        if len(pairs) != 1:
            raise RuntimeError(
                f"Expected one FASTQ for single-end run {accession}, "
                f"found {len(pairs)}"
            )

        return {
            "layout": "SINGLE",
            "r1_url": pairs[0][0],
            "r1_md5": pairs[0][1],
            "r2_url": "",
            "r2_md5": "",
        }

    raise RuntimeError(
        f"Unsupported ENA library_layout for {accession}: {layout!r}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accessions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.1)
    args = parser.parse_args()

    rows = read_accessions(args.accessions)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "sample",
        "protocol",
        "layout",
        "r1_url",
        "r1_md5",
        "r2_url",
        "r2_md5",
    ]

    resolved = []

    for index, row in enumerate(rows, start=1):
        sample = row["sample"].strip()
        print(f"[{index}/{len(rows)}] ENA metadata: {sample}")

        metadata = query_run(sample, args.timeout)
        resolved.append(
            {
                "sample": sample,
                "protocol": row["protocol"].strip(),
                **metadata,
            }
        )

        if args.sleep:
            time.sleep(args.sleep)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(resolved)

    print(f"Wrote {len(resolved)} rows to {output}")


if __name__ == "__main__":
    main()
