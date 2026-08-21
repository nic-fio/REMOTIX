#!/usr/bin/env python3
"""07-b63-worker.py — ⭐ IL PERCORSO VIDEO DELLA PAGINA, misurato sulle DUE strade.

    python3 banchi/07-b63-worker.py --nomi            ⛔ il controllo che NON serve una macchina
    python3 banchi/07-b63-worker.py --certifica       ⛔ PRIMA di credergli: guasto innestato in una COPIA
    python3 banchi/07-b63-worker.py --giri 3          la misura vera, base ⇄ worker alternati

═══════════════════════════════════════════════════════════════════════════════
⛔ CHE COSA MISURA, E LE DUE `[?]` CHE DEVE CHIUDERE
═══════════════════════════════════════════════════════════════════════════════

`fasi/06` §7.2 ne lascia aperte due, e **stanno insieme**:

  1. ⏳ `?video=worker` non e' MAI stato esercitato — e il motivo scritto nel
     `PIANO.md` §1409 e' *«il credito degli stream unidirezionali di QUIC si
     esaurisce»*;
  2. ⏳ il costo di `createImageBitmap` non l'ha mai misurato nessuno, ed e' nel
     percorso di disegno di **tutti** i fotogrammi (§4.9: *«il ritardo che
     aggiunge non e' ancora misurato»*).

⇒ Qui si misurano tutt'e due **sulla catena vera**: server, filo, Firefox vero.

═══════════════════════════════════════════════════════════════════════════════
⛔ IL CONTROLLO CHE VALE PIU' DI TUTTI GLI ALTRI: `--nomi`
═══════════════════════════════════════════════════════════════════════════════

Il sorgente del worker si **COMPONE** (`sorgente_worker()`): costanti
serializzate + `Schermo.toString()` + `leggi_uno_stream.toString()`.  ⛔ Non c'e'
nessun `import` che possa fallire, quindi **un nome mancante non si vede finche'
non lo si esegue** — e allora si vede dentro una promessa che nessuno raccoglie,
cioe' non si vede affatto.

`[M]` 21 agosto 2026: mancavano **tre** nomi (`VIA_MSE`, `GIRO`, `SCENA`) e il
percorso dipingeva **zero** fotogrammi in perfetto silenzio.

⇒ `--nomi` legge `src/pagina.html`, estrae gli identificatori liberi di
  `Schermo` e `leggi_uno_stream`, e li confronta con quel che il worker mette a
  disposizione.  ⭐ Gira senza macchina di prova e senza browser, quindi puo'
  girare a ogni modifica della pagina.

═══════════════════════════════════════════════════════════════════════════════
⛔ COME SI TIENE ONESTO IL CONFRONTO
═══════════════════════════════════════════════════════════════════════════════

  1. ⭐ **la stessa scena, e in MOVIMENTO** — `07-b63-scena.sh`.  `[M]` sul
     desktop vuoto la pagina dipinge 13 fotogrammi in 30 s e poi niente: un
     confronto li' avrebbe misurato la scena, non le due strade;
  2. ⛔ **si ALTERNA** base, worker, base, worker: la macchina e' in dieci, e il
     carico si muove di minuto in minuto.  Due misure di fila sullo stesso lato
     misurerebbero anche la deriva del carico e la chiamerebbero differenza;
  3. ⛔ **il carico si scrive accanto a ogni numero**, delle DUE macchine;
  4. ⛔ **non basta `dipinti`**: un numero che sale sembra sempre sano.  Si
     leggono anche `saltati_coda`, `buchi`, `scartati_ordine`,
     `scartati_misura`, `tardive`, `errori` — e i rifiuti per credito del
     SERVER, che la pagina non puo' vedere;
  5. ⛔ **il banco si rifiuta di pubblicare un numero** se `consegnati` non e'
     cresciuto: senza fotogrammi la misura non e' bassa, e' assente.

⚠ E IL BUCO CIECO, dichiarato: qui NON si misura il ritardo cattura → vetro
  (quello e' `03-b17-ritardo.py`, che ha bisogno del ponte e dell'ancora
  dell'orologio).  Qui si misurano il TETTO e il costo del DISEGNO.
"""
import argparse
import importlib.util as _iu
import json
import os
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
ALBERO = os.path.dirname(QUI)
_spec = _iu.spec_from_file_location(
    "marionette", os.path.join(QUI, "07-b46-marionette.py"))
M = _iu.module_from_spec(_spec)
_spec.loader.exec_module(M)

VERDE, ROSSO, GRIGIO, FINE = "\033[1;32m", "\033[1;31m", "\033[2m", "\033[0m"


def ok(t):  print("    %sOK%s  %s" % (VERDE, FINE, t))
def ko(t):  print("    %sNO%s  %s" % (ROSSO, FINE, t))
def inf(t): print("    --  %s" % t)
def log(t): print("\n\033[1m== %s\033[0m" % t)


# ═══════════════════════════════════════════════════════════════════════════
# 1 · IL CONTROLLO DEI NOMI — gira senza niente
# ═══════════════════════════════════════════════════════════════════════════

PAROLE = set("""break case catch class const continue debugger default delete do else export
extends finally for function if import in instanceof let new return static super switch this
throw try typeof var void while with yield async await of get set null true false
constructor""".split())

MOTORE = set("""Math JSON Object Array String Number Boolean Promise Error Uint8Array
Uint8ClampedArray DataView ArrayBuffer Map Set WeakMap Date console performance setTimeout
clearTimeout setInterval clearInterval VideoDecoder VideoFrame EncodedVideoChunk
createImageBitmap ImageBitmap OffscreenCanvas isNaN parseInt parseFloat Infinity NaN undefined
self globalThis queueMicrotask structuredClone TextDecoder TextEncoder MediaSource SourceBuffer
URL Blob Function Symbol RegExp navigator""".split())


def senza_commenti(s):
    """⛔ Grezzo ma dichiarato: toglie /* */, // e il CONTENUTO delle stringhe.
    Le stringhe si svuotano invece di sparire, o `"a" + b` diventerebbe `+ b`."""
    fuori, i, n, modo = [], 0, len(s), "codice"
    while i < n:
        c = s[i]
        if modo == "codice":
            if c == "/" and i + 1 < n and s[i + 1] == "*":
                modo = "blocco"; i += 2; continue
            if c == "/" and i + 1 < n and s[i + 1] == "/":
                modo = "riga"; i += 2; continue
            if c in "\"'`":
                modo = c; fuori.append(" "); i += 1; continue
            fuori.append(c); i += 1
        elif modo == "blocco":
            if c == "*" and i + 1 < n and s[i + 1] == "/":
                modo = "codice"; i += 2; fuori.append(" "); continue
            fuori.append("\n" if c == "\n" else "")
            i += 1
        elif modo == "riga":
            if c == "\n":
                modo = "codice"; fuori.append("\n")
            i += 1
        else:
            if c == "\\":
                i += 2; continue
            if c == modo:
                modo = "codice"
            i += 1
    return "".join(fuori)


def liberi(codice):
    s = senza_commenti(codice)
    ids = set(re.findall(r'(?<![\w.$])([A-Za-z_$][\w$]*)', s))
    dich = set(re.findall(r'\b(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)', s))
    dich |= set(re.findall(r'\bcatch\s*\(\s*([A-Za-z_$][\w$]*)', s))
    return sorted(i for i in ids if i not in PAROLE and i not in MOTORE and i not in dich)


def pezzo(testo, inizio, fine):
    a = testo.index(inizio)
    b = testo.index(fine, a)
    return testo[a:b]


# ⛔ LE ESENZIONI SI DICHIARANO QUI, UNA PER UNA, CON LA RAGIONE — e sono
#    l'unica strada per far tacere questo controllo.  ⚠ Una lista di esenzioni
#    che si allunga da sola sarebbe il controllo che si spegne da solo.
ESENTI = {
    # `MuxMP4` e le quindici funzioni delle scatole MP4 NON attraversano il
    # confine, e non devono: si arriva a `MuxMP4` solo con `VIA_MSE` acceso, e
    # `pagina.html` RIFIUTA `?video=worker&disegno=mse` dicendolo.
    "MuxMP4": "raggiungibile solo con VIA_MSE, e le due strade insieme sono rifiutate",
    "MSE_SOGLIA_S": "idem — dentro `mse_insegui`",
    "MSE_FRETTA": "idem — dentro `mse_insegui`",
}


def controllo_nomi(pagina):
    """⭐ Ogni nome libero di `Schermo`/`leggi_uno_stream` deve essere fornito
    dal sorgente che il worker riceve.  Torna (esito, mancanti, usati, dati)."""
    t = open(pagina, encoding="utf-8").read()
    classe = pezzo(t, "class Schermo {", "\nfunction disposizione()")
    lettore = pezzo(t, "async function leggi_uno_stream(", "\n/* ═══")
    guscio = pezzo(t, "const GUSCIO_WORKER = `", "\n`;\n")
    comp = pezzo(t, "function sorgente_worker() {", "\n}\n")

    # quel che il guscio dichiara, piu' le costanti che `sorgente_worker`
    # serializza, piu' le funzioni che stampa con `.toString()`
    dati = set(re.findall(r'\b(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)', guscio))
    dati |= set(re.findall(r'"const\s+([A-Za-z_$][\w$]*)\s*=', comp))
    dati |= set(re.findall(r'(?:^|\s)([A-Za-z_$][\w$]*)\.toString\(\)', comp))

    # ⛔ I METODI DELLA CLASSE non sono globali: `componi() {` e' una
    #    dichiarazione, e senza questa riga ne uscivano quaranta falsi allarmi —
    #    ⚠ e un controllo che grida sempre e' un controllo che nessuno legge.
    metodi = set(re.findall(r'^  (?:async\s+|get\s+|set\s+)?([A-Za-z_$][\w$]*)\s*\(',
                            senza_commenti(classe), re.M))

    corpo = senza_commenti(classe) + "\n" + senza_commenti(lettore)
    tutti = (set(liberi(classe)) | set(liberi(lettore))) - metodi

    # ⛔ CHE COSA E' UN GLOBALE, e la regola e' scritta apposta larga in un verso
    #    e stretta nell'altro:
    #      · **maiuscola iniziale** — le costanti (`VIA_MSE`) e i registri
    #        (`GIRO`, `SCENA`) e le classi (`MuxMP4`) del progetto.  ⭐ Questo
    #        ramo prende i tre nomi che il 21 agosto mancavano davvero, e li
    #        prende ANCHE quando si usano come semplice VALORE — che e' il caso
    #        di `VIA_MSE ? a : b`, cioe' quello che una regola «solo `NOME.` o
    #        `NOME(`» avrebbe lasciato passare;
    #      · **chiamata nuda** `nome(` — le funzioni globali minuscole
    #        (`nota`, `dopo`, `differenza`, `misura_vista`, `congeda`).
    #    ⚠ Quel che resta fuori sono parametri, chiavi di oggetto e variabili
    #      locali: nomi minuscoli che non si chiamano mai.  ⛔ Il buco e'
    #      dichiarato: una funzione globale minuscola passata come VALORE
    #      (`setTimeout(pulisci, 0)`) non verrebbe vista.
    globali = set()
    for n in tutti:
        if n[0].isupper():
            globali.add(n)
        elif re.search(r'(?<![\w.$])' + re.escape(n) + r'\s*\(', corpo):
            globali.add(n)
    usati = sorted(globali)
    mancanti = sorted(n for n in usati if n not in dati and n not in ESENTI)
    return (not mancanti), mancanti, usati, sorted(dati)


# ═══════════════════════════════════════════════════════════════════════════
# 2 · LA MISURA SULLA CATENA VERA
# ═══════════════════════════════════════════════════════════════════════════

LETTURA = """
  const s = (window.REMOTIX && REMOTIX.schermo) || null;
  if (!s) return null;
  const v = (window.REMOTIX && REMOTIX.video) || null;
  const t = document.getElementById('schermo');
  return { conti: s.conti,
           formato: s.formato,
           /* ⛔⭐ LA TELA SI GUARDA DAI DUE VERSI — e la ragione viene dalla
              revisione avversariale di `06-b37` (21 agosto 2026): li' NESSUNA
              verifica sulla tela ha un limite INFERIORE, quindi una tela piu'
              PICCOLA del dovuto passa verde.  ⇒ Qui si pretende l'UGUAGLIANZA
              fra il buffer e la misura del fotogramma dipinto, non un «almeno». */
           /* ⚠ E sul percorso worker il buffer VERO non e' quello del nodo:
              la tela e' stata ceduta con `transferControlToOffscreen()`, e di
              qua il nodo resta a 16x16 per sempre.  ⇒ Si legge dallo specchio. */
           buffer: (v && v.tela) ? v.tela : [t.width, t.height],
           dipinta: s.dipinta ? [s.dipinta.l, s.dipinta.a] : null,
           /* ⛔ Sul percorso worker gli array veri stanno di la': il riassunto
              arriva con lo specchio.  Di qua si calcola dai campioni. */
           bmp: v ? v.bmp : riassunto(s.bmp_ms),
           vetro: v ? v.vetro : riassunto(s.vetro_ms),
           worker: v ? { pronto: v.pronto, flussi: v.flussi, rotto: !!v.rotto,
                         riscontro_fatto: !!v.riscontro_fatto } : null,
           /* ⭐ IL GIRO COMPLETO input → fotogramma: e' il numero di
              `CODER.md` §1-bis, tetto 50 ms.  ⚠ Sul percorso worker ci sta
              dentro un `postMessage` in piu' (il ritorno passa dal thread
              principale), e va detto accanto al numero. */
           giro: (window.REMOTIX && REMOTIX.giro)
                   ? { med: REMOTIX.giro.mediana(), peg: REMOTIX.giro.peggiore(),
                       visti: REMOTIX.giro.visti } : null,
           errori: s.errori.slice(-6) };
  function riassunto(a) {
    if (!a || !a.length) return null;
    const b = a.slice().sort((x, y) => x - y);
    return { n: b.length, med: b[Math.floor(b.length / 2)], peg: b[b.length - 1] };
  }
"""


def carico(macchina=None):
    if macchina:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", macchina, "cat /proc/loadavg"],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip().split(" ")[0] if r.returncode == 0 else "?"
    return open("/proc/loadavg").read().split(" ")[0]


def registro_server(a):
    """⛔ Quel che la PAGINA non puo' vedere: quanti stream il server ha aperto e
    quanti fotogrammi ha buttato per mancanza di credito."""
    c = ("L=%s/registro.log; "
         "echo aperti=$(grep -c 'aperto per un fotogramma' $L); "
         "echo senza_credito=$(grep -c 'ne concede ancora' $L); "
         "echo chiavi_attese=$(grep -c 'nessuno stream unidirezionale per una CHIAVE' $L); "
         "echo ultimo_stream=$(grep -o 'stream uni [0-9]* aperto' $L | tail -1 | "
         "  sed 's/stream uni //; s/ aperto//')") % a.lav
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", a.macchina, c],
                       capture_output=True, text=True, timeout=30)
    d = {}
    for riga in r.stdout.splitlines():
        if "=" in riga:
            k, v = riga.split("=", 1)
            d[k] = int(v) if v.strip().isdigit() else v.strip()
    return d


def azzera_registro(a):
    subprocess.run(["ssh", "-o", "BatchMode=yes", a.macchina,
                    "printf '%%s\\n' '%s' | sudo -S -p '' truncate -s 0 %s/registro.log"
                    % (a.parola_sudo, a.lav)],
                   capture_output=True, text=True, timeout=30)


_dove = [0]


def muovi(m, a):
    """Un giro di puntatore sulla pagina, con una pausa: e' l'input che fa
    esistere il numero di `GIRO`.  ⛔ Le coordinate sono relative alla
    FINESTRA (`origin: viewport`), e NON si sottrae nessuno scostamento —
    la revisione di `06-b37` ha trovato li' una misura azzerata per
    costruzione, e questo banco non la ripete: qui non si confronta «dove
    e' finito» con «dove la pagina crede», si conta soltanto il TEMPO."""
    _dove[0] = (_dove[0] + 1) % 8
    x = 200 + 90 * _dove[0]
    y = 250 + 40 * (_dove[0] % 4)
    try:
        m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse",
            "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "duration": 30,
                         "origin": "viewport", "x": x, "y": y},
                        {"type": "pause", "duration": 170}]}]})
    except Exception:
        time.sleep(0.2)


def un_giro(a, worker):
    """Un giro solo.  Torna un dizionario, o `None` se la misura non c'e'."""
    nome = "worker" if worker else "base"
    url = "https://%s:%d/%s" % (a.ind, a.porta, "?video=worker" if worker else "")
    azzera_registro(a)
    c0 = (carico(), carico(a.macchina))
    p, m, prof = M.accendi(porta=a.marionette, headless=True,
                           largo=a.larghezza, alto=a.altezza)
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(a.larghezza, a.altezza)
        m.vai(url)
        m.js("""
          document.getElementById('utente').value = arguments[0];
          document.getElementById('parola').value = arguments[1];
          document.getElementById('vai').click(); return true;
        """, [a.utente, a.parola])
        t0 = time.time()
        while time.time() - t0 < 30:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.4)
        else:
            ko("%s: lo schermo non si e' acceso in 30 s — NON pubblico un numero" % nome)
            # ⛔ E si stampa PERCHE': un rosso senza le righe della pagina manda
            #    a cercare nel posto sbagliato.  `[M]` la prima volta che questo
            #    ramo e' scattato, la causa non era il worker — era il POSTO
            #    ancora occupato dal giro precedente (§5.3, trenta secondi di
            #    silenzio prima che il server lo liberi).
            righe = m.js(
                "return document.getElementById('registro').innerText")["value"]
            # ⛔ Si cercano le righe che DICONO qualcosa, non le ultime: la coda
            #    del registro e' il racconto periodico, che a schermo spento e'
            #    una fila di zeri e non nomina nessuna causa.
            utili = [r for r in righe.splitlines()
                     if any(k in r.lower() for k in
                            ("sessione", "rifiut", "occupat", "⛔", "chiusa",
                             "negat", "codice"))]
            print(GRIGIO + "\n".join(utili[-8:]) + FINE)
            return None
        # ⛔ Un respiro prima di far partire il cronometro: i primi fotogrammi
        #    sono la configurazione del decodificatore, non il regime.
        time.sleep(a.riscaldamento)
        r0 = m.js(LETTURA)["value"]
        t_a = time.time()
        # ⛔⭐ E IL PUNTATORE SI MUOVE, o il giro completo non esiste.
        #    `GIRO` misura input → fotogramma che DICHIARA quell'input: senza
        #    input non e' un numero basso, e' un numero assente — la stessa
        #    forma della scena ferma, un piano piu' sotto.
        #    ⚠ Il movimento e' anche una perturbazione: si dichiara.  Sono ~5
        #      spostamenti al secondo, cioe' molto meno di quel che fa una mano.
        while time.time() - t_a < a.secondi:
            muovi(m, a)
        r1 = m.js(LETTURA)["value"]
        t_b = time.time()
        righe = m.js("return document.getElementById('registro').innerText.slice(-4000)")["value"]
        # ⛔⭐ IL POSTO SI LASCIA PRIMA DI SPEGNERE IL BROWSER, e non e' pulizia:
        #    ammazzando Firefox il server tiene il posto per i **trenta secondi**
        #    di silenzio di §5.3, e il giro dopo trova la sessione occupata.
        #    ⚠ `[M]` cosi' e' andata la prima volta: tre giri `base` verdi e tre
        #    `worker` che «non si accendono» — e non era il worker.
        #    ⇒ `about:blank` fa scattare il `pagehide` con cui la pagina rilascia
        #      da se', che e' la strada del PRODOTTO e non una scorciatoia mia.
        m.vai("about:blank")
        # ⛔ E si aspetta che il congedo ESCA: ammazzare Firefox l'istante dopo
        #    `about:blank` lascia il messaggio nella coda del trasporto, e il
        #    posto resta occupato per i trenta secondi di §5.3 lo stesso.
        time.sleep(1.5)
    finally:
        M.spegni(p, prof)
    time.sleep(a.respiro)
    c1 = (carico(), carico(a.macchina))
    srv = registro_server(a)
    dt = t_b - t_a
    d0, d1 = r0["conti"], r1["conti"]
    cons = d1["consegnati"] - d0["consegnati"]
    if cons <= 0:
        ko("%s: `consegnati` non e' cresciuto in %.1f s — la misura non e' bassa, "
           "E' ASSENTE.  NON pubblico un numero." % (nome, dt))
        return None
    # ⛔ LA TELA, DAI DUE VERSI: uguale, non «almeno».  Una tela piu' piccola
    #    del fotogramma e' il difetto che l'utente vede come «immagine stirata»
    #    e — peggio — come «i clic finiscono nell'angolo», perche'
    #    `cl_geometria()` divide per `tela.width`.
    tela_ok = (r1["dipinta"] is not None
               and list(r1["buffer"]) == list(r1["dipinta"]))
    if not tela_ok:
        ko("%s: ⛔ la tela NON e' uguale al fotogramma dipinto: buffer %s, "
           "fotogramma %s" % (nome, r1["buffer"], r1["dipinta"]))

    v = {"strada": nome, "secondi": round(dt, 2), "tela_uguale": tela_ok,
         "buffer": r1["buffer"], "fotogramma": r1["dipinta"],
         "consegnati_s": round(cons / dt, 2),
         "dipinti_s": round((d1["dipinti"] - d0["dipinti"]) / dt, 2),
         "delta": {k: d1[k] - d0.get(k, 0) for k in sorted(d1)},
         "bmp": r1["bmp"], "vetro": r1["vetro"], "giro_completo": r1["giro"],
         "worker": r1["worker"], "errori": r1["errori"],
         "server": srv,
         "carico_portatile": [c0[0], c1[0]], "carico_prova": [c0[1], c1[1]],
         "registro_coda": righe[-1200:]}
    return v


def stampa(v):
    d = v["delta"]
    print("    %-7s %6.1f/s dipinti · %6.1f/s consegnati · salt %d buchi %d ord %d "
          "mis %d tard %d err %d"
          % (v["strada"], v["dipinti_s"], v["consegnati_s"],
             d.get("saltati_coda", 0), d.get("buchi", 0), d.get("scartati_ordine", 0),
             d.get("scartati_misura", 0), d.get("tardive", 0), d.get("errori", 0)))
    b, g = v["bmp"], v["vetro"]
    print("            createImageBitmap  mediana %s ms · peggiore %s ms (su %s) "
          "· transferFromImageBitmap mediana %s ms"
          % (("%.2f" % b["med"]) if b else "—", ("%.2f" % b["peg"]) if b else "—",
             b["n"] if b else 0, ("%.3f" % g["med"]) if g else "—"))
    s = v["server"]
    print("            server: %s stream aperti · %s fotogrammi senza credito · "
          "%s chiavi aspettate" % (s.get("aperti"), s.get("senza_credito"),
                                   s.get("chiavi_attese")))
    gc = v["giro_completo"]
    print("            giro completo input → fotogramma: mediana %s ms · "
          "peggiore %s ms (su %s comandi) — tetto 50 ms"
          % (("%.0f" % gc["med"]) if gc and gc["med"] is not None else "—",
             ("%.0f" % gc["peg"]) if gc and gc["peg"] is not None else "—",
             gc["visti"] if gc else 0))
    print("            tela %s == fotogramma %s : %s"
          % (v["buffer"], v["fotogramma"],
             (VERDE + "si" + FINE) if v["tela_uguale"] else (ROSSO + "NO" + FINE)))
    print("            %scarico portatile %s→%s · prova %s→%s%s"
          % (GRIGIO, v["carico_portatile"][0], v["carico_portatile"][1],
             v["carico_prova"][0], v["carico_prova"][1], FINE))
    if v["worker"]:
        print("            %sworker: pronto=%s flussi=%s rotto=%s riscontro_fatto=%s%s"
              % (GRIGIO, v["worker"]["pronto"], v["worker"]["flussi"],
                 v["worker"]["rotto"], v["worker"]["riscontro_fatto"], FINE))


def main():
    a_ = argparse.ArgumentParser()
    a_.add_argument("--ind", default="192.168.0.2")
    a_.add_argument("--porta", type=int, default=7771)
    a_.add_argument("--macchina", default="nicfio@192.168.0.2")
    a_.add_argument("--parola-sudo", default="nicfio")
    a_.add_argument("--lav", default="/media/REMOTIX/tmp/07-v")
    a_.add_argument("--utente", default="provav7")
    a_.add_argument("--parola", default="provav7-2026")
    a_.add_argument("--secondi", type=float, default=20)
    a_.add_argument("--riscaldamento", type=float, default=3)
    a_.add_argument("--respiro", type=float, default=3,
                    help="il respiro fra un giro e l'altro, perche' il posto si liberi")
    a_.add_argument("--giri", type=int, default=2)
    a_.add_argument("--larghezza", type=int, default=1600)
    a_.add_argument("--altezza", type=int, default=1000)
    a_.add_argument("--marionette", type=int, default=2863)
    a_.add_argument("--pagina", default=os.path.join(ALBERO, "src", "pagina.html"))
    a_.add_argument("--fuori", default="/tmp/07-b63")
    a_.add_argument("--nomi", action="store_true")
    a_.add_argument("--certifica", action="store_true")
    a = a_.parse_args()

    if a.nomi or a.certifica:
        log("Il controllo dei nomi — `Schermo` contro quel che il worker riceve")
        esito, mancanti, globali, dati = controllo_nomi(a.pagina)
        inf("nomi globali usati da `Schermo`/`leggi_uno_stream`: %s" % ", ".join(globali))
        inf("nomi che il worker riceve: %s" % ", ".join(dati))
        if esito:
            ok("nessun nome manca")
        else:
            ko("⛔ MANCANO: %s — il worker si rompera' MUTO al primo fotogramma"
               % ", ".join(mancanti))
        if not a.certifica:
            return 0 if esito else 3

        # ═══════════════════════════════════════════════════════════════════
        # ⛔ LA CERTIFICAZIONE: il guasto si innesta in una COPIA, mai nel
        #    prodotto.  Se il banco non accusa la copia guasta, il suo verde
        #    sulla copia sana non vale niente (`PIANO.md` §0.3.4).
        # ═══════════════════════════════════════════════════════════════════
        log("La certificazione — guasto innestato in una COPIA")
        os.makedirs(a.fuori, exist_ok=True)
        t = open(a.pagina, encoding="utf-8").read()
        for nome, riga in (("VIA_MSE", '    "const VIA_MSE = " + JSON.stringify(VIA_MSE) + ";",\n'),
                           ("GIRO", "const GIRO = { torna: function (id)")):
            if riga not in t:
                ko("il guasto «%s» non si puo' innestare: la riga non c'e' piu' "
                   "(⇒ il banco NON e' certificato)" % nome)
                return 3
        # ⛔ guasto 1 — una costante tolta dalla composizione: e' il difetto
        #    VERO del 21 agosto, e si usa come VALORE (`VIA_MSE ? a : b`), cioe'
        #    la forma che una regola «solo `NOME.` o `NOME(`» non vedrebbe.
        g1 = t.replace('    "const VIA_MSE = " + JSON.stringify(VIA_MSE) + ";",\n', "")
        # ⛔ guasto 2 — un registro tolto dal guscio.
        g2 = re.sub(r'const GIRO = \{ torna: function \(id\)[^\n]*\n', "", t)
        # ⛔⭐ guasto 3 — IL PIU' IMPORTANTE, ed e' quello che GUARDA AVANTI: un
        #     nome NUOVO che qualcuno aggiunge domani a `Schermo` senza farlo
        #     attraversare il confine.  ⚠ Gli altri due provano che il banco
        #     vede il difetto di IERI; questo prova che vedra' quello di domani.
        g3 = t.replace("      SCENA.dipinto();\n      if (this.sessione",
                       "      SCENA.dipinto();\n      DOMANI.qualcosa();\n      if (this.sessione")
        if g3 == t:
            ko("il guasto «nome nuovo» non si e' potuto innestare (⇒ NON certificato)")
            return 3
        for nome, testo in (("VIA_MSE tolto", g1), ("GIRO tolto", g2),
                            ("un nome NUOVO in `Schermo` (DOMANI)", g3)):
            f = os.path.join(a.fuori, "copia-guasta.html")
            open(f, "w", encoding="utf-8").write(testo)
            e, manc, _, _ = controllo_nomi(f)
            if e:
                ko("⛔ guasto «%s»: il banco NON lo vede ⇒ NON CERTIFICATO" % nome)
                return 3
            ok("guasto «%s»: accusato — mancano %s" % (nome, ", ".join(manc)))
        ok("⭐ il banco sa vedere il difetto che cerca")
        return 0

    log("La misura sulla catena vera — %d giri per lato, %.0f s ciascuno"
        % (a.giri, a.secondi))
    inf("⚠ la scena deve essere VIVA: `bash banchi/07-b63-scena.sh avvia`")
    esiti = []
    for g in range(a.giri):
        for worker in (False, True):          # ⛔ alternati, non a blocchi
            v = un_giro(a, worker)
            if v:
                v["giro"] = g + 1
                esiti.append(v)
                stampa(v)
    if not esiti:
        ko("nessun giro ha prodotto una misura")
        return 3

    log("Il verdetto")
    for strada in ("base", "worker"):
        g = [v for v in esiti if v["strada"] == strada]
        if not g:
            ko("%s: nessun giro" % strada); continue
        dip = sorted(v["dipinti_s"] for v in g)
        bmp = [v["bmp"]["med"] for v in g if v["bmp"]]
        inf("%-7s dipinti/s %s (mediana %.1f) · createImageBitmap mediana %s ms"
            % (strada, [round(x, 1) for x in dip], dip[len(dip) // 2],
               ("%.2f" % (sorted(bmp)[len(bmp) // 2])) if bmp else "—"))
    os.makedirs(a.fuori, exist_ok=True)
    fj = os.path.join(a.fuori, "07-b63-esiti.json")
    json.dump(esiti, open(fj, "w"), indent=1, ensure_ascii=False)
    inf("esiti: %s" % fj)
    return 0


if __name__ == "__main__":
    sys.exit(main())
