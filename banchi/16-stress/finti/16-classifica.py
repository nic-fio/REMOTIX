#!/usr/bin/env python3
"""FINTO di 16-classifica.py (stessa riga di comando: --livello-dir DIR …):
FINTO_CLASSE="4:FAIL,3:GREEN" sceglie la classe per numero di utenti
(livello.json); predefinito GREEN.  Stampa la riga del livello come --json."""
import argparse, json, os, sys
a = argparse.ArgumentParser()
a.add_argument("--livello-dir", required=True)
for k in ("--fps-video", "--finestra-s", "--campagna", "--livello"):
    a.add_argument(k)
a.add_argument("--json", action="store_true"); a.add_argument("--secco", action="store_true")
o = a.parse_args()
L = json.load(open(os.path.join(o.livello_dir, "livello.json")))
m = dict(x.split(":") for x in os.environ.get("FINTO_CLASSE", "").split(",") if ":" in x)
c = m.get(str(L["livello"]), "GREEN")
print("LIVELLO finto %s" % o.livello_dir)
print(json.dumps({"tipo": "livello", "classe": c, "significativo": c == "DEGRADED", "ragione": "finta"}))
print(json.dumps({"tipo": "sessione", "classe": "GREEN"}))
sys.exit({"GREEN": 0, "DEGRADED": 3, "FAIL": 1}[c])
