#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g1b-explore — DIAGNOSIS TOOL of group G1b (it certifies nothing).

    python3 15-g1b-explore.py --box kde --browser chrome --evidence DIR \
        --steps 'foto:a;clic:100,2140;attendi:2;foto:b;tasti:Alt+Tab;dentro:comando'

Logs into a new session (tenant c15099u<n>), runs the steps, photographs.
Coordinates in DESKTOP pixels.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._load("g1b", os.path.join(S.HERE, "15-g1b-common.py"))


def extra(a):
    a.add_argument("--steps", default="foto:inizio")


def body(o, E):
    with S.Session(o, "099", E) as s:
        ok, m = s.enter()
        print("login:", ok, m, flush=True)
        if not ok:
            raise S.Blocked(m)
        time.sleep(4)
        geo = s.geometry()
        print("geo:", geo, flush=True)
        steps = o.steps
        if steps.startswith("b64:"):
            import base64
            steps = base64.b64decode(steps[4:]).decode()
        for p in steps.split(";"):
            kind, _, arg = p.partition(":")
            G1B.step("step %s" % p)
            if kind in ("photo", "foto1"):
                png, dove = G1B.photo(s, arg, scale_factor=0.5 if kind == "photo" else 1)
                print("photo", dove, flush=True)
            elif kind == "click":
                x, y = [float(v) for v in arg.split(",")]
                G1B.click_desktop(s, geo, x, y)
            elif kind == "destro":
                x, y = [float(v) for v in arg.split(",")]
                G1B.click_desktop(s, geo, x, y, button_code=2)
            elif kind == "move_to":
                x, y = [float(v) for v in arg.split(",")]
                vx, vy = S.C21.desktop_to_glass(geo, x, y)
                s.g.move_to(vx, vy)
            elif kind == "attendi":
                time.sleep(float(arg))
            elif kind == "keys":
                G1B.combination(s.g, arg.split("+"))
            elif kind == "orologio":
                print(G1B.put_window(s), G1B.open_window(s, "orologio", "#00ffff", 1100, 600,
                      other="#ffff00", period=int(arg or 30)), flush=True)
            elif kind == "size":
                png, dove = G1B.photo(s, "m", scale_factor=0.5)
                k = G1B.count_colors(png, (G1B.CYAN, (255, 255, 0)))
                st = s.pr.state() or {}
                print("measure", [round(v, 3) for v in k.values()],
                      {x: st.get(x) for x in ("painted", "delivered", "decoded")}, flush=True)
            elif kind == "js":
                print(s.g.js(arg), flush=True)
            elif kind == "inside":
                print(s.sc.inside(arg, 60), flush=True)
            elif kind == "sess":
                print(s.in_session(arg, 60, background=False), flush=True)
        E.put("F-099", S.PASS, "exploration")


if __name__ == "__main__":
    sys.exit(S.run(__doc__, ("F-099",), body, extra=extra))
