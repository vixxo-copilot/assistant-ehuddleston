#!/usr/bin/env python3
"""Sample fascia / raceway colors from a storefront photo (JSON to stdout)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from sw_palette import nearest_sw


def sample_region(arr: np.ndarray, y1: int, y2: int, x1: int, x2: int) -> dict:
    crop = arr[y1:y2, x1:x2].reshape(-1, 3).astype(float)
    r, g, b = crop[:, 0], crop[:, 1], crop[:, 2]
    mask = (
        (r > 130)
        & (g > 120)
        & (b > 100)
        & (r < 245)
        & (r - b < 60)
        & (np.abs(r.astype(int) - g.astype(int)) < 45)
    )
    pts = crop[mask] if mask.sum() > 20 else crop
    med = tuple(int(x) for x in np.median(pts, axis=0))
    out = {
        "region": {"y1": y1, "y2": y2, "x1": x1, "x2": x2},
        "rgb": list(med),
        "hex": f"#{med[0]:02x}{med[1]:02x}{med[2]:02x}",
    }
    out.update(nearest_sw(med))
    return out


def auto_bands(h: int, w: int) -> dict[str, tuple[int, int, int, int]]:
    """Default regions for channel-letter fascia photos (full-width bands)."""
    return {
        "center_fascia_band": (int(h * 0.33), int(h * 0.42), int(w * 0.03), int(w * 0.97)),
        "upper_fascia_band": (int(h * 0.07), int(h * 0.17), int(w * 0.2), int(w * 0.8)),
        "lower_fascia_band": (int(h * 0.80), int(h * 0.90), int(w * 0.2), int(w * 0.8)),
        "raceway_band": (int(h * 0.56), int(h * 0.59), int(w * 0.25), int(w * 0.85)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Sample fascia colors from a photo")
    ap.add_argument("image", type=Path)
    ap.add_argument("--json", action="store_true", help="Print JSON only")
    args = ap.parse_args()

    arr = np.array(Image.open(args.image).convert("RGB"))
    h, w = arr.shape[:2]
    bands = auto_bands(h, w)
    samples = {name: sample_region(arr, *box) for name, box in bands.items()}

    payload = {
        "image": str(args.image.resolve()),
        "size": {"width": w, "height": h},
        "samples": samples,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
