#!/usr/bin/env python3

import argparse
import csv
from urllib.request import urlopen

BASE = (
    "https://raw.githubusercontent.com/frgonzanu/TFM/main/"
    "Scripts/Preprocesado%20%28bash%29"
)


def read_lines(url):
    with urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    all_accessions = read_lines(f"{BASE}/SRA_list.txt")
    tang_accessions = set(read_lines(f"{BASE}/Tang_samples.txt"))

    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["sample", "protocol"])

        for sample in all_accessions:
            protocol = "tang" if sample in tang_accessions else "smartseq2"
            writer.writerow([sample, protocol])

    print(f"Wrote {len(all_accessions)} accessions to {args.output}")


if __name__ == "__main__":
    main()
