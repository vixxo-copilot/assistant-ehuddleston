"""Nearest Sherwin-Williams match for sampled RGB (sign fascia subset)."""

from __future__ import annotations

import math
from typing import Iterable

from color_registry import bm_rgb_map, pms_to_sw_map, sw_rgb_map

SW_COLORS: dict[str, tuple[int, int, int]] = sw_rgb_map()
BM_COLORS: dict[str, tuple[int, int, int]] = bm_rgb_map()
PMS_TO_SW: dict[str, str] = pms_to_sw_map()


def rgb_dist(a: Iterable[int], b: Iterable[int]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def nearest_sw(rgb: tuple[int, int, int]) -> dict:
    ranked = sorted(SW_COLORS.items(), key=lambda kv: rgb_dist(rgb, kv[1]))
    name, sw_rgb = ranked[0]
    code = name.split()[0] + " " + name.split()[1]
    result = {
        "sw_code": code,
        "sw_name": " ".join(name.split()[2:]),
        "sw_rgb": list(sw_rgb),
        "sw_hex": f"#{sw_rgb[0]:02x}{sw_rgb[1]:02x}{sw_rgb[2]:02x}",
        "delta_rgb": round(rgb_dist(rgb, sw_rgb), 1),
    }
    bm_ranked = sorted(BM_COLORS.items(), key=lambda kv: rgb_dist(rgb, kv[1]))
    if bm_ranked:
        bm_name, bm_rgb = bm_ranked[0]
        bm_delta = rgb_dist(rgb, bm_rgb)
        if bm_delta < result["delta_rgb"]:
            result["bm_code"] = bm_name
            result["bm_hex"] = f"#{bm_rgb[0]:02x}{bm_rgb[1]:02x}{bm_rgb[2]:02x}"
            result["bm_delta_rgb"] = round(bm_delta, 1)
    return result
