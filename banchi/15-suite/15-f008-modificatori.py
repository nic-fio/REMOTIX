#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f008 — F-008 MODIFICATORI E COMBINAZIONI (la maglia C23 dentro la suite, allargata)

    python3 15-f008-modificatori.py --scatola gnome --browser chrome [--guasto]
    python3 15-f008-modificatori.py --certifica

La scena e' quella di C23 — IMPORTATA: `firefox-esr --kiosk` nella sessione con
un <input> sempre a fuoco e sotto la STRISCIA DI COLORI, una casella per
carattere: il valore del campo si legge dalla FOTOGRAFIA della tela
(`C23.fotografa_e_leggi`), tasti VERI dati al browser (`C23.manda`).  Per ogni
caso: pulizia (Ctrl+A, Canc indietro) ⇒ striscia vuota; la BASE ⇒ striscia =
base (se no BLOCKED: la scrittura semplice e' di F-007); la SEQUENZA ⇒ l'atteso.

I GRUPPI (una riga SUITE per passata, i gruppi e i casi nei campi `gruppi`/`casi`):
  Maiusc+frecce        i casi 1, 3, 4 di C23 (3 e 4: il Maiusc non resta incastrato)
  Ctrl+Maiusc+frecce   il caso 2 di C23 (Ctrl+Maiusc+Sinistra), Ctrl+Maiusc+Sinistra×2,
                       Ctrl+Maiusc+Destra (selezione per parola)
  Ctrl+A               seleziona tutto, e la lettera lo sostituisce
  Ctrl+C / Ctrl+V      copia e incolla DENTRO l'applicazione della sessione: una
                       parte selezionata col Maiusc, poi tutto con Ctrl+A e incollato
                       due volte — il testo incollato si LEGGE nella striscia
L'atteso di ogni caso e' anche calcolato da `simula()` (un campo di testo finto,
esteso da quello di C23: Destra, Ctrl+Destra, Ctrl+C, Ctrl+V), e `--certifica`
controlla che coincida e che la sequenza col guasto dia un'altra cosa.

GUASTO, per ciascun gruppo (stessa sessione, stessa scena, dopo la passata sana):
  Maiusc+frecce, Ctrl+Maiusc+frecce   le stesse sequenze senza Maiusc (`C23.senza_maiusc`)
  Ctrl+A                              la «a» senza Ctrl
  Ctrl+C / Ctrl+V                     la «c» e la «v» senza Ctrl (il Ctrl+A resta)
⇒ ogni caso deve dare rosso; un caso conta solo se la sua passata sana era verde.

⚠ Ctrl+V passa per il browser: la pagina, sull'evento `paste`, annuncia al server
  gli appunti DEL BROWSER (src/pagina.html ~7110-7220), e il server mette in coda
  l'incolla finche' l'annuncio non arriva.  ⇒ Il caso Ctrl+C/Ctrl+V prova tutta
  la catena come la vive l'utente: copia di la' ⇒ appunti al browser ⇒ incolla
  di la'.  ⛔ Il labwc del server e' di TUTTI gli agenti: gli appunti del browser
  sono condivisi con le loro prove (vedi il rapporto).
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._carica("g3", os.path.join(S.QUI, "15-g3-comune.py"))
C23 = G3.carica_maglia("c23", "11-c23-maiusc-e-frecce-selezionano.py")
VERDE, ROSSO, CIECO = C23.VERDE, C23.ROSSO, C23.CIECO
FUNZIONI = ("F-008",)

# ⭐ L'allargamento della tavolozza e dei tasti di C23 — si AGGIUNGE, non si copia:
#   la pagina (`C23.pagina_scena`) e il giudice (`C23.nome_colore`) leggono lo
#   stesso dizionario, quindi non possono divergere.
C23.SPECIALI.setdefault("ArrowRight", ("ArrowRight", "ArrowRight", 39, "", 0))
for _l in "rtv":
    if _l not in C23.COLORI:
        _libero = [c for c in C23._cubo() if c not in (C23.VUOTO, C23.ALTRO, C23.MARCA)
                   and c not in C23.COLORI.values()][0]
        C23.COLORI[_l] = _libero
        C23.ALFABETO += _l

premi, scrivi, col = C23.premi, C23.scrivi, C23.col


def _cc(guasto, passi):
    """Ctrl tenuto giu' su `passi` — o, col guasto, niente Ctrl."""
    return passi if guasto else col("Control", passi)


# (gruppo, titolo, base, costruttore(guasto) ⇒ sequenza, atteso)
def _da_c23(i):
    t, b, seq, a = C23.CASI[i]
    return (t, b, lambda g, seq=seq: C23.senza_maiusc(seq) if g else seq, a)


CASI = [
    ("Maiusc+frecce",) + _da_c23(0),
    ("Maiusc+frecce",) + _da_c23(2),
    ("Maiusc+frecce",) + _da_c23(3),
    ("Ctrl+Maiusc+frecce",) + _da_c23(1),
    ("Ctrl+Maiusc+frecce", "5 Ctrl+Maiusc+Sinistra×2, z", "uno due tre",
     lambda g: (col("Control", premi("ArrowLeft") * 2) if g else
                col("Control", col("Shift", premi("ArrowLeft") * 2))) + premi("z"),
     "uno z"),
    ("Ctrl+Maiusc+frecce", "6 Ctrl+Sinistra×2, Ctrl+Maiusc+Destra, z", "abc def",
     lambda g: col("Control", premi("ArrowLeft") * 2)
     + (col("Control", premi("ArrowRight")) if g else
        col("Control", col("Shift", premi("ArrowRight"))))
     + premi("z"),
     "z def"),
    ("Ctrl+A", "7 Ctrl+A, q", "abc de",
     lambda g: _cc(g, premi("a")) + premi("q"), "q"),
    ("Ctrl+C/Ctrl+V", "8 Maiusc+Sinistra×3, Ctrl+C, Destra, Ctrl+V", "abcdef",
     lambda g: col("Shift", premi("ArrowLeft") * 3) + _cc(g, premi("c"))
     + premi("ArrowRight") + _cc(g, premi("v")),
     "abcdefdef"),
    ("Ctrl+C/Ctrl+V", "9 Ctrl+A, Ctrl+C, Destra, Ctrl+V×2", "ab",
     lambda g: col("Control", premi("a")) + _cc(g, premi("c")) + premi("ArrowRight")
     + _cc(g, premi("v")) + _cc(g, premi("v")),
     "ababab"),
]
GRUPPI = []
for _c in CASI:
    if _c[0] not in GRUPPI:
        GRUPPI.append(_c[0])


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def simula(passi, valore=""):
    """Il campo finto di C23, allargato: Destra, Ctrl+Destra (a fine parola, come
    Firefox/GTK su Linux), Ctrl+C e Ctrl+V con un appunto."""
    ancora = fuoco = len(valore)
    giu, appunto = set(), ""
    for tipo, nome in passi:
        if tipo == "su":
            giu.discard(nome)
            continue
        if nome in ("Shift", "Control"):
            giu.add(nome)
            continue
        a, b = min(ancora, fuoco), max(ancora, fuoco)
        ctrl, maiusc = "Control" in giu, "Shift" in giu
        if nome in ("ArrowLeft", "ArrowRight"):
            n = len(valore)
            if ctrl:
                i = fuoco
                if nome == "ArrowLeft":
                    while i > 0 and valore[i - 1] == " ":
                        i -= 1
                    while i > 0 and valore[i - 1] != " ":
                        i -= 1
                else:
                    while i < n and valore[i] == " ":
                        i += 1
                    while i < n and valore[i] != " ":
                        i += 1
                nuovo = i
            elif not maiusc and a != b:
                nuovo = a if nome == "ArrowLeft" else b
            else:
                nuovo = max(0, fuoco - 1) if nome == "ArrowLeft" else min(n, fuoco + 1)
            fuoco = nuovo
            if not maiusc:
                ancora = fuoco
        elif nome == "Backspace":
            if a != b:
                valore = valore[:a] + valore[b:]
                ancora = fuoco = a
            elif a > 0:
                valore = valore[:a - 1] + valore[a:]
                ancora = fuoco = a - 1
        elif ctrl:
            k = nome.lower()
            if k == "a":
                ancora, fuoco = 0, len(valore)
            elif k == "c" and a != b:
                appunto = valore[a:b]
            elif k == "v":
                valore = valore[:a] + appunto + valore[b:]
                ancora = fuoco = a + len(appunto)
        else:
            valore = valore[:a] + nome + valore[b:]
            ancora = fuoco = a + len(nome)
    return valore


def esito_guasto_gruppo(coppie):
    """[(esito sano, esito col guasto)] di un gruppo ⇒ True visto / False / None.
    ⛔ Un caso conta solo se la sua passata sana era verde."""
    if not coppie or any(s != VERDE for s, _g in coppie):
        return None
    e = C23.esito_col_guasto([g for _s, g in coppie])
    return {VERDE: True, ROSSO: False, CIECO: None}[e]


def certifica():
    r = C23.certifica()
    print("\n⭐ 15-f008 · L'ALLARGAMENTO")
    guai = []

    def prova(cosa, vero, d=""):
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa, (" — " + d) if d else ""))
        if not vero:
            guai.append(cosa)

    tutti = [C23.MARCA, C23.VUOTO, C23.ALTRO] + list(C23.COLORI.values())
    dmin = min(C23._dist(a, b) for i, a in enumerate(tutti) for b in tutti[i + 1:])
    prova("tavolozza allargata: %d colori distinti, distanza minima %d > 2×%d"
          % (len(set(tutti)), dmin, C23.TOLLERANZA),
          len(set(tutti)) == len(tutti) and dmin > 2 * C23.TOLLERANZA)
    for t, b, seq, a in C23.CASI:
        prova("simula allargata = simula di C23 sul caso %s" % t.split()[0],
              simula(scrivi(b) + seq) == C23.simula(scrivi(b) + seq))
    for gr, t, b, costr, a in CASI:
        sano, gu = simula(scrivi(b) + costr(False)), simula(scrivi(b) + costr(True))
        prova("[%s] %s ⇒ %r" % (gr, t, a), sano == a, "da' %r" % sano)
        prova("[%s] %s col guasto ⇒ un'altra cosa" % (gr, t.split()[0]), gu != a,
              "da' %r" % gu)
        prova("[%s] %s: ogni carattere ha il suo colore, e ci sta" % (gr, t.split()[0]),
              all(c in C23.COLORI for c in b + a + gu) and max(len(b), len(a), len(gu))
              <= C23.CASELLE)
    geo = {"tl": 1920, "ta": 1080, "bw": 1920, "bh": 1080, "bx0": 0, "by0": 0,
           "sx": 1.0, "sy": 1.0}
    for v in ("abcdefdef", "ababab", "uno zdue tre", "cvv", "abccv"):
        letto, perche = C23.leggi_striscia(C23.campionatore(C23._foto_finta(v, geo), geo))
        prova("striscia %r si rilegge" % v, letto == v, "letto %r %s" % (letto, perche))
    prova("guasto: sano verde, guasto tutti rossi ⇒ visto",
          esito_guasto_gruppo([(VERDE, ROSSO), (VERDE, ROSSO)]) is True)
    prova("guasto: uno torna lo stesso ⇒ NON visto",
          esito_guasto_gruppo([(VERDE, ROSSO), (VERDE, VERDE)]) is False)
    prova("guasto: sano rosso ⇒ non si giudica",
          esito_guasto_gruppo([(ROSSO, ROSSO)]) is None)
    if guai:
        print("⛔ ALLARGAMENTO NON CERTIFICATO: %d" % len(guai))
        return 1
    print("⭐ ALLARGAMENTO CERTIFICATO")
    return r


# ═══════════════════════════════════════════════════════════════════════════
#  LA PASSATA
# ═══════════════════════════════════════════════════════════════════════════
def un_caso(s, geo, gruppo, titolo, base, seq, atteso, etichetta):
    """Il caso come lo fa `C23.osserva`: pulizia, base, sequenza, tre fotografie."""
    g, o = s.g, s.o
    corto = titolo.split()[0]
    nome = "%s-%s-c%s" % (o.browser, etichetta, corto)
    C23.manda(g, C23.PULISCI)
    vuoto, pv = C23.fotografa_e_leggi(g, geo, "", o.salva, nome + "-0vuoto")
    if vuoto:
        # ⚠ `[M]` 25 set, kde, server carico: una pulizia persa (il campo resta
        #   col valore del caso prima).  Si ripete UNA volta: la pulizia non e'
        #   la cosa giudicata, e il controllo «vuoto» resta com'e'.
        C23.manda(g, C23.PULISCI)
        vuoto, pv = C23.fotografa_e_leggi(g, geo, "", o.salva, nome + "-0vuoto-bis")
    C23.manda(g, scrivi(base))
    vb, pb = C23.fotografa_e_leggi(g, geo, base, o.salva, nome + "-1base")
    n0 = len(C23.leggi_il_quaderno(s.sc, s.chi))
    C23.manda(g, seq)
    visto, pvi = C23.fotografa_e_leggi(g, geo, atteso, o.salva, nome + "-2dopo")
    es, msg = C23.giudica_caso(titolo, base, atteso, vuoto, vb, visto)
    if es == CIECO and (vuoto is None or vb is None):
        msg += " — %s" % (pv or pb)
    elif visto is None and es != CIECO:
        es, msg = CIECO, "%s: la striscia non si legge dopo la sequenza: %s" % (titolo, pvi)
    if es == ROSSO and not G3.scena_viva(s.sc, s.chi):
        es, msg = CIECO, ("%s: la scena e' MORTA durante il caso (firefox-esr non c'e' piu' "
                          "nella sessione): il rosso non e' del prodotto%s"
                          % (titolo, G3.spiega_cieco(s.oom0)))
    quad = C23.leggi_il_quaderno(s.sc, s.chi)[n0:]
    tasti = [r[2:] for r in quad if r.startswith("K ")]
    valori = [r[2:] for r in quad if r.startswith("V ")]
    print("   %s [%s] %s" % ({VERDE: "⭐", ROSSO: "⛔", CIECO: "⚠"}[es], gruppo, msg), flush=True)
    if es != VERDE:
        print("        keydown remoti: %s" % " | ".join(tasti)[:400], flush=True)
        print("        valori remoti:  %s" % " | ".join(valori)[-300:], flush=True)
    return {"gruppo": gruppo, "caso": corto, "titolo": titolo, "esito": es, "motivo": msg,
            "visto": visto, "atteso": atteso, "keydown_remoti": tasti[-40:],
            "valori_remoti": valori[-10:]}


def passata(s, geo, guasto):
    risultati = []
    for gruppo, titolo, base, costr, atteso in CASI:
        r = un_caso(s, geo, gruppo, titolo, base, costr(guasto), atteso,
                    "guasto" if guasto else "sano")
        risultati.append(r)
        ciechi = [x for x in risultati[-2:] if x["esito"] == CIECO]
        if r["esito"] == CIECO and (not guasto or len(ciechi) >= 2
                                    or not G3.scena_viva(s.sc, s.chi)):
            # come C23: un caso cieco vuol dire che la scena non testimonia
            break
    return risultati


def corpo(o, E):
    with S.Sessione(o, "008", E) as s:
        G3.prepara_o(o, s)
        s.oom0 = G3.uccisi_dal_server()
        segno = s.segno_registro()
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        geo = s.geometria()
        if not geo:
            raise S.Bloccata("`REMOTIX_PUNTATORE.geometria` non c'e'")
        print("   sveglia: %s" % S.C21.sveglia(s.g, geo), flush=True)
        porta = random.randint(39400, 39499)
        ok, t = C23.accendi_la_scena(s.sc, s.chi, porta)
        print("   scena: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
        if not ok:
            raise S.Bloccata("la scena non si accende: %s" % t[-300:])
        time.sleep(3)
        x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.26)
        s.g.clic(x, y)
        time.sleep(1.0)

        prima = G3.evidenze_ora(o)
        sani = passata(s, geo, False)
        ev = G3.evidenze_nuove(o, prima)
        gruppi = {}
        for gr in GRUPPI:
            es = [r["esito"] for r in sani if r["gruppo"] == gr]
            gruppi[gr] = C23.esito_complessivo(es) if es else CIECO
        tutto = C23.esito_complessivo(list(gruppi.values()))
        male = [r["motivo"] for r in sani if r["esito"] != VERDE]
        if tutto == VERDE:
            ragione = "tutti e %d i casi tornano (%s)" % (len(sani), ", ".join(GRUPPI))
        else:
            ragione = "; ".join(male) or "casi non guardati: %s" % [
                g for g, e in gruppi.items() if e == CIECO]
            if tutto == CIECO and "OOM" not in ragione:
                ragione += G3.spiega_cieco(s.oom0)
        quaderno = s.salva_testo("quaderno-scena-%s.txt" % o.browser,
                                 C23.leggi_il_quaderno(s.sc, s.chi))
        try:
            premuti = s.g.js("return REMOTIX.input_classico.stato().tasti_premuti")
        except Exception as ex:                  # noqa: BLE001
            premuti = "? (%s)" % str(ex)[:80]
        E.metti("F-008", tutto, ragione,
                atteso="; ".join("%s: %r ⇒ %r" % (c[1].split()[0], c[2], c[4]) for c in CASI),
                osservato="; ".join("%s %r" % (r["caso"], r["visto"]) for r in sani),
                evidenze=ev + [quaderno, s.salva_console()],
                gruppi={k: S.DA_CODICE[v] for k, v in gruppi.items()},
                casi=[dict(r, esito=S.DA_CODICE[r["esito"]]) for r in sani],
                tasti_premuti_alla_fine=premuti)

        if o.guasto:
            print("   ── GUASTO: le stesse sequenze senza il modificatore di ciascun gruppo ──",
                  flush=True)
            prima = G3.evidenze_ora(o)
            guasti = passata(s, geo, True)
            per_gruppo = {}
            for gr in GRUPPI:
                coppie = [(sa["esito"], gu["esito"]) for sa, gu in zip(sani, guasti)
                          if sa["gruppo"] == gr]
                per_gruppo[gr] = esito_guasto_gruppo(coppie)
            v = list(per_gruppo.values())
            visto = None if None in v else all(v)
            ragione = "; ".join("%s: %s" % (gr, {True: "visto", False: "NON VISTO",
                                                  None: "non giudicabile"}[x])
                                for gr, x in per_gruppo.items())
            E.guasto("F-008", visto, ragione,
                     atteso="senza il modificatore ogni caso da' rosso",
                     osservato="; ".join("%s %r" % (r["caso"], r["visto"]) for r in guasti),
                     evidenze=G3.evidenze_nuove(o, prima),
                     gruppi={k: x for k, x in per_gruppo.items()},
                     casi=[dict(r, esito=S.DA_CODICE[r["esito"]]) for r in guasti])
        server = s.registro_da(segno) if segno is not None else []
        s.salva_testo("server-f008.txt", server)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
