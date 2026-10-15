"""Vitosoft unit tokens -> Home Assistant / SI unit symbols.

Single source of truth for the `unit_of_measurement:` and `device_class:` that
`gen_catalog.py` emits. Stdlib-only, no dependencies.

WHY A TABLE AND NOT THE TRANSLATIONS
The export names a unit by a token (`ecnUnit.kWh`, `ecnUnit.U pro min`, ...)
whose display text lives in `Textresource_<culture>.xml`. That text is a UI
label, not a unit symbol, and it differs by language: `ecnUnit.kWh` is "kWh" in
German and "кВтч" in Russian, `ecnUnit.dBm` is "-dBm" in German, "dBm" in
English and "#NAME?" in Russian, and English leaves `ecnUnit.sech` empty. Home
Assistant needs one canonical symbol per quantity (its device classes and
long-term statistics key on it), so the symbol is fixed here and the catalog
language changes names and labels only, never units.

ROW FORMAT
    token: (symbol, device_class, negate)
- symbol        -- HA's spelling where HA has the unit (`L/h`, `m³/h`, `var`),
                   SI/ISO otherwise; "" = dimensionless, emit no unit.
- device_class  -- only where the unit determines the quantity unambiguously
                   and HA accepts that unit for the class; None otherwise. `K`
                   (a temperature DIFFERENCE), `%`, `m³` (gas or water?) get none.
- negate        -- the device stores a magnitude whose sign is in the unit.
                   `ecnUnit.dBm`: the RF level datapoints are unsigned bytes
                   (`Byte`, NoConversion) and German Vitosoft labels them
                   "-dBm", i.e. a stored 70 is -70 dBm. UNVERIFIED on hardware.

COVERAGE
Every unit token in the 2026 export has a row (60 tokens; the table also keeps
the older spellings earlier exports used). A token missing here falls back to
its German label, never to the translated label of the catalog language;
tests/unit/test_units.py checks the table's shape.
"""

UNITS = {
    # temperature / temperature difference
    "ecnUnit.Grad C": ("°C", "temperature", False),
    "ecnUnit.K": ("K", None, False),
    "ecnUnit.Kelvin": ("K", None, False),
    "ecnUnit.K pro h": ("K/h", None, False),
    "ecnUnit.KelvinProStunde": ("K/h", None, False),
    "ecnUnit.K Min": ("K·min", None, False),
    "ecnUnit.K Sec": ("K·s", None, False),
    "ecnUnit.Grad C pro Min": ("°C/min", None, False),
    "ecnUnit.Grad": ("°", None, False),
    # ratios
    "ecnUnit.Prozent": ("%", None, False),
    "ecnUnit.ProzentProStunde": ("%/h", None, False),
    "ecnUnit.Prozent pro K": ("%/K", None, False),
    "ecnUnit.ppm": ("ppm", None, False),
    "ecnUnit.Minus": ("", None, False),
    "Pkt": ("pts", None, False),
    "Pts": ("pts", None, False),
    # time
    "ecnUnit.Sekunden": ("s", "duration", False),
    "ecnUnit.Sek.": ("s", "duration", False),
    "ecnUnit.Minuten": ("min", "duration", False),
    "Minuten": ("min", "duration", False),
    "ecnUnit.Stunden": ("h", "duration", False),
    "ecnUnit.h": ("h", "duration", False),
    "ecnUnit.Tage": ("d", "duration", False),
    "ecnUnit.Monate": ("months", None, False),
    "ecnUnit.Jahre": ("a", None, False),
    "ecnUnit.sech": ("s/h", None, False),
    # energy
    "ecnUnit.Wh": ("Wh", "energy", False),
    "ecnUnit.kWh": ("kWh", "energy", False),
    "ecnUnit.KiloWattStunden": ("kWh", "energy", False),
    "ecnUnit.KiloWattstunde": ("kWh", "energy", False),
    "ecnUnit.MWh": ("MWh", "energy", False),
    "ecnUnit.MegaWattStunden": ("MWh", "energy", False),
    "ecnUnit.kJ": ("kJ", "energy", False),
    "ecnUnit.MJ": ("MJ", "energy", False),
    "ecnUnit.GJ": ("GJ", "energy", False),
    "ecnUnit.ct_pro_kwh": ("ct/kWh", None, False),
    "ecnUnit.kWh pro m3": ("kWh/m³", None, False),
    # power
    "ecnUnit.W": ("W", "power", False),
    "ecnUnit.Watt": ("W", "power", False),
    "ecnUnit.kW": ("kW", "power", False),
    "ecnUnit.KW": ("kW", "power", False),
    "ecnUnit.KiloWatt": ("kW", "power", False),
    # "1/10 kW" is a scaling statement, not a unit; the one datapoint carrying
    # it keeps the literal text so nobody reads its raw value as kW.
    "ecnUnit.kW_10": ("1/10 kW", None, False),
    "ecnUnit.VA": ("VA", "apparent_power", False),
    "ecnUnit.VAr": ("var", "reactive_power", False),
    # electrical
    "ecnUnit.V": ("V", "voltage", False),
    "ecnUnit.Volt": ("V", "voltage", False),
    "ecnUnit.mV": ("mV", "voltage", False),
    "ecnUnit.A": ("A", "current", False),
    "ecnUnit.Ampere": ("A", "current", False),
    "ecnUnit.MilliAmpere": ("mA", "current", False),
    "ecnUnit.Ah": ("Ah", None, False),
    "ecnUnit.Ohm": ("Ω", None, False),
    "ecnUnit.Hz": ("Hz", "frequency", False),
    "ecnUnit.Hertz": ("Hz", "frequency", False),
    "Hz": ("Hz", "frequency", False),
    "ecnUnit.dBm": ("dBm", "signal_strength", True),
    # pressure
    "ecnUnit.Bar": ("bar", "pressure", False),
    "ecnUnit.Bar (absolut)": ("bar", "pressure", False),
    "ecnUnit.mBar": ("mbar", "pressure", False),
    "ecnUnit.MilliBar": ("mbar", "pressure", False),
    "ecnUnit.Pascal": ("Pa", "pressure", False),
    "ecnUnit.HektoPascal": ("hPa", "pressure", False),
    # volume, flow, mass
    "ecnUnit.Liter": ("L", None, False),
    "Liter": ("L", None, False),
    "ecnUnit.m3": ("m³", None, False),
    "ecnUnit.KubikMeter": ("m³", None, False),
    "ecnUnit.l pro h": ("L/h", None, False),
    "ecnUnit.LiterProStunde": ("L/h", None, False),
    "ecnUnit.l pro min": ("L/min", "volume_flow_rate", False),
    "ecnUnit.LiterProMinute": ("L/min", "volume_flow_rate", False),
    "ecnUnit.m3 pro h": ("m³/h", "volume_flow_rate", False),
    "ecnUnit.KubikMeterProStunde": ("m³/h", "volume_flow_rate", False),
    "ecnUnit.cbm pro h": ("m³/h", "volume_flow_rate", False),
    "ecnUnit.kg": ("kg", "weight", False),
    "ecnUnit.Tonnen": ("t", None, False),
    "ecnUnit.kg_pro_h": ("kg/h", None, False),
    "ecnUnit.g_pro_sec": ("g/s", None, False),
    # rotation
    "ecnUnit.U pro min": ("rpm", None, False),
    "ecnUnit.Umdrehungen": ("rpm", None, False),
    "ecnUnit.UmdrehungenProMinute": ("rpm", None, False),
    "ecnUnit.rps": ("rps", None, False),
    "ecnUnit.rps pro s": ("rps/s", None, False),
}

# Symbol -> device_class, derived from UNITS (one class per symbol; the table
# never gives one symbol two classes -- tests/unit/test_units.py checks it).
DEVICE_CLASS_BY_SYMBOL = {sym: dc for sym, dc, _neg in UNITS.values() if dc}


def lookup(token: str):
    """(symbol, device_class, negate) for a raw unit token, or None."""
    return UNITS.get((token or "").strip())
