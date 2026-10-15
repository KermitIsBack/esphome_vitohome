#!/usr/bin/env bash
# Regenerate the committed catalog set from a Vitosoft export:
#
#   example/catalogs/de/*.yaml + index.csv    German catalogs
#   example/catalogs/de/gfa/chip_<XX>.yaml    German GFA companions, one per chip
#   example/catalogs/en/...                   the same in English
#   example/catalogs/resolve.json             the catalog finder's lookup table
#
# Both languages carry the same files under the same names; only the entity
# names, option labels and fault texts differ (units do not -- scripts/units.py).
# resolve.json does not depend on the language, so one copy serves both.
#
# The export directory must hold the FULL Textresource_de.xml and
# Textresource_en.xml (about 30 MB each, from the Vitosoft installation): the
# slim Textresource.xml alone has no entity names and no fault texts, and the
# catalogs would silently fall back to technical identifiers.
#
# Usage, from anywhere:  bash scripts/export_catalogs.sh <vitosoft-export-dir>
set -euo pipefail

DATA="${1:?usage: scripts/export_catalogs.sh <vitosoft-export-dir>}"
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
OUT="example/catalogs"

for lang in de en; do
  f="$DATA/Textresource_$lang.xml"
  if [ ! -f "$f" ] || [ "$(wc -c < "$f")" -lt 10000000 ]; then
    echo "error: $f is missing or is the slim UI-strings file; copy the full one from the Vitosoft installation" >&2
    exit 1
  fi
done

# The generator owns every *.yaml and index.csv under example/catalogs; clear
# them so a catalog that is no longer produced does not linger. This also
# removes the pre-0008 single-language set at the top level. The hand-written
# README.md files are left alone.
rm -f "$OUT"/*.yaml "$OUT"/index.csv
for lang in de en; do
  mkdir -p "$OUT/$lang"
  rm -f "$OUT/$lang"/*.yaml "$OUT/$lang"/index.csv "$OUT/$lang"/resolve.json "$OUT/$lang"/gfa/*.yaml
  "$PY" scripts/gen_catalog.py --data "$DATA" --export-all --culture "$lang" --out "$OUT/$lang"
done

# One lookup table for both languages; refuse to pick one if they disagree.
# Compared in Python (already required) rather than with cmp, which not every
# Windows shell has.
if ! "$PY" -c 'import sys; a, b = (open(f, "rb").read() for f in sys.argv[1:]); sys.exit(a != b)' "$OUT/de/resolve.json" "$OUT/en/resolve.json"; then
  echo "error: resolve.json differs between de and en -- the catalog sets do not match" >&2
  exit 1
fi
mv "$OUT/de/resolve.json" "$OUT/resolve.json"
rm "$OUT/en/resolve.json"
echo "catalogs: $(ls "$OUT/de"/*.yaml | wc -l) per language in $OUT/{de,en}; lookup: $OUT/resolve.json"
