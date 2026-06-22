#!/usr/bin/env python3
"""Reconcile survey raceway paint with photo samples (JSON + markdown)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from extract_survey_paint import extract_from_text, extract_pdf, merge_extractions
from raceway_output import build_raceway_rows, format_raceway_markdown
from sample_photo_colors import auto_bands, sample_region

import numpy as np
from PIL import Image


def reconcile_photo(merged: dict, photo: dict) -> dict:
    sw_survey = merged.get("sherwin_williams", [])
    bm_survey = merged.get("benjamin_moore", [])
    survey_sw_nums = {c.replace("SW ", "") for c in sw_survey}
    conflicts: list[str] = []

    for key, sample in photo.get("samples", {}).items():
        photo_code = sample["sw_code"]
        if sw_survey and photo_code.replace("SW ", "") not in survey_sw_nums:
            conflicts.append(
                f"{key}: photo ~{photo_code}, survey cites {', '.join(sw_survey + bm_survey)}"
            )

    raceway_sample = photo.get("samples", {}).get("raceway_band") or photo.get("samples", {}).get(
        "center_fascia_band"
    )
    return {"conflicts": conflicts, "photo_sample": raceway_sample}


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile survey + photo raceway colors")
    ap.add_argument("--image", type=Path, required=True)
    ap.add_argument("--survey", type=Path, action="append", default=[], help="Survey/art PDF(s)")
    ap.add_argument("--survey-text", type=Path, help="Survey plain text (if PDF OCR needed)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    arr = np.array(Image.open(args.image).convert("RGB"))
    h, w = arr.shape[:2]
    photo = {
        "image": str(args.image.resolve()),
        "size": {"width": w, "height": h},
        "samples": {n: sample_region(arr, *b) for n, b in auto_bands(h, w).items()},
    }

    if args.survey_text:
        merged = extract_from_text(args.survey_text.read_text(encoding="utf-8", errors="ignore"))
    elif args.survey:
        merged = merge_extractions([extract_pdf(p)["merged"] for p in args.survey])
    else:
        merged = {}

    rows = build_raceway_rows(merged)
    photo_result = reconcile_photo(merged, photo)

    if args.json:
        print(
            json.dumps(
                {
                    "raceway": rows,
                    "photo_sample": photo_result.get("photo_sample"),
                    "conflicts": photo_result.get("conflicts", []),
                },
                indent=2,
            )
        )
    else:
        print(
            format_raceway_markdown(
                rows,
                sources=[str(p.resolve()) for p in args.survey] if args.survey else [],
                merged=merged,
                photo_used=str(args.image.resolve()),
                photo_sample=photo_result.get("photo_sample"),
                conflicts=photo_result.get("conflicts", []),
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
