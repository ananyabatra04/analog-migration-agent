#!/usr/bin/env python3
"""
Minimal Spectre netlist migrator.

Features:
  - Joins continuation lines ending with "\"
  - Updates MOS model names using a JSON rules file
  - Optionally scales W/L parameters
  - Optionally rewrites include paths
"""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_RULES: Dict[str, Dict[str, object]] = {
    "model_map": {},
    "param_scale": {"W": 1.0, "L": 1.0},
    "include_map": {},
}

MOS_RE = re.compile(r"^(\s*)(M\S+)\s+\(([^)]*)\)\s+(\S+)(.*)$", re.IGNORECASE)
NUMERIC_RE = re.compile(
    r"^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)([a-zA-Z]+)?$"
)


def join_continuations(lines: Iterable[str]) -> List[str]:
    """Join lines ending with '\' into single logical lines."""
    joined: List[str] = []
    buffer: str | None = None

    for line in lines:
        raw = line.rstrip("\n")
        if raw.endswith("\\"):
            piece = raw[:-1].rstrip()
            buffer = f"{buffer} {piece}".strip() if buffer else piece
            continue

        if buffer is not None:
            combined = f"{buffer} {raw.lstrip()}".strip()
            joined.append(combined)
            buffer = None
        else:
            joined.append(raw)

    if buffer is not None:
        joined.append(buffer)

    return joined


def load_rules(path: str | None) -> Dict[str, Dict[str, object]]:
    rules = deepcopy(DEFAULT_RULES)
    if not path:
        return rules

    data = json.loads(Path(path).read_text())
    if "model_map" in data:
        rules["model_map"].update(data["model_map"])
    if "include_map" in data:
        rules["include_map"].update(data["include_map"])
    if "param_scale" in data:
        for key, value in data["param_scale"].items():
            rules["param_scale"][key.upper()] = float(value)

    return rules


def parse_param_tokens(tail: str) -> List[Tuple[str | None, str]]:
    tokens = tail.strip().split()
    parsed: List[Tuple[str | None, str]] = []
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            parsed.append((key, value))
        else:
            parsed.append((None, token))
    return parsed


def scale_value(value: str, factor: float) -> str:
    if factor == 1.0:
        return value
    match = NUMERIC_RE.match(value)
    if not match:
        return value
    number = float(match.group(1))
    suffix = match.group(2) or ""
    scaled = number * factor
    return f"{scaled:g}{suffix}"


def migrate_mos_line(
    line: str, rules: Dict[str, Dict[str, object]], stats: Dict[str, int]
) -> str:
    match = MOS_RE.match(line)
    if not match:
        return line

    prefix, name, nodes, model, tail = match.groups()
    stats["mos_lines"] += 1

    model_map = rules["model_map"]
    new_model = model_map.get(model) or model_map.get(model.lower()) or model
    if new_model != model:
        stats["models_mapped"] += 1

    tokens = parse_param_tokens(tail)
    scale = rules["param_scale"]
    new_tokens: List[str] = []
    for key, value in tokens:
        if key is None:
            new_tokens.append(value)
            continue

        key_upper = key.upper()
        if key_upper in ("W", "L") and scale.get(key_upper, 1.0) != 1.0:
            new_value = scale_value(value, float(scale.get(key_upper, 1.0)))
            if new_value != value:
                stats["params_scaled"] += 1
            new_tokens.append(f"{key}={new_value}")
        else:
            new_tokens.append(f"{key}={value}")

    new_tail = f" {' '.join(new_tokens)}" if new_tokens else ""
    return f"{prefix}{name} ({nodes}) {new_model}{new_tail}"


def migrate_line(
    line: str, rules: Dict[str, Dict[str, object]], stats: Dict[str, int]
) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith(("//", "*", ";")):
        return line

    if stripped.lower().startswith("include "):
        include_target = stripped[len("include ") :].strip()
        include_map = rules["include_map"]
        mapped = include_map.get(include_target)
        if not mapped and include_target.startswith('"') and include_target.endswith('"'):
            mapped = include_map.get(include_target.strip('"'))
            if mapped:
                mapped = f"\"{mapped}\""
        if mapped:
            stats["includes_mapped"] += 1
            return line.replace(include_target, mapped, 1)
        return line

    return migrate_mos_line(line, rules, stats)


def migrate_netlist(text: str, rules: Dict[str, Dict[str, object]]) -> Tuple[str, Dict[str, int]]:
    stats = {
        "lines": 0,
        "mos_lines": 0,
        "models_mapped": 0,
        "params_scaled": 0,
        "includes_mapped": 0,
    }

    logical_lines = join_continuations(text.splitlines())
    output_lines: List[str] = []
    for line in logical_lines:
        stats["lines"] += 1
        output_lines.append(migrate_line(line, rules, stats))

    return "\n".join(output_lines) + "\n", stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate a Spectre netlist via simple rules.")
    parser.add_argument("--input", required=True, help="Path to source netlist")
    parser.add_argument("--output", required=True, help="Path to migrated netlist")
    parser.add_argument("--rules", help="Path to JSON rules file")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    src_text = Path(args.input).read_text()
    migrated, stats = migrate_netlist(src_text, rules)
    Path(args.output).write_text(migrated)

    print("Migration complete.")
    print(
        f"Lines: {stats['lines']}, MOS lines: {stats['mos_lines']}, "
        f"models mapped: {stats['models_mapped']}, params scaled: {stats['params_scaled']}, "
        f"includes mapped: {stats['includes_mapped']}"
    )


if __name__ == "__main__":
    main()
