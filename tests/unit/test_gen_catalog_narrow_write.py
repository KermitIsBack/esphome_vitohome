"""Writes narrower than their block are demoted to read-only (gen_catalog).

Hardware, VScotHO1_72 (P300), 2026-10-14: Neptun_ZP~0x7953 is a 2-byte block
whose byte 1 read 00 before any write. After a 1-byte write the device held
01 D6, then 00 D5 -- byte 1 became the checksum byte of our own write telegram.
The device writes its whole datapoint and fills it from whatever follows the
payload. The ACK and a 1-byte read-back both look fine, so the generator, which
knows the block length, is the only place that can prevent it.

    python -m pytest tests/unit/test_gen_catalog_narrow_write.py -q
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS = os.path.join(_REPO_ROOT, "scripts")
for _p in (_SCRIPTS, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_catalog as gc  # noqa: E402


def _ev(values=None, **over):
    """Vitotwin_1013_Leistungsgrenze_Haupterzeuger-shaped: a writable 1-byte
    field at byte 0 of a 2-byte block."""
    kw = {
        "id": "t",
        "name": "Vitotwin 1013 Leistungsgrenze Haupterzeuger",
        "tech": "Vitotwin_1013_Leistungsgrenze_Haupterzeuger",
        "address": 0x1013,
        "conversion": "NoConversion",
        "access_type": 3,
        "block_length": 2,
        "byte_length": 1,
        "byte_position": 0,
        "bit_length": 0,
        "bit_position": 0,
        "lower": "0",
        "upper": "100",
        "stepping": "1",
        "fc_read": "Virtual_READ",
        "fc_write": "Virtual_WRITE",
    }
    kw.update(over)
    ev = gc.Event(**kw)
    if values:
        ev.values = [gc.EventValue(enum_address_value=v, description=label) for v, label in values]
    return ev


def test_narrow_numeric_write_is_demoted():
    platform, lines = gc.emit_entity(_ev(), "full", gc.PROTO_P300)
    assert platform == "sensor"
    text = "\n".join(lines)
    assert "writes 1 byte(s) of a 2-byte block" in text
    assert "hardware-confirmed" in text
    assert "min_value" not in text


def test_narrow_two_byte_write_in_a_three_byte_block_is_demoted():
    # Vitotwin_2000_Komfortsollwert: 2 bytes of a 3-byte block.
    ev = _ev(address=0x2000, block_length=3, byte_length=2, conversion="Div10", lower="10", upper="30", stepping="0.5")
    platform, lines = gc.emit_entity(ev, "full", gc.PROTO_P300)
    assert platform == "sensor"
    assert "writes 2 byte(s) of a 3-byte block" in "\n".join(lines)


def test_narrow_enum_write_is_demoted():
    # Vitotwin_1030_Brenner_sperren: a select on byte 0 of a 2-byte block.
    ev = _ev(values=[(0, "frei"), (1, "gesperrt"), (2, "extern")], lower="", upper="", stepping="")
    platform, lines = gc.emit_entity(ev, "full", gc.PROTO_P300)
    assert platform == "text_sensor"
    assert "writes 1 byte(s) of a 2-byte block" in "\n".join(lines)


def test_full_width_write_is_unchanged():
    # BedienRTSolltemperaturA1M1 (0x2306): a true 1-byte datapoint stays writable.
    ev = _ev(address=0x2306, block_length=1, byte_length=1, lower="3", upper="37")
    platform, lines = gc.emit_entity(ev, "full", gc.PROTO_P300)
    assert platform == "number"
    assert "byte(s) of a" not in "\n".join(lines)


def test_whole_block_write_is_unchanged():
    # A 2-byte field that IS the whole 2-byte block writes the whole datapoint.
    ev = _ev(block_length=2, byte_length=2, lower="0", upper="1000")
    platform, _ = gc.emit_entity(ev, "full", gc.PROTO_P300)
    assert platform == "number"
