"""Load and query the raceway-color registry (color-registry.json)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "color-registry.json"


@lru_cache(maxsize=1)
def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().upper())


def _index_registry(reg: dict) -> dict[str, list[dict]]:
    """Map normalized alias -> list of matching entries."""
    idx: dict[str, list[dict]] = {}

    def add(key: str, entry: dict) -> None:
        k = _norm(key)
        idx.setdefault(k, [])
        if entry not in idx[k]:
            idx[k].append(entry)

    for face in reg.get("letter_faces", []):
        entry = {**face, "system": "acrylic", "category": "letter_face"}
        add(face["code"], entry)
        add(face["code"].lstrip("#"), entry)

    for vinyl in reg.get("vinyl_and_films", []):
        entry = {**vinyl, "system": "vinyl", "category": "letter_material"}
        add(vinyl["code"], entry)

    for system_key, system_label in (
        ("sherwin_williams", "sw"),
        ("benjamin_moore", "bm"),
        ("pantone", "pms"),
        ("custom", "custom"),
    ):
        for row in reg.get("field_paint", {}).get(system_key, []):
            entry = {**row, "system": system_label, "category": "field_paint"}
            add(row["code"], entry)
            if "number" in row:
                add(row["number"], entry)
                add(f"SW {row['number']}", entry)
                add(f"BM {row['number']}", entry)
                add(f"PMS {row['number']}", entry)
            for alias in row.get("aliases", []):
                add(alias, entry)

    return idx


def lookup(query: str) -> list[dict]:
    """Find registry entries by code, number, or alias (case-insensitive)."""
    reg = load_registry()
    idx = _index_registry(reg)
    q = _norm(query)
    hits = list(idx.get(q, []))
    if hits:
        return hits
    # Fuzzy: strip SW/PMS/BM/# prefixes
    for prefix in ("SW ", "PMS ", "PANTONE ", "BM ", "#"):
        if q.startswith(prefix.strip()):
            q2 = q[len(prefix.strip()) :].strip()
            hits = idx.get(q2, [])
            if hits:
                return hits
    if q.isdigit() and len(q) == 4:
        return idx.get(q, []) or idx.get(f"SW {q}", [])
    return []


def list_by_tier(tier: int) -> list[dict]:
    reg = load_registry()
    out: list[dict] = []
    for face in reg.get("letter_faces", []):
        if face.get("tier") == tier:
            out.append({**face, "system": "acrylic", "category": "letter_face"})
    for system_key, system_label in (
        ("sherwin_williams", "sw"),
        ("benjamin_moore", "bm"),
        ("pantone", "pms"),
        ("custom", "custom"),
    ):
        for row in reg.get("field_paint", {}).get(system_key, []):
            if row.get("tier") == tier:
                out.append({**row, "system": system_label, "category": "field_paint"})
    return out


def list_by_system(system: str) -> list[dict]:
    reg = load_registry()
    system = system.lower()
    if system in ("acrylic", "plex", "letter"):
        return [{**f, "system": "acrylic", "category": "letter_face"} for f in reg.get("letter_faces", [])]
    key_map = {
        "sw": "sherwin_williams",
        "sherwin-williams": "sherwin_williams",
        "bm": "benjamin_moore",
        "benjamin-moore": "benjamin_moore",
        "pms": "pantone",
        "pantone": "pantone",
        "custom": "custom",
    }
    fk = key_map.get(system)
    if not fk:
        return []
    label = fk.split("_")[0] if fk != "custom" else "custom"
    if fk == "sherwin_williams":
        label = "sw"
    elif fk == "benjamin_moore":
        label = "bm"
    elif fk == "pantone":
        label = "pms"
    return [
        {**row, "system": label, "category": "field_paint"}
        for row in reg.get("field_paint", {}).get(fk, [])
    ]


def sw_rgb_map() -> dict[str, tuple[int, int, int]]:
    reg = load_registry()
    out: dict[str, tuple[int, int, int]] = {}
    for row in reg.get("field_paint", {}).get("sherwin_williams", []):
        if "rgb" in row:
            key = f"{row['code']} {row['name']}"
            out[key] = tuple(row["rgb"])
    return out


def bm_rgb_map() -> dict[str, tuple[int, int, int]]:
    reg = load_registry()
    out: dict[str, tuple[int, int, int]] = {}
    for row in reg.get("field_paint", {}).get("benjamin_moore", []):
        if "rgb" in row:
            key = f"{row['code']}"
            out[key] = tuple(row["rgb"])
    return out


def pms_to_sw_map() -> dict[str, str]:
    reg = load_registry()
    out: dict[str, str] = {}
    for key, values in reg.get("pms_to_sw", {}).items():
        if values:
            out[key] = values[0]
    return out


def normalize_hex(hex_val: str | None) -> str | None:
    if not hex_val:
        return None
    h = str(hex_val).strip().lstrip("#").upper()
    if len(h) != 6 or not all(c in "0123456789ABCDEF" for c in h):
        return None
    return f"#{h}"


def color_swatch_md(hex_val: str | None) -> str:
    """Inline HTML swatch + hex for markdown output."""
    hx = normalize_hex(hex_val)
    if not hx:
        return "—"
    return (
        f'<span style="display:inline-block;width:18px;height:18px;background:{hx};'
        f'border:1px solid #666;border-radius:3px;vertical-align:middle"></span> '
        f"**{hx}**"
    )


def get_part_defaults(part: str) -> dict | None:
    return load_registry().get("part_defaults", {}).get(part.upper())


def list_sign_components() -> list[str]:
    return load_registry().get("sign_components", [])


def enrich_code(code: str) -> dict | None:
    """Return registry metadata for a paint code string, or None."""
    hits = lookup(code)
    if not hits:
        return None
    row = dict(hits[0])
    hx = normalize_hex(row.get("hex"))
    if hx:
        row["hex"] = hx
    return row
