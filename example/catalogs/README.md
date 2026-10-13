# Generated device catalogs

One ready-to-include ESPHome package per Viessmann unit, generated from the
Vitosoft 2026 XML export by `scripts/gen_catalog.py --export-all`. These are
**include-only fragments** (no top-level `esphome:` block) — pull one into a
standalone config via `packages:` / `!include`; see [`../README.md`](../README.md)
for a complete wiring example.

**Find your unit with the [catalog finder](https://soulsolistice.github.io/esphome_vitohome/)**: paste the `Device`
line the hub logs at boot (e.g. `Device: 0x20CB (VScotHO1) HW=0x03 SW=0x51`), or
follow the link the hub logs after it. The device id alone does not select a
file: most ids cover several catalogs that differ by software index.

[`index.csv`](index.csv) is the manifest behind the finder and
[`resolve.json`](resolve.json) the precomputed lookup it reads; see
[`../README.md`](../README.md) for the columns and for reading the manifest by
hand. Rows with `status: skipped` have no file — every datapoint on that unit
needs a non-Optolink access method. Rows with `status: missing` (the GWG units)
have no file in this directory; generate them with
`scripts/gen_catalog.py --export-all`.

> **Fault-code caveat.** `--export-all` attaches the default `vd300`
> (Vitodens 300-W B3HA) fault-code map to *every* unit. Fault-code semantics
> are device-variant-specific; for any unit other than the reference one,
> regenerate with the correct `--error-code-set` (see the note in
> [`../README.md`](../README.md)).

This stub is hand-written and survives regeneration: `gen_catalog.py` creates
the directory with `exist_ok=True` and never clears it.
