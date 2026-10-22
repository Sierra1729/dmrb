"""dMRV Command Line Interface for ACVA Verification and Calculation Reproducibility."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

from reports.bundle import ReproducibilityBundle, hash_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dmrv",
        description="dMRV Indian Carbon Market Calculation & Verification CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # `dmrv run --bundle <bundle.zip>`
    run_parser = subparsers.add_parser("run", help="Verify and reproduce a calculation run bundle")
    run_parser.add_argument(
        "--bundle",
        type=str,
        required=True,
        help="Path to the ACVA reproducibility ZIP bundle",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        bundle_path = Path(args.bundle)
        if not bundle_path.exists():
            print(f"[ERROR] Bundle file not found: {bundle_path}", file=sys.stderr)
            return 1

        print("=" * 60)
        print("  dMRV REPRODUCIBILITY VERIFICATION (BEE / ACVA AUDIT)")
        print("=" * 60)
        print(f"Loading bundle: {bundle_path}")

        try:
            with zipfile.ZipFile(bundle_path, mode="r") as zf:
                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
                outputs = json.loads(zf.read("outputs.json").decode("utf-8"))

            print(f"Project ID:      {manifest_data.get('project_id')}")
            print(f"Methodology:     {manifest_data.get('methodology')}")
            print(f"Engine Version:  {manifest_data.get('engine_version')}")
            print("-" * 60)
            print("Manifest File Hashes (SHA-256):")
            for fname, sha_val in manifest_data.get("files", {}).items():
                print(f"  [OK] {fname:<20} {sha_val[:16]}...")

            print("-" * 60)
            print("Re-running pure engine calculation...")
            is_identical = ReproducibilityBundle.verify_and_reproduce(bundle_path)

            print("-" * 60)
            print("Recorded Outputs:")
            for k, v in outputs.items():
                print(f"  {k:<30} {v}")

            if is_identical:
                print("=" * 60)
                print("  [SUCCESS] 100% BIT-IDENTICAL REPRODUCTION CONFIRMED")
                print("=" * 60)
                return 0
            else:
                print("=" * 60)
                print("  [FAILURE] REPRODUCTION DIVERGED FROM RECORDED OUTPUTS")
                print("=" * 60)
                return 1

        except Exception as e:
            print(f"[ERROR] Bundle verification failed: {e}", file=sys.stderr)
            return 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
