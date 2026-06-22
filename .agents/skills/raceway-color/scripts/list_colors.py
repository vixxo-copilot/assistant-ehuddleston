#!/usr/bin/env python3
"""Query the raceway color registry."""

from __future__ import annotations

import argparse
import json
import sys

from color_registry import list_by_system, list_by_tier, load_registry, lookup
from raceway_output import format_registry_markdown


def _field_paint_only(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("category") == "field_paint"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Query raceway / field paint registry")
    ap.add_argument("--code", help="Lookup by code (7100, SW 7100, PMS 482 C)")
    ap.add_argument("--tier", type=int, choices=[1, 2, 3], help="List field paint by tier")
    ap.add_argument("--system", choices=["sw", "bm", "pms", "custom"], help="List field paint system")
    ap.add_argument("--json", action="store_true", help="JSON output (default is markdown with swatches)")
    args = ap.parse_args()

    if args.code:
        payload = lookup(args.code)
    elif args.tier is not None:
        payload = _field_paint_only(list_by_tier(args.tier))
    elif args.system:
        payload = list_by_system(args.system)
    else:
        reg = load_registry()
        payload = {
            "version": reg.get("version"),
            "paint_product": reg.get("paint_product"),
            "raceway_rule": reg.get("raceway_rule"),
            "tier_labels": reg.get("tier_labels"),
        }

    if args.json:
        print(json.dumps(payload, indent=2))
    elif isinstance(payload, list) and payload and "code" in payload[0]:
        print(format_registry_markdown(payload))
    elif isinstance(payload, list):
        print(format_registry_markdown(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
