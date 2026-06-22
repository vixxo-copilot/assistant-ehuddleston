#!/usr/bin/env python3
"""Extract all sign color callouts from survey / art PDF text (JSON to stdout)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

from color_registry import load_registry
from sw_palette import PMS_TO_SW

SW_RE = re.compile(
    r"(?:SW|Sherwin[- ]?Williams?)\s*[#]?\s*(\d{4})\b",
    re.I,
)
PAINTED_SW_RE = re.compile(
    r"PAINTED\s+(?:TO\s+MATCH\s+)?(?:BUILDING\s+SIGN\s*BAND\s*FASCIA\s*)?SW\s+(\d{4})\s*([A-Z][A-Za-z\s-]{2,30})?",
    re.I,
)
PMS_RE = re.compile(r"PMS\s*(\d{3,4})\s*([CU])?", re.I)
PANTONE_RE = re.compile(r"Pantone\s*(\d{3,4})\s*([CU])?", re.I)
PMS_INLINE_RE = re.compile(r"(?:PMS|Pantone)\s*(\d{3,4})([CU])\b", re.I)
WALL_COLOR_RE = re.compile(
    r"WALL\s*COLOR\s*\|\s*(?:PANTONE|PMS)\s*(\d{3,4})\s*([CU])?",
    re.I,
)
FASCIA_COLOR_RE = re.compile(
    r"(?:Sign\s*Area\s*)?(?:Fascia|facia)\s*Color\s*(?:Pantone|PMS)?\s*(\d{3,4})\s*([CU])?",
    re.I,
)
FASCIA_DESC_RE = re.compile(
    r"(?:Sign\s*Area\s*)?(?:Fascia|facia)\s*Color\s+(?!Pantone|PMS|SW\s*\d)([A-Za-z][A-Za-z\s-]{2,24})",
    re.I,
)
FASCIA_SW_RE = re.compile(
    r"(?:Sign\s*Area\s*)?(?:Fascia|facia)\s*Color\s+SW\s+(\d{4})",
    re.I,
)
RW_COLOR_RE = re.compile(
    r"RW\s*Color\s*[-–:]\s*(?:SW\s*)?(\d{4})\b",
    re.I,
)
RW_COLOR_PMS_RE = re.compile(
    r"RW\s*Color\s*[-–:]\s*(?:PMS|Pantone)\s*(\d{3,4})\s*([CU])?",
    re.I,
)
BM_RE = re.compile(
    r"(?:BM|Benjamin\s+Moore)\s*[#]?\s*([A-Za-z][A-Za-z\s-]*\d{3,4}(?:-\d+)?|\d{3,4}(?:-\d+)?)",
    re.I,
)
BM_PAINTED_RE = re.compile(
    r"PAINTED\s+TO\s+MATCH\s+(?:BUILDING\s+SIGN\s*BAND\s*FASCIA\s*)?_?BM\s+([A-Za-z][A-Za-z\s-]+\d{3,4}(?:-\d+)?)",
    re.I,
)
BEAM_PAINT_RE = re.compile(
    r"(?:BEAM|ARCH(?:ITECTURAL)?\s*BEAM).*?(?:BM|SW|PMS)\s*([#\w\s-]+)",
    re.I,
)
CUSTOM_PAINT_RE = re.compile(
    r"(EAST\s+END\s+CANOPY\s+MATCH|CUSTOM\s+SHER[- ]?COLOR\s+MATCH)",
    re.I,
)
CANOPY_COLOR_RE = re.compile(
    r"CANOPY\s*(?:COLOR|MATCH|PAINT).*?(SW\s+\d{4}|PMS\s+\d{3,4}\s*[CU]?|BM\s+[\w\s-]+\d{3,4}(?:-\d+)?)",
    re.I,
)
POCKET_COLOR_RE = re.compile(
    r"(?:SIGN\s*)?POCKET\s*(?:COLOR|PANEL).*?(SW\s+\d{4}|PMS\s+\d{3,4}\s*[CU]?)",
    re.I,
)
CABINET_FACE_RE = re.compile(
    r"(?:CABINET|PANEL)\s*FACE\s*COLOR\s*(.+?)(?:\n|$)",
    re.I,
)
RACEWAY_NOTE_RE = re.compile(
    r"Raceway\s+color\s+is\s+(\w+)",
    re.I,
)
PAINTED_PMS_RE = re.compile(
    r"PAINTED\s+(?:PANTONE\s+)?PMS\s*(\d{3,4})\s*([CU])?",
    re.I,
)
WORD_FACE_RE = re.compile(
    r'["\']?\s*([A-Z][A-Za-z0-9\s&\'-]{1,24}?)\s*["\']?\s*#?\s*(\d{4})\s*'
    r"(RED|WHITE|BLUE|BLACK|GREEN|YELLOW)?\s*(?:3/16\"?\s*)?(?:IN\.?\s*)?(PLEX(?:IGLAS)?|ACRYLIC)",
    re.I,
)
PERF_VINYL_RE = re.compile(
    r"(\d+/\d+)\s*(?:BLACK\s+)?(?:PERF(?:ORATED)?\s*VINYL|PERFORATED\s+VINYL)",
    re.I,
)
THREE_M_RE = re.compile(r"3M\s*#?\s*(\d{4}-\d{3})", re.I)
RETURNS_FINISH_RE = re.compile(
    r"RETURNS?[^.\n]{0,40}PRE[- ]?PAINTED\s+(BLACK|WHITE|[A-Z][A-Za-z]+)",
    re.I,
)
TRIM_CAP_RE = re.compile(r"TRIM\s*CAP[^.\n]{0,30}\b(BLACK|WHITE)\b", re.I)
PART_RE = re.compile(r"\b(SB\d{2}[A-Z]{1,3})\b", re.I)

CONTEXT_KEYWORDS = re.compile(
    r"fascia|raceway|trim|wall|stucco|eifs|dryvit|sign\s*band|building|paint|color|match|beam|pocket|canopy|cabinet|panel|return|plex|acrylic|vinyl|3M",
    re.I,
)

VISUAL_READ_MIN_CHARS = 120


def _known_plex_numbers() -> set[str]:
    reg = load_registry()
    nums = {f["code"].lstrip("#") for f in reg.get("letter_faces", [])}
    nums.add("2648")
    return nums


def _pms_label(num: str, suffix: str | None) -> str:
    return f"PMS {num} {(suffix or 'C').upper()}"


def _collect_pms(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(num: str, suffix: str | None) -> None:
        label = _pms_label(num, suffix)
        if label not in seen:
            seen.add(label)
            found.append(label)

    for pat in (PMS_RE, PANTONE_RE, PMS_INLINE_RE, WALL_COLOR_RE, FASCIA_COLOR_RE, PAINTED_PMS_RE):
        for m in pat.finditer(text):
            add(m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None)
    return found


def _collect_sw(text: str) -> list[str]:
    codes = {m.group(1) for m in SW_RE.finditer(text)}
    codes |= {m.group(1) for m in RW_COLOR_RE.finditer(text)}
    codes |= {m.group(1) for m in FASCIA_SW_RE.finditer(text)}
    for m in PAINTED_SW_RE.finditer(text):
        codes.add(m.group(1))
    return sorted(codes)


def _collect_bm(text: str) -> list[str]:
    found: set[str] = set()
    for m in BM_RE.finditer(text):
        found.add(m.group(1).strip())
    for m in BM_PAINTED_RE.finditer(text):
        found.add(m.group(1).strip())
    return sorted(found)


def _extract_sign_colors(text: str) -> dict:
    """Structured sign color components."""
    letter_faces: list[dict] = []
    films_vinyl: list[dict] = []
    factory_finishes: list[dict] = []
    field_paint: list[dict] = []
    seen_faces: set[str] = set()

    for m in WORD_FACE_RE.finditer(text):
        element = m.group(1).strip().strip('"').strip("'")
        code = f"#{m.group(2)}"
        key = f"{element.upper()}:{code}"
        if key in seen_faces:
            continue
        seen_faces.add(key)
        row = {
            "element": element,
            "code": code,
            "material": f"3/16 {m.group(4)}".strip(),
            "source": "extract",
        }
        if m.group(3):
            row["hue"] = m.group(3).upper()
        letter_faces.append(row)

    plex_nums = _known_plex_numbers()
    for num in plex_nums:
        if re.search(rf"#?\s*{num}\b", text) and not any(f["code"] == f"#{num}" for f in letter_faces):
            letter_faces.append(
                {"element": "letters (unspecified)", "code": f"#{num}", "source": "extract"}
            )

    for m in THREE_M_RE.finditer(text):
        films_vinyl.append(
            {
                "element": "logo / graphic",
                "code": f"3M #{m.group(1)}",
                "source": "extract",
            }
        )

    for m in PERF_VINYL_RE.finditer(text):
        films_vinyl.append(
            {
                "element": "BEAUTY",
                "spec": f"{m.group(1)} black perf vinyl",
                "source": "extract",
            }
        )

    for m in RETURNS_FINISH_RE.finditer(text):
        factory_finishes.append(
            {"component": "returns", "spec": f"pre-painted {m.group(1).lower()}", "source": "extract"}
        )
    for m in TRIM_CAP_RE.finditer(text):
        factory_finishes.append(
            {"component": "trim_cap", "spec": m.group(1).lower(), "source": "extract"}
        )

    def add_field(surface: str, code: str, system: str) -> None:
        if any(r["surface"] == surface and r["code"] == code for r in field_paint):
            return
        field_paint.append({"surface": surface, "code": code, "system": system, "source": "extract"})

    for m in FASCIA_SW_RE.finditer(text):
        add_field("fascia / sign band", f"SW {m.group(1)}", "SW")
    for m in FASCIA_COLOR_RE.finditer(text):
        add_field("fascia / sign band", _pms_label(m.group(1), m.group(2)), "PMS")
    for m in FASCIA_DESC_RE.finditer(text):
        add_field("fascia (descriptive)", m.group(1).strip(), "descriptive")
    for m in RW_COLOR_RE.finditer(text):
        add_field("raceway", f"SW {m.group(1)}", "SW")
    for m in RW_COLOR_PMS_RE.finditer(text):
        add_field("raceway", _pms_label(m.group(1), m.group(2)), "PMS")
    for m in WALL_COLOR_RE.finditer(text):
        add_field("wall / building", _pms_label(m.group(1), m.group(2)), "PMS")
    for m in PAINTED_PMS_RE.finditer(text):
        add_field("raceway / fascia", _pms_label(m.group(1), m.group(2)), "PMS")
    for m in PAINTED_SW_RE.finditer(text):
        add_field("raceway / fascia", f"SW {m.group(1)}", "SW")
    for m in BM_PAINTED_RE.finditer(text):
        add_field("fascia / beam", f"BM {m.group(1).strip()}", "BM")
    for m in BM_RE.finditer(text):
        add_field("beam / building", f"BM {m.group(1).strip()}", "BM")
    for m in CUSTOM_PAINT_RE.finditer(text):
        add_field("canopy / custom", m.group(1).strip(), "custom")
    for m in CANOPY_COLOR_RE.finditer(text):
        add_field("canopy", m.group(1).strip(), "mixed")
    for m in POCKET_COLOR_RE.finditer(text):
        add_field("sign pocket / panel", m.group(1).strip(), "mixed")
    for m in CABINET_FACE_RE.finditer(text):
        add_field("cabinet / pan face", m.group(1).strip()[:60], "mixed")

    parts = sorted({m.group(1).upper() for m in PART_RE.finditer(text)})

    return {
        "letter_faces": letter_faces,
        "films_vinyl": films_vinyl,
        "factory_finishes": factory_finishes,
        "field_paint": field_paint,
        "part_numbers": parts,
    }


def _lines_with_context(text: str) -> list[dict]:
    hits: list[dict] = []
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if len(line) < 4:
            continue
        if not (
            SW_RE.search(line)
            or PAINTED_SW_RE.search(line)
            or PMS_RE.search(line)
            or PANTONE_RE.search(line)
            or WORD_FACE_RE.search(line)
            or THREE_M_RE.search(line)
            or PERF_VINYL_RE.search(line)
            or RETURNS_FINISH_RE.search(line)
            or TRIM_CAP_RE.search(line)
            or WALL_COLOR_RE.search(line)
            or FASCIA_COLOR_RE.search(line)
            or FASCIA_DESC_RE.search(line)
            or FASCIA_SW_RE.search(line)
            or RW_COLOR_RE.search(line)
            or BM_RE.search(line)
            or CUSTOM_PAINT_RE.search(line)
            or RACEWAY_NOTE_RE.search(line)
            or re.search(r"#?\s*\d{4}\b", line)
            or (PART_RE.search(line) and "SB" in line.upper())
            or (CONTEXT_KEYWORDS.search(line) and re.search(r"\d{3,4}|[A-Za-z]{3,}", line))
        ):
            continue
        hits.append({"line": i + 1, "text": line})
    return hits


def extract_from_text(text: str) -> dict:
    sign_colors = _extract_sign_colors(text)
    sw_codes = _collect_sw(text)
    pms = _collect_pms(text)
    bm = _collect_bm(text)
    plex = sorted({f["code"].lstrip("#") for f in sign_colors["letter_faces"]})
    parts = sign_colors["part_numbers"]
    fascia_desc = sorted({m.group(1).strip() for m in FASCIA_DESC_RE.finditer(text)})
    custom_paint = sorted({m.group(1).strip() for m in CUSTOM_PAINT_RE.finditer(text)})
    raceway_notes = sorted({m.group(1).strip() for m in RACEWAY_NOTE_RE.finditer(text)})

    pms_sw = []
    for p in pms:
        key = p.replace("PMS ", "").replace(" ", "")
        if key in PMS_TO_SW:
            pms_sw.append({"pms": p, "suggested_sw": PMS_TO_SW[key]})

    has_colors = bool(
        sw_codes
        or pms
        or bm
        or sign_colors["letter_faces"]
        or sign_colors["films_vinyl"]
        or sign_colors["factory_finishes"]
        or sign_colors["field_paint"]
        or fascia_desc
        or custom_paint
    )
    needs_visual_read = not has_colors and len(text.strip()) < VISUAL_READ_MIN_CHARS

    return {
        "sign_colors": sign_colors,
        "sherwin_williams": [f"SW {c}" for c in sw_codes],
        "pantone": sorted(set(pms)),
        "benjamin_moore": bm,
        "plexiglas": [f"#{n}" for n in plex],
        "part_numbers": parts,
        "fascia_descriptive": fascia_desc,
        "custom_paint": custom_paint,
        "raceway_notes": raceway_notes,
        "pms_to_sw_suggestions": pms_sw,
        "context_lines": _lines_with_context(text),
        "needs_visual_read": needs_visual_read,
        "text_char_count": len(text.strip()),
    }


def merge_extractions(merged_list: list[dict]) -> dict:
    """Merge multiple extract_from_text / extract_pdf merged dicts (art + survey)."""
    keys_list = [
        "sherwin_williams",
        "pantone",
        "benjamin_moore",
        "plexiglas",
        "part_numbers",
        "fascia_descriptive",
        "custom_paint",
        "raceway_notes",
    ]
    out: dict = {k: [] for k in keys_list}
    out["pms_to_sw_suggestions"] = []
    out["context_lines"] = []
    out["needs_visual_read"] = False
    out["text_char_count"] = 0
    out["sign_colors"] = _empty_sign_colors()

    seen: dict[str, set] = {k: set() for k in keys_list}
    sc = out["sign_colors"]

    def merge_sign_list(key: str, items: list[dict], dedupe_key: tuple[str, ...]) -> None:
        seen_keys: set[tuple] = set()
        for item in sc[key]:
            seen_keys.add(tuple(item.get(k) for k in dedupe_key))
        for item in items:
            t = tuple(item.get(k) for k in dedupe_key)
            if t not in seen_keys:
                seen_keys.add(t)
                sc[key].append(item)

    for m in merged_list:
        out["text_char_count"] += m.get("text_char_count", 0)
        out["needs_visual_read"] = out["needs_visual_read"] or m.get("needs_visual_read", False)
        for k in keys_list:
            for v in m.get(k, []):
                if v not in seen[k]:
                    seen[k].add(v)
                    out[k].append(v)
        for sug in m.get("pms_to_sw_suggestions", []):
            if sug not in out["pms_to_sw_suggestions"]:
                out["pms_to_sw_suggestions"].append(sug)
        out["context_lines"].extend(m.get("context_lines", []))

        src = m.get("sign_colors") or {}
        merge_sign_list("letter_faces", src.get("letter_faces", []), ("element", "code"))
        merge_sign_list("films_vinyl", src.get("films_vinyl", []), ("element", "spec", "code"))
        merge_sign_list("factory_finishes", src.get("factory_finishes", []), ("component", "spec"))
        merge_sign_list("field_paint", src.get("field_paint", []), ("surface", "code"))
        for p in src.get("part_numbers", []):
            if p not in sc["part_numbers"]:
                sc["part_numbers"].append(p)

    dedup_lines: list[dict] = []
    seen_text: set[str] = set()
    for hit in out["context_lines"]:
        t = hit["text"]
        if t in seen_text:
            continue
        seen_text.add(t)
        dedup_lines.append(hit)
    out["context_lines"] = dedup_lines[:20]
    return out


def _empty_sign_colors() -> dict:
    return {
        "letter_faces": [],
        "films_vinyl": [],
        "factory_finishes": [],
        "field_paint": [],
        "part_numbers": [],
    }


def extract_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages: list[dict] = []
    full_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        full_text.append(text)
        page_hits = extract_from_text(text)
        if any(
            page_hits.get(k)
            for k in (
                "sign_colors",
                "sherwin_williams",
                "pantone",
                "benjamin_moore",
                "plexiglas",
                "part_numbers",
                "context_lines",
            )
        ):
            pages.append({"page": i + 1, **page_hits})

    merged = extract_from_text("\n".join(full_text))
    return {
        "survey_pdf": str(path.resolve()),
        "page_count": len(reader.pages),
        "merged": merged,
        "by_page": pages,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract all sign colors from survey/art PDF")
    ap.add_argument("survey_pdf", type=Path, nargs="*", help="One or more PDF paths")
    ap.add_argument("--text", type=Path, help="Plain text file instead of PDF")
    args = ap.parse_args()

    if args.text:
        text = args.text.read_text(encoding="utf-8", errors="ignore")
        payload = {
            "survey_text": str(args.text.resolve()),
            "merged": extract_from_text(text),
            "by_page": [],
        }
    elif args.survey_pdf:
        extractions = [extract_pdf(p) for p in args.survey_pdf]
        if len(extractions) == 1:
            payload = extractions[0]
        else:
            payload = {
                "survey_pdfs": [e["survey_pdf"] for e in extractions],
                "merged": merge_extractions([e["merged"] for e in extractions]),
                "by_pdf": extractions,
            }
    else:
        ap.error("Provide survey_pdf or --text")
        return 2

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
