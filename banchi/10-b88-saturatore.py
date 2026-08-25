#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b88-saturatore — ⭐ DOVE CEDE IL CODIFICATORE DEL PRODOTTO, E **PERCHE'** CEDE.

===========================================================================
⛔ CHE COSA MISURA, E CHE COSA NON MISURA

`SPECIFICHE.md` §5.5 e `DECISIONI.md` §4.6 dichiarano una tabella di pixel al
secondo **ricavata dalla generazione del chip, non misurata** — un `[?]` grosso
come il budget del prodotto.  `vainfo` dice *quali* profili ci sono, non
**quanti pixel al secondo**.  Questo banco trasforma quel `[?]` in `[M]`.

⛔ **Misura il codificatore DEL PRODOTTO** (`src/codificatore.c`), non `ffmpeg`:
   il carico lo porta `banchi/10-b88-flusso`, un guscio sottile che chiama le
   stesse funzioni di `figlio.c` (`CODER.md` §3.6).  ⚠ Un `ffmpeg` compare qui
   **solo** nel comando `controllo`, ed e' dichiarato per quel che e': un
   **secondo metro**, non il metro.

⛔⛔ **IL CODEC NON E' UNO SOLO, E IL PREDEFINITO DI QUESTO BANCO NON E' QUELLO
    CHE IL PRODOTTO SCEGLIE PIU' SPESSO.**  `[M]` 24 agosto 2026, letto nel
    codice: `src/rcp.c:1829` offre `NOSTRO_CODEC "hevc,h264"` e §4.3 sceglie
    **nell'ordine del CLIENT**; `src/pagina.html:831` dichiara
    `PREFERENZA = ["hevc","h264"]` ⇒ ⭐ **su un browser che decodifica HEVC il
    prodotto manda HEVC**, e H.264 e' il ripiego (Firefox per Android non ha
    HEVC: `DECISIONI.md` §1.13-ter).  ⇒ **Servono tutt'e due le colonne.**

⛔⛔ **E LE COLONNE NON SI MEDIANO MAI.**  La fase 9 §13.5 ha pagato l'errore
    opposto — *«tutti i numeri di banda erano HEVC, e il prodotto manda
    H.264»*: `[M]` stessa scena, **21,18 contro 7,92 Mbit/s**, e mezza giornata
    di numeri buttati.  ⚠ E il rapporto fra i due **non e' una costante**
    (0,36× sul retinato, 0,76× sulla grana, **1,7× in su** sul desktop vero):
    non e' correggibile a posteriori con un fattore.
    ⭐ L'ANCORA che lo rende impossibile e' `ancora_del_flusso()`: il codec, la
    profondita' e il modo del bitrate si leggono **dal flusso prodotto** (la
    stringa composta sull'SPS) e dal contesto riletto — **non dal comando dato**.

⛔ E la PROFONDITA' e' la stessa storia in piccolo: `rcp.c` offre `8,10`, la
   pagina dichiara `8,10` ⇒ il negoziato da' **8**, cioe' HEVC **Main**.  Main10
   (`--profondita 10`) e' una colonna sua, e nemmeno lei si media.

===========================================================================
⛔⛔ LE DUE STRADE SONO DUE MISURE DIVERSE, E NON SI SOMMANO

  `scheda`   il fotogramma sta **gia' sulla GPU** (`codificatore_comprimi_
             scheda`, la copia zero della fase 8).  Per fotogramma la CPU non
             copia niente ⇒ ⭐ e' la misura **del motore di codifica**, ed e'
             anche la strada vera del prodotto quando la cattura consegna un
             DMA-BUF.
  `memoria`  i pixel passano per la memoria di sistema: `sws_scale` in CPU +
             caricamento + codifica.  ⇒ e' la **catena di ripiego**, quella che
             si percorre quando il passo non e' importabile.

===========================================================================
⛔ IL METRO DELLA GPU, E LA SUA TARATURA (regola 6, `LEZIONI.md` §1.33)

⛔ IL METRO NON E' MIO: e' `banchi/10-b87-metro-gpu.py` dell'agente **A1**,
   tarato (`--certifica` 43/43, `--tara`, `--tara-clock`).  `10-b88-sonda.py` lo
   importa invece di rileggersi i `fdinfo` per conto suo — un metro scritto qui
   non sarebbe tarato, e `LEZIONI.md` §1.33 dice che allora produce numeri e non
   misure.

⛔ E porta con se' due avvertimenti che cambiano la lettura di OGNI riga:

  1. **I VDBOX sono DUE** (`drm-engine-capacity-video: 2`) ⇒ il massimo e'
     **200 %** in motori-equivalenti, cioe' **100 %** di capacita'.  Il banco
     stampa tutt'e due i numeri col nome accanto: confonderli sbaglia il budget
     di un fattore due.
  2. ⛔⛔ **`drm-engine-video` conta TEMPO OCCUPATO, non LAVORO FATTO**: `[M]`
     A1, stessa codifica 1080p30, **26,41 %** a 300 MHz contro **7,01 %** a
     1550 MHz — fattore **3,77** a lavoro identico.  ⇒ **La capienza non si
     estrapola** da un carico leggero: si misura **a saturazione**, ed e'
     esattamente quel che fa la rampa.  `10-b88-saturatore.py tara` lo dimostra
     sui numeri di QUESTO banco invece di fidarsi.

===========================================================================
⛔ `None` NON E' ZERO

Un flusso che non parte non e' «un flusso a 0 fps»; un'occupazione che non si e'
potuta leggere non e' «0 %».  Ogni casella che non si e' potuta misurare esce
`null` e il banco **si rifiuta di giudicarla**.

===========================================================================
⛔ I GIRI CORTI SOTTOSTIMANO (`LEZIONI.md` §1.32)

Ogni casella si fa a **due durate** (15 s e 60 s).  Se il risultato cambia, il
numero che vale e' quello **lungo**, e la differenza si scrive.

===========================================================================
Uso (dal portatile):

    python3 banchi/10-b88-saturatore.py porta        # spedisce e compila
    python3 banchi/10-b88-saturatore.py scene        # genera le scene
    python3 banchi/10-b88-saturatore.py tara         # ⛔ prima di crederci
    python3 banchi/10-b88-saturatore.py rampa        # la rampa, tre taglie
    python3 banchi/10-b88-saturatore.py bitrate      # ⭐ QVBR: il modo del tetto
    python3 banchi/10-b88-saturatore.py controllo    # il secondo metro (ffmpeg)
    python3 banchi/10-b88-saturatore.py certifica    # ⛔ i guasti innestati

⭐ E la rampa si fa in TRE colonne che non si mediano mai:

    … rampa                                   # H.264 High 8 bit, CQP
    … rampa --codec hevc                      # HEVC **Main** (8 bit) — ⭐ ed e'
                                              #   quel che il prodotto NEGOZIA
    … rampa --codec hevc --profondita 10      # HEVC **Main10**
    … bitrate --tetto-banda-mbit 20           # ⇒ QVBR invece di CQP

⛔⛔ OGNI GIRO DA CUI ESCE UN NUMERO PRENDE IL LUCCHETTO DELLA GPU (`$CHI_BANCO`): la
    GPU e' una, e due carichi insieme si falsano **in silenzio**.
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
ALBERO = os.environ.get("ALBERO", "/media/REMOTIX/src/10a2-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10a2")
DENTRO = os.environ.get("DENTRO_ALB", "/srv/src/10a2-src")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
# ⛔ CHI SONO, e serve a due cose che non si possono confondere: il nome sul
#    lucchetto della GPU e il `CHI=` del controllo del terreno.  ⚠ Predefinito
#    `10-a2` perche' e' l'agente che ha scritto questo banco; chi lo riusa passa
#    il proprio nome, o due agenti si scambierebbero il lucchetto credendolo
#    proprio.
CHI = os.environ.get("CHI_BANCO", "10-a2")
BIN = ALBERO + "/banchi/10-b88-flusso"
SONDA = ALBERO + "/banchi/10-b88-sonda.py"
NUCLEI = 20  # i5-13500T: 6P+8E, 20 fili — si dichiara, non si indovina
JIFFY = 100  # USER_HZ

# ⚠ La tolleranza sul ritmo, scritta UNA volta e citata in ogni verdetto: un
#   banco che decide la soglia caso per caso non ha una soglia.
TOLLERANZA = 0.95

VERDE, ROSSO, GIALLO, GRASSO, FINE = (
    "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[1m", "\033[0m")


def ok(s):  print("    %sOK%s  %s" % (VERDE, FINE, s))
def ko(s):  print("    %sNO%s  %s" % (ROSSO, FINE, s))
def att(s): print("    %s??%s  %s" % (GIALLO, FINE, s))
def inf(s): print("    --  %s" % s)
def tit(s): print("\n%s== %s%s" % (GRASSO, s, FINE))


# ───────────────────────────────────────────────────────────────────────────
# Il lucchetto della GPU.  ⛔ Si prende per il tempo del giro e si molla subito:
#    gli altri nove agenti aspettano.
def _carica_lucchetto():
    os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
    spec = importlib.util.spec_from_file_location(
        "luc", os.path.join(QUI, "09-lucchetto.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LUC = None
DENTRO_LUCCHETTO = 0


class Lucchetto:
    """⛔ `with Lucchetto():` attorno a ogni BLOCCO che produce numeri.

    ⚠ E' RIENTRANTE apposta: il blocco lo prende una volta sola e i giri dentro
      non lo ripigliano.  ⛔ La ragione e' misurata sul campo il 24 agosto 2026:
      con dieci agenti in coda, prendere e mollare a ogni singolo giro vuol dire
      aspettare il proprio turno **fra un giro e l'altro dello stesso confronto**
      — e una rampa i cui gradini sono presi a mezz'ora di distanza, con la
      macchina in tre stati diversi, non e' una rampa.  ⇒ Il lucchetto si prende
      per **una casella intera** (una taglia a una durata) e si molla subito
      dopo: e' il piu' piccolo blocco che abbia senso come misura."""

    # ⛔⛔ «IL LUCCHETTO L'HO GIA' PRESO IO, DI FUORI».
    #
    #     `09-lucchetto.prendi()` NON e' rientrante: il possesso e' un `mkdir`
    #     atomico, e se la cartella c'e' gia' fallisce **anche se e' mia**.  ⇒ Un
    #     lanciatore che prende il lucchetto e poi chiama questo banco lo farebbe
    #     aspettare **se stesso**, per sempre.
    #
    # ⭐ Perche' un lanciatore lo faccia: la coda sul lucchetto e' lunga (`[M]` 24
    #    agosto 2026, oltre 40 minuti con dieci agenti), e rimettersi in fondo
    #    alla fila fra la rampa e lo studio del bitrate vuol dire misurare **due
    #    macchine diverse** e chiamarle una.
    #
    # ⛔ E' UNA PROMESSA DI CHI CHIAMA, e il banco non la puo' verificare: se
    #    fosse falsa, i numeri sarebbero presi con un altro carico sulla stessa
    #    GPU e **non lo griderebbe nessuno** (`LEZIONI.md` §1.26).  ⇒ Chi la fa
    #    la dichiara, e il banco la SCRIVE accanto ai numeri invece di tacerla.
    #    ⚠ Il controllo del terreno resta a fare da giudice: `LUCCHETTO_MIO=1` gli
    #    fa verificare che il possessore sia davvero `CHI`, e li' la bugia si
    #    vede.
    FUORI = os.environ.get("LUCCHETTO_GIA_MIO") == "1"

    def __init__(self, secondi=1200):
        self.secondi, self.mio = secondi, False

    def __enter__(self):
        global LUC, DENTRO_LUCCHETTO
        if Lucchetto.FUORI:
            if DENTRO_LUCCHETTO == 0:
                print("   ⚠   LUCCHETTO_GIA_MIO=1: il lucchetto l'ha preso il "
                      "LANCIATORE, non questo banco — e il terreno lo verifica",
                      flush=True)
            DENTRO_LUCCHETTO += 1
            return self
        if DENTRO_LUCCHETTO == 0:
            if LUC is None:
                LUC = _carica_lucchetto()
            self.aspetta()
            self.mio = True
        DENTRO_LUCCHETTO += 1
        return self

    def aspetta(self, tetto=7200.0, passo=1.0):
        """⛔ SI ASPETTA DENTRO IL PROCESSO, e si ritenta piu' fitto di 5 s.

        ⚠ E LO DICHIARO, perche' e' una scelta che tocca gli altri: `prendi()`
          ritenta ogni **5 s**, e `[M]` 24 agosto 2026 con dieci agenti in fila su
          quel passo questo banco ha perso la corsa **quattro volte di seguito** —
          ogni volta che il lucchetto si liberava, lo prendeva un altro dentro la
          finestra dei 5 s.  ⇒ Qui si ritenta ogni **secondo**.  ⛔ Non e' un
          modo di scavalcare la coda: e' lo stesso `mkdir` atomico, tentato piu'
          spesso; chi arriva prima vince lo stesso.
        ⭐ E il prezzo si paga subito: il lucchetto si molla in `finally`, appena
          finita la sessione di misura."""
        fine = time.time() + tetto
        detto = 0.0
        while True:
            try:
                LUC.prendi(CHI, secondi=self.secondi, attesa=0, dillo=False)
                print("   OK  lucchetto della GPU preso da «%s» per %d s"
                      % (CHI, self.secondi), flush=True)
                return
            except LUC.NonMio:
                pass
            if time.time() >= fine:
                raise RuntimeError(
                    "⛔ ho aspettato il lucchetto della GPU %d minuti e non e' mai "
                    "toccato a me: NON misuro, e lo dichiaro" % int(tetto / 60))
            if time.time() - detto > 60:
                detto = time.time()
                chi, scad = LUC.stato()
                print("   --  aspetto il mio turno (e' di «%s», ancora %d s)"
                      % (chi, int((scad or 0) - time.time())), flush=True)
            time.sleep(passo)

    def __exit__(self, *a):
        global DENTRO_LUCCHETTO
        DENTRO_LUCCHETTO -= 1
        # ⛔ Chi non l'ha preso non lo molla: mollare il lucchetto di un altro
        #    (fosse pure il proprio lanciatore) e' la stessa ferita al contrario.
        if self.mio and DENTRO_LUCCHETTO == 0:
            LUC.molla(CHI)
        return False


# ───────────────────────────────────────────────────────────────────────────
def remoto(comando, tetto=600):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def orologio_remoto_ns():
    rc, out, _ = remoto("date +%s%N")
    return int(out.strip()) if rc == 0 else None


# ═══════════════════════════════════════════════════════════════════════════
# 1 · PORTA — i sorgenti e la compilazione
# ═══════════════════════════════════════════════════════════════════════════
def porta():
    tit("1 · I sorgenti del PRODOTTO in %s" % ALBERO)
    radice = os.path.dirname(QUI)
    for f in ("src/codificatore.c", "src/registro.c"):
        h = subprocess.run(["md5sum", os.path.join(radice, f)],
                           capture_output=True).stdout.decode().split()[0]
        inf("md5 locale %-18s %s" % (f + ":", h))
    # ⛔⭐ SI SPEDISCE L'ALBERO INTERO, non i quattro file che mi servono.
    #
    # ⚠ Il banco compila da se' **solo** `codificatore.c` e `registro.c`
    #   (`10-b88-costruisci.sh`): il server non gli serve per misurare.  Ma
    #   `10-b0-terreno.sh` T5.2/T5.3 chiede un'altra cosa, e la chiede giusto —
    #   *«il codice che gira e' quello che sto leggendo?»*: un albero monco non
    #   permette di dirlo, e un binario che MANCA e' un guaio, non un ignoto.
    # ⛔ E `banchi/rcp` ci va per forza: `src/costruisci.sh` confronta la copia
    #   gemella di `rcp.c` (R12.3) e senza quella cartella si rifiuta.
    for f in ("rcp.c", "rcp.h", "autenticazione.c"):
        if subprocess.run(["cmp", "-s", os.path.join(radice, "src", f),
                           os.path.join(radice, "banchi/rcp", f)]).returncode != 0:
            ko("⛔ src/%s e banchi/rcp/%s DIVERGONO: la costruzione fallirebbe "
               "(R12.3)" % (f, f))
            return 2
    ok("le due copie di rcp.c/rcp.h/autenticazione.c sono allineate")
    p = subprocess.run(
        ["bash", "-c",
         "tar -C %s --exclude='src/remotix' --exclude='src/*.o' -cf - src "
         "banchi/rcp banchi/10-b88-flusso.c banchi/10-b88-costruisci.sh "
         "banchi/10-b88-sonda.py banchi/10-b87-metro-gpu.py | gzip | "
         "ssh -o BatchMode=yes %s 'mkdir -p %s %s && tar -C %s -xzf -'"
         % (radice, MACCHINA, ALBERO, LAV, ALBERO)],
        capture_output=True)
    if p.returncode != 0:
        ko("⛔ i sorgenti non sono arrivati: %s" % p.stderr.decode()[:300])
        return 2
    ok("sorgenti (albero intero) in %s" % ALBERO)

    tit("2 · Compilo DENTRO il contenitore (il rootfs vive in RAM)")
    inf("prima il guscio del banco, poi il server intero (per T5.3 del terreno)")
    rc, out, err = remoto(
        "printf '%%s\\n' '%s' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root "
        "'LAV_COSTRUZIONE=%s/lav bash %s/banchi/10-b88-costruisci.sh 2>&1 | tail -30'"
        % (PAROLA_SUDO, DENTRO, DENTRO), tetto=900)
    print(out)
    if rc != 0:
        ko("⛔ la compilazione del guscio e' fallita: NON si misura niente")
        return 2
    ok("guscio del banco costruito")

    rc, out, err = remoto(
        "printf '%%s\\n' '%s' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root "
        "'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 "
        "NGHTTP3=/srv/src/b2/nghttp3 bash %s/src/costruisci.sh 2>&1 | tail -12'"
        % (PAROLA_SUDO, DENTRO), tetto=1800)
    print(out)
    if rc != 0:
        # ⚠ Il server non mi serve per MISURARE: se non si costruisce lo dico e
        #   vado avanti, ma il terreno restera' rosso su T5.3 e quel rosso e'
        #   vero.  ⛔ Quel che NON si fa e' nasconderlo.
        att("⚠ il server intero non si e' costruito: T5.3 del terreno restera' "
            "rosso, e il rosso e' vero.  Il banco misura lo stesso il "
            "codificatore, che e' quel che gli serve")
    else:
        ok("server intero costruito (T5.3 del terreno diventa verde)")
    return 0


# ⭐⭐ LE TRE SCENE, E SONO TRE GRANDEZZE DIVERSE.
#
# ⛔ Per il RITMO (la rampa) basta `testsrc2`: il costo di codifica dipende poco
#    dal contenuto.  ⛔⛔ Per il BITRATE no — e' la lezione di `codificatore.c`:
#    `[M]` la stessa tela costa 0,204 Mbit/s col desktop vero e 58,668 col film
#    con la grana.  ⇒ Un tetto si giudica su una scena FACILE e una DURA, e le
#    due dicono due cose opposte:
#      facile ⇒ il tetto NON deve spendere: se spende, il driver ha dedotto CBR
#               (`[M]` 83 volte il necessario, R31) e la cura si butta;
#      dura   ⇒ il tetto DEVE mordere: se il flusso resta sopra il filo, il
#               driver non ha obbedito e i primi due testimoni erano verdi per
#               niente.
FILTRI_SCENA = {
    "": "testsrc2=size=%s:rate=30",
    # ⚠ `noise` ad alta intensita': e' la scena piu' cara che si sappia produrre
    #   senza un film vero, ed e' quella su cui §3.8 misura i 58,668 Mbit/s.
    "-grana": "testsrc2=size=%s:rate=30,noise=alls=60:allf=t+u",
    # ⭐ La scena FACILE del prodotto e' il desktop vero, che qui non c'e'.  La
    #   piu' vicina che si puo' produrre e' una tinta piatta che si muove appena.
    #   ⛔ E si dichiara per quel che e': **non e' un desktop**, e' il fondo scala.
    "-piatta": "color=c=0x203040:size=%s:rate=30",
}


def scene(misure, quanti=6, quali=("",)):
    tit("3 · Le scene — %d fotogrammi BGRx per taglia, %d varianti"
        % (quanti, len(quali)))
    inf("⚠ La scena e' `testsrc2` di ffmpeg: deterministica, con movimento e")
    inf("  dettaglio.  ⛔ NON e' un desktop vero — la banda che esce da qui non")
    inf("  si legge come banda del prodotto; qui si misura il RITMO.")
    for m in misure:
        for q in quali:
            filtro = FILTRI_SCENA[q] % m
            rc, out, err = remoto(
                "mkdir -p %s/scene && test -s %s/scene/scena%s-%s.raw || "
                "ffmpeg -v error -y -f lavfi -i '%s' -frames:v %d "
                "-pix_fmt bgr0 -f rawvideo %s/scene/scena%s-%s.raw"
                % (LAV, LAV, q, m, filtro, quanti, LAV, q, m), tetto=900)
            if rc != 0:
                ko("⛔ scena%s %s: %s" % (q, m, err[:200]))
                return 2
            ok("scena%s %s" % (q or " (testsrc2)", m))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 2 · UN GIRO — N flussi identici, partenza sincronizzata, sonda accanto
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(nome, n, misura, fps, secondi, strada="scheda", codec="h264",
            componente="h264_vaapi", nodo="/dev/dri/renderD128", qp=26,
            zavorra=0, scena_fotogrammi=None, nodo_guasto_su=None,
            componente_guasto_su=None, metro_cieco=False,
            profondita=8, tetto_mbit=0, senza_scadenza=False, scena="",
            codec_davvero=None, profondita_davvero=None, tetto_davvero=None):
    """⭐ `codec_davvero` / `profondita_davvero` / `tetto_davvero` esistono per i
    guasti innestati e per NIENT'ALTRO: fanno girare una cosa e la fanno
    DICHIARARE come un'altra.  ⛔ E' il guasto che l'ancora del codec deve
    cogliere — un giro HEVC contato come H.264 (`fasi/09-…` §13.5: 21,18 contro
    7,92 Mbit/s sulla stessa scena, e mezza giornata di numeri buttati)."""
    l, a = (int(x) for x in misura.split("x"))
    # ⛔ Quel che si FA GIRARE puo' differire da quel che si DICHIARA solo nei
    #    guasti innestati; nel giro vero i due sono lo stesso valore.
    codec_giro = codec if codec_davvero is None else codec_davvero
    prof_giro = profondita if profondita_davvero is None else profondita_davvero
    tetto_giro = tetto_mbit if tetto_davvero is None else tetto_davvero
    if scena_fotogrammi is None:
        scena_fotogrammi = 4 if l * a > 3000000 else 6
    # ⛔ IL NONCE — l'antidoto al difetto della fase 9 (tre profili di fila che
    #    riferivano gli stessi identici numeri, letti dal giro precedente).  Ogni
    #    giro ha il suo, e il giudizio RIFIUTA un file che non lo porta.
    nonce = "%s-%d-%d" % (nome, n, int(time.time() * 1000))
    dir_giro = "%s/giri/%s" % (LAV, nonce)
    # ⚠ Il margine di partenza cresce con N e con la tela: aprire dodici
    #   codificatori 4K non e' istantaneo, e un flusso che parte tardi
    #   misurerebbe una macchina meno carica di quella che si voleva.
    margine = 4.0 + 0.5 * n + (2.0 if l * a > 3000000 else 0.0)
    ora_ns = orologio_remoto_ns()
    if ora_ns is None:
        return {"errore": "l'orologio della macchina non risponde"}
    parti_a = ora_ns + int(margine * 1e9)

    comandi = []
    for i in range(1, n + 1):
        nd = nodo_guasto_su if (nodo_guasto_su and i == 1) else nodo
        cp = componente_guasto_su if (componente_guasto_su and i == 1) else componente
        comandi.append(
            "%s --scena %s/scene/scena%s-%s.raw --misura %s --fps %d --secondi %d "
            "--uscita %s/f%d.json --nonce %s --strada %s --codec %s --componente %s "
            "--nodo %s --qp %d --scena-fotogrammi %d --parti-a %d --zavorra-us %d "
            "--profondita %d --tetto-banda-mbit %d %s"
            "--flusso %d > %s/f%d.log 2>&1 &"
            % (BIN, LAV, scena, misura, misura, fps, secondi, dir_giro, i, nonce,
               strada, codec_giro, cp, nd, qp, scena_fotogrammi, parti_a, zavorra,
               prof_giro, tetto_giro,
               "--senza-scadenza " if senza_scadenza else "",
               i, dir_giro, i))
    # ⛔ La sonda gira da ROOT: senza, non vede i descrittori DRM degli ALTRI
    #    processi, e «non ho potuto guardare» somiglierebbe a «non c'era nessuno».
    # ⚠ Senza scadenza il giro dura quanto ci vuole a fare i fotogrammi, non
    #   `secondi`: sotto carico puo' essere molto di piu'.  ⛔ Il tetto si allarga
    #   in proporzione a N, o il banco ucciderebbe il proprio giro e chiamerebbe
    #   «flusso non partito» un flusso che stava lavorando.
    respiro = (margine + secondi * (1 + n) + 120.0) if senza_scadenza \
        else (margine + secondi + 5.0)
    script = (
        "set -u; mkdir -p %s; "
        "printf '%%s\\n' '%s' | sudo -S -p '' python3 %s --uscita %s/sonda.jsonl "
        "  --secondi %.1f %s --nodo %s > %s/sonda.log 2>&1 & SP=$!; "
        "%s wait; kill $SP 2>/dev/null; wait $SP 2>/dev/null; "
        "for f in %s/f*.json; do echo \"@@@ $f\"; cat $f; done; "
        "echo '@@@FINE'"
        % (dir_giro, PAROLA_SUDO, SONDA, dir_giro, respiro,
           "--metro-cieco" if metro_cieco else "", nodo, dir_giro,
           " ".join(comandi), dir_giro))
    t_avvio = time.time()
    rc, out, err = remoto(script, tetto=int(respiro + 180))
    crudo = {"nonce": nonce, "dir": dir_giro, "n": n, "misura": misura, "fps": fps,
             "secondi": secondi, "strada": strada, "codec": codec,
             "componente": componente, "parti_a_ns": parti_a, "rc": rc,
             "profondita": profondita, "tetto_mbit": tetto_mbit, "scena": scena,
             "senza_scadenza": senza_scadenza,
             "durata_orologio": time.time() - t_avvio, "flussi": [], "guasti_lettura": []}
    for pezzo in out.split("@@@")[1:]:
        pezzo = pezzo.strip()
        if pezzo.startswith("FINE") or not pezzo:
            continue
        righe = pezzo.split("\n", 1)
        if len(righe) < 2:
            crudo["guasti_lettura"].append("file vuoto: %s" % righe[0])
            continue
        try:
            crudo["flussi"].append(json.loads(righe[1]))
        except Exception as e:
            crudo["guasti_lettura"].append("%s non e' JSON: %s" % (righe[0], e))
    rc2, sonda, _ = remoto("cat %s/sonda.jsonl" % dir_giro, tetto=120)
    crudo["sonda"] = []
    for riga in sonda.splitlines():
        try:
            crudo["sonda"].append(json.loads(riga))
        except Exception:
            pass
    return crudo


# ───────────────────────────────────────────────────────────────────────────
def _finestra(campioni, da_t, a_t):
    """I campioni dentro la finestra STABILE del giro.  ⚠ Il primo quinto si
    butta: e' l'avvio, e un avvio dentro la media abbassa l'occupazione."""
    dentro = [c for c in campioni if da_t <= c["t"] <= a_t]
    return dentro if len(dentro) >= 2 else None


def _media(v):
    """La media di quel che si e' letto, oppure `None` se non si e' letto
       niente.  ⛔ Mai 0 al posto di `None`."""
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def meccanismo(crudo):
    """⭐ IL MECCANISMO ACCANTO AL SINTOMO: che cosa stava facendo la macchina.

    ⛔ La GPU la legge il metro TARATO di A1 (`10-b87-metro-gpu.py`), non una
       lettura fatta qui: vedi l'intestazione di `10-b88-sonda.py`.  E i numeri
       che ne escono sono DUE, con nomi diversi perche' non sono la stessa cosa:

         `video_pct`      motori-equivalenti ×100 — il massimo e' **200**,
                          perche' `[M]` i VDBOX di questa scheda sono **due**;
         `video_uso_pct`  frazione della capacita' video totale, 0..100.

    ⛔ Ogni voce che non si e' potuta leggere torna `None`, non zero."""
    s = crudo.get("sonda") or []
    t0 = crudo["parti_a_ns"] / 1e9
    t1 = t0 + crudo["secondi"]
    # ⚠ Il primo quinto si butta: e' l'avvio, e `LEZIONI.md` §1.4 (forma E9) dice
    #   che un campione dell'avvio non e' un campione del regime.
    dentro = _finestra(s, t0 + crudo["secondi"] * 0.2, t1)
    fuori = {"campioni": len(dentro) if dentro else 0,
             "video_pct": None, "video_uso_pct": None, "miei_video_pct": None,
             "estranei_video_pct": None, "chi_estraneo": None,
             "render_pct": None, "video_enhance_pct": None,
             "capacita_video": None, "parziale": None, "radice": None,
             "cpu": None, "cpu_nuclei": None, "mem_disponibile_min_kb": None,
             "gt": None}
    if not dentro:
        return fuori
    a, b = dentro[0], dentro[-1]
    dt = b["t"] - a["t"]

    g = [c["gpu"] for c in dentro if c.get("gpu")]
    if g:
        fuori["video_pct"] = _media([x.get("video_pct") for x in g])
        fuori["video_uso_pct"] = _media([x.get("video_uso_pct") for x in g])
        fuori["miei_video_pct"] = _media([x.get("miei_video_pct") for x in g])
        fuori["estranei_video_pct"] = _media([x.get("estranei_video_pct") for x in g])
        fuori["render_pct"] = _media([x.get("render_pct") for x in g])
        fuori["video_enhance_pct"] = _media([x.get("video_enhance_pct") for x in g])
        fuori["capacita_video"] = g[-1].get("capacita_video")
        fuori["parziale"] = any(x.get("parziale") for x in g)
        fuori["radice"] = g[-1].get("radice")
        chi = {}
        for x in g:
            for k, v in (x.get("chi_estraneo") or {}).items():
                chi[k] = max(chi.get(k, 0.0), v)
        fuori["chi_estraneo"] = chi or None
        # ⭐ IL CONTESTO GT, senza il quale la percentuale e' ambigua: `[M]` A1,
        #    stesso lavoro, 26,41 % a 300 MHz contro 7,01 % a 1550 MHz.
        gt = [x.get("gt") for x in g if x.get("gt")]
        if gt:
            fuori["gt"] = {
                "act_mhz": _media([x.get("act_mhz") for x in gt]),
                "cur_mhz": _media([x.get("cur_mhz") for x in gt]),
                "min_mhz": gt[-1].get("min_mhz"), "max_mhz": gt[-1].get("max_mhz"),
                "bloccata": gt[-1].get("bloccata"),
                "rc6_pct": _media([x.get("rc6_pct") for x in gt]),
                "sveglia_pct": _media([x.get("sveglia_pct") for x in gt]),
            }
    try:
        du = b["cpu"]["utente"] - a["cpu"]["utente"]
        ds = b["cpu"]["sistema"] - a["cpu"]["sistema"]
        fuori["cpu"] = {"utente_nuclei": du / JIFFY / dt,
                        "sistema_nuclei": ds / JIFFY / dt}
        fuori["cpu_nuclei"] = (du + ds) / JIFFY / dt
    except Exception:
        pass
    try:
        fuori["mem_disponibile_min_kb"] = min(
            c["memoria"]["MemAvailable"] for c in dentro if c.get("memoria"))
    except Exception:
        pass
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ANCORA — che cosa e' USCITO, non che cosa si e' chiesto
# ═══════════════════════════════════════════════════════════════════════════
# Il prefisso della stringa per il decodificatore, per codec.  ⛔ Non si deduce
# dal nome del componente ne' dal comando dato: `codificatore.c` la compone
# leggendo l'**SPS del flusso prodotto** (`leggi_sps_h264` / `leggi_sps_hevc`),
# e questa e' l'unica riga del banco che sappia distinguere H.264 da HEVC senza
# fidarsi di nessuno.
PREFISSO_CODEC = {"h264": "avc1.", "hevc": "hev1."}


def ancora_del_flusso(crudo, f):
    """⛔⛔ IL GIRO E' DAVVERO QUELLO CHE DICE DI ESSERE?  Torna l'elenco (vuoto
    se tutto torna) delle ragioni per cui NON si puo' contare.

    ⛔ ESISTE PER UN DIFETTO CHE E' COSTATO MEZZA GIORNATA: fase 9 §13.5, il
       banco negoziava **HEVC** mentre il prodotto mandava **H.264**, e i due
       numeri sulla stessa scena erano `[M]` **21,18 contro 7,92 Mbit/s**.  ⚠ E
       il rapporto fra i due **non e' una costante** (0,36× sul retinato, 0,76×
       sulla grana, 1,7× in su sul desktop vero): non e' correggibile a
       posteriori con un fattore.  ⇒ Un giro HEVC contato come H.264 non si
       aggiusta, si butta — e per buttarlo bisogna accorgersene.

    ⛔ LE QUATTRO DOMANDE, e ognuna ha tre esiti:
       1. il **codec** che e' uscito: dal PREFISSO della stringa composta
          sull'SPS del flusso, non dal `--codec` dato ne' dal nome del
          componente (`h264_vaapi`);
       2. la **profondita'** che e' uscita: dall'SPS, non dalla richiesta;
       3. il **modo di controllo del bitrate**: `1 = CQP` a tetto spento,
          `5 = QVBR` a tetto acceso.  ⚠ `fasi/10-…md` §6.6: *«la rilettura dentro
          VA-API non dice niente»* — `vaQueryConfigAttributes` rende la maschera
          delle CAPACITA', identica qualunque cosa si sia chiesta.  ⛔ Ma
          `modo_bitrate` qui NON e' quella maschera: e' `rc_mode` **riletto dal
          contesto** (`codificatore.c:2399`), ed e' il **secondo** testimone.
          Il terzo sono i byte, e li guarda `p_bitrate()`;
       4. che il flusso che si legge sia stato prodotto con la **stessa riga di
          comando** che il banco crede di aver dato (`codec_chiesto`,
          `profondita_chiesta`, `tetto_banda_mbit` sono scritti dal C leggendo il
          proprio `argv`).

    ⛔ E `letto_dal_flusso == false` NON e' un verde: e' *«non ho potuto
       leggere che cosa e' uscito»*, e allora il giro non si conta.  `None` non
       e' zero."""
    guai = []
    c = f.get("confessione", {})
    quale = f.get("flusso")

    # 4 · quel che il C dice di aver ricevuto contro quel che il banco crede.
    #     ⚠ Va per primo: se il comando dato non e' quello creduto, tutto il
    #     resto e' la risposta giusta alla domanda sbagliata.
    for campo, atteso, nome in (
            ("codec_chiesto", crudo.get("codec"), "il codec"),
            ("profondita_chiesta", crudo.get("profondita", 8), "la profondita'"),
            ("tetto_banda_mbit", crudo.get("tetto_mbit", 0), "il tetto di banda")):
        avuto = f.get(campo)
        if avuto is None:
            guai.append(
                "⛔ flusso %s: il flusso NON DICHIARA «%s» — questo banco non puo' "
                "verificare che abbia girato quel che credo di avergli chiesto "
                "(binario vecchio?).  ⛔ E «non l'ho letto» non e' «era giusto»"
                % (quale, campo))
        elif avuto != atteso:
            guai.append(
                "⛔⛔ flusso %s: %s CHIESTO dal banco e' «%s», il flusso e' partito "
                "con «%s» — il giro sta misurando una cosa e il banco ne conterebbe "
                "un'altra (fase 9 §13.5)" % (quale, nome, atteso, avuto))

    # 1-2 · quel che e' USCITO, letto dai byte.
    if not c.get("letto_dal_flusso"):
        guai.append(
            "⛔ flusso %s: l'SPS del flusso NON e' stato letto ⇒ codec e "
            "profondita' effettivi sono `[?]`, e un giro di cui non si sa che cosa "
            "sia uscito non si conta come verde" % quale)
        return guai
    atteso_pref = PREFISSO_CODEC.get(crudo.get("codec"))
    stringa = c.get("stringa_codec") or ""
    if atteso_pref is None:
        guai.append("⛔ flusso %s: codec «%s» sconosciuto a questo banco: non so "
                    "quale prefisso pretendere" % (quale, crudo.get("codec")))
    elif not stringa.startswith(atteso_pref):
        guai.append(
            "⛔⛔ flusso %s: si conta come **%s** un flusso la cui stringa e' «%s» "
            "(attesa «%s…»).  ⛔ La stringa e' composta sull'SPS PRODOTTO: e' il "
            "flusso a dire il codec, non il comando"
            % (quale, (crudo.get("codec") or "?").upper(), stringa or "(vuota)",
               atteso_pref))
    prof_attesa = crudo.get("profondita", 8)
    prof_flusso = c.get("profondita_flusso")
    if prof_flusso is None:
        guai.append("⛔ flusso %s: profondita' del flusso non letta" % quale)
    elif prof_flusso != prof_attesa:
        guai.append(
            "⛔ flusso %s: chiesti %d bit per campione, l'SPS ne dichiara %d — "
            "Main e Main10 sono due colonne e non si mediano"
            % (quale, prof_attesa, prof_flusso))

    # 3 · il modo del bitrate, RILETTO dal contesto.
    atteso_modo = 5 if crudo.get("tetto_mbit", 0) else 1
    nome_modo = {1: "CQP", 5: "QVBR"}
    avuto_modo = c.get("modo_bitrate")
    if avuto_modo is None or avuto_modo < 0:
        guai.append(
            "⛔ flusso %s: il modo di controllo del bitrate NON si e' potuto "
            "rileggere ⇒ `[?]`, e non si conclude che sia quello chiesto" % quale)
    elif avuto_modo != atteso_modo:
        guai.append(
            "⛔⛔ flusso %s: CHIESTO %s (%d) e il contesto ne rilegge %s (%d) — e' "
            "R31: *«il modo di controllo del bitrate non si sceglie: lo deduce il "
            "driver»*"
            % (quale, nome_modo.get(atteso_modo, "?"), atteso_modo,
               nome_modo.get(avuto_modo, "?"), avuto_modo))
    # ⛔ E i tre numeri del tetto: a tetto acceso il punto DEVE stare sotto il
    #    filo, o il driver deduce CBR (R31 alla lettera, `codificatore.c:1907`).
    if crudo.get("tetto_mbit", 0):
        punto, filo = c.get("banda_punto"), c.get("banda_filo")
        if punto is None or filo is None:
            guai.append("⛔ flusso %s: i numeri del tetto non si sono letti" % quale)
        elif punto >= filo:
            guai.append(
                "⛔⛔ flusso %s: punto di lavoro %d bit/s ≥ filo %d — con "
                "`rc_max_rate == bit_rate` il driver Intel DEDUCE il CBR, senza un "
                "errore e senza una riga di registro.  E' R31" % (quale, punto, filo))
    return guai


def giudica(crudo):
    """⛔ IL VERDETTO, E LE SUE RAGIONI.  Tre esiti, non due: VERDE (il ritmo si
    tiene), ROSSO (non si tiene, o il giro non vale), `[?]` (non si e' potuto
    misurare — e allora non si giudica)."""
    v = {"verde": None, "perche": [], "invalido": [], "sintomo": {}, "causa": None}
    n = crudo["n"]
    flussi = crudo.get("flussi", [])

    # ⛔ 1 · IL GIRO VALE?  Prima di ogni numero.
    if crudo.get("errore"):
        v["invalido"].append(crudo["errore"])
    for g in crudo.get("guasti_lettura", []):
        v["invalido"].append(g)
    if len(flussi) != n:
        v["invalido"].append(
            "⛔ chiesti %d flussi, tornati %d risultati: i mancanti NON sono «flussi "
            "a 0 fps», sono flussi di cui non si sa niente" % (n, len(flussi)))
    for f in flussi:
        # ⛔ IL NONCE — un risultato del giro precedente e' peggio di un risultato
        #    mancante: sembra buono.
        if f.get("nonce") != crudo["nonce"]:
            v["invalido"].append(
                "⛔ il flusso %s porta il nonce «%s» e questo giro e' «%s»: e' il "
                "conteggio di UN ALTRO GIRO e non si legge"
                % (f.get("flusso"), f.get("nonce"), crudo["nonce"]))
        if f.get("scritto_ns") and f["scritto_ns"] < crudo["parti_a_ns"]:
            v["invalido"].append(
                "⛔ il flusso %s e' stato scritto PRIMA della partenza di questo giro"
                % f.get("flusso"))
        if not f.get("aperto"):
            v["invalido"].append(
                "⛔ il flusso %s NON E' PARTITO: %s — e non si conta come «0 fps»"
                % (f.get("flusso"), f.get("errore")))
            continue
        c = f.get("confessione", {})
        if not c.get("ha_obbedito"):
            v["invalido"].append("⛔ flusso %s: il codificatore non ha obbedito (%s)"
                                 % (f["flusso"], c.get("perche_no")))
        if not c.get("in_hardware"):
            v["invalido"].append(
                "⛔ flusso %s: RIPIEGO IN SOFTWARE — componente «%s», non in "
                "hardware.  ⚠ Un soffitto misurato cosi' non e' quello della GPU"
                % (f["flusso"], c.get("componente")))
        if c.get("componente") != crudo["componente"]:
            v["invalido"].append(
                "⛔ flusso %s: chiesto «%s», aperto «%s»"
                % (f["flusso"], crudo["componente"], c.get("componente")))
        if not c.get("bassa_potenza_verificata"):
            v["invalido"].append(
                "⛔ flusso %s: l'entrypoint NON e' stato verificato sul driver — "
                "«gliel'ho chiesto» e «l'ha fatto» hanno lo stesso aspetto "
                "(`LEZIONI.md` §1.8)" % f["flusso"])
        for riga in ancora_del_flusso(crudo, f):
            v["invalido"].append(riga)
        if not f.get("in_orario"):
            v["invalido"].append(
                "⛔ flusso %s non era pronto all'istante di partenza: ha misurato "
                "una macchina meno carica di quella che si voleva" % f["flusso"])
    # ⛔⛔ 1-bis · LA GPU E' UNA — e se ci stava anche qualcun altro, il numero e'
    #      piu' basso del vero **e non lo grida nessuno** (`LEZIONI.md` §1.26).
    v["meccanismo"] = meccanismo(crudo)
    m0 = v["meccanismo"]
    if m0.get("radice") is False:
        v["invalido"].append(
            "⛔ il metro NON girava da root: i processi degli altri utenti non li "
            "ha visti, e «non ho guardato» non e' «non c'era nessuno»")
    # ⚠ La soglia e' il 5 % di UN motore-equivalente, e si dichiara: sotto quel
    #   valore c'e' il fondo delle sessioni ferme degli altri banchi (un desktop
    #   immobile codifica pochissimo); sopra, c'e' qualcuno che lavora davvero.
    if m0.get("estranei_video_pct") is not None and m0["estranei_video_pct"] > 5.0:
        v["invalido"].append(
            "⛔ UN ALTRO CARICO STAVA SUL MOTORE VIDEO (%.1f %% di un motore, %s): "
            "il giro non vale — due carichi di GPU insieme si falsano in silenzio"
            % (m0["estranei_video_pct"], m0.get("chi_estraneo")))
    if v["invalido"]:
        v["verde"] = False
        return v

    # 2 · IL SINTOMO — fotogrammi effettivi, ritardo, pixel.
    fps_eff = [f["fps_effettivi"] for f in flussi]
    prodotti = [f["fotogrammi_prodotti"] for f in flussi]
    richiesti = flussi[0]["fotogrammi_richiesti"]
    l, a = (int(x) for x in crudo["misura"].split("x"))
    mpix = sum(f["mpixel_s"] for f in flussi)
    v["sintomo"] = {
        "fps_richiesti": crudo["fps"],
        "fps_effettivi_minimo": min(fps_eff),
        "fps_effettivi_medio": sum(fps_eff) / len(fps_eff),
        "fotogrammi_richiesti_per_flusso": richiesti,
        "fotogrammi_prodotti_minimo": min(prodotti),
        "mpixel_s_totali": mpix,
        "mbit_s_totali": sum(f["mbit_s"] for f in flussi),
        "us_codifica_mediana": max(f["us_codifica"]["mediana"] for f in flussi),
        "us_codifica_peggiore": max(f["us_codifica"]["peggiore"] for f in flussi),
        "us_totale_mediana": max(f["us_totale"]["mediana"] for f in flussi),
        "us_conversione_mediana": max(f["us_conversione"]["mediana"] for f in flussi),
        "us_caricamento_mediana": max(f["us_caricamento"]["mediana"] for f in flussi),
        "ritardo_ms_mediano": max(f["us_ritardo"]["mediana"] for f in flussi) / 1000.0,
        "ritardo_ms_peggiore": max(f["us_ritardo"]["peggiore"] for f in flussi) / 1000.0,
        "trattenuti": sum(f["trattenuti"] for f in flussi),
        "ricodifiche": sum(f["ricodifiche"] for f in flussi),
    }

    # ⛔ 3 · IL RITMO E' STATO MANTENUTO?  E si dice col NUMERO, non arrotondando.
    soglia = crudo["fps"] * TOLLERANZA
    v["verde"] = min(fps_eff) >= soglia
    if v["verde"]:
        v["perche"].append(
            "il ritmo si tiene su tutti e %d: chiesti %d fotogrammi/s, il peggiore "
            "ne fa %.1f (soglia %.1f = %d%% del chiesto)"
            % (n, crudo["fps"], min(fps_eff), soglia, int(TOLLERANZA * 100)))
    else:
        v["perche"].append(
            "⛔ IL RITMO NON SI TIENE: chiesti %d fotogrammi/s per flusso, il "
            "peggiore ne fa %.1f e il medio %.1f; chiesti %d fotogrammi per flusso, "
            "il peggiore ne consegna %d"
            % (crudo["fps"], min(fps_eff), sum(fps_eff) / len(fps_eff), richiesti,
               min(prodotti)))
        v["causa"] = attribuisci(v, crudo)
    return v


def attribuisci(v, crudo):
    """⛔⛔ PERCHE' HA CEDUTO — ed e' la parte che vale.

    ⚠ Questa e' un'**attribuzione**, e si dichiara come tale: e' la lettura di
      cinque testimoni messi in fila, non una dimostrazione.  Ogni causa porta
      accanto il numero che l'ha fatta scegliere, cosi' chi non e' d'accordo sa
      quale numero contestare.

    ⛔ E il testimone della GPU si legge in **frazione della capacita'**
      (`video_uso_pct`, 0..100 su DUE motori), non in motori-equivalenti: sono i
      due numeri che A1 avverte di non confondere, e confonderli sbaglia il
      budget di un fattore due."""
    m = v.get("meccanismo") or {}
    s = v["sintomo"]
    uso, uno = m.get("video_uso_pct"), m.get("video_pct")
    cpu = m.get("cpu_nuclei")
    prova = []

    # a) LA GPU — i motori video pieni.  ⛔ `None` non e' zero: se il metro non
    #    ha letto, questa strada non si percorre e si dichiara.
    if uso is None:
        prova.append("[?] l'occupazione dei motori video NON e' stata letta: la "
                     "causa GPU non si puo' ne' affermare ne' escludere")
    elif uso >= 90.0:
        return {"quale": "GPU", "prova": "i motori video sono al %.0f %% della "
                "capacita' (%.0f su 200 in motori-equivalenti): pieni"
                % (uso, uno), "note": prova}
    else:
        prova.append("i motori video stanno al %.0f %% della capacita' "
                     "(%.0f/200 motori-equivalenti): NON sono saturi" % (uso, uno))
        # ⭐ IL CASO CHE VALE DA SOLO: un motore pieno e l'altro fermo.  Vuol
        #    dire che il lavoro non si divide fra i due VDBOX, e il soffitto e'
        #    la META' di quel che la scheda avrebbe.
        if uno is not None and uno >= 90.0 and uso < 60.0:
            return {"quale": "GPU — ma UN SOLO VDBOX su due",
                    "prova": "%.0f motori-equivalenti su 200: un motore e' pieno "
                    "e l'altro no.  ⛔ Il soffitto qui e' la META' della scheda, "
                    "e non e' un limite dell'hardware" % uno, "note": prova}

    # b) LA CPU — chi prepara i fotogrammi.
    if cpu is None:
        prova.append("[?] la CPU non e' stata letta")
    elif cpu >= NUCLEI * 0.90:
        return {"quale": "CPU", "prova": "%.1f nuclei occupati su %d disponibili"
                % (cpu, NUCLEI), "note": prova}
    else:
        prova.append("la CPU sta a %.1f nuclei su %d: non e' finita" % (cpu, NUCLEI))

    # c) LA PREPARAZIONE del singolo flusso — anche senza saturare la macchina,
    #    se preparare costa piu' del codificare il collo e' li'.
    prep = s["us_conversione_mediana"] + s["us_caricamento_mediana"]
    if prep > s["us_codifica_mediana"]:
        return {"quale": "CPU (preparazione del fotogramma)",
                "prova": "per fotogramma: preparare %.1f ms (conversione %.1f + "
                "caricamento %.1f) contro %.1f ms di codifica"
                % (prep / 1000.0, s["us_conversione_mediana"] / 1000.0,
                   s["us_caricamento_mediana"] / 1000.0,
                   s["us_codifica_mediana"] / 1000.0), "note": prova}

    # d) LA MEMORIA.
    mem = m.get("mem_disponibile_min_kb")
    if mem is not None and mem < 1024 * 1024:
        return {"quale": "memoria", "prova": "MemAvailable sceso a %.1f GB"
                % (mem / 1048576.0), "note": prova}

    # e) LA SERIALIZZAZIONE — il caso che resta, ed e' un caso vero: il flusso
    #    aspetta la GPU un fotogramma per volta (`avcodec_receive_packet` subito
    #    dopo il `send`), quindi il singolo flusso e' fermo anche se il motore ha
    #    ancora spazio.  ⚠ E' un limite del CAMMINO, non del ferro.
    if s["us_totale_mediana"] > 1e6 / crudo["fps"]:
        return {"quale": "il singolo flusso, non la macchina",
                "prova": "un fotogramma costa %.1f ms e il ritmo chiesto ne "
                "concede %.1f: il flusso aspetta la GPU a turno, e i motori non "
                "sono pieni" % (s["us_totale_mediana"] / 1000.0,
                                1000.0 / crudo["fps"]), "note": prova}
    return {"quale": None, "prova": "[?] nessuno dei cinque testimoni spiega il "
            "calo: NON si attribuisce", "note": prova}


def etichetta(crudo):
    """⭐ La riga che identifica il giro, e porta addosso le TRE cose che non si
    mediano fra loro: il codec, la profondita' e il modo del bitrate.  ⛔ Un
    verdetto stampato senza queste tre e' un numero che si puo' rileggere sotto
    l'etichetta sbagliata."""
    prof = crudo.get("profondita", 8)
    tetto = crudo.get("tetto_mbit", 0)
    nome = crudo["codec"].upper()
    if crudo["codec"] == "hevc":
        nome += " Main10" if prof == 10 else " Main"
    else:
        nome += " %d bit" % prof
    modo = ("QVBR tetto %d Mbit/s" % tetto) if tetto else "CQP"
    return "%s · %s · N=%-2d · %s · %d/s · %ds · strada %s%s" % (
        nome, modo, crudo["n"], crudo["misura"], crudo["fps"],
        crudo["secondi"], crudo["strada"],
        (" · scena%s" % crudo["scena"]) if crudo.get("scena") else "")


def stampa_verdetto(crudo, v):
    e = etichetta(crudo)
    if v["invalido"]:
        ko(e + "  ⇒ GIRO NON VALIDO")
        for r in v["invalido"][:6]:
            inf(r)
        return
    s, m = v["sintomo"], v.get("meccanismo") or {}
    (ok if v["verde"] else ko)(e)
    for r in v["perche"]:
        inf(r)
    inf("Mpixel/s totali %.1f · banda %.1f Mbit/s · codifica mediana %.2f ms, "
        "peggiore %.2f ms" % (s["mpixel_s_totali"], s["mbit_s_totali"],
                              s["us_codifica_mediana"] / 1000.0,
                              s["us_codifica_peggiore"] / 1000.0))
    inf("ritardo di consegna: mediano %.1f ms, peggiore %.1f ms · trattenuti %d "
        "· ricodifiche %d" % (s["ritardo_ms_mediano"], s["ritardo_ms_peggiore"],
                              s["trattenuti"], s["ricodifiche"]))
    # ⭐ IL MECCANISMO, e i due numeri della GPU si scrivono TUTT'E DUE con il
    #    nome accanto: chi li confonde sbaglia il budget di un fattore due.
    inf("motori video: %s della capacita' (%s/200 motori-equivalenti, capacita' "
        "%s) · miei %s · estranei %s"
        % (_pct(m.get("video_uso_pct")), _pct(m.get("video_pct")),
           m.get("capacita_video"), _pct(m.get("miei_video_pct")),
           _pct(m.get("estranei_video_pct"))))
    inf("render %s · video-enhance %s · CPU %s nuclei/%d (utente %s, sistema %s)"
        % (_pct(m.get("render_pct")), _pct(m.get("video_enhance_pct")),
           "%.1f" % m["cpu_nuclei"] if m.get("cpu_nuclei") is not None else "[?]",
           NUCLEI,
           "%.1f" % m["cpu"]["utente_nuclei"] if m.get("cpu") else "[?]",
           "%.1f" % m["cpu"]["sistema_nuclei"] if m.get("cpu") else "[?]"))
    gt = m.get("gt") or {}
    inf("⚠ contesto GT (senza il quale la percentuale e' ambigua): atto %s MHz, "
        "chiesta %s, min %s, max %s%s · RC6 %s · sveglia %s"
        % (_num(gt.get("act_mhz")), _num(gt.get("cur_mhz")), gt.get("min_mhz"),
           gt.get("max_mhz"), "  ⚠ BLOCCATA" if gt.get("bloccata") else "",
           _pct(gt.get("rc6_pct")), _pct(gt.get("sveglia_pct"))))
    if m.get("parziale"):
        att("⚠ il metro dichiara la lettura PARZIALE: e' un limite INFERIORE")
    if v.get("causa"):
        c = v["causa"]
        att("PERCHE' CEDE ⇒ %s — %s" % (c["quale"] or "[?] non attribuito", c["prova"]))
        for nota in c.get("note", []):
            inf("   " + nota)


def _pct(x):
    return "[?]" if x is None else "%.1f %%" % x


def _num(x):
    return "[?]" if x is None else "%.0f" % x


# ═══════════════════════════════════════════════════════════════════════════
# 3 · LA TARATURA DEL METRO (regola 6) — si inietta un valore NOTO
# ═══════════════════════════════════════════════════════════════════════════
def tara(args):
    """⭐ IL CONTROLLO POSITIVO DEL METRO, E LA PROVA DEL §CLOCK DI A1.

    ⛔ Il metro non lo taro io: e' gia' tarato (`10-b87-metro-gpu.py --tara`,
       `--certifica` 43/43).  Quel che faccio qui e' l'altra meta', ed e' quella
       che vincola la rampa: **inietto una quantita' NOTA di lavoro** — lo stesso
       identico flusso a 10, 20 e 30 fotogrammi al secondo — e guardo se
       l'occupazione la segue **in proporzione**.

    ⛔⛔ E la previsione e' che NON la segua, perche' `drm-engine-video` conta
        TEMPO OCCUPATO e non LAVORO FATTO: `[M]` A1, stessa codifica 1080p30,
        26,41 % a 300 MHz contro 7,01 % a 1550 MHz.  ⇒ Se la proporzione salta e
        la GT si e' mossa, **la retta non si estrapola** e la capienza si misura
        **a saturazione**.  Questo comando serve a dimostrarlo sui MIEI numeri,
        non a fidarsi di quelli di un altro."""
    tit("CONTROLLO POSITIVO DEL METRO + LA PROVA DEL §CLOCK")
    altro = os.path.join(QUI, "10-b87-metro-gpu.py")
    if not os.path.exists(altro):
        ko("⛔ manca `10-b87-metro-gpu.py` (il metro tarato di A1): NON misuro "
           "con un metro mio non tarato")
        return 2
    ok("il metro tarato di A1 c'e': %s" % altro)
    inf("Inietto un lavoro NOTO: lo stesso flusso a 10, 20 e 30 fotogrammi/s.")
    letture = []
    luc = Lucchetto(secondi=3 * args.secondi + 400)
    luc.__enter__()
    for fps in (10, 20, 30):
        c = un_giro("tara%d" % fps, 1, args.misura, fps, args.secondi)
        v = giudica(c)
        m = v.get("meccanismo") or {}
        gt = m.get("gt") or {}
        fatti = c["flussi"][0] if c.get("flussi") else {}
        letture.append({"fps": fps, "mio": m.get("miei_video_pct"),
                        "uso": m.get("video_uso_pct"),
                        "eff": fatti.get("fps_effettivi"),
                        "mhz": gt.get("act_mhz"),
                        "cod_us": (fatti.get("us_codifica") or {}).get("mediana")})
        inf("%2d/s chiesti · %s/s effettivi · MIO motore video %s · GT %s MHz · "
            "codifica mediana %s ms"
            % (fps, "%.1f" % (fatti.get("fps_effettivi") or 0),
               _pct(m.get("miei_video_pct")), _num(gt.get("act_mhz")),
               "%.2f" % ((fatti.get("us_codifica") or {}).get("mediana", 0) / 1000.0)))
        if v.get("invalido"):
            for r in v["invalido"][:4]:
                inf(r)
    luc.__exit__()

    if any(x["mio"] is None for x in letture):
        ko("⛔ IL METRO NON HA LETTO il mio carico: l'occupazione resta `[?]` in "
           "tutto il banco.  `None` non e' zero.")
        return 1
    base = letture[0]
    if not base["mio"] or not base["eff"]:
        ko("⛔ a 10 fps il metro legge zero o il flusso non e' partito: non c'e' "
           "controllo positivo")
        return 1

    tit("LA PROPORZIONE — e il numero che conta e' lo SCARTO, non il rapporto")
    lineare = True
    for x in letture:
        # ⚠ Il rapporto atteso si prende dal ritmo VERO, non dal chiesto: se a 30
        #   ne sono usciti 28, il lavoro iniettato era 2,8× e non 3×.
        atteso = x["eff"] / base["eff"]
        letto = x["mio"] / base["mio"]
        scarto = abs(letto - atteso) / atteso
        (ok if scarto <= 0.10 else ko)(
            "%2d/s: lavoro ×%.2f, occupazione letta ×%.2f — scarto %.0f %% "
            "(GT %s MHz)" % (x["fps"], atteso, letto, scarto * 100, _num(x["mhz"])))
        lineare = lineare and scarto <= 0.10

    mhz = [x["mhz"] for x in letture if x["mhz"] is not None]
    mossa = bool(mhz) and (max(mhz) - min(mhz)) > 50
    if lineare:
        ok("⭐ l'occupazione segue il lavoro entro il 10 %: il metro fa da "
           "controllo positivo e, IN QUESTA FINESTRA, la proporzione tiene.")
    else:
        ko("⛔ L'OCCUPAZIONE NON SEGUE IL LAVORO IN PROPORZIONE.")
    if mossa:
        att("⚠ E la GT si e' mossa fra %d e %d MHz durante le tre prove: e' il "
            "§CLOCK di A1 — `drm-engine-video` conta TEMPO, e il tempo dipende "
            "dalla frequenza." % (min(mhz), max(mhz)))
    inf("⛔⛔ LA CONSEGUENZA, e vincola tutta la rampa: la capienza della GPU "
        "**non si estrapola** da un carico leggero.  Il numero di Mpixel/s si "
        "prende **al punto di saturazione**, dove la GT e' gia' alta.")
    inf("⚠ Quel che resta `[?]`: il valore ASSOLUTO in pixel/s del motore — "
        "fdinfo dice per quanto tempo il motore e' stato occupato, non quanto "
        "lavoro ci e' passato dentro.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 4 · LA RAMPA
# ═══════════════════════════════════════════════════════════════════════════
ESITI = []          # tutti i giri della sessione, per il sunto finale
TERRENO = {"esito": None, "righe": []}   # ⛔ `None` = non l'ho verificato


def terreno(args):
    """⛔ IL CONTROLLO DEL TERRENO — e NON e' riscritto qui: si chiama
    `banchi/10-b0-terreno.sh`, che ha 21 predicati e `[M]` 30 guasti su 30 che
    lo fanno mordere.  ⚠ Riscriverne una versione mia sarebbe un secondo metro
    non tarato accanto a uno tarato.

    ⛔ Si chiama con `LUCCHETTO_MIO=1`: da questo giro escono numeri che
       riferiro', e allora il lucchetto **dev'essere mio** — che sia libero non
       basta.

    ⭐ E L'ESITO NON FERMA IL BANCO, LO ETICHETTA.  La ragione e' il fatto della
       giornata: sulla macchina di prova ci sono **altri banchi della fase 10
       con sessioni GNOME vere accese**, e non sono miei da spegnere.  ⇒ Un
       soffitto misurato con quattro desktop vivi accanto **non e' il soffitto
       di una macchina scarica**, e questa e' la scena che va scritta di fianco
       a ogni numero.  ⛔ Un numero con la scena accanto vale; un numero senza,
       no."""
    tit("IL TERRENO — 21 predicati, chiamati e non riscritti")
    amb = ("CHI=%s PORTA=%d UTENTE=%s ALBERO=%s LAV=%s LUCCHETTO=%s "
           "LUCCHETTO_MIO=1 PORTE_AMMESSE='%s' MACCHINA=%s PAROLA_SUDO=%s"
           % (CHI, args.porta_finta, args.utente, ALBERO, LAV,
              os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d"),
              " ".join(args.porte_ammesse), MACCHINA, PAROLA_SUDO))
    p = subprocess.run(["bash", "-c", "%s bash %s/10-b0-terreno.sh"
                        % (amb, QUI)], capture_output=True, timeout=900)
    testo = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    print(testo)
    TERRENO["esito"] = p.returncode
    TERRENO["righe"] = [r for r in testo.splitlines() if "NO" in r or "??" in r][:12]
    if p.returncode == 0:
        ok("⭐ il terreno regge, su quel che ha potuto guardare")
    elif p.returncode == 1:
        ko("⛔ IL TERRENO NON REGGE — e il banco NON si ferma: misura lo stesso e "
           "SCRIVE la scena accanto ai numeri (ordine del regista: «un numero "
           "con la scena scritta accanto vale, uno senza no»)")
    else:
        att("⛔ NON HO POTUTO VERIFICARE IL TERRENO (esito 2): e' il terzo esito, "
            "non un verde.  I numeri che seguono portano questo `[?]` addosso")
    inf("⚠ LA SCENA, e va letta accanto a OGNI numero di questo banco: sulla "
        "macchina ci sono altri banchi della fase 10 con server e sessioni "
        "GNOME VERE accese (porte dichiarate: %s).  Non sono miei da spegnere."
        % (" ".join(args.porte_ammesse) or "nessuna"))
    return p.returncode


def una_rampa(misura, fps, secondi, scala, args, strada=None):
    """Un gradino dopo l'altro finche' cede.  Torna (ultimo_verde, primo_rosso).

    ⛔ Si ferma al PRIMO che non tiene: oltre non c'e' niente da imparare sul
       soffitto, e ogni giro in piu' e' tempo tolto agli altri nove agenti che
       aspettano il lucchetto."""
    strada = strada or args.strada
    print("  %s— %s a %d/s · durata %d s · strada %s —%s"
          % (GRASSO, misura, fps, secondi, strada, FINE))
    ultimo_verde, primo_rosso = None, None
    for n in scala:
        c = un_giro("r%s-%d-%s" % (misura, secondi, strada), n, misura, fps,
                    secondi, strada=strada, codec=args.codec,
                    componente=args.componente, profondita=args.profondita,
                    tetto_mbit=args.tetto_banda_mbit)
        v = giudica(c)
        stampa_verdetto(c, v)
        ESITI.append({"misura": misura, "fps": fps, "secondi": secondi, "n": n,
                      "strada": strada, "codec": args.codec,
                      "profondita": args.profondita,
                      "tetto_mbit": args.tetto_banda_mbit,
                      "verde": v["verde"], "invalido": bool(v["invalido"]),
                      "invalido_perche": v["invalido"][:3],
                      "sintomo": v.get("sintomo"), "meccanismo": v.get("meccanismo"),
                      "causa": v.get("causa")})
        if v["invalido"]:
            ko("⛔ giro non valido: la rampa su questa taglia si ferma qui")
            break
        if v["verde"]:
            ultimo_verde = n
        else:
            primo_rosso = n
            inf("⇒ ha ceduto a N=%d; l'ultimo che teneva era N=%s" % (n, ultimo_verde))
            break
    return ultimo_verde, primo_rosso


def scrivi_esiti(args):
    with open(args.esiti, "a") as f:
        for e in ESITI:
            f.write(json.dumps(e) + "\n")


def sunto(args):
    tit("⚠ LA SCENA DI QUESTI NUMERI — si legge PRIMA della tabella")
    inf("ferro: i5-13500T (20 filiere) · Intel UHD 730 integrata `renderD128` "
        "(`i915`, iHD 25.2.3) · ⛔ la Radeon `renderD129` e' chiusa da udev")
    prof = "Main10" if (args.codec == "hevc" and args.profondita == 10) else \
        ("Main" if args.codec == "hevc" else "High")
    inf("codificatore: `%s`, profilo %s (%d bit), `EncSliceLP` (bassa potenza) "
        "VERIFICATO sul driver · bframes 0 · nessun tetto di livello"
        % (args.componente, prof, args.profondita))
    if args.tetto_banda_mbit:
        inf("⛔ modo del bitrate: **QVBR**, pavimento %d Mbit/s ⇒ filo %.1f, punto "
            "%.1f, serbatoio %d ms (i tre numeri li deriva `codificatore.c`, non "
            "questo banco).  ⚠ QP %d = FATTORE DI QUALITA', non quantizzatore fisso"
            % (args.tetto_banda_mbit, args.tetto_banda_mbit * 0.8,
               args.tetto_banda_mbit * 0.8 * 0.75, 40, 26))
    else:
        inf("⛔ modo del bitrate: **CQP**, QP 26 costante — ed e' il predefinito "
            "del PRODOTTO (`main.c`: il tetto di banda nasce spento, invariante I6)")
    inf("scena: `testsrc2` di ffmpeg, %s fotogrammi ciclati — ⛔ NON e' un "
        "desktop vero: la banda che esce di qui non e' banda del prodotto" % 4)
    inf("⛔⛔ E QUESTA COLONNA NON SI MEDIA CON LE ALTRE: H.264 e HEVC, Main e "
        "Main10, CQP e QVBR sono grandezze diverse.  `[M]` fase 9 §13.5, stessa "
        "scena: 21,18 contro 7,92 Mbit/s, e il rapporto NON e' una costante")
    inf("terreno (`10-b0-terreno.sh`): esito %s%s"
        % (TERRENO["esito"],
           " — ⛔ NON REGGEVA: " + " / ".join(TERRENO["righe"][:4])
           if TERRENO["esito"] not in (0, None) else ""))
    tit("IL SUNTO — quanti Mpixel/s ha retto `renderD128` in %s"
        % args.codec.upper())
    inf("⛔ Il numero si legge dove il ritmo TIENE: e' il piu' alto misurato "
        "senza che nessun flusso perdesse il passo.")
    per_taglia = {}
    for e in ESITI:
        if e["verde"] and e["sintomo"]:
            k = (e["misura"], e["fps"], e["secondi"], e["strada"])
            if e["sintomo"]["mpixel_s_totali"] > per_taglia.get(k, (0, 0))[0]:
                per_taglia[k] = (e["sintomo"]["mpixel_s_totali"], e["n"])
    for k in sorted(per_taglia):
        mp, n = per_taglia[k]
        inf("%-10s %2d/s · %2ds · %-8s ⇒ N=%-2d tiene · %.0f Mpixel/s"
            % (k[0], k[1], k[2], k[3], n, mp))
    for e in ESITI:
        if e.get("causa") and e["causa"].get("quale"):
            inf("cede a %s N=%d: %s" % (e["misura"], e["n"], e["causa"]["quale"]))


def rampa(args):
    # ⛔⛔ IL LUCCHETTO PRIMA DEL TERRENO, e non dopo.
    #
    #    Il terreno controlla `LUCCHETTO_MIO=1`, cioe' *«il lucchetto e' MIO?»* —
    #    e con ragione: che sia libero non basta, perche' fra il controllo e la
    #    misura qualcun altro puo' prenderlo.  ⛔ Chiamarlo PRIMA di prendere il
    #    lucchetto lo fa dare rosso su una cosa vera ma sbagliata (*«e' di un
    #    altro»*), e quel rosso finisce accanto a numeri che invece sono stati
    #    presi col lucchetto in mano.  `[M]` 24 agosto 2026, e' successo qui.
    with Lucchetto(secondi=args.tetto_lucchetto):
        terreno(args)
        taglie = [(m, int(f)) for m, f in zip(args.misure, args.fps)]
        for misura, fps in taglie:
            tit("LA RAMPA · %s a %d/s · strada %s · %s"
                % (misura, fps, args.strada, args.codec.upper()))
            for secondi in args.durate:
                una_rampa(misura, fps, secondi, args.scala, args)
        scrivi_esiti(args)
        sunto(args)
    return 0


def tutto(args):
    """⭐⭐ TUTTO IL BANCO IN UN LUCCHETTO SOLO.

    ⛔ PERCHE' ESISTE, e la ragione e' misurata sul campo il 24 agosto 2026: sono
       **dieci agenti** in coda sullo stesso lucchetto, e chi lo prende lo tiene
       anche un'ora.  Prendere e mollare a ogni comando vuol dire rimettersi in
       fondo alla fila fra la taratura e la rampa, e fra la rampa e la
       certificazione — cioe' misurare **tre macchine diverse** e chiamarle una.
       ⚠ Il prezzo si dichiara: mentre questo gira, gli altri nove aspettano."""
    luc = Lucchetto(secondi=args.tetto_lucchetto)
    luc.__enter__()
    try:
        terreno(args)
        tara(args)

        tit("LA RAMPA CORTA — si cerca il GINOCCHIO a %d s" % args.durate[0])
        ginocchi = {}
        for misura, fps in zip(args.misure, [int(x) for x in args.fps]):
            ginocchi[(misura, fps)] = una_rampa(misura, fps, args.durate[0],
                                                args.scala, args)

        if len(args.durate) > 1:
            lunga = args.durate[1]
            tit("⚠ LA STESSA CASELLA A DURATA LUNGA (%d s) — `LEZIONI.md` §1.32"
                % lunga)
            inf("I giri corti sottostimano.  Se il verdetto cambia, quello che "
                "vale e' il LUNGO, e la differenza si scrive.")
            for (misura, fps), (verde, rosso) in ginocchi.items():
                scala = [x for x in (verde, rosso) if x]
                if not scala:
                    ko("%s: la rampa corta non ha dato nessun gradino da "
                       "riprovare" % misura)
                    continue
                una_rampa(misura, fps, lunga, scala, args)

        tit("⚠ IL CONTRASTO — le stesse taglie sulla STRADA DELLA MEMORIA")
        inf("⛔ Non e' la stessa misura e non si media con l'altra: qui i pixel")
        inf("   passano per la CPU (`sws_scale` + caricamento).  Serve a dire")
        inf("   quanto costa NON avere la copia zero della fase 8.")
        inf("⛔⭐ E per 854x480 NON E' UNA SCELTA: `[M]` 24 agosto 2026, il buffer")
        inf("   GBM di quella tela esce con passo **3416**, che non e' multiplo di")
        inf("   64 — la guardia di `codificatore.h` rifiuta l'importazione, e la")
        inf("   copia zero **su quella tela non esiste**.  ⇒ Il minimo di")
        inf("   `SPECIFICHE.md` §5.5 si misura QUI, non sulla strada della scheda.")
        for m, f in [(x, int(y)) for x, y in zip(args.memoria_misure,
                                                 args.memoria_fps)]:
            una_rampa(m, f, args.durate[0], args.scala, args, strada="memoria")

        scrivi_esiti(args)
        sunto(args)
        certifica(args)
        controllo(args)
    finally:
        luc.__exit__()
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 4-bis · ⭐⭐ QVBR — IL MODO CHE IL PRODOTTO USA QUANDO IL TETTO E' ACCESO
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ PERCHE' QUESTO PEZZO E' PIU' DELICATO DI COME SUONA.  `LEZIONI.md` §1.8:
#     v1 si e' fatto male **due volte** proprio qui — il driver che DEDUCEVA il
#     modo di controllo del bitrate da come erano riempiti due campi, e imponeva
#     banda costante senza che nessuno l'avesse scelta.  `[M]` su questo ferro il
#     CBR a scena ferma spende **83 volte** il necessario (15,98 contro 0,193
#     Mbit/s), e a dirlo fu solo la bolletta.
#
# ⛔ E LA VERIFICA NON SI CHIUDE DENTRO VA-API su questo driver (`fasi/10-…md`
#    §6.6): `vaQueryConfigAttributes` sulla config creata rende **la maschera
#    delle capacita'**, identica qualunque cosa si sia chiesta ⇒ *quale* modo sia
#    in vigore **non si legge**.  ⇒ ⭐ La verifica si fa sul **FLUSSO**: due
#    richieste note devono dare due risposte diverse e prevedibili.
#
# ⛔⛔ E LA SCENA E' META' DELLA MISURA.  A scena DURA i modi regolati stanno
#     tutti dentro l'1 % l'uno dall'altro, e un banco che misurasse solo li' non
#     misurerebbe niente: il numero che smaschera il CBR e' a scena **facile**.
#     ⇒ Ogni bersaglio si prova su tutt'e due, e i due verdetti sono opposti.

# ⚠ I tre numeri del tetto si derivano dal pavimento DENTRO `codificatore.c`
#   (`TETTO_QUOTA_FILO 80`, `TETTO_QUOTA_PUNTO 75`, `TETTO_VBV_MS 40`).  ⛔ Qui
#   si RIPETONO solo per stampare l'atteso accanto al misurato: il valore che
#   fa fede e' quello **riletto dal contesto** (`banda_filo`, `banda_punto`), e
#   se i due divergessero sarebbe il banco a essere vecchio, non il prodotto.
def tetto_atteso(pavimento_mbit):
    filo = pavimento_mbit * 1e6 * 80 / 100
    return filo / 1e6, filo * 75 / 100 / 1e6


def _uno(crudo, v):
    """I numeri del PRIMO flusso di un giro a N=1, o `None` se il giro non vale."""
    if v["invalido"] or not crudo.get("flussi"):
        return None
    f = crudo["flussi"][0]
    c = f.get("confessione", {})
    return {"mbit": f["mbit_s"], "fps": f["fps_effettivi"],
            "fotogrammi": f["fotogrammi_prodotti"], "byte": f["byte_totali"],
            "impronta": f.get("impronta"),
            "modo": c.get("modo_bitrate"),
            "filo": (c.get("banda_filo") or 0) / 1e6,
            "punto": (c.get("banda_punto") or 0) / 1e6,
            "serbatoio_ms": c.get("banda_serbatoio_ms"),
            "stringa": c.get("stringa_codec")}


def tara_bitrate(args):
    """⛔ IL METRO SI TARA PRIMA (regola 6, `LEZIONI.md` §1.33): si inietta un
    valore NOTO e si verifica che il metro lo ritrovi.

    ⚠ E QUI IL VALORE NOTO NON PUO' VENIRE DAL PRODOTTO: il nostro codificatore
      offre due modi soli — CQP (tetto spento) e QVBR (tetto acceso) — e **in
      nessuno dei due il bitrate e' un valore che si chiede e si ritrova**.  ⇒ Il
      valore noto lo inietta `ffmpeg` in **CBR**, che e' il modo in cui il
      predicato e' verificabile senza ambiguita', e il metro tarato e' l'unica
      cosa che passa di qui al resto del comando: `byte × 8 / secondi`.
    ⛔ Si dichiara per quel che e': il metro e' tarato su ffmpeg, il MISURATO e'
       il prodotto.  Chi legge deve poter sapere quale delle due cose ha in mano."""
    tit("LA TARATURA DEL METRO DEL BITRATE — ⚠ il valore noto lo inietta ffmpeg")
    inf("⛔ Il prodotto non sa fare CBR: fa CQP e QVBR, e in nessuno dei due il")
    inf("   bitrate e' un numero che si chiede.  ⇒ Il bersaglio noto si inietta")
    inf("   con ffmpeg, e quel che si tara e' l'ARITMETICA, non il codificatore.")
    esiti = []
    for chiesto in (5, 20):
        secondi = 10
        cmd = ("cd %s && ffmpeg -v error -y -vaapi_device %s -f rawvideo "
               "-pix_fmt bgr0 -s %s -r 30 -stream_loop -1 -i %s/scene/scena-%s.raw "
               "-vf 'format=nv12,hwupload' -c:v h264_vaapi -low_power 1 "
               "-rc_mode CBR -b:v %dM -maxrate %dM -bufsize %dM -bf 0 "
               "-frames:v %d -f h264 %s/tara-cbr-%d.h264 && "
               "stat -c %%s %s/tara-cbr-%d.h264"
               % (LAV, args.nodo, args.misura, LAV, args.misura, chiesto, chiesto,
                  chiesto, 30 * secondi, LAV, chiesto, LAV, chiesto))
        rc, out, err = remoto(cmd, tetto=300)
        if rc != 0:
            ko("⛔ il bersaglio CBR %d Mbit/s non e' stato prodotto: %s"
               % (chiesto, err[:200]))
            return None
        try:
            byte = int(out.strip().splitlines()[-1])
        except Exception:
            ko("⛔ non ho letto la misura del file: il metro NON e' tarato")
            return None
        letto = byte * 8.0 / secondi / 1e6
        scarto = abs(letto - chiesto) / chiesto
        (ok if scarto <= 0.15 else ko)(
            "iniettati %d Mbit/s in CBR ⇒ il metro ne legge %.2f (scarto %.1f %%)"
            % (chiesto, letto, scarto * 100))
        esiti.append(scarto <= 0.15)
    if not all(esiti):
        ko("⛔ IL METRO DEL BITRATE NON RITROVA I VALORI NOTI: da qui in poi non "
           "si misura niente — un metro non tarato produce numeri, non misure")
        return False
    ok("⭐ il metro ritrova tutt'e due i bersagli: da qui in poi i Mbit/s valgono")
    return True


def p_tetto_morde(x, filo, tolleranza):
    """⛔ IL PREDICATO DEL BERSAGLIO, e sta in UNA funzione sola perche' `--certifica`
    innesta il guasto **su questa**, non su una copia.  `CODER.md` §3.3-bis: la
    guardia va dove il numero si consuma.

    Tre esiti.  ⛔ E il rosso porta **il numero, non arrotondato**: «ha sforato»
    non dice di quanto, e chi legge non sa se e' un margine o un ordine di
    grandezza."""
    if x is None or x.get("mbit") is None:
        return None, "il flusso non ha prodotto byte: non si giudica"
    ammesso = filo * (1.0 + tolleranza)
    if x["mbit"] <= ammesso:
        return True, ("chiesto un filo di %.3f Mbit/s, il flusso ne fa **%.3f** "
                      "(tolleranza %.0f %% ⇒ %.3f): ci sta"
                      % (filo, x["mbit"], tolleranza * 100, ammesso))
    return False, ("⛔ BERSAGLIO MANCATO: chiesto un filo di %.3f Mbit/s, il "
                   "flusso ne fa **%.3f** — sforo di %.3f Mbit/s, cioe' il "
                   "%.1f %% in piu' (tolleranza %.0f %% ⇒ %.3f)"
                   % (filo, x["mbit"], x["mbit"] - filo,
                      (x["mbit"] / filo - 1) * 100 if filo else 0.0,
                      tolleranza * 100, ammesso))


def _riga_qvbr(crudo, v, x, atteso_filo, atteso_punto):
    if x is None:
        ko("%s ⇒ GIRO NON VALIDO" % etichetta(crudo))
        for r in v["invalido"][:4]:
            inf(r)
        return
    inf("%-58s ⇒ %8.3f Mbit/s · %5.1f fot/s · modo %s · filo %.1f (atteso %.1f) "
        "· punto %.1f (atteso %.1f) · serbatoio %s ms"
        % (etichetta(crudo), x["mbit"], x["fps"],
           {1: "CQP", 5: "QVBR"}.get(x["modo"], "[?] %s" % x["modo"]),
           x["filo"], atteso_filo, x["punto"], atteso_punto, x["serbatoio_ms"]))


def bitrate(args):
    """⭐⭐ QVBR — quattro domande, e la terza e' quella che il primo giro non
    aveva potuto fare."""
    esiti_q = []

    def predicato(nome, esito, riga):
        """⛔ Tre esiti: `None` = non ho misurato, e allora NON si giudica."""
        if esito is None:
            att("[?] %s — %s" % (nome, riga))
        else:
            (ok if esito else ko)("%s — %s" % (nome, riga))
        esiti_q.append({"predicato": nome, "esito": esito, "riga": riga})

    tit("0 · CHE COSA CHIEDE IL PRODOTTO — ⚠ LETTO NEL CODICE, non misurato")
    inf("`src/codificatore.c:400` `modo_bitrate_voluto()`, e sono DUE modi:")
    inf("  tetto SPENTO  ⇒ `rc_mode = 1` **CQP**, nessun bit_rate, nessun serbatoio")
    inf("  tetto ACCESO  ⇒ `rc_mode = 5` **QVBR** + i tre numeri derivati dal")
    inf("                  pavimento: filo 80 %, punto 75 % del filo, serbatoio 40 ms")
    inf("⛔ E IL MODO SI CHIEDE PER NOME: `av_opt_set_int(priv_data, \"rc_mode\", …)`,")
    inf("   mai `auto` — `auto` sceglie in base alle altre opzioni, ed e' R31.")
    inf("⛔⛔ MA IL PREDEFINITO DEL PRODOTTO E' **CQP**, NON QVBR: `main.c:657`")
    inf("   `tetto_banda_mbit = 0` e `--tetto-banda-mbit` non e' fra le cinque cure")
    inf("   che si accendono (`CODER.md` §2-bis).  ⇒ Oggi, di suo, il prodotto")
    inf("   NON usa QVBR: lo usa solo se qualcuno accende il tetto a mano.")

    if not tara_bitrate(args):
        ko("⛔ senza metro tarato non si misura: mi fermo e lo dichiaro")
        return 1

    tit("1 · QVBR OBBEDISCE? — due scene, e i due verdetti sono OPPOSTI")
    inf("⛔ scena DURA (grana): il tetto DEVE mordere ⇒ sotto il filo")
    inf("⛔ scena FACILE (tinta): il tetto NON deve spendere ⇒ molto sotto il punto")
    inf("   ⚠ se spendesse, il driver avrebbe dedotto il CBR — `[M]` 83 volte il")
    inf("     necessario, ed e' R31, il difetto piu' caro del progetto.")
    tabella = {}
    for scena_q, nome_scena in (("-grana", "DURA"), ("-piatta", "FACILE")):
        print("\n  %s— scena %s (%s) —%s" % (GRASSO, scena_q, nome_scena, FINE))
        for pavimento in [0] + list(args.pavimenti):
            af, ap = tetto_atteso(pavimento)
            c = un_giro("qvbr%s-%d" % (scena_q, pavimento), 1, args.misura,
                        args.fps_bitrate, args.secondi, codec=args.codec,
                        componente=args.componente, profondita=args.profondita,
                        tetto_mbit=pavimento, scena=scena_q, qp=args.qp)
            v = giudica(c)
            x = _uno(c, v)
            _riga_qvbr(c, v, x, af, ap)
            tabella[(scena_q, pavimento)] = x

    # ── P1 · a scena dura il tetto deve MORDERE
    for pavimento in args.pavimenti:
        x = tabella.get(("-grana", pavimento))
        af, _ = tetto_atteso(pavimento)
        if x is None:
            predicato("P1 il tetto morde a scena dura (pavimento %d)" % pavimento,
                      None, "il giro non e' valido: non si giudica")
            continue
        # ⚠ Il filo che fa fede e' quello RILETTO dal contesto, non l'atteso.
        filo = x["filo"] or af
        e, riga = p_tetto_morde(x, filo, args.tolleranza_bitrate)
        predicato("P1 il tetto MORDE a scena dura (pavimento %d Mbit/s)"
                  % pavimento, e, riga)
    cqp_dura = tabella.get(("-grana", 0))
    if cqp_dura:
        inf("⚠ il paragone: la STESSA scena in CQP %d, cioe' senza nessuno che "
            "dica di no, fa %.3f Mbit/s" % (args.qp, cqp_dura["mbit"]))

    # ── P2 · e la risposta segue la richiesta in modo PREVEDIBILE
    duri = [(p, tabella.get(("-grana", p))) for p in args.pavimenti]
    duri = [(p, x) for p, x in duri if x is not None]
    if len(duri) < 2:
        predicato("P2 due richieste note ⇒ due risposte diverse e prevedibili",
                  None, "meno di due bersagli misurati: non si giudica")
    else:
        righe, monotono, proporzionale = [], True, True
        for i in range(1, len(duri)):
            p0, x0 = duri[i - 1]
            p1, x1 = duri[i]
            atteso = p1 / p0
            avuto = x1["mbit"] / x0["mbit"] if x0["mbit"] > 0 else None
            if avuto is None:
                proporzionale = None
                righe.append("%d→%d: il primo flusso e' a zero, non si divide"
                             % (p0, p1))
                continue
            monotono = monotono and x1["mbit"] > x0["mbit"]
            scarto = abs(avuto - atteso) / atteso
            proporzionale = proporzionale and scarto <= 0.25
            righe.append("%d→%d Mbit/s: chiesto ×%.2f, il flusso fa ×%.2f "
                         "(%.3f → %.3f, scarto %.0f %%)"
                         % (p0, p1, atteso, avuto, x0["mbit"], x1["mbit"],
                            scarto * 100))
        predicato("P2 due richieste note ⇒ due risposte DIVERSE", monotono,
                  " · ".join(righe))
        predicato("P2-bis … e PREVEDIBILI (proporzionali entro il 25 %)",
                  proporzionale, " · ".join(righe))

    # ── P3 · a scena facile il tetto NON deve spendere (⇒ non e' CBR travestito)
    for pavimento in args.pavimenti:
        x = tabella.get(("-piatta", pavimento))
        rif = tabella.get(("-piatta", 0))
        _, ap = tetto_atteso(pavimento)
        if x is None or rif is None:
            predicato("P3 a scena facile NON spende (pavimento %d)" % pavimento,
                      None, "manca il giro o il riferimento CQP: non si giudica")
            continue
        punto = x["punto"] or ap
        quota = x["mbit"] / punto if punto else None
        volte = x["mbit"] / rif["mbit"] if rif["mbit"] > 0 else None
        predicato(
            "P3 a scena FACILE il tetto non spende (pavimento %d Mbit/s)" % pavimento,
            quota is not None and quota < 0.25,
            "il punto di lavoro chiesto e' %.1f Mbit/s e il flusso ne fa **%.3f** "
            "(%.1f %% del punto) · lo stesso in CQP %d fa %.3f ⇒ %s"
            % (punto, x["mbit"], (quota or 0) * 100, args.qp, rif["mbit"],
               ("×%.2f del CQP" % volte) if volte else "[?]"))

    # ── P4 · e il QP sotto QVBR e' il FATTORE DI QUALITA': la scala deve reggere
    tit("2 · IL QP SOTTO QVBR — e' il fattore di qualita', e la scala deve reggere")
    inf("⛔ E' la ragione per cui il tetto usa QVBR e non VBR: `[M]` sotto VBR il")
    inf("   `qp` e' IGNORATO, byte per byte identico con e senza, e tutta la scala")
    inf("   della degradazione della fase 9 diventerebbe un no-op silenzioso.")
    # ⛔⛔ E LA SCENA DI QUESTO PREDICATO E' META' DEL PREDICATO — si sbaglia da
    #     TUTTE E DUE LE PARTI, e questo banco le ha sbagliate tutt'e due:
    #
    #   scena troppo DURA  ⇒ il tetto e' in presa e la qualita' la decide LUI:
    #                        `[M]` 11,14 · 11,31 · 11,19 sui tre QP — la scala
    #                        non morde, e non e' colpa del QP.
    #   scena troppo FACILE ⇒ ⛔ `[M]` 24 agosto 2026, ORE 23:30, IL ROSSO CHE HA
    #                        INSEGNATO QUESTA RIGA: su una tinta piatta i tre QP
    #                        hanno dato **0,0200 · 0,0200 · 0,0200 Mbit/s**, cioe'
    #                        lo stesso identico numero.  Non perche' il QP sia
    #                        ignorato: perche' il flusso era gia' sul **fondo**
    #                        (nessun residuo da togliere), e sotto il fondo non si
    #                        scende.  ⇒ Il banco stava per dichiarare un difetto
    #                        del prodotto che era una sua scelta di scena.
    #
    # ⇒ ⭐ Si prova a scena MEDIA (`testsrc2`) e col pavimento PIU' ALTO, cioe'
    #      dove il tetto NON e' in presa: li' l'unica cosa che puo' muovere i bit
    #      e' il QP, e se non li muove il difetto e' vero.
    pav_qp = args.pavimento_qp or max(args.pavimenti)
    inf("⚠ Scena «%s» e pavimento %d Mbit/s: si sceglie il punto in cui il tetto "
        "NON e' in presa e il flusso NON e' sul fondo — ⛔ negli altri due punti "
        "il QP non muove i bit per ragioni che non sono il QP"
        % (args.scena_qp or "testsrc2", pav_qp))
    scala = []
    for qp in args.scala_qp:
        c = un_giro("qvbr-qp%d" % qp, 1, args.misura, args.fps_bitrate,
                    args.secondi, codec=args.codec, componente=args.componente,
                    profondita=args.profondita, tetto_mbit=pav_qp,
                    scena=args.scena_qp, qp=qp)
        v = giudica(c)
        x = _uno(c, v)
        if x is None:
            ko("QP %d ⇒ giro non valido" % qp)
            for r in v["invalido"][:3]:
                inf(r)
        else:
            inf("QP %2d ⇒ %.4f Mbit/s" % (qp, x["mbit"]))
        scala.append((qp, x))
    buoni = [(q, x) for q, x in scala if x is not None]
    if len(buoni) < 2:
        predicato("P4 sotto QVBR il QP conta", None,
                  "meno di due QP misurati: non si giudica")
    else:
        cala = all(buoni[i][1]["mbit"] < buoni[i - 1][1]["mbit"]
                   for i in range(1, len(buoni)))
        righe_qp = " · ".join("QP %d ⇒ %.4f Mbit/s" % (q, x["mbit"])
                              for q, x in buoni)
        # ⛔ IL TERZO ESITO, e senza di lui questo predicato mente.  Se il flusso
        #    e' sul FONDO (tutti i QP allo stesso millesimo) oppure il tetto e' in
        #    PRESA (tutti dentro l'1 % del filo), «il QP non muove i bit» e' vero
        #    e non dice niente sul QP: la scena non ha lasciato niente da
        #    muovere.  ⇒ `None`, e si dichiara CHE COSA rifare.
        primo, ultimo = buoni[0][1]["mbit"], buoni[-1][1]["mbit"]
        filo_qp = buoni[0][1]["filo"] or tetto_atteso(pav_qp)[0]
        sul_fondo = primo > 0 and abs(ultimo - primo) / primo < 0.01
        in_presa = filo_qp > 0 and primo >= filo_qp * 0.90
        if not cala and (sul_fondo or in_presa):
            predicato(
                "P4 sotto QVBR il QP CONTA (la scala regge)", None,
                "%s — ⛔ NON SI GIUDICA: %s ⇒ la scena non ha lasciato niente che "
                "il QP possa muovere, e «il QP non muove i bit» qui non parla del "
                "QP.  Rifare su una scena di mezzo, col tetto non in presa"
                % (righe_qp,
                   ("il flusso e' sul FONDO (i tre QP entro l'1 %%: %.4f → %.4f)"
                    % (primo, ultimo)) if sul_fondo else
                   ("il TETTO e' in presa (%.3f contro un filo di %.3f)"
                    % (primo, filo_qp))))
        else:
            predicato("P4 sotto QVBR il QP CONTA (la scala regge)", cala, righe_qp)

    # ── P5 · SOTTO CARICO decide qualcuno al posto nostro?
    tit("3 · SOTTO CARICO — 1, 4, 8 codifiche insieme A PARITA' DI RICHIESTA")
    inf("⛔ E' la domanda che il primo giro ha fatto in CQP e CBR su `ffmpeg`")
    inf("   (`[M]` flusso identico byte per byte, 13 su 13) e NON in QVBR, che e'")
    inf("   il modo con una discrezionalita' in piu'.  ⚠ Qui si fa sul PRODOTTO.")
    inf("⛔ E si fa `--senza-scadenza`: ogni flusso fa lo STESSO numero di")
    inf("   fotogrammi, quanto tempo ci voglia.  Due flussi con conteggi diversi")
    inf("   non sono confrontabili, e il confronto direbbe «diversi» quando la")
    inf("   risposta vera e' «non ho misurato la stessa cosa».")
    for pavimento, nome_modo in ((args.pavimenti[0], "QVBR"), (0, "CQP")):
        print("\n  %s— %s, scena dura, %s a %d/s, %d fotogrammi per flusso —%s"
              % (GRASSO, nome_modo, args.misura_carico, args.fps_bitrate,
                 args.fps_bitrate * args.secondi_carico, FINE))
        riferimento, impronte = None, []
        for n in args.carico:
            c = un_giro("carico-%s-%d" % (nome_modo, n), n, args.misura_carico,
                        args.fps_bitrate, args.secondi_carico, codec=args.codec,
                        componente=args.componente, profondita=args.profondita,
                        tetto_mbit=pavimento, scena="-grana",
                        senza_scadenza=True, qp=args.qp)
            v = giudica(c)
            if v["invalido"]:
                ko("N=%d ⇒ GIRO NON VALIDO" % n)
                for r in v["invalido"][:3]:
                    inf(r)
                impronte.append((n, None))
                continue
            fs = c["flussi"]
            terne = [(f.get("impronta"), f["byte_totali"], f["fotogrammi_prodotti"])
                     for f in fs]
            if any(t[0] is None for t in terne):
                att("N=%d ⇒ [?] l'impronta non c'e' (binario vecchio): non giudico"
                    % n)
                impronte.append((n, None))
                continue
            if riferimento is None:
                riferimento = terne[0]
            uguali = sum(1 for t in terne if t == riferimento)
            inf("N=%-2d ⇒ %d/%d flussi identici al giro da solo · %s · %.3f Mbit/s "
                "per flusso · %.1f fot/s per flusso"
                % (n, uguali, len(terne),
                   "impronta %s, %d byte, %d fotogrammi" % riferimento,
                   sum(f["mbit_s"] for f in fs) / len(fs),
                   sum(f["fps_effettivi"] for f in fs) / len(fs)))
            if uguali != len(terne):
                for t in terne:
                    if t != riferimento:
                        inf("   ⛔ diverso: impronta %s, %d byte, %d fotogrammi" % t)
            impronte.append((n, (uguali, len(terne))))
        buone = [(n, r) for n, r in impronte if r is not None]
        if not buone:
            predicato("P5 %s: sotto carico non decide nessuno al posto nostro"
                      % nome_modo, None, "nessun giro valido: non si giudica")
        else:
            tot = sum(r[1] for _, r in buone)
            eq = sum(r[0] for _, r in buone)
            predicato("P5 %s: sotto carico non decide nessuno al posto nostro"
                      % nome_modo, eq == tot,
                      "%d flussi su %d identici (impronta + byte + fotogrammi) al "
                      "giro da solo, su %s"
                      % (eq, tot, ", ".join("N=%d" % n for n, _ in buone)))

    tit("IL CONTO DEI PREDICATI DI QVBR")
    for e in esiti_q:
        if e["esito"] is None:
            att("[?] %-58s %s" % (e["predicato"], e["riga"][:80]))
        else:
            (ok if e["esito"] else ko)("%-58s %s" % (e["predicato"], e["riga"][:80]))
    with open(args.esiti, "a") as f:
        for e in esiti_q:
            f.write(json.dumps(dict(e, giro="bitrate", codec=args.codec,
                                    profondita=args.profondita)) + "\n")
    rossi = [e for e in esiti_q if e["esito"] is False]
    return 1 if rossi else 0


# ═══════════════════════════════════════════════════════════════════════════
# 5 · IL CONTROLLO — ⚠ ffmpeg, e si dichiara: e' un SECONDO metro
# ═══════════════════════════════════════════════════════════════════════════
def controllo(args):
    tit("CONTROLLO DI PARAGONE — ⚠ QUESTO E' `ffmpeg`, NON IL PRODOTTO")
    inf("Serve a una cosa sola: dire se il numero del prodotto e' dello stesso")
    inf("ordine di quel che la scheda sa fare con un altro programma.  ⛔ Se i due")
    inf("divergessero, il numero da spiegare sarebbe il nostro — non si sostituisce.")
    l, a = args.misura.split("x")
    fps_c = args.fps_uno
    # ⚠ `/usr/bin/time` NON c'e' sulla macchina di prova (`[M]` 24 agosto 2026):
    #   il cronometro e' `date +%s.%N` attorno al comando, che e' quel che c'e'.
    cmd = ("cd %s && A=$(date +%%s%%N) && ffmpeg -v error -y -vaapi_device "
           "/dev/dri/renderD128 -f rawvideo -pix_fmt bgr0 -s %s -r %d -stream_loop %d "
           "-i %s/scene/scena-%s.raw -vf 'format=nv12,hwupload' -c:v h264_vaapi "
           "-low_power 1 -rc_mode CQP -qp 26 -bf 0 -f null - && "
           # ⚠ Aritmetica di bash: `bc` NON c'e' sulla macchina (`[M]`), e un
           #   cronometro che stampa una riga vuota e' peggio di nessun cronometro.
           "echo \"MILLISECONDI $(( ($(date +%%s%%N) - A) / 1000000 ))\""
           % (LAV, args.misura, fps_c, args.giri, LAV, args.misura))
    with Lucchetto(secondi=1200):
        rc, out, err = remoto(cmd, tetto=900)
    print(out.strip())
    fotogrammi = args.giri * 6
    m = re.search(r"MILLISECONDI\s+([0-9]+)", out)
    if m:
        t = float(m.group(1)) / 1000.0
        inf("⇒ ffmpeg: %d fotogrammi in %.2f s = %.1f/s = %.0f Mpixel/s "
            "(⚠ SECONDO METRO, un flusso solo, con hwupload dalla memoria)"
            % (fotogrammi, t, fotogrammi / t,
               fotogrammi / t * int(l) * int(a) / 1e6))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 6 · ⛔⛔ `--certifica` — UN BANCO NON E' FINITO FINCHE' NON L'HAI VISTO ROSSO
# ═══════════════════════════════════════════════════════════════════════════
def certifica(args):
    tit("CERTIFICAZIONE — sano → guasto → risanato, e i guasti si FANNO GIRARE")
    misura, fps, sec = args.misura, args.fps_uno, args.secondi
    esiti = []
    # ⛔ Un lucchetto solo per tutta la certificazione: i sette passi sono UN
    #    confronto, e spezzarli su macchine in stati diversi lo scioglierebbe.
    luc = Lucchetto(secondi=9 * sec + 900)
    luc.__enter__()

    def passo(nome, atteso_verde, crudo, cerca=None):
        v = giudica(crudo)
        stampa_verdetto(crudo, v)
        testo = " ".join(v["invalido"]) + " ".join(v["perche"])
        bene = (v["verde"] is True) if atteso_verde else (v["verde"] is False)
        if cerca and bene:
            bene = cerca in testo
            if not bene:
                ko("⛔ il rosso c'e' ma NON nomina «%s»: un rosso che non dice "
                   "quale difetto ha visto manda la caccia dalla parte sbagliata"
                   % cerca)
        (ok if bene else ko)("%s ⇒ %s (atteso %s)"
                             % (nome, "VERDE" if v["verde"] else "ROSSO",
                                "VERDE" if atteso_verde else "ROSSO"))
        esiti.append({"passo": nome, "atteso": atteso_verde, "avuto": v["verde"],
                      "bene": bene})
        return v

    # ── SANO
    tit("0 · SANO — due flussi che devono tenere il ritmo")
    if True:
        sano = un_giro("cert-sano", 2, misura, fps, sec)
    passo("sano", True, sano)

    # ── G1: un flusso che NON PARTE
    tit("G1 · un flusso che NON PARTE (nodo inesistente sul flusso 1)")
    inf("⛔ Atteso: il banco lo dichiara NON PARTITO — non lo conta come «0 fps»,")
    inf("   e non fa la media sugli altri tre come se fossero tutti.")
    if True:
        g = un_giro("cert-g1", 4, misura, fps, sec,
                    nodo_guasto_su="/dev/dri/renderD127")
    passo("G1 flusso che non parte", False, g, cerca="NON E' PARTITO")

    # ── G2: RIPIEGO IN SOFTWARE
    tit("G2 · il codificatore ripiega IN SOFTWARE (`libx264`, strada memoria)")
    inf("⛔ Atteso: ROSSO dichiarato.  ⚠ Un ripiego in CPU che nessuno dichiara")
    inf("   farebbe apparire un soffitto che non e' quello dell'hardware.")
    if True:
        g = un_giro("cert-g2", 1, misura, fps, sec, strada="memoria",
                    componente="libx264")
    passo("G2 ripiego in software", False, g, cerca="RIPIEGO IN SOFTWARE")

    # ── G3: il conteggio del GIRO PRECEDENTE
    tit("G3 · i fotogrammi letti DAL GIRO PRECEDENTE")
    inf("⛔ E' successo davvero in fase 9: tre profili di fila hanno riferito gli")
    inf("   stessi identici numeri.  Qui si innesta apposta: si prende il crudo")
    inf("   SANO e gli si mette il nonce di un giro nuovo.")
    finto = dict(sano)
    finto["nonce"] = "cert-g3-%d" % int(time.time() * 1000)
    finto["parti_a_ns"] = orologio_remoto_ns()
    passo("G3 conteggio del giro precedente", False, finto, cerca="UN ALTRO GIRO")

    # ── G4: «ho chiesto 60 e ne sono arrivati 41»
    tit("G4 · il ritmo chiesto NON arriva (zavorra di %d us per fotogramma)"
        % args.zavorra)
    inf("⛔ Atteso: il banco lo DICE col numero, non arrotonda.")
    if True:
        g = un_giro("cert-g4", 1, misura, fps, sec, zavorra=args.zavorra)
    v = passo("G4 ritmo non mantenuto", False, g, cerca="IL RITMO NON SI TIENE")
    if v.get("sintomo"):
        inf("   la riga onesta: chiesti %d/s, arrivati %.1f/s"
            % (fps, v["sintomo"]["fps_effettivi_minimo"]))

    # ── G5: il metro della GPU che NON LEGGE ⇒ `None`, non zero
    tit("G5 · il metro della GPU non legge (`--metro-cieco`)")
    inf("⛔ Atteso: l'occupazione esce `[?] non letta`, e l'attribuzione della")
    inf("   causa DICE che non puo' ne' affermare ne' escludere la GPU.")
    inf("   ⚠ Uno «0 %» li' vorrebbe dire «la GPU non ha lavorato»: il contrario.")
    if True:
        g = un_giro("cert-g5", 1, misura, fps, sec, zavorra=args.zavorra,
                    metro_cieco=True)
    v = giudica(g)
    stampa_verdetto(g, v)
    m = (v.get("meccanismo") or {})
    bene = m.get("video_uso_pct") is None and v.get("causa") is not None and \
        any("[?]" in n for n in v["causa"].get("note", []))
    (ok if bene else ko)("G5 metro cieco ⇒ occupazione %s"
                         % ("`None` e l'ha dichiarato" if bene
                            else "NON dichiarata come mancante"))
    esiti.append({"passo": "G5 metro cieco", "atteso": False, "avuto": v["verde"],
                  "bene": bene})

    # ── G6: UN GIRO HEVC CONTATO COME H.264
    tit("G6 · un giro **HEVC** contato come **H.264** (e il contrario)")
    inf("⛔ E' il difetto della fase 9 §13.5: il banco negoziava HEVC e il")
    inf("   prodotto mandava H.264 — `[M]` 21,18 contro 7,92 Mbit/s sulla stessa")
    inf("   scena, e mezza giornata di numeri buttati.  ⚠ E il rapporto fra i due")
    inf("   NON e' una costante (0,36× · 0,76× · 1,7×): non si corregge dopo.")
    inf("⭐ L'ANCORA: il codec si legge DAL FLUSSO PRODOTTO — la stringa per il")
    inf("   decodificatore, composta sull'SPS — non dal comando dato.")
    g = un_giro("cert-g6", 1, misura, fps, sec, codec="h264",
                componente="hevc_vaapi", codec_davvero="hevc")
    passo("G6 HEVC contato come H.264", False, g, cerca="e' il flusso a dire il codec")
    tit("G6-bis · e il contrario: **H.264** dichiarato **HEVC**")
    g = un_giro("cert-g6b", 1, misura, fps, sec, codec="hevc",
                componente="h264_vaapi", codec_davvero="h264")
    passo("G6-bis H.264 contato come HEVC", False, g,
          cerca="e' il flusso a dire il codec")

    # ── G7: IL MODO CHIESTO E NON OTTENUTO
    tit("G7 · il modo del bitrate CHIESTO e NON ottenuto")
    inf("⛔ Il banco deve accorgersene DAL FLUSSO e dal contesto riletto, non")
    inf("   dalla rilettura dentro VA-API — che su questo driver **non dice")
    inf("   niente**: `vaQueryConfigAttributes` rende la maschera delle capacita',")
    inf("   identica qualunque cosa si sia chiesta (`fasi/10-…md` §6.6).")
    inf("⚠ Il guasto si innesta cosi': si fa girare il flusso col tetto SPENTO")
    inf("  (⇒ CQP) e lo si dichiara acceso (⇒ il banco pretende QVBR).")
    g = un_giro("cert-g7", 1, misura, fps, sec, tetto_mbit=20, tetto_davvero=0)
    passo("G7 modo chiesto e non ottenuto", False, g, cerca="R31")

    # ── G8: IL BERSAGLIO DI BITRATE MANCATO, COL NUMERO
    tit("G8 · il bersaglio di bitrate MANCATO ⇒ rosso **col numero**")
    inf("⛔ Non arrotondato: «ha sforato» non dice di quanto, e un banco che non")
    inf("   dice il numero manda la caccia dalla parte sbagliata.")
    inf("⚠ Il bersaglio si fa mancare per costruzione: si giudica un flusso CQP")
    inf("  a scena dura contro il filo di un tetto da 1 Mbit/s (filo 0,8), che")
    inf("  nessun flusso vero puo' rispettare.")
    g8 = un_giro("cert-g8", 1, misura, fps, sec, scena="-grana", tetto_mbit=0)
    v8 = giudica(g8)
    x8 = _uno(g8, v8)
    if x8 is None:
        ko("⛔ G8: il giro di appoggio non e' valido, il guasto NON e' stato "
           "innestato — e un guasto non innestato NON conta come verde")
        for r in v8["invalido"][:3]:
            inf(r)
        esiti.append({"passo": "G8 bersaglio mancato", "atteso": False,
                      "avuto": None, "bene": False})
    else:
        # ⛔ Si innesta sul PREDICATO VERO (`p_tetto_morde`), non su una copia:
        #    un guasto innestato su una copia certifica la copia.
        filo_finto = 0.8
        sano_e, sano_riga = p_tetto_morde(x8, max(x8["mbit"] * 2.0, 1.0),
                                          args.tolleranza_bitrate)
        guasto_e, guasto_riga = p_tetto_morde(x8, filo_finto,
                                              args.tolleranza_bitrate)
        cieco_e, cieco_riga = p_tetto_morde(None, filo_finto,
                                            args.tolleranza_bitrate)
        inf("sano   (filo largo)   ⇒ %s — %s" % (sano_e, sano_riga))
        inf("guasto (filo 0,8)     ⇒ %s — %s" % (guasto_e, guasto_riga))
        inf("cieco  (nessun byte)  ⇒ %s — %s" % (cieco_e, cieco_riga))
        # ⛔ Tre pretese, e la terza e' quella che di solito manca: il rosso deve
        #    portare il numero VERO a tre decimali, non arrotondato.
        bene = (sano_e is True and guasto_e is False and cieco_e is None
                and ("%.3f" % x8["mbit"]) in guasto_riga)
        (ok if bene else ko)("G8 bersaglio mancato ⇒ rosso col numero: %s"
                             % guasto_riga)
        if guasto_e is not False:
            inf("⚠ il guasto NON e' stato innestato: la scena dura ha fatto %.3f "
                "Mbit/s, che sta sotto il filo finto — e un guasto non innestato "
                "non conta" % x8["mbit"])
        esiti.append({"passo": "G8 bersaglio mancato (col numero)",
                      "atteso": False, "avuto": False, "bene": bene})

    # ── RISANATO
    tit("R · RISANATO — si toglie ogni guasto e si rifa' il giro sano")
    if True:
        risanato = un_giro("cert-risanato", 2, misura, fps, sec)
    passo("risanato", True, risanato)
    # ⛔ E il risanato NON deve portare gli stessi identici numeri del sano: due
    #    giri identici al fotogramma sono il sintomo del difetto G3 vero.
    a = sano["flussi"][0]["fotogrammi_prodotti"] if sano.get("flussi") else -1
    b = risanato["flussi"][0]["fotogrammi_prodotti"] if risanato.get("flussi") else -2
    ta = sano["flussi"][0]["durata_s"] if sano.get("flussi") else 0
    tb = risanato["flussi"][0]["durata_s"] if risanato.get("flussi") else 0
    if ta == tb:
        ko("⛔ sano e risanato hanno la STESSA durata al decimo di microsecondo: "
           "sospetto di lettura dal giro precedente")
    else:
        ok("sano e risanato sono due giri DIVERSI (durate %.4f e %.4f s)" % (ta, tb))

    luc.__exit__()
    tit("IL CONTO")
    buoni = sum(1 for e in esiti if e["bene"])
    for e in esiti:
        (ok if e["bene"] else ko)("%-36s atteso %s, avuto %s"
                                  % (e["passo"], "VERDE" if e["atteso"] else "ROSSO",
                                     "VERDE" if e["avuto"] else "ROSSO"))
    print()
    (ok if buoni == len(esiti) else ko)(
        "%d/%d passi come attesi" % (buoni, len(esiti)))
    with open(args.esiti, "a") as f:
        for e in esiti:
            f.write(json.dumps(dict(e, giro="certifica")) + "\n")
    return 0 if buoni == len(esiti) else 1


# ═══════════════════════════════════════════════════════════════════════════
def main():
    a = argparse.ArgumentParser(description="il saturatore del codificatore")
    a.add_argument("comando", choices=["porta", "scene", "tara", "rampa",
                                       "controllo", "certifica", "tutto",
                                       "bitrate", "pulisci"])
    a.add_argument("--misure", nargs="+", default=["854x480", "1920x1080", "3840x2160"])
    a.add_argument("--fps", nargs="+", default=["25", "30", "60"])
    a.add_argument("--misura", default="1920x1080")
    a.add_argument("--durate", nargs="+", type=int, default=[15, 60])
    a.add_argument("--scala", nargs="+", type=int,
                   default=[1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32])
    a.add_argument("--secondi", type=int, default=15)
    a.add_argument("--strada", default="scheda", choices=["scheda", "memoria"])
    a.add_argument("--codec", default="h264", choices=["h264", "hevc"])
    # ⛔ 8 e' quel che il PRODOTTO negozia (`rcp.c` offre `8,10`, §4.3 sceglie
    #    nell'ordine del client, e `pagina.html` dichiara `8,10`) ⇒ HEVC **Main**.
    #    Main10 si chiede a mano, e resta una colonna sua.
    a.add_argument("--profondita", type=int, default=8, choices=[8, 10])
    # ⛔ 0 = tetto spento = **CQP**, ed e' il predefinito del prodotto (I6).
    #    Diverso da zero = il PAVIMENTO in Mbit/s ⇒ il codificatore chiede QVBR.
    a.add_argument("--tetto-banda-mbit", type=int, default=0)
    a.add_argument("--componente", default=None)
    # ⚠ `--fps-uno` e' il ritmo dei comandi che accendono UN flusso solo
    #   (`controllo`, `certifica`): tenerlo separato dalla terna della rampa
    #   evita di leggere «il primo della lista» e chiamarlo una scelta.
    a.add_argument("--fps-uno", type=int, default=60)
    a.add_argument("--zavorra", type=int, default=20000)
    a.add_argument("--giri", type=int, default=100)
    a.add_argument("--tetto-lucchetto", type=int, default=5400)
    # ⚠ Il terreno vuole una porta e un utente anche a chi non apre porte: questo
    #   banco non parla RCP, e li dichiara per quel che sono.
    a.add_argument("--porta-finta", type=int, default=7902)
    a.add_argument("--utente", default="nicfio")
    a.add_argument("--porte-ammesse", nargs="*",
                   default=["8010", "8020", "8030", "8100"])
    a.add_argument("--memoria-misure", nargs="+", default=["854x480", "1920x1080"])
    a.add_argument("--memoria-fps", nargs="+", default=["25", "30"])
    a.add_argument("--esiti", default=os.path.join(QUI, "10-b88-esiti.jsonl"))
    a.add_argument("--nodo", default="/dev/dri/renderD128")
    # ── il comando `bitrate` ────────────────────────────────────────────────
    # ⛔ 20 e' il pavimento del prodotto (`DECISIONI.md` §3.1-bis) ⇒ filo 16,
    #    punto 12.  Gli altri due servono a P2: due richieste note devono dare
    #    due risposte diverse e PREVEDIBILI, e con un bersaglio solo non si sa
    #    se il flusso segue la richiesta o ci e' finito per caso.
    a.add_argument("--pavimenti", nargs="+", type=int, default=[10, 20, 40])
    a.add_argument("--fps-bitrate", type=int, default=30)
    a.add_argument("--qp", type=int, default=26)
    # ⚠ La scala della degradazione della fase 9, i tre gradini misurati sul
    #   portatile: 26 → 0,218 · 35 → 0,125 · 44 → 0,076 Mbit/s.
    a.add_argument("--scala-qp", nargs="+", type=int, default=[26, 35, 44])
    # ⛔ La scena e il pavimento del predicato P4: si prova dove il tetto NON e'
    #    in presa e il flusso NON e' sul fondo — vedi il riquadro in `bitrate()`.
    #    `""` = `testsrc2`, la scena di mezzo.  `None` = il pavimento piu' alto.
    a.add_argument("--scena-qp", default="")
    a.add_argument("--pavimento-qp", type=int, default=None)
    a.add_argument("--tolleranza-bitrate", type=float, default=0.15)
    a.add_argument("--carico", nargs="+", type=int, default=[1, 4, 8])
    a.add_argument("--misura-carico", default="1280x720")
    a.add_argument("--secondi-carico", type=int, default=20)
    # ⚠ Le varianti di scena che `scene` produce.  ⛔ `bitrate` le vuole tutte:
    #   un tetto si giudica su una scena facile E su una dura, e i due verdetti
    #   sono opposti.
    a.add_argument("--scene", nargs="+", default=["", "-grana", "-piatta"])
    args = a.parse_args()
    if args.componente is None:
        args.componente = "h264_vaapi" if args.codec == "h264" else "hevc_vaapi"
    if args.comando == "porta":
        return porta()
    if args.comando == "scene":
        # ⚠ Le tre taglie della rampa nella sola variante `testsrc2`, e le taglie
        #   del bitrate in tutte: la grana a 4K pesa 100 MB per fotogramma-set e
        #   li' non serve a niente.
        r = scene(args.misure)
        if r:
            return r
        extra = sorted({args.misura, args.misura_carico} - set(args.misure))
        quali = [q for q in args.scene if q]
        if extra:
            r = scene(extra, quali=[""] + quali)
            if r:
                return r
        return scene([args.misura, args.misura_carico], quali=quali)
    if args.comando == "tara":
        return tara(args)
    if args.comando == "rampa":
        return rampa(args)
    if args.comando == "tutto":
        return tutto(args)
    if args.comando == "controllo":
        return controllo(args)
    if args.comando == "certifica":
        return certifica(args)
    if args.comando == "bitrate":
        # ⛔ Da qui escono numeri che si riferiscono ⇒ il lucchetto e' mio, e il
        #    terreno si guarda PRIMA.
        with Lucchetto(secondi=args.tetto_lucchetto):
            terreno(args)
            return bitrate(args)
    if args.comando == "pulisci":
        rc, out, _ = remoto("pkill -f 10-b88-flusso; pkill -f 10-b88-sonda; sleep 1; "
                            "pgrep -a 10-b88 || echo 'nessun processo del banco vivo'")
        print(out)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
