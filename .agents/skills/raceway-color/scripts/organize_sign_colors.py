"""Organize extracted sign colors into a full component sheet."""

from __future__ import annotations

from color_registry import enrich_code, load_registry


def _empty_sign_colors() -> dict:
    return {
        "letter_faces": [],
        "films_vinyl": [],
        "factory_finishes": [],
        "field_paint": [],
        "part_numbers": [],
        "gaps": [],
    }


def apply_part_defaults(sheet: dict) -> dict:
    """Fill missing letter/factory specs from registry part_defaults."""
    reg = load_registry()
    parts = sheet.get("part_numbers") or []
    for part in parts:
        defaults = reg.get("part_defaults", {}).get(part.upper())
        if not defaults:
            continue
        existing_elements = {f.get("element", "").upper() for f in sheet["letter_faces"]}
        for face in defaults.get("letter_faces", []):
            el = face.get("element", "").upper()
            if el not in existing_elements and el != "ALL WORDS":
                row = {**face, "source": "part_default"}
                sheet["letter_faces"].append(row)
            elif el == "ALL WORDS" and not sheet["letter_faces"]:
                sheet["letter_faces"].append({**face, "source": "part_default"})
        for face in defaults.get("letter_faces", []):
            if face.get("overlay"):
                spec = face["overlay"]
                if any(
                    (v.get("element") or "").upper() == (face.get("element") or "").upper()
                    and (spec in (v.get("spec") or "") or (v.get("spec") or "") in spec)
                    for v in sheet["films_vinyl"]
                ):
                    continue
                sheet["films_vinyl"].append(
                    {
                        "element": face.get("element"),
                        "spec": face["overlay"],
                        "substrate": face.get("code"),
                        "source": "part_default",
                    }
                )
        existing_factory = {f.get("component") for f in sheet["factory_finishes"]}
        for fin in defaults.get("factory_finishes", []):
            if fin.get("component") not in existing_factory:
                sheet["factory_finishes"].append({**fin, "source": "part_default"})
    return sheet


def build_sign_color_sheet(merged: dict, photo_result: dict | None = None) -> dict:
    """Build full sign color sheet from extract merge + optional photo reconcile."""
    sheet = _empty_sign_colors()

    # Structured extract (preferred)
    if merged.get("sign_colors"):
        sc = merged["sign_colors"]
        sheet["letter_faces"] = list(sc.get("letter_faces", []))
        sheet["films_vinyl"] = list(sc.get("films_vinyl", []))
        sheet["factory_finishes"] = list(sc.get("factory_finishes", []))
        sheet["field_paint"] = list(sc.get("field_paint", []))
        sheet["part_numbers"] = list(sc.get("part_numbers", []))

    # Legacy flat keys → field paint + materials
    if not sheet["part_numbers"]:
        sheet["part_numbers"] = list(merged.get("part_numbers", []))

    surface_default = "fascia / sign band"
    for code in merged.get("sherwin_williams", []):
        if not _has_field_code(sheet["field_paint"], code):
            sheet["field_paint"].append(
                {"surface": surface_default, "code": code, "system": "SW", "source": "extract"}
            )
    for bm in merged.get("benjamin_moore", []):
        label = bm if str(bm).startswith("BM ") else f"BM {bm}"
        if not _has_field_code(sheet["field_paint"], label):
            sheet["field_paint"].append(
                {"surface": "beam / fascia", "code": label, "system": "BM", "source": "extract"}
            )
    for p in merged.get("pantone", []):
        if not _has_field_code(sheet["field_paint"], p):
            sug = next(
                (x["suggested_sw"] for x in merged.get("pms_to_sw_suggestions", []) if x["pms"] == p),
                None,
            )
            row = {"surface": surface_default, "code": p, "system": "PMS", "source": "extract"}
            if sug:
                row["suggested_sw"] = sug
            sheet["field_paint"].append(row)
    for name in merged.get("custom_paint", []):
        sheet["field_paint"].append(
            {"surface": "canopy / custom", "code": name, "system": "custom", "source": "extract"}
        )
    for desc in merged.get("fascia_descriptive", []):
        sheet["field_paint"].append(
            {"surface": "fascia (descriptive)", "code": desc, "system": "descriptive", "source": "extract"}
        )
    for note in merged.get("raceway_notes", []):
        sheet["field_paint"].append(
            {"surface": "raceway (intake)", "code": note, "system": "intake", "source": "extract"}
        )

    for plex in merged.get("plexiglas", []):
        code = plex if plex.startswith("#") else f"#{plex.lstrip('#')}"
        if not any(f.get("code") == code for f in sheet["letter_faces"]):
            sheet["letter_faces"].append(
                {"element": "letters (unspecified)", "code": code, "source": "extract"}
            )

    sheet = apply_part_defaults(sheet)

    # Enrich from registry
    for row in sheet["letter_faces"]:
        meta = enrich_code(row.get("code", ""))
        if meta:
            row["name"] = meta.get("name")
    for row in sheet["field_paint"]:
        meta = enrich_code(row.get("code", ""))
        if meta:
            row["name"] = meta.get("name")

    if merged.get("needs_visual_read"):
        sheet["gaps"].append("PDF text sparse — render art page 2 + survey visually")

    missing = []
    if not sheet["letter_faces"]:
        missing.append("letter faces")
    if not sheet["field_paint"]:
        missing.append("field paint (fascia/raceway/wall)")
    if missing:
        sheet["gaps"].append(f"No extract for: {', '.join(missing)} — check art + standards")

    if photo_result:
        sheet["photo_conflicts"] = photo_result.get("conflicts", [])
        for row in photo_result.get("field_paint", []):
            if row.get("source") == "photo":
                sheet["field_paint"].append(
                    {
                        "surface": row.get("surface", "photo sample"),
                        "code": row.get("code"),
                        "name": row.get("name"),
                        "system": "SW",
                        "source": "photo",
                        "confidence": row.get("confidence", "medium"),
                        "hex": row.get("hex"),
                    }
                )

    sheet["context_lines"] = merged.get("context_lines", [])[:12]
    sheet["needs_visual_read"] = merged.get("needs_visual_read", False)
    return sheet


def _has_field_code(rows: list[dict], code: str) -> bool:
    return any(r.get("code") == code for r in rows)


def to_sign_markdown(sheet: dict, design: str | None = None, sources: list[str] | None = None) -> str:
    lines: list[str] = ["# Sign color sheet"]
    if design:
        lines.append(f"**Design:** {design}")
    lines.append("")

    lines += ["## 1. Letter faces (illuminated)", "| Element | Code | Material / name | Source |", "|---------|------|---------------|--------|"]
    if sheet["letter_faces"]:
        for r in sheet["letter_faces"]:
            mat = r.get("material") or r.get("name") or "—"
            lines.append(f"| {r.get('element', '—')} | {r.get('code', '—')} | {mat} | {r.get('source', 'extract')} |")
    else:
        lines.append("| — | — | Pull from art page 2 or part_defaults | — |")

    lines += ["", "## 2. Films & vinyl overlays", "| Element | Spec | Substrate | Source |", "|---------|------|-----------|--------|"]
    if sheet["films_vinyl"]:
        for r in sheet["films_vinyl"]:
            lines.append(
                f"| {r.get('element', '—')} | {r.get('spec') or r.get('code', '—')} | {r.get('substrate', '—')} | {r.get('source', 'extract')} |"
            )
    else:
        lines.append("| — | — | — | — |")

    lines += ["", "## 3. Factory finishes (not site paint)", "| Component | Spec | Source |", "|-----------|------|--------|"]
    if sheet["factory_finishes"]:
        for r in sheet["factory_finishes"]:
            lines.append(f"| {r.get('component', '—')} | {r.get('spec', '—')} | {r.get('source', 'extract')} |")
    else:
        lines.append("| returns | pre-painted black (Sally SB30 default) | standards |")
        lines.append("| trim cap | black (Sally SB30 default) | standards |")

    lines += [
        "",
        "## 4. Field paint (site-applied)",
        "| Surface | Code | Name | System | Source |",
        "|---------|------|------|--------|--------|",
    ]
    if sheet["field_paint"]:
        for r in sheet["field_paint"]:
            name = r.get("name") or r.get("suggested_sw") or "—"
            conf = f" ({r['confidence']})" if r.get("confidence") else ""
            lines.append(
                f"| {r.get('surface', '—')} | {r.get('code', '—')} | {name} | {r.get('system', '—')} | {r.get('source', 'extract')}{conf} |"
            )
    else:
        lines.append("| — | — | needs visual read | — | — |")

    if sheet.get("part_numbers"):
        lines += ["", "## 5. Part numbers", "- " + ", ".join(sheet["part_numbers"])]

    lines += ["", "## 6. Gaps / caveats"]
    if sheet.get("needs_visual_read"):
        lines.append("- **Scanned PDF** — render art page 2 if extract is empty.")
    for g in sheet.get("gaps", []):
        lines.append(f"- {g}")
    if sheet.get("photo_conflicts"):
        for c in sheet["photo_conflicts"]:
            lines.append(f"- **Photo conflict:** {c}")
    elif not sheet.get("gaps"):
        lines.append("- Survey/art codes take priority over photo estimates.")

    if sheet.get("context_lines"):
        lines.append("- Spec excerpts:")
        for hit in sheet["context_lines"][:6]:
            t = hit["text"] if isinstance(hit, dict) else str(hit)
            lines.append(f"  - {t[:120]}")

    if sources:
        lines += ["", "## Sources"]
        for s in sources:
            lines.append(f"- {s}")

    lines += [
        "",
        "## Order notes",
        "- Letter faces: order acrylic stock # — not wall paint.",
        "- Raceway/fascia: SW Pro Industrial DTM Acrylic; same code + sheen per surface.",
        "- Factory finishes (returns, trim): do not field-paint unless art revises.",
    ]
    return "\n".join(lines)
