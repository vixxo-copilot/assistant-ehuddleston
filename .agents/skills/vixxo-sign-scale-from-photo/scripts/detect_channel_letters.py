#!/usr/bin/env python3
"""Detect channel-letter cap-line edges on tan/low-contrast fascias.

Uses CLAHE, green-logo anchor (when present), cap-row ink, and Sobel edge
peaks. Avoids the common cornice false-positive band.

Outputs pixel corners for measure_facade.py / overlay drawing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def leaf_mask(arr: np.ndarray, y_min: int, y_max: int) -> np.ndarray:
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    m = (
        (g > r + 18)
        & (g > b + 12)
        & (g >= 115)
        & (g <= 200)
        & (r < 120)
    )
    m[:y_min, :] = False
    m[y_max:, :] = False
    return m


def clahe_enhanced(crop: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(crop, cv2.COLOR_RGB2LAB)
    l, a, bb = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    return cv2.cvtColor(cv2.merge([clahe.apply(l), a, bb]), cv2.COLOR_LAB2RGB)


def cap_row_ink(enh: np.ndarray, row_lo: int, row_hi: int) -> np.ndarray:
    band = enh[row_lo:row_hi, :]
    rr = band[:, :, 0].astype(np.int16)
    gg = band[:, :, 1].astype(np.int16)
    bb = band[:, :, 2].astype(np.int16)
    ink = (bb > rr + 3) & (bb > gg + 1)
    for y in range(ink.shape[0]):
        if ink[y].mean() > 0.35:
            ink[y, :] = False
    return ink


def sobel_edges(gray: np.ndarray, row_lo: int, row_hi: int) -> np.ndarray:
    cap = gray[row_lo:row_hi, :]
    sx = np.abs(cv2.Sobel(cap, cv2.CV_64F, 1, 0, ksize=3))
    return sx.sum(axis=0)


def find_edge_peaks(profile: np.ndarray, x0: int, x1: int, min_strength: float) -> list[int]:
    region = profile[x0:x1]
    if region.size == 0:
        return []
    thresh = max(region.max() * min_strength, 800)
    peaks: list[int] = []
    for i in range(1, len(region) - 1):
        if region[i] >= thresh and region[i] >= region[i - 1] and region[i] >= region[i + 1]:
            peaks.append(x0 + i)
    return peaks


def column_cap_stats(ink: np.ndarray, y_offset: int, min_rows: int = 5) -> list[tuple[int, int, int, int]]:
    cols: list[tuple[int, int, int, int]] = []
    h, w = ink.shape
    for x in range(w):
        ys = np.where(ink[:, x])[0]
        if len(ys) >= min_rows:
            cols.append((x, ys.min() + y_offset, ys.max() + y_offset, ys.max() - ys.min() + 1))
    return cols


def detect(
    arr: np.ndarray,
    glass_top_y: int | None = None,
) -> dict:
    h, w = arr.shape[:2]
    glass_top = glass_top_y if glass_top_y is not None else int(h * 0.48)
    y0 = max(90, glass_top - 130)
    y1 = min(h - 5, glass_top - 25)

    leaf = leaf_mask(arr, y0, y1)
    ys, xs = np.where(leaf)
    has_leaf = len(xs) > 0
    if has_leaf:
        leaf_l, leaf_r = int(xs.min()), int(xs.max())
        leaf_t, leaf_b = int(ys.min()), int(ys.max())
        leaf_cx = (leaf_l + leaf_r) // 2
        x0 = max(0, leaf_l - 200)
        x1 = min(w - 1, leaf_r + 200)
    else:
        leaf_l = leaf_r = leaf_t = leaf_b = leaf_cx = None
        x0, x1 = int(w * 0.15), int(w * 0.85)

    crop = arr[y0:y1, x0:x1]
    enh = clahe_enhanced(crop)
    gray = cv2.cvtColor(enh, cv2.COLOR_RGB2GRAY)

    # Cap rows: anchor to green leaf top when present (not fixed crop offset)
    if has_leaf and leaf_t is not None:
        row_lo = max(0, min(enh.shape[0] - 8, leaf_t - y0 - 2))
    else:
        row_lo = max(0, min(enh.shape[0] - 8, int(enh.shape[0] * 0.35)))
    row_hi = min(enh.shape[0], row_lo + 14)
    ink = cap_row_ink(enh, row_lo, row_hi)

    # Width from cap-row ink columns
    ink_cols = np.where(ink.any(axis=0))[0]
    sign_l_ink = sign_r_ink = None
    if len(ink_cols) >= 2:
        sign_l_ink = int(ink_cols.min()) + x0
        sign_r_ink = int(ink_cols.max()) + x0

    # Sobel refinement
    profile = sobel_edges(gray, row_lo, row_hi)
    if has_leaf:
        left_peaks = find_edge_peaks(profile, max(0, leaf_l - x0 - 120), leaf_l - x0 - 5, 0.22)
        right_peaks = find_edge_peaks(profile, leaf_r - x0 + 5, min(profile.size, leaf_r - x0 + 120), 0.22)
    else:
        left_peaks = find_edge_peaks(profile, 0, profile.size // 2, 0.25)
        right_peaks = find_edge_peaks(profile, profile.size // 2, profile.size, 0.25)

    sign_l_sobel = (left_peaks[0] + x0) if left_peaks else None
    sign_r_sobel = (right_peaks[-1] + x0) if right_peaks else None
    sign_l = sign_l_sobel if sign_l_sobel is not None else sign_l_ink
    sign_r = sign_r_sobel if sign_r_sobel is not None else sign_r_ink

    # Prefer cap-row ink span when Sobel collapses to interior strokes
    if sign_l_ink is not None and sign_r_ink is not None:
        ink_w = sign_r_ink - sign_l_ink
        sob_w = (sign_r - sign_l) if sign_l is not None and sign_r is not None else 0
        if ink_w >= 80 and (sob_w < 80 or abs(sign_l_ink - (sign_l or 0)) > 25):
            sign_l = sign_l_ink
            sign_r = sign_r_ink
        elif sign_l is None:
            sign_l = sign_l_ink
        elif sign_r is None:
            sign_r = sign_r_ink

    # Cap height from full-body columns in crop (centered on cap rows)
    body_lo = max(0, row_lo - 10)
    body_hi = min(enh.shape[0], row_lo + 50)
    rr = enh[body_lo:body_hi, :, 0].astype(np.int16)
    gg = enh[body_lo:body_hi, :, 1].astype(np.int16)
    bb = enh[body_lo:body_hi, :, 2].astype(np.int16)
    body_ink = (bb > rr + 3) & (bb > gg + 1)
    for y in range(body_ink.shape[0]):
        if body_ink[y].mean() > 0.12:
            body_ink[y, :] = False
    cols = column_cap_stats(body_ink, y0 + body_lo, min_rows=4)
    cap_top = cap_bot = None
    if cols:
        max_h = max(c[3] for c in cols)
        tall = [c for c in cols if c[3] >= max(12, int(max_h * 0.7))]
        if tall:
            cap_top = int(np.median([c[1] for c in tall]))
            cap_bot = int(np.median([c[2] for c in tall]))
            if sign_l is None:
                sign_l = min(c[0] for c in tall) + x0
            if sign_r is None:
                sign_r = max(c[0] for c in tall) + x0

    warnings: list[str] = []
    if sign_l is None or sign_r is None or cap_top is None or cap_bot is None:
        warnings.append("incomplete_detection")
    elif cap_top is not None and cap_top < y0 + 5:
        warnings.append("cap_top_near_cornice_check_y_band")
    if sign_l is not None and sign_r is not None and sign_r - sign_l < 80:
        warnings.append("width_span_too_narrow_recheck_cap_rows")
    if (
        sign_l_ink is not None
        and sign_r_ink is not None
        and sign_r_ink - sign_l_ink > 0.55 * w
    ):
        warnings.append("width_span_suspiciously_wide_check_seam_mask")

    sign_quad: list[str] | None = None
    if sign_l is not None and sign_r is not None and cap_top is not None and cap_bot is not None:
        sign_quad = [
            f"{sign_l},{cap_top}",
            f"{sign_r},{cap_top}",
            f"{sign_l},{cap_bot}",
            f"{sign_r},{cap_bot}",
        ]

    return {
        "fascia_band": {"y0": y0, "y1": y1, "x0": x0, "x1": x1},
        "leaf": {
            "found": has_leaf,
            "l": leaf_l,
            "r": leaf_r,
            "t": leaf_t,
            "b": leaf_b,
            "cx": leaf_cx,
        },
        "sign_l": sign_l,
        "sign_r": sign_r,
        "cap_top": cap_top,
        "cap_bot": cap_bot,
        "width_px": (sign_r - sign_l + 1) if sign_l is not None and sign_r is not None else None,
        "cap_px": (cap_bot - cap_top + 1) if cap_top is not None and cap_bot is not None else None,
        "ink_width_fallback": {"l": sign_l_ink, "r": sign_r_ink},
        "sign_quad": sign_quad,
        "measure_facade_sign_args": sign_quad,
        "warnings": warnings,
    }


def draw_debug(arr: np.ndarray, result: dict, path: Path) -> None:
    img = Image.fromarray(arr.copy())
    draw = ImageDraw.Draw(img)
    fb = result["fascia_band"]
    draw.line([(0, fb["y0"]), (arr.shape[1], fb["y0"])], fill=(255, 0, 255), width=1)
    draw.line([(0, fb["y1"]), (arr.shape[1], fb["y1"])], fill=(255, 0, 255), width=1)
    if result["leaf"]["found"]:
        lf = result["leaf"]
        draw.rectangle([lf["l"], lf["t"], lf["r"], lf["b"]], outline=(0, 200, 0), width=2)
    if result["sign_l"] is not None and result["sign_r"] is not None:
        sl, sr = result["sign_l"], result["sign_r"]
        ct, cb = result["cap_top"], result["cap_bot"]
        if ct is not None and cb is not None:
            draw.line([(sl, ct), (sr, ct)], fill=(0, 255, 255), width=2)
            draw.line([(sl, cb), (sr, cb)], fill=(0, 255, 255), width=2)
            draw.line([(sl, ct), (sl, cb)], fill=(0, 255, 0), width=2)
            draw.line([(sr, ct), (sr, cb)], fill=(0, 255, 0), width=2)


    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--glass-top-y", type=int, help="Y pixel of storefront glass top")
    parser.add_argument("--debug", help="Save QA debug PNG")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    arr = np.array(Image.open(args.image).convert("RGB"))
    result = detect(arr, glass_top_y=args.glass_top_y)

    if args.debug:
        draw_debug(arr, result, Path(args.debug))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"sign_l={result['sign_l']} sign_r={result['sign_r']}")
        print(f"cap_top={result['cap_top']} cap_bot={result['cap_bot']}")
        if result["warnings"]:
            print("warnings:", ", ".join(result["warnings"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
