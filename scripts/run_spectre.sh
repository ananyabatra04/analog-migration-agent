#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") NETLIST [OUTDIR]" >&2
  echo "Example: $(basename "$0") netlists/input/inv_tsmc03.scs netlists/output/run1" >&2
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
fi

netlist="$1"
outdir="${2:-netlists/output/$(basename "${netlist%.*}")_$(date +%Y%m%d_%H%M%S)}"

if [[ ! -f "$netlist" ]]; then
  echo "Netlist not found: $netlist" >&2
  exit 1
fi

if ! command -v spectre >/dev/null 2>&1; then
  echo "spectre not found in PATH" >&2
  exit 1
fi

if grep -q '\$CDK_DIR' "$netlist" && [[ -z "${CDK_DIR:-}" ]]; then
  echo "CDK_DIR is not set but netlist references \$CDK_DIR" >&2
  exit 1
fi

mkdir -p "$outdir"

spectre "$netlist" -format psf -raw "$outdir" -log "$outdir/spectre.log"

if [[ ! -s "$outdir/spectre.log" ]]; then
  echo "Spectre did not produce a log at $outdir/spectre.log" >&2
  exit 1
fi

echo "Simulation complete: $outdir"
