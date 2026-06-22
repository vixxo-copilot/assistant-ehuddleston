"""Raceway color output helpers — hex swatches and markdown tables."""

from __future__ import annotations

from color_registry import color_swatch_md, enrich_code, normalize_hex


def enrich_raceway_row(row: dict) -> dict:
    meta = enrich_code(row.get("code", ""))
    if meta:
        row = {
            **row,
            "registry_name": meta.get("name"),
            "registry_use": meta.get("use"),
            "tier": meta.get("tier"),
        }
        hx = normalize_hex(meta.get("hex"))
        if hx:
            row["hex"] = hx
    if row.get("suggested_sw"):
        sug = enrich_code(row["suggested_sw"])
        if sug:
            row["suggested_name"] = sug.get("name")
            hx = normalize_hex(sug.get("hex"))
            if hx:
                row["suggested_hex"] = hx
    if row.get("hex") and "swatch" not in row:
        row["swatch"] = color_swatch_md(row["hex"])
    return row


def build_raceway_rows(merged: dict) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    def add(row: dict) -> None:
        key = row.get("code", "")
        if key in seen:
            return
        seen.add(key)
        rows.append(enrich_raceway_row(row))

    for fp in merged.get("sign_colors", {}).get("field_paint", []):
        if "raceway" in fp.get("surface", "").lower():
            add(
                {
                    "code": fp["code"],
                    "system": fp.get("system", "—"),
                    "source": "extract",
                    "confidence": "high",
                }
            )

    for code in merged.get("sherwin_williams", []):
        add({"code": code, "system": "SW", "source": "extract", "confidence": "high"})
    for code in merged.get("benjamin_moore", []):
        label = f"BM {code}".replace("BM BM", "BM")
        add({"code": label, "system": "BM", "source": "extract", "confidence": "high"})
    for p in merged.get("pantone", []):
        sug = next(
            (x["suggested_sw"] for x in merged.get("pms_to_sw_suggestions", []) if x["pms"] == p),
            None,
        )
        add(
            {
                "code": p,
                "system": "PMS",
                "suggested_sw": sug,
                "source": "extract",
                "confidence": "high" if sug else "medium",
            }
        )
    for name in merged.get("custom_paint", []):
        add({"code": name, "system": "custom", "source": "extract", "confidence": "high"})
    for desc in merged.get("fascia_descriptive", []):
        add({"code": desc, "system": "descriptive", "source": "extract", "confidence": "medium"})
    for note in merged.get("raceway_notes", []):
        add({"code": note, "system": "intake", "source": "extract", "confidence": "medium"})

    return rows


def format_raceway_markdown(
    rows: list[dict],
    design: str | None = None,
    sources: list[str] | None = None,
    merged: dict | None = None,
    photo_used: str | None = None,
    photo_sample: dict | None = None,
    conflicts: list[str] | None = None,
) -> str:
    lines = ["## Raceway color"]
    if design:
        lines.append(f"**Design:** {design}")
    lines.append("")
    lines.append("| Color | Code | Name | System | Confidence |")
    lines.append("|-------|------|------|--------|------------|")

    if rows:
        for r in rows:
            hx = r.get("hex") or r.get("suggested_hex")
            swatch = color_swatch_md(hx) if hx else "—"
            name = r.get("registry_name") or r.get("suggested_name") or "—"
            if r.get("suggested_sw") and r.get("system") == "PMS":
                sug_swatch = color_swatch_md(r.get("suggested_hex"))
                name = f"{name} → {r['suggested_sw']} {sug_swatch}"
            lines.append(
                f"| {swatch} | {r.get('code', '—')} | {name} | {r.get('system', '—')} | {r.get('confidence', '—')} |"
            )
    else:
        lines.append("| — | — | needs visual read | — | — |")

    if photo_sample:
        lines += [
            "",
            "## Photo sample (raceway band)",
            f"- Sampled: {color_swatch_md(photo_sample.get('hex'))} nearest **{photo_sample.get('sw_code', '—')}** "
            f"({photo_sample.get('sw_name', '—')})",
        ]
        if photo_sample.get("bm_code"):
            lines.append(
                f"- Alternate: {color_swatch_md(photo_sample.get('bm_hex'))} **{photo_sample['bm_code']}**"
            )

    if sources:
        lines += ["", "## Sources"]
        for s in sources:
            lines.append(f"- {s}")
    if photo_used:
        lines.append(f"- Photo: `{photo_used}`")

    if merged:
        hits = [h["text"] for h in merged.get("context_lines", [])[:8]]
        if hits:
            lines += ["", "## Spec excerpts"]
            for t in hits:
                lines.append(f"- {t[:140]}")
        if merged.get("needs_visual_read"):
            lines += ["", "## Action", "- PDF text sparse — render art page 2 + survey visually."]

    if conflicts:
        lines += ["", "## Conflicts"]
        for c in conflicts:
            lines.append(f"- {c}")

    lines += [
        "",
        "## Order note",
        "- SW Pro Industrial DTM Acrylic; same code + sheen as matched fascia/pocket/beam.",
        "- Brush-out on site when photo and spec disagree.",
    ]
    return "\n".join(lines)


def format_registry_markdown(entries: list[dict]) -> str:
    lines = ["| Color | Code | Name | Use |", "|-------|------|------|-----|"]
    for e in entries:
        hx = normalize_hex(e.get("hex"))
        swatch = color_swatch_md(hx) if hx else "—"
        lines.append(
            f"| {swatch} | **{e.get('code', '—')}** | {e.get('name', '—')} | {e.get('use', '—')} |"
        )
    return "\n".join(lines)
