#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import load_dotenv, hubspot_request, pages_api, _find_page_by_slug
load_dotenv(ROOT)
api = pages_api('site-page')

for slug in ['about-us/contact-us', 'solutions/hvac', 'about-us/careers']:
    found = _find_page_by_slug(slug, 'site-page')
    page = hubspot_request('GET', f'{api}/{found["id"]}')
    print('---', slug)
    print('  template:', page.get('templatePath'))
    print('  layoutSections keys:', list((page.get('layoutSections') or {}).keys()))
    print('  top-level keys:', [k for k in page.keys() if k not in ('layoutSections',)])
    # check widgets
    for k in ['widgets', 'widgetContainers', 'body', 'pageExpiryEnabled']:
        if k in page:
            print(f'  {k}:', type(page[k]), str(page[k])[:100])
