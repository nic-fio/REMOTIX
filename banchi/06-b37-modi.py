#!/usr/bin/env python3
"""06-b37-modi.py — ⛔ LA TELA NON SI TOCCA A SESSIONE VIVA, IN NESSUN MODO.

    python3 banchi/06-b37-modi.py <porta> <display> <pid> <nome> <esiti>

⛔⛔ QUESTO BANCO HA CAMBIATO MESTIERE IL 17 AGOSTO 2026, e va detto perche' il
   nome del file e' rimasto quello di prima.  Misurava **i tre modi di
   `?adatta=`** e l'invariante **I6** — cioe' che l'interruttore
   dell'inseguimento fosse davvero spento di suo, e che acceso inseguisse.

⭐ Poi l'utente ha deciso (`DECISIONI.md` §5.1-bis): *«non voglio mettere delle
   eccezioni nel progetto.  Il dynamic resolution esce dalle funzionalita' di
   Remotix»*.  L'interruttore non esiste piu', e con lui la domanda su I6.

⇒ ⛔ **QUEL CHE QUESTO BANCO SORVEGLIA ADESSO E' CHE LA FUNZIONE NON RIENTRI**:
   che ridimensionare la finestra a sessione aperta **non mandi niente sul filo**,
   qualunque cosa ci sia nell'indirizzo.  ⚠ E' una guardia contro il ritorno, non
   una prova di una funzione: il giorno in cui qualcuno riscrivesse
   `tela_forse_chiedi()` credendo di curare le bande nere, questo diventa rosso.

⛔ L'ATTESO, DICHIARATO PRIMA — ridimensionando la finestra 4 volte a sessione
   aperta, le richieste di tela che partono devono essere:

     *(niente)*        0   (si chiede SOLO all'attacco e al riattacco — §5.0-sexies)
     `?adatta=no`      0   (`SPECIFICHE.md` §6.4 · non chiede mai, nemmeno all'attacco)
     `?adatta=segui`   0   ⭐ IL VALORE CHE NON ESISTE PIU': un indirizzo vecchio,
                           un segnalibro, un banco non aggiornato.  Deve valere il
                           predefinito e **non riattivare niente**

⭐ IL CONTROLLO POSITIVO, e senza di lui i tre zeri non valgono niente: nello
   stesso giro si conta quanti `resize` la pagina ha RICEVUTO.  Uno zero con 4
   resize arrivati e' una funzione che non c'e'; uno zero con 0 resize e' un banco
   che non ha stimolato nulla (`CODER.md` §3.10).
"""
import importlib.util
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("b37comune",
                                            os.path.join(QUI, "06-b37-comune.py"))
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)

B = _m.Banco(*sys.argv[1:6])

PREPARA = """(function () {
  schermo.tela_l = 1000; schermo.tela_a = 700;
  schermo.sessione = true;
  window.__b37_chieste = [];
  window.__b37_r = 0;
  addEventListener("resize", function () { window.__b37_r++; });
  chiedi_tela = function (perche) {
    window.__b37_chieste.push({ perche: perche, spenta: tela_spenta });
  };
  return ADATTA;
})()"""


def giro(modo):
    """⛔ Ogni modo vuole un CARICAMENTO suo: `ADATTA` si legge una volta sola,
       all'avvio della pagina (`const ADATTA` in `src/pagina.html`)."""
    try:
        B.com("location.hash = %r; location.reload(); 'ricarico'"
              % ("adatta=" + modo if modo else ""), 3)
    except Exception:
        pass
    time.sleep(2.5)
    if not B.aspetta_pagina(25):
        return None
    time.sleep(1.0)
    vero = B.val(PREPARA)
    g = B.geometria()
    for i in range(4):
        B.ridimensiona(g["l"] - 12 * (i + 1), g["a"])
        time.sleep(0.55)
    time.sleep(1.0)
    chieste = B.js("window.__b37_chieste")
    resize = B.js("window.__b37_r")
    B.ridimensiona(g["l"], g["a"])
    time.sleep(0.5)
    return {"modo": modo or "(niente)", "ADATTA": vero, "chieste": chieste,
            "resize_arrivati": resize}


print("== 06-b37 · %s — la tela non si tocca a sessione viva (§5.1-bis)"
      % B.nome, flush=True)
if not B.aspetta_pagina() or not B.trova_finestra():
    print("    NO  pagina o finestra assenti", flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

atteso = {"no": 0, "": 0, "segui": 0}
guasti = 0
for modo in ("no", "", "segui"):
    r = giro(modo)
    if not r:
        print("    NO  modo «%s»: la pagina non e' tornata dopo il "
              "ricaricamento" % (modo or "(niente)"), flush=True)
        guasti += 1
        continue
    n = len(r["chieste"])
    B.scrivi({"tipo": "modi", **r}, iniezione="si")
    print("    --  `?adatta=%-6s` ⇒ ADATTA=«%s» · %d resize arrivati · %d "
          "richieste di tela (atteso %d)"
          % (r["modo"], r["ADATTA"], r["resize_arrivati"], n, atteso[modo]),
          flush=True)
    if r["resize_arrivati"] < 4:
        print("    NO  solo %d resize su 4 sono arrivati: il conto delle "
              "richieste non e' giudicabile — e' il PALCO"
              % r["resize_arrivati"], flush=True)
        guasti += 1
        continue
    if n == atteso[modo]:
        print("    OK  la tela non si tocca a sessione viva (0 richieste con 4 "
              "resize arrivati)", flush=True)
    else:
        # ⛔ E il rosso qui ha UN significato solo, che vale la pena scrivere:
        #    il ridimensionamento a caldo e' RIENTRATO.  Non «il conto e'
        #    diverso»: la funzione che l'utente ha tolto il 17 agosto 2026 e'
        #    tornata viva (`DECISIONI.md` §5.1-bis).
        print("    NO  ⛔ IL RIDIMENSIONAMENTO A CALDO E' RIENTRATO: %d "
              "richieste invece di 0 — %s"
              % (n, [c["perche"] for c in r["chieste"]]), flush=True)
        guasti += 1

sys.exit(1 if guasti else 0)
