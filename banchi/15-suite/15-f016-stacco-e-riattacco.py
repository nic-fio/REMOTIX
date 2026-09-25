#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f016 — F-016 STACCO · F-017 RIATTACCO ALLA STESSA MISURA · percorsi P-A e P-F

    python3 15-f016-stacco-e-riattacco.py --scatola kde --browser chrome [--guasto]

La scena (15-g6-comune): nella sessione un firefox-esr con fondo ciano, un
campo di testo e la STRISCIA che mostra a colori quel che vi si scrive; il
programma annota ogni 2 s il suo stato (gettone, valore, schermo) in un file.

  P-A/P-F  creazione → desktop → applicazione aperta → INPUT VERO (clic sulla
           scena e lettere scritte dal browser) → STACCO (il browser si chiude,
           col suo congedo) → ATTESA 35 s (oltre l'orologio del silenzio, §5.3)
           → RIATTACCO (browser nuovo, stesso utente e parola) → STATO → INPUT.

F-016  atteso: dopo lo stacco e l'attesa la sessione resta e i programmi restano.
       campi: il PID di firefox-esr della scena e quello del compositore sono
       gli STESSI di prima; la sessione di logind c'e'; la scena continua a
       battere (righe nuove nel quaderno DOPO l'attesa, con lo STESSO gettone e
       lo stesso testo); il registro del server non dice che la sessione muore.
F-017  atteso: rientrando ⇒ ammesso, e lo STATO si ritrova — dalla FOTO: la
       finestra ciano c'e' e la striscia legge il testo scritto prima; dal
       CAMPO: stesso gettone (la pagina non e' rinata), stesso valore.
       ⚠ La frase della pagina («Ammesso, sessione nuova|ripresa») si guarda:
       `RCP.md` §4 (`SESSIONE`, stato 1 = NUOVA, 2 = RIPRESA).
P-A    atteso: anche l'input DOPO il riattacco arriva (lettere nuove lette in foto).
P-F    atteso: F-016 e F-017 insieme (applicazione aperta, attesa, stato).

GUASTO (vero, nella scena): si stacca di nuovo e durante lo stacco si UCCIDE il
       programma della scena (kill -9 di firefox-esr dell'inquilino) — cioe'
       «i programmi non restano».  Le stesse prove devono dare ROSSO: F-016
       (PID sparito, battiti fermi), F-017 (niente finestra ne' testo), P-A, P-F.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g6", os.path.join(S.QUI, "15-g6-comune.py"))
FUNZIONI = ("F-016", "F-017", "P-A", "P-F")
ATTESA_S = 35          # oltre i 30 s del silenzio (§5.3): la sessione deve restare
# ⛔ le righe del registro che vorrebbero dire «la sessione e' morta col client»
MORTE = ("nascera' una NUOVA", "sessione grafica e' finita", "SESSIONE_TERMINATA",
         "la sessione e' morta")


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI (puri)
# ═══════════════════════════════════════════════════════════════════════════
def giudica_stacco(prima, dopo, q_dopo, t_fine_attesa_ms, testo, registro):
    """F-016.  prima/dopo: {nome: [pid]} (G.processi); q_dopo: quaderno;
    torna (esito, ragione)."""
    probl = []
    pf0, pf1 = G.pid_scena(prima), G.pid_scena(dopo)
    if pf0 is None:
        return S.BLOCKED, "prima dello stacco la scena non c'era: niente da confrontare"
    if pf1 != pf0:
        probl.append("il programma della scena (firefox-esr %s) dopo lo stacco %s"
                     % (pf0, "NON C'E' PIU'" if pf1 is None else "e' un ALTRO (%s)" % pf1))
    for comp in ("gnome-shell", "kwin_wayland", "labwc"):
        if prima.get(comp):
            if sorted(prima[comp]) != sorted(dopo.get(comp) or []):
                probl.append("il compositore %s era %s, dopo %s"
                             % (comp, prima[comp], dopo.get(comp)))
    if prima.get("sessione") and not dopo.get("sessione"):
        probl.append("la sessione di logind %s non c'e' piu'" % prima["sessione"])
    battiti = [r for r in q_dopo if r.get("t", 0) >= t_fine_attesa_ms]
    g0 = None
    for r in q_dopo:
        if r.get("t", 0) < t_fine_attesa_ms and r.get("v") == testo:
            g0 = r.get("g")
    if not battiti:
        probl.append("la scena non batte piu' dopo l'attesa (nessuna riga nuova nel quaderno)")
    elif g0 and any(r.get("g") != g0 for r in battiti):
        probl.append("la scena ha un gettone NUOVO: la pagina e' rinata")
    elif battiti[-1].get("v") != testo:
        probl.append("il testo della scena e' «%s», non «%s»" % (battiti[-1].get("v"), testo))
    morte = [r for r in registro if any(m in r for m in MORTE)]
    vive = [r for r in registro if "(I4)" in r or "invariante I4" in r]
    if not vive:
        probl.append("il registro del server (%d righe dallo stacco) non dice che il palco "
                     "resta (nessuna riga «I4»)" % len(registro))
    if morte:
        probl.append("il registro del server dice che la sessione finisce: «%s»" % morte[0][-200:])
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, ("registro: «%s» · dopo %d s staccato: firefox-esr %s e compositore vivi, stessi PID; "
                    "sessione %s; la scena batte ancora (%d righe dopo l'attesa, stesso "
                    "gettone, testo «%s»)" % (vive[0].split("] ", 1)[-1][:90], ATTESA_S, pf0, (dopo.get("sessione") or ["?"])[0],
                                              len(battiti), testo))


def giudica_ritrovo(testo, vista, stato_dopo, gettone_prima):
    """F-017 (lo stato).  vista: G.guarda_la_scena; stato_dopo: ultima riga del
    quaderno.  Torna (esito, ragione)."""
    probl = []
    cieco = vista.get("png") is None and "finestra" in vista and vista.get("foto") is not None
    if cieco:
        pass                     # la foto non si e' potuta fare: decidono i campi, o BLOCKED
    elif not vista.get("finestra"):
        probl.append("nella foto la finestra della scena NON c'e' (%s)" % vista.get("perche"))
    elif vista.get("letto") != testo:
        probl.append("nella foto la striscia dice «%s» (crudo %s), scritto prima «%s»"
                     % (vista.get("letto"), vista.get("crudo"), testo))
    if not stato_dopo:
        probl.append("la scena non scrive piu' il suo stato")
    else:
        if gettone_prima and stato_dopo.get("g") != gettone_prima:
            probl.append("il gettone della scena e' cambiato (%s → %s): e' rinata"
                         % (gettone_prima, stato_dopo.get("g")))
        if stato_dopo.get("v") != testo:
            probl.append("il campo della scena vale «%s», non «%s»" % (stato_dopo.get("v"), testo))
    if probl:
        return S.FAIL, "; ".join(probl) + (" (la foto non si e' potuta fare: %s)"
                                           % vista.get("perche") if cieco else "")
    if cieco:
        return S.BLOCKED, "i campi tornano, ma la foto non si e' potuta fare: %s" % vista.get("perche")
    return S.PASS, ("ritrovato: finestra in foto, striscia «%s», gettone %s invariato"
                    % (testo, gettone_prima))


def giudica_frase(esito):
    """La frase che l'utente legge al riattacco (RCP §4: 2 = RIPRESA)."""
    e = esito or ""
    if "sessione ripresa" in e:
        return True, "la pagina dice «%s»" % e
    return False, ("la pagina dice «%s» a una sessione RIPRESA (RCP.md §4: stato 2 = "
                   "RIPRESA; src/rcp.c manda sempre 1 = NUOVA)" % e)


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    pr = {"firefox-esr": ["100", "120"], "labwc": ["90"], "sessione": ["c7"]}
    q = [{"g": "x", "v": "abc", "t": 1000}, {"g": "x", "v": "abc", "t": 5000}]
    I4 = ["x figlio [u] il palco resta in piedi (I4)"]
    e, m = giudica_stacco(pr, pr, q, 3000, "abc", I4)
    prova("stacco sano ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_stacco(pr, pr, q, 3000, "abc", [])
    prova("registro senza I4 ⇒ FAIL", e == S.FAIL)
    e, m = giudica_stacco(pr, {"labwc": ["90"], "sessione": ["c7"]}, q[:1], 3000, "abc", I4)
    prova("programma ucciso ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = giudica_stacco(pr, pr, q + [{"g": "y", "v": "", "t": 6000}], 3000, "abc", I4)
    prova("pagina rinata ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_stacco(pr, pr, q, 3000, "abc", I4 + ["... nascera' una NUOVA"])
    prova("registro di morte ⇒ FAIL", e == S.FAIL)
    # la foto: una scena sintetica con «abc» nella striscia
    png = scena_finta("abc")
    v = G.guarda_la_scena(_Finta(png), "x")
    prova("foto finta: striscia letta «%s»" % v.get("letto"), v.get("letto") == "abc")
    e, _ = giudica_ritrovo("abc", v, {"g": "x", "v": "abc"}, "x")
    prova("ritrovo sano ⇒ PASS", e == S.PASS)
    v2 = G.guarda_la_scena(_Finta(scena_finta(None)), "x")
    e, _ = giudica_ritrovo("abc", v2, None, "x")
    prova("senza finestra ⇒ FAIL", e == S.FAIL)
    v3 = {"finestra": None, "letto": None, "foto": "", "perche": "timed out", "png": None}
    e, _ = giudica_ritrovo("abc", v3, {"g": "x", "v": "abc"}, "x")
    prova("foto fallita, campi buoni ⇒ BLOCKED", e == S.BLOCKED)
    prova("frase «nuova» ⇒ no", not giudica_frase("Ammesso, sessione nuova, tela")[0])
    return 0 if ok else 1


def scena_finta(testo, w=1920, h=1080):
    """Un desktop grigio scuro con la finestra della scena (per --certifica)."""
    import io
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (40, 40, 60))
    d = ImageDraw.Draw(im)
    if testo is not None:
        x0, y0, x1, y1 = 100, 120, 1300, 900
        d.rectangle([x0, y0, x1, y1], fill=G.CIANO)
        W, H = x1 - x0 + 1, y1 - y0 + 1
        passo = (G.STR_X1 - G.STR_X0) / G.CASELLE
        for i in range(G.CASELLE):
            c = G.TAVOLOZZA[testo[i]] if i < len(testo) else G.VUOTO
            a = x0 + W * (G.STR_X0 + i * passo)
            b = a + W * passo - W * 0.014
            d.rectangle([a, y0 + H * G.STR_Y0, b, y0 + H * G.STR_Y1], fill=c)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


class _Finta:
    """Una Sessione finta che «fotografa» un png dato."""
    def __init__(self, png):
        self.png = png

    def foto(self, nome):
        return self.png, ""


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def testo_a_caso(n):
    """Lettere DIVERSE fra loro: una striscia «bbbb» direbbe poco sull'ordine."""
    return "".join(random.sample(G.ALFABETO, n))


def trova_scena(s, tetto=30.0):
    fine = time.time() + tetto
    v = {}
    while time.time() < fine:
        v = G.guarda_la_scena(s, "scena")
        if v.get("finestra"):
            return v
        time.sleep(2)
    return v


def un_giro(o, E, s, testo, passata, guasto=False):
    """Stacco → attesa → riattacco → stato → input.  Mette F-016, F-017, P-A, P-F."""
    metti = (lambda f, e, r, **k: E.guasto(f, e == S.FAIL, "guasto (scena uccisa): " + r, **k)) \
        if guasto else (lambda f, e, r, **k: E.metti(f, e, r, passata=passata, **k))
    q0 = G.quaderno(s)
    gettone = next((r.get("g") for r in reversed(q0) if r.get("v") == testo), None)
    prima = G.processi(s)
    segno = s.segno_registro()
    print("   prima dello stacco: %s · gettone %s" % (prima, gettone), flush=True)
    # ── STACCO: il browser si chiude (la guida naviga ad about:blank ⇒ congedo, poi esce)
    s.spegni_browser()
    t_stacco = time.time()
    if guasto:
        c, t = s.sc.dentro("pkill -KILL -u %s -x firefox-esr; sleep 1; pgrep -u %s -x "
                           "firefox-esr || echo uccisa" % (s.chi, s.chi), 30)
        print("   ⛔ GUASTO: la scena uccisa durante lo stacco: %s" % t.strip()[-80:], flush=True)
    time.sleep(max(0, ATTESA_S - (time.time() - t_stacco)))
    t_fine = time.time()
    time.sleep(3)                                 # almeno un battito dopo l'attesa
    dopo = G.processi(s)
    q1 = G.quaderno(s)
    reg = s.registro_da(segno) if segno is not None else []
    ev = [s.salva_testo("server-%s-stacco.txt" % passata, reg)]
    e16, r16 = giudica_stacco(prima, dopo, q1, int(t_fine * 1000), testo, reg)
    metti("F-016", e16, r16, atteso="dopo %d s staccato: stessi PID, sessione viva, la scena "
          "batte col suo testo" % ATTESA_S,
          osservato="prima %s · dopo %s · %d righe di quaderno" % (prima, dopo, len(q1)),
          evidenze=ev)

    # ── RIATTACCO: un browser nuovo, stesso utente e parola
    segno = s.segno_registro()
    s.accendi_browser()
    ok, m, rifiuti, sec = G.entra_con_riprova(s, tetto_s=40)
    reg = s.registro_da(segno) if segno is not None else []
    ev = [s.salva_testo("server-%s-riattacco.txt" % passata, reg)]
    if not ok:
        for f in ("F-017", "P-A", "P-F"):
            metti(f, S.FAIL, "il riattacco non entra in %.0f s: %s (rifiuti: %s)"
                  % (sec, m, rifiuti), evidenze=ev)
        return
    ob = G.osserva_tela(s)
    frase_ok, frase = giudica_frase(ob.get("esito"))
    v = G.aspetta_testo(s, testo, "riattacco-%s" % passata, tetto=12)
    st = G.ultimo_stato(s)
    e17, r17 = giudica_ritrovo(testo, v, st, gettone)
    e17_stato = e17                  # i percorsi guardano lo STATO, non la frase
    if e17 == S.PASS and not frase_ok and not guasto:
        e17, r17 = S.FAIL, "stato ritrovato (%s) MA %s" % (r17, frase)
    ev17 = ev + [v.get("foto")]
    metti("F-017", e17, r17, atteso="ammesso con «sessione ripresa»; foto: finestra e "
          "striscia «%s»; campo: stesso gettone e valore" % testo,
          osservato="%s · %s · rientrato in %.1f s (%d rifiuti) · stato %s"
          % (frase, v.get("crudo"), sec, len(rifiuti), st), evidenze=ev17)

    # ── INPUT DOPO IL RIATTACCO (P-A)
    agg = testo_a_caso(2)
    if v.get("finestra"):
        cl = G.clic_sulla_scena(s, v)
        G.scrivi(s, agg)
        v2 = G.aspetta_testo(s, testo + agg, "input-dopo-%s" % passata, tetto=10)
        in_ok = v2.get("letto") == testo + agg
        r_in = "scritto «%s» dopo il riattacco (%s): la foto legge «%s»" % (
            agg, cl, v2.get("letto"))
        ev_in = [v2.get("foto")]
    else:
        in_ok, r_in, ev_in = False, "nessuna finestra su cui scrivere dopo il riattacco", []
    ea = S.PASS if (e16 == S.PASS and e17_stato == S.PASS and in_ok) else S.FAIL
    metti("P-A", ea, "stacco %s · stato al riattacco %s · input dopo: %s" % (e16, e17_stato, r_in),
          atteso="creazione→desktop→input→stacco→riattacco→input, tutto visto",
          osservato=r_in, evidenze=ev17 + ev_in)
    ef = S.PASS if (e16 == S.PASS and e17_stato == S.PASS) else S.FAIL
    metti("P-F", ef, "applicazione aperta, stacco, %d s, riattacco: F-016 %s · stato %s"
          % (ATTESA_S, e16, e17_stato), atteso="lo stato dell'applicazione ritrovato",
          osservato="%s | %s" % (r16[:200], r17[:200]), evidenze=ev17)
    return testo + agg if in_ok else None


def corpo(o, E):
    with S.Sessione(o, "016", E) as s:
        try:
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("senza accesso non c'e' niente da staccare: " + m)
            ok, t = G.accendi_scena(s)
            if not ok:
                raise S.Bloccata("la scena non si accende nella sessione: " + t[-200:])
            G.sveglia(s)
            v = trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("la finestra della scena non si vede nella foto: %s"
                                 % v.get("perche"))
            testo = testo_a_caso(4)
            v, note = G.scrivi_la_base(s, v, testo)
            if v.get("letto") != testo:
                raise S.Bloccata("l'input di PREPARAZIONE non arriva alla scena (e' F-004/F-007, "
                                 "non questa funzione): %s" % " | ".join(note))
            print("   scritto «%s» e letto in foto" % testo, flush=True)
            nuovo = un_giro(o, E, s, testo, "sana")
            if o.guasto:
                if s.g is None:
                    s.accendi_browser()
                un_giro(o, E, s, nuovo or testo, "guasto", guasto=True)
        finally:
            s.salva_console() if s.g else None
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
