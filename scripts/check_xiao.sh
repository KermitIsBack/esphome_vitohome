#!/usr/bin/env bash
# Validate both profiles in an isolated dummy-secrets directory. Never upload.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
root="$PWD"
stage="$root/.validation/xiao"
mkdir -p "$stage"
cp devices/xiao-esp32s3/{base.yaml,read-only.yaml,with-controls.yaml} "$stage/"
cp devices/xiao-esp32s3/secrets.example.yaml "$stage/secrets.yaml"
# Both directories are two levels below the repository root.
for profile in read-only with-controls; do
  if ! "$root/.venv/bin/esphome" config "$stage/$profile.yaml" >"$stage/$profile.schema.log" 2>&1; then
    cat "$stage/$profile.schema.log" >&2
    exit 1
  fi
done
printf 'Beide XIAO-Konfigurationen sind gültig. Es wurde nichts geflasht.\n'
