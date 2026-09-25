#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f006 — F-006 RIDIMENSIONARE DAL BORDO (la maglia C22 dentro la suite)

    python3 15-f006-il-bordo-si-trascina.py --scatola lxqt --browser firefox [--guasto]
    python3 15-f006-il-bordo-si-trascina.py --certifica

atteso: nella sessione una finestra vera di `firefox-esr` (la pagina nota di
        C21); col pulsante sinistro premuto sul bordo destro e trascinato di
        150 px, in uno dei punti di presa da -2 a +6 px dall'ultimo pixel ciano,
        il bordo destro si sposta di almeno 100 px e il sinistro e l'alto
        restano fermi (±4 px): RIDIMENSIONATA, non spostata.
giudizio: `C22.prova_browser` (sana) — IMPORTATA: la finestra misurata nella
        FOTOGRAFIA della tela prima e dopo ogni presa.

GUASTO (quello di C22, `--senza-pulsante`): nella stessa sessione, dopo la
        passata sana, lo stesso gesto negli stessi punti a pulsante ALZATO
        (`C22.scansiona(..., premi=False)`) ⇒ la finestra non deve cambiare,
        e la prova deve dare rosso.  Il controllo sano e' la passata sana
        appena fatta (`C22.verdetto_col_guasto`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._carica("g3", os.path.join(S.QUI, "15-g3-comune.py"))
C22 = G3.carica_maglia("c22", "11-c22-il-bordo-si-trascina.py")
G3.traccia_la_ricerca(C22.C21)
FUNZIONI = ("F-006",)
ATTESO = ("trascinando il bordo destro di %d px col pulsante premuto il bordo destro si "
          "sposta di almeno %d px, il sinistro e l'alto fermi (±%d px)"
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
        # ⚠ la maglia usa il SUO `12-client-veri` (C22 → C21 → C20V → VERI)
        with G3.guida_prestata(C22.VERI, s.g):
            riga = C22.prova_browser(o.browser, o, s.sc, s.chi)
        if riga.get("esito") == S.CIECO:
            s.foto("quando-non-si-guarda")        # che cosa c'era sulla tela
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
                E.guasto("F-006", None, "la passata sana non ha trascinato niente (%s): il "
                         "guasto non si puo' innestare" % riga.get("perche"))
                return
            sano = (riga["esito"], riga.get("perche", ""),
                    (riga["presa_px"], riga["spostamento_px"]) if "presa_px" in riga
                    else None)
            geo = s.geometria()
            prima = G3.evidenze_ora(o)
            print("   ── GUASTO: lo stesso gesto a pulsante ALZATO ──", flush=True)
            senza = C22.scansiona(s.g, geo, o, o.browser + "-guasto", False)
            if senza[0] == S.CIECO:
                s.foto("guasto-quando-non-si-guarda")
                senza = (senza[0], senza[1] + G3.spiega_cieco(oom0)) + tuple(senza[2:])
            eg, mg = C22.verdetto_col_guasto(senza[:3], sano)
            E.guasto("F-006", G3.DA_ESITO_GUASTO[eg], mg,
                     atteso="a pulsante alzato nessun punto di presa ridimensiona",
                     osservato="; ".join(r[2] for r in senza[3]),
                     evidenze=G3.evidenze_nuove(o, prima))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, G3.argomenti_g3))
