#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f005 — F-005 POINTER SHAPE (the C21 mesh inside the suite)

    python3 15-f005-forma-del-puntatore.py --scatola kde --browser chrome [--guasto]
    python3 15-f005-forma-del-puntatore.py --certifica

expected: in the session a real `firefox-esr` window (known page with a cyan
        background, yellow text box): the pointer the BROWSER wears is
          · the ARROW at the centre of the window,
          · the TEXT bar on the yellow box,
          · the HORIZONTAL resize arrow at one point of the
            scan of the right edge (from -4 to +8 px),
        each within 300 ms of the movement.
judgment: `C21.osserva` + `C21.giudica_browser` — IMPORTED: the image of the
        cursor (the canvas's `cursor` rule) classified by its PIXELS.

FAULT (C21's, `--forma-sbagliata`): the table of expectations shifted
        by one, on the SAME images ⇒ it must give red.  The red can come
        only from the classes, that is from the pixels of the real cursors.

OBSERVATION FOR THE USER (it is not a judgment): the «1 px dot» under the
        tip (the price of the shape on KDE and labwc, fasi/14 ~214).  With the
        pointer still at the centre of the window (all cyan) we look in the
        PHOTO of the canvas at a neighbourhood of the tip: the non-cyan pixels; then the
        pointer moves by 120 px and the same place is looked at again (does the dot
        go away?) and the new place (does the dot follow it?).  x12 enlargements
        in the evidence.  The `puntino` field of the SUITE line tells it.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._carica("g3", os.path.join(S.QUI, "15-g3-comune.py"))
C21 = S.C21                     # the mesh, already loaded by the suite: only one in memory
FUNZIONI = ("F-005",)
ATTESO = ("arrow at the centre, text bar on the text, horizontal arrow on the right "
          "edge (scan -4..+8 px), each within 300 ms of the movement")

# the dot: the neighbourhood of the tip, in PHOTO pixels, and the move
INTORNO = 10
SPOSTA = 120


def certifica():
    return C21.certifica()


# ─────────────────────────────────────────────────────────────────────────────
#  the 1 px dot — an observation, not a judgment
# ─────────────────────────────────────────────────────────────────────────────
def _al_pixel_foto(geo, pw, ph, X, Y):
    return ((geo["bx0"] + X * geo["sx"]) * pw / geo["bw"],
            (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])


def _non_ciano(im, cx, cy):
    """[(dx, dy, rgb)] of the NON-cyan pixels around (cx, cy) in the photo."""
    fuori = []
    for dy in range(-INTORNO, INTORNO + 1):
        for dx in range(-INTORNO, INTORNO + 1):
            x, y = int(cx) + dx, int(cy) + dy
            if 0 <= x < im.size[0] and 0 <= y < im.size[1]:
                p = im.getpixel((x, y))[:3]
                if not C21._vicino(p, C21.CIANO):
                    fuori.append((dx, dy, p))
    return fuori


def _ingrandisci(s, im, cx, cy, nome):
    if not s.o.evidenze:
        return ""
    r = INTORNO + 6
    pezzo = im.crop((int(cx) - r, int(cy) - r, int(cx) + r + 1, int(cy) + r + 1))
    pezzo = pezzo.resize((pezzo.size[0] * 12, pezzo.size[1] * 12), 0)
    p = os.path.join(s.o.evidenze, "puntino-%s-%s.png" % (s.o.browser, nome))
    pezzo.save(p)
    return p


def osserva_puntino(s, riga):
    from PIL import Image
    try:
        mira = riga["finestra"]["mira_desktop"]["centro"]
    except (KeyError, TypeError):
        return {"visto": None, "detto": "the window was not found: not looking"}
    geo = s.geometria()
    X, Y = mira
    out = {"evidenze": []}

    def foto_con_puntatore(Xp, Yp, nome):
        vx, vy = C21.dal_desktop_al_vetro(geo, Xp, Yp)
        s.g.muovi(vx, vy)
        time.sleep(2.0)
        png, dove = s.foto("puntino-" + nome)
        if not png:
            return None
        if dove:
            out["evidenze"].append(dove)
        return Image.open(io.BytesIO(png)).convert("RGB")

    a = foto_con_puntatore(X, Y, "fermo")
    b = foto_con_puntatore(X - SPOSTA, Y, "spostato")
    if a is None or b is None:
        return {"visto": None, "detto": "the canvas cannot be photographed"}
    pw, ph = a.size
    p1 = _al_pixel_foto(geo, pw, ph, X, Y)
    p2 = _al_pixel_foto(geo, pw, ph, X - SPOSTA, Y)
    a_p1, b_p1, b_p2 = _non_ciano(a, *p1), _non_ciano(b, *p1), _non_ciano(b, *p2)
    for im, (cx, cy), nome in ((a, p1, "sotto-la-punta"), (b, p1, "posto-lasciato"),
                               (b, p2, "sotto-la-punta-spostata")):
        e = _ingrandisci(s, im, cx, cy, nome)
        if e:
            out["evidenze"].append(e)
    # ⭐ and over the WHOLE cyan window: what changes between the two photos (the
    #   pointer moved, nothing else): where it is, relative to the tip
    diff = []
    try:
        cx0, cy0, cx1, cy1 = riga["finestra"]["ciano_foto"]
        for y in range(cy0 + 4, cy1 - 4):
            for x in range(cx0 + 4, cx1 - 4):
                pa, pb = a.getpixel((x, y)), b.getpixel((x, y))
                if max(abs(pa[i] - pb[i]) for i in range(3)) > 40:
                    diff.append((x, y))
    except (KeyError, TypeError, ValueError):
        pass
    vicino = lambda q, c: abs(q[0] - c[0]) <= 24 and abs(q[1] - c[1]) <= 24   # noqa: E731
    out["differenze_fra_le_foto"] = len(diff)
    out["differenze_vicino_alle_punte"] = sum(1 for d in diff if vicino(d, p1) or vicino(d, p2))
    out["differenze_esempi"] = [[round(x - p1[0]), round(y - p1[1])] for x, y in diff[:8]]
    segue = bool(a_p1) and not b_p1 and bool(b_p2)
    out.update({
        "visto": segue,
        "sotto_la_punta": [[dx, dy, list(p)] for dx, dy, p in a_p1[:12]],
        "posto_lasciato": len(b_p1), "dopo_lo_spostamento": len(b_p2),
        "foto": [pw, ph], "punta_foto": [round(p1[0], 1), round(p1[1], 1)]})
    if segue:
        out["detto"] = ("DOT SEEN: %d non-cyan px around the tip (%s), and it follows the "
                        "pointer moved by %d px — for the user to judge"
                        % (len(a_p1), ", ".join("%+d,%+d rgb%s" % (dx, dy, p)
                                                for dx, dy, p in a_p1[:4]), SPOSTA))
    elif not a_p1 and not b_p2:
        out["detto"] = ("no dot: around the tip all cyan, still and moved; "
                        "between the two photos %d px of the window change (%d near the tips)"
                        % (len(diff), out["differenze_vicino_alle_punte"]))
    else:
        out["detto"] = ("uncertain: %d non-cyan px under the tip, %d in the place left, %d "
                        "under the moved tip" % (len(a_p1), len(b_p1), len(b_p2)))
    return out


# ─────────────────────────────────────────────────────────────────────────────
def corpo(o, E):
    with S.Sessione(o, "005", E) as s:
        G3.prepara_o(o, s)
        oom0 = G3.uccisi_dal_server()
        segno = s.segno_registro()
        prima = G3.evidenze_ora(o)
        with G3.guida_prestata(S.VERI, s.g):
            riga, oss = C21.osserva(o.browser, o, s.sc, s.chi)
        server = s.registro_da(segno) if segno is not None else []
        ev = G3.evidenze_nuove(o, prima) + [s.salva_testo("server-f005.txt", server),
                                             s.salva_console()]
        if oss is None:
            s.foto("quando-non-si-guarda")
            raise S.Bloccata(riga.get("perche", "the mesh did not observe")
                             + G3.spiega_cieco(oom0))
        r = C21.giudica_browser(dict(riga), oss, False)
        passi = "; ".join(m for _p, _e, m in r["sano"]["passi"])

        # the dot: after the judgment, with the same browser and the same window
        try:
            pt = osserva_puntino(s, riga)
        except Exception as ex:                  # noqa: BLE001
            pt = {"visto": None, "detto": "observation fell over: %r" % ex}
        print("   DOT: %s" % pt.get("detto"), flush=True)
        E.metti("F-005", r["esito"], r["perche"], atteso=ATTESO, osservato=passi,
                evidenze=[e for e in ev if e] + pt.pop("evidenze", []),
                puntino=pt, finestra=riga.get("finestra"))

        if o.guasto:
            rg = C21.giudica_browser(dict(riga), oss, True)
            E.guasto("F-005", G3.DA_ESITO_GUASTO[rg["esito"]], rg["perche"],
                     atteso="with the table of expectations shifted by one, the same "
                            "images give red",
                     osservato="; ".join(m for _p, _e, m in rg.get("guasto", {})
                                         .get("passi", [])))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, G3.argomenti_g3))
