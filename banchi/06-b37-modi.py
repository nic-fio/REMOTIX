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

⭐ I CONTROLLI POSITIVI SONO TRE, e senza di loro i tre zeri non valgono niente —
   quando l'atteso e' zero dappertutto, TUTTO quel che non guarda e' verde:

   1. quanti `resize` la pagina ha RICEVUTO (dev'essere 4): uno zero con 0 resize
      e' un banco che non ha stimolato nulla, non un prodotto sano;
   2. ⭐ **la spia vede?**  Si chiama `chiedi_tela` a mano e si pretende che il
      conto salga.  ⛔ Difetto di QUESTO banco, trovato il 17 agosto 2026: finche'
      l'atteso di `segui` era 4, quel 4 faceva da controllo positivo senza dirlo;
      azzerati tutti gli attesi, una spia rotta darebbe zero — cioe' verde — su
      un prodotto che inseguisse la finestra a ogni pixel;
   3. ⭐ `typeof tela_forse_chiedi` dev'essere `undefined`: e' la prova DIRETTA
      che la funzione e' uscita, e non dipende da nessuna spia.
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

# ⛔⭐ 22 agosto 2026: anche qui la spia non SOSTITUISCE piu' la funzione, la
#    AVVOLGE — dentro c'e' il TESTO VERO di `chiedi_tela` estratto dal prodotto
#    (`06-b37-strumenta.py`), con un canale finto nello scope.  ⇒ Ai due zeri
#    («0 arrivi», «0 messaggi») corrispondono due domande diverse, e la seconda
#    e' quella che conta: se il ridimensionamento a caldo rientrasse, sul canale
#    finito arriverebbe un `ADATTA_TELA` VERO.
PREPARA = """(function () {
  schermo.tela_l = 1000; schermo.tela_a = 700;
  schermo.sessione = true;
  window.__b37_chieste = [];
  window.__b37_mandati = [];
  window.__b37_r = 0;
  addEventListener("resize", function () { window.__b37_r++; });
  if (typeof window.__b37_chiedi_tela_sorgente !== "string")
    return "⛔ manca il testo vero di chiedi_tela";
  const canale = {
    manda: async function (tipo, corpo) {
      window.__b37_mandati.push({ tipo: tipo, byte: corpo.length });
      return true;
    }
  };
  tela_spenta = false;
  tela_richiesta_ripetuta = false;
  tela_chiesta_l = 0; tela_chiesta_a = 0;
  eval(window.__b37_chiedi_tela_sorgente);
  window.__b37_vera_chiedi_tela = chiedi_tela;
  chiedi_tela = function (perche) {
    window.__b37_chieste.push({ perche: perche, spenta: tela_spenta });
    return window.__b37_vera_chiedi_tela(perche);
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
    mandati = B.js("window.__b37_mandati")
    resize = B.js("window.__b37_r")
    # ⛔⭐⭐ IL CONTROLLO POSITIVO DELLA SPIA, e senza di lui questo banco NON SA
    #      FALLIRE — difetto suo, trovato il 17 agosto 2026 rileggendo la
    #      riscrittura di quello stesso giorno.
    #
    # ⚠ Finche' l'atteso di `segui` era 4, quel 4 faceva da controllo positivo
    #   SENZA DIRLO: una spia che non si fosse installata avrebbe dato 0 dove ne
    #   servivano 4, e il banco sarebbe diventato rosso.  ⛔ Da quando gli attesi
    #   sono ZERO DAPPERTUTTO quella prova e' sparita con l'atteso che la
    #   conteneva: una spia rotta darebbe zero — cioe' VERDE — su un prodotto
    #   qualunque, anche su uno che insegue la finestra a ogni pixel.
    #
    # ⇒ Si chiama `chiedi_tela` a mano e si pretende che la spia LO VEDA.  ⚠ E'
    #   `chiedi_tela` e non `tela_forse_chiedi()`: quest'ultima e' uscita col
    #   fondo, e chiamarla darebbe un `ReferenceError` che il banco leggerebbe
    #   come «zero richieste» — un verde per il motivo sbagliato, di nuovo.
    B.val("chiedi_tela('controllo positivo del banco')")
    time.sleep(0.7)
    positivo = len(B.js("window.__b37_chieste")) - len(chieste)
    # ⛔⭐ E IL CONTROLLO POSITIVO VERO: la funzione del prodotto, a voce accesa,
    #    DEVE mandare un `ADATTA_TELA` sul canale finto.  Senza questo, «zero
    #    messaggi» direbbe la stessa cosa se il canale fosse rotto.
    positivo_filo = len(B.js("window.__b37_mandati")) - len(mandati)
    # ⭐ E la prova DIRETTA che la funzione e' uscita, che non dipende da nessuna
    #   spia: il fondo non deve nemmeno esistere nella pagina.
    fondo = B.js("typeof tela_forse_chiedi")
    B.ridimensiona(g["l"], g["a"])
    time.sleep(0.5)
    return {"modo": modo or "(niente)", "ADATTA": vero, "chieste": chieste,
            "mandati": mandati, "resize_arrivati": resize,
            "positivo": positivo, "positivo_filo": positivo_filo,
            "fondo": fondo}


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
    m = len(r["mandati"])
    B.scrivi({"tipo": "modi", **r}, iniezione="si")
    print("    --  `?adatta=%-6s` ⇒ ADATTA=«%s» · %d resize arrivati · %d "
          "arrivi a `chiedi_tela` (atteso %d) · %d ADATTA_TELA sul canale "
          "(atteso 0) · spia %s · canale %s · tela_forse_chiedi «%s»"
          % (r["modo"], r["ADATTA"], r["resize_arrivati"], n, atteso[modo], m,
             "VEDE" if r["positivo"] >= 1 else "CIECA",
             "VIVO" if r["positivo_filo"] >= 1 else "MUTO", r["fondo"]),
          flush=True)
    if r["resize_arrivati"] < 4:
        print("    NO  solo %d resize su 4 sono arrivati: il conto delle "
              "richieste non e' giudicabile — e' il PALCO"
              % r["resize_arrivati"], flush=True)
        guasti += 1
        continue
    # ⛔ I DUE CONTROLLI CHE RENDONO GIUDICABILE LO ZERO, e vanno PRIMA di
    #    giudicarlo: senza, «la funzione non c'e'» e «il banco non guarda» hanno
    #    lo stesso aspetto (`CODER.md` §3.10, §4.6).
    if r["positivo"] < 1:
        print("    NO  ⛔ la spia NON vede una richiesta chiamata a mano ⇒ lo "
              "zero e' del BANCO, non del prodotto: non si giudica niente",
              flush=True)
        guasti += 1
        continue
    if r["positivo_filo"] < 1:
        print("    NO  ⛔ la funzione VERA del prodotto, chiamata a voce accesa, "
              "non ha mandato niente sul canale finto ⇒ lo zero degli "
              "`ADATTA_TELA` e' del BANCO: non si giudica niente", flush=True)
        guasti += 1
        continue
    if m:
        print("    NO  ⛔⛔ IL RIDIMENSIONAMENTO A CALDO E' RIENTRATO: %d "
              "`ADATTA_TELA` sono partiti sul canale dopo 4 ridimensionamenti"
              % m, flush=True)
        guasti += 1
        continue
    if r["fondo"] != "undefined":
        print("    NO  ⛔ `tela_forse_chiedi` esiste ancora (typeof «%s»): il "
              "fondo del ridimensionamento a caldo e' rientrato (§5.1-bis)"
              % r["fondo"], flush=True)
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
