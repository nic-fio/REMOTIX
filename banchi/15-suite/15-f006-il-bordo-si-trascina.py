#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f006 — F-006 RESIZING FROM THE EDGE (the C22 mesh inside the suite)

    python3 15-f006-il-bordo-si-trascina.py --scatola lxqt --browser firefox [--guasto]
    python3 15-f006-il-bordo-si-trascina.py --certifica

expected: in the session a real `firefox-esr` window (C21's known
        page); with the left button pressed on the right edge and dragged by
        150 px, at one of the grip points from -2 to +6 px from the last cyan pixel,
        the right edge moves by at least 100 px and the left and the top
        stay still (±4 px): RESIZED, not moved.
judgment: `C22.prova_browser` (healthy) — IMPORTED: the window measured in the
        PHOTO of the canvas before and after each grip.

FAULT (C22's, `--senza-pulsante`): in the same session, after the
        healthy pass, the same gesture at the same points with the button UP
        (`C22.scansiona(..., premi=False)`) ⇒ the window must not change,
        and the test must give red.  The healthy control is the healthy pass
        just done (`C22.verdetto_col_guasto`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._carica("g3", os.path.join(S.QUI, "15-g3-comune.py"))
C22 = G3.carica_maglia("c22", "11-c22-il-bordo-si-trascina.py")
G3.traccia_la_ricerca(C22.C21)
FUNZIONI = ("F-006",)
ATTESO = ("dragging the right edge by %d px with the button pressed the right edge "
          "moves by at least %d px, the left and the top still (±%d px)"
          % (C22.SPINTA, C22.SOGLIA, C22.FERMO))


def certifica():
    return C22.certifica()


def corpo(o, E):
    o.senza_pulsante = False
    with S.Sessione(o, "006", E) as s:
        G3.prepara_o(o, s)
        oom0 = G3.uccisi_dal_server()
        segno = s.segno_registro()
        prima = G3.evidenze_ora(o)
        # ⚠ the mesh uses ITS OWN `12-client-veri` (C22 → C21 → C20V → VERI)
        with G3.guida_prestata(C22.VERI, s.g):
            riga = C22.prova_browser(o.browser, o, s.sc, s.chi)
        if riga.get("esito") == S.CIECO:
            s.foto("quando-non-si-guarda")        # what was on the canvas
            riga["perche"] = riga.get("perche", "") + G3.spiega_cieco(oom0)
        server = s.registro_da(segno) if segno is not None else []
        ev = G3.evidenze_nuove(o, prima) + [s.salva_testo("server-f006.txt", server),
                                             s.salva_console()]
        prese = "; ".join(m for _k, _e, m in riga.get("prese", []))
        E.metti("F-006", riga["esito"], riga.get("perche", ""), atteso=ATTESO,
                osservato=prese or riga.get("perche", ""), evidenze=[e for e in ev if e],
                finestra=riga.get("finestra"), presa_px=riga.get("presa_px"),
                spostamento_px=riga.get("spostamento_px"))

        if o.guasto:
            if "prese" not in riga:
                E.guasto("F-006", None, "the healthy pass did not drag anything (%s): the "
                         "fault cannot be injected" % riga.get("perche"))
                return
            sano = (riga["esito"], riga.get("perche", ""),
                    (riga["presa_px"], riga["spostamento_px"]) if "presa_px" in riga
                    else None)
            geo = s.geometria()
            prima = G3.evidenze_ora(o)
            print("   ── FAULT: the same gesture with the button UP ──", flush=True)
            senza = C22.scansiona(s.g, geo, o, o.browser + "-guasto", False)
            if senza[0] == S.CIECO:
                s.foto("guasto-quando-non-si-guarda")
                senza = (senza[0], senza[1] + G3.spiega_cieco(oom0)) + tuple(senza[2:])
            eg, mg = C22.verdetto_col_guasto(senza[:3], sano)
            E.guasto("F-006", G3.DA_ESITO_GUASTO[eg], mg,
                     atteso="with the button up no grip point resizes",
                     osservato="; ".join(r[2] for r in senza[3]),
                     evidenze=G3.evidenze_nuove(o, prima))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, G3.argomenti_g3))
