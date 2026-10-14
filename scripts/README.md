# scripts

Tooling for producing and maintaining the datapoint catalog. The two tools here
are independent:

- `gen_catalog.py` reads a Viessmann Vitosoft **XML export** and emits a
  ready-to-include ESPHome package. This is the path you use to configure a
  device.
- `migrate_ecnViessmann.cmd` is a **development tool** that converts the
  Vitosoft SQL Server database into a portable SQLite file for offline
  inspection. It is not part of the ESPHome build or of catalog generation.

## `gen_catalog.py` — generate an ESPHome package

Per-device datapoint definitions (address, length, conversion, access type,
enums, units, borders) are not discoverable over the Optolink bus; they come
from Viessmann's Vitosoft data. `gen_catalog.py` reads the XML export of that
data and emits an ESPHome package with each datapoint on the right platform,
the correct converter, length, bit masks, units and a sensible poll interval.

It is stdlib-only and runs in a bare Python install.

### Input

Point `--data` at the directory holding the Vitosoft XML export. The generator
reads up to four files from it:

| File | Provides |
|---|---|
| `DPDefinitions.xml` | Device types, event links, enum value types, units, borders |
| `ecnEventType.xml` | Per-event Optolink address, lengths, bit position, read/write access, conversion |
| `ecnDataPointType.xml` | Identification ranges (group/ident, hardware/software index) used by `--identify` |
| `Textresource.xml` | UI names in the chosen language (optional; see note) |

`DPDefinitions.xml` does not carry datapoint lengths; those live in
`ecnEventType.xml`, so keep the export files together in one directory.

> **Label source (2026 export).** `Textresource.xml` carries UI strings only and,
> in current exports, **none** of the per-event/value display names — so
> `--culture` mainly affects those (mostly absent) names. Enum **option** labels
> are independent: they come from `ecnEventValueType.Description` in
> `DPDefinitions.xml` (pre-resolved German, ~87% coverage), so an enum/`select`'s
> `options:` are readable regardless of `--culture`. Entity `name:` falls back to
> a snake_case derivation of the technical id where no UI name exists.
>
> One `--culture` side effect: the switch-vs-select decision
> (`_boolean_pair`) recognises German/English on-off label pairs only
> (EIN/AUS, ON/OFF, Ja/Nein, ...). Under other cultures a boolean pair whose
> labels are localised differently is emitted as a two-option `select` instead
> of a `switch` -- functionally equivalent, just not a native HA toggle.

### Options

| Option | Purpose |
|---|---|
| `--data <dir>` | The Vitosoft XML export directory |
| `--list-devices` | List the device tokens (and identification ranges) in the export, then exit |
| `--identify <hex>` | Device identification (`group << 8 \| ident`), e.g. `0x20CB`; auto-selects the revision |
| `--hw <hex>` / `--sw <hex>` / `--f0 <hex>` | Hardware / software index / protocol offset, used with `--identify` |
| `--device <token>` | Generate for a named datapoint-type token, e.g. `VScotHO1_72` |
| `--profile {minimal,standard,full}` | How many datapoints to emit (default: `standard`) |
| `--include <regex>` / `--exclude <regex>` | Keep / drop events whose name matches |
| `--[no-]reachable-only` | Emit only datapoints VitoWiFi can read over Optolink; drop `GFA_READ`/`RPC`/`PROZESS`/`KBUS`/`OT` (default: on). `--no-reachable-only` adds them back — they need custom decode |
| `--order {address,group}` | Entity order: `address` (sorted by Optolink address) or `group` (by the Vitosoft navigation tree, with a section comment per group). Default: `group` with `--export-all`, `address` otherwise |
| `--culture {de,en,fr,it,ru,nl,pl,da,hu,es,tr,lt,cs}` | Language for names/labels (default: `de`). Currently a near-no-op — see the label-source note above |
| `--[no-]device-id` | Emit a `device_id` diagnostic `text_sensor` and suppress the raw `0xF8`–`0xFB` reads (default: on) |
| `--[no-]bitfield-writes` | Emit writable bit fields as `number` / `select` / `switch` with `bit_mask` (the component writes them as a read-modify-write of their byte) where the read and the write are the same 1-byte register (default: on). `--no-bitfield-writes` keeps every bit field read-only. See *Bit fields* below |
| `--[no-]error-history` | Emit `error_history` entities for the `FehlerHis*` slots (default: on) |
| `--[no-]error-codes` | Attach a fault-code map to those entities (default: on) |
| `--error-code-set {openv,vd200,vd300,union}` | Which fault-code map to attach (default: `vd300`) |
| `--export-all` | Bulk mode: one catalog per token into `--out` (a directory) plus an `index.csv` manifest and a `resolve.json` lookup table — see below |
| `--export-filter <regex>` | With `--export-all`: only export tokens whose ID matches (e.g. `^V`) |
| `--export-suffix <ext>` | With `--export-all`: catalog file extension (default: `.yaml`) |
| `--out <file>` | Output file (default: stdout); with `--export-all`, the output **directory** |

The fault-code maps live in [`fault_codes.py`](fault_codes.py) (one module, the
single source of truth): `vd300` is the Vitodens 300-W (B3HA) set and the default
(VScotHO1_72 / "Projekt Neptun" is the Vitotronic 200 controller in that boiler),
`vd200` is the Vitodens 200 (WB2A) set, `openv` is the generic openv/community
map, and `union` merges all three (most-specific manual wins). **Fault-code
semantics are device-variant-specific** — these are a default to verify on the
unit; openv-vs-VD200 disagreements are in `fault_codes.CONFLICTS`, and the VD300
set carries OCR caveats (a few codes to verify against the PDF) in its header.

### Signedness

`div2` and `div10` decode signed in the component. Where Vitosoft declares the
value unsigned (`Parameter` `Byte`/`Int`/`Int4`) **and** its lower border is 0 or
above, the generator emits `signed: false` with the reason as a comment, so a
1-byte 0..127.5 degC temperature does not turn negative above 63.5 degC. The
declared type alone is not trusted: it contradicts the borders on 27 rows,
including the outdoor sensor at `0x0800` (design_notes §8h).

### Bit fields

A datapoint with `BitLength` 1..8 is a field of one byte that other datapoints
share (GWG EEPROM `0x0005` holds eight coding flags). Every such field except a
read-only single bit is emitted with a native `bit_mask` (converters.md, *Bit
fields*), and the mask line cites the export:

```yaml
    bit_mask: 0xF0  # Vitosoft BitPosition 0, BitLength 4 (MSB-first)
```

Writable only where it is safe: the field must be byte 0 of a 1-byte datapoint
(every GWG bit field). Read-only, with a `NOTE` saying why:

- a field in byte 0 of a wider block: a 1-byte write there overwrites the rest
  of the block with telegram bytes (hardware-confirmed on the `Neptun_*`
  outputs of VScotHO1_72, see below);
- an interior field (no declared write address);
- an inferred scale (fractional stepping on `NoConversion`, e.g. SPR30) or a
  `MultOffset` with an offset -- there is no encode path for either;
- everything, with `--no-bitfield-writes`.

The same rule applies to every writable datapoint, bit field or not: a field
narrower than its block (`ByteLength < BlockLength`) is emitted read-only with a
`NOTE`. On VScotHO1_72 a 1-byte write into a 2-byte block stored our telegram's
checksum byte in byte 1 (design_notes §5b, §8g). The weekday Schaltzeiten,
written 8 bytes per day as vcontrold does, are generated by their own path and
are not affected.

The `ConversionFactor` / `ConversionOffset` columns on `NoConversion` bit fields
are stale copies of the last `MultOffset` row and are ignored. An enum whose own
option values do not fit its field is a contradiction in the export and becomes
a comment: `SM1_Sensor_*_Status_GWG` declares 7 bits but lists `128` ("Nicht
verwendet", the sibling `0x80` flag), and decoding it as 7 bits showed
"Unterbrechung" on a unit with no SM1 module installed.

### Examples

List what the export contains:

```
python3 scripts/gen_catalog.py --data <export-dir> --list-devices
```

Generate for a device by identification (the values the hub logs at boot, e.g.
`Device: 0x20CB (VScotHO1) HW=0x03 SW=0x51`):

```
python3 scripts/gen_catalog.py --data <export-dir> \
    --identify 0x20CB --hw 0x03 --sw 0x51 \
    --profile standard --out my-heater.vitohome.yaml
```

If several device types share the id and the export gives them no
hardware/software-index range to tell them apart (Dekamatik cascades, M-Bus
meters, which carry serial-style extensions), `--identify` stops and lists them
instead of picking the first one; name the token with `--device`. Earlier
versions silently took the first row.

Or name the datapoint-type token directly:

```
python3 scripts/gen_catalog.py --data <export-dir> --device VScotHO1_72 \
    --profile standard --out my-heater.vitohome.yaml
```

### Bulk export (`--export-all`)

`--export-all` runs the generator for **every** device token with the flags you
pass, writing one catalog per unit into `--out` (a directory) and an `index.csv`
manifest alongside. A unit that produces no Optolink-reachable datapoint is
recorded in the manifest and skipped (no file); one bad unit never aborts the
batch.

```
python3 scripts/gen_catalog.py --data <export-dir> \
    --export-all --no-error-codes --out catalogs/
```

`index.csv` maps every token to its file and identification signature (`ident`,
`hw_index`, software-index and F0 ranges), the linked-event and emitted-entity
counts, and a `status` (`ok` / `skipped: …` / `error: …`).

`resolve.json` is written alongside. It holds the answer of the `--identify`
matching rules for every device id, hardware index and software index, plus
each token's file and status. The [catalog finder](https://soulsolistice.github.io/esphome_vitohome/)
(`web/` in this repository, published by `.github/workflows/pages.yml`) reads
it, so the page carries no copy of the rules. `tests/unit/test_resolve_index.py`
runs `web/lookup.js` under Node against `Catalog.resolve()`. To preview the
page locally, copy `example/catalogs/resolve.json` next to `web/index.html` and
serve that folder (`python3 -m http.server`).

Bulk mode orders entities by group (`--order group`) unless you say otherwise,
which is how the catalogs in [`example/catalogs/`](../example/catalogs/) were
produced — so a re-export diffs against them entity by entity instead of
reordering every file. Pass `--order address` for the address-sorted layout.

Because fault-code semantics are device-variant-specific, `--export-all`
attaches the *same* default map (`vd300`) to every unit — pass `--no-error-codes`
for a neutral bulk export, or regenerate an individual unit with the right
`--error-code-set`. The committed result of this command lives in
[`example/catalogs/`](../example/catalogs/).

### Using the output

Include the emitted file from your device YAML and define the `vitohome:` hub
(and `uart:`) yourself:

```yaml
packages:
  heater: !include my-heater.vitohome.yaml
```

Every emitted entity is `disabled_by_default: true`, so you opt in to each one
from Home Assistant. Always run `esphome config`, then `esphome compile` /
`run`, before relying on a value — not every address answers on every firmware.

To facilitate the interpretation of the datapoints' naming, an overview of the
Viessmann nomenclature has been established in
[`docs/datapoint_acronyms.md`](../docs/datapoint_acronyms.md)

## `migrate_ecnViessmann.cmd` — Vitosoft database to SQLite (development tool)

A one-time Windows utility that exports the Vitosoft SQL Server database
(`ecnViessmann.mdf`) to a portable SQLite file. If you have the Vitosoft XML you
already installed Vitosoft, which ships a SQL Server instance, so the engine is
already present; this script uses it once to produce a SQLite copy you can query
offline without SQL Server.

This is a maintenance and inspection convenience for working with the catalog
data. It is not consumed by `gen_catalog.py` (which reads the XML export) and is
not part of the ESPHome build.

**Prerequisites:** `sqlcmd`, `sqlite3`, the export tool, PowerShell, and the two
companion scripts in this folder (`verify_counts.ps1`, `verify_encoding.ps1`).

**Configuration:** set the source `.mdf` / `.ldf` paths and the tool paths in
the configuration block at the top of the script before running. The script
operates on **copies** of the database files and detaches (never drops) the
working database, so the source files are never at risk.

**Verification:** after export it checks per-table row counts
(`verify_counts.ps1`) and text encoding (`verify_encoding.ps1`); the encoding
check catches UTF-16 to UTF-8 transcoding errors that a row-count comparison
cannot detect. Both exit non-zero on a discrepancy.
