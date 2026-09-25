#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g1b-esplora — ATTREZZO DI DIAGNOSI del gruppo G1b (non certifica niente).

    python3 15-g1b-esplora.py --scatola kde --browser chrome --evidenze DIR \
        --passi 'foto:a;clic:100,2140;attendi:2;foto:b;tasti:Alt+Tab;dentro:comando'

Entra in una sessione nuova (inquilino c15099u<n>), esegue i passi, fotografa.
Coordinate in pixel del DESKTOP.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))


def extra(a):
    a.add_argument("--passi", default="foto:inizio")


def corpo(o, E):
    with S.Sessione(o, "099", E) as s:
        ok, m = s.entra()
        print("entra:", ok, m, flush=True)
        if not ok:
            raise S.Bloccata(m)
        time.sleep(4)
        geo = s.geometria()
        print("geo:", geo, flush=True)
        passi = o.passi
        if passi.startswith("b64:"):
            import base64
            passi = base64.b64decode(passi[4:]).decode()
        for p in passi.split(";"):
            tipo, _, arg = p.partition(":")
            G1B.passo("passo %s" % p)
            if tipo in ("foto", "foto1"):
                png, dove = G1B.foto(s, arg, scala=0.5 if tipo == "foto" else 1)
                print("foto", dove, flush=True)
            elif tipo == "clic":
                x, y = [float(v) for v in arg.split(",")]
                G1B.clic_desktop(s, geo, x, y)
            elif tipo == "destro":
                x, y = [float(v) for v in arg.split(",")]
                G1B.clic_desktop(s, geo, x, y, bottone=2)
            elif tipo == "muovi":
                x, y = [float(v) for v in arg.split(",")]
                vx, vy = S.C21.dal_desktop_al_vetro(geo, x, y)
                s.g.muovi(vx, vy)
            elif tipo == "attendi":
                time.sleep(float(arg))
            elif tipo == "tasti":
                G1B.combinazione(s.g, arg.split("+"))
            elif tipo == "orologio":
                print(G1B.metti_finestra(s), G1B.apri_finestra(s, "orologio", "#00ffff", 1100, 600,
                      altro="#ffff00", periodo=int(arg or 30)), flush=True)
            elif tipo == "misura":
                png, dove = G1B.foto(s, "m", scala=0.5)
                k = G1B.conta_colori(png, (G1B.CIANO, (255, 255, 0)))
                st = s.pr.stato() or {}
                print("misura", [round(v, 3) for v in k.values()],
                      {x: st.get(x) for x in ("dipinti", "consegnati", "decodificati")}, flush=True)
            elif tipo == "js":
                print(s.g.js(arg), flush=True)
            elif tipo == "dentro":
                print(s.sc.dentro(arg, 60), flush=True)
            elif tipo == "sess":
                print(s.nella_sessione(arg, 60, fondo=False), flush=True)
        E.metti("F-099", S.PASS, "esplorazione")


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, ("F-099",), corpo, extra=extra))
