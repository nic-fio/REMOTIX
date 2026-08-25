#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b2-browser — ⭐⭐ IL BROWSER VERO, e i due `[?]` che solo un motore vero
                 puo' chiudere (incarico 10-b2, fase 10).

    porta 8120 · utenti `provadec1` (1100) e `provadec1b` (1123)
    albero /media/REMOTIX/src/10b2-src · lavoro /media/REMOTIX/tmp/10b2
    unita' remotix-8120 · lucchetto GPU `10-b2`

═══════════════════════════════════════════════════════════════════════════
LE DUE DOMANDE, E PERCHE' IL CLIENTE DI PROVA NON LE PUO' CHIUDERE
═══════════════════════════════════════════════════════════════════════════

`[?]` 1 — `--scena viva`.  Il primo giro ha misurato, **col cliente di prova
    `aioquic`**, che su un desktop FERMO, linea pulita, perdita ZERO, la
    sessione viene chiusa dopo 10 s, e il prodotto scrive da se':

        linea-morta causa=silenzio silenzio_ms=10004 prove=16 persi=0 permille=0

    ⭐ Il meccanismo: la cura del **silenzio dell'audio** (fase 9) ha tolto il
    traffico che teneva il cliente a rispondere, e la **linea morta** — tarata
    quando quel traffico c'era — sfratta chi non ha piu' niente da dire.
    ⛔ Ma un browser vero potrebbe tenersi vivo da se': QUIC ha i suoi `PING`, e
    Gecko li manda o non li manda secondo regole sue.  ⇒ *«Mai staccare»* e'
    l'unico obbligo che vale ovunque, e prima di dire che il prodotto lo rompe
    bisogna guardarlo su un motore vero.

`[?]` 2 — `--scena capsula`.  Il primo giro, sul rifiuto a tabella piena: **10
    chiusure ARMATE, 0 capsule messe in coda**, e la connessione QUIC terminata
    con **0**, che `RCP.md` §3.1 dice *«NON DEVE essere usato»*.  Il meccanismo
    ha un nome: `chiudi_sessione()` rimanda la capsula di 500 ms
    (`WT_ATTESA_CHIUSURA_NS`, la cura di B11), e un cliente che si stacca
    appena letto il `CONGEDO` se ne va ~2 ms dopo.  `[?]` Un browser che NON si
    stacca la riceve: misurato **1 volta su 1**, mai ripetuto.

═══════════════════════════════════════════════════════════════════════════
⛔⭐ DOVE SI LEGGE OGNI COSA — e questa e' la meta' che vale del banco
═══════════════════════════════════════════════════════════════════════════

| grandezza | dove si legge | perche' NON altrove |
|---|---|---|
| la sessione e' viva o chiusa | **nel browser** (`#registro` della pagina, con l'ora messa da un `MutationObserver`) | il registro del server dice che LUI ha chiuso, non che il browser se ne sia accorto |
| ⛔ **la capsula di chiusura** | **nel browser**: `wt.closed` che si RISOLVE con un `closeCode` e' la capsula arrivata; `wt.closed` che RIFIUTA e' la connessione morta senza capsula | il registro del server dice *«messa in coda»*: e' dove PARTE, non dove ARRIVA |
| chi tiene viva la linea | **sul filo**, `10-b2-filo.py`, pacchetto per pacchetto, i due versi separati | dedurlo dal comportamento e' indovinare |
| lo schermo era davvero fermo | **nel browser**: `schermo.conti.consegnati` e `dipinti`, piu' i byte s2c del filo | «sopravvissuta» perche' qualcosa si muoveva non prova niente |
| il MOTIVO della chiusura | nel registro del server (`linea-morta causa=…`) | ⛔ e si legge IL MOTIVO, non il fatto che sia finita: una sessione chiusa da un ban o da un server spento NON e' una linea morta |

⛔⛔ E il terzo esito esiste: **«non ho misurato»**.  Un browser che non si e'
     mai collegato non ha *«sopravvissuto»*: ha *«non misurato»*.  E' la forma
     che in fase 9 ha prodotto nove difetti su nove (`LEZIONI.md` §1.29).

⚠ DOVE GIRA FIREFOX: sul **portatile** (192.168.0.3, e ci arriva per **Wi-Fi**,
  `wlo1`), non sulla macchina di prova.  ⭐ Cosi' non aggiunge carico alla GPU
  che gli altri banchi stanno misurando; ⛔ ma il percorso NON e' un cavo, e
  «linea pulita» qui vuol dire «nessun `netem` messo da me», non «perdita zero
  garantita».  Il filo lo dice: i pacchetti persi FRA il punto di cattura e il
  browser questo metro non li vede (buco 4 di `10-b2-filo.py`).

⭐ E C'E' UNA TERZA SCENA CHE NON ERA NEL MANDATO — `--scena finestra`.  L'ha
  prodotta il banco stesso, sbattendoci contro al primo giro: con la finestra
  che Firefox apre di suo la sessione moriva a 1,3 s perche' **il figlio veniva
  ucciso dal segnale 11**.  Il riquadro sopra `scena_finestra` porta il registro
  del server per intero.

Uso:
    python3 banchi/10-b2-browser.py --certifica
    python3 banchi/10-b2-browser.py --scena taratura     # ⛔ il metro, PRIMA
    python3 banchi/10-b2-browser.py --scena viva --durata 120
    python3 banchi/10-b2-browser.py --scena viva --durata 120 --senza-audio-silenzio
    python3 banchi/10-b2-browser.py --scena finestra --giri 5
    python3 banchi/10-b2-browser.py --scena capsula --giri 10

⭐ Tutta la campagna in ordine, col lucchetto GIA' in mano:
    bash banchi/10-b2-lancia.sh
"""
import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "8120"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10b2-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10b2")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10b2-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10b2")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
IFACCIA = os.environ.get("IFACCIA", "enp7s0")
IO_SONO = os.environ.get("IO_SONO", "192.168.0.3")
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "b2-browser-2026")
FUORI = os.environ.get("FUORI", "/tmp/10-b2")

UTENTE_A = ("provadec1", 1100)      # chi entra
UTENTE_B = ("provadec1b", 1123)     # chi viene respinto a tabella piena

MOTIVO_PIENO = 0x0E                 # «il registro delle sessioni e' pieno»
MOTIVO_VIETATO = 0x00               # ⛔ §3.1: «NON DEVE essere usato»


def _log(t):
    print("\n\033[1m== %s\033[0m" % t, flush=True)


def _ok(t):
    print("    \033[1;32mOK\033[0m  %s" % t, flush=True)


def _ko(t):
    print("    \033[1;31mNO\033[0m  %s" % t, flush=True)


def _dub(t):
    print("    \033[1;33m??\033[0m  %s" % t, flush=True)


def _inf(t):
    print("    --  %s" % t, flush=True)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def catena_root(cmd):
    return ("printf '%%s\\n' %s | sudo -S -p '' bash -c %s"
            % (shlex.quote(PAROLA_SUDO), shlex.quote(cmd)))


def root(cmd, tetto=120):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, catena_root(cmd)],
                       capture_output=True, text=True, timeout=tetto)
    return p.returncode, p.stdout, p.stderr


def righe_registro():
    """Quante righe ha il registro del server ADESSO.

    ⛔ `None` se non l'ho potuto leggere: un `0` qui vorrebbe dire «registro
       vuoto», e farebbe rileggere tutto il passato come se fosse di adesso.
    """
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    s = (out or "").strip().splitlines()
    s = s[-1].strip() if s else ""
    return int(s) if s.isdigit() else None


def opzioni_del_server():
    """⛔⛔ LE CURE CHE IL SERVER HA DAVVERO ADDOSSO, lette dal suo `argv`.

    ⭐ `CODER.md` §2-bis: le cure della fase 9 nascono ACCESE, e un banco che
       confronta col passato **le spegne a mano e lo dichiara**.  ⚠ Dichiararlo
       nella riga di comando del BANCO non basta: il banco non accende il
       server, lo accende il terreno.  ⇒ Si legge `/proc/<pid>/cmdline` del
       processo che sta ascoltando, e ⛔ se non si legge si torna `None`.
    """
    rc, out, _ = root("p=$(systemctl show -p MainPID --value %s.service); "
                      "[ -n \"$p\" ] && [ \"$p\" != 0 ] && "
                      "tr '\\0' ' ' < /proc/$p/cmdline" % UNITA)
    if rc != 0 or not out or "remotix" not in out:
        return None
    return out.strip()


def registro_da(riga0):
    """Il registro DALLA riga `riga0` in poi.

    ⛔ Con `sed`, non con `tail -n`: `10-b93` ha pagato quel `tail`, che sotto
       migliaia di righe PERDEVA la riga che si stava aspettando.
    """
    if riga0 is None:
        return None
    rc, out, _ = root("sed -n '%d,$p' %s/registro.log" % (riga0 + 1, LAV))
    return out if rc == 0 else None


def pagina_servita():
    """⭐ La pagina COME IL SERVER LA SERVE, presa dal filo.

    ⛔ Non `src/pagina.html` del repository e nemmeno il file sull'albero: si
       chiede al server, perche' la sola voce che conta e' quella che l'utente
       scarica.  ⚠ Un albero ricompilato a meta', un `--pagina` che punta
       altrove, una copia vecchia: tutte e tre danno un file giusto sul disco e
       una pagina sbagliata sul filo.

    ⛔ `None` se non l'ho potuta leggere — e `None` non e' «pagina vuota».
    """
    p = subprocess.run(["curl", "-sk", "--max-time", "20",
                        "https://%s:%d/" % (IND, PORTA)],
                       capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout or "MOTIVO" not in p.stdout:
        return None
    return p.stdout


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL BROWSER VERO — Firefox 140 ESR sul portatile, guidato da Marionette
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ L'OSSERVATORE SI INSTALLA PRIMA DEL CLIC, non dopo: le righe che contano —
#    «sessione WebTransport aperta», «sessione chiusa dal server: codice N» —
#    escono nei primi millisecondi, e un osservatore installato dopo le
#    troverebbe senza ora.  ⚠ E l'ora la mette la PAGINA (`Date.now()`), non
#    io: fra il momento in cui la riga compare e il momento in cui io la leggo
#    ci sono i giri di Marionette, che valgono decine di millisecondi e sono
#    proprio la grandezza che questo banco misura (500 ms di attesa).
OSSERVATORE = r"""
window.__b2b = { righe: [], esiti: [], schermo: [] };
const R = document.getElementById('registro');
const E = document.getElementById('esito');
function __prendi() {
  const t = Date.now();
  const l = (R.textContent || "").split("\n");
  while (window.__b2b.righe.length < l.length)
    window.__b2b.righe.push({ t: t, riga: l[window.__b2b.righe.length] });
}
new MutationObserver(__prendi).observe(R,
  { childList: true, characterData: true, subtree: true });
new MutationObserver(function () {
  const s = (E.textContent || "").trim();
  const u = window.__b2b.esiti;
  if (s && (!u.length || u[u.length - 1].testo !== s))
    u.push({ t: Date.now(), testo: s });
}).observe(E, { childList: true, characterData: true, subtree: true });
new MutationObserver(function () {
  const s = document.body.dataset.schermo || "(nessuno)";
  const u = window.__b2b.schermo;
  if (!u.length || u[u.length - 1].valore !== s)
    u.push({ t: Date.now(), valore: s });
}).observe(document.body, { attributes: true, attributeFilter: ['data-schermo'] });
__prendi();
return true;
"""

LEGGI = r"""
let conti = null;
try {
  const s = window.REMOTIX && window.REMOTIX.schermo;
  if (s && s.conti) conti = JSON.parse(JSON.stringify(s.conti));
} catch (e) { conti = null; }
return { righe: window.__b2b.righe, esiti: window.__b2b.esiti,
         schermo: window.__b2b.schermo,
         schermo_ora: document.body.dataset.schermo || null,
         crudo: (document.getElementById('registro').textContent || ""),
         conti: conti, t: Date.now() };
"""

# ⛔⛔ E IL TESTO CRUDO NON E' UN LUSSO — `[M]` 24 agosto 2026, e me l'ha
#     insegnato il banco stesso.  L'osservatore ha **perso due righe** — «apro
#     https://…» e «sessione WebTransport aperta» — che la pagina aveva scritto
#     davvero: `nota()` riscrive tutto `textContent`, e due riscritture nello
#     stesso giro di eventi arrivano al `MutationObserver` come **una sola**
#     mutazione con l'indice gia' avanti.  ⚠ Il sintomo era la forma peggiore:
#     il banco diceva *«in 90 s la sessione non si e' aperta»* su una sessione
#     che si era aperta in 1,1 s.
#
# ⇒ La regola che ne esce: **la PRESENZA si legge dal testo crudo, l'ORA
#   dall'osservatore.**  L'osservatore puo' perdere una riga; il testo crudo no.
#   Un'ora mancante e' un `None` dichiarato; una riga mancante era un verdetto
#   sbagliato.


# ⛔⛔ LA LARGHEZZA CHE CONTA E' `clientWidth`, NON `innerWidth` — e fra le due
#     ci sono i 12 px della barra di scorrimento.  `[M]` 24 agosto 2026: con la
#     finestra portata a `innerWidth = 1280` la pagina ha continuato a chiedere
#     una tela di **1268**, cioe' un passo di 5072 — non multiplo di 64 — e il
#     figlio e' morto lo stesso.  ⇒ Si insegue la grandezza che il prodotto
#     usa davvero (`misura_vista()` della pagina), non quella che le somiglia.
MISURE = ("return [window.outerWidth, window.outerHeight, "
          "document.documentElement.clientWidth, "
          "document.documentElement.clientHeight, "
          "window.innerWidth, window.innerHeight];")

REGOLA_TELA = r"""
const l = arguments[0], a = arguments[1];
return { outer: [window.outerWidth, window.outerHeight],
         inner: [window.innerWidth, window.innerHeight],
         dpr: window.devicePixelRatio || 1 };
"""


class Browser(object):
    """⛔ Un Firefox vero, e se non parte lo si DICHIARA invece di ripiegare."""

    def __init__(self, porta_mar=2860, headless=True):
        self.M = _carica("b46mar", os.path.join(QUI, "07-b46-marionette.py"))
        self.p, self.mar, self.prof = self.M.accendi(
            porta=porta_mar, headless=headless, largo=1280, alto=800)
        self.mar.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})

    def finestra(self, inner_l, inner_a):
        """⛔⛔ LA MISURA DELLA FINESTRA NON E' UN DETTAGLIO DI COMODO.

        `[M]` 24 agosto 2026, e l'ha trovato questo banco per caso: con la
        finestra che Marionette apre di suo la pagina chiede una tela di
        **1268×714**, il passo del DMA-BUF diventa **5072** — che non e'
        multiplo di 64 — il figlio rimonta il palco sulla memoria e **muore di
        SIGSEGV**.  ⇒ Nessuna sessione, nessuna misura.

        ⚠ Il difetto e' del PRODOTTO e si riferisce a parte; qui la finestra si
          porta a una misura in cui il difetto non morde, e **lo si dichiara**:
          i numeri di questo banco valgono per una tela larga un multiplo di 16.
        """
        # ⛔⛔ E SI ASPETTA CHE LA PAGINA SI SIA POSATA PRIMA DI MISURARLA.
        #     `[M]` 24 agosto 2026: subito dopo `Navigate` la finestra dice
        #     `inner == outer == 1280`; un attimo dopo compare la barra di
        #     scorrimento e `inner` diventa **1268**.  ⇒ Un ciclo che si ferma
        #     alla prima lettura crede di aver messo 1280 e la pagina chiede
        #     1268 — e 1268×4 = 5072, che NON e' multiplo di 64.
        # ⛔⛔ SI INSEGUE SOLO LA LARGHEZZA, e la ragione e' misurata:
        #     lo schermo virtuale e' **1366×768**, e chiedere una finestra
        #     INTERNA alta 720 vorrebbe dire una finestra esterna alta ~806 —
        #     che non ci sta, viene tagliata, e il ciclo non converge MAI.
        #     Inseguendo tutt'e due, la larghezza non arrivava mai a posto e la
        #     tela restava 1268 (passo 5072, non multiplo di 64).
        #     ⭐ E la larghezza e' la sola che conta per il passo: il passo del
        #       DMA-BUF e' `larghezza × 4`.
        d = None
        time.sleep(2.5)   # ⛔ la barra di scorrimento compare DOPO il carico
        for _ in range(8):
            time.sleep(0.8)
            d = self.mar.js(MISURE)["value"]
            if d[2] == inner_l:
                return d
            self.mar.misura(d[0] + (inner_l - d[2]), inner_a)
        return d

    def carica(self, inner_l=1280, inner_a=720):
        self.mar.vai("https://%s:%d/" % (IND, PORTA))
        d = self.finestra(inner_l, inner_a)
        # ⛔ E SI RILEGGE UN'ULTIMA VOLTA, subito prima di installare
        #    l'osservatore: quel che conta e' la larghezza che la pagina avra'
        #    quando chiedera' la tela, non quella che aveva quando gliel'ho
        #    imposta.
        time.sleep(0.8)
        d = self.mar.js(MISURE)["value"]
        self.mar.js(OSSERVATORE)
        return d

    def larghezza_dentro(self):
        return self.mar.js("return window.innerWidth")["value"]

    def entra(self, utente, parola):
        t = time.time()
        self.mar.js("""document.getElementById('utente').value = arguments[0];
                       document.getElementById('parola').value = arguments[1];
                       document.getElementById('vai').click(); return Date.now();""",
                    [utente, parola])
        return t

    def leggi(self):
        return self.mar.js(LEGGI)["value"]

    def spegni(self):
        try:
            self.M.spegni(self.p, self.prof)
        except Exception:
            pass


def c_e(oss, modello):
    """⭐ LA PRESENZA, dal testo CRUDO del registro della pagina.

    Torna `True`/`False`, e ⛔ `None` se non ho letto niente: «non l'ho vista»
    e «non c'era» non sono la stessa cosa.
    """
    if not oss or oss.get("crudo") is None:
        return None
    return modello in oss["crudo"]


def riga_crudo(oss, modello):
    """La prima riga del testo crudo che contiene `modello` (o `None`)."""
    if not oss or oss.get("crudo") is None:
        return None
    for l in oss["crudo"].split("\n"):
        if modello in l:
            return l
    return None


def riga_con(oss, modello):
    """⚠ La riga CON L'ORA, dall'osservatore — e puo' mancare anche quando la
       riga c'e' (vedi il riquadro sopra `REGOLA_TELA`).  ⇒ Si usa **solo per
       il tempo**, mai per decidere se una cosa e' successa."""
    if not oss or oss.get("righe") is None:
        return None
    for r in oss["righe"]:
        if modello in (r.get("riga") or ""):
            return r
    return None


def quando(oss, modello):
    """L'ora della riga, in secondi, oppure `None` se l'osservatore l'ha persa."""
    r = riga_con(oss, modello)
    return (r["t"] / 1000.0) if r else None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐ I GIUDIZI — funzioni pure, cosi' i guasti si innestano senza rete
# ═══════════════════════════════════════════════════════════════════════════
CHIUSA_SERVER = "sessione chiusa dal server: codice "
CHIUSA_ERRORE = "sessione chiusa con errore"
CHIUSA_PAGINA = "sessione chiusa da questa pagina"
APERTA = "sessione WebTransport aperta"


def esito_del_browser(oss):
    """⛔⭐ COME E' FINITA, LETTA DOVE ARRIVA — il cuore del banco.

    Torna un dizionario con:
      `come`  · `"capsula"`   la capsula `CLOSE_WEBTRANSPORT_SESSION` e'
                              ARRIVATA: `wt.closed` si e' RISOLTA e la pagina
                              ha scritto il codice che portava;
              · `"errore"`    `wt.closed` ha RIFIUTATO: la sessione e' finita
                              **senza** capsula (connessione QUIC chiusa,
                              inattivita', trasporto rotto);
              · `"pagina"`    a chiudere e' stata la pagina stessa;
              · `"viva"`      non e' finita;
              · `None`        ⛔ NON HO MISURATO — la sessione non si e' mai
                              aperta, o non ho letto niente.
      `codice` il codice applicativo, quando c'e' (⚠ `None` se la pagina ha
               scritto `?`, che vuol dire «non me l'hanno detto»)
      `t`      l'ora della riga, messa dalla pagina

    ⚠ La distinzione fra `capsula` ed `errore` NON e' un'opinione: e' quel che
      la piattaforma promette.  `wt.closed` si risolve **solo** su un
      `CLOSE_WEBTRANSPORT_SESSION`; qualunque altra fine la fa rifiutare.  ⭐ E
      questo banco la TARA lo stesso, invece di crederci (vedi `taratura`).
    """
    if c_e(oss, APERTA) is None:
        return {"come": None, "perche": "non ho letto niente dal browser"}
    if not c_e(oss, APERTA):
        return {"come": None,
                "perche": "la sessione WebTransport non si e' mai aperta"}
    l = riga_crudo(oss, CHIUSA_SERVER)
    if l is not None:
        s = (l.split(CHIUSA_SERVER, 1)[1] or "").strip()
        cod = int(s) if re.match(r"^\d+$", s) else None
        return {"come": "capsula", "codice": cod,
                "t": quando(oss, CHIUSA_SERVER), "riga": l}
    l = riga_crudo(oss, CHIUSA_PAGINA)
    if l is not None:
        return {"come": "pagina", "codice": None,
                "t": quando(oss, CHIUSA_PAGINA), "riga": l}
    l = riga_crudo(oss, CHIUSA_ERRORE)
    if l is not None:
        return {"come": "errore", "codice": None,
                "t": quando(oss, CHIUSA_ERRORE), "riga": l}
    return {"come": "viva", "codice": None}


CAUSA = re.compile(r"linea-morta\s+(\S+)\s+causa=(\S+)\s+"
                   r"stallo_ms=(\d+)\s+soglia_stallo_ms=(\d+)"
                   r".*?silenzio_ms=(\d+)", re.S)


def causa_dal_server(testo):
    """⛔ IL MOTIVO, NON IL FATTO.  Legge la riga che il prodotto scrive da se'.

    Torna `{"causa": …, "silenzio_ms": …, "riga": …}` oppure `None` se quella
    riga non c'e'.  ⚠ `None` NON vuol dire «non e' stata la linea morta»: vuol
    dire «il prodotto non l'ha detto», e chi chiama deve dirlo cosi'.
    """
    if testo is None:
        return None
    for l in testo.splitlines():
        if "linea-morta " in l and "causa=" in l:
            m = re.search(r"causa=(\S+)", l)
            s = re.search(r"silenzio_ms=(\d+)", l)
            pe = re.search(r"permille=(\d+)", l)
            pr = re.search(r"prove=(\d+)", l)
            pp = re.search(r"persi=(\d+)", l)
            return {"causa": m.group(1) if m else None,
                    "silenzio_ms": int(s.group(1)) if s else None,
                    "permille": int(pe.group(1)) if pe else None,
                    "prove": int(pr.group(1)) if pr else None,
                    "persi": int(pp.group(1)) if pp else None,
                    "riga": l.strip()}
    return None


# ⛔ Le altre strade per cui una sessione finisce, e che NON sono la linea
#    morta.  Contarle come «linea morta» e' il guasto che il `--certifica`
#    innesta: si legge IL MOTIVO, non il fatto che sia finita.
ALTRE_FINI = (
    ("parola sbagliata", ("credenziali", "autenticazione fallita", "RESPINTO 0x07")),
    # ⛔⛔ «BANNATO» NUDO NON VA BENE, ed e' costato un giro intero di campagna:
    #     il server scrive «NON-BANNATO» nella sua riga di saluto, e il modello
    #     `"BANNATO"` ci finisce dentro.  ⇒ Tre sessioni sane sono state
    #     dichiarate «non misurate perche' il registro nomina: bannato».
    #     ⚠ E' la forma opposta a quella che si teme di solito: non un verde
    #     falso, un ROSSO falso — ma costa lo stesso la misura.
    ("bannato", ("e' BANNATO", "ban di §4.4-bis", "BANNATO per")),
    ("server spento", ("il server si spegne", "SIGTERM", "in chiusura")),
    ("tabella piena", ("e' PIENO (", "registro delle sessioni",)),
    ("posto occupato", ("posto occupato", "gia' collegato")),
    ("inattivita' §2.2", ("trenta secondi di silenzio",)),
)


def perche_finita(testo_server):
    """Tutte le ragioni di fine che il registro del server nomina."""
    if testo_server is None:
        return None
    trovate = []
    for nome, modelli in ALTRE_FINI:
        for m in modelli:
            if m in testo_server:
                trovate.append(nome)
                break
    return trovate


def fermo_davvero(conti0, conti1, secondi, soglia_fot_s=0.5):
    """⛔ LO SCHERMO ERA DAVVERO FERMO? — e si legge dal lato che CONSUMA.

    ⚠ Non basta «non ho toccato niente»: un desktop GNOME che ridipinge
      l'orologio, un cursore che lampeggia, una notifica, e la scena non e' piu'
      quella dichiarata.  ⇒ Si contano i fotogrammi CONSEGNATI dal filo e quelli
      DIPINTI sul vetro, e si divide per il tempo.

    Torna `None` se i conti non si sono potuti leggere: `None` non e' zero, e
    «zero fotogrammi» e' esattamente la conclusione che si vorrebbe trarre.
    """
    if conti0 is None or conti1 is None or not secondi or secondi <= 0:
        return None
    d_cons = conti1.get("consegnati", 0) - conti0.get("consegnati", 0)
    d_dip = conti1.get("dipinti", 0) - conti0.get("dipinti", 0)
    if d_cons < 0 or d_dip < 0:
        return None                       # i conti sono andati indietro
    return {"consegnati": d_cons, "dipinti": d_dip, "secondi": secondi,
            "fot_s": d_cons / secondi,
            "fermo": (d_cons / secondi) <= soglia_fot_s}


def cadenza(pacchetti, t_da=None, t_a=None):
    """⭐ CHI TIENE VIVA LA LINEA — i due versi, separati, con la cadenza.

    `pacchetti` e' la lista di `{"t":…, "v":"c2s"|"s2c", "l":…}` del filo.
    Torna `None` se non ne e' passato nessuno: ⛔ una finestra senza pacchetti
    non e' «una linea silenziosa», e' **una prova che non ha morso**
    (`LEZIONI.md` §1.30).
    """
    if pacchetti is None:
        return None
    v = [p for p in pacchetti
         if (t_da is None or p["t"] >= t_da) and (t_a is None or p["t"] <= t_a)]
    if not v:
        return None
    fuori = {}
    for verso in ("c2s", "s2c"):
        q = [p for p in v if p["v"] == verso]
        ts = [p["t"] for p in q]
        salti = [b - a for a, b in zip(ts, ts[1:])]
        salti_ord = sorted(salti)
        fuori[verso] = {
            "pacchetti": len(q),
            "byte": sum(p["l"] for p in q),
            "mediano_s": (salti_ord[len(salti_ord) // 2] if salti_ord else None),
            "massimo_s": (max(salti) if salti else None),
            "primo": (ts[0] if ts else None),
            "ultimo": (ts[-1] if ts else None),
        }
    # ⛔⭐ E LA DOMANDA VERA NON E' «QUANTI», E' «CHI COMINCIA».
    #
    #     Due versi che mandano lo stesso numero di pacchetti ogni 5 s sono
    #     compatibili con due storie opposte: **il browser** si tiene vivo da se'
    #     (e il server risponde), oppure **il server** manda i suoi PING (e il
    #     browser risponde).  ⇒ Si guarda, per ogni pacchetto del cliente, se
    #     nell'ultimo secondo era passato qualcosa dal server:
    #       · SI'  ⇒ e' una RISPOSTA, e a tenere viva la linea e' il server;
    #       · NO   ⇒ e' una parola del cliente, e il browser si tiene vivo da se'.
    s = [p["t"] for p in v if p["v"] == "s2c"]
    risposte, spontanei, ritardi = 0, 0, []
    j = 0
    for p in [q["t"] for q in v if q["v"] == "c2s"]:
        while j + 1 < len(s) and s[j + 1] <= p:
            j += 1
        prec = s[j] if (s and s[j] <= p) else None
        if prec is not None and (p - prec) <= 1.0:
            risposte += 1
            ritardi.append(p - prec)
        else:
            spontanei += 1
    ritardi.sort()
    fuori["chi_comincia"] = {
        "cliente_risposte": risposte,
        "cliente_spontanei": spontanei,
        "ritardo_mediano_s": (ritardi[len(ritardi) // 2] if ritardi else None),
        "chi": (None if (risposte + spontanei) == 0
                else ("il server (il cliente risponde)" if risposte > spontanei
                      else "il cliente (parla da se')")),
    }
    return fuori


def giudica_viva(oss, testo_server, filo, durata, t_apertura=None):
    """⛔⛔ IL VERDETTO DELLA SESSIONE FERMA — e i tre esiti sono TRE.

    Torna `{"esito": "sopravvissuta" | "morta" | "non-misurato", …}`.
    """
    e = esito_del_browser(oss)
    if e["come"] is None:
        return {"esito": "non-misurato", "perche": e.get("perche"),
                "browser": e}
    # ⛔ La prova ha morso?  Zero pacchetti sul filo vuol dire che non ho
    #    guardato niente, non che la linea taceva.
    if filo is not None and not filo:
        return {"esito": "non-misurato",
                "perche": "il filo non ha visto passare NIENTE: la prova non "
                          "ha morso, o il metro guardava altrove",
                "browser": e}
    if e["come"] == "viva":
        return {"esito": "sopravvissuta", "durata": durata, "browser": e,
                "causa": causa_dal_server(testo_server)}
    if e["come"] == "pagina":
        return {"esito": "non-misurato",
                "perche": "a chiudere e' stata la PAGINA, non il server: questa "
                          "non e' la scena dichiarata",
                "browser": e}
    # ── e' morta: ⛔ ADESSO SI LEGGE IL MOTIVO, non il fatto ────────────────
    c = causa_dal_server(testo_server)
    altre = perche_finita(testo_server)
    if c is None:
        return {"esito": "non-misurato",
                "perche": "la sessione e' finita ma il prodotto NON ha scritto "
                          "nessuna riga `linea-morta`: non so perche' sia "
                          "finita" + ("" if not altre else
                                      " (il registro nomina: %s)" % ", ".join(altre)),
                "browser": e, "altre_fini": altre}
    if altre:
        return {"esito": "non-misurato",
                "perche": "e' finita, ma il registro nomina anche %s: non posso "
                          "attribuirla alla linea morta" % ", ".join(altre),
                "browser": e, "causa": c, "altre_fini": altre}
    quanto = None
    if t_apertura is not None and e.get("t"):
        quanto = e["t"] - t_apertura
    return {"esito": "morta", "causa": c, "browser": e, "sopravvissuta_s": quanto}


def giudica_capsula(oss, testo_server, dove="browser"):
    """⛔⭐ LA CAPSULA, LETTA DOVE ARRIVA.

    ⚠ `dove="server"` esiste **solo** per il `--certifica`: e' il guasto
      «dichiarata arrivata leggendo il registro del server invece del filo», e
      deve dare **rosso** quando i due non concordano.
    """
    e = esito_del_browser(oss)
    dal_server = None
    if testo_server is not None:
        armate = testo_server.count("chiusura della sessione RIMANDATA")
        spedite = testo_server.count("chiusa la sessione WebTransport, codice")
        dal_server = {"armate": armate, "spedite": spedite}
    if dove == "server":
        if dal_server is None:
            return {"arrivata": None, "perche": "registro del server non letto"}
        return {"arrivata": dal_server["spedite"] > 0, "letta_dove": "server",
                "server": dal_server, "browser": e}
    if e["come"] is None:
        return {"arrivata": None, "letta_dove": "browser",
                "perche": e.get("perche"), "server": dal_server, "browser": e}
    if e["come"] == "viva":
        return {"arrivata": None, "letta_dove": "browser",
                "perche": "la sessione e' ancora viva: non c'e' niente da "
                          "giudicare", "server": dal_server, "browser": e}
    if e["come"] == "pagina":
        return {"arrivata": None, "letta_dove": "browser",
                "perche": "a chiudere e' stata la pagina: la capsula del server "
                          "non c'entra", "server": dal_server, "browser": e}
    arrivata = (e["come"] == "capsula")
    fuori = {"arrivata": arrivata, "letta_dove": "browser",
             "codice": e.get("codice"), "server": dal_server, "browser": e}
    # ⛔ §3.1: il codice `0` «NON DEVE essere usato».
    if arrivata and e.get("codice") == MOTIVO_VIETATO:
        fuori["vietato"] = ("⛔ codice 0: `RCP.md` §3.1 dice «NON DEVE essere "
                            "usato»")
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ LA FRASE CHE L'UTENTE LEGGE — e si legge NEL BROWSER, mai nel file
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ QUESTO E' IL PEZZO CHE ESISTE PER UN BUCO DICHIARATO.  `fasi/10-…md` §6.4
#      ha misurato la frase di `0x0E` dentro Firefox vero, 10 su 10, e l'ha
#      dichiarata *«byte-identica alla voce della pagina servita»* — ma quel
#      confronto **l'ha fatto una persona guardando**, perche' la tabella dei
#      motivi non si legge da dentro il browser (`const` di script non e'
#      proprieta' di `window`).  ⇒ Qui il confronto lo fa il banco, e i due
#      testi arrivano da **due strade diverse**: uno dal browser che l'ha
#      dipinta, l'altro dal filo che ha servito il file.
#
# ⛔⛔ E LA FORMA D'ERRORE CHE SI VUOLE PRENDERE E' PRECISA: un banco che legge
#      la frase **solo dal file servito** dichiara giusta una frase che il
#      browser non ha mai mostrato.  Basta che il motivo sul filo sia un altro,
#      o che la pagina costruisca l'esito da un'altra parte, e il banco e' verde
#      su un prodotto rotto.  ⇒ `concordano` e' un predicato a se', e da'
#      **rosso** quando i due testi non coincidono.
#
# ⚠ E I TRE PREDICATI DELLA FRASE SONO **LESSICALI**, e va detto invece che
#   lasciato credere.  `RCP.md` §8.2 pretende che una frase dica tre cose — che
#   cosa e' successo, DI CHI e' il limite, che GESTO fare — e un banco non sa
#   leggere il senso.  ⇒ Si misura quel che si puo' misurare: che le parole ci
#   siano.  ⛔ Un metro cosi' **si puo' ingannare** (una frase che nomina il
#   server senza dire niente passa), ma **non si puo' aggirare**: una frase che
#   quelle parole non le ha, quelle tre cose non le dice di sicuro.  ⇒ Vale come
#   RETE, non come giudizio: il giudizio e' del regista (§10).

# ⭐ Le parole con cui una frase puo' dire DI CHI e' il limite.  ⛔ «quella
#    sessione non si puo' servire» non ne ha nessuna: il soggetto e' la sessione
#    dell'utente, e il fatto e' del server.
DI_CHI = ("il server", "questo server", "questa macchina", "il sistema",
          "dal server", "del server")

# ⭐ I gesti che il prodotto OFFRE DAVVERO.  ⛔ La lista e' chiusa apposta:
#    «entra chiedendo meno qualita'» NON c'e', perche' `src/pagina.html` non ha
#    una manopola della qualita' — il modulo ha due campi, utente e parola — e
#    un gesto che il prodotto non offre e' una consolazione travestita.
GESTI = ("riprova", "ricarica", "chiedi", "rientra", "rimpicciolisci",
         "sblocca", "aspetta")

VOCE = re.compile(r'^\s*0x([0-9A-Fa-f]{2})\s*:\s*(".*?"(?:\s*\+\s*".*?")*)\s*,',
                  re.M)


def voce_del_file(html, motivo):
    """⭐ La frase che il FILE SERVITO dichiara per un motivo di §8.2.

    Legge la tabella `MOTIVO` di `src/pagina.html` cosi' com'e' scritta — anche
    quando la voce e' spezzata su piu' righe con `+`, come `0x02`.

    ⛔ Torna `None` se il file non c'e' o la voce non c'e': «non l'ho letta» non
       e' «non c'era».
    """
    if not html:
        return None
    for m in VOCE.finditer(html):
        if int(m.group(1), 16) != motivo:
            continue
        pezzi = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
        return "".join(p.replace('\\"', '"').replace("\\\\", "\\")
                       for p in pezzi)
    return None


def giudica_frase(oss, html_servito, motivo_atteso):
    """⛔⭐ LA FRASE, LETTA DOVE L'UTENTE LA LEGGE — e confrontata col file.

    Torna un dizionario con:
      `browser`     la frase che il browser ha DIPINTO (`None` = non letta)
      `file`        la voce del motivo nel file SERVITO (`None` = non letta)
      `concordano`  ⛔ i due testi coincidono byte per byte (`None` = non ho
                    potuto confrontarli)
      `dice_di_chi` la frase nomina il server — predicato lessicale
      `da_un_gesto` la frase porta un gesto della lista chiusa `GESTI`
      `verdetto`    `"verde"` / `"rosso"` / `None` (⛔ = non ho misurato)

    ⛔ `None` non e' `False` in nessuno dei quattro: un browser che non ha
       scritto niente **non ha mostrato una frase sbagliata**, non ha mostrato
       niente, e un banco che li confonde produce rossi falsi.
    """
    esiti = (oss or {}).get("esiti") or []
    b = esiti[-1]["testo"] if esiti else None
    f = voce_del_file(html_servito, motivo_atteso)
    r = {"browser": b, "file": f, "motivo": motivo_atteso}
    if b is None:
        r.update({"concordano": None, "dice_di_chi": None,
                  "da_un_gesto": None, "verdetto": None,
                  "perche": "il browser non ha dipinto nessun esito"})
        return r
    bb = b.lower()
    r["dice_di_chi"] = any(x in bb for x in DI_CHI)
    r["da_un_gesto"] = any(x in bb for x in GESTI)
    if f is None:
        r["concordano"] = None
        r["perche"] = ("⛔ la pagina servita non e' stata letta, o non porta la "
                       "voce 0x%02x: il confronto NON e' stato fatto"
                       % motivo_atteso)
    else:
        r["concordano"] = (b == f)
    # ⛔ Il verdetto e' verde solo se TUTTI e tre i predicati sono veri.  Un
    #    `None` fra i tre non e' un rosso: e' «non ho misurato», e si dice.
    tre = (r["concordano"], r["dice_di_chi"], r["da_un_gesto"])
    if None in tre:
        r["verdetto"] = None
    else:
        r["verdetto"] = "verde" if all(tre) else "rosso"
    return r


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — i guasti innestati, e fatti GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def _oss(righe, esiti=None, schermo=None):
    t = 1000000.0
    return {"righe": [{"t": (t + i) * 1000, "riga": r} for i, r in enumerate(righe)],
            "crudo": "\n".join(righe),
            "esiti": esiti or [], "schermo": schermo or [], "conti": None}


SANE = ["apro https://…", "sessione WebTransport aperta", "CIAO mandato", "AMMESSO"]


def certifica():
    casi = []

    def caso(nome, fatto, atteso):
        bene = (fatto == atteso)
        casi.append((nome, atteso, fatto, bene))

    _log("A · `esito_del_browser` — dove si legge come e' finita")
    caso("sano · sessione viva",
         esito_del_browser(_oss(SANE))["come"], "viva")
    caso("sano · la capsula e' arrivata (codice 14)",
         esito_del_browser(_oss(SANE + [CHIUSA_SERVER + "14"]))["come"], "capsula")
    caso("sano · e il codice si legge",
         esito_del_browser(_oss(SANE + [CHIUSA_SERVER + "14"]))["codice"], 14)
    caso("⛔ finita SENZA capsula ⇒ «errore», non «capsula»",
         esito_del_browser(_oss(SANE + [CHIUSA_ERRORE + ": WebTransportError"]))["come"],
         "errore")
    caso("⛔ il browser non si e' MAI collegato ⇒ None, non «viva»",
         esito_del_browser(_oss(["apro https://…", "⛔ non arrivo"]))["come"], None)
    caso("⛔ registro vuoto ⇒ None",
         esito_del_browser(_oss([]))["come"], None)
    caso("⛔ non ho letto niente dal browser ⇒ None",
         esito_del_browser(None)["come"], None)
    caso("⛔ a chiudere e' stata la PAGINA ⇒ «pagina», non «capsula»",
         esito_del_browser(_oss(SANE + [CHIUSA_PAGINA + ": codice 0x10"]))["come"],
         "pagina")
    caso("⚠ la pagina ha scritto «codice ?» ⇒ codice None, non 0",
         esito_del_browser(_oss(SANE + [CHIUSA_SERVER + "?"]))["codice"], None)

    _log("B · `causa_dal_server` — il MOTIVO, non il fatto")
    riga_lm = ("[QUIC] 192.168.0.3:5 — linea-morta SCATTATA causa=silenzio "
               "stallo_ms=0 soglia_stallo_ms=100 silenzio_ms=10004 "
               "soglia_silenzio_ms=10000 prove=16 persi=0 permille=0")
    caso("sano · la riga c'e' e la causa e' «silenzio»",
         causa_dal_server("bla\n" + riga_lm + "\nbla")["causa"], "silenzio")
    caso("sano · e i millisecondi si leggono",
         causa_dal_server(riga_lm)["silenzio_ms"], 10004)
    caso("sano · e i persi",
         causa_dal_server(riga_lm)["persi"], 0)
    caso("⛔ nessuna riga `linea-morta` ⇒ None, non «no»",
         causa_dal_server("il server e' partito\nun cliente e' entrato"), None)
    caso("⛔ registro non letto ⇒ None", causa_dal_server(None), None)
    caso("⭐ causa DIVERSA (stallo) si legge come tale",
         causa_dal_server(riga_lm.replace("causa=silenzio", "causa=stallo"))["causa"],
         "stallo")

    _log("C · `perche_finita` — le altre strade, che non sono la linea morta")
    caso("sano · registro pulito ⇒ nessun'altra fine",
         perche_finita("un cliente e' entrato\n" + riga_lm), [])
    caso("⛔ il BAN nel registro si vede",
         perche_finita("… BANNATO per §4.4-bis …"), ["bannato"])
    caso("⛔ la parola sbagliata si vede",
         perche_finita("… autenticazione fallita per provadec1 …"),
         ["parola sbagliata"])
    caso("⛔ il server che si spegne si vede",
         perche_finita("… il server si spegne, congedo tutti …"), ["server spento"])
    caso("⛔ registro non letto ⇒ None", perche_finita(None), None)

    _log("D · `giudica_viva` — e i tre esiti sono TRE")
    filo_ok = [{"t": 1.0, "v": "c2s", "l": 60}, {"t": 2.0, "v": "c2s", "l": 60}]
    caso("sano · viva a fine durata ⇒ «sopravvissuta»",
         giudica_viva(_oss(SANE), "niente", filo_ok, 120.0)["esito"],
         "sopravvissuta")
    caso("sano · morta con la riga `linea-morta causa=silenzio` ⇒ «morta»",
         giudica_viva(_oss(SANE + [CHIUSA_ERRORE + ": x"]), riga_lm, filo_ok,
                      120.0)["esito"], "morta")
    caso("⛔ IL BROWSER NON SI E' MAI COLLEGATO ⇒ «non-misurato», mai «sopravvissuta»",
         giudica_viva(_oss(["apro https://…"]), "niente", filo_ok, 120.0)["esito"],
         "non-misurato")
    caso("⛔ il browser resta APPESO e la durata scade ⇒ «non-misurato»",
         giudica_viva(_oss(["apro https://…", "impronta chiesta"]), "niente",
                      filo_ok, 600.0)["esito"], "non-misurato")
    caso("⛔ finita ma il registro NON dice `linea-morta` ⇒ «non-misurato»",
         giudica_viva(_oss(SANE + [CHIUSA_ERRORE + ": x"]), "niente", filo_ok,
                      120.0)["esito"], "non-misurato")
    caso("⛔ finita per un BAN, contata come linea morta ⇒ «non-misurato»",
         giudica_viva(_oss(SANE + [CHIUSA_ERRORE + ": x"]),
                      riga_lm + "\n⛔ BANNATO per §4.4-bis", filo_ok,
                      120.0)["esito"], "non-misurato")
    caso("⛔ finita perche' il SERVER SI E' SPENTO ⇒ «non-misurato»",
         giudica_viva(_oss(SANE + [CHIUSA_ERRORE + ": x"]),
                      riga_lm + "\nil server si spegne, congedo tutti", filo_ok,
                      120.0)["esito"], "non-misurato")
    caso("⛔ IL FILO NON HA VISTO NIENTE ⇒ «non-misurato» (la prova non morde)",
         giudica_viva(_oss(SANE), "niente", [], 120.0)["esito"], "non-misurato")
    caso("⛔ a chiudere e' stata la pagina ⇒ «non-misurato»",
         giudica_viva(_oss(SANE + [CHIUSA_PAGINA + ": 0x10"]), riga_lm, filo_ok,
                      120.0)["esito"], "non-misurato")

    _log("E · `giudica_capsula` — letta DOVE ARRIVA, non dove parte")
    reg_armata = "chiusura della sessione RIMANDATA, codice 0x0e (in coda: 0 elementi)"
    reg_spedita = (reg_armata + "\nchiusa la sessione WebTransport, codice 0x0e "
                                "(9 byte: 2 di frame DATA + 7 di capsula)")
    oss_cap = _oss(SANE + [CHIUSA_SERVER + "14"])
    oss_err = _oss(SANE + [CHIUSA_ERRORE + ": WebTransportError"])
    caso("sano · arrivata al browser E spedita dal server ⇒ arrivata",
         giudica_capsula(oss_cap, reg_spedita)["arrivata"], True)
    caso("⛔⛔ IL SERVER DICE «SPEDITA» E IL BROWSER NON L'HA VISTA ⇒ NON arrivata",
         giudica_capsula(oss_err, reg_spedita)["arrivata"], False)
    caso("⛔ e il guasto «la leggo dal registro del SERVER» dice il contrario "
         "(ecco perche' non si fa)",
         giudica_capsula(oss_err, reg_spedita, dove="server")["arrivata"], True)
    caso("⛔ armata ma mai spedita, browser in errore ⇒ NON arrivata",
         giudica_capsula(oss_err, reg_armata)["arrivata"], False)
    caso("⛔ il browser non si e' collegato ⇒ None, non False",
         giudica_capsula(_oss(["apro …"]), reg_spedita)["arrivata"], None)
    caso("⛔ la sessione e' ancora viva ⇒ None, non False",
         giudica_capsula(_oss(SANE), reg_armata)["arrivata"], None)
    caso("⛔ CODICE 0 sul filo ⇒ §3.1 lo vieta, e il banco lo dice",
         "vietato" in giudica_capsula(_oss(SANE + [CHIUSA_SERVER + "0"]),
                                      reg_spedita), True)
    caso("⭐ e il conto del server si riporta comunque, per il confronto",
         giudica_capsula(oss_err, reg_spedita)["server"], {"armate": 1, "spedite": 1})

    _log("F · `fermo_davvero` — lo schermo era fermo, letto dal lato che consuma")
    c0 = {"consegnati": 100, "dipinti": 98}
    caso("sano · nessun fotogramma in 100 s ⇒ fermo",
         fermo_davvero(c0, {"consegnati": 100, "dipinti": 98}, 100.0)["fermo"], True)
    caso("⛔ 30 fot/s ⇒ NON fermo (la scena dichiarata e' falsa)",
         fermo_davvero(c0, {"consegnati": 3100, "dipinti": 3098}, 100.0)["fermo"],
         False)
    caso("⛔ 1 fot/s ⇒ NON fermo: la soglia morde a mezzo",
         fermo_davvero(c0, {"consegnati": 200, "dipinti": 198}, 100.0)["fermo"],
         False)
    caso("⛔ conti non letti ⇒ None, non «fermo»",
         fermo_davvero(c0, None, 100.0), None)
    caso("⛔ conti che vanno INDIETRO ⇒ None",
         fermo_davvero(c0, {"consegnati": 50, "dipinti": 40}, 100.0), None)
    caso("⛔ zero secondi ⇒ None, non divisione per zero",
         fermo_davvero(c0, c0, 0.0), None)

    _log("G · `cadenza` — chi manda pacchetti, e ogni quanto")
    p = ([{"t": float(i), "v": "c2s", "l": 60} for i in range(0, 20, 2)]
         + [{"t": 0.5, "v": "s2c", "l": 1400}])
    caso("sano · il cliente manda ogni 2 s",
         cadenza(p)["c2s"]["mediano_s"], 2.0)
    caso("sano · e il server una volta sola",
         cadenza(p)["s2c"]["pacchetti"], 1)
    caso("⛔ finestra senza pacchetti ⇒ None, non «linea silenziosa»",
         cadenza(p, t_da=100.0, t_a=200.0), None)
    caso("⛔ filo non letto ⇒ None", cadenza(None), None)
    caso("⭐ i byte si sommano per verso",
         cadenza(p)["s2c"]["byte"], 1400)
    # ⛔⭐ «chi comincia»: due scene con lo STESSO conteggio e storie opposte
    server_ping = []
    for i in range(10):
        server_ping.append({"t": 5.0 * i, "v": "s2c", "l": 60})
        server_ping.append({"t": 5.0 * i + 0.012, "v": "c2s", "l": 60})
    caso("⭐ il SERVER manda e il cliente risponde ⇒ «il server»",
         cadenza(server_ping)["chi_comincia"]["chi"],
         "il server (il cliente risponde)")
    cliente_ping = []
    for i in range(10):
        cliente_ping.append({"t": 5.0 * i, "v": "c2s", "l": 60})
        cliente_ping.append({"t": 5.0 * i + 0.012, "v": "s2c", "l": 60})
    caso("⛔ IL CLIENTE manda e il server risponde ⇒ «il cliente» "
         "(stesso conteggio, storia opposta)",
         cadenza(cliente_ping)["chi_comincia"]["chi"],
         "il cliente (parla da se')")
    caso("⭐ e i due casi hanno lo STESSO numero di pacchetti per verso",
         (cadenza(server_ping)["c2s"]["pacchetti"],
          cadenza(cliente_ping)["c2s"]["pacchetti"]), (10, 10))
    caso("⭐ il ritardo di risposta si misura",
         round(cadenza(server_ping)["chi_comincia"]["ritardo_mediano_s"], 3), 0.012)
    caso("⛔ nessun pacchetto del cliente ⇒ «chi» resta None",
         cadenza([{"t": 1.0, "v": "s2c", "l": 60}])["chi_comincia"]["chi"], None)

    _log("G-bis · `segnale_del_figlio` — il difetto della finestra")
    reg_morto = ("il figlio di «provadec1» (uid 1100) e' stato RACCOLTO: "
                 "l'ha ucciso il segnale 11.  Da adesso «morto» e «vivo»…")
    caso("sano · il segnale 11 si legge", segnale_del_figlio(reg_morto), 11)
    caso("⭐ e un segnale diverso si legge come tale",
         segnale_del_figlio(reg_morto.replace("segnale 11", "segnale 9")), 9)
    caso("⛔ figlio vivo ⇒ None, non 0",
         segnale_del_figlio("il figlio di «provadec1» lavora"), None)
    caso("⛔ registro non letto ⇒ None", segnale_del_figlio(None), None)
    caso("⛔ una USCITA normale non e' un segnale",
         segnale_del_figlio("il figlio se n'e' andato: uscita 0"), None)

    # ═══════════════════════════════════════════════════════════════════════
    _log("G-ter · ⭐⭐ `voce_del_file` e `giudica_frase` — LA FRASE CHE L'UTENTE LEGGE")
    # ⭐ Un pezzo di pagina VERO nella forma, e minuscolo: la tabella `MOTIVO`
    #   com'e' scritta, compresa una voce spezzata con `+` (e' `0x02`).
    FILE_NUOVO = (
        'const MOTIVO = {\n'
        '  0x01: "la sessione e\' stata chiusa dall\'utente",\n'
        '  0x02: "sei stato mezz\'ora senza toccare niente: per rientrare "\n'
        '      + "servi tu, con la tua parola d\'ordine",\n'
        '  /* un commento in mezzo, che non deve confondere il lettore */\n'
        '  0x06: "questo server non ha piu\' capacita\' per un altro desktop — '
        'le sessioni gia\' aperte continuano: riprova fra un momento, oppure '
        'rimpicciolisci la finestra e riprova",\n'
        '  0x0E: "il server non ha potuto aprirti la sessione, e non e\' un tuo '
        'errore: riprova fra un momento, e se si ripete chiedi a chi amministra '
        'il server — il perche\' preciso e\' nel suo registro",\n'
        '  0x0F: "il posto di questa sessione risulta occupato da un altro '
        'client — se eri tu e sei appena caduto, riprova fra qualche secondo",\n'
        '};\n')
    VECCHIA_0E = "quella sessione non si puo' servire"
    FILE_VECCHIO = re.sub(r'(0x0E: )".*?"(?=,\n)',
                          lambda m: m.group(1) + '"%s"' % VECCHIA_0E,
                          FILE_NUOVO, flags=re.S)

    caso("`voce_del_file` legge la voce 0x0E",
         voce_del_file(FILE_NUOVO, 0x0E)[:20], "il server non ha pot")
    caso("⭐ e ricuce una voce spezzata con `+` (0x02)",
         voce_del_file(FILE_NUOVO, 0x02),
         "sei stato mezz'ora senza toccare niente: per rientrare servi tu, "
         "con la tua parola d'ordine")
    caso("⛔ voce che non c'e' ⇒ None, non stringa vuota",
         voce_del_file(FILE_NUOVO, 0x0C), None)
    caso("⛔ file non letto ⇒ None", voce_del_file(None, 0x0E), None)

    nuova_0e = voce_del_file(FILE_NUOVO, 0x0E)
    nuova_06 = voce_del_file(FILE_NUOVO, 0x06)

    def _osf(frase):
        return _oss(SANE, esiti=[{"t": 1000.0, "testo": frase}] if frase else [])

    # ── SANO ────────────────────────────────────────────────────────────────
    g = giudica_frase(_osf(nuova_0e), FILE_NUOVO, 0x0E)
    caso("SANO · browser e file concordano", g["concordano"], True)
    caso("SANO · la frase dice DI CHI e' il limite", g["dice_di_chi"], True)
    caso("SANO · la frase da' un gesto", g["da_un_gesto"], True)
    caso("SANO · verdetto", g["verdetto"], "verde")
    g6 = giudica_frase(_osf(nuova_06), FILE_NUOVO, 0x06)
    caso("SANO · e lo stesso per 0x06", g6["verdetto"], "verde")

    # ── GUASTO 1: la frase di IERI, quella che §6.4 ha letto nel browser ────
    gv = giudica_frase(_osf(VECCHIA_0E), FILE_VECCHIO, 0x0E)
    caso("⛔ GUASTO · la frase di ieri NON dice di chi e' il limite",
         gv["dice_di_chi"], False)
    caso("⛔ GUASTO · la frase di ieri NON da' nessun gesto",
         gv["da_un_gesto"], False)
    caso("⛔ GUASTO · e concorda col file lo stesso: ROSSO su una frase "
         "che il file conferma", (gv["concordano"], gv["verdetto"]),
         (True, "rosso"))

    # ── GUASTO 2 ⛔⛔ IL BANCO SCRITTO MALE: il file dice una cosa, il browser
    #    un'altra.  Chi legge SOLO il file dichiara verde.
    gd = giudica_frase(_osf(voce_del_file(FILE_NUOVO, 0x0F)), FILE_NUOVO, 0x0E)
    caso("⛔⛔ GUASTO · file 0x0E giusto ma browser mostra la voce 0x0F "
         "⇒ NON concordano", gd["concordano"], False)
    caso("⛔⛔ GUASTO · e il verdetto e' ROSSO, non verde",
         gd["verdetto"], "rosso")
    caso("⭐ e i due testi restano tutt'e due in mano, per diagnosticare",
         (gd["file"] == nuova_0e, gd["browser"].startswith("il posto di questa")),
         (True, True))

    # ── GUASTO 3: una frase che nomina il server ma non da' nessun gesto ────
    gs = giudica_frase(_osf("il server non ha potuto aprirti la sessione"),
                       FILE_NUOVO, 0x0E)
    caso("⛔ GUASTO · dice di chi ma non da' il gesto ⇒ rosso",
         (gs["dice_di_chi"], gs["da_un_gesto"], gs["verdetto"]),
         (True, False, "rosso"))

    # ── GUASTO 4: il gesto che il prodotto NON offre non e' un gesto ────────
    gq = giudica_frase(
        _osf("il server e' pieno: entra chiedendo meno qualita'"),
        FILE_NUOVO, 0x0E)
    caso("⛔⛔ GUASTO · «entra chiedendo meno qualita'» NON conta come gesto: "
         "la pagina non ha una manopola della qualita'", gq["da_un_gesto"], False)

    # ── ⛔ `None` NON E' `False` — in tutti e quattro ────────────────────────
    gn = giudica_frase(_osf(None), FILE_NUOVO, 0x0E)
    caso("⛔ browser muto ⇒ NON HO MISURATO, non «frase sbagliata»",
         (gn["browser"], gn["concordano"], gn["dice_di_chi"],
          gn["da_un_gesto"], gn["verdetto"]),
         (None, None, None, None, None))
    gm = giudica_frase(_osf(nuova_0e), None, 0x0E)
    caso("⛔ file servito non letto ⇒ concordano None e verdetto None, "
         "anche se i due predicati lessicali sono VERI",
         (gm["concordano"], gm["dice_di_chi"], gm["verdetto"]),
         (None, True, None))
    gp = giudica_frase(_osf(nuova_0e), FILE_NUOVO, 0x0C)
    caso("⛔ voce assente dal file ⇒ non misurato, mai «non concordano»",
         (gp["concordano"], gp["verdetto"]), (None, None))

    # ── ⭐ E IL CONTROLLO POSITIVO DEL METRO LESSICALE: sa dire di no? ──────
    caso("⭐ il metro lessicale NON e' sempre vero: «errore di protocollo» "
         "fallisce tutt'e due i predicati",
         (giudica_frase(_osf("errore di protocollo"), FILE_NUOVO, 0x0E)["dice_di_chi"],
          giudica_frase(_osf("errore di protocollo"), FILE_NUOVO, 0x0E)["da_un_gesto"]),
         (False, False))

    _log("H · il metro del filo (`10-b2-filo.py`) si certifica da se'")
    filo = _carica("b2filo", os.path.join(QUI, "10-b2-filo.py"))
    rc = filo.certifica()
    casi.append(("il parser del filo: 17 guasti innestati", 0, rc, rc == 0))

    _log("IL CONTO")
    buoni = 0
    for nome, atteso, avuto, bene in casi:
        if bene:
            buoni += 1
            print("    \033[1;32mOK\033[0m  %s" % nome)
        else:
            print("    \033[1;31mNO\033[0m  %s\n          atteso %r · avuto %r"
                  % (nome, atteso, avuto))
    print("\n  \033[1m%d su %d\033[0m" % (buoni, len(casi)))
    return 0 if buoni == len(casi) else 3


# ═══════════════════════════════════════════════════════════════════════════
# IL FILO — lo si accende sulla macchina, e lo si rilegge dopo
# ═══════════════════════════════════════════════════════════════════════════
def filo_spedisci():
    """⛔ Il testimone che gira e' QUELLO CHE HO IN MANO, non una copia vecchia
       rimasta nell'albero: si spedisce a ogni giro, e la si verifica con l'md5.
       Un metro stantio resta verde (forma D5)."""
    import base64
    import hashlib
    b = open(os.path.join(QUI, "10-b2-filo.py"), "rb").read()
    mio = hashlib.md5(b).hexdigest()
    root("mkdir -p %s/banchi && printf '%%s' '%s' | base64 -d > %s/banchi/10-b2-filo.py"
         % (ALB, base64.b64encode(b).decode("ascii"), ALB))
    rc, out, _ = root("md5sum %s/banchi/10-b2-filo.py | cut -d' ' -f1" % ALB)
    la = (out or "").strip().splitlines()
    la = la[-1].strip() if la else ""
    return la == mio


def filo_accendi(secondi, nome):
    fuori = "%s/filo-%s.jsonl" % (LAV, nome)
    if not filo_spedisci():
        return None
    root("rm -f %s" % fuori)
    riga = catena_root(
        "nohup python3 -u %s/banchi/10-b2-filo.py --iface %s --porta %d "
        "--pari %s --secondi %.1f --fuori %s >%s/filo-%s.log 2>&1 & echo AVVIATO"
        % (ALB, IFACCIA, PORTA, IO_SONO, secondi, fuori, LAV, nome))
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, riga],
                   capture_output=True, text=True, timeout=60)
    # ⛔ E si aspetta che il file esista DAVVERO: «l'ho lanciato» non e' «sta
    #    guardando», e un banco che misura credendo di avere un testimone che
    #    non c'e' e' esattamente la forma «silenzio invece di rosso».
    for _ in range(40):
        rc, out, _ = root("head -c 200 %s 2>/dev/null" % fuori)
        if '"tipo": "inizio"' in (out or ""):
            return fuori
        time.sleep(0.25)
    return None


def filo_leggi(fuori):
    """I pacchetti, oppure `None` se il testimone non ha scritto niente."""
    if fuori is None:
        return None
    rc, out, _ = root("cat %s" % fuori, tetto=300)
    if rc != 0 or not out:
        return None
    p = []
    visto_inizio = False
    for l in out.splitlines():
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("tipo") == "inizio":
            visto_inizio = True
        elif "v" in d:
            p.append(d)
    return p if visto_inizio else None


def filo_spegni():
    root("pkill -f '[1]0-b2-filo.py'; true")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ SCENA «VIVA» — `[?]` 1
# ═══════════════════════════════════════════════════════════════════════════
def scena_viva(o):
    nome = ("%s-%ds" % ("senza-audio" if o.senza_audio_silenzio else "cure-accese",
                        int(o.durata)))
    _log("LA SCENA: desktop FERMO, browser vero, cure %s"
         % ("ai predefiniti TRANNE il silenzio dell'audio, SPENTO"
            if o.senza_audio_silenzio else "TUTTE ai predefiniti"))
    # ⛔⛔ E PRIMA DI TUTTO: LE CURE CHE IL SERVER HA DAVVERO ADDOSSO.
    #     Un braccio di controllo dichiarato e non acceso e' due misure identiche
    #     spacciate per un A/B, ed e' il modo piu' comodo di «confermare» quel
    #     che si voleva sentire.
    arg = opzioni_del_server()
    if arg is None:
        _ko("⛔ non ho potuto leggere la riga di comando del server: NON MISURO")
        return 2
    ha_spento = "--niente-audio-silenzio" in arg
    _inf("il server gira con: %s" % arg[arg.find("--indirizzo"):][:400])
    if ha_spento != bool(o.senza_audio_silenzio):
        _ko("⛔ NON MISURO: il banco dichiara «silenzio dell'audio %s» e il "
            "server dice il contrario.  Accendilo con "
            "`OPZIONI_SERVER='--niente-audio-silenzio' bash banchi/10-b2-terreno.sh accendi`"
            % ("SPENTO" if o.senza_audio_silenzio else "acceso"))
        return 2
    _ok("le cure: silenzio dell'audio %s · linea morta %s · ritmo adattivo %s"
        % ("SPENTO (braccio di controllo)" if ha_spento else "acceso (predefinito)",
           "SPENTA" if "--niente-linea-morta" in arg else "accesa (predefinito)",
           "SPENTO" if "--niente-ritmo-adattivo" in arg else "acceso (predefinito)"))

    # ⛔ E IL PALCO DI PRIMA DEV'ESSERE MORTO DAVVERO, non «l'ho appena ucciso»
    if not sgombra_palco():
        _ko("⛔ il palco precedente non e' morto in 20 s: NON MISURO (mi "
            "attaccherei a un palco che sta morendo, e misurerei la sua morte)")
        return 2

    riga0 = righe_registro()
    if riga0 is None:
        _ko("⛔ non ho potuto leggere il registro del server: NON MISURO")
        return 2

    filo_f = filo_accendi(o.durata + 60, nome)
    if filo_f is None:
        _ko("⛔ il testimone sul filo non e' partito: NON MISURO")
        return 2
    _ok("il testimone sul filo guarda %s, porta %d, pari %s"
        % (IFACCIA, PORTA, IO_SONO))

    b = None
    try:
        b = Browser(porta_mar=o.marionette, headless=not o.con_schermo)
    except Exception as e:
        filo_spegni()
        _ko("⛔ Firefox non e' partito (%s: %s): NON MISURO" % (type(e).__name__, e))
        return 2
    try:
        d = b.carica()
        # ⛔⛔ E PRIMA DI CLICCARE SI GUARDA IL PASSO CHE LA TELA AVRA'.
        #     `[M]` 24 agosto 2026: con una larghezza che non e' multiplo di 16
        #     il passo del DMA-BUF non e' multiplo di 64, il figlio rimonta il
        #     palco sulla memoria e **muore di SIGSEGV** prima del primo
        #     fotogramma.  ⇒ Su quella strada questa scena non puo' misurare
        #     niente, e lo dice invece di misurare la morte del palco.
        lp = d[2] if d else None
        if lp is None or (lp * 4) % 64 != 0:
            filo_spegni()
            _ko("⛔ NON MISURO: la finestra e' larga %s, il passo del DMA-BUF "
                "sarebbe %s e NON e' multiplo di 64 — su questo prodotto quella "
                "strada uccide il figlio (segnale 11) prima del primo fotogramma"
                % (lp, None if lp is None else lp * 4))
            return 2
        _ok("finestra dentro %d×%d ⇒ passo %d, multiplo di 64"
            % (d[2], d[3], d[2] * 4))
        t_clic = b.entra(UTENTE_A[0], PAROLA_UTENTE)
        _inf("Firefox 140 ESR ha cliccato «Collegati» come %s" % UTENTE_A[0])

        # ── si aspetta che la sessione sia DAVVERO su ────────────────────
        t_pronto = None
        scade = time.time() + 90
        while time.time() < scade:
            oss = b.leggi()
            if c_e(oss, APERTA):
                t_pronto = time.time()
                break
            e = esito_del_browser(oss)
            if e["come"] in ("errore", "capsula", "pagina"):
                break
            time.sleep(0.5)
        if t_pronto is None:
            oss = b.leggi()
            filo_spegni()
            _ko("⛔ in 90 s la sessione non si e' aperta: NON HO MISURATO")
            for r in (oss or {}).get("righe", [])[-12:]:
                _inf(r["riga"])
            return 2
        _ok("sessione aperta")

        # ⛔ E si aspetta anche il DESKTOP: «sessione aperta» e «schermo acceso»
        #    sono due cose diverse, e la scena dichiarata e' la seconda.
        t_schermo = None
        scade = time.time() + 90
        while time.time() < scade:
            oss = b.leggi()
            if oss.get("schermo_ora") == "acceso":
                t_schermo = time.time()
                break
            if esito_del_browser(oss)["come"] in ("errore", "capsula", "pagina"):
                break
            time.sleep(0.5)
        if t_schermo is None:
            _dub("⚠ lo schermo non si e' acceso: misuro lo stesso, ma la scena "
                 "e' «sessione aperta senza desktop», e lo dico")
        else:
            _ok("desktop acceso dopo %.1f s dal clic" % (t_schermo - t_clic))

        # ── ⭐ ADESSO NON SI TOCCA PIU' NIENTE ────────────────────────────
        base = time.time()
        oss0 = b.leggi()
        conti0 = oss0.get("conti")
        _log("⭐ NESSUNO TOCCA NIENTE per %.0f s — si guarda e basta" % o.durata)
        fine = None
        campioni = []
        scade = base + o.durata
        while time.time() < scade:
            time.sleep(2.0)
            oss = b.leggi()
            e = esito_del_browser(oss)
            campioni.append({"t": time.time(), "conti": oss.get("conti"),
                             "schermo": oss.get("schermo_ora")})
            if e["come"] in ("errore", "capsula", "pagina"):
                fine = time.time()
                _inf("⛔ finita dopo %.1f s dall'apertura — «%s»"
                     % (fine - t_pronto, e.get("riga")))
                break
            if int(time.time() - base) % 20 < 2:
                _inf("%.0f s · viva · schermo %s · consegnati %s"
                     % (time.time() - base, oss.get("schermo_ora"),
                        (oss.get("conti") or {}).get("consegnati")))
        oss = b.leggi()
        conti1 = oss.get("conti")
        t_fine = time.time()
    finally:
        if b is not None:
            b.spegni()
        time.sleep(1.0)
        filo_spegni()

    testo = registro_da(riga0)
    pacchetti = filo_leggi(filo_f)
    v = giudica_viva(oss, testo, pacchetti, o.durata, t_apertura=t_pronto)
    f = fermo_davvero(conti0, conti1, t_fine - base)
    cad = cadenza(pacchetti, t_da=base, t_a=(fine or t_fine))

    _log("IL VERDETTO")
    if v["esito"] == "non-misurato":
        _ko("⛔ NON HO MISURATO: %s" % v.get("perche"))
    elif v["esito"] == "sopravvissuta":
        _ok("⭐ la sessione ferma di un browser vero e' SOPRAVVISSUTA %.0f s"
            % o.durata)
    else:
        _ko("⛔ MORTA dopo %.1f s · causa=%s silenzio_ms=%s persi=%s permille=%s"
            % (v.get("sopravvissuta_s") or -1, v["causa"]["causa"],
               v["causa"]["silenzio_ms"], v["causa"]["persi"],
               v["causa"]["permille"]))
        _inf(v["causa"]["riga"])

    if f is None:
        _dub("⚠ i fotogrammi non si sono potuti leggere: NON dico che lo "
             "schermo fosse fermo")
    else:
        (_ok if f["fermo"] else _ko)(
            "lo schermo %s: %d consegnati e %d dipinti in %.0f s (%.3f fot/s)"
            % ("era FERMO" if f["fermo"] else "⛔ NON era fermo",
               f["consegnati"], f["dipinti"], f["secondi"], f["fot_s"]))

    if cad is None:
        _dub("⚠ nessun pacchetto nella finestra: la prova non ha morso")
    else:
        for verso, etichetta in (("c2s", "browser → server"),
                                 ("s2c", "server → browser")):
            q = cad[verso]
            _inf("%s: %d pacchetti, %d byte, salto mediano %s s, massimo %s s"
                 % (etichetta, q["pacchetti"], q["byte"],
                    "%.3f" % q["mediano_s"] if q["mediano_s"] is not None else "—",
                    "%.3f" % q["massimo_s"] if q["massimo_s"] is not None else "—"))
        # ⭐⭐ E QUANTO COSTA UNA SESSIONE FERMA, SUL FILO — il numero che il
        #    riquadro di `webtransport.c` dichiara «~26 byte/s per sessione».
        #    ⚠ Quel numero e' un `[?]` scritto nel codice («~40 byte di carico
        #    piu' 28 di IP/UDP»); qui si legge quel che passa davvero.
        dur = (fine or t_fine) - base
        tot = cad["c2s"]["byte"] + cad["s2c"]["byte"]
        if dur > 0:
            _inf("⭐ quanto costa la sessione FERMA sul filo: %.1f byte/s in "
                 "tutto (%.1f dal server + %.1f dal cliente) = %.3f kbit/s "
                 "— e il riquadro di `webtransport.c` dichiara ~26 byte/s"
                 % (tot / dur, cad["s2c"]["byte"] / dur,
                    cad["c2s"]["byte"] / dur, tot * 8 / dur / 1000.0))
        k = cad["chi_comincia"]
        if k["chi"] is None:
            _dub("⚠ il cliente non ha mandato niente: non so chi tenga viva la linea")
        else:
            _inf("⭐ A TENERE VIVA LA LINEA E': **%s** — %d pacchetti del "
                 "cliente sono RISPOSTE (entro 1 s da uno del server), %d sono "
                 "parole sue; ritardo mediano della risposta %s s"
                 % (k["chi"], k["cliente_risposte"], k["cliente_spontanei"],
                    "%.4f" % k["ritardo_mediano_s"]
                    if k["ritardo_mediano_s"] is not None else "—"))

    fuori = {"scena": nome, "durata": o.durata, "verdetto": v, "fermo": f,
             "argv_server": arg,
             "cadenza": cad, "conti0": conti0, "conti1": conti1,
             "campioni": campioni,
             "righe_pagina": [r["riga"] for r in (oss or {}).get("righe", [])],
             "esiti_pagina": (oss or {}).get("esiti"),
             "pacchetti": len(pacchetti) if pacchetti is not None else None}
    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "viva-%s.json" % nome), "w") as fh:
        json.dump(fuori, fh, indent=1, ensure_ascii=False)
    if pacchetti is not None:
        with open(os.path.join(FUORI, "filo-%s.json" % nome), "w") as fh:
            json.dump(pacchetti, fh)
    return 0 if v["esito"] != "non-misurato" else 2


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ SCENA «FINESTRA» — il difetto che nessuno cercava, e l'A/B che lo isola
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 24 agosto 2026: al primo giro di questo banco la sessione moriva a 1,3 s
# e il registro del server diceva, per intero:
#
#   ⛔⛔ il passo del DMA-BUF e' 5072 su una tela 1268x714, e NON e' multiplo
#        di 64 … ⇒ Rimonto il palco sulla MEMORIA per questa tela
#   il figlio di «provadec1» … se ne va: Connection reset by peer
#   ⭐ il figlio di «provadec1» e' stato RACCOLTO: l'ha ucciso il segnale 11
#
# ⚠ E la misura della finestra NON era una scelta del banco: e' quella che
#   Firefox apre di suo.  ⇒ Un utente vero con una finestra di quella misura
#   perde il desktop **prima del primo fotogramma**.
#
# ⛔ MA UNA VOLTA NON E' UNA MISURA.  ⇒ Qui si fa l'A/B sulla sola grandezza
#    che entra nel passo: la LARGHEZZA della vista.  1268 × 4 = **5072**, che
#    non e' multiplo di 64; 1280 × 4 = **5120**, che lo e'.  N giri ciascuna, e
#    il palco sgombrato fra un giro e l'altro perche' ognuno lo faccia NASCERE
#    invece di riattaccarsi a quello di prima — il rimontaggio sulla memoria
#    avviene solo alla nascita.
#
# ⛔⛔ E LA LARGHEZZA CHE CONTA E' `clientWidth`, non `innerWidth`: fra le due
#      ci sono i 12 px della barra di scorrimento, e per un giro intero il banco
#      ha creduto di misurare 1280 mentre la pagina chiedeva 1268.


def sgombra_palco():
    """⛔ Fra un giro e l'altro il palco si sgombra, e SOLO il mio.

    ⚠ Senza, il secondo giro e' un RIATTACCO: il palco c'e' gia', e la strada
      che si vuole misurare — la nascita del palco — non viene percorsa.
    """
    root("for u in %s %s; do pkill -u $u -f gnome-session-binary 2>/dev/null; "
         "done; true" % (UTENTE_A[0], UTENTE_B[0]))
    # ⛔⛔ E SI ASPETTA CHE SIA DAVVERO MORTO, non due secondi a caso.
    #     `[M]` 24 agosto 2026: attaccandosi mentre il palco precedente stava
    #     ancora morendo, il server congedava la sessione NUOVA con `0x10` («la
    #     sessione grafica e' terminata») dopo 4,6 s — e il banco misurava la
    #     morte del palco di PRIMA credendo di misurare la linea morta.
    #     ⚠ E' il «palco orfano» di `LEZIONI.md` §1.26 con un'altra faccia: non
    #     dava rosso, dava un numero plausibile.
    for _ in range(40):
        rc, out, _ = root("pgrep -u %s -c gnome-shell; pgrep -u %s -c gnome-shell; true"
                          % (UTENTE_A[0], UTENTE_B[0]))
        n = [x.strip() for x in (out or "").splitlines() if x.strip().isdigit()]
        if all(x == "0" for x in n) or not n:
            time.sleep(2.0)
            return True
        time.sleep(0.5)
    return False


SEGNALE = re.compile(r"e' stato RACCOLTO: l'ha ucciso il segnale (\d+)")


def segnale_del_figlio(testo):
    """Il segnale che ha ucciso il figlio, o `None` se non e' morto cosi'.

    ⛔ `None` vuol dire «il registro non lo dice»: puo' essere che il figlio sia
       vivo, o che io non abbia letto il registro.  Chi chiama distingue.
    """
    if testo is None:
        return None
    m = SEGNALE.search(testo)
    return int(m.group(1)) if m else None


def scena_finestra(o):
    _log("LA SCENA: la MISURA DELLA FINESTRA — stessa larghezza, due altezze")
    esiti = {}
    b = None
    try:
        b = Browser(porta_mar=o.marionette, headless=not o.con_schermo)
    except Exception as e:
        _ko("⛔ Firefox non e' partito (%s: %s): NON MISURO" % (type(e).__name__, e))
        return 2
    try:
        for largo in (1268, 1280):
            morti, vivi, ignoti, tele = 0, 0, 0, set()
            for g in range(o.giri):
                sgombra_palco()
                r0 = righe_registro()
                d = b.carica(largo, 714)
                b.entra(UTENTE_A[0], PAROLA_UTENTE)
                t0 = time.time()
                acceso = False
                while time.time() - t0 < 45:
                    oss = b.leggi()
                    if oss.get("schermo_ora") == "acceso":
                        acceso = True
                    if esito_del_browser(oss)["come"] in ("errore", "capsula",
                                                          "pagina"):
                        break
                    if acceso and time.time() - t0 > 12:
                        break
                    time.sleep(0.5)
                oss = b.leggi()
                testo = registro_da(r0)
                sig = segnale_del_figlio(testo)
                # ⛔⛔ IL SEGNALE 15 E' MIO — `sgombra_palco()` manda `SIGTERM` a
                #     `gnome-session`, e il figlio se ne va dietro.  Contarlo
                #     come difetto del prodotto vorrebbe dire accusare il
                #     prodotto di quel che ho fatto io: `[M]` 24 agosto 2026,
                #     e per un giro ha dato «figlio MORTO 5 su 5» su tutt'e due
                #     i bracci, cioe' un A/B in cui a uccidere ero io.
                if sig == 15:
                    sig = None
                t = riga_crudo(oss, "video · negoziato")
                if t:
                    tele.add(t.split("tela ")[-1].strip())
                if testo is None:
                    ignoti += 1
                    stato = "⚠ registro non letto"
                elif sig is not None:
                    morti += 1
                    stato = "⛔ IL FIGLIO E' MORTO col segnale %d" % sig
                elif esito_del_browser(oss)["come"] == "viva" and acceso:
                    vivi += 1
                    stato = "⭐ vivo, desktop acceso"
                else:
                    ee = esito_del_browser(oss)
                    ignoti += 1
                    stato = ("⚠ ne' morto ne' vivo: come=%s perche'=%s"
                             % (ee["come"], ee.get("perche")))
                _inf("larghezza %d (passo %d, %s) · vista %sx%s · giro %d/%d · %s"
                     % (largo, largo * 4,
                        "multiplo di 64" if (largo * 4) % 64 == 0
                        else "⛔ NON multiplo di 64",
                        d[2] if d else "?", d[3] if d else "?",
                        g + 1, o.giri, stato))
            esiti[largo] = {"morti": morti, "vivi": vivi, "ignoti": ignoti,
                            "tele": sorted(tele), "passo": largo * 4,
                            "multiplo64": (largo * 4) % 64 == 0}
    finally:
        if b is not None:
            b.spegni()
        sgombra_palco()

    _log("IL VERDETTO")
    for largo, e in esiti.items():
        (_ko if e["morti"] else _ok)(
            "tela larga %d ⇒ passo %d (%s): figlio MORTO di SIGSEGV %d volte su "
            "%d · vivo %d · non misurato %d · tele viste %s"
            % (largo, e["passo"],
               "multiplo di 64" if e["multiplo64"] else "⛔ NON multiplo di 64",
               e["morti"], o.giri, e["vivi"], e["ignoti"], e["tele"]))
    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "finestra.json"), "w") as fh:
        json.dump(esiti, fh, indent=1, ensure_ascii=False)
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ SCENA «CAPSULA» — `[?]` 2
# ═══════════════════════════════════════════════════════════════════════════
def occupante_riga(utente, resta):
    return ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
            "--utente %s --parola-file %s/parola --audio-codec pcm "
            "--video-codec h264 --adatta 1280x720 --resta %s"
            % (DENTRO_ALB, IND, PORTA, utente, DENTRO_LAV, resta))


def occupante_avvia(utente, resta):
    riga = catena_root("bash /media/REMOTIX/enter.sh --root %s"
                       % shlex.quote(occupante_riga(utente, resta)))
    return subprocess.Popen(["ssh", "-o", "BatchMode=yes", MACCHINA, riga],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def aspetta_posto(riga0, utente, tetto=90):
    scade = time.time() + tetto
    while time.time() < scade:
        t = registro_da(riga0) or ""
        if ("posto PRESO da %s" % utente) in t:
            return True
        time.sleep(1.0)
    return False


def scena_capsula(o):
    _log("LA SCENA: tabella PIENA, e il respinto e' un browser vero che NON si stacca")
    # ⛔⛔ IL NUMERO SI E' SPOSTATO — 25 agosto 2026, cura C3 della fase 10.
    #     Qui si leggeva `#define MAX_ATTACCATE` in `rcp.c`, e adesso quella
    #     riga dice `#define MAX_ATTACCATE RCP_TETTO_SESSIONI`: il modello
    #     `"MAX_ATTACCATE 16"` non ci finisce piu' dentro, la guardia passa
    #     SEMPRE, e il banco misurerebbe un server con sedici posti credendo di
    #     misurarne uno con uno.  ⇒ E' la stessa forma che ha rotto il terreno
    #     di `10-b93` (§5.4 conseguenza 1): un controllo che non morde piu' non
    #     da' un errore, da' un verde.
    rc, out, _ = root("grep -h '^#define RCP_TETTO_SESSIONI' %s/src/rcp.h" % ALB)
    _inf("il binario in prova: %s" % (out or "").strip())
    m = re.search(r"RCP_TETTO_SESSIONI\s+(\d+)", out or "")
    if m is None:
        _ko("⛔ non ho letto il tetto da %s/src/rcp.h: NON MISURO" % ALB)
        return 2
    if int(m.group(1)) > 2:
        _ko("⛔ l'albero ha il tetto a %s: riempirlo vorrebbe dire %s sessioni "
            "grafiche.  Ricompila con "
            "`MAX_ATT=1 bash banchi/10-b2-terreno.sh porta`"
            % (m.group(1), m.group(1)))
        return 2

    # ⭐ LA PAGINA COME IL SERVER LA SERVE, presa UNA volta e prima dei giri:
    #    il confronto con quel che il browser dipinge vale solo se i due testi
    #    vengono da strade diverse.
    html = pagina_servita()
    if html is None:
        _inf("⚠ la pagina servita NON e' stata letta: il confronto della frase "
             "col file restera' «non misurato», non «sbagliato»")
    else:
        _inf("pagina servita letta dal filo: %d byte · voce 0x%02x = «%s»"
             % (len(html), o.motivo_atteso,
                voce_del_file(html, o.motivo_atteso)))

    riga0 = righe_registro()
    if riga0 is None:
        _ko("⛔ registro del server illeggibile: NON MISURO")
        return 2
    # ⚠ Largo: ogni rifiuto costa una sessione grafica ANCHE al respinto
    #   (e' il difetto di §6.4 punto 6), e un occupante che se ne va a
    #   meta' campagna svuoterebbe la tabella senza dirlo.
    occ = occupante_avvia(UTENTE_A[0], o.giri * 45 + 150)
    if not aspetta_posto(riga0, UTENTE_A[0]):
        try:
            occ.kill()
        except Exception:
            pass
        _ko("⛔ il posto non si e' riempito: senza tabella piena la prova che "
            "segue misurerebbe un server LIBERO.  NON MISURO")
        return 2
    _ok("la tabella e' piena: adesso il browser e' il respinto")

    giri = []
    b = None
    try:
        b = Browser(porta_mar=o.marionette, headless=not o.con_schermo)
    except Exception as e:
        try:
            occ.kill()
        except Exception:
            pass
        _ko("⛔ Firefox non e' partito (%s: %s): NON MISURO" % (type(e).__name__, e))
        return 2
    try:
        for g in range(o.giri):
            r0 = righe_registro()
            b.carica()
            b.entra(UTENTE_A[0] if o.respinto_uguale else UTENTE_B[0],
                    PAROLA_UTENTE)
            t0 = time.time()
            oss = None
            while time.time() - t0 < 25:
                oss = b.leggi()
                e = esito_del_browser(oss)
                if e["come"] in ("errore", "capsula", "pagina"):
                    break
                time.sleep(0.15)
            time.sleep(1.5)          # ⛔ 500 ms di attesa + il volo: si aspetta
            oss = b.leggi()
            testo = registro_da(r0)
            c = giudica_capsula(oss, testo)
            # ⛔ QUANDO E' ARRIVATO IL `CONGEDO` — e NON si legge nel registro
            #    della pagina: su questa strada `collega()` scrive solo
            #    l'`esito`, e nessuna riga.  ⇒ L'ora e' quella del PRIMO esito,
            #    che l'osservatore marca appena `#esito` cambia.
            #    ⚠ Se l'osservatore l'ha perso, il ritardo e' `None`, non zero.
            esiti0 = oss.get("esiti") or []
            t_cong = esiti0[0]["t"] / 1000.0 if esiti0 else None
            e = esito_del_browser(oss)
            ritardo = None
            if t_cong is not None and e.get("t"):
                ritardo = e["t"] - t_cong
            esiti = oss.get("esiti") or []
            c["frase"] = esiti[-1]["testo"] if esiti else None
            c["giudizio_frase"] = giudica_frase(oss, html, o.motivo_atteso)
            c["ritardo_dal_congedo_s"] = ritardo
            c["righe"] = [x["riga"] for x in oss.get("righe", [])]
            giri.append(c)
            _inf("giro %d/%d · capsula %s · codice %s · %s s dopo il congedo · «%s»"
                 % (g + 1, o.giri,
                    {True: "ARRIVATA", False: "⛔ NO", None: "?"}[c["arrivata"]],
                    c.get("codice"),
                    "%.3f" % ritardo if ritardo is not None else "?",
                    (c.get("frase") or "")[:60]))
    finally:
        if b is not None:
            b.spegni()
        try:
            occ.kill()
        except Exception:
            pass
        root("pkill -f '[0]1-b3-cliente.py .*--porta %d'; true" % PORTA)

    arr = sum(1 for g in giri if g["arrivata"] is True)
    no = sum(1 for g in giri if g["arrivata"] is False)
    ign = sum(1 for g in giri if g["arrivata"] is None)
    _log("IL VERDETTO")
    _inf("⭐ letto NEL BROWSER, non nel registro del server")
    (_ok if arr == len(giri) and giri else _ko)(
        "la capsula di chiusura e' arrivata al browser **%d volte su %d** "
        "(non arrivata %d · non misurato %d)" % (arr, len(giri), no, ign))
    # ⚠ `str()` prima di ordinare: un codice `None` (la pagina ha scritto «?»)
    #   accanto a un intero farebbe esplodere l'ordinamento, e un banco che
    #   esplode nel riassunto perde la misura che aveva gia' in mano.
    cod = sorted(set(str(g.get("codice")) for g in giri if g["arrivata"]))
    _inf("codici visti dal browser: %s (atteso 0x%02x = %d)"
         % (cod, MOTIVO_PIENO, MOTIVO_PIENO))
    rit = [g["ritardo_dal_congedo_s"] for g in giri
           if g["ritardo_dal_congedo_s"] is not None]
    if rit:
        _inf("ritardo fra il CONGEDO e la capsula: mediano %.3f s, da %.3f a %.3f"
             % (sorted(rit)[len(rit) // 2], min(rit), max(rit)))
    for g in giri:
        if g.get("vietato"):
            _ko(g["vietato"])
    srv = [g.get("server") for g in giri if g.get("server")]
    if srv:
        _inf("⚠ e il registro del SERVER, per confronto (NON e' il verdetto): "
             "armate %d, spedite %d"
             % (sum(s["armate"] for s in srv), sum(s["spedite"] for s in srv)))
    frasi = sorted(set(g.get("frase") or "(nessuna)" for g in giri))
    for f in frasi:
        _inf("la pagina ha mostrato: «%s»" % f)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⭐⭐ IL VERDETTO SULLA FRASE — ed e' quel che l'utente VEDE
    # ═══════════════════════════════════════════════════════════════════════
    _log("LA FRASE CHE L'UTENTE LEGGE — letta NEL BROWSER, e confrontata col file servito")
    gf = [g.get("giudizio_frase") for g in giri if g.get("giudizio_frase")]
    esito_frase = 0
    if not gf:
        _ko("⛔ nessuna frase giudicata: NON HO MISURATO")
        esito_frase = 2
    else:
        def conta(chiave, valore):
            return sum(1 for x in gf if x.get(chiave) is valore)

        for chiave, testo in (
                ("concordano",
                 "⛔ la frase del BROWSER e la voce 0x%02x del FILE SERVITO "
                 "coincidono byte per byte" % o.motivo_atteso),
                ("dice_di_chi",
                 "la frase dice DI CHI e' il limite (nomina il server) — "
                 "predicato lessicale, vedi il riquadro"),
                ("da_un_gesto",
                 "la frase da' un GESTO che il prodotto offre davvero")):
            si, no, nm = conta(chiave, True), conta(chiave, False), conta(chiave, None)
            if nm:
                _dub("%s: ⛔ NON MISURATO in %d giri su %d (si' %d · no %d)"
                     % (testo, nm, len(gf), si, no))
                esito_frase = max(esito_frase, 2)
            elif si == len(gf):
                _ok("%s — %d su %d" % (testo, si, len(gf)))
            else:
                _ko("%s — ⛔ solo %d su %d" % (testo, si, len(gf)))
                esito_frase = max(esito_frase, 1)
        # ⛔ E QUANDO I DUE TESTI NON COINCIDONO SI STAMPANO TUTT'E DUE: e' la
        #    forma d'errore che questo pezzo esiste per prendere, e un rosso che
        #    non fa vedere le due meta' non si puo' diagnosticare.
        for x in gf:
            if x.get("concordano") is False:
                _ko("⛔⛔ IL BANCO CHE LEGGE IL FILE SAREBBE VERDE, IL BROWSER NO:")
                _inf("    file servito (0x%02x): «%s»" % (x["motivo"], x["file"]))
                _inf("    browser:              «%s»" % x["browser"])
                break
        verdi = sum(1 for x in gf if x.get("verdetto") == "verde")
        rossi = sum(1 for x in gf if x.get("verdetto") == "rosso")
        muti = sum(1 for x in gf if x.get("verdetto") is None)
        (_ok if verdi == len(gf) else _ko)(
            "verdetto sulla frase: ⭐ %d verdi · ⛔ %d rossi · %d non misurati "
            "(su %d giri)" % (verdi, rossi, muti, len(gf)))

    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "capsula.json"), "w") as fh:
        json.dump({"giri": giri, "arrivate": arr, "su": len(giri),
                   "motivo_atteso": o.motivo_atteso,
                   "voce_del_file": voce_del_file(html, o.motivo_atteso)},
                  fh, indent=1, ensure_ascii=False)
    if giri and ign == 0 and esito_frase == 0:
        return 0
    return 2


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA TARATURA DELLO STRUMENTO «CAPSULA» — si inietta il caso NOTO senza
#    capsula, e si guarda se lo strumento lo chiama cosi'
# ═══════════════════════════════════════════════════════════════════════════
def taratura(o):
    """⛔ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33).

    Lo strumento e': *«`wt.closed` che si risolve = capsula arrivata;
    `wt.closed` che rifiuta = niente capsula»*.  ⚠ E' quel che la piattaforma
    promette, ma promesso non e' misurato.  ⇒ Si inietta il caso NOTO in cui la
    capsula **non puo'** essere arrivata — il server viene ucciso di netto
    (`SIGKILL`): nessun `CONGEDO`, nessuna capsula, nessun `CONNECTION_CLOSE` —
    e lo strumento deve dire **«errore»**, non «capsula».

    ⚠ Costa quanto l'inattivita' di QUIC (`IDLE_MS` = 30 s in `trasporto.c`).
    """
    _log("⛔ LA TARATURA — si inietta «nessuna capsula» e si guarda che cosa dice")
    b = None
    try:
        b = Browser(porta_mar=o.marionette + 1, headless=True)
        b.carica()
        b.entra(UTENTE_A[0], PAROLA_UTENTE)
        t0 = time.time()
        aperta = False
        while time.time() - t0 < 90:
            oss = b.leggi()
            if c_e(oss, APERTA):
                aperta = True
                break
            time.sleep(0.5)
        if not aperta:
            _ko("⛔ la sessione non si e' aperta: la taratura non e' stata fatta")
            return None
        _ok("sessione aperta · adesso uccido il server di netto (SIGKILL)")
        root("systemctl kill -s KILL %s.service; true" % UNITA)
        t1 = time.time()
        e = {"come": "viva"}
        while time.time() - t1 < 75:
            oss = b.leggi()
            e = esito_del_browser(oss)
            if e["come"] in ("errore", "capsula", "pagina"):
                break
            time.sleep(0.5)
        _inf("dopo %.1f s lo strumento dice «%s» (codice %s)"
             % (time.time() - t1, e["come"], e.get("codice")))
        if e["come"] == "errore":
            _ok("⭐ METRO TARATO: senza capsula lo strumento dice «errore», "
                "non «capsula»")
            return True
        _ko("⛔ METRO NON TARATO: senza capsula lo strumento ha detto «%s»"
            % e["come"])
        return False
    except Exception as ex:
        _ko("⛔ la taratura non e' riuscita (%s: %s)" % (type(ex).__name__, ex))
        return None
    finally:
        if b is not None:
            b.spegni()


def principale():
    a = argparse.ArgumentParser()
    a.add_argument("--certifica", action="store_true",
                   help="⭐ innesta i guasti e conta sano→guasto→risanato, "
                        "senza rete e senza macchina")
    a.add_argument("--scena", choices=("viva", "capsula", "taratura", "finestra"))
    a.add_argument("--durata", type=float, default=120.0)
    a.add_argument("--giri", type=int, default=10)
    a.add_argument("--marionette", type=int, default=2860)
    # ⭐ Il motivo la cui voce si va a cercare nel file servito.  ⛔ Serve al
    #    controllo negativo di punto 4: si tiene `0x0E` mentre si fa arrivare al
    #    browser un congedo `0x0F`, e il banco DEVE accorgersi che il testo che
    #    ha dichiarato giusto leggendo il file non e' quello che il browser ha
    #    mostrato.  Un banco che legge solo il file non se ne accorge.
    a.add_argument("--motivo-atteso", type=lambda s: int(s, 0),
                   default=MOTIVO_PIENO,
                   help="il motivo di §8.2 la cui voce si cerca nel file "
                        "servito (predefinito 0x0E)")
    # ⭐ Chi viene respinto.  ⛔ `--respinto-uguale` lo fa entrare con lo STESSO
    #    utente dell'occupante: `posto_prendi()` allora risponde `0x0F` (posto
    #    occupato) e non `0x0E` — due strade diverse, e la seconda serve
    #    apposta a far divergere la frase dal file.
    a.add_argument("--respinto-uguale", action="store_true",
                   help="il respinto e' lo STESSO utente dell'occupante ⇒ 0x0F")
    a.add_argument("--con-schermo", action="store_true")
    a.add_argument("--senza-audio-silenzio", action="store_true",
                   help="⭐ il BRACCIO DI CONTROLLO: dichiara che il server e' "
                        "acceso con `--niente-audio-silenzio`.  ⛔ Non lo "
                        "accende lui: lo fa il terreno, e questo lo scrive")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if o.scena == "viva":
        return scena_viva(o)
    if o.scena == "capsula":
        return scena_capsula(o)
    if o.scena == "finestra":
        return scena_finestra(o)
    if o.scena == "taratura":
        return 0 if taratura(o) else 3
    print("⛔ serve --certifica oppure --scena viva|capsula|finestra|taratura")
    return 2


if __name__ == "__main__":
    sys.exit(principale())
