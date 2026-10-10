#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f006 — F-006 RESIZING FROM THE EDGE (the C22 mesh inside the suite)

    python3 15-f006-il-bordo-si-trascina.py --container_box lxqt --browser firefox [--fault]
    python3 15-f006-il-bordo-si-trascina.py --certify

expected: in the session a real `firefox-esr` window (C21's known
        page); with the left button pressed on the right edge and dragged by
        150 px, at one of the grip points from -2 to +6 px from the last cyan pixel,
        the right edge moves by at least 100 px and the left and the top
        stay still (±4 px): RESIZED, not moved.
judgment: `C22.test_browser` (healthy) — IMPORTED: the window measured in the
        PHOTO of the canvas before and after each grip.

FAULT (C22's, `--no-button`): in the same session, after the
        healthy pass, the same gesture at the same points with the button UP
        (`C22.scan_edge(..., press=False)`) ⇒ the window must not change,
        and the test must give red.  The healthy control is the healthy pass
        just done (`C22.verdict_with_fault`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._load("g3", os.path.join(S.HERE, "15-g3-comune.py"))
C22 = G3.load_mesh("c22", "11-c22-il-bordo-si-trascina.py")
G3.trace_search(C22.C21)
FUNCTIONS = ("F-006",)
EXPECTED = ("dragging the right edge by %d px with the button pressed the right edge "
          "moves by at least %d px, the left and the top still (±%d px)"
          % (C22.PUSH, C22.THRESHOLD, C22.STOPPED))


def certify():
    return C22.certify()


def body_el(o, E):
    o.no_button = False
    with S.Session(o, "006", E) as s:
        G3.prepare_o(o, s)
        oom0 = G3.killed_by_server()
        sign = s.log_mark()
        before = G3.evidence_now(o)
        # ⚠ the mesh uses ITS OWN `12-client-veri` (C22 → C21 → C20V → REAL)
        with G3.lend_driver(C22.REAL, s.g):
            row = C22.test_browser(o.browser, o, s.sc, s.chi)
        if row.get("outcome") == S.BLIND:
            s.picture("quando-non-si-guarda")        # what was on the canvas
            row["reason_text"] = row.get("reason_text", "") + G3.explain_blind(oom0)
        server = s.log_from(sign) if sign is not None else []
        ev = G3.new_evidence(o, before) + [s.save_text("server-f006.txt", server),
                                             s.save_console()]
        taken = "; ".join(m for _k, _e, m in row.get("taken", []))
        E.put("F-006", row["outcome"], row.get("reason_text", ""), expected_val=EXPECTED,
                observed=taken or row.get("reason_text", ""), evidence=[e for e in ev if e],
                win=row.get("win"), take_px=row.get("take_px"),
                displacement_px=row.get("displacement_px"))

        if o.fault:
            if "taken" not in row:
                E.fault("F-006", None, "the healthy pass did not drag anything (%s): the "
                         "fault cannot be injected" % row.get("reason_text"))
                return
            healthy = (row["outcome"], row.get("reason_text", ""),
                    (row["take_px"], row["displacement_px"]) if "take_px" in row
                    else None)
            geo = s.geometry()
            before = G3.evidence_now(o)
            print("   ── FAULT: the same gesture with the button UP ──", flush=True)
            without = C22.scan_edge(s.g, geo, o, o.browser + "-fault", False)
            if without[0] == S.BLIND:
                s.picture("guasto-quando-non-si-guarda")
                without = (without[0], without[1] + G3.explain_blind(oom0)) + tuple(without[2:])
            eg, mg = C22.verdict_with_fault(without[:3], healthy)
            E.fault("F-006", G3.FAULT_FROM_OUTCOME[eg], mg,
                     expected_val="with the button up no grip point resizes",
                     observed="; ".join(r[2] for r in without[3]),
                     evidence=G3.new_evidence(o, before))


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify, G3.arguments_g3))
