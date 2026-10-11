#!/usr/bin/env python3
"""FAKE of 16-classify.py (same command line: --level-dir DIR …):
FAKE_CLASS="4:FAIL,3:GREEN" picks the class by number of users
(level.json); default GREEN.  Prints the level row like --json."""
import argparse, json, os, sys
a = argparse.ArgumentParser()
a.add_argument("--level-dir", required=True)
for k in ("--fps-video", "--window-s", "--campaign", "--level"):
    a.add_argument(k)
a.add_argument("--json", action="store_true"); a.add_argument("--dry-run", action="store_true")
o = a.parse_args()
L = json.load(open(os.path.join(o.level_dir, "level.json")))
m = dict(x.split(":") for x in os.environ.get("FAKE_CLASS", "").split(",") if ":" in x)
c = m.get(str(L["level"]), "GREEN")
print("fake LEVEL %s" % o.level_dir)
print(json.dumps({"type": "level", "class": c, "significant": c == "DEGRADED", "rationale": "fake"}))
print(json.dumps({"type": "session", "class": "GREEN"}))
sys.exit({"GREEN": 0, "DEGRADED": 3, "FAIL": 1}[c])
