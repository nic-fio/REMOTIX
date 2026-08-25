#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
10-b97-guardiano — ⛔⛔ LA SOGLIA DEL GUARDIANO DI LOGIND (rilievo R10-A3).

Un difetto DEDOTTO leggendo il codice, che qui si misura o si ritira.

---------------------------------------------------------------------------
IL DIFETTO, COME ERA STATO DEDOTTO (`fasi/10-multi-tenant-e-il-budget.md` §4.2)

  · `webtransport.c:5364 wt_sorveglia_locali()` cicla su TUTTE le sessioni
    attaccate e per ognuna chiama il gancio del guardiano;
  · il gancio e' `main.c:1029 chiedi_sessione_locale()`, che fa una chiamata
    SINCRONA a logind — nessuna cache, attesa massima 300 ms
    (`sentinella.c:30 ATTESA_MS`);
  · il ripasso gira ogni 2 s (`main.c:130 RIPASSO_LOCALI_MS`) DENTRO lo stesso
    `poll` che consegna i fotogrammi;
  ⇒ il costo e' LINEARE negli inquilini, e mentre il ciclo e' fermo `lm_usciti`
    non sale per NESSUNA sessione mentre `lm_offerti` continua a salire
    ⇒ superati i 5 s (`WT_LM_STALLO_MS`) `linea_morta_scatta()` butta fuori
    tutti, ognuno con la frase «la linea e' MORTA» — che ACCUSA LA RETE
    DELL'UTENTE per un difetto della macchina.

---------------------------------------------------------------------------
⭐ LA LEVA — e la dichiara il prodotto stesso

`src/main.c:1028` dice, testualmente, che l'adattatore sta li' perche' *«il
banco possa innestare un guardiano finto senza toccare il trasporto»*.
⇒ `banchi/10-b97-innesta.py` sostituisce QUEL SOLO adattatore nella copia
  sulla macchina di prova.  `webtransport.c` non cambia di una virgola, e
  `src/main.c` del repository nemmeno: gli md5 lo dicono.

Il guardiano finto dorme **D** millisecondi invece di chiamare logind, e legge
D da un file — cosi' la superficie (D, N) si misura senza riaccendere il
server, cioe' senza rifare sette sessioni grafiche.

⭐⭐ E IL COSTO CHE CONTA E' IL PRODOTTO N×D, non D: il ciclo `poll` si ferma
    per la somma delle chiamate di un ripasso.  ⇒ La griglia si percorre a
    **P = N×D costante**, e la domanda «cresce con gli inquilini?» diventa
    «a parita' di P il confine e' lo stesso?».

---------------------------------------------------------------------------
⛔ CHE COSA QUESTO BANCO **NON** SA DIRE — detto prima, non dopo

 1. ⛔ NON dice quanto e' lento logind su una macchina MALATA.  Misura quanto
    costa `ListSessions` su QUESTA macchina, con le sessioni che QUESTA
    macchina ha — e su una macchina di prova condivisa il pavimento e' alto
    (decine di sessioni `linger` di altri agenti) e non si puo' abbassare.
 2. ⛔ NON prova che logind possa arrivare alla soglia.  Prova che SE ci
    arrivasse il prodotto butterebbe fuori tutti, e a quale valore.  La
    condizione la fa scattare il numero degli inquilini, non la fortuna —
    ⚠ ma il valore assoluto di partenza e' misurato, non supposto.
 3. ⚠ NON misura la SECONDA strada allo stesso scatto (una sessione bloccata
    dal controllo di congestione mentre il palco produce): il banco la nomina
    e dice quale banco la chiuderebbe.
 4. ⚠ Il tetto vero degli inquilini qui e' SETTE, non dieci: `posto_prendi()`
    risponde `POSTO_OCCUPATO` al secondo attacco dello stesso nome, quindi N
    sessioni vogliono N utenti, e l'incarico ne assegna sette.
 5. ⛔ NON parla della GPU.  Il carico grafico serve solo a far PRODURRE i
    palchi: senza fotogrammi offerti `avevo_da_mandare` e' falso e il
    meccanismo non puo' scattare — un verde per costruzione.

---------------------------------------------------------------------------
Uso (dal portatile):

    python3 banchi/10-b97-guardiano.py --certifica     # ⛔ i guasti innestati
    python3 banchi/10-b97-guardiano.py taratura        # il metro, a valore noto
    python3 banchi/10-b97-guardiano.py logind          # il costo vero di ListSessions
    python3 banchi/10-b97-guardiano.py soglia          # la superficie (D, N)
    python3 banchi/10-b97-guardiano.py tutto
    python3 banchi/10-b97-guardiano.py stato|sgombra

Codici d'uscita — ⛔⛔ e i primi due sono GIUDIZI, gli altri no:

    0  ⭐ GIUDIZIO: tutti i predicati hanno fatto quel che era scritto prima
    1  ⛔ GIUDIZIO: almeno un rosso
    3  ⚠ «NON HO NIENTE DA GIUDICARE» — e non e' un verde educato: ho
          misurato, e qualche predicato non ha potuto pronunciarsi
    2  ⛔ uso sbagliato, terreno che non regge
    4  ⛔ IL TURNO NON E' MAI ARRIVATO — il lucchetto della GPU non si e'
          liberato in tempo.  ⛔ NON e' un problema di terreno e non e' un
          giudizio: **la domanda non e' mai stata posta.**

⛔⛔ CHI LANCIA QUESTO BANCO RIMETTE IN CODA **SOLO** L'USCITA 4.
   Un giro che ha dato un giudizio — regge (0), non regge (1), o «non giudico»
   (3) — **non si rifa' mai**: rifarlo vorrebbe dire misurare due volte finche'
   non esce il numero che piace, che e' il modo di trasformare un banco in un
   avvocato.  ⭐ `/tmp/10-b97/pilota.sh` fa esattamente questo, e non di piu'.
===========================================================================
"""
import argparse
import importlib.util
import json
import os
import re
import signal
import statistics
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
IO_SONO = os.environ.setdefault("IO_SONO", "10-b6")
PORTA = int(os.environ.setdefault("PORTA", "8160"))
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10b6")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10b6-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10b6-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10b6")
UNITA = os.environ.setdefault("UNITA", "remotix-%d" % PORTA)
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
os.environ.setdefault("QUANTI", "7")
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
FUORI = os.environ.get("FUORI", "/tmp/10-b97")

# ⛔ I MIEI utenti, e l'uid segue il nome per costruzione come nel terreno.
UID_BASE = 1159
QUANTI_MAX = 7

# Il file da cui il guardiano finto legge il ritardo (lo stesso che
# `10-b97-innesta.py --file=` ha compilato dentro il binario).
FILE_RITARDO = "%s/b97-ritardo" % LAV
REGISTRO = "%s/registro.log" % LAV

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `SOGLIA_STALLO_MS` NON e' una scelta di questo banco: e' il predefinito del
#    prodotto (`webtransport.c` WT_LM_STALLO_MS).  Sta qui perche' due predicati
#    ne hanno bisogno, e perche' un giro piu' corto di questo NON PUO' vedere
#    uno scatto — il banco lo dice invece di dare verde.
SOGLIA_STALLO_MS = 5000
# ⛔ Il giro minimo perche' uno scatto sia POSSIBILE: la soglia dello stallo,
#    piu' il ripasso (2 s) che deve arrivare, piu' un respiro.  Sotto, il banco
#    NON GIUDICA: e' il guasto «il giro sano e' troppo corto» del `--certifica`.
GIRO_MINIMO_S = (SOGLIA_STALLO_MS / 1000.0) + 2.0 + 3.0
# La taratura del metro: si inietta questo e si pretende di ritrovarlo.
TARA_MS = 150
TARA_TOLLERANZA = 0.12      # ±12 % — il `nanosleep` non e' un orologio atomico
# Quante chiamate al guardiano devono essere ARRIVATE perche' una cella conti
# (`LEZIONI.md` §1.30: si conta la sollecitazione, non la si presume).
CHIAMATE_MINIME = 3
# I fotogrammi che il palco deve aver offerto perche' «zero scatti» voglia dire
# qualcosa: sotto, il verde e' PER COSTRUZIONE.
OFFERTI_MINIMI = 5


# ═══════════════════════════════════════════════════════════════════════════
# GLI ATTREZZI CHE ESISTONO GIA' — si chiamano, non si riscrivono
# ═══════════════════════════════════════════════════════════════════════════
def _carica(nome, file_):
    perc = os.path.join(QUI, file_)
    if not os.path.exists(perc):
        raise SystemExit("⛔ NON MISURO: manca «%s»" % perc)
    s = importlib.util.spec_from_file_location(nome, perc)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


b92 = None
luc = None


def apri_attrezzi():
    """⛔ `10-b92-dieci.py` porta il cliente, le scene, il ritaglio e il
       trasporto verso la macchina.  ⭐ Si importa e si RIBATTEZZANO gli utenti:
       i `provamt*` sono di un altro incarico e questo banco non li tocca."""
    global b92, luc
    b92 = _carica("b92", "10-b92-dieci.py")
    b92.UID_BASE = UID_BASE
    b92.utente = lambda i: "provaf%d" % i
    b92.uid = lambda i: UID_BASE + i
    # ⛔ `/dev/shm` e' UNO su tutta la macchina: il nome della scena dev'essere
    #    mio, o `shm_open` risponde «Permission denied» sul segmento di un altro
    #    agente e la scena non parte — cioe' il palco non produce, cioe' il
    #    meccanismo non puo' scattare e il banco darebbe un verde per
    #    costruzione.  ⚠ E' successo davvero, al primo giro di messa a punto.
    b92.SHM_NOME = "/10b97"
    luc = _carica("luc", "09-lucchetto.py")
    return b92, luc


def guardiano_a_riposo(perche=""):
    """⛔⛔ IL GUARDIANO SI RIMETTE A ZERO PRIMA DI APRIRE O RIAPRIRE UNA SESSIONE.

    `[M]` 25 agosto 2026, e la rampa si e' fermata al primo N per questo: col
    guardiano finto a 5000 ms **una sessione nuova non si apre affatto** — il
    cliente muore di `TimeoutError` nella stretta di mano, perche' il ciclo
    `poll` che deve rispondergli e' fermo cinque secondi per volta, e la domanda
    del guardiano la fa ANCHE `rcp.c` all'`ATTACCA`.

    ⭐ E' un fatto del PRODOTTO che vale la pena riferire — un inquilino lento
       non solo rallenta chi c'e', **impedisce a chi arriva di entrare**.
    ⛔ Ma dentro il banco e' un guasto MIO: senza questa riga i gradini
       successivi risultano «il terreno delle sessioni non regge», che accusa il
       terreno di un difetto del banco.

    ⚠ Con ZERO sessioni attaccate il gancio non viene chiamato e la riga `CAMBIO`
      non arriva: non e' un guasto, e' il prodotto (`wt_sorveglia_locali()` cicla
      sulle sessioni).  ⇒ In quel caso si scrive il file e si prosegue,
      dichiarandolo.
    """
    giro = "riposo-%d" % int(time.time() * 1000)
    vive = [i for i in range(1, QUANTI_MAX + 1) if b92.vivo(i)]
    if not vive:
        b92.root("printf '%%s %%d\\n' '%s' 0 > %s" % (giro, FILE_RITARDO))
        _inf("guardiano a riposo (D=0)%s — ⚠ nessuna sessione attaccata, quindi "
             "il file lo leggera' la prima che entra" % (": " + perche if perche else ""))
        return True
    ok, detto = ritardo_poni(giro, 0, tetto_s=20.0)
    if ok:
        _inf("guardiano a riposo (D=0)%s" % (": " + perche if perche else ""))
    else:
        _ko("⛔ non sono riuscito a rimettere il guardiano a riposo: %s" % detto)
    return ok


def accendi_scena(i, movimento="pieno"):
    """La scena di `b92`, con il MIO nome di `/dev/shm`.  ⛔ Tre tentativi, e il
       registro della scena si conserva: una scena che non parte deve poter dire
       perche'."""
    n = b92.uid(i)
    log = "%s/scena-%d.log" % (LAV, i)
    # ⛔⛔ PRIMA SI SPEGNE QUELLA CHE C'E', E NON E' PULIZIA: e' che questa
    #     funzione viene richiamata anche per una sessione RIAPERTA dopo uno
    #     scatto, e senza questa riga il secondo giro lascerebbe DUE scene
    #     addosso allo stesso utente.  ⚠ Il carico raddoppiato non da' rosso:
    #     da' celle successive misurate su una macchina piu' carica di quella
    #     dichiarata, cioe' la forma peggiore.
    b92.root("pkill -u %d -f '04-b30-scena --uscita' ; true" % n)
    time.sleep(0.6)
    for tentativo in range(3):
        usc = b92.uscita_del(i)
        if not usc:
            time.sleep(3.0)
            continue
        b92.root(
            "setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
            "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
            "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
            "%s --uscita %s --movimento %s --shm /10b97-%d --giro b97-%d "
            ">> %s 2>&1 & echo acceso"
            % (n, n, b92.utente(i), b92.utente(i), n, b92.SCENA_BIN, usc,
               movimento, i, i, log))
        time.sleep(2.5)
        rc, out, _ = b92.root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
        if out.strip():
            return usc
        rc, out, _ = b92.root("tail -3 %s 2>/dev/null || true" % log)
        _dub("⚠ la scena di s%d non e' partita al tentativo %d — dice: %s"
             % (i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


def orologio_ms():
    """⛔ L'orologio DELLA MACCHINA DI PROVA, `CLOCK_MONOTONIC`, in ms — lo
       stesso asse su cui scrivono i giornali dei clienti.  `None` se non l'ho
       letto: un tempo indovinato ritaglierebbe la fetta sbagliata."""
    rc, out, _ = b92.rem("python3 -c 'import time;"
                         "print(time.clock_gettime(time.CLOCK_MONOTONIC)*1000)'")
    try:
        return float(out.strip())
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA LEVA — porre D, e PRETENDERE la prova che abbia preso
# ═══════════════════════════════════════════════════════════════════════════
def ritardo_poni(giro, ritardo_ms, tetto_s=25.0):
    """Scrive `<giro> <ritardo_ms>` nel file e ASPETTA la riga `CAMBIO` con
       QUESTO giro nel registro del server.

    ⛔⛔ E' il predicato piu' importante del banco: se la leva non ha preso, ogni
        cella successiva conterebbe zero scatti su un prodotto che nessuno ha
        sollecitato — cioe' direbbe «tutto bene» avendo misurato niente.
        ⇒ Torna `(False, perche')`, e il banco NON GIUDICA quella cella.

    ⚠ E il ritardo si applica solo mentre c'e' almeno una sessione ATTACCATA: il
      gancio lo chiama `wt_sorveglia_locali()`, che cicla sulle sessioni.  Con
      zero sessioni il file non viene nemmeno riletto — e non e' un guasto, e'
      il prodotto.
    """
    b92.root("printf '%%s %%d\\n' '%s' %d > %s" % (giro, ritardo_ms, FILE_RITARDO))
    fine = time.time() + tetto_s
    while time.time() < fine:
        rc, out, _ = b92.root(
            "grep -ac 'b97-guardiano CAMBIO giro=%s ritardo_ms=%d' %s || true"
            % (giro, ritardo_ms, REGISTRO))
        t = out.strip()
        if t.isdigit() and int(t) > 0:
            return True, "la leva ha preso (giro=%s, D=%d ms)" % (giro, ritardo_ms)
        time.sleep(1.0)
    return False, ("⛔ LA LEVA NON HA PRESO in %.0f s: nessuna riga «b97-guardiano "
                   "CAMBIO giro=%s ritardo_ms=%d» nel registro.  ⛔ NON HO "
                   "MISURATO — e questo non e' «nessuno scatto: tutto bene»."
                   % (tetto_s, giro, ritardo_ms))


def innesto_c_e():
    """`True` se il binario acceso PORTA il guardiano finto.  ⛔ `None` se non
       ho potuto guardare."""
    rc, out, _ = b92.root("grep -ac 'b97-guardiano INNESTATO' %s || true" % REGISTRO)
    t = out.strip()
    if not t.isdigit():
        return None
    return int(t) > 0


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL LETTORE DEL REGISTRO — una passata sola, e per OFFSET IN BYTE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ L'ANCORA, ED E' DOPPIA.  Il difetto che questo banco cerca lascia UNA
#     RIGA, e quella riga resta nel registro per sempre: contarla due volte, o
#     contare quella del giro precedente, sarebbe la forma d'errore piu' facile
#     di tutte.
#       1. la finestra e' `[r0, r1]` in BYTE, letti col server acceso prima e
#          dopo la cella (`10-b92-dieci.py` fa lo stesso);
#       2. ⭐ e dentro la finestra si pretende che il GIRO in vigore sia il mio:
#          ogni riga `b97-guardiano` porta `giro=`, e una cella che non trova
#          nemmeno una riga col proprio giro NON GIUDICA.
#     ⇒ Un conto letto dal giro precedente e' impossibile per costruzione: quel
#       giro ha un altro nonce.

LETTORE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b97-lettore — la fetta del registro fra due offset, in UNA passata."""
import json, re, sys

percorso, r0, r1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
with open(percorso, "rb") as f:
    f.seek(r0)
    testo = f.read(max(0, r1 - r0)).decode("utf-8", "replace")

GUARD = re.compile(r"b97-guardiano giro=(\S+) ritardo_ms=(-?\d+) finto=(\S+) "
                   r"chiamate=(\d+) costo_us=(-?\d+) utente=(\S+) esito=(\d+)")
CAMBIO = re.compile(r"b97-guardiano CAMBIO giro=(\S+) ritardo_ms=(-?\d+)")
MORTA = re.compile(r"linea-morta (\S+) (causa=.*?) giudizio=")
CAMPO = re.compile(r"(\w+)=([^\s]+)")
CICLO = re.compile(r"ciclo: (\d+) fotogrammi consegnati")
SPEDITO = re.compile(r"fotogramma (\d+) SPEDITO")

guardiano, cambi, scatti = [], [], []
consegnati, spediti, righe = 0, 0, 0
for riga in testo.splitlines():
    righe += 1
    g = GUARD.search(riga)
    if g:
        guardiano.append({"giro": g.group(1), "ritardo_ms": int(g.group(2)),
                          "finto": g.group(3) == "si",
                          "chiamate": int(g.group(4)),
                          "costo_us": int(g.group(5)), "utente": g.group(6)})
        continue
    c = CAMBIO.search(riga)
    if c:
        cambi.append({"giro": c.group(1), "ritardo_ms": int(c.group(2))})
        continue
    m = MORTA.search(riga)
    if m:
        d = {k: v for k, v in CAMPO.findall(m.group(2))}
        d["provenienza"] = m.group(1)
        scatti.append(d)
        continue
    k = CICLO.search(riga)
    if k:
        consegnati += int(k.group(1))
        continue
    if SPEDITO.search(riga):
        spediti += 1

print(json.dumps({"esito": "letto", "byte0": r0, "byte1": r1, "righe": righe,
                  "guardiano": guardiano, "cambi": cambi, "scatti": scatti,
                  "consegnati_dal_palco": consegnati,
                  "fotogrammi_spediti": spediti}))
'''


def registro_byte():
    """A che punto e' il registro, in byte.  ⛔ `None` se non l'ho letto: uno
       zero che vuol dire «non ho letto» e uno che vuol dire «non e' successo
       niente» non devono avere la stessa faccia."""
    rc, out, err = b92.root("stat -c %%s %s" % REGISTRO)
    t = out.strip()
    if rc != 0 or not t.isdigit():
        return None
    n = int(t)
    return n if n > 0 else None


def registro_fetta(r0, r1):
    """⛔ `{"esito": "..."}` se non ho letto.  Mai un dizionario vuoto."""
    if r0 is None or r1 is None or r1 < r0:
        return {"esito": "⛔ NON HO LETTO — confini «%s»→«%s»" % (r0, r1)}
    rc, out, err = b92.root("python3 %s/10-b97-lettore.py %s %d %d"
                            % (LAV, REGISTRO, r0, r1), 600)
    try:
        return json.loads(out)
    except Exception as e:
        return {"esito": "⛔ NON HO LETTO — il lettore non ha risposto: %s — %s"
                         % (e, (out + err)[-200:])}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I GIUDIZI — funzioni PURE, cosi' il `--certifica` puo' innestare i guasti
#      senza toccare la macchina.  Ne torna `(esito, perche)`:
#         True  l'atteso ha retto · False ⛔ rosso · None ⚠ NON GIUDICO
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def giudica_cella(cella):
    """⛔ IL GIUDIZIO DI UNA CELLA (N, D), e ha quattro cancelli in fila.  Ogni
       cancello che si chiude produce `None`, mai un verde.

       1. la leva ha preso?          (senza, non ho misurato)
       2. il guardiano ha morso?     (chiamate col MIO giro nella finestra)
       3. il giro era abbastanza lungo perche' uno scatto fosse POSSIBILE?
       4. i palchi PRODUCEVANO?      (senza, «zero scatti» e' per costruzione)
    """
    if not cella.get("leva"):
        return _muto("⛔ NON HO MISURATO: %s" % cella.get("leva_perche", "la leva non ha preso"))
    fetta = cella.get("fetta") or {}
    if fetta.get("esito") != "letto":
        return _muto("⛔ NON HO MISURATO: la fetta del registro — %s"
                     % fetta.get("esito", "?"))
    mie = [g for g in fetta["guardiano"] if g["giro"] == cella["giro"]]
    if len(mie) < CHIAMATE_MINIME:
        return _muto("⛔ NON HO MISURATO: solo %d chiamate al guardiano col MIO "
                     "giro «%s» nella finestra (ne servono %d).  ⚠ Una prova che "
                     "non morde da' un giudizio che sembra un risultato "
                     "(`LEZIONI.md` §1.30)" % (len(mie), cella["giro"], CHIAMATE_MINIME))
    if cella["durata_s"] < GIRO_MINIMO_S:
        return _muto("⛔ NON HO MISURATO: il giro e' durato %.1f s, e sotto %.1f s "
                     "uno scatto NON PUO' avvenire (soglia dello stallo %d ms + un "
                     "ripasso + un respiro).  ⚠ Un verde qui sarebbe per "
                     "costruzione" % (cella["durata_s"], GIRO_MINIMO_S, SOGLIA_STALLO_MS))
    # ⛔⛔ IL CARICO DEV'ESSERE ADDOSSO, E SI GUARDA — non si presume.
    #
    #     `[M]` 24 agosto 2026, su questa macchina: **a scena SPENTA il palco
    #     consegna quasi niente, `avevo_da_mandare` e' FALSO e la linea morta
    #     non scatta nemmeno con il ciclo fermo TRE SECONDI per volta**.  Con la
    #     scena accesa, la stessa cella butta fuori l'utente in sei secondi.
    #     ⇒ Un banco che non guardasse le scene darebbe VERDE per costruzione, e
    #       il verde sarebbe indistinguibile da «il difetto non c'e'».
    #
    # ⚠ E la scena viva e' il testimone GIUSTO, non i fotogrammi arrivati al
    #   cliente: quelli vanno a zero proprio quando il difetto morde, quindi
    #   userebbero il sintomo come prova della premessa.
    vive, attese = cella.get("scene_vive"), cella.get("quanti")
    if vive is None:
        return _muto("⛔ NON HO MISURATO: non so se le scene stessero disegnando")
    if vive < attese:
        return _muto("⛔ NON GIUDICO: solo %d scene su %d stavano disegnando.  "
                     "⛔ A palco fermo `avevo_da_mandare` e' FALSO e il "
                     "meccanismo NON PUO' scattare: un verde qui sarebbe PER "
                     "COSTRUZIONE" % (vive, attese))
    offerti = cella.get("offerti_nella_finestra")
    if offerti is None:
        return _muto("⛔ NON HO MISURATO: non so quanti fotogrammi i palchi "
                     "abbiano offerto nella finestra")
    if offerti < OFFERTI_MINIMI and not cella["scatti"]:
        return _muto("⛔ NON GIUDICO «zero scatti»: i palchi hanno offerto %d "
                     "fotogrammi (< %d).  ⛔ Con `offerti=0` `avevo_da_mandare` e' "
                     "FALSO e il meccanismo NON PUO' scattare: quel verde sarebbe "
                     "PER COSTRUZIONE" % (offerti, OFFERTI_MINIMI))
    return _si("cella misurata: %d chiamate al guardiano, %d/%d scene che "
               "disegnano, %d fotogrammi offerti, %.1f s"
               % (len(mie), vive, attese, offerti, cella["durata_s"]))


def giudica_meccanismo(cella):
    """⛔ LA PROVA CHE IL MECCANISMO E' QUELLO DEDOTTO, e non un altro.

    Non basta che qualcuno venga staccato: la riga del prodotto deve dire
      · `causa=stallo`  — «non passavano byte», non «il client tace»;
      · `persi=0`       — su una linea PULITA: se si perdesse, la colpa
                          sarebbe della rete e il difetto dedotto e' un altro;
      · `offerti>0`     — il palco stava producendo, cioe' `avevo_da_mandare`
                          era vero per la ragione giusta;
      · `usciti_byte=0` — e non usciva niente.
    """
    scatti = cella.get("scatti")
    if not scatti:
        return _si("nessuno scatto in questa cella (e non c'e' niente da attribuire)")
    guai, buoni = [], 0
    for s in scatti:
        causa = s.get("causa")
        if causa != "stallo":
            guai.append("⛔ scatto con causa=%s (non «stallo»): il difetto dedotto "
                        "NON E' QUESTO e va ritirato per questa riga — %s"
                        % (causa, s.get("provenienza")))
            continue
        persi = int(s.get("persi", "-1"))
        if persi != 0:
            guai.append("⛔ scatto con persi=%d: la linea NON era pulita, e la "
                        "causa puo' essere la rete — %s" % (persi, s.get("provenienza")))
            continue
        offerti = int(s.get("offerti", "-1"))
        usciti = int(s.get("usciti_byte", "-1"))
        if offerti <= 0:
            guai.append("⛔ scatto con offerti=%d: il palco non stava producendo, "
                        "quindi non e' il meccanismo di R10-A3" % offerti)
            continue
        if usciti != 0:
            guai.append("⚠ scatto con usciti_byte=%d: qualcosa era uscito, e lo "
                        "stallo non e' totale" % usciti)
            continue
        buoni += 1
    if guai:
        return _no(" · ".join(guai[:4]))
    return _si("%d scatti su %d sono il meccanismo dedotto: causa=stallo, persi=0, "
               "offerti>0, usciti_byte=0 su linea pulita" % (buoni, len(scatti)))


def giudica_controllo(cella_zero):
    """⛔ IL BRACCIO DI CONTROLLO — guardiano finto a 0 ms, stessa N.

    Senza questo braccio non si e' attribuito NIENTE: gli scatti potrebbero
    venire dal carico, dalla GPU satura, dai sette GNOME.  ⇒ A D=0 devono essere
    ZERO.  ⚠ E se non ci sono state abbastanza chiamate, non e' uno zero: e' un
    «non lo so».
    """
    passa, perche = giudica_cella(cella_zero)
    if passa is None:
        return _muto("il braccio di controllo NON ha misurato: %s" % perche)
    if cella_zero["scatti"]:
        return _no("⛔ IL BRACCIO DI CONTROLLO HA SCATTATO: %d scatti col "
                   "guardiano a 0 ms.  ⇒ Gli scatti delle altre celle NON sono "
                   "attribuibili al guardiano" % len(cella_zero["scatti"]))
    return _si("controllo a D=0 con N=%d: ZERO scatti su %.0f s ⇒ quel che scatta "
               "altrove e' il guardiano" % (cella_zero["quanti"], cella_zero["durata_s"]))


def giudica_taratura(campioni, atteso_ms):
    """⛔ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33): si inietta un valore NOTO
       e si guarda se il metro lo ritrova."""
    if not campioni:
        return _muto("⛔ NON HO TARATO: nessun campione di `costo_us`")
    med = statistics.median(campioni) / 1000.0
    basso = atteso_ms * (1 - TARA_TOLLERANZA)
    alto = atteso_ms * (1 + TARA_TOLLERANZA) + 5
    if not (basso <= med <= alto):
        return _no("⛔ IL METRO NON RITROVA IL VALORE NOTO: iniettati %d ms, "
                   "misurati %.1f ms (ammesso %.0f-%.0f).  ⇒ I numeri che ne "
                   "escono non sono misure" % (atteso_ms, med, basso, alto))
    return _si("metro tarato: iniettati %d ms, il registro ne dice %.1f "
               "(%d campioni)" % (atteso_ms, med, len(campioni)))


def giudica_crescita(per_n):
    """⭐ IL COSTO CRESCE COGLI INQUILINI — la riga che rende il difetto
       «condizionato al numero», non alla fortuna.

    `per_n` = {N: chiamate_per_ripasso}.  Si pretende che le chiamate di un
    ripasso siano N, cioe' che il costo del ripasso sia N × D.
    """
    if len(per_n) < 2:
        return _muto("⛔ NON GIUDICO la crescita: ho un solo valore di N")
    guai = []
    for n, quante in sorted(per_n.items()):
        if quante is None:
            guai.append("N=%d: non ho contato" % n)
        elif quante != n:
            guai.append("N=%d: %s chiamate per ripasso" % (n, quante))
    if guai:
        return _no("⛔ il ripasso NON costa N chiamate: %s" % " · ".join(guai))
    return _si("il ripasso costa esattamente N chiamate a ogni N provato (%s) ⇒ il "
               "costo del ciclo e' N × D, cioe' LINEARE negli inquilini"
               % ", ".join("N=%d" % n for n in sorted(per_n)))


# ═══════════════════════════════════════════════════════════════════════════
# LE MISURE
# ═══════════════════════════════════════════════════════════════════════════
def sessioni_logind():
    """Quante sessioni logind ha la macchina ADESSO.  ⛔ `None` se non l'ho
       letto.  ⚠ E il pavimento non e' zero: su una macchina di prova condivisa
       ci sono decine di sessioni `manager` di altri agenti, e non si toccano."""
    rc, out, _ = b92.rem("loginctl list-sessions --no-legend | wc -l")
    t = out.strip()
    return int(t) if t.isdigit() else None


def cella(giro, quanti, ritardo_ms, durata_s, dillo=True):
    """⭐ UNA CELLA DELLA SUPERFICIE (D, N).  Torna un dizionario, e `None`
       dovunque non abbia misurato."""
    if dillo:
        _log("cella N=%d · D=%d ms · P=N×D=%d ms · %.0f s · giro «%s»"
             % (quanti, ritardo_ms, quanti * ritardo_ms, durata_s, giro))
    d = {"giro": giro, "quanti": quanti, "ritardo_ms": ritardo_ms,
         "prodotto_ms": quanti * ritardo_ms, "durata_s": None,
         "leva": False, "leva_perche": "", "fetta": None, "scatti": [],
         "offerti_nella_finestra": None, "vivi_prima": None, "vivi_dopo": None,
         "per_sessione": {}}
    r0 = registro_byte()
    t0 = orologio_ms()
    ok, perche = ritardo_poni(giro, ritardo_ms)
    d["leva"], d["leva_perche"] = ok, perche
    if dillo:
        (_ok if ok else _ko)(perche)
    partito = time.time()
    time.sleep(durata_s)
    d["durata_s"] = time.time() - partito
    t1 = orologio_ms()
    r1 = registro_byte()
    fetta = registro_fetta(r0, r1)
    d["fetta"] = fetta
    if fetta.get("esito") == "letto":
        mie = [g for g in fetta["guardiano"] if g["giro"] == giro]
        d["chiamate"] = len(mie)
        d["costi_us"] = [g["costo_us"] for g in mie]
        d["scatti"] = fetta["scatti"]
        # ⭐ IL MECCANISMO ACCANTO AL SINTOMO (`LEZIONI.md` §1.31 e §1.34): il
        #    sintomo e' lo scatto, il meccanismo e' che il palco PRODUCEVA e
        #    niente usciva.  I fotogrammi offerti dai palchi si leggono dalle
        #    righe `ciclo:` del figlio, che sono per palco e nella finestra.
        d["offerti_nella_finestra"] = fetta.get("consegnati_dal_palco")
        d["spediti_nella_finestra"] = fetta.get("fotogrammi_spediti")
    d["t0_ms"], d["t1_ms"] = t0, t1
    # ⭐ Chi e' ancora vivo e chi DISEGNA, in una domanda sola: uno scatto si
    #    vede anche da qui, ed e' il testimone indipendente dal registro; le
    #    scene sono la prova che il carico era addosso.
    vivi, scene_vive = [], 0
    try:
        v, sc, manca = b92.chi_c_e(quanti)
        vivi = [i for i in range(1, quanti + 1) if v.get(i)]
        # ⛔ Chi non ha risposto NON e' «ferma»: e' «non lo so».
        scene_vive = (None if manca
                      else sum(1 for i in range(1, quanti + 1) if sc.get(i)))
    except Exception as e:
        _dub("⚠ non ho potuto chiedere chi c'e': %s" % e)
        scene_vive = None
    d["vivi_dopo"] = vivi
    d["scene_vive"] = scene_vive
    if dillo:
        _inf("chiamate al guardiano col mio giro: %s · costo mediano %s ms"
             % (d.get("chiamate"),
                round(statistics.median(d["costi_us"]) / 1000.0, 1)
                if d.get("costi_us") else "?"))
        _inf("scene che disegnano: %s su %d · fotogrammi offerti dai palchi nella "
             "finestra: %s · spediti sul filo: %s"
             % (d.get("scene_vive"), quanti, d.get("offerti_nella_finestra"),
                d.get("spediti_nella_finestra")))
        if d["scatti"]:
            _ko("⛔ %d SCATTI di linea morta" % len(d["scatti"]))
            for s in d["scatti"][:8]:
                _inf("   %s causa=%s stallo_ms=%s offerti=%s usciti_byte=%s "
                     "coda_video=%s persi=%s permille=%s srtt_us=%s"
                     % (s.get("provenienza"), s.get("causa"), s.get("stallo_ms"),
                        s.get("offerti"), s.get("usciti_byte"), s.get("coda_video"),
                        s.get("persi"), s.get("permille"), s.get("srtt_us")))
        else:
            _ok("nessuno scatto")
        _inf("sessioni ancora vive: %s su %d" % (len(vivi), quanti))
    return d


def per_sessione(cella_, quanti, durata_s):
    """fot/s e ritardo di consegna per ogni sessione nella finestra della cella.

    ⚠ E' l'altra meta' del banco: ⭐ *«se non stacca nessuno ma toglie 300 ms di
      risposta a dieci utenti, e' comunque un difetto»* (`CODER.md` §1-bis).
    """
    fuori = {}
    if cella_.get("t0_ms") is None or cella_.get("t1_ms") is None:
        return {"esito": "⛔ NON HO LETTO L'OROLOGIO della macchina di prova"}
    for i in range(1, quanti + 1):
        try:
            fuori[i] = b92.fetta(i, cella_["t0_ms"], cella_["t1_ms"], durata_s)
        except Exception as e:
            fuori[i] = {"esito": "⛔ la fetta non si e' letta: %s" % e}
    return fuori


def stampa_sessioni(per):
    if not isinstance(per, dict) or "esito" in per:
        _dub("⛔ %s" % per.get("esito", "?"))
        return
    for i in sorted(per):
        n = per[i]
        if n.get("esito") != "misurato":
            _dub("s%d: %s" % (i, n.get("esito", "?")))
            continue
        r = n.get("ritardo", {})
        _inf("s%-2d %6.2f fot/s · %5d fotogrammi · ritardo mediano %8s ms · "
             "p95 %8s · massimo %8s"
             % (i, n.get("fps", 0), n.get("fotogrammi", 0),
                r.get("mediano_ms"), r.get("p95_ms"), r.get("massimo_ms")))


# ═══════════════════════════════════════════════════════════════════════════
def apri_fino_a(quanti, resta_s, gia=0):
    """Apre le sessioni da `gia+1` a `quanti`, ciascuna con la SUA scena.

    ⛔ E il guardiano va a RIPOSO prima: con la leva ancora tirata dalla cella
       precedente, una sessione nuova non entra proprio (vedi
       `guardiano_a_riposo`)."""
    guai = []
    if quanti > gia:
        guardiano_a_riposo("sto per aprire le sessioni %d-%d" % (gia + 1, quanti))
    for i in range(gia + 1, quanti + 1):
        t0 = time.time()
        ok, detto = b92.apri_sessione(i, resta_s)
        if not ok:
            guai.append("s%d non si e' aperta: %s" % (i, detto[:200]))
            _ko("s%d NON aperta" % i)
            continue
        _ok("s%d aperta in %.0f s — %s" % (i, time.time() - t0, detto[:110]))
        usc = accendi_scena(i)
        if usc:
            _ok("s%d: scena accesa su «%s»" % (i, usc))
        else:
            guai.append("s%d: la scena NON e' partita ⇒ il palco non produce, e "
                        "il meccanismo non puo' scattare" % i)
            _ko("s%d: scena NON partita" % i)
    return guai


def riapri_i_caduti(quanti, resta_s):
    """Dopo una cella che ha buttato fuori qualcuno, si rimette in piedi la
       scena: ⛔ la cella dopo dev'essere allo stesso N, o si confronterebbero
       due scene diverse."""
    caduti = [i for i in range(1, quanti + 1) if not b92.vivo(i)]
    if not caduti:
        return []
    _dub("⚠ riapro le sessioni cadute: %s" % ", ".join("s%d" % i for i in caduti))
    # ⛔ A leva tirata non rientrerebbero: la stretta di mano scade.
    guardiano_a_riposo("sto per riaprire %d sessioni cadute" % len(caduti))
    guai = []
    for i in caduti:
        ok, detto = b92.apri_sessione(i, resta_s)
        if not ok:
            guai.append("s%d non si e' riaperta: %s" % (i, detto[:160]))
            continue
        if not accendi_scena(i):
            guai.append("s%d: la scena non e' ripartita" % i)
    return guai


def sgombra(quanti=QUANTI_MAX, dillo=True):
    """⛔ Si lascia la macchina come la si e' trovata."""
    b92.root("printf 'sgombro -1\\n' > %s" % FILE_RITARDO)
    for i in range(1, quanti + 1):
        b92.root("pkill -u %d -f '04-b30-scena' ; true" % b92.uid(i))
    b92.root("pkill -f -- '--giornale [/]srv/remotix/tmp/10b6/' ; true")
    b92.root("pkill -f '10-b92-cliente[.]py --cliente' ; true")
    time.sleep(2)
    b92.chiudi_palchi(quanti, dillo=dillo)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL TERRENO — si chiama PRIMA di misurare, e fa fallire il banco
# ═══════════════════════════════════════════════════════════════════════════
def porte_altrui():
    """Le porte 7xxx/8xxx in ascolto che NON sono la mia.

    ⛔ Non le si tollera in silenzio e non le si spegne: si DICHIARANO, che e'
       quel che `PORTE_AMMESSE` vuole.  ⚠ In questa fase nove agenti lavorano
       insieme e l'elenco cambia di minuto in minuto: scriverlo a mano
       significherebbe o dare rosso su un vicino nuovo, o tacere su di lui.
    """
    rc, out, _ = b92.rem("ss -uln | grep -oE ':(7[0-9]{3}|8[0-9]{3}) ' "
                         "| tr -d ': ' | sort -u || true")
    fuori = [p for p in out.split() if p.isdigit() and int(p) != PORTA]
    return fuori


def terreno(lucchetto_mio, palco_ammesso=False):
    altrui = porte_altrui()
    if altrui:
        _inf("⚠ porte di ALTRI incarichi in ascolto, che dichiaro e non tocco: %s"
             % " ".join(altrui))
    amb = dict(os.environ)
    # ⛔⭐ `REPO` e' la COPIA DI RAFFRONTO, non il repository: questo albero si
    #     compila con un innesto dichiarato, e il confronto byte per byte va
    #     fatto contro quel che ho DAVVERO spedito.  ⚠ La differenza col
    #     repository e' un file solo, ed e' scritta nel passo `porta` del
    #     terreno con i due md5.
    staging = os.environ.get("STAGING", "/tmp/10-b97-repo")
    if not os.path.isdir(os.path.join(staging, "src")):
        _ko("⛔ manca la copia di raffronto «%s»: gira prima "
            "`bash banchi/10-b97-terreno.sh porta`" % staging)
        return 2
    amb.update({"CHI": IO_SONO, "PORTA": str(PORTA), "UTENTE": "provaf1",
                "ALBERO": ALB, "LAV": LAV, "REPO": staging,
                "LUCCHETTO_MIO": "1" if lucchetto_mio else "0",
                "PALCO_AMMESSO": "1" if palco_ammesso else "0",
                "PORTE_AMMESSE": " ".join(altrui)})
    p = subprocess.run(["bash", os.path.join(QUI, "10-b0-terreno.sh")], env=amb)
    return p.returncode


def spedisci_attrezzi():
    guai = []
    if not b92.spedisci(LETTORE, "10-b97-lettore.py"):
        guai.append("«10-b97-lettore.py» non si e' scritto in %s" % LAV)
    for sorg, nome in ((b92.CLIENTE, "10-b92-cliente.py"),
                       (b92.FETTA, "10-b92-fetta.py")):
        if not b92.spedisci(sorg, nome):
            guai.append("«%s» non si e' scritto in %s" % (nome, LAV))
    return guai


# ═══════════════════════════════════════════════════════════════════════════
# M1 · LA TARATURA DEL METRO
# ═══════════════════════════════════════════════════════════════════════════
def m1_taratura(esiti):
    _log("M1 · ⛔ IL METRO SI TARA PRIMA — si inietta %d ms e si guarda se torna"
         % TARA_MS)
    c = cella("tara-%d" % int(time.time()), 1, TARA_MS, 12.0, dillo=False)
    campioni = c.get("costi_us") or []
    passa, perche = giudica_taratura(campioni, TARA_MS)
    esiti["taratura"] = {"campioni": len(campioni),
                         "mediana_ms": round(statistics.median(campioni) / 1000.0, 2)
                         if campioni else None, "esito": perche}
    (_ok if passa else (_dub if passa is None else _ko))(perche)
    return passa


# ═══════════════════════════════════════════════════════════════════════════
# M2 · IL COSTO VERO DI `ListSessions`
# ═══════════════════════════════════════════════════════════════════════════
def m2_logind(esiti, quanti_extra, per_gradino_s):
    _log("M2 · ⭐ IL COSTO VERO DI `ListSessions` SU QUESTA MACCHINA")
    _inf("⛔ Il pavimento NON e' zero: questa macchina di prova e' condivisa e "
         "porta gia' decine di sessioni `manager` di altri incarichi.  Si "
         "MISURA quel che c'e' e si AGGIUNGONO sessioni, non si finge di "
         "partire da una.")
    righe, aperte = [], []
    try:
        for extra in range(0, quanti_extra + 1):
            if extra:
                # ⭐ Una sessione logind vera in piu': un accesso ssh ne crea una.
                p = subprocess.Popen(
                    ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30",
                     MACCHINA, "sleep 900"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                aperte.append(p)
                time.sleep(1.5)
            quante = sessioni_logind()
            giro = "logind%d-%d" % (extra, int(time.time()))
            c = cella(giro, 1, -1, per_gradino_s, dillo=False)
            costi = c.get("costi_us") or []
            if not costi:
                _dub("⛔ +%d sessioni: NON ho campioni — non giudico questo gradino"
                     % extra)
                righe.append({"extra": extra, "sessioni_logind": quante,
                              "campioni": 0, "mediana_us": None, "massimo_us": None})
                continue
            r = {"extra": extra, "sessioni_logind": quante,
                 "campioni": len(costi),
                 "mediana_us": int(statistics.median(costi)),
                 "massimo_us": max(costi), "minimo_us": min(costi)}
            righe.append(r)
            _inf("+%-2d sessioni ssh · %s sessioni logind in tutto · "
                 "ListSessions mediana %6.2f ms · massimo %6.2f ms (%d campioni)"
                 % (extra, quante, r["mediana_us"] / 1000.0,
                    r["massimo_us"] / 1000.0, r["campioni"]))
    finally:
        for p in aperte:
            p.terminate()
        for p in aperte:
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
    esiti["logind"] = righe
    buone = [r for r in righe if r.get("mediana_us")]
    if len(buone) < 2:
        _dub("⛔ NON GIUDICO la crescita di `ListSessions`: meno di due gradini letti")
        return None
    a, b = buone[0], buone[-1]
    dn = b["sessioni_logind"] - a["sessioni_logind"]
    pend = (b["mediana_us"] - a["mediana_us"]) / dn if dn else None
    esiti["logind_pendenza_us_per_sessione"] = round(pend, 1) if pend else None
    _inf("⭐ da %s a %s sessioni logind: la mediana passa da %.2f a %.2f ms "
         "(%s µs per sessione in piu')"
         % (a["sessioni_logind"], b["sessioni_logind"], a["mediana_us"] / 1000.0,
            b["mediana_us"] / 1000.0,
            round(pend, 1) if pend is not None else "?"))
    piu_alta = max(r["massimo_us"] for r in buone) / 1000.0
    _inf("⛔ IL NUMERO CHE CONTA: il PEGGIO misurato e' %.2f ms per chiamata.  "
         "La soglia dello stallo e' %d ms ⇒ servirebbero %.0f chiamate come "
         "quella in un ripasso per arrivarci."
         % (piu_alta, SOGLIA_STALLO_MS, SOGLIA_STALLO_MS / piu_alta))
    esiti["logind_peggio_ms"] = round(piu_alta, 3)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# M3 · LA SOGLIA — la superficie (D, N)
# ═══════════════════════════════════════════════════════════════════════════
def m3_soglia(esiti, enne, prodotti, durata_s, resta_s, rossi, muti,
              gia_aperte=0):
    _log("M3 · ⭐ LA SOGLIA — la superficie (D, N), percorsa a P = N×D costante")
    _inf("⛔ Il costo di un ripasso e' la SOMMA delle chiamate: N × D.  Percorrere "
         "la griglia a P costante e' quel che permette di dire se il confine e' "
         "dello STESSO posto per uno e per sette inquilini.")
    superficie, per_n_chiamate = [], {}
    # ⛔⛔ GLI ESITI PRENDONO LA LISTA **ADESSO**, non alla fine.
    #
    #     `[M]` 25 agosto 2026: un giro interrotto a meta' ha scritto il suo file
    #     degli esiti — il `finally` fa il suo mestiere — ⛔ ma la superficie era
    #     VUOTA, perche' `esiti["superficie"]` veniva assegnato solo quando
    #     questa funzione TORNAVA.  ⇒ Cinque celle gia' misurate, e il file
    #     diceva «nessuna cella».  Un file che esiste e non porta i numeri e'
    #     peggio di un file che manca: sembra un risultato.
    #
    # ⭐ La lista si passa per RIFERIMENTO e si riempie in luogo: da qui in poi
    #    ogni cella chiusa e' gia' negli esiti, e un'interruzione ne perde al
    #    massimo una.
    esiti["superficie"] = superficie
    esiti["chiamate_per_ripasso"] = per_n_chiamate
    aperte = gia_aperte
    for n in enne:
        _log("N = %d inquilini" % n)
        muti.extend("N=%d: %s" % (n, g) for g in riapri_i_caduti(aperte, resta_s))
        guai = apri_fino_a(n, resta_s, gia=aperte)
        if guai:
            for g in guai:
                muti.append("N=%d: %s" % (n, g))
            _dub("⚠ N=%d: il terreno delle sessioni non regge, salto questo N" % n)
            continue
        aperte = n
        time.sleep(6)   # assestamento
        # ── il braccio di controllo, SEMPRE per primo ────────────────────
        giro = "n%dP0-%d" % (n, int(time.time()))
        c0 = cella(giro, n, 0, durata_s)
        passa, perche = giudica_controllo(c0)
        (_ok if passa else (_dub if passa is None else _ko))(perche)
        if passa is False:
            rossi.append("N=%d controllo: %s" % (n, perche))
        elif passa is None:
            muti.append("N=%d controllo: %s" % (n, perche))
        c0["per_sessione"] = per_sessione(c0, n, durata_s)
        stampa_sessioni(c0["per_sessione"])
        superficie.append(c0)
        per_n_chiamate[n] = _chiamate_per_ripasso(c0)
        riapri_i_caduti(n, resta_s)
        # ── la salita in P ───────────────────────────────────────────────
        for p_ms in prodotti:
            d_ms = int(round(p_ms / float(n)))
            giro = "n%dP%d-%d" % (n, p_ms, int(time.time()))
            c = cella(giro, n, d_ms, durata_s)
            passa, perche = giudica_cella(c)
            if passa is None:
                _dub(perche)
                muti.append("N=%d D=%d: %s" % (n, d_ms, perche))
            mecc, perche_m = giudica_meccanismo(c)
            (_ok if mecc else (_dub if mecc is None else _ko))(perche_m)
            if mecc is False:
                rossi.append("N=%d D=%d: %s" % (n, d_ms, perche_m))
            c["giudizio"] = perche
            c["meccanismo"] = perche_m
            c["per_sessione"] = per_sessione(c, n, durata_s)
            stampa_sessioni(c["per_sessione"])
            superficie.append(c)
            if c["scatti"]:
                _ko("⛔⛔ IL CONFINE E' QUI: N=%d · D=%d ms · P=%d ms ⇒ %d "
                    "sessioni buttate fuori" % (n, d_ms, p_ms, len(c["scatti"])))
                riapri_i_caduti(n, resta_s)
                break
    passa, perche = giudica_crescita({k: v for k, v in per_n_chiamate.items()
                                      if v is not None})
    (_ok if passa else (_dub if passa is None else _ko))(perche)
    if passa is False:
        rossi.append(perche)
    elif passa is None:
        muti.append(perche)
    return superficie


def _chiamate_per_ripasso(c):
    """Quante chiamate al guardiano stanno in UN ripasso.  ⛔ `None` se non l'ho
       contato.  ⭐ E' la prova che il costo e' lineare negli inquilini: il
       ripasso gira ogni 2 s, e in `durata` secondi ci stanno `durata/2` ripassi."""
    n = c.get("chiamate")
    if not n or not c.get("durata_s"):
        return None
    ripassi = max(1, int(round(c["durata_s"] / 2.0)))
    return int(round(n / float(ripassi)))


# ═══════════════════════════════════════════════════════════════════════════
# M4 · LE DUE DURATE — ⚠ i giri corti sottostimano (`LEZIONI.md` §1.32)
# ═══════════════════════════════════════════════════════════════════════════
def m4_due_durate(esiti, n, p_ms, corta, lunga, resta_s, rossi, muti):
    _log("M4 · ⚠ LE DUE DURATE, sulla cella appena SOTTO il confine (N=%d, P=%d ms)"
         % (n, p_ms))
    _inf("⛔ Un fenomeno che «a volte succede» si prova a due durate: se la "
         "frazione segue l'esposizione, e' un fenomeno; se no, e' rumore "
         "(`LEZIONI.md` §1.32).")
    d_ms = int(round(p_ms / float(n)))
    fuori = []
    for durata in (corta, lunga):
        riapri_i_caduti(n, resta_s)
        time.sleep(5)
        giro = "dur%d-%d" % (int(durata), int(time.time()))
        c = cella(giro, n, d_ms, durata)
        passa, perche = giudica_cella(c)
        if passa is None:
            muti.append("due durate (%.0f s): %s" % (durata, perche))
        fuori.append({"durata_s": c["durata_s"], "scatti": len(c["scatti"]),
                      "vivi_dopo": len(c["vivi_dopo"] or []), "giudizio": perche})
    esiti["due_durate"] = fuori
    if len(fuori) == 2 and all(f["scatti"] is not None for f in fuori):
        a, b = fuori
        _inf("⭐ %.0f s ⇒ %d scatti · %.0f s ⇒ %d scatti (esposizione ×%.1f)"
             % (a["durata_s"], a["scatti"], b["durata_s"], b["scatti"],
                b["durata_s"] / max(1.0, a["durata_s"])))
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL RIASSUNTO — ⛔ e si stampano TUTTE le grandezze, non quella che serve
#    alla tesi (`LEZIONI.md` §6.2: una tabella con una colonna sola non e' una
#    misura corta, e' una misura ORIENTATA).
# ═══════════════════════════════════════════════════════════════════════════
def riassunto(esiti):
    _log("⭐ LA SUPERFICIE (D, N) — la tabella intera")
    print("   N   D(ms)  P=N×D  scene  chiam.  costo_med  offerti  SCATTI  "
          "vivi  fot/s medio  ritardo mediano  ritardo p95")
    print("  " + "-" * 108)
    for c in esiti.get("superficie", []):
        per = c.get("per_sessione") or {}
        buone = [n for n in per.values()
                 if isinstance(n, dict) and n.get("esito") == "misurato"]
        fps = round(statistics.mean(n["fps"] for n in buone), 2) if buone else None
        rit = [n["ritardo"]["mediano_ms"] for n in buone
               if n.get("ritardo", {}).get("mediano_ms") is not None]
        p95 = [n["ritardo"]["p95_ms"] for n in buone
               if n.get("ritardo", {}).get("p95_ms") is not None]
        costi = c.get("costi_us") or []
        print("  %2d  %6d  %6d  %2s/%-2d  %5s  %8s  %7s  %6d  %4s  %11s  %15s  %11s"
              % (c["quanti"], c["ritardo_ms"], c["prodotto_ms"],
                 c.get("scene_vive"), c["quanti"], c.get("chiamate"),
                 round(statistics.median(costi) / 1000.0, 1) if costi else "?",
                 c.get("offerti_nella_finestra"), len(c.get("scatti") or []),
                 len(c.get("vivi_dopo") or []),
                 fps if fps is not None else "?",
                 round(statistics.mean(rit), 1) if rit else "?",
                 round(statistics.mean(p95), 1) if p95 else "?"))
    _log("⭐ IL CONFINE")
    con = [c for c in esiti.get("superficie", []) if c.get("scatti")]
    if not con:
        _inf("⚠ nessuno scatto in tutta la griglia provata: il confine sta OLTRE "
             "P = %s ms" % max((c["prodotto_ms"] for c in
                                esiti.get("superficie", [])), default="?"))
        return
    for n in sorted({c["quanti"] for c in con}):
        primo = min((c for c in con if c["quanti"] == n),
                    key=lambda c: c["prodotto_ms"])
        cause = {}
        for s in primo["scatti"]:
            cause[s.get("causa")] = cause.get(s.get("causa"), 0) + 1
        _ko("N=%d ⇒ il primo utente viene staccato a D=%d ms (P=N×D=%d ms): "
            "%d scatti, cause %s, persi %s"
            % (n, primo["ritardo_ms"], primo["prodotto_ms"], len(primo["scatti"]),
               cause, {s.get("persi") for s in primo["scatti"]}))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL `--certifica` — UN BANCO NON E' FINITO FINCHE' NON LO SI E' VISTO
#     DARE ROSSO.  Qui i guasti si innestano sui GIUDIZI, che sono funzioni
#     pure: non si tocca la macchina, e ogni predicato ha il suo guasto.
# ═══════════════════════════════════════════════════════════════════════════
def _cella_finta(scatti=None, chiamate=8, giro="g1", durata=45.0, offerti=400,
                 leva=True, fetta_rotta=False, scene_vive=7):
    guard = [{"giro": giro, "ritardo_ms": 300, "finto": True, "chiamate": i + 1,
              "costo_us": 300000, "utente": "provaf1"} for i in range(chiamate)]
    fetta = {"esito": "letto", "guardiano": guard, "cambi": [], "righe": 100,
             "scatti": scatti or [], "consegnati_dal_palco": offerti,
             "fotogrammi_spediti": offerti}
    if fetta_rotta:
        fetta = {"esito": "⛔ NON HO LETTO — il lettore non ha risposto"}
    return {"giro": giro, "quanti": 7, "ritardo_ms": 300, "durata_s": durata,
            "leva": leva, "leva_perche": "" if leva else "la leva non ha preso",
            "fetta": fetta, "scatti": scatti or [],
            "offerti_nella_finestra": offerti if not fetta_rotta else None,
            "chiamate": chiamate, "costi_us": [300000] * chiamate,
            "scene_vive": scene_vive, "vivi_dopo": []}


def _scatto(causa="stallo", persi="0", offerti="52", usciti="0"):
    return {"provenienza": "[192.168.0.2]:48924", "causa": causa,
            "stallo_ms": "6004", "soglia_stallo_ms": "5000", "offerti": offerti,
            "usciti_byte": usciti, "coda_video": "13398", "persi": persi,
            "permille": "0", "srtt_us": "2470530"}


def certifica():
    _log("⛔⛔ `--certifica` — I GUASTI INNESTATI, E FATTI GIRARE")
    _inf("⭐ I giudizi sono funzioni PURE: il guasto si innesta sui dati, non "
         "sulla macchina, e ogni caso gira davvero — sano → guasto → risanato.")
    rossi = []
    conto = {"casi": 0, "rossi": 0}

    def caso(nome, atteso, visto, ok):
        conto["casi"] += 1
        if ok:
            _ok("%-46s atteso %-9s · visto %s" % (nome, atteso, visto))
        else:
            conto["rossi"] += 1
            rossi.append(nome)
            _ko("%-46s atteso %-9s · visto %s" % (nome, atteso, visto))

    def nome_esito(e):
        return {True: "VERDE", False: "ROSSO", None: "NON-GIUDICO"}[e]

    # ── G0 · IL SANO ────────────────────────────────────────────────────
    _log("G0 · il SANO — una cella che ha misurato, con uno scatto vero")
    sano = _cella_finta(scatti=[_scatto()])
    e, p = giudica_cella(sano)
    caso("sano: la cella ha misurato", "VERDE", nome_esito(e), e is True)
    e, p = giudica_meccanismo(sano)
    caso("sano: il meccanismo e' quello dedotto", "VERDE", nome_esito(e), e is True)
    e, p = giudica_controllo(_cella_finta(scatti=[]))
    caso("sano: il controllo a D=0 non scatta", "VERDE", nome_esito(e), e is True)
    e, p = giudica_taratura([150000] * 9, TARA_MS)
    caso("sano: il metro ritrova i 150 ms", "VERDE", nome_esito(e), e is True)
    e, p = giudica_crescita({1: 1, 3: 3, 5: 5, 7: 7})
    caso("sano: il ripasso costa N chiamate", "VERDE", nome_esito(e), e is True)

    # ── G1 · LA LEVA NON HA PRESO ───────────────────────────────────────
    _log("G1 · ⛔ IL GUARDIANO FINTO NON E' STATO INNESTATO — il caso che rende "
         "il banco inutile se passa in silenzio")
    e, p = giudica_cella(_cella_finta(scatti=[], leva=False))
    caso("leva non presa ⇒ NON HO MISURATO", "NON-GIUDICO", nome_esito(e), e is None)
    caso("  …e la ragione lo dice", "«non ho misurato»",
         "si" if "NON HO MISURATO" in p else "NO", "NON HO MISURATO" in p)

    # ── G2 · UN'ALTRA CAUSA CONTATA COME LINEA MORTA ────────────────────
    _log("G2 · ⛔ UNA SESSIONE STACCATA PER UN ALTRO MOTIVO — si legge la CAUSA")
    e, p = giudica_meccanismo(_cella_finta(scatti=[_scatto(causa="silenzio")]))
    caso("causa=silenzio ⇒ non e' il difetto dedotto", "ROSSO", nome_esito(e), e is False)
    e, p = giudica_meccanismo(_cella_finta(scatti=[_scatto(persi="37")]))
    caso("persi=37 ⇒ la linea non era pulita", "ROSSO", nome_esito(e), e is False)
    e, p = giudica_meccanismo(_cella_finta(scatti=[_scatto(usciti="8100")]))
    caso("usciti_byte>0 ⇒ lo stallo non e' totale", "ROSSO", nome_esito(e), e is False)

    # ── G3 · ZERO SCATTI PERCHE' NESSUNO PRODUCEVA ──────────────────────
    _log("G3 · ⛔ ZERO SCATTI PERCHE' I PALCHI NON PRODUCEVANO — il verde per "
         "costruzione, smascherato dai fotogrammi offerti")
    e, p = giudica_cella(_cella_finta(scatti=[], offerti=0))
    caso("offerti=0 e zero scatti ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)
    caso("  …e dice «PER COSTRUZIONE»", "si",
         "si" if "COSTRUZIONE" in p else "NO", "COSTRUZIONE" in p)
    e, p = giudica_meccanismo(_cella_finta(scatti=[_scatto(offerti="0")]))
    caso("uno scatto con offerti=0 non e' R10-A3", "ROSSO", nome_esito(e), e is False)
    # ⭐ E il guasto GEMELLO, quello che sulla macchina vera e' successo davvero:
    #    le scene spente.  `[M]` 24 ago 2026: a scena spenta il ciclo fermo 3 s
    #    per volta NON butta fuori nessuno; a scena accesa, sei secondi.
    e, p = giudica_cella(_cella_finta(scatti=[], scene_vive=3))
    caso("3 scene su 7 disegnano ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)
    e, p = giudica_cella(_cella_finta(scatti=[], scene_vive=None))
    caso("non so se disegnassero ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)
    e, p = giudica_cella(_cella_finta(scatti=[], scene_vive=7))
    caso("risanato: 7 scene su 7 ⇒ giudica", "VERDE", nome_esito(e), e is True)

    # ── G4 · IL CONTO DEL GIRO PRECEDENTE ───────────────────────────────
    _log("G4 · ⛔ IL CONTO DEGLI SCATTI LETTO DAL GIRO PRECEDENTE — l'ancora")
    vecchia = _cella_finta(scatti=[_scatto()], giro="g1")
    vecchia["fetta"]["guardiano"] = [
        {"giro": "IL-GIRO-DI-IERI", "ritardo_ms": 300, "finto": True,
         "chiamate": i, "costo_us": 300000, "utente": "provaf1"}
        for i in range(20)]
    e, p = giudica_cella(vecchia)
    caso("righe del giro di IERI ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)
    caso("  …e nomina il MIO giro", "si", "si" if "g1" in p else "NO", "g1" in p)

    # ── G5 · IL GIRO TROPPO CORTO ───────────────────────────────────────
    _log("G5 · ⛔ IL GIRO SANO TROPPO CORTO PERCHE' LA SOGLIA SIA RAGGIUNGIBILE")
    e, p = giudica_cella(_cella_finta(scatti=[], durata=4.0))
    caso("giro di 4 s (< %.0f) ⇒ NON GIUDICO" % GIRO_MINIMO_S,
         "NON-GIUDICO", nome_esito(e), e is None)
    e, p = giudica_cella(_cella_finta(scatti=[], durata=GIRO_MINIMO_S + 1))
    caso("risanato: giro di %.0f s ⇒ giudica" % (GIRO_MINIMO_S + 1),
         "VERDE", nome_esito(e), e is True)

    # ── G6 · IL GUARDIANO NON HA MORSO ──────────────────────────────────
    _log("G6 · ⛔ IL GUARDIANO NON E' STATO CHIAMATO ABBASTANZA — la "
         "sollecitazione si CONTA (`LEZIONI.md` §1.30)")
    e, p = giudica_cella(_cella_finta(scatti=[], chiamate=1))
    caso("1 chiamata sola ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)
    e, p = giudica_cella(_cella_finta(scatti=[], chiamate=CHIAMATE_MINIME))
    caso("risanato: %d chiamate ⇒ giudica" % CHIAMATE_MINIME,
         "VERDE", nome_esito(e), e is True)

    # ── G7 · IL BRACCIO DI CONTROLLO CHE SCATTA ─────────────────────────
    _log("G7 · ⛔ IL BRACCIO DI CONTROLLO CHE SCATTA — allora non si e' "
         "attribuito niente")
    e, p = giudica_controllo(_cella_finta(scatti=[_scatto()]))
    caso("controllo a D=0 con scatti ⇒ ROSSO", "ROSSO", nome_esito(e), e is False)
    e, p = giudica_controllo(_cella_finta(scatti=[], chiamate=0))
    caso("controllo senza chiamate ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)

    # ── G8 · IL METRO NON TARATO ────────────────────────────────────────
    _log("G8 · ⛔ IL METRO CHE NON RITROVA IL VALORE NOTO")
    e, p = giudica_taratura([12000] * 9, TARA_MS)
    caso("iniettati 150 ms, il metro ne dice 12 ⇒ ROSSO", "ROSSO", nome_esito(e), e is False)
    e, p = giudica_taratura([], TARA_MS)
    caso("nessun campione ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)

    # ── G9 · LA CRESCITA CHE NON C'E' ───────────────────────────────────
    _log("G9 · ⛔ IL RIPASSO CHE NON COSTA N CHIAMATE")
    e, p = giudica_crescita({1: 1, 7: 1})
    caso("N=7 ma una chiamata sola ⇒ ROSSO", "ROSSO", nome_esito(e), e is False)
    e, p = giudica_crescita({7: 7})
    caso("un solo N ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)

    # ── G10 · LA FETTA CHE NON SI E' LETTA ──────────────────────────────
    _log("G10 · ⛔ IL REGISTRO CHE NON SI E' LETTO — «non ho letto» ≠ «zero»")
    e, p = giudica_cella(_cella_finta(scatti=[], fetta_rotta=True))
    caso("fetta illeggibile ⇒ NON GIUDICO", "NON-GIUDICO", nome_esito(e), e is None)

    # ── G11 · IL LETTORE DEL REGISTRO, su righe VERE ────────────────────
    _log("G11 · ⭐ IL LETTORE DEL REGISTRO, provato su righe VERE del prodotto")
    prova = (
        "19:35:35.055 wt      linea-morta [192.168.0.2]:48924 causa=stallo "
        "stallo_ms=6004 soglia_stallo_ms=5000 offerti=52 usciti_byte=0 "
        "coda_video=13398 silenzio_ms=0 soglia_silenzio_ms=10000 prove=0 "
        "minimo_prove=2 persi=0 spediti=0 permille=0 finestra_ms=0 "
        "minimo_pacchetti=200 cwnd=13200 cwnd_left=13200 srtt_us=2470530 "
        "giudizio=⛔ la linea e' MORTA: da troppo tempo non esce un fotogramma\n"
        "19:32:36.634 sessione b97-guardiano giro=g1 ritardo_ms=300 finto=si "
        "chiamate=1 costo_us=300155 utente=provaf1 esito=0\n"
        "19:32:36.631 sessione b97-guardiano CAMBIO giro=g1 ritardo_ms=300\n"
        "19:35:35.055 figlio  ciclo: 67 fotogrammi consegnati (3 chiavi), 21176 "
        "attese a vuoto\n")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write(prova)
        dove = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(LETTORE)
        lett = f.name
    p2 = subprocess.run([sys.executable, lett, dove, "0", str(len(prova.encode()))],
                        capture_output=True)
    try:
        d = json.loads(p2.stdout.decode())
    except Exception as e:
        d = {}
    os.unlink(dove)
    os.unlink(lett)
    caso("legge lo scatto e la sua causa", "stallo",
         (d.get("scatti") or [{}])[0].get("causa"),
         (d.get("scatti") or [{}])[0].get("causa") == "stallo")
    caso("legge persi=0 dallo scatto", "0",
         (d.get("scatti") or [{}])[0].get("persi"),
         (d.get("scatti") or [{}])[0].get("persi") == "0")
    caso("legge il giro del guardiano", "g1",
         (d.get("guardiano") or [{}])[0].get("giro"),
         (d.get("guardiano") or [{}])[0].get("giro") == "g1")
    caso("legge il costo iniettato", "300155",
         (d.get("guardiano") or [{}])[0].get("costo_us"),
         (d.get("guardiano") or [{}])[0].get("costo_us") == 300155)
    caso("legge i fotogrammi offerti dal palco", "67",
         d.get("consegnati_dal_palco"), d.get("consegnati_dal_palco") == 67)
    caso("⛔ NON conta il CAMBIO come una chiamata", "1",
         len(d.get("guardiano") or []), len(d.get("guardiano") or []) == 1)

    _log("IL VERDETTO DEL `--certifica` — %d casi · %d rossi"
         % (conto["casi"], conto["rossi"]))
    if conto["rossi"]:
        for r in rossi:
            _ko(r)
        return 1
    _ok("⭐ %d casi su %d: ogni predicato ha il suo guasto, e il guasto e' stato "
        "FATTO GIRARE (sano → guasto → risanato)" % (conto["casi"], conto["casi"]))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL SEGNALE CHE AMMAZZA LA PULIZIA — e non e' un dettaglio di robustezza
# ═══════════════════════════════════════════════════════════════════════════
#
# `timeout`, `kill`, `pkill` e la chiusura di un terminale mandano **SIGTERM**,
# e SIGTERM ammazza Python **senza eseguire nessun `finally`**.  ⇒ Il lucchetto
# della GPU resterebbe preso fino alla scadenza, i palchi resterebbero montati e
# le scene a disegnare — e ⛔ **chi arriva dopo misurerebbe su un terreno che non
# e' quello che crede, senza un rosso per nessuno**.  E' la forma peggiore: non
# da' errore, da' un numero plausibile.
#
# ⇒ Si trasforma il segnale in un'ECCEZIONE, che i `finally` li esegue.
#   ⚠ E si arma un secondo colpo: se il segnale torna MENTRE si sta sgomberando,
#     alla terza volta si muore davvero invece di restare appesi in pulizia.
_SEGNALATO = {"quante": 0}


class Interrotto(SystemExit):
    """⛔ Un segnale, non un guasto: ma esce dalla porta che passa dai `finally`."""


def _prendi_i_segnali():
    def gestisci(numero, _quadro):
        _SEGNALATO["quante"] += 1
        nome = {signal.SIGTERM: "SIGTERM", signal.SIGINT: "SIGINT",
                signal.SIGHUP: "SIGHUP"}.get(numero, str(numero))
        if _SEGNALATO["quante"] >= 3:
            _ko("⛔ %s per la terza volta: esco SENZA sgomberare, e lo dico "
                "invece di tacerlo" % nome)
            os._exit(143)
        _ko("⚠ %s ricevuto: sgombero e mollo il lucchetto PRIMA di uscire "
            "(colpo %d di 3)" % (nome, _SEGNALATO["quante"]))
        raise Interrotto(143)
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(s, gestisci)
        except (ValueError, OSError):
            pass


ISTANZA = {"file": None}


def istanza_unica():
    """⛔⛔ UNA COPIA SOLA DI QUESTO BANCO PER VOLTA, e non e' pignoleria.

    `[M]` 25 agosto 2026, ed e' successo a me: un pilota riavviato ha lasciato
    vivo il **python figlio** del pilota precedente (il pid nel file era quello
    della SHELL, non del misuratore).  ⇒ Due copie dello stesso banco, tutt'e
    due di nome «10-b6», tutt'e due in corsa per lo stesso lucchetto, tutt'e due
    a scrivere nello stesso registro.  ⛔ La seconda non ha falsato la misura
    solo per fortuna: stava aspettando.  Se il turno le fosse arrivato avrebbe
    aperto sette palchi SOPRA quelli dell'altra.

    ⇒ Un `flock` su un file locale, tenuto per tutta la vita del processo.  Chi
      arriva secondo **esce dicendo chi c'e' gia'**, invece di mettersi in coda
      contro se stesso.
    """
    import fcntl
    dove = os.path.join(FUORI, "istanza.lock")
    os.makedirs(FUORI, exist_ok=True)
    f = open(dove, "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.seek(0)
        altro = f.read().strip() or "?"
        _ko("⛔ C'E' GIA' UNA COPIA DI QUESTO BANCO IN GIRO (pid %s, da «%s»)."
            % (altro, dove))
        _ko("   ⛔ NON parto: due copie si contendono lo stesso lucchetto col "
            "MEDESIMO nome, e nessuna delle due se ne accorge.")
        _inf("   Se quella copia e' morta male, il `flock` cade da se': "
             "controlla con  ps -p %s" % altro)
        return False
    f.seek(0)
    f.truncate()
    f.write("%d\n" % os.getpid())
    f.flush()
    ISTANZA["file"] = f          # ⛔ si tiene aperto: chiuderlo mollerebbe il flock
    return True


def principale():
    _prendi_i_segnali()
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", default="tutto",
                   choices=["taratura", "logind", "soglia", "tutto", "stato",
                            "sgombra"])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--durata", type=float, default=45.0,
                   help="la finestra di una cella, in secondi")
    p.add_argument("--enne", default="1,3,5,7",
                   help="i valori di N (inquilini) da percorrere")
    p.add_argument("--prodotti", default="500,1000,2000,3000",
                   help="i valori di P = N×D, in ms")
    p.add_argument("--logind-extra", type=int, default=12,
                   help="quante sessioni logind in piu' aprire per M2")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⚠ per la messa a punto: i numeri NON si riferiscono")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    # ⛔ Prima di qualunque cosa che tocchi la macchina: sono solo?
    if not istanza_unica():
        return 2

    apri_attrezzi()

    if a.passo == "stato":
        rc, out, _ = b92.root("systemctl is-active %s; ss -uln | grep -c ':%d ' "
                              "|| true" % (UNITA, PORTA))
        _inf("unita' %s: %s" % (UNITA, out.strip().replace("\n", " · ")))
        _inf("innesto nel registro: %s" % innesto_c_e())
        _inf("sessioni logind sulla macchina: %s" % sessioni_logind())
        for i in range(1, QUANTI_MAX + 1):
            _inf("s%d (%s): %s" % (i, b92.utente(i),
                                   "viva" if b92.vivo(i) else "spenta"))
        return 0

    if a.passo == "sgombra":
        sgombra()
        return 0

    enne = [int(x) for x in a.enne.split(",") if x.strip()]
    prodotti = [int(x) for x in a.prodotti.split(",") if x.strip()]
    quanti_max = max(enne) if enne else 1
    if quanti_max > QUANTI_MAX:
        _ko("⛔ ho sette utenti, non %d" % quanti_max)
        return 2

    # ── il metro della riduzione, PRIMA ─────────────────────────────────
    _log("IL METRO DELLA RIDUZIONE — importato da `09-b70-ritmo.py` e TARATO")
    b92.B70 = b92._importa_b70()
    sano, guai = b92.tara_riduzione(b92.B70, dillo=True)
    if not sano:
        for g in guai:
            _ko(g)
        _ko("⛔ NON MISURO: il metro dei fotogrammi non e' tarato")
        return 2

    # ── il posto si sgombra PRIMA, e poi si guarda ──────────────────────
    # ⛔ Un palco ORFANO non da' rosso: da' un numero plausibile
    #    (`LEZIONI.md` §1.26, e in fase 9 ha quasi fatto accusare tre cure
    #    innocenti).  ⇒ Prima si sgombra, poi il terreno GUARDA che sia sgombro.
    esiti = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "porta": PORTA,
             "albero": ALB, "passo": a.passo, "durata_cella_s": a.durata,
             "enne": enne, "prodotti_ms": prodotti}
    rossi, muti = [], []

    guai = spedisci_attrezzi()
    if guai:
        for g in guai:
            _ko(g)
        return 2

    # ── ⛔ IL LUCCHETTO PRIMA DEL TERRENO, e prima di toccare un utente ──
    #    Il preambolo della fase e' esplicito: la GPU e' UNA, e chi non ha il
    #    lucchetto non misura.  ⇒ Si prende PRIMA, cosi' il controllo del
    #    terreno puo' pretendere che sia MIO (`LUCCHETTO_MIO=1`) invece di
    #    accontentarsi che sia libero.
    # ⛔⛔ QUANTO DICHIARO DI TENERE IL LUCCHETTO — e si sbaglia PER ECCESSO.
    #
    #     `09-lucchetto.prendi()` SCASSINA un lucchetto scaduto, e lo fa bene:
    #     senza, un banco morto bloccherebbe tutti fino a domani.  ⛔ Ma vuol
    #     dire che un giro che dura PIU' di quanto ha dichiarato si trova la
    #     GPU portata via mentre sta misurando — e chi gliel'ha portata via
    #     misura su sette palchi accesi credendo la macchina sgombra.
    #     ⚠ Nessuno dei due vede un rosso: tutt'e due leggono numeri plausibili.
    #
    # ⇒ La stima somma i pezzi veri del giro e poi si moltiplica per un MARGINE
    #   dichiarato.  Sbagliare per eccesso costa qualche minuto di attesa a chi
    #   viene dopo; sbagliare per difetto costa la misura a tutt'e due.
    MARGINE = 1.6
    stima = (180                                             # taratura e spedizioni
             + (a.logind_extra + 1) * (max(12.0, a.durata / 3.0) + 22)   # M2
             + (len(prodotti) + 1) * len(enne) * (a.durata + 32)         # M3, le celle
             + 240 * quanti_max                              # l'apertura dei palchi
             + 4 * (a.durata + 32)                           # M4 e le riaperture
             + 120)                                          # lo sgombero finale
    quanto = int(stima * MARGINE)
    _inf("⭐ il giro si stima in %d s; dichiaro di tenere il lucchetto %d s "
         "(margine ×%.1f, e si sbaglia per ECCESSO: un lucchetto scaduto viene "
         "SCASSINATO, e allora due banchi misurano insieme senza saperlo)"
         % (stima, quanto, MARGINE))
    # ⛔⛔ E L'ATTESA DEL TURNO STA DENTRO IL `try`, NON PRIMA.
    #     Il turno puo' arrivare dopo un'ora, e in quell'ora un `timeout` o un
    #     `pkill` possono trovarmi: se il segnale arrivasse fuori dal `try`, il
    #     lucchetto appena preso resterebbe preso.
    preso = False
    resta_s = quanto
    try:
        if not a.senza_lucchetto:
            try:
                # ⛔⛔ SEI ORE DI ATTESA, E LA RAGIONE STA QUI PERCHE' NESSUNO LA
                #     RIABBASSI CREDENDO CHE SIA PRUDENZA SPRECATA.
                #
                #     `09-lucchetto.prendi()` **non e' una coda: e' una CORSA.**
                #     Il `mkdir` si ritenta ogni 5 s e vince chi arriva per primo
                #     dopo un `molla` — nessuna prenotazione, nessuna anzianita'.
                #     `[M]` 24 agosto 2026: un incarico in attesa dalle 19:53 ha
                #     perso **due passaggi di mano consecutivi** senza mai
                #     toccare la GPU.
                #
                #     ⇒ Siamo in cinque sulla stessa scheda e un giro dura ~90
                #       minuti: un'attesa di 90 minuti **scade dentro il turno di
                #       un altro**, e il giro viene SALTATO.  Sei ore sono
                #       cinque turni pieni piu' il margine della corsa.
                #
                # ⛔ E se il turno non arriva NEMMENO COSI', l'uscita e' **4** e
                #    non 2: «il turno non e' mai arrivato» e «il terreno non
                #    regge» sono due fatti diversi, e confonderli e' la forma
                #    «silenzio invece di rosso» — un giro mai fatto che somiglia
                #    a un giro fallito.  Su 4 il pilota RIMETTE IN CODA; su 2 no.
                luc.prendi(IO_SONO, secondi=quanto, attesa=21600)
                preso = True
            except Interrotto:
                raise
            except Exception as e:
                _ko("⛔ IL TURNO NON E' MAI ARRIVATO: %s" % e)
                _dub("⛔ NON HO MISURATO — e non e' «il terreno non regge»: la "
                     "domanda non e' mai stata posta.  Uscita 4: chi mi ha "
                     "lanciato mi rimetta in coda.")
                return 4
        else:
            _dub("⚠ SENZA LUCCHETTO: questi numeri NON si riferiscono (messa a punto)")

        _log("SGOMBERO DI PARTENZA — chi arriva dopo deve trovare pulito, e io pure")
        sgombra(QUANTI_MAX, dillo=True)

        # ── il terreno ──────────────────────────────────────────────────
        _log("⛔ IL TERRENO DELLA FASE 10 — si guarda PRIMA di misurare")
        rc = terreno(lucchetto_mio=preso)
        if rc != 0:
            _ko("⛔ il terreno non ha dato verde (uscita %d): NON misuro" % rc)
            return 2

        # ⛔⛔ LA PRIMA SESSIONE PRIMA DI TUTTO, E NON E' UN DETTAGLIO DI ORDINE.
        #
        #     Il gancio del guardiano lo chiama `wt_sorveglia_locali()`, che
        #     cicla sulle sessioni ATTACCATE: con zero sessioni il guardiano non
        #     viene chiamato **mai**, il file del ritardo non viene nemmeno
        #     riletto, e ogni misura darebbe zero campioni.  ⇒ Senza questa
        #     sessione il banco misurerebbe il proprio silenzio.
        _log("LA PRIMA SESSIONE — senza, il guardiano non viene chiamato mai")
        guai = apri_fino_a(1, resta_s, gia=0)
        if guai:
            for g in guai:
                _ko(g)
            _ko("⛔ NON MISURO: la prima sessione non sta in piedi")
            return 2
        time.sleep(5)

        if a.passo in ("taratura", "tutto", "soglia"):
            if not m1_taratura(esiti):
                _ko("⛔ NON PROSEGUO: senza il metro tarato i numeri non sono misure")
                return 1
        if a.passo == "taratura":
            return 0
        if a.passo in ("logind", "tutto"):
            m2_logind(esiti, a.logind_extra, max(12.0, a.durata / 3.0))
        if a.passo == "logind":
            return 0
        if a.passo in ("soglia", "tutto"):
            sup = m3_soglia(esiti, enne, prodotti, a.durata, resta_s, rossi,
                            muti, gia_aperte=1)
            # ── la cella appena SOTTO il confine, a due durate ───────────
            confine = [c for c in sup if c["scatti"]]
            if confine:
                primo = min(confine, key=lambda c: (c["quanti"], c["prodotto_ms"]))
                sotto = [c for c in sup
                         if c["quanti"] == primo["quanti"]
                         and 0 < c["prodotto_ms"] < primo["prodotto_ms"]]
                if sotto:
                    p_sotto = max(c["prodotto_ms"] for c in sotto)
                    m4_due_durate(esiti, primo["quanti"], p_sotto, a.durata,
                                  a.durata * 3, resta_s, rossi, muti)
                else:
                    muti.append("⚠ NON ho una cella SOTTO il confine per le due "
                                "durate: il confine e' al primo P provato")
            else:
                # ⛔ E SE IL CONFINE NON C'E', LO SI DICE.  `[M]` 25 ago 2026: la
                #    griglia intera (20 celle, N=1..7, P fino a 5001 ms) non ha
                #    prodotto NEMMENO UNO scatto ⇒ M4 non e' stato eseguito.
                #    ⚠ Un passo che non gira e non lascia una riga e' un buco che
                #      somiglia a un passo riuscito: la prova delle DUE DURATE
                #      (`LEZIONI.md` §1.32) qui NON e' stata fatta, e il banco
                #      deve dirlo invece di tacere.
                muti.append("⚠ M4 NON ESEGUITO: nessuno scatto in tutta la "
                            "griglia (P fino a %d ms, N fino a %d) ⇒ non c'e' "
                            "nessuna cella «appena sotto il confine» su cui "
                            "provare le due durate.  ⛔ La prova di §1.32 su "
                            "questo fenomeno resta APERTA."
                            % (max((c["prodotto_ms"] for c in sup), default=0),
                               max((c["quanti"] for c in sup), default=0)))
    finally:
        # ⛔⛔ QUESTO BLOCCO GIRA ANCHE SU SIGTERM — e' per quello che i segnali
        #     diventano un'eccezione: senza, il lucchetto resterebbe preso fino
        #     alla scadenza e sette palchi resterebbero montati a disegnare.
        #     ⚠ E ogni passo e' protetto da se': se lo sgombero alza, il
        #     lucchetto va mollato lo stesso — chi arriva dopo aspetta un
        #     lucchetto, non un'eccezione mia.
        _log("SGOMBERO — la macchina si lascia come la si e' trovata")
        try:
            os.makedirs(FUORI, exist_ok=True)
            with open(os.path.join(FUORI, "10-b97-esiti.json"), "w") as f:
                json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
            _inf("esiti in %s/10-b97-esiti.json (scritti PRIMA dello sgombero: "
                 "un giro interrotto lascia comunque i suoi numeri)" % FUORI)
        except Exception as e:
            _dub("⚠ gli esiti non si sono scritti: %s" % e)
        try:
            sgombra(quanti_max)
        except Exception as e:
            _dub("⚠ lo sgombero non e' riuscito del tutto: %s" % e)
        try:
            rc, out, _ = b92.rem("ss -uln | grep -c ':%d ' || true" % PORTA)
            _inf("ascoltatori sulla mia porta %d: %s" % (PORTA, out.strip()))
        except Exception as e:
            _dub("⚠ non ho riletto la mia porta: %s" % e)
        # ⛔⛔ SI MOLLA **SOLO** QUEL CHE SI E' PRESO — e questa riga e' costata.
        #
        #     La stesura di prima mollava anche quando `preso` era falso, se il
        #     nome sul lucchetto era il mio: sembrava prudenza contro la finestra
        #     fra il `mkdir` e la scrittura di `chi`.  ⛔ `[M]` 25 agosto 2026: due
        #     copie DELLO STESSO banco si chiamano tutt'e due «10-b6», e quella
        #     che stava solo aspettando avrebbe MOLLATO IL LUCCHETTO DELL'ALTRA e
        #     ne avrebbe sgomberato i sette palchi — a meta' misura, e senza che
        #     nessuno dei due vedesse un rosso.
        #
        # ⇒ Il nome sul lucchetto NON dimostra la proprieta'.  Solo `preso` lo fa.
        #   ⚠ E la finestra `mkdir`-senza-`chi` non si cura qui: `10-b0-terreno.sh`
        #     ha gia' il ramo «illeggibile» apposta, e dice la cosa giusta —
        #     *«non e' libero, ed e' il caso in cui NON si tira a indovinare»*.
        try:
            if preso:
                luc.molla(IO_SONO)
            else:
                chi, _scad = luc.stato()
                _inf("non avevo il lucchetto: non lo tocco (adesso e' di «%s»)"
                     % (chi if chi else "nessuno"))
        except Exception as e:
            _dub("⚠ NON ho potuto mollare il lucchetto (%s) — ⛔ guardalo a mano: "
                 "`LUCCHETTO=%s python3 banchi/09-lucchetto.py stato`"
                 % (e, os.environ.get("LUCCHETTO")))

    if esiti.get("superficie"):
        riassunto(esiti)

    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi[:40]:
        _ko(r)
    for m in muti[:40]:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
