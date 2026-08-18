#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import load_dotenv, hubspot_request, pages_api, _find_page_by_slug
load_dotenv(ROOT)
api = pages_api('site-page')
live = _find_page_by_slug('about-us/contact-us', 'site-page')
page = hubspot_request('GET', f'{api}/{live["id"]}')
ls = page.get('layoutSections')
print('live id', live['id'])
print('layoutSections is None?', ls is None)
print('layoutSections type', type(ls))
if isinstance(ls, dict):
    print('keys', list(ls.keys()))
    print('json size', len(json.dumps(ls)))
else:
    print('value', ls)
