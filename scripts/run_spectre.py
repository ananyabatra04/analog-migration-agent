#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Spectre simulation on a netlist."
    )
    parser.add_argument("netlist", help="Path to Spectre netlist (.scs)")
    parser.add_argument(
        "outdir",
        nargs="?",
        help="Output directory (defaults to netlists/output/<name>_<timestamp>)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    netlist = Path(args.netlist)

    if not netlist.is_file():
        print(f"Netlist not found: {netlist}", file=sys.stderr)
        return 1

    spectre_path = shutil.which("spectre")
    if not spectre_path:
        print("spectre not found in PATH", file=sys.stderr)
        return 1

    netlist_text = netlist.read_text(encoding="utf-8", errors="replace")
    if "$CDK_DIR" in netlist_text and not os.environ.get("CDK_DIR"):
        print("CDK_DIR is not set but netlist references $CDK_DIR", file=sys.stderr)
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_outdir = Path("netlists/output") / f"{netlist.stem}_{timestamp}"
    outdir = Path(args.outdir) if args.outdir else default_outdir
    outdir.mkdir(parents=True, exist_ok=True)

    log_path = outdir / "spectre.log"
    cmd = [
        spectre_path,
        str(netlist),
        "-format",
        "psf",
        "-raw",
        str(outdir),
        "-log",
        str(log_path),
    ]

    subprocess.run(cmd, check=True)

    if not log_path.is_file() or log_path.stat().st_size == 0:
        print(f"Spectre did not produce a log at {log_path}", file=sys.stderr)
        return 1

    print(f"Simulation complete: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
