# Generated device catalogs

One ready-to-include ESPHome package per Viessmann unit, generated from the
Vitosoft 2026 XML export by `scripts/export_catalogs.sh` (which runs
`scripts/gen_catalog.py --export-all` once per language). These are
**include-only fragments** (no top-level `esphome:` block) — pull one into a
standalone config via `packages:` / `!include`; see [`../README.md`](../README.md)
for a complete wiring example.

| Folder | Language |
|---|---|
| [`de/`](de/) | German entity names, option labels and fault texts |
| [`en/`](en/) | English (German where Vitosoft has no translation) |
| `<lang>/gfa/` | Burner-control (GFA) fault texts, one companion per chip |

Both folders hold the same files under the same names; units and entity types
are identical. Home Assistant derives entity IDs from the names, so switching
an installed catalog to the other language creates new entities.

**Find your unit with the [catalog finder](https://soulsolistice.github.io/esphome_vitohome/)**: paste the `Device`
line the hub logs at boot (e.g. `Device: 0x20CB (VScotHO1) HW=0x03 SW=0x51`), or
follow the link the hub logs after it, and pick the language there. The device
id alone does not select a file: most ids cover several catalogs that differ by
software index.

Each language folder has its [`index.csv`](de/index.csv) manifest;
[`resolve.json`](resolve.json) is the precomputed lookup the finder reads, shared
by both. See [`../README.md`](../README.md) for the columns and for reading the
manifest by hand. Rows with `status: skipped` have no file — every datapoint on
that unit needs a non-Optolink access method.

> **Fault texts.** Every catalog carries Vitosoft's fault texts for its own
> device. The burner-control (GFA) history slots need the chip your unit reports
> at `0x7650`: include `gfa/chip_<XX>.yaml` next to the catalog (the finder
> shows the line), see [`../../scripts/README.md`](../../scripts/README.md).

This stub is hand-written and survives regeneration: `export_catalogs.sh`
clears only the generated `*.yaml` (including `gfa/`), `index.csv` and
`resolve.json` files.
