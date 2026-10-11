#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f006 — F-006 RESIZING FROM THE EDGE (the C22 mesh inside the suite)

    python3 15-f006-the-edge-drags.py --box lxqt --browser firefox [--fault]
    python3 15-f006-the-edge-drags.py --certify

expected: in the session a real `firefox-esr` window (C21's known
        page); with the left button pressed on the right edge and dragged by
        150 px, at one of the grip points from -2 to +6 px from the last cyan pixel,
        the right edge moves by at least 100 px and the left and the top
        stay still (±4 px): RESIZED, not moved.
judgment: `C22.test_browser` (healthy) — IMPORTED: the window measured in the
        PHOTO of the canvas before and after each grip.

FAULT (C22's, `--no-button`): in the same session, after the
        healthy pass, the same gesture at the same points with the button UP
        (`C22.scansiona(..., premi=False)`) ⇒ the window must not change,
        and the test must give red.  The healthy control is the healthy pass
        just done (`C22.verdetto_col_guasto`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._load("g3", os.path.join(S.HERE, "15-g3-common.py"))
C22 = G3.load_mesh("c22", "11-c22-the-edge-drags.py")
G3.trace_search(C22.C21)
FUNCTIONS = ("F-006",)
ATTESO = ("dragging the right edge by %d px with the button pressed the right edge "
          "moves by at least %d px, the left and the top still (±%d px)"
          % (C22.PUSH, C22.THRESHOLD, C22.STOPPED))


def certify():
    return C22.certify()


def body(o, E):
    o.no_button = False
    with S.Session(o, "006", E) as s:
        G3.prepare_o(o, s)
        oom0 = G3.killed_by_server()
        sign = s.log_mark()
        before = G3.evidence_now(o)
        # ⚠ the mesh uses ITS OWN `12-real-clients` (C22 → C21 → C20V → VERI)
        with G3.borrowed_driver(C22.VERI, s.g):
            line = C22.test_browser(o.browser, o, s.sc, s.chi)
        if line.get("outcome") == S.BLIND:
            s.photo("quando-non-si-guarda")        # what was on the canvas
            line["why"] = line.get("why", "") + G3.explain_blind(oom0)
        server = s.log_from(sign) if sign is not None else []
        ev = G3.new_evidence(o, before) + [s.save_text("server-f006.txt", server),
                                             s.save_console()]
        prese = "; ".join(m for _k, _e, m in line.get("prese", []))
        E.put("F-006", line["outcome"], line.get("why", ""), expected=ATTESO,
                observed=prese or line.get("why", ""), evidence=[e for e in ev if e],
                window=line.get("window"), presa_px=line.get("presa_px"),
                spostamento_px=line.get("spostamento_px"))

        if o.fault:
            if "prese" not in line:
                E.fault("F-006", None, "the healthy pass did not drag anything (%s): the "
                         "fault cannot be injected" % line.get("why"))
                return
            healthy = (line["outcome"], line.get("why", ""),
                    (line["presa_px"], line["spostamento_px"]) if "presa_px" in line
                    else None)
            geo = s.geometry()
            before = G3.evidence_now(o)
            print("   ── FAULT: the same gesture with the button UP ──", flush=True)
            without = C22.scan_edge(s.g, geo, o, o.browser + "-guasto", False)
            if without[0] == S.BLIND:
                s.photo("guasto-quando-non-si-guarda")
                without = (without[0], without[1] + G3.explain_blind(oom0)) + tuple(without[2:])
            eg, mg = C22.verdict_with_fault(without[:3], healthy)
            E.fault("F-006", G3.FAULT_FROM_OUTCOME[eg], mg,
                     expected="with the button up no grip point resizes",
                     observed="; ".join(r[2] for r in without[3]),
                     evidence=G3.new_evidence(o, before))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, G3.arguments_g3))
