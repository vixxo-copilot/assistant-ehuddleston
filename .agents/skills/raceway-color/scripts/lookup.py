#!/usr/bin/env python3
"""Raceway color lookup from art/survey PDFs and optional site photo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from extract_survey_paint import extract_pdf, merge_extractions
from raceway_output import build_raceway_rows, format_raceway_markdown
from reconcile_colors import reconcile_photo

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import numpy as np
from PIL import Image

from sample_photo_colors import auto_bands, sample_region


def _largest_embedded_photo(pdf_path: Path, page_index: int = 0) -> Path | None:
    if fitz is None:
        return None
    out_dir = pdf_path.parent / f".{pdf_path.stem}-photos"
    out_dir.mkdir(exist_ok=True)
    doc = fitz.open(pdf_path)
    if page_index >= doc.page_count:
        return None
    best: tuple[int, Path] | None = None
    for i, info in enumerate(doc[page_index].get_images(full=True)):
        xref = info[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        area = pix.width * pix.height
        if area < 40_000:
            continue
        path = out_dir / f"p{page_index + 1}-img{i}.png"
        pix.save(path)
        if best is None or area > best[0]:
            best = (area, path)
    return best[1] if best else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Raceway color lookup from PDFs + optional photo")
    ap.add_argument("design", nargs="?", help="Design # label (VX1108893) for output header only")
    ap.add_argument("--art", type=Path, help="Shop drawing / art PDF (preferred first)")
    ap.add_argument("--survey", type=Path, action="append", default=[], help="Survey PDF(s)")
    ap.add_argument("--image", type=Path, help="Site photo (optional; else largest embed from art p1)")
    ap.add_argument("--json", action="store_true", help="JSON output (default is markdown with color swatches)")
    args = ap.parse_args()

    pdfs: list[Path] = []
    if args.art:
        pdfs.append(args.art)
    pdfs.extend(args.survey)
    if not pdfs:
        ap.error("Provide --art and/or --survey PDF")

    extractions = [extract_pdf(p) for p in pdfs]
    merged = merge_extractions([e["merged"] for e in extractions])
    sources = [str(p.resolve()) for p in pdfs]
    rows = build_raceway_rows(merged)

    image_path = args.image
    if image_path is None and args.art:
        image_path = _largest_embedded_photo(args.art, 0)

    conflicts: list[str] = []
    photo_sample = None
    photo = None
    if image_path and image_path.exists():
        arr = np.array(Image.open(image_path).convert("RGB"))
        h, w = arr.shape[:2]
        photo = {
            "image": str(image_path.resolve()),
            "samples": {n: sample_region(arr, *b) for n, b in auto_bands(h, w).items()},
        }
        photo_result = reconcile_photo(merged, photo)
        conflicts = photo_result.get("conflicts", [])
        photo_sample = photo["samples"].get("raceway_band") or photo["samples"].get("center_fascia_band")

    if args.json:
        payload = {
            "design": args.design,
            "sources": sources,
            "raceway": rows,
            "merged": merged,
            "photo_sample": photo_sample,
            "conflicts": conflicts,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            format_raceway_markdown(
                rows,
                design=args.design,
                sources=sources,
                merged=merged,
                photo_used=str(image_path.resolve()) if image_path else None,
                photo_sample=photo_sample,
                conflicts=conflicts,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
