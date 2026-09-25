#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f026 — F-026 PIU' UTENTI INSIEME: ognuno vede la SUA sessione, e scrive solo nella sua

    python3 15-f026-piu-utenti-insieme.py --scatola xfce --browser chrome --porte-base 4920 [--guasto] [--inquilini 3]

Server normale della scatola (85xx).  N inquilini (2 di norma, fino a 3:
`c15026u<n>`), ognuno col SUO browser vero dello stesso tipo (porte-base,
+50, +54: finestre 4K insieme nel labwc), tutti dentro INSIEME.  Nella sessione
di ciascuno una scena `firefox-esr --kiosk` di un COLORE suo (rosso, verde,
magenta) con un campo di testo a fuoco; un piccolo servitore annota nella casa
dell'inquilino ogni tasto e ogni valore del campo.

L'ATTESO (SPECIFICHE §5.5 «ciascuno la propria sessione grafica remota,
indipendenti»):
  immagine  la tela di ciascun browser e' coperta dal SUO colore (>= 50 %) e non
            mostra quelli degli altri (<= 3 % ciascuno) — FOTOGRAFIA;
  input     una parola diversa per ciascuno, battuta con TASTI VERI nel suo
            browser, a turno: alla fine il campo della scena di ciascuno vale
            ESATTAMENTE la sua parola, e nessuno ha ricevuto tasti degli altri
            (valore del campo e quaderno dei tasti, nella sessione).

GUASTI (dopo la passata sana, stesse sessioni):
  immagine  la scena del secondo inquilino si ridipinge col colore del PRIMO (il
            file del colore cambia: e' la scena, non il giudice) ⇒ il giudice
            dell'immagine deve dire rosso;
  input     la parola del primo si batte nel browser del SECONDO (il gesto va
            all'inquilino sbagliato) ⇒ il giudice dell'input deve dire rosso.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g8", os.path.join(S.QUI, "15-g8-comune.py"))
FUNZIONI = ("F-026",)
COLORI = {"rosso": (220, 40, 40), "verde": (40, 190, 60), "magenta": (200, 40, 200)}
NOMI = ("rosso", "verde", "magenta")
PAROLE = ("alfa", "bravo", "xyz")        # lettere diverse: un tasto altrui si vede
SUO_MIN = 0.5
ALTRUI_MAX = 0.03


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def giudica_immagini(frazioni, nomi):
    """`frazioni[i]` = {colore: frazione} della tela dell'inquilino i."""
    guai = []
    for i, fr in enumerate(frazioni):
        if fr is None:
            return S.BLOCKED, "la tela dell'inquilino %d non si fotografa" % (i + 1)
        if fr.get(nomi[i], 0) < SUO_MIN:
            guai.append("%d: il SUO %s copre solo il %.1f%%" % (i + 1, nomi[i], 100 * fr.get(nomi[i], 0)))
        for j, n in enumerate(nomi):
            if j != i and fr.get(n, 0) > ALTRUI_MAX:
                guai.append("%d: mostra il %s dell'inquilino %d (%.1f%%)" % (
                    i + 1, n, j + 1, 100 * fr[n]))
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, " · ".join("%d vede %s %.0f%%" % (i + 1, nomi[i], 100 * fr[nomi[i]])
                              for i, fr in enumerate(frazioni))


def giudica_input(valori, tasti, parole):
    """`valori[i]` = valore finale del campo, `tasti[i]` = tasti ricevuti."""
    guai = []
    for i, v in enumerate(valori):
        if v is None:
            return S.BLOCKED, "il quaderno dell'inquilino %d non si legge" % (i + 1)
        if v != parole[i]:
            guai.append("%d: il campo vale «%s», atteso «%s»" % (i + 1, v, parole[i]))
        estranei = [k for k in tasti[i] if len(k) == 1 and k not in parole[i]]
        if estranei:
            guai.append("%d: ha ricevuto tasti altrui %s" % (i + 1, "".join(estranei)))
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, " · ".join("%d «%s»" % (i + 1, v) for i, v in enumerate(valori))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    n = NOMI[:2]
    buone = [{"rosso": 0.9, "verde": 0.0}, {"rosso": 0.0, "verde": 0.9}]
    prova("ognuno il suo ⇒ PASS", giudica_immagini(buone, n)[0] == S.PASS)
    prova("il secondo vede il rosso ⇒ FAIL", giudica_immagini(
        [buone[0], {"rosso": 0.9, "verde": 0.0}], n)[0] == S.FAIL)
    prova("mezzo e mezzo ⇒ FAIL", giudica_immagini(
        [buone[0], {"rosso": 0.2, "verde": 0.6}], n)[0] == S.FAIL)
    prova("foto mancante ⇒ BLOCKED", giudica_immagini([buone[0], None], n)[0] == S.BLOCKED)
    p = PAROLE[:2]
    prova("parole giuste ⇒ PASS", giudica_input(["alfa", "bravo"], [list("alfa"), list("bravo")], p)[0] == S.PASS)
    prova("parola nel posto sbagliato ⇒ FAIL", giudica_input(
        ["", "bravoalfa"], [[], list("bravoalfa")], p)[0] == S.FAIL)
    prova("tasto estraneo ⇒ FAIL", giudica_input(
        ["alfa", "bravo"], [list("alfa") + ["x"], list("bravo")], p)[0] == S.FAIL)
    # le frazioni su una foto sintetica
    from PIL import Image
    import io
    im = Image.new("RGB", (100, 50), COLORI["verde"])
    im.paste(COLORI["rosso"], (0, 0, 10, 50))
    b = io.BytesIO()
    im.save(b, "PNG")
    fr = G.frazioni(b.getvalue(), COLORI, riduci=1)
    prova("frazioni: verde 90%%, rosso 10%% (%s)" % G.fr_testo(fr),
          abs(fr["verde"] - 0.9) < 0.01 and abs(fr["rosso"] - 0.1) < 0.01 and fr["magenta"] == 0)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def extra(a):
    a.add_argument("--inquilini", type=int, default=2, choices=(2, 3))


def davanti(s):
    """(Niente da fare: vedi `browser_per` — la finestra Chrome e' sempre in cima.)"""
    return


def browser_per(o, i, n):
    """⛔ LA COLONNA CHROME: Chrome per l'ULTIMO inquilino, Firefox per gli altri.

    `[M]` 25 set 2026: sotto Wayland (labwc) una finestra Chrome COPERTA da
    un'altra non riceve piu' i «frame callback», non ridipinge, e la sua
    fotografia CDP (`Page.captureScreenshot`) aspetta PER SEMPRE — F-026 appesa
    15 minuti su gnome, xfce, lxqt; ne' `Page.bringToFront`, ne' le opzioni
    contro l'occlusione, ne' ridurre a icona le altre (un client Wayland non
    puo' tornare da solo dall'icona) bastano.  Firefox invece si fotografa anche
    coperto.  ⇒ Due utenti con due browser diversi (caso vero), Chrome creato
    per ULTIMO e quindi in cima.  Dichiarato nel rapporto."""
    o2 = G.o_per(o, i)
    if o.browser == "chrome":
        if i < n - 1:
            o2.browser = "firefox"
            o2.porte_base = o.porte_base + G.SPOSTA_BROWSER[i + 1]
        else:
            o2.porte_base = o.porte_base
    return o2


def fotografa_tutti(sess, nomi, etichetta):
    frs, ev = [], []
    for i, s in enumerate(sess):
        davanti(s)
        png, dove = s.foto("%s-%d-%s" % (etichetta, i + 1, nomi[i]))
        frs.append(G.frazioni(png, COLORI) if png else None)
        if dove:
            ev.append(dove)
    return frs, ev


def batti(s, parola):
    davanti(s)
    G.clic_centro(s)
    time.sleep(0.8)
    G.C23.manda(s.g, G.C23.scrivi(parola))


def leggi_tutti(sess):
    val, tas = [], []
    for s in sess:
        q = G.quaderno(s.sc, s.chi)
        val.append(G.valore(q))
        tas.append(G.tasti(q))
    return val, tas


def corpo(o, E):
    n = o.inquilini
    nomi, parole = NOMI[:n], PAROLE[:n]
    sess = []
    try:
        for i in range(n):
            s = S.Sessione(browser_per(o, i, n), "026", E)
            s.__enter__()
            sess.append(s)
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("l'inquilino %d (%s) non entra: %s" % (i + 1, s.chi, m))
            print("   ⭐ %d %s (%s) dentro: %s" % (i + 1, s.chi, s.o.browser, m[:70]), flush=True)
            davanti(s)
            S.C21.sveglia(s.g, s.geometria())
            ok, t = G.accendi_scena(s.sc, s.chi, o.porte_base + G.SPOSTA_SCENA + i,
                                    COLORI[nomi[i]])
            if not ok:
                raise S.Bloccata("la scena %s di %s non si accende: %s"
                                 % (nomi[i], s.chi, " | ".join(t.splitlines()[-6:])[-400:]))
        # tutti dentro, ognuno con la sua scena: si aspetta che ciascuna si veda
        for i, s in enumerate(sess):
            davanti(s)
            fr, _d, perche = G.aspetta_colore(s, "attesa-%d" % (i + 1), COLORI, nomi[i],
                                              SUO_MIN, 40)
            print("   tela %d: %s %s" % (i + 1, G.fr_testo(fr), perche), flush=True)
        # ── l'immagine ─────────────────────────────────────────────────────
        frs, ev = fotografa_tutti(sess, nomi, "immagine")
        ei, ri = giudica_immagini(frs, nomi)
        print("   immagine: %s — %s" % (ei, ri), flush=True)
        # ── l'input, a turno ───────────────────────────────────────────────
        for i, s in enumerate(sess):
            batti(s, parole[i])
            time.sleep(2.5)
        time.sleep(2)
        val, tas = leggi_tutti(sess)
        ein, rin = giudica_input(val, tas, parole)
        print("   input: %s — %s" % (ein, rin), flush=True)
        _f, ev2 = fotografa_tutti(sess, nomi, "dopo-input")
        chi = [s.chi for s in sess]
        righe = []
        for s in sess:
            righe += ["## %s" % s.chi] + [r for r in s.registro_da(0)
                                          if "sessione aperta" in r or "posto" in r][-6:]
        ev.append(sess[0].salva_testo("f026-server.txt", righe))
        tutti = [ei, ein]
        esito = S.FAIL if S.FAIL in tutti else (S.BLOCKED if S.BLOCKED in tutti else S.PASS)
        E.metti("F-026", esito, "immagine %s · input %s" % (ei, ein),
                atteso="%d inquilini insieme (%s): ciascuno vede il SUO colore e non gli altri; "
                       "la sua parola finisce SOLO nel suo campo" % (n, ", ".join(chi)),
                osservato="immagine: %s | input: %s" % (ri, rin), evidenze=ev + ev2)

        if o.guasto:
            # immagine: la scena del secondo prende il colore del primo
            G.cambia_colore(sess[1].sc, sess[1].chi, COLORI[nomi[0]])
            davanti(sess[1])
            G.aspetta_colore(sess[1], "guasto-attesa", COLORI, nomi[0], SUO_MIN, 20)
            frs, _e = fotografa_tutti(sess, nomi, "guasto-immagine")
            eg1, rg1 = giudica_immagini(frs, nomi)
            G.cambia_colore(sess[1].sc, sess[1].chi, COLORI[nomi[1]])
            # input: la parola del primo nel browser del secondo
            batti(sess[1], parole[0])
            time.sleep(3)
            val, tas = leggi_tutti(sess)
            eg2, rg2 = giudica_input(val, tas, parole)
            v1 = eg1 == S.FAIL if eg1 != S.BLOCKED else None
            v2 = eg2 == S.FAIL if eg2 != S.BLOCKED else None
            visto = None if None in (v1, v2) else (v1 and v2)
            E.guasto("F-026", visto, "scena del 2 col colore dell'1 ⇒ %s (%s) · parola dell'1 nel "
                     "browser del 2 ⇒ %s (%s)" % (eg1, rg1[:100], eg2, rg2[:100]))
    finally:
        for s in reversed(sess):
            try:
                s.__exit__(None, None, None)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ uscita di %s: %s" % (s.chi, e))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
