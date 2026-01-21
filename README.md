# analog-migration-agent

## Quick start (netlist MVP)
1) Place a Spectre/SPICE netlist under `netlists/input/`.
2) Edit `src/rules.json` with your model mapping and optional W/L scaling.
3) Run the migrator:

```
python src/netlist_migrator.py \
  --input netlists/input/inv_tb.scs \
  --output netlists/output/inv_tb_migrated.scs \
  --rules src/rules.json
```

Notes:
- The migrator updates MOS model names and optionally scales W/L.
- Other devices and statements are passed through unchanged.
- You can map `include` paths via `include_map` in `src/rules.json`.