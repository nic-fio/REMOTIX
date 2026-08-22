#!/usr/bin/env python3
"""06-b37-voce.py — ⛔ `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`: LA VOCE SPENTA.

    python3 banchi/06-b37-voce.py <porta> <display> <pid-browser> <nome> <esiti.jsonl>

`RCP.md` §7.1: «se il compositore non sa ridimensionare, il server **DEVE**
rispondere ad `ADATTA_TELA` con `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, e il
client **DEVE** mostrare la voce come spenta.  NON DEVE fingere che sia
riuscito.»

⛔⛔ QUESTA E' UN'INIEZIONE, E NON E' IL FILO.  Non c'e' nessun compositore
   incapace su questa macchina (Mutter sa ridimensionare, KWin ≤ 6.7.4 non c'e').
   ⇒ Il messaggio si costruisce byte per byte con lo stesso `Scrittore` della
   pagina e si consegna ad `ascolta_controllo()` attraverso un **canale finto**.
   ⭐ Cosi' il ramo esercitato e' quello VERO — la riga 3619 e seguenti — e non
   una sua imitazione.  ⚠ Quel che questa scena NON prova: che il server mandi
   davvero quel messaggio (e' 6.4), e che i byte sul filo siano quelli (e' 6.6).

═══════════════════════════════════════════════════════════════════════════
⛔ L'ATTESO, DICHIARATO PRIMA

  V1 la pagina NON dichiara riuscito un `ADATTA_TELA` rifiutato: nel registro
     c'e' la riga del rifiuto, e nessuna riga dice «adattata».
  V2 ⭐ una «voce» da spegnere ESISTE?  ⚠ Parto dall'ipotesi che **non esista**:
     ho letto la pagina e non c'e' nessun comando «adatta il desktop» — la
     misura serve a dirlo con un numero invece che con una lettura.
  V3 dopo il rifiuto la pagina RICHIEDE una volta dopo 4 s
     (`TELA_RICHIESTA_RIPETI_MS`), e il codice non distingue il motivo: lo fa
     anche con `COMPOSITORE_INCAPACE`, dove il suo stesso commento dice che
     «insistere non lo insegna».
  V4 ⛔ con `?adatta=segui` acceso, dopo il rifiuto **ogni** ridimensionamento
     manda un `ADATTA_TELA` nuovo, per sempre: la voce non si spegne mai.

⛔⛔ E V4 HA CAMBIATO DOMANDA IL 17 AGOSTO 2026 — `DECISIONI.md` §5.1-bis, e la
   riga qui sopra e' la storia, non l'atteso.  Il ridimensionamento a caldo e'
   **uscito dal prodotto** per decisione dell'utente, e con lui l'interruttore
   `?adatta=segui`.  ⇒ L'atteso di V4 non e' piu' «zero richieste che passano la
   guardia», e' **zero arrivi a `chiedi_tela`**: la scena che produceva il
   difetto non puo' piu' esistere.  ⚠ V1-V3 non cambiano: la voce spenta serve
   ancora, perche' la tela si chiede a ogni **riattacco** e la ripetizione su
   `NON_ORA` (4 s) e' viva.
"""
import importlib.util
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("b37comune",
                                            os.path.join(QUI, "06-b37-comune.py"))
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)

B = _m.Banco(*sys.argv[1:6])

# ---------------------------------------------------------------------------
# ⛔⭐⭐ LA GUARDIA SI PROVA DOVE VIVE — 22 agosto 2026, `fasi/06` §5.5, secondo
#      falso verde.  Qui c'era una SPIA che SOSTITUIVA `chiedi_tela`, e la
#      guardia (`if (tela_spenta) { … return; }`) sta DENTRO la funzione
#      sostituita: il banco provava che **un booleano cambia valore**.
#
#  ⇒ Adesso si installa il TESTO VERO della funzione del prodotto — estratto da
#    `src/pagina.html` da `06-b37-strumenta.py` e messo nella pagina come
#    `window.__b37_chiedi_tela_sorgente` — dentro una `eval` diretta che ha nello
#    scope un **canale finto**.  ⭐ Quel che gira e' l'assegnazione del prodotto,
#    carattere per carattere, guardia compresa; e l'osservabile non e' piu' «la
#    spia e' stata chiamata», e' **`canale.manda(TIPO.ADATTA_TELA, …)`**, cioe' il
#    messaggio che sarebbe partito sul filo.
#
#  ⚠ E la spia resta, ma SOPRA: conta gli ARRIVI alla funzione e poi chiama
#    quella vera.  Due numeri distinti, e servono tutt'e due — «non e' stata
#    chiamata» e «e' stata chiamata e non ha mandato niente» sono due esiti
#    diversi, e prima erano lo stesso.
PREPARA = """(function () {
  /* la sessione, quanto basta perche' il ramo del `TELA` abbia senso */
  schermo.tela_l = 1000; schermo.tela_a = 700;
  schermo.sessione = true;
  window.__b37_chieste = [];
  window.__b37_mandati = [];
  window.__b37_coda = [];
  window.__b37_congedi = 0;
  if (typeof window.__b37_chiedi_tela_sorgente !== "string")
    return "⛔ manca il testo vero di chiedi_tela: la strumentazione non l'ha "
         + "messo, e questo banco NON si arrangia con un'imitazione";
  /* il canale finto: consegna quel che gli si mette in coda, e REGISTRA quel
     che gli si manda.  ⛔ E' l'unico osservabile che conta: senza server non
     c'e' nessun filo, ma `canale.manda` e' esattamente la riga che lo userebbe. */
  const canale = {
    ricevi: async function () {
      for (;;) {
        if (window.__b37_coda.length) return window.__b37_coda.shift();
        await new Promise(function (r) { setTimeout(r, 20); });
      }
    },
    manda: async function (tipo, corpo) {
      window.__b37_mandati.push({ tipo: tipo, byte: corpo.length,
                                  t: Date.now() });
      return true;
    }
  };
  /* ⛔ Lo stato di partenza e' quello che il prodotto mette due righe SOPRA
     l'assegnazione («la voce riparte ACCESA a ogni sessione»): si dichiara,
     perche' non fa parte del testo estratto. */
  tela_spenta = false;
  tela_richiesta_ripetuta = false;
  tela_chiesta_l = 0; tela_chiesta_a = 0;
  /* ⭐ L'EVAL DIRETTA: installa il testo del PRODOTTO, con `canale` nello scope. */
  eval(window.__b37_chiedi_tela_sorgente);
  if (typeof chiedi_tela !== "function")
    return "⛔ il testo vero non ha installato niente";
  window.__b37_vera_chiedi_tela = chiedi_tela;
  chiedi_tela = function (perche) {
    window.__b37_chieste.push({ perche: perche, t: Date.now(),
                                spenta: tela_spenta,
                                misura: tela_da_chiedere() });
    return window.__b37_vera_chiedi_tela(perche);
  };
  ascolta_controllo(canale, function () { window.__b37_congedi++; });
  window.__b37_righe0 = righe.length;
  return "pronto";
})()"""

RIFIUTA = """(function (motivo) {
  const c = new Scrittore().u8(2).u8(motivo).u32(schermo.tela_l)
                           .u32(schermo.tela_a).byte();
  window.__b37_coda.push({ tipo: TIPO.TELA, corpo: c });
  return "consegnato";
})(%d)"""

# ⛔ La domanda «esiste una voce da spegnere?» si fa al DOM, non alla memoria.
CERCA_VOCE = """(function () {
  const c = [];
  for (const el of document.querySelectorAll(
       "button, input, select, [role=button], a, label, summary")) {
    const t = ((el.textContent || "") + " " + (el.value || "") + " "
               + (el.id || "") + " " + (el.title || "")).toLowerCase();
    if (t.indexOf("adatta") >= 0 || t.indexOf("desktop") >= 0
        || t.indexOf("tela") >= 0 || t.indexOf("schermo") >= 0)
      c.push({ tag: el.tagName, id: el.id,
               testo: (el.textContent || el.value || "").trim().slice(0, 40),
               spento: !!el.disabled });
  }
  return JSON.stringify({ candidati: c,
                          comandi_totali: document.querySelectorAll(
                            "button, input, select, [role=button]").length });
})()"""


def righe_nuove():
    return json.loads(B.val("JSON.stringify(righe.slice(window.__b37_righe0))"))


print("== 06-b37 · %s — la voce spenta (INIEZIONE, non il filo)" % B.nome,
      flush=True)
if not B.aspetta_pagina():
    print("    NO  la pagina non si e' mai annunciata", flush=True)
    sys.exit(3)
if not B.trova_finestra():
    print("    NO  nessuna finestra X", flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

guasti = 0

# --- V2: la voce esiste? ----------------------------------------------------
voce = json.loads(B.val(CERCA_VOCE))
print("\n    --  V2 · comandi nella pagina: %d in tutto, %d che nominino "
      "«adatta/desktop/tela/schermo»"
      % (voce["comandi_totali"], len(voce["candidati"])), flush=True)
if voce["candidati"]:
    for c in voce["candidati"]:
        print("        %s#%s «%s» spento=%s" % (c["tag"], c["id"], c["testo"],
                                                c["spento"]), flush=True)
else:
    print("    ⛔  V2: NESSUNA voce «adatta il desktop» esiste in questa "
          "pagina ⇒ la prescrizione di §7.1 «mostrare la voce come spenta» "
          "OGGI NON HA OGGETTO.  ⚠ Non e' un verde: e' un obbligo senza un "
          "posto dove atterrare", flush=True)
B.scrivi({"tipo": "voce-dom", "candidati": voce["candidati"],
          "comandi_totali": voce["comandi_totali"]}, iniezione="si")

# --- V1/V3: il rifiuto ------------------------------------------------------
print("\n    --  V1/V3 · TELA(RIFIUTATA, COMPOSITORE_INCAPACE) iniettato",
      flush=True)
B.val(PREPARA)
B.val(RIFIUTA % 1)
time.sleep(1.2)
righe1 = righe_nuove()
chieste1 = B.js("window.__b37_chieste")
for r in righe1:
    print("        registro: %s" % r[:150], flush=True)
finge = [r for r in righe1 if "adattata" in r.lower() or "riuscit" in r.lower()]
if finge:
    print("    NO  V1: la pagina dichiara riuscito un rifiuto: %s" % finge,
          flush=True)
    guasti += 1
else:
    print("    OK  V1: nessuna riga dice che sia riuscito (%d righe nuove)"
          % len(righe1), flush=True)
if not any("RIFIUTATA" in r for r in righe1):
    print("    NO  V1: e non c'e' nemmeno la riga del rifiuto: il ramo non e' "
          "stato percorso — questa non e' una misura", flush=True)
    guasti += 1

# ⛔ La ripetizione: si aspetta il fondo dichiarato + un margine.
attesa = B.js("TELA_RICHIESTA_RIPETI_MS") / 1000.0
print("        (aspetto %.1f s: TELA_RICHIESTA_RIPETI_MS)" % attesa, flush=True)
time.sleep(attesa + 1.5)
chieste2 = B.js("window.__b37_chieste")
print("    --  V3: ADATTA_TELA che la pagina VORREBBE rimandare dopo il "
      "rifiuto: %d subito, %d dopo l'attesa" % (len(chieste1), len(chieste2)),
      flush=True)
for c in chieste2:
    print("        «%s» misura %s · la guardia `tela_spenta` valeva %s"
          % (c["perche"], c["misura"], c["spenta"]), flush=True)
spenta = B.js("tela_spenta")
print("    --  V3: dopo il rifiuto `tela_spenta` vale %s" % spenta, flush=True)
if spenta is not True:
    print("    NO  V3: la voce NON si e' spenta su COMPOSITORE_INCAPACE",
          flush=True)
    guasti += 1
else:
    print("    OK  V3: la voce si e' SPENTA (RCP.md §7.1), e la dichiarazione "
          "all'utente dice: «%s»" % B.js("DICHIARAZIONI.video"), flush=True)
ripetute = [c for c in chieste2 if "NON_ORA" in c["perche"]]
if ripetute:
    print("    NO  V3: la richiesta si e' ripetuta con un motivo che il server "
          "non ha dato (%d volte)" % len(ripetute), flush=True)
    guasti += 1
else:
    print("    OK  V3: nessuna ripetizione su COMPOSITORE_INCAPACE — la "
          "ripetizione resta solo per NON_ORA (motivo 3)", flush=True)

# --- ⛔⭐⭐ V5: LA GUARDIA, PROVATA DENTRO LA FUNZIONE VERA ------------------
# `fasi/06` §5.5, secondo falso verde.  Fino al 21 agosto 2026 questa scena
# provava che `tela_spenta` **cambia valore**.  ⇒ Adesso si chiama la funzione
# del prodotto e si guarda l'unico osservabile che conta: e' partito un
# `ADATTA_TELA` sul canale, si' o no?
print("\n    --  V5 · la guardia, ESERCITATA dentro `chiedi_tela` (il testo "
      "vero del prodotto, installato con una eval diretta)", flush=True)
mandati_prima = B.js("window.__b37_mandati")
B.val("chiedi_tela('V5: la prova della guardia')")
time.sleep(0.8)
mandati_dopo = B.js("window.__b37_mandati")
chieste5 = B.js("window.__b37_chieste")
nuovi = len(mandati_dopo) - len(mandati_prima)
print("    --  V5: arrivi a `chiedi_tela` %d · messaggi sul canale prima %d, "
      "dopo %d ⇒ %d nuovi · `tela_spenta` = %s"
      % (len(chieste5), len(mandati_prima), len(mandati_dopo), nuovi,
         B.js("tela_spenta")), flush=True)
if not chieste5:
    print("    NO  ⛔ V5: la funzione non e' stata nemmeno chiamata: lo zero "
          "sui messaggi e' del BANCO, non del prodotto", flush=True)
    guasti += 1
elif nuovi == 0:
    print("    OK  V5: chiamata a voce SPENTA, la funzione VERA non ha mandato "
          "nessun `ADATTA_TELA` — la guardia e' stata attraversata, non "
          "aggirata", flush=True)
else:
    print("    NO  ⛔⛔ V5: a voce spenta la funzione VERA ha mandato %d "
          "`ADATTA_TELA` sul canale: la guardia di §7.1 NON tiene, e la pagina "
          "insiste con un compositore che ha gia' detto di non saperlo fare"
          % nuovi, flush=True)
    guasti += 1

# ⛔ E IL CONTROLLO POSITIVO DI V5, senza cui quello zero non vale niente: a
#    voce ACCESA la stessa funzione DEVE mandare.  Se non manda, a tacere non e'
#    la guardia — e' il banco.
B.val("tela_spenta = false; tela_chiesta_l = 0; tela_chiesta_a = 0;"
      " schermo.tela_l = 640; schermo.tela_a = 480; 'riacceso'")
mandati_prima = B.js("window.__b37_mandati")
B.val("chiedi_tela('V5: il controllo positivo, a voce ACCESA')")
time.sleep(0.8)
nuovi_acceso = len(B.js("window.__b37_mandati")) - len(mandati_prima)
if nuovi_acceso >= 1:
    print("    OK  V5 · controllo positivo: a voce ACCESA la stessa funzione "
          "manda %d `ADATTA_TELA` ⇒ lo zero di sopra e' della GUARDIA, non del "
          "canale finto" % nuovi_acceso, flush=True)
else:
    print("    NO  ⛔ V5 · controllo positivo: a voce ACCESA non e' partito "
          "NIENTE ⇒ lo zero di sopra e' del BANCO, e V5 non giudica", flush=True)
    guasti += 1

B.scrivi({"tipo": "voce-rifiuto", "motivo": 1, "righe": righe1,
          "richieste_dopo": chieste2, "congedi": B.js("window.__b37_congedi"),
          "v5_mandati_a_voce_spenta": nuovi,
          "v5_mandati_a_voce_accesa": nuovi_acceso},
         iniezione="si")

# --- V4: la scena del 16 agosto NON ESISTE PIU' -----------------------------
# ⛔⛔ QUESTA VERIFICA HA CAMBIATO SENSO IL 17 AGOSTO 2026, `DECISIONI.md`
#    §5.1-bis.  Chiedeva: «con `?adatta=segui` acceso, dopo un rifiuto la voce si
#    spegne o si continua a chiedere per sempre?» — e il 16 agosto trovo' il
#    difetto (`[M]` 5 richieste in 4 ridimensionamenti).
#
# ⭐ Adesso l'inseguimento e' USCITO dal prodotto, e con lui l'interruttore.  ⇒ La
#    domanda non e' piu' «la voce si spegne», e' **«la funzione e' davvero
#    uscita, anche con addosso l'indirizzo vecchio e un rifiuto?»**  L'atteso
#    passa da «zero richieste che passano la guardia» a **zero arrivi**.
#
# ⚠ E `?adatta=segui` si tiene APPOSTA: e' il segnalibro di chi aveva la pagina
#   di ieri.  Un valore che non esiste piu' deve valere il predefinito e non
#   riaccendere niente.
print("\n    --  V4 · l'indirizzo vecchio `?adatta=segui` non riaccende niente",
      flush=True)
try:
    B.com("location.hash = 'adatta=segui'; location.reload(); 'ricarico'", 3)
except Exception:
    pass
time.sleep(3)
if not B.aspetta_pagina(20):
    print("    NO  la pagina non e' tornata dopo il ricaricamento", flush=True)
    sys.exit(3)
time.sleep(1.5)
modo = B.val("ADATTA")
print("        `ADATTA` vale «%s» dopo il ricaricamento" % modo, flush=True)
B.val(PREPARA)
B.val(RIFIUTA % 1)
time.sleep(1.0)
B.val("window.__b37_chieste = []; window.__b37_r2 = 0;"
      " addEventListener('resize', function(){ window.__b37_r2++; });"
      " 'contatore acceso'")
g = B.geometria()
for i in range(4):
    B.ridimensiona(g["l"] - 10 * (i + 1), g["a"])
    time.sleep(0.5)
time.sleep(1.2)
dopo = B.js("window.__b37_chieste")
# ⛔⭐ IL CONTROLLO POSITIVO, e senza di lui lo zero qui sopra non vale niente:
#    «la funzione non c'e'» e «il banco non ha stimolato niente» hanno lo stesso
#    aspetto (`CODER.md` §3.10, §4.6).
# ⚠ Si chiama `chiedi_tela` e non piu' `tela_forse_chiedi()`: quest'ultima e'
#   uscita col fondo, e chiamarla darebbe un `ReferenceError` che il banco
#   leggerebbe come «zero richieste» — cioe' un verde per il motivo sbagliato.
diag = B.js("""({ resize: window.__b37_r2, sessione: !!schermo.sessione,
                  quadro: quadro_vista, adatta: ADATTA,
                  chiedi: typeof chiedi_tela,
                  fondo: typeof tela_forse_chiedi })""")
print("    --  controllo: %d resize arrivati · sessione=%s · quadro=%s · "
      "ADATTA=%s · chiedi_tela=%s · tela_forse_chiedi=%s"
      % (diag["resize"], diag["sessione"], diag["quadro"], diag["adatta"],
         diag["chiedi"], diag["fondo"]), flush=True)
if diag["fondo"] != "undefined":
    print("    NO  ⛔ `tela_forse_chiedi` ESISTE ANCORA: il fondo del "
          "ridimensionamento a caldo e' rientrato (§5.1-bis)", flush=True)
    guasti += 1
B.val("chiedi_tela('controllo positivo del banco')")
time.sleep(1.0)
positivo = B.js("window.__b37_chieste")
if len(positivo) <= len(dopo):
    print("    NO  ⛔ il controllo positivo NON scatta: la spia non vede "
          "nemmeno una richiesta chiamata a mano ⇒ lo zero qui sopra e' "
          "del BANCO, non del prodotto, e non si giudica niente", flush=True)
    guasti += 1
    dopo = None
elif diag["resize"] < 4:
    print("    NO  ⛔ solo %d resize su 4 sono arrivati alla pagina: lo "
          "zero e' del PALCO, non del prodotto" % diag["resize"], flush=True)
    guasti += 1
    dopo = None
if dopo is None:
    sys.exit(1)
B.scrivi({"tipo": "voce-segui-uscito", "modo": modo,
          "richieste_dopo_rifiuto": dopo}, iniezione="si")
if dopo:
    for c in dopo:
        print("        «%s» misura %s · guardia %s"
              % (c["perche"], c["misura"], c["spenta"]), flush=True)
    print("    NO  ⛔⛔ IL RIDIMENSIONAMENTO A CALDO E' RIENTRATO: %d arrivi a "
          "`chiedi_tela` dopo 4 ridimensionamenti — la funzione e' uscita dal "
          "prodotto il 17 agosto 2026 (`DECISIONI.md` §5.1-bis)" % len(dopo),
          flush=True)
    guasti += 1
else:
    print("    OK  V4: 4 resize arrivati, 0 arrivi a `chiedi_tela` — la tela "
          "non si tocca a sessione viva, nemmeno con l'indirizzo vecchio",
          flush=True)

sys.exit(1 if guasti else 0)
