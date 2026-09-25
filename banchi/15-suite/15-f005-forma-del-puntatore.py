#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f005 — F-005 FORMA DEL PUNTATORE (la maglia C21 dentro la suite)

    python3 15-f005-forma-del-puntatore.py --scatola kde --browser chrome [--guasto]
    python3 15-f005-forma-del-puntatore.py --certifica

atteso: nella sessione una finestra vera di `firefox-esr` (pagina nota a fondo
        ciano, riquadro giallo di testo): il puntatore che il BROWSER indossa e'
          · la FRECCIA al centro della finestra,
          · la barra del TESTO sul riquadro giallo,
          · la freccia ORIZZONTALE di ridimensionamento in un punto della
            scansione del bordo destro (da -4 a +8 px),
        ciascuna entro 300 ms dal movimento.
giudizio: `C21.osserva` + `C21.giudica_browser` — IMPORTATI: l'immagine del
        cursore (la regola `cursor` della tela) classificata dai suoi PIXEL.

GUASTO (quello di C21, `--forma-sbagliata`): la tabella delle attese spostata
        di uno, sulle STESSE immagini ⇒ deve dare rosso.  Il rosso puo' venire
        solo dalle classi, cioe' dai pixel dei cursori veri.

OSSERVAZIONE PER L'UTENTE (non e' un giudizio): il «puntino di 1 px» sotto la
        punta (il prezzo della forma su KDE e labwc, fasi/14 ~214).  Col
        puntatore fermo al centro della finestra (tutto ciano) si guarda nella
        FOTO della tela un intorno della punta: i pixel non ciano; poi il
        puntatore si sposta di 120 px e si riguarda lo stesso posto (il puntino
        se ne va?) e il posto nuovo (il puntino lo segue?).  Ingrandimenti x12
        nelle evidenze.  Il campo `puntino` della riga SUITE lo racconta.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._carica("g3", os.path.join(S.QUI, "15-g3-comune.py"))
C21 = S.C21                     # la maglia, gia' caricata dalla suite: una sola in memoria
FUNZIONI = ("F-005",)
ATTESO = ("freccia al centro, barra del testo sul testo, freccia orizzontale sul bordo "
          "destro (scansione -4..+8 px), ciascuna entro 300 ms dal movimento")

# il puntino: l'intorno della punta, in pixel della FOTO, e lo spostamento
INTORNO = 10
SPOSTA = 120


def certifica():
    return C21.certifica()


# ─────────────────────────────────────────────────────────────────────────────
#  il puntino di 1 px — un'osservazione, non un giudizio
# ─────────────────────────────────────────────────────────────────────────────
def _al_pixel_foto(geo, pw, ph, X, Y):
    return ((geo["bx0"] + X * geo["sx"]) * pw / geo["bw"],
            (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])


def _non_ciano(im, cx, cy):
    """[(dx, dy, rgb)] dei pixel NON ciano attorno a (cx, cy) nella foto."""
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
        return {"visto": None, "detto": "la finestra non e' stata trovata: non si guarda"}
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
        return {"visto": None, "detto": "la tela non si fotografa"}
    pw, ph = a.size
    p1 = _al_pixel_foto(geo, pw, ph, X, Y)
    p2 = _al_pixel_foto(geo, pw, ph, X - SPOSTA, Y)
    a_p1, b_p1, b_p2 = _non_ciano(a, *p1), _non_ciano(b, *p1), _non_ciano(b, *p2)
    for im, (cx, cy), nome in ((a, p1, "sotto-la-punta"), (b, p1, "posto-lasciato"),
                               (b, p2, "sotto-la-punta-spostata")):
        e = _ingrandisci(s, im, cx, cy, nome)
        if e:
            out["evidenze"].append(e)
    # ⭐ e su TUTTA la finestra ciano: che cosa cambia fra le due foto (il
    #   puntatore si e' spostato, nient'altro): dove sta, rispetto alla punta
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
        out["detto"] = ("PUNTINO VISTO: %d px non ciano attorno alla punta (%s), e segue il "
                        "puntatore spostato di %d px — da giudicare dall'utente"
                        % (len(a_p1), ", ".join("%+d,%+d rgb%s" % (dx, dy, p)
                                                for dx, dy, p in a_p1[:4]), SPOSTA))
    elif not a_p1 and not b_p2:
        out["detto"] = ("nessun puntino: attorno alla punta tutto ciano, fermo e spostato; "
                        "fra le due foto cambiano %d px della finestra (%d vicino alle punte)"
                        % (len(diff), out["differenze_vicino_alle_punte"]))
    else:
        out["detto"] = ("incerto: %d px non ciano sotto la punta, %d nel posto lasciato, %d "
                        "sotto la punta spostata" % (len(a_p1), len(b_p1), len(b_p2)))
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
            raise S.Bloccata(riga.get("perche", "la maglia non ha osservato")
                             + G3.spiega_cieco(oom0))
        r = C21.giudica_browser(dict(riga), oss, False)
        passi = "; ".join(m for _p, _e, m in r["sano"]["passi"])

        # il puntino: dopo il giudizio, con lo stesso browser e la stessa finestra
        try:
            pt = osserva_puntino(s, riga)
        except Exception as ex:                  # noqa: BLE001
            pt = {"visto": None, "detto": "osservazione caduta: %r" % ex}
        print("   PUNTINO: %s" % pt.get("detto"), flush=True)
        E.metti("F-005", r["esito"], r["perche"], atteso=ATTESO, osservato=passi,
                evidenze=[e for e in ev if e] + pt.pop("evidenze", []),
                puntino=pt, finestra=riga.get("finestra"))

        if o.guasto:
            rg = C21.giudica_browser(dict(riga), oss, True)
            E.guasto("F-005", G3.DA_ESITO_GUASTO[rg["esito"]], rg["perche"],
                     atteso="con la tabella delle attese spostata di uno, le stesse "
                            "immagini danno rosso",
                     osservato="; ".join(m for _p, _e, m in rg.get("guasto", {})
                                         .get("passi", [])))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, G3.argomenti_g3))
