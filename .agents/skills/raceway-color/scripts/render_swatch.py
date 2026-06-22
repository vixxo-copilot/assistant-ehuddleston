#!/usr/bin/env python3
"""Render raceway paint colors as PNG swatch images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from color_registry import list_by_tier, lookup, normalize_hex
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "swatches"


def _hex_to_rgb(hex_val: str) -> tuple[int, int, int]:
    h = normalize_hex(hex_val)
    if not h:
        raise ValueError(f"Invalid hex: {hex_val}")
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def render_single(code: str, hex_val: str, name: str, out: Path, size: int = 400) -> Path:
    rgb = _hex_to_rgb(hex_val)
    img = Image.new("RGB", (size, size + 80), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size, size], fill=rgb, outline=(102, 102, 102), width=2)
    label = f"{code}  {name}\n{normalize_hex(hex_val)}"
    draw.multiline_text((12, size + 12), label, fill=(30, 30, 30))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def render_palette(entries: list[dict], out: Path, swatch: int = 120) -> Path:
    rows = []
    for e in entries:
        hx = normalize_hex(e.get("hex"))
        if hx:
            rows.append((e.get("code", ""), e.get("name", ""), hx))

    cols = min(4, max(1, len(rows)))
    row_count = (len(rows) + cols - 1) // cols
    pad = 16
    label_h = 52
    w = cols * swatch + (cols + 1) * pad
    h = row_count * (swatch + label_h) + (row_count + 1) * pad
    img = Image.new("RGB", (w, h), (248, 248, 248))
    draw = ImageDraw.Draw(img)

    for i, (code, name, hx) in enumerate(rows):
        col = i % cols
        row = i // cols
        x = pad + col * (swatch + pad)
        y = pad + row * (swatch + label_h + pad)
        rgb = _hex_to_rgb(hx)
        draw.rectangle([x, y, x + swatch, y + swatch], fill=rgb, outline=(102, 102, 102), width=1)
        draw.text((x, y + swatch + 4), code, fill=(20, 20, 20))
        draw.text((x, y + swatch + 20), hx, fill=(80, 80, 80))
        if name:
            short = name if len(name) <= 18 else name[:16] + "…"
            draw.text((x, y + swatch + 36), short, fill=(60, 60, 60))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Render raceway color swatch PNGs")
    ap.add_argument("--code", help="Single code (7100, SW 7100, PMS 482 C)")
    ap.add_argument("--tier", type=int, choices=[1, 2, 3], help="Render palette for tier")
    ap.add_argument("--out", type=Path, help="Output PNG path")
    args = ap.parse_args()

    if args.code:
        hits = lookup(args.code)
        if not hits or not hits[0].get("hex"):
            print(f"No hex in registry for: {args.code}", file=sys.stderr)
            return 1
        e = hits[0]
        hx = normalize_hex(e["hex"])
        out = args.out or OUT_DIR / f"{e['code'].replace(' ', '_')}.png"
        path = render_single(e["code"], hx, e.get("name", ""), out)
        print(path)
        return 0

    if args.tier is not None:
        entries = [e for e in list_by_tier(args.tier) if e.get("category") == "field_paint" and e.get("hex")]
        out = args.out or OUT_DIR / f"raceway-tier-{args.tier}.png"
        path = render_palette(entries, out)
        print(path)
        return 0

    ap.error("Provide --code or --tier")
    return 2


if __name__ == "__main__":
    sys.exit(main())
