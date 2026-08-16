#!/usr/bin/env python3
"""06-b37-modi.py — ⛔ I TRE MODI DI `?adatta=`, E L'INVARIANTE **I6**.

    python3 banchi/06-b37-modi.py <porta> <display> <pid> <nome> <esiti>

`CODER.md` **I6**: «cio' che cambia quel che si VEDE sta dietro un interruttore
spento finche' l'utente non lo guarda».  ⇒ Le due domande, e sono diverse:

  · **lo spento e' davvero spento?**  Non «l'interruttore esiste»: che con
    l'interruttore in posizione di riposo il cammino **non venga percorso**.
  · **`segui` fa UNA cosa sola?**  Cioe' insegue la finestra, e nient'altro.

⛔ L'ATTESO, DICHIARATO PRIMA — ridimensionando la finestra 4 volte a sessione
   aperta, le richieste di tela che partono devono essere:

     `?adatta=no`      0   (`SPECIFICHE.md` §6.4 · e' la pagina di ieri)
     *(niente)*        0   (di suo si chiede SOLO all'attacco — §6.4, §5.0-sexies)
     `?adatta=segui`   4   (una per ridimensionamento, dietro il fondo di 250 ms)

⭐ IL CONTROLLO POSITIVO, e senza di lui i due zeri non valgono niente: nello
   stesso giro si conta quanti `resize` la pagina ha RICEVUTO.  Uno zero con 4
   resize arrivati e' un interruttore spento; uno zero con 0 resize e' un banco
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
       all'avvio della pagina (`src/pagina.html:2776`)."""
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


print("== 06-b37 · %s — i tre modi di `?adatta=` (I6)" % B.nome, flush=True)
if not B.aspetta_pagina() or not B.trova_finestra():
    print("    NO  pagina o finestra assenti", flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

atteso = {"no": 0, "": 0, "segui": 4}
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
        print("    OK  %s" % ("lo spento e' DAVVERO spento (0 richieste con 4 "
                              "resize arrivati)" if atteso[modo] == 0 else
                              "«segui» insegue la finestra: una richiesta per "
                              "ridimensionamento, e nient'altro"), flush=True)
    else:
        print("    NO  %d richieste invece di %d: %s"
              % (n, atteso[modo], [c["perche"] for c in r["chieste"]]),
              flush=True)
        guasti += 1

sys.exit(1 if guasti else 0)
