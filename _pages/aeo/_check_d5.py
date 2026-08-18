#!/usr/bin/env python3
import re
import zipfile
from pathlib import Path

fixed = Path(__file__).resolve().parent / "Vixxo-AEO-Website-Revamp-Status-fixed.xlsx"
with zipfile.ZipFile(fixed) as z:
    sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
match = re.search(r'<c r="D5"[^>]*>.*?</c>', sheet, re.S)
print(match.group(0)[:1000] if match else "NOT FOUND")
