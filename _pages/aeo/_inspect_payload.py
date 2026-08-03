#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
import aeo_revamp
print(aeo_revamp.__file__)
import inspect
print(inspect.getsource(aeo_revamp.build_stage_payload))
