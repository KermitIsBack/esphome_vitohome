# Examples

Configurations for the `vitohome` component. Each file carries a header comment
explaining its purpose in more detail.

## Reference-unit device configs / user curated

The official Viessmann XML catalogs are not complete and datapoints that are
supported by the unit may not be included in the automatically generated
configuration files.

[`example/user_curated`](example/user_curated/) contains contributed device
configurations that can serve as a starting point.

Contributions there go in `example/user_curated/<device>/` as
`<device>.vitohome.yaml` (the full device config) plus `*.dp.*.yaml` datapoint
packages, and CI (`scripts/validate_user_curated.sh`) checks that:

- the device file takes everything from this repo through the
  `vitohome_repo` / `vitohome_ref` substitutions (`url: ${vitohome_repo}`), so
  CI can validate the files in the pull request rather than what is on GitHub;
  no other sources;
- credentials use `!secret` with the names in
  [`secrets.example.yaml`](secrets.example.yaml);
- `esphome config` passes on the ESPHome version pinned in
  `requirements.txt`, so keep `min_version` at or below it.

## Feature examples

Each is self-contained (validates on its own). To adopt a feature, lift the
relevant block into your device config and keep your own network, `uart:`, and
secrets.

| File | Demonstrates |
|---|---|
| `vitohome-climate.yaml` | Heating circuit 1 as a Home Assistant climate/thermostat card. Betriebsart is exposed as custom presets that bind the split read/write value spaces (write `0x2323`, read `0x2301`) in one place. |
| `vitohome-dhw.yaml` | Domestic hot water as a native HA `water_heater`, built from existing datapoints via ESPHome's template platform — temperature-only, because DHW on/off is folded into the shared Betriebsart register on this controller. |
| `vitohome-timer-clock.yaml` | `time_sync` (hub reads the device clock at `0x088E` and rewrites it on drift) plus per-day Schaltzeiten editing through `text:` entities — one entity per weekday holding that day's switching program. |
| `vitohome-scanner-raw.yaml` | The raw-lane console: one-off `queue_raw_read`/`queue_raw_write`, raw hex with exact 64-bit integer views (no float32 narrowing), and a range sweep from an HA action. Use it to probe addresses. |

## Supporting file

| File | Purpose |
|---|---|
| `secrets.example.yaml` | Copy to `secrets.yaml` alongside your config and fill in the API Noise key and OTA password. These configs use Ethernet (DM9051), so no Wi-Fi secrets are needed. |

## The full catalog set — `catalogs/`

`catalogs/` is the **entire generated catalog**: one ready-to-include package
per Viessmann unit, produced from the Vitosoft **2026** XML export by
`scripts/gen_catalog.py --export-all`. It holds **180 device catalogs**
(group-ordered) plus a manifest.

> :warning: **Warning**
> Do not blindly add full catalogs since ESPHome registers all data points
> regardless if they are set to `disabled_by_default: true` or not.
> Especially on resource-constraint devices this may lead to unwanted
> behavior.

- **Find your unit with the [catalog finder](https://soulsolistice.github.io/esphome_vitohome/)**: paste the
  `Device` line the hub logs at boot, or follow the link the hub logs right
  after it. The finder applies the same matching rules as
  `gen_catalog.py --identify` and tells you when a match is only approximate.

- **`catalogs/index.csv`** — the manifest behind the finder.
  It has one row per device token in the export (**399** rows): **180** are
  `status: ok` (a catalog file was written), **198** are
  `status: skipped: no Optolink-reachable datapoints` (no file — every datapoint
  on that unit needs a non-Optolink access method), and **21** are
  `status: missing: …` — the GWG units, whose catalogs are not committed here.
  `gen_catalog.py --export-all` writes them like any other unit; this one row
  status is set by hand for the committed set and is never produced by the
  generator. Columns:

  | Column | Meaning |
  |---|---|
  | `file` | Catalog filename to include (blank when skipped) |
  | `token` | Vitosoft device token, e.g. `VScotHO1_72` |
  | `ident` | Identification hex, `group << 8 \| ident`, e.g. `0x20CB` |
  | `hw_index` | Hardware index |
  | `sw_lo` / `sw_hi` | Software-index range this catalog covers |
  | `f0_lo` / `f0_hi` | Protocol-offset (`0xF0`) range |
  | `events` | Datapoints linked to the unit in the export |
  | `entities` | Entities actually emitted (after profile/filters) |
  | `bytes` | File size |
  | `status` | `ok`, `skipped: …`, or `error: …` (`missing: …` in the committed set only) |
  | `ext_raw` | Raw identification-extension field |

  Reading it by hand takes three steps, and the device id alone is not enough
  (most ids have several rows):

  1. Filter by `ident`, the 4-digit value the hub logs (e.g. `0x20CB`).
  2. Pick the row whose `sw_lo`..`sw_hi` range contains your software index.
     The hub logs it in **hex** (`SW=0x51`); the columns are **decimal** (81).
     If no range contains it, take the row with the highest `sw_lo` below it.
     Use `hw_index` only when the id lists more than one value; a logged `HW`
     that does not occur for the id is ignored.
  3. If several rows remain, they differ by `f0_lo`..`f0_hi`, the value at
     address `0x00F0`, which the hub does not read.

- **`catalogs/resolve.json`** — the same mapping, precomputed for every device
  id, hardware index and software index. The finder reads this file; it is
  written by `gen_catalog.py --export-all` together with `index.csv`.

- **`catalogs/README.md`** — a short pointer stub for the directory.

> **Fault codes in the bulk set.** `--export-all` attaches the default `vd300`
> (Vitodens 300-W B3HA) fault-code map to *every* unit. Fault-code semantics are
> device-variant-specific, so for any unit other than the reference one,
> regenerate that catalog individually with the right `--error-code-set` — see
> [`scripts/README.md`](../scripts/README.md).

## Using a catalog

Include the file you want as a package and define the hub yourself (or start
from `vscotho1_72.vitohome.yaml`, which already does):

```yaml
packages:
  heater: !include vscotho1_72.dp.curated.yaml   # or catalogs/<your-unit>.yaml
```

Every generated entity is `disabled_by_default: true`, so you opt in to each one
from Home Assistant. Always run `esphome config`, then `esphome compile` / `run`,
before relying on a value — not every address answers on every firmware.
