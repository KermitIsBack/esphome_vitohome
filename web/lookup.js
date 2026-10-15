// Catalog finder lookup for esphome_vitohome.
//
// All matching rules live in scripts/gen_catalog.py (Catalog.resolve_pool).
// example/catalogs/resolve.json is that function's answer for every device id,
// hardware index and software index, so this file only reads the table. The
// pytest in tests/unit/test_resolve_index.py runs it under Node and compares
// each answer with Catalog.resolve().
"use strict";

const hex = (value, width) => value.toString(16).toUpperCase().padStart(width, "0");

function parseHex(text, max) {
  if (text === null || text === undefined) return null;
  const match = /^\s*(?:0x)?([0-9a-f]+)\s*$/i.exec(String(text));
  if (!match) return null;
  const value = parseInt(match[1], 16);
  return value <= max ? value : null;
}

// Reads the identification out of anything the hub prints, e.g.
//   "Device: 0x2053 (GWG_VBEM) HW=0x01 SW=0x7A"
// plus an optional "GFA=0x24": the burner-control chip, which selects the GFA
// fault-text companion. Missing fields come back as null.
function parseIdentification(text) {
  // Prefer the hub's own "Device:" / "Device identification:" line when a whole
  // log was pasted, so an unrelated 0xNNNN address earlier in it is not taken.
  // Without such a line, only a single-line input (a typed "0x20CB HW=03 ...")
  // is read: in a multi-line paste the first 0xNNNN is a register address far
  // more often than a device id.
  const pasted = String(text || "");
  const line = /^.*\bDevice(?: identification)?:.*\b0x[0-9a-f]{4}\b.*$/im.exec(pasted);
  const trimmed = pasted.trim();
  if (!line && /[\r\n]/.test(trimmed)) return { id: null, hw: null, sw: null, f0: null, gfa: null };
  const source = line ? line[0].slice(line[0].search(/\bDevice(?: identification)?:/i)) : trimmed;
  const pick = (pattern, max) => {
    const match = pattern.exec(source);
    return match ? parseHex(match[1], max) : null;
  };
  return {
    id: pick(/\b0x([0-9a-f]{4})\b/i, 0xffff),
    hw: pick(/\bHW\s*[=:]\s*(?:0x)?([0-9a-f]{1,2})\b/i, 0xff),
    sw: pick(/\bSW\s*[=:]\s*(?:0x)?([0-9a-f]{1,2})\b/i, 0xff),
    f0: pick(/\bF0\s*[=:]\s*(?:0x)?([0-9a-f]{1,4})\b/i, 0xffff),
    gfa: pick(/\bGFA\s*[=:]\s*(?:0x)?([0-9a-f]{1,2})\b/i, 0xff),
  };
}

function catalogOf(data, token) {
  return data.tokens[token] || { file: "", status: "unknown", detail: "not part of this export" };
}

// Returns one of:
//   { kind: "unknown", ident }
//   { kind: "family", ident, tokens: [{token, catalog}] }
//   { kind: "need-sw", ident, tokens: [{token, catalog}] }
//   { kind: "match", ident, token, catalog, how, hwIgnored, sw: [lo, hi],
//     f0: null | "matched" | "missing" | "no-match", candidates, unranged }
function lookup(data, id, hw, sw, f0) {
  if (id === null || id === undefined) return { kind: "unknown", ident: null };
  const ident = hex(id, 4);
  const entry = data.idents[ident];
  const describe = (token) => ({ token, catalog: catalogOf(data, token) });
  if (!entry) return { kind: "unknown", ident };
  if (entry.family) return { kind: "family", ident, tokens: entry.family.map(describe) };

  const hwKey = hw === null || hw === undefined ? null : hex(hw, 2);
  const hwKnown = hwKey !== null && Object.prototype.hasOwnProperty.call(entry.hw, hwKey);
  const runs = hwKnown ? entry.hw[hwKey] : entry.any;

  if (sw === null || sw === undefined) {
    const seen = new Set();
    for (const run of runs) for (const c of run.candidates || [{ token: run.token }]) seen.add(c.token);
    return { kind: "need-sw", ident, tokens: [...seen].map(describe) };
  }

  const run = runs.find((r) => r.sw[0] <= sw && sw <= r.sw[1]);
  let token = run.token;
  let f0State = null;
  const candidates = (run.candidates || []).map((c) => ({ ...describe(c.token), f0: c.f0 }));
  if (candidates.some((c) => c.f0 !== null)) {
    f0State = "missing";
    if (f0 !== null && f0 !== undefined) {
      const hit = candidates.find((c) => c.f0 !== null && c.f0[0] <= f0 && f0 <= c.f0[1]);
      f0State = hit ? "matched" : "no-match";
      if (hit) token = hit.token;
    }
  }
  return {
    kind: "match",
    ident,
    token,
    catalog: catalogOf(data, token),
    how: run.how,
    hwIgnored: hwKey !== null && !hwKnown,
    hwCatalogued: Object.keys(entry.hw),
    sw: run.sw,
    f0: f0State,
    candidates,
    unranged: (entry.unranged || []).map(describe),
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { lookup, parseIdentification, parseHex };
}
