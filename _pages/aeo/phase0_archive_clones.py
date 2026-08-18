#!/usr/bin/env python3
"""Archive v1 AEO clone drafts with [DEPRECATED-AEO-v1] prefix (idempotent)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_JSON = ROOT / "_pages" / "aeo" / "_audit_results.json"
LOG = ROOT / "_pages" / "aeo" / "_phase0_archive_log.json"
DEPRECATED_PREFIX = "[DEPRECATED-AEO-v1]"

sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
os.environ.setdefault("HUBSPOT_PAGES_ALLOW_PRIVATE_APP_TOKEN", "true")

# Load .env if present
env_file = ROOT / ".env"
if env_file.is_file():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> int:
    from hubspot_pages import patch_page_name

    results = {"archived": 0, "skipped": 0, "failed": [], "items": []}
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    for item in audit.get("results", []):
        page_id = str(item.get("page_id") or "")
        name = str(item.get("name") or "")
        slug = str(item.get("slug") or "")
        if not page_id:
            results["failed"].append({"slug": slug, "error": "missing page_id"})
            continue
        if name.startswith(DEPRECATED_PREFIX):
            results["skipped"] += 1
            results["items"].append({"page_id": page_id, "slug": slug, "status": "already_deprecated"})
            continue
        new_name = f"{DEPRECATED_PREFIX} {name}"
        try:
            patch_page_name(page_id, new_name, "site-page")
            results["archived"] += 1
            results["items"].append({"page_id": page_id, "slug": slug, "status": "archived", "new_name": new_name})
        except Exception as exc:
            results["failed"].append({"page_id": page_id, "slug": slug, "error": str(exc)})

    LOG.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"archived": results["archived"], "skipped": results["skipped"], "failed": len(results["failed"])}, indent=2))
    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
