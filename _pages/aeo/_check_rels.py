#!/usr/bin/env python3
import re
import zipfile
from pathlib import Path

p = Path(r"c:\Users\EHuddleston\source\assistant-EHuddleston\_pages\aeo\_sp_current.xlsx")
with zipfile.ZipFile(p) as z:
    rels = z.read("xl/worksheets/_rels/sheet1.xml.rels").decode("utf-8")
    targets = re.findall(r'Target="([^"]+)"', rels)
    hubspot = [t for t in targets if "hubspot.com" in t]
    no_edit = [t for t in hubspot if not t.rstrip("/").endswith("/edit")]
    print(f"total hubspot targets: {len(hubspot)}")
    print(f"without /edit: {len(no_edit)}")
    for t in no_edit[:20]:
        print(" ", t)
    m = re.search(r'Id="rId2"[^>]*Target="([^"]+)"', rels)
    print("D5 rId2 target:", m.group(1) if m else "NOT FOUND")
