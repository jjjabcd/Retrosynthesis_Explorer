"""Thin wrapper around ``aizynthcli`` for running retrosynthesis planning on a single SMILES or a CSV batch."""

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def _run_aizynthcli(config: str, smiles: str, output: str) -> int:
    cmd = ["aizynthcli", "--config", config, "--smiles", smiles, "--output", output]
    return subprocess.call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run retrosynthesis planning on a single target molecule or a CSV batch of molecules."
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--smiles", help="the target molecule SMILES")
    target_group.add_argument(
        "--smiles_csv",
        help="path to a CSV file with 'ID' and 'SMILES' columns to process in batch",
    )
    parser.add_argument(
        "--config",
        default="data/config.yml",
        help="the filename of the aizynthfinder configuration file (default: data/config.yml)",
    )
    parser.add_argument(
        "--output",
        default="trees.json",
        help="output filename for single-SMILES mode (default: trees.json)",
    )
    parser.add_argument(
        "--output_dir",
        help="output directory for CSV batch mode; each row is saved as <ID>.json",
    )
    args = parser.parse_args()

    if args.smiles_csv:
        if not args.output_dir:
            parser.error("--output_dir is required when using --smiles_csv")
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(args.smiles_csv, newline="") as fileobj:
            rows = list(csv.DictReader(fileobj))

        failed = []
        for i, row in enumerate(rows, start=1):
            mol_id = row["ID"]
            smiles = row["SMILES"]
            output = output_dir / f"{mol_id}.json"
            print(f"[{i}/{len(rows)}] {mol_id}: {smiles}")
            if _run_aizynthcli(args.config, smiles, str(output)) != 0:
                failed.append(mol_id)

        if failed:
            print(
                f"Failed for {len(failed)} molecule(s): {', '.join(failed)}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        sys.exit(_run_aizynthcli(args.config, args.smiles, args.output))


if __name__ == "__main__":
    main()
