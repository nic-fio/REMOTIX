#!/usr/bin/env python3
# ⭐ CORSIA D — le tabelle del rapporto, estratte dai verbali invece che
#    ricopiate a mano.
#
# ⛔ Non e' una comodita': i «numeri FOSSILI incollati nei commenti» sono una
#    voce del catalogo delle trappole gia' pagate.  Chi rilancia la campagna
#    rilancia questo e le tabelle si rifanno da sole.
#
# ⭐ E accanto a ogni numero ci sta la SCENA: motore, palco, gpu vista dalla
#    pagina, e se il giro era solo.  Un numero senza la sua scena non e' un
#    numero (`LEZIONI.md` §1.1 e §2.0).
#
# uso:  python3 banchi/03-ff-riassunto.py [cartella]
import glob
import json
import os
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/var/tmp/corsia-d"


def dist(v):
    v = sorted(x for x in v if isinstance(x, (int, float)))
    if not v:
        return None
    return {"n": len(v), "med": round(v[len(v) // 2], 2),
            "p95": round(v[min(len(v) - 1, int(0.95 * (len(v) - 1)))], 2)}


def palco_di(g):
    p = g.get("palco") or g.get("_palco") or {}
    q = g.get("_palco") or {}
    return {"gpu": p.get("gpu"), "headless": q.get("headless"),
            "motore": q.get("motore")}


def decodifica():
    print("\n" + "=" * 100)
    print("DECODIFICA — mediana del modo SERIALE (ms/fotogramma), un pezzo alla volta")
    print("=" * 100)
    righe = {}
    scene = {}
    for f in sorted(glob.glob(os.path.join(BASE, "03-ff-decodifica-*.json"))):
        d = json.load(open(f))
        etic = os.path.basename(f)[len("03-ff-decodifica-"):-len(".json")]
        for g in d["giri"]:
            if "esiti" not in g:
                continue
            scene[etic] = palco_di(g)["gpu"]
            for e in g["esiti"]:
                k = (e["etichetta"].split("—")[0].strip(), e["modo"])
                s = e.get("seriale") or {}
                r = e.get("raffica") or {}
                v = righe.setdefault(k, {}).setdefault(etic, {"ser": [], "raf": [],
                                                              "fps": [], "buchi": [],
                                                              "dich": set(), "forma": set()})
                dic = (e.get("dichiara") or {}).get("supported")
                v["dich"].add(dic)
                if dic is not True:
                    continue
                d2 = dist(s.get("latenze_ms") or [])
                if d2:
                    v["ser"].append(d2["med"])
                if r.get("ms_per_fotogramma"):
                    v["raf"].append(r["ms_per_fotogramma"])
                    v["fps"].append(r["fotogrammi_al_secondo"])
                v["buchi"].append("%s/%s" % (s.get("uscite"), s.get("entrate")))
                v["forma"].add((s.get("forma") or {}).get("format"))
    palchi = sorted(scene)
    print("\nle scene:")
    for p in palchi:
        print("   %-18s gpu vista dalla pagina: %s" % (p, scene[p]))
    print("\n%-14s %-16s %s" % ("flusso", "modo",
                                "".join("%-26s" % p for p in palchi)))
    for k in sorted(righe):
        celle = ""
        for p in palchi:
            v = righe[k].get(p)
            if not v:
                celle += "%-26s" % "—"
            elif True not in v["dich"]:
                celle += "%-26s" % "⛔ non dichiarato"
            else:
                celle += "%-26s" % ("%s ms · %s fo/s"
                                    % (v["ser"] or "—",
                                       [round(x) for x in v["fps"]] or "—"))
        print("%-14s %-16s %s" % (k[0][:14], k[1], celle))
    print("\n⚠ ogni cella e' l'elenco delle mediane dei giri (3 giri per caso).")
    print("⛔ i fotogrammi in uscita sono CONTATI: qui sotto i casi in cui non "
          "erano tutti.")
    for k in sorted(righe):
        for p in palchi:
            v = righe[k].get(p) or {}
            for b in v.get("buchi", []):
                if b and "/" in b and b.split("/")[0] != b.split("/")[1]:
                    print("   ⛔ %s %s su %s: usciti %s" % (k[0][:20], k[1], p, b))


def disegno():
    print("\n" + "=" * 100)
    print("DISEGNO — i due `drawImage` del prodotto, e i quadri di rAF")
    print("=" * 100)
    for f in sorted(glob.glob(os.path.join(BASE, "03-ff-disegno-*.json"))):
        d = json.load(open(f))
        etic = os.path.basename(f)[len("03-ff-disegno-"):-len(".json")]
        print("\n== %s" % etic)
        for i, g in enumerate(d["giri"]):
            if "palco" not in g:
                print("   giro %d ⛔ %s" % (i + 1, g.get("errore") or g.get("errore_pagina")))
                continue
            q = g.get("quadri") or {}
            n = g.get("disegno_come_il_prodotto") or {}
            fz = g.get("disegno_con_rilettura") or {}
            print("   giro %d  gpu: %s" % (i + 1, (g.get("palco") or {}).get("gpu")))
            print("      quadri rAF in 3 s: %s   (visibilita' %s)"
                  % (q.get("quadri"), q.get("visibilita")))
            for nome, r in (("come il prodotto", n), ("+ rilettura 1 px", fz)):
                dd = dist(r.get("disegno_ms") or [])
                cc = dist(r.get("decodifica_ms") or [])
                v = r.get("vernice") or {}
                print("      %-18s disegno %s · decodifica %s · pixel %s-%s%s%s"
                      % (nome, dd, cc, v.get("minimo"), v.get("massimo"),
                         "  ⛔ TELA UNIFORME" if v.get("uniforme") else "",
                         "  ⛔ usciti %s su %s" % (r.get("uscite"), r.get("entrate"))
                         if r.get("uscite") != r.get("entrate") else ""))


def solitudine():
    print("\n" + "=" * 100)
    print("⛔ ERO SOLO?  — la domanda che decide se i millisecondi valgono")
    print("=" * 100)
    for f in sorted(glob.glob(os.path.join(BASE, "03-ff-*.json"))):
        try:
            d = json.load(open(f))
        except (json.JSONDecodeError, OSError):
            continue
        if "prima" not in d:
            continue
        p = d["prima"]
        print("   %-34s prima: %s  %s" % (os.path.basename(f),
                                          "SOLO" if p.get("sono_solo") else "⛔ NO",
                                          "; ".join(p.get("perche") or [])[:110]))


if __name__ == "__main__":
    decodifica()
    disegno()
    solitudine()
