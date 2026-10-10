#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f005 — F-005 POINTER SHAPE (the C21 mesh inside the suite)

    python3 15-f005-forma-del-puntatore.py --container_box kde --browser chrome [--fault]
    python3 15-f005-forma-del-puntatore.py --certify

expected: in the session a real `firefox-esr` window (known page with a cyan
        background, yellow text box): the pointer the BROWSER wears is
          · the ARROW at the centre of the window,
          · the TEXT bar on the yellow box,
          · the HORIZONTAL resize arrow at one point of the
            scan of the right edge (from -4 to +8 px),
        each within 300 ms of the movement.
judgment: `C21.observe` + `C21.judge_browser` — IMPORTED: the image of the
        cursor (the canvas's `cursor` rule) classified by its PIXELS.

FAULT (C21's, `--wrong-shape`): the table of expectations shifted
        by one, on the SAME images ⇒ it must give red.  The red can come
        only from the classes, that is from the pixels of the real cursors.

OBSERVATION FOR THE USER (it is not a judgment): the «1 px dot» under the
        tip (the price of the shape on KDE and labwc, fasi/14 ~214).  With the
        pointer still at the centre of the window (all cyan) we look in the
        PHOTO of the canvas at a neighbourhood of the tip: the non-cyan pixels; then the
        pointer moves by 120 px and the same place is looked at again (does the dot
        go away?) and the new place (does the dot follow it?).  x12 enlargements
        in the evidence.  The `dot` field of the SUITE line tells it.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._load("g3", os.path.join(S.HERE, "15-g3-comune.py"))
C21 = S.C21                     # the mesh, already loaded by the suite: only one in memory
FUNCTIONS = ("F-005",)
EXPECTED = ("arrow at the centre, text bar on the text, horizontal arrow on the right "
          "edge (scan -4..+8 px), each within 300 ms of the movement")

# the dot: the neighbourhood of the tip, in PHOTO pixels, and the move
AROUND = 10
MOVE = 120


def certify():
    return C21.certify()


# ─────────────────────────────────────────────────────────────────────────────
#  the 1 px dot — an observation, not a judgment
# ─────────────────────────────────────────────────────────────────────────────
def _to_photo_pixel(geo, pw, ph, X, Y):
    return ((geo["bx0"] + X * geo["left_side"]) * pw / geo["bw"],
            (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])


def _not_cyan(im, cx, cy):
    """[(right, dy, rgb)] of the NON-cyan pixels around (cx, cy) in the photo."""
    outside = []
    for dy in range(-AROUND, AROUND + 1):
        for right in range(-AROUND, AROUND + 1):
            x, y = int(cx) + right, int(cy) + dy
            if 0 <= x < im.size[0] and 0 <= y < im.size[1]:
                p = im.getpixel((x, y))[:3]
                if not C21._near(p, C21.CYAN):
                    outside.append((right, dy, p))
    return outside


def _zoom_in(s, im, cx, cy, label_name):
    if not s.o.evidence:
        return ""
    r = AROUND + 6
    piece = im.crop((int(cx) - r, int(cy) - r, int(cx) + r + 1, int(cy) + r + 1))
    piece = piece.resize((piece.size[0] * 12, piece.size[1] * 12), 0)
    p = os.path.join(s.o.evidence, "dot-%s-%s.png" % (s.o.browser, label_name))
    piece.save(p)
    return p


def observe_dot(s, row):
    from PIL import Image
    try:
        mira = row["win"]["mira_desktop"]["center"]
    except (KeyError, TypeError):
        return {"seen_v": None, "said": "the window was not found: not looking"}
    geo = s.geometry()
    X, Y = mira
    out = {"evidence": []}

    def photo_with_pointer(Xp, Yp, label_name):
        vx, vy = C21.desktop_to_glass(geo, Xp, Yp)
        s.g.move_to(vx, vy)
        time.sleep(2.0)
        png, dove = s.picture("dot-" + label_name)
        if not png:
            return None
        if dove:
            out["evidence"].append(dove)
        return Image.open(io.BytesIO(png)).convert("RGB")

    a = photo_with_pointer(X, Y, "stopped")
    b = photo_with_pointer(X - MOVE, Y, "moved")
    if a is None or b is None:
        return {"seen_v": None, "said": "the canvas cannot be photographed"}
    pw, ph = a.size
    p1 = _to_photo_pixel(geo, pw, ph, X, Y)
    p2 = _to_photo_pixel(geo, pw, ph, X - MOVE, Y)
    a_p1, b_p1, b_p2 = _not_cyan(a, *p1), _not_cyan(b, *p1), _not_cyan(b, *p2)
    for im, (cx, cy), label_name in ((a, p1, "sotto-la-punta"), (b, p1, "posto-lasciato"),
                               (b, p2, "sotto-la-punta-spostata")):
        e = _zoom_in(s, im, cx, cy, label_name)
        if e:
            out["evidence"].append(e)
    # ⭐ and over the WHOLE cyan window: what changes between the two photos (the
    #   pointer moved, nothing else): where it is, relative to the tip
    diff = []
    try:
        cx0, cy0, cx1, cy1 = row["win"]["ciano_foto"]
        for y in range(cy0 + 4, cy1 - 4):
            for x in range(cx0 + 4, cx1 - 4):
                pa, pb = a.getpixel((x, y)), b.getpixel((x, y))
                if max(abs(pa[i] - pb[i]) for i in range(3)) > 40:
                    diff.append((x, y))
    except (KeyError, TypeError, ValueError):
        pass
    near = lambda q, c: abs(q[0] - c[0]) <= 24 and abs(q[1] - c[1]) <= 24   # noqa: E731
    out["differenze_fra_le_foto"] = len(diff)
    out["differenze_vicino_alle_punte"] = sum(1 for d in diff if near(d, p1) or near(d, p2))
    out["differenze_esempi"] = [[round(x - p1[0]), round(y - p1[1])] for x, y in diff[:8]]
    follows = bool(a_p1) and not b_p1 and bool(b_p2)
    out.update({
        "seen_v": follows,
        "sotto_la_punta": [[right, dy, list(p)] for right, dy, p in a_p1[:12]],
        "posto_lasciato": len(b_p1), "dopo_lo_spostamento": len(b_p2),
        "picture": [pw, ph], "punta_foto": [round(p1[0], 1), round(p1[1], 1)]})
    if follows:
        out["said"] = ("DOT SEEN: %d non-cyan px around the tip (%s), and it follows the "
                        "pointer moved by %d px — for the user to judge"
                        % (len(a_p1), ", ".join("%+d,%+d rgb%s" % (right, dy, p)
                                                for right, dy, p in a_p1[:4]), MOVE))
    elif not a_p1 and not b_p2:
        out["said"] = ("no dot: around the tip all cyan, still and moved; "
                        "between the two photos %d px of the window change (%d near the tips)"
                        % (len(diff), out["differenze_vicino_alle_punte"]))
    else:
        out["said"] = ("uncertain: %d non-cyan px under the tip, %d in the place left, %d "
                        "under the moved tip" % (len(a_p1), len(b_p1), len(b_p2)))
    return out


# ─────────────────────────────────────────────────────────────────────────────
def body_el(o, E):
    with S.Session(o, "005", E) as s:
        G3.prepare_o(o, s)
        oom0 = G3.killed_by_server()
        sign = s.log_mark()
        before = G3.evidence_now(o)
        with G3.lend_driver(S.REAL, s.g):
            row, oss = C21.observe(o.browser, o, s.sc, s.chi)
        server = s.log_from(sign) if sign is not None else []
        ev = G3.new_evidence(o, before) + [s.save_text("server-f005.txt", server),
                                             s.save_console()]
        if oss is None:
            s.picture("quando-non-si-guarda")
            raise S.Blocked(row.get("reason_text", "the mesh did not observe")
                             + G3.explain_blind(oom0))
        r = C21.judge_browser(dict(row), oss, False)
        steps = "; ".join(m for _p, _e, m in r["healthy"]["steps"])

        # the dot: after the judgment, with the same browser and the same window
        try:
            pt = observe_dot(s, row)
        except Exception as ex:                  # noqa: BLE001
            pt = {"seen_v": None, "said": "observation fell over: %r" % ex}
        print("   DOT: %s" % pt.get("said"), flush=True)
        E.put("F-005", r["outcome"], r["reason_text"], expected_val=EXPECTED, observed=steps,
                evidence=[e for e in ev if e] + pt.pop("evidence", []),
                dot=pt, win=row.get("win"))

        if o.fault:
            rg = C21.judge_browser(dict(row), oss, True)
            E.fault("F-005", G3.FAULT_FROM_OUTCOME[rg["outcome"]], rg["reason_text"],
                     expected_val="with the table of expectations shifted by one, the same "
                            "images give red",
                     observed="; ".join(m for _p, _e, m in rg.get("fault", {})
                                         .get("steps", [])))


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify, G3.arguments_g3))
