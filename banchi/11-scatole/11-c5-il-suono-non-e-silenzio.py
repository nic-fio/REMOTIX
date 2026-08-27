#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c5 — ⭐⭐ «IL SUONO C'E' E NON E' SILENZIO»
===========================================================================

    python3 11-c5-il-suono-non-e-silenzio.py --porta 8512
    python3 11-c5-il-suono-non-e-silenzio.py --porta 8512 --senza-sorgente
    python3 11-c5-il-suono-non-e-silenzio.py --certifica

E' la riga **C5** di `fasi/11-la-rete-di-sicurezza.md` §4.1:

    che cosa deve essere vero : il suono c'e' e non e' silenzio
    da dove parte             : ⛔ una sessione NUOVA (un inquilino mai usato)
    che cosa guarda           : ⭐ i BYTE che arrivano al cliente, e che non
                                siano silenzio
    come so che sa dare rosso : si toglie la sorgente ⇒ rosso

---------------------------------------------------------------------------
⭐⭐ PERCHE' QUESTA MAGLIA VEDE QUALCOSA MENTRE LE ALTRE SONO CIECHE
---------------------------------------------------------------------------

`fasi/11…` §6 e §7-bis.13: `[M]` **dieci sessioni GNOME nuove su dieci nascono
senza monitor**, ⇒ C2, C3, C4, C6 e la meta' B di C8 **non hanno niente da
guardare**, perche' guardano un pixel attraverso il prodotto.

⭐ C5 giudica **byte**, non pixel — e i byte del suono non passano dal
  compositore.  ⛔ **Ma non e' stato dato per scontato: e' stato misurato.**

  `[M]` 26 agosto 2026, scatola `rete11-kde`, porta 8512, inquilino `c5u1`:
  il registro del prodotto dice per quella stessa sessione

      figlio [c5u1] ⛔ nessun monitor virtuale da catturare … monitor «»
                    (0 prima, 0 dopo), 0x0

  cioe' **la sessione era CIECA** — ⇒ e nello stesso identico giro il cliente
  ha ricevuto **13 753 blocchi PCM, 13 202 880 byte, purezza 1,0000**.

  ⭐ E c'e' un secondo fatto misurato che rende C5 **piu' rapida** di tutte le
    altre: il sink «remotix» compare nel PipeWire dell'inquilino dopo **3
    secondi**, mentre il palco grafico ne vuole ~13 quando ci riesce.

  ⇒ **C5 e' oggi l'unica maglia che attraversa il prodotto da cima a fondo e
    ha ancora qualcosa da giudicare.**

---------------------------------------------------------------------------
⛔⛔ CHE COS'E' «SILENZIO», CON UN NUMERO — e il numero e' TARATO
---------------------------------------------------------------------------

⛔ *«Sono arrivati dei byte»* **non e' una prova che ci sia del suono**: un
   flusso di zeri e' byte che arrivano ed e' silenzio perfetto.  ⇒ Serve una
   misura di **energia**, e una **soglia dichiarata**.

**Il metro**: si chiede al cliente il codec **PCM** (`--audio-codec pcm`, che
§4.3 del protocollo impone come «base sempre disponibile»), ⇒ il carico del
datagram e' **s16 little-endian, 48 000 Hz, 2 canali, 240 fotogrammi = 480
campioni = 960 byte per blocco, 5 ms** (`src/audio.h`: `AUDIO_BLOCCO_PCM`,
`AUDIO_FREQUENZA`, `AUDIO_CANALI`).  ⭐ Su quei campioni si calcola l'**RMS**,
in unita' di fondo scala 32767.

⚠ E si chiede PCM apposta: con Opus il carico e' compresso e per misurare
  l'energia servirebbe un decodificatore dentro il banco.  ⛔ Un banco che si
  porta dentro un decodificatore e' un banco che puo' sbagliare da solo.

**I tre numeri del verdetto**, e ciascuno con la sua ragione:

    SOGLIA_RMS   = 328 su 32767  ⇒ 1,0 % del fondo scala, cioe' −40 dBFS
    MIN_BLOCCHI  = 200           ⇒ 1 secondo di suono (5 ms a blocco)
    MIN_FRAZIONE = 0,50          ⇒ meta' dei blocchi dev'essere sopra soglia

⭐⭐ **LA TARATURA — `[M]` 26 agosto 2026, `rete11-kde`, porta 8512, SEI
    sessioni vere.**  ⛔ La soglia non e' inventata: e' stata **cercata**
    facendo girare la maglia vera su ampiezze diverse, finche' si e' visto dove
    passa il confine.

  | la sorgente (onda a 440 Hz)  | RMS misurato | in dBFS | volte la soglia | verdetto |
  |------------------------------|--------------|---------|-----------------|----------|
  | ampiezza **1,0** (predefinita) | **23 169,3** |  −3,0  | **70,6 ×**  | ⭐ VERDE |
  | ampiezza 0,5                 |   11 582,7   |  −9,0   | 35,3 ×      | VERDE |
  | ampiezza **0,02**            |      463,1   | −37,0   | **1,41 ×**  | ⭐ VERDE — il punto vero piu' vicino da sopra |
  | ampiezza **0,01**            |      231,2   | −43,0   | **0,71 ×**  | ⛔ ROSSO — il punto vero piu' vicino da sotto |
  | ampiezza 0,001               |       22,6   | −63,2   | 0,07 ×      | ⛔ ROSSO |
  | ⛔ **nessuna sorgente**       |      —       |   —     |      —      | ⛔ ROSSO: **zero blocchi**, non arriva NIENTE |

⭐ **Il confine e' stato ATTRAVERSATO in tutt'e due i versi su dati veri**, non
  dedotto: fra 0,01 e 0,02 di ampiezza la maglia cambia verdetto, e la soglia
  cade dove il documento dice che cade (ampiezza 0,0142 = 1,42 % del fondo
  scala).  ⇒ Non e' una soglia che «non ha mai dato rosso in vita sua»
  (`LEZIONI.md` §1.47).

⚠ **E il percorso e' TRASPARENTE**, misurato e non supposto: RMS misurato /
  RMS atteso = 23 169,3 / 23 170 = **1,0000**.  ⇒ Quel che `pw-play` mette nel
  sink arriva al cliente **con lo stesso livello**, e il conto del prodotto lo
  conferma dall'altro capo del filo (`PICCO 32767 su 32767`).

⛔⛔ **E QUI IL BANCO HA GIA' MENTITO UNA VOLTA, prima di essere scritto.**
  La sonda esplorativa faceva l'onda con `ffmpeg -f lavfi -i sine=…` e misurava
  **RMS 2 047,5, PICCO 2 896** — cioe' *«il percorso attenua di 21 dB»*.  ⛔ Era
  falso: attenuava **il generatore**, non il percorso.  ⇒ Una soglia tarata su
  quel numero sarebbe stata **dieci volte troppo bassa**, e nessuno se ne
  sarebbe accorto finche' non avesse smesso di dare rosso.
  ⭐ **E' la ragione per cui l'onda la scrive questo file**: un'ampiezza che
    dipende dalla semantica del generatore di qualcun altro e' una soglia che
    si sposta senza dirlo.

⇒ ⭐ E per la stessa ragione la maglia **stampa sempre il margine**: il giorno
  in cui quel percorso smettesse di essere trasparente, si vedrebbe **prima**
  che diventi un rosso falso, invece che dopo.

⛔ E QUEL CHE LA SOGLIA **NON** E': non e' un giudizio su quanto sia forte il
   suono dell'utente.  E' la riga che separa *«e' passato il tono che ho messo
   io»* da *«arriva un flusso di quasi-zeri»*.  ⚠ La qualita' fine del suono
   e' giudizio dell'utente (I8), e §6 la mette **fuori** dalla rete.

---------------------------------------------------------------------------
⭐ DA DOVE VIENE IL SUONO — e non c'e' niente da aggiungere alla ricetta
---------------------------------------------------------------------------

Il prodotto **si fa il suo sink da solo**: `src/suono.c` crea nel PipeWire
dell'inquilino un `support.null-audio-sink` chiamato **`remotix`** e ne cattura
il monitor.  ⇒ ⭐ Per fare del suono basta **suonare dentro quel sink**.

`[M]` 26 agosto 2026, dentro `rete11-kde`, gia' presenti e verificati **prima**
di scrivere questa maglia (E1: non si ispeziona la ricetta, si prova a fare la
cosa):

    /usr/bin/pw-play   pipewire-bin 1.4.2-1     ⭐ suona il tono
    /usr/bin/pw-cli    pipewire-bin 1.4.2-1     ⭐ dice se il sink c'e'
    /usr/sbin/runuser  util-linux               diventa l'inquilino

⛔ **Non serve aggiungere niente alle quattro ricette**, e non e' un dettaglio:
   una maglia che chiede un pacchetto nuovo obbliga a ricostruire le quattro
   scatole, cioe' a rimettere in discussione C11 (l'allineamento).

⚠ E l'onda **non** la fa `ffmpeg`, che pure c'e': la scrive questa maglia, in
  Python, campione per campione.  ⭐ Cosi' **l'ampiezza e' un numero di questo
  file** e non la semantica di un filtro altrui — che e' esattamente quel che
  serve a una soglia tarata.

---------------------------------------------------------------------------
⛔⛔ TRE ESITI DISTINTI, E NON DUE — §4.5, e il difetto di `LEZIONI.md` §1.49
---------------------------------------------------------------------------

⭐ *«Non e' arrivato NIENTE»* e *«non sono riuscito ad aprire la sessione»*
  hanno lo stesso sintomo — un file di blocchi vuoto — **e sono due cose
  opposte**.  ⇒ La maglia le separa **prima** di guardare i blocchi:

  · il cliente non e' stato AMMESSO           ⇒ **3**, non ho potuto guardare
  · il PipeWire dell'inquilino non risponde   ⇒ **3**, il terreno non parla
  · PipeWire risponde e il sink «remotix» NON c'e'
                                              ⇒ ⛔ **1**, ROSSO: il prodotto
                                                 non ha aperto la via del suono
  · il sink c'e', la sorgente suona, e non arriva un blocco
                                              ⇒ ⛔ **1**, ROSSO: il suono non c'e'
  · arrivano blocchi ma l'energia e' sotto soglia
                                              ⇒ ⛔ **1**, ROSSO: e' silenzio
  · il codec negoziato non e' PCM             ⇒ **3**: non so misurare l'energia

---------------------------------------------------------------------------
⛔ IL GUASTO INNESTATO — `--senza-sorgente`, e va fatto girare
---------------------------------------------------------------------------

`--senza-sorgente` fa tutto **tranne** suonare il tono.  ⇒ La sessione consegna
silenzio digitale, e la cura di `src/audio.c` (accesa dal 24 agosto 2026) **non
spedisce i blocchi tutti a zero**: ⇒ al cliente non arriva niente.

⭐ Con il guasto innestato **l'esito si legge al contrario**: qui il verde e' un
  rosso.  Se C5 dicesse verde senza sorgente, ⛔ non starebbe guardando il suono
  — starebbe guardando qualcos'altro, e non ci si potrebbe fidare di lei.

⚠ `[M]` E' stato fatto girare, non immaginato: i numeri stanno nel rapporto
  della maglia (§7-bis del documento di fase).

---------------------------------------------------------------------------
⛔ QUEL CHE C5 **NON** GUARDA — dichiarato, o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · ⛔ **non guarda un pixel.**  Una sessione cieca la fa passare VERDE, ed e'
    giusto cosi': quella e' C1.  ⚠ ⇒ C5 verde **non vuol dire «la sessione
    sta bene»**, vuol dire «la via del suono e' aperta».
  · ⛔ **non giudica la qualita' del suono**: ne' fedelta', ne' distorsione, ne'
    sincronia con il video (I8, giudizio dell'utente; §6 della fase).
  · ⛔ **non giudica il ritardo** ne' il jitter: il cliente li sa contare, questa
    maglia non li legge.
  · ⛔ **non guarda Opus**, che e' il codec che il browser vero negozia: qui si
    chiede PCM per poter misurare l'energia senza un decodificatore.
    ⚠ ⇒ Un guasto che colpisse **solo** il ramo Opus, C5 non lo vedrebbe.
  · ⛔ **non e' una prova di intermittenza**: apre **una** sessione, non dieci.
    Se la nascita del sink diventasse saltuaria, ⇒ e' C1 che conta i giri.
  · ⛔ **non prova che il suono sia quello GIUSTO**: prova che c'e' energia, non
    che sia l'onda che abbiamo suonato noi.  ⚠ Un rumore qualunque passerebbe.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: il suono arriva e non e' silenzio
  1  ⛔ ho guardato e NON regge ⇒ rosso
  3  ⛔ non ho potuto guardare — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import importlib.util
import base64
import json
import math
import os
import struct
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — ⛔ IL PREDICATO SI IMPORTA, NON SI
#     RISCRIVE.  La casa e' `11-c1-nasce-e-si-vede.py`, e ce n'e' UNA (§1.47).
#
# ⛔ Fino al 27 agosto 2026 qui c'era `"AMMESSO" in uscita`, ⭐ e non poteva
#    dire di no: `[R]` `01-b3-cliente.py` stampa quella parola anche nei **due
#    messaggi di rifiuto** — «CONGEDO invece di AMMESSO: motivo …» (:1315) e
#    «atteso AMMESSO, arrivato …» (:1322) — e li stampa sullo **stdout**, che
#    e' esattamente dove si guardava.  ⇒ Un predicato che non puo' fallire,
#    `LEZIONI.md` §1.44: la maglia si credeva entrata **anche quando era stata
#    respinta**, e poi giudicava il buio che ne seguiva come un difetto del
#    prodotto.
# ⚠ Era in CINQUE maglie con la stessa riga.  ⇒ Curarla cinque volte sarebbe
#   stato creare cinque posti da cui divergere di nuovo (§1.47): sta in C1, e
#   le altre quattro la importano da li'.
# ⛔ E se non si riesce a importarla si esce **3** e lo si dice, ⇒ ⛔ non si
#   ripiega in silenzio sul predicato povero — che e' il difetto stesso.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente.

    ⚠ Si cerca accanto a me (dentro la scatola tutto sta in `/opt/remotix`) e
      un piano piu' su, come fanno C2, C3 e C6 coi loro giudici importati.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ Si VERIFICA che ci sia quel che serve, invece di fidarsi del nome
        #    del file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ E da C1 viene anche la garanzia dei gruppi della scheda: stessa
        #    ragione, stesso posto solo (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   viene il predicato «il cliente e' stato AMMESSO?» — che sta")
        print("   in un posto solo apposta (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama esce **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ e anche questo sta in un posto solo (C1).

    Torna `(esito, perche)`: `0` = l'inquilino vede e si puo' misurare,
    `3` = ⛔ NON si misura.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica.  ⭐ `[M]` senza i gruppi
       dei nodi `/dev/dri` la sessione nasce CIECA — 0 su 4, mai in 90 s, zero
       fotogrammi — e questa maglia avrebbe misurato il buio chiamandolo
       difetto del prodotto (`fasi/10-…` §7.4).
    ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid dai NODI e
       rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ IL METRO, DICHIARATO QUI E STAMPATO A OGNI GIRO.  Un verdetto senza il suo
#    metro e' un'opinione (§4.2 della fase).
# ---------------------------------------------------------------------------
FONDO_SCALA = 32767.0

# 1,0 % del fondo scala = −40 dBFS.  ⭐ TARATA su sei sessioni vere (la tabella
# in testa): il tono predefinito ci sta **70,6 volte sopra**, e il confine e'
# stato attraversato in tutt'e due i versi fra ampiezza 0,01 (rosso) e 0,02
# (verde).  ⛔ Non e' un numero che non ha mai dato rosso in vita sua.
SOGLIA_RMS = 328.0

# 200 blocchi da 5 ms = 1 secondo di suono.  ⛔ Un blocco solo non e' un flusso:
# potrebbe essere uno schiocco in mezzo al nulla.
MIN_BLOCCHI = 200

# ⛔ Meta' dei blocchi dev'essere sopra soglia.  Senza questo, un tono forte per
#    un decimo del tempo e zeri per il resto avrebbe l'RMS globale a posto.
#
# ⚠⚠ E VA DETTO CHE OGGI QUESTO CRITERIO E' QUASI CIECO SUL PERCORSO VERO, come
#    C5 dice le altre cose che non guarda: `src/audio.c` (`audio_taci_silenzio`,
#    accesa in modo predefinito) **non spedisce i blocchi muti**, quindi i buchi
#    non arrivano al cliente e non entrano nel denominatore.  ⇒ Sui dati veri
#    `frazione` e' ~1,0 **per costruzione**, e perche' `A TRATTI` scatti
#    servirebbe un flusso quasi-silenzioso ma non esattamente nullo — che il
#    criterio `SILENZIO` prende prima.
#    ⇒ Non e' un rosso falso e non e' un verde falso: e' un criterio
#      certificato su casi sintetici che il prodotto struttura per non produrre
#      mai.  ⭐ Resta a difendere il giorno in cui quella cura si spegnesse (un
#      server acceso con `--niente-audio-silenzio`), e resta a difendere la
#      TESTA dell'onda — i secondi fra l'ammissione e la comparsa del sink, che
#      nessun margine copre (vedi `--resta` piu' sotto).
MIN_FRAZIONE = 0.50

# Il formato del carico PCM — `src/audio.h`.
PCM_CODEC = 2
PCM_FREQUENZA = 48000
PCM_CANALI = 2
PCM_FOTOGRAMMI = 240          # 5 ms
PCM_BYTE_BLOCCO = PCM_FOTOGRAMMI * PCM_CANALI * 2   # = 960

# Il sink che il prodotto si crea da solo — `src/suono.c`, `NOME_SINK`.
NOME_SINK = "remotix"

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL TETTO DELLA NASCITA — ed e' una MISURA, non un numero tondo (§1.45).
#
# ⛔ Il sink «remotix» non puo' comparire prima che la SESSIONE sia nata: se ne
#    occupa `src/suono.c` dentro la sessione.  ⇒ Il tetto di C5 e' il tetto
#    della nascita, ed e' lo stesso numero di C1 (`TETTO_NASCITA` la').
#
# `[M]` 27 agosto 2026, scatola GNOME **curata**, tre sessioni nuove: il
# `formato negoziato` — l'istante in cui il monitor nasce — arriva in
#
#     1,105 s        0,998 s        0,957 s        ⇒ massimo **1,105 s**
#
# e il sink si vede in `[M]` **3 s** (misura del 26 ago, scatole sane).
#
# ⛔⛔ E QUESTA RIGA HA GIA' PORTATO UN NUMERO SBAGLIATO, PER MEZZA GIORNATA:
#     **152 s**, tarati su un ritardo di ~97 s che **non era del prodotto**.
#     `[M]` Era un guasto della SCATOLA: il §6 della ricetta spostava il gruppo
#     `polkitd` da 991 a 1991 per dare 991 a `render`, e `groupmod -g` non si
#     porta dietro i file ⇒ `polkitd` non leggeva piu'
#     `/etc/polkit-1/rules.d`, moriva, e `gnome-shell` incassava quattro
#     scadenze da 25 s.  ⇒ ⚠ Un tetto di 152 s su un fenomeno di 1,1 s e'
#     **cento volte** il fenomeno: ⛔ un tetto cosi' non protegge, **nasconde**
#     — scaduto non ha piu' niente da dire, e nel frattempo ha pagato
#     centocinquanta secondi per ogni giro che va storto.
#   ⭐ La lezione, e vale piu' del numero: **prima di tarare un tetto su una
#     misura, si guarda se quella misura e' del prodotto o del banco.**
#
# ⭐ IL MARGINE, E DA DOVE VIENE — e non e' il margine della dispersione di
#   oggi (0,957-1,105 s, il 15 %), che sarebbe un margine misurato su una
#   macchina sola e a riposo:
#
#     · il fenomeno sano, oggi                      `[M]`  1,105 s
#     · il sink, sulle scatole sane                 `[M]`  3 s
#     · ⚠ la nascita piu' lenta MAI misurata in
#       questo progetto (26 ago, scatola carica)    `[M]` ~13 s
#     · il margine dichiarato su QUELLA             **× 2**
#                                                   ⇒ **26 s**
#
#   ⇒ 26 s sono **8,7 volte** il sink misurato e **due volte** il peggiore mai
#     visto.  ⚠ Il margine sta sul peggiore apposta: la scatola puo' essere
#     carica, e la macchina vera ha una **Intel UHD 730 integrata**.
TETTO_NASCITA = 26.0

# ⭐ E la FINESTRA DI MISURA vera e propria, cioe' quanto suono si vuole avere
#   in mano dopo che il sink si e' visto.  ⚠ 25 s = ~5 000 blocchi da 5 ms:
#   e' la popolazione su cui e' tarata la soglia (`[M]` ~4 878 blocchi sulle
#   scatole sane) e **25 volte** `MIN_BLOCCHI`.
FINESTRA_MISURA = 25.0


# ---------------------------------------------------------------------------
# ⭐⭐ IL GIUDICE — e vive da solo, senza rete, senza scatola, senza sessione.
#
# ⛔ E' la parte che `--certifica` mette alla prova.  Prende una lista di
#    blocchi `(codec, carico)` e torna un verdetto:
#      True  = c'e' suono e non e' silenzio
#      False = ⛔ rosso
#      None  = ⛔ non lo so — e ⛔ `None` NON e' zero (§4.5)
# ---------------------------------------------------------------------------
def giudica(blocchi, soglia=SOGLIA_RMS, min_blocchi=MIN_BLOCCHI,
            min_frazione=MIN_FRAZIONE):
    m = {"blocchi": None, "byte": 0, "codec": None, "campioni": 0,
         "rms": None, "picco": None, "sopra": None, "frazione": None,
         "motivo": None}

    if blocchi is None:
        m["motivo"] = "non sono riuscito a leggere i blocchi"
        return None, m

    m["blocchi"] = len(blocchi)
    m["byte"] = sum(len(c) for _, c in blocchi)

    # ⛔ PRIMA di ogni altra cosa: «non e' arrivato niente» e' un ROSSO, non un
    #    «non lo so».  Chi arriva qui ha gia' avuto la sessione e il sink: se
    #    con la sorgente accesa non arriva un blocco, il suono NON C'E'.
    if not blocchi:
        m["motivo"] = "NIENTE: non e' arrivato un solo blocco d'audio"
        return False, m

    codec = set(c for c, _ in blocchi)
    if len(codec) != 1:
        m["codec"] = sorted(codec)
        m["motivo"] = ("il codec CAMBIA a meta' sessione (%s): non so su che "
                       "formato misurare l'energia" % sorted(codec))
        return None, m
    m["codec"] = codec.pop()
    if m["codec"] != PCM_CODEC:
        m["motivo"] = ("il codec negoziato e' %d, non PCM (%d): l'energia si "
                       "misurerebbe solo decodificando, e questo banco non "
                       "decodifica" % (m["codec"], PCM_CODEC))
        return None, m

    # ⛔ Un carico di lunghezza dispari non e' s16: non si tira a indovinare.
    if any(len(c) % 2 for _, c in blocchi):
        m["motivo"] = "almeno un carico ha lunghezza DISPARI: non e' s16"
        return None, m

    somma = 0
    campioni = 0
    picco = 0
    sopra = 0
    for _, carico in blocchi:
        n = len(carico) // 2
        if n == 0:
            continue
        v = struct.unpack("<%dh" % n, carico)
        s = 0
        for x in v:
            s += x * x
            if x < 0:
                x = -x
            if x > picco:
                picco = x
        somma += s
        campioni += n
        if math.sqrt(s / n) >= soglia:
            sopra += 1

    if campioni == 0:
        m["motivo"] = "sono arrivati %d blocchi e ZERO campioni" % len(blocchi)
        return None, m

    m["campioni"] = campioni
    m["rms"] = math.sqrt(somma / campioni)
    m["picco"] = picco
    m["sopra"] = sopra
    m["frazione"] = sopra / float(len(blocchi))

    # ⚠ L'ordine dei tre controlli e' quello del rapporto che si vuole leggere:
    #   prima «quanto», poi «quanto forte», poi «per quanto tempo».
    if len(blocchi) < min_blocchi:
        m["motivo"] = ("POCHI: %d blocchi su %d attesi al minimo (%d ms di "
                       "suono): non e' un flusso"
                       % (len(blocchi), min_blocchi, len(blocchi) * 5))
        return False, m
    if m["rms"] < soglia:
        m["motivo"] = ("SILENZIO: RMS %.1f sotto la soglia %.0f (%.4f %% del "
                       "fondo scala): arrivano byte, ma non sono suono"
                       % (m["rms"], soglia, 100 * m["rms"] / FONDO_SCALA))
        return False, m
    if m["frazione"] < min_frazione:
        m["motivo"] = ("A TRATTI: solo %d blocchi su %d (%.0f %%) sono sopra "
                       "soglia: il suono c'e' a sprazzi"
                       % (sopra, len(blocchi), 100 * m["frazione"]))
        return False, m

    m["motivo"] = ("RMS %.1f = %.2f volte la soglia" % (m["rms"], m["rms"] / soglia))
    return True, m


def guasto_visto(verdetto, m):
    """⛔⛔ §1.52 — «il guasto e' stato visto» NON e' «il verdetto e' rosso».

    ⚠ C5 su GNOME e' rossa per conto suo (`[M]` 41 blocchi invece di ~4 878,
      motivo `POCHI`).  ⇒ Un predicato che guardasse solo il colore direbbe
      «visto» anche se l'iniezione non avesse morso niente, e la
      certificazione della rete poggerebbe su un difetto del prodotto.
    ⭐ Si pretendono DUE cose: il rosso **e** la differenza misurabile — senza
      sorgente devono arrivare **ZERO** blocchi, non «pochi».
    ⛔ `None` non e' zero: se non si e' potuto giudicare, non si e' visto
       niente (§4.5).
    """
    return verdetto is False and m.get("blocchi") == 0


def in_db(v):
    """dBFS, e ⛔ `None` per «non lo so»: uno zero qui sarebbe una bugia."""
    if v is None or v <= 0:
        return None
    return 20.0 * math.log10(v / FONDO_SCALA)


def riga_misure(m):
    def q(x, f="%.1f"):
        return "non lo so" if x is None else (f % x)
    db = in_db(m["rms"])
    return ("blocchi %s · byte %d · codec %s · RMS %s (%s %% f.s., %s dBFS) · "
            "PICCO %s · sopra soglia %s/%s (%s %%)"
            % (q(m["blocchi"], "%d"), m["byte"], m["codec"],
               q(m["rms"]),
               "?" if m["rms"] is None else "%.4f" % (100 * m["rms"] / FONDO_SCALA),
               "?" if db is None else "%.1f" % db,
               q(m["picco"], "%d"), q(m["sopra"], "%d"), q(m["blocchi"], "%d"),
               "?" if m["frazione"] is None else "%.0f" % (100 * m["frazione"])))


# ---------------------------------------------------------------------------
# L'onda di prova — scritta qui, campione per campione.
# ---------------------------------------------------------------------------
def scrivi_onda(percorso, secondi, ampiezza, hertz=440.0):
    """Un WAV s16le 48 kHz stereo con un'onda sinusoidale.

    ⚠ Si scrive a mano invece di chiamare `ffmpeg` per una ragione sola, e non
      e' l'eleganza: ⭐ **l'ampiezza dev'essere un numero di questo file**.  Una
      soglia tarata su un'ampiezza che dipende dalla semantica del filtro di
      qualcun altro e' una soglia che si sposta senza che nessuno lo sappia.
    """
    picco = int(ampiezza * 32767)
    passo = 2.0 * math.pi * hertz / PCM_FREQUENZA
    # ⭐ Si costruisce UN SECONDO e lo si ripete, e non e' solo per fare presto:
    #   a 440 Hz un secondo contiene 440 cicli INTERI, ⇒ la giuntura e' esatta e
    #   non produce lo scatto che un taglio a meta' onda lascerebbe.
    #   ⚠ Con un `--hertz` non intero la giuntura non e' piu' esatta: e' un
    #     difetto sonoro dichiarato, e non tocca la misura d'energia.
    uno = []
    for i in range(PCM_FREQUENZA):
        v = int(round(picco * math.sin(passo * i)))
        v = 32767 if v > 32767 else (-32768 if v < -32768 else v)
        uno.append(v)
        uno.append(v)
    secondo = struct.pack("<%dh" % len(uno), *uno)
    corpo = secondo * max(1, int(round(secondi)))
    with open(percorso, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + len(corpo)))
        f.write(b"WAVEfmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, PCM_CANALI, PCM_FREQUENZA,
                            PCM_FREQUENZA * PCM_CANALI * 2, PCM_CANALI * 2, 16))
        f.write(b"data")
        f.write(struct.pack("<I", len(corpo)))
        f.write(corpo)
    os.chmod(percorso, 0o644)
    return picco


def leggi_blocchi(percorso):
    """⛔ Torna `None` se il file non si e' fatto leggere, `[]` se e' vuoto.
       Sono due cose diverse e non devono avere la stessa faccia."""
    if not os.path.exists(percorso):
        return None
    fuori = []
    try:
        with open(percorso, "r") as f:
            for riga in f:
                riga = riga.strip()
                if not riga:
                    continue
                d = json.loads(riga)
                fuori.append((d["codec"], base64.b64decode(d["byte"])))
    except (OSError, ValueError, KeyError):
        return None
    return fuori


# ---------------------------------------------------------------------------
# ⛔ NIENTE `sh -c` ANNIDATI — `LEZIONI.md` §1.46.  Ogni comando e' un array, e
#    i programmi si chiamano per percorso.
# ---------------------------------------------------------------------------
def esegui(comando, tetto=30):
    try:
        return subprocess.run(comando, capture_output=True, text=True, timeout=tetto)
    except (OSError, subprocess.TimeoutExpired):
        return None


def come(chi, uid, resto, tetto=30):
    """Esegue `resto` **come l'inquilino**, col suo `XDG_RUNTIME_DIR`."""
    return esegui(["runuser", "-u", chi, "--", "env",
                   "XDG_RUNTIME_DIR=/run/user/%d" % uid] + resto, tetto=tetto)


def sink_c_e(chi, uid):
    """Torna True / False / ⛔ None se PipeWire non ha risposto affatto.

    ⭐ E i tre valori sono tre esiti diversi piu' avanti: «non risponde» e' il
      terreno (3), «risponde e il sink non c'e'» e' un rosso del prodotto (1).
    """
    p = come(chi, uid, ["pw-cli", "ls", "Node"], tetto=20)
    if p is None or p.returncode != 0 or not p.stdout.strip():
        return None
    nome = classe = None
    for riga in p.stdout.splitlines():
        r = riga.strip()
        if r.startswith("id ") and ", type " in r:
            nome = classe = None
            continue
        if r.startswith("node.name"):
            nome = r.split("=", 1)[1].strip().strip('"')
        elif r.startswith("media.class"):
            classe = r.split("=", 1)[1].strip().strip('"')
        # ⛔ Non basta che il nome compaia: ci sono DUE nodi «remotix» — il sink
        #    e il flusso che lo cattura.  ⭐ Quello che serve e' il SINK.
        if nome == NOME_SINK and classe == "Audio/Sink":
            return True
    return False


def sgombra(chi, attesa=45.0):
    """⭐ Sempre e solo il PROPRIO inquilino, per nome: mai un modello globale.
       (fase 10 §7.3: un `pkill -f` globale ha rischiato di uccidere il lavoro
       di un'altra prova che stava misurando.)

    ⛔⛔ E SI ASPETTA L'EVENTO, NON L'OROLOGIO.  `loginctl terminate-user` e
        `pkill` tornano SUBITO: chi ripartisse dopo mezzo secondo ricreerebbe
        l'inquilino mentre il precedente sta ancora morendo.  ⚠ E' esattamente
        il difetto che ha fatto dire a C1 «non lo so» cinque volte su dieci
        (`fasi/11…` §7-bis.13).  ⇒ Torna True se il campo e' libero DAVVERO.
    """
    esegui(["loginctl", "terminate-user", chi], tetto=20)
    time.sleep(1.0)
    esegui(["pkill", "-KILL", "-u", chi], tetto=20)
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        viva = esegui(["loginctl", "show-user", chi], tetto=15)
        proc = esegui(["pgrep", "-u", chi], tetto=15)
        if (viva is not None and viva.returncode != 0) and \
           (proc is not None and proc.returncode != 0):
            return True
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
def certifica():
    """⛔ Il guasto innestato in laboratorio: si dimostra che il giudice sa dire
       VERDE, sa dire ROSSO, e sa dire «non lo so».

    ⚠ E si dichiara che cosa copre e che cosa no.
      COPRE: la misura dell'energia e i tre criteri — che un flusso di zeri sia
      rosso, che pochi blocchi siano rossi, che il suono a sprazzi sia rosso,
      che un tono a META' del livello vero resti VERDE, e che quel che non e'
      PCM torni «non lo so» invece che zero.
      ⛔ NON COPRE: che la sessione nasca, che il sink si apra, che `pw-play`
      suoni.  ⇒ Quello lo copre il giro vero, e il suo guasto innestato e'
      `--senza-sorgente`.
    """
    def onda(ampiezza, quanti, hertz=440.0):
        fuori = []
        passo = 2.0 * math.pi * hertz / PCM_FREQUENZA
        i = 0
        for _ in range(quanti):
            b = bytearray()
            for _k in range(PCM_FOTOGRAMMI):
                v = int(round(ampiezza * 32767 * math.sin(passo * i)))
                b += struct.pack("<hh", v, v)
                i += 1
            fuori.append((PCM_CODEC, bytes(b)))
        return fuori

    def zeri(quanti):
        return [(PCM_CODEC, b"\x00" * PCM_BYTE_BLOCCO) for _ in range(quanti)]

    # ⭐ Le ampiezze NON sono inventate: sono le stesse che hanno girato su
    #   sessioni vere (la tabella della taratura, in testa).  ⇒ La
    #   certificazione e il giro vero parlano dello stesso metro.
    VERO = 1.0

    casi = [
        # (nome, blocchi, atteso, pezzo del motivo atteso)
        ("il tono predefinito (ampiezza 1,0)", onda(VERO, 1000), True, "RMS"),
        # ⛔⛔ Il caso che tiene ONESTA la soglia — l'equivalente dei «colori
        #    spostati» di C1 (§4.1): il punto vero piu' vicino da SOPRA deve
        #    restare verde, o la soglia e' troppo stretta e fra due settimane
        #    la rete si butta.  `[M]` a 0,02 il filo ha dato RMS 463,1.
        ("⭐ ampiezza 0,02 — il punto vero piu' vicino da SOPRA: DEVE restare VERDE",
         onda(0.02, 1000), True, "RMS"),
        # ⛔ E il punto vero piu' vicino da SOTTO: `[M]` a 0,01 il filo ha dato
        #    RMS 231,2, e la maglia vera ha detto ROSSO.  ⇒ Il confine e'
        #    attraversato in tutt'e due i versi.
        ("⛔ ampiezza 0,01 — il punto vero piu' vicino da SOTTO",
         onda(0.01, 1000), False, "SILENZIO"),
        ("⛔ non e' arrivato NIENTE", [], False, "NIENTE"),
        # ⭐⭐ IL CASO CHE GIUSTIFICA TUTTA LA MISURA D'ENERGIA: byte che
        #    arrivano, e sono silenzio.  Un giudice che contasse i byte
        #    direbbe verde qui.
        ("⛔ 4 000 blocchi di ZERI — byte che arrivano ed e' silenzio",
         zeri(4000), False, "SILENZIO"),
        ("⛔ quasi-silenzio (ampiezza 0,001)", onda(0.001, 1000), False, "SILENZIO"),
        ("⛔ solo 50 blocchi di tono pieno", onda(VERO, 50), False, "POCHI"),
        # ⛔ RMS globale a posto (il tono e' forte), ma il suono c'e' per un
        #    quarto del tempo: senza il terzo criterio questo passerebbe.
        ("⛔ tono per un quarto del tempo, zeri per il resto",
         onda(VERO, 1000) + zeri(3000), False, "A TRATTI"),
        ("codec Opus ⇒ non lo so", [(1, b"\x00" * 100)] * 400, None, "non PCM"),
        ("codec che CAMBIA ⇒ non lo so",
         onda(VERO, 200) + [(1, b"\x00" * 100)] * 200, None, "CAMBIA"),
        ("carico di lunghezza dispari ⇒ non lo so",
         [(PCM_CODEC, b"\x00" * 961)] * 400, None, "DISPARI"),
        ("il file dei blocchi non si e' letto ⇒ non lo so", None, None, "non sono riuscito"),
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA SECONDA META' — «il guasto e' stato visto?» (§1.52).
    #
    # ⛔ Non c'era prima del 27 ago 2026, ed e' il caso che avrebbe preso il
    #    difetto: le DUE popolazioni misurate su GNOME — 41 blocchi col giro
    #    normale, 0 col guasto innestato — sono tutt'e due ROSSE, ⇒ un
    #    predicato che guarda il colore le confonde.
    # ⚠ 41 e' misurato: `[M]` §7-bis.18, scatola GNOME, contro ~4 878 altrove.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ senza sorgente: ZERO blocchi ⇒ il guasto E' STATO VISTO", [], True),

        ("⛔⛔ i 41 blocchi FORTI di GNOME: rossi per POCHI ⇒ ⛔ NON «visto»",
         onda(VERO, 41), False),

        ("⛔ 4 000 blocchi di zeri: rossi per SILENZIO ⇒ ⛔ NON «visto»",
         zeri(4000), False),

        ("⛔ il giro sano e' verde ⇒ ⛔ NON «visto»", onda(VERO, 1000), False),

        ("⛔ «non lo so» non e' «visto» (§4.5)", None, False),
    ]

    print("== certificazione del giudice di C5 ==")
    print("   il metro: soglia RMS %.0f su %.0f (%.1f %% f.s., %.0f dBFS) · "
          "almeno %d blocchi · almeno il %.0f %% sopra soglia"
          % (SOGLIA_RMS, FONDO_SCALA, 100 * SOGLIA_RMS / FONDO_SCALA,
             in_db(SOGLIA_RMS), MIN_BLOCCHI, 100 * MIN_FRAZIONE))
    print()
    guai = 0
    for nome, blocchi, atteso, pezzo in casi:
        v, m = giudica(blocchi)
        bene = (v is atteso) and (pezzo in (m["motivo"] or ""))
        print("  %s  %-52s  verdetto=%-5s (atteso %-5s)  %s"
              % ("OK " if bene else "NO ", nome, v, atteso,
               (m["motivo"] or "")[:72]))
        if not bene:
            guai += 1
    print()
    print("  ⛔ e il guasto innestato si legge sulla DIFFERENZA, non sul colore:")
    for nome, blocchi, atteso in casi_guasto:
        v, m = giudica(blocchi)
        avuto = guasto_visto(v, m)
        bene = avuto is atteso
        print("  %s  %-52s  visto=%-5s (atteso %-5s)  %s"
              % ("OK " if bene else "NO ", nome, avuto, atteso,
                 (m["motivo"] or "")[:40]))
        if not bene:
            guai += 1
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ E IL TETTO SI CERTIFICA COME UNA SOGLIA — ⛔ o e' un numero che
    #     nessuno ricontrolla piu' (`LEZIONI.md` §1.45).  ⚠ Non c'era prima del
    #     27 ago 2026.
    # ⚠ E il margine sta sul PEGGIORE mai misurato, non sulla dispersione di
    #   oggi: tre misure su una macchina a riposo non dicono niente su una
    #   scatola carica.  ⇒ Vedi `TETTO_NASCITA` in testa.
    # ⛔ E c'e' una seconda pretesa, ed e' quella che C5 aveva sbagliato: il
    #   cliente dev'essere ANCORA ATTACCATO quando il sink compare.
    # ═══════════════════════════════════════════════════════════════════════
    MISURE_SANE = (1.105, 0.998, 0.957)   # `[M]` 27 ago 2026, scatola curata
    SINK_MISURATO = 3.0                   # `[M]` 26 ago 2026, scatole sane
    PEGGIORE_MAI_VISTA = 13.0             # `[M]` 26 ago 2026, scatola carica
    MARGINE = 2.0
    serve = PEGGIORE_MAI_VISTA * MARGINE
    tetto_ok = TETTO_NASCITA >= serve
    resta_ok = (TETTO_NASCITA + FINESTRA_MISURA) >= TETTO_NASCITA + 1.0
    if not tetto_ok or not resta_ok:
        guai += 1
    print()
    print("  %s  il tetto copre la nascita piu' lenta MAI misurata: "
          "%.0f s × %.0f = %.0f s ⇒ TETTO_NASCITA %.0f s"
          % ("OK " if tetto_ok else "NO ", PEGGIORE_MAI_VISTA, MARGINE,
             serve, TETTO_NASCITA))
    print("      ⇒ e sono %.1f volte il sink misurato (%.0f s) e %.0f volte il "
          "fenomeno sano di oggi (%.3f s)"
          % (TETTO_NASCITA / SINK_MISURATO, SINK_MISURATO,
             TETTO_NASCITA / max(MISURE_SANE), max(MISURE_SANE)))
    print("  %s  il cliente resta attaccato %.0f s = tetto %.0f + finestra di "
          "misura %.0f ⇒ e' ancora li' quando il sink compare"
          % ("OK " if resta_ok else "NO ", TETTO_NASCITA + FINESTRA_MISURA,
             TETTO_NASCITA, FINESTRA_MISURA))

    # ⭐⭐ I CASI DELL'AMMISSIONE — ⛔ quelli che oggi non c'erano.
    #    Il predicato vive in C1 e lo si certifica con i casi di C1: ⛔ una
    #    copia dei casi qui sarebbe un secondo posto da cui divergere (§1.47).
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C5")
    guai += guai_amm

    # ⭐⭐ E I CASI DEI GRUPPI DELLA SCHEDA — ⛔ l'altro caso che non c'era:
    #    un inquilino senza i gruppi dei nodi ⇒ «non ho potuto guardare», ⛔
    #    mai rosso.  Vivono in C1 col passo che certificano.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C5")
    guai += guai_gr

    # ⚠ `+ 2` e non `+ 1`: le prove stampate qui sopra sono DUE (il tetto e
    #   il tempo d'attacco).  ⛔ Il conto diceva 1 dal giorno in cui la
    #   seconda e' nata, ⇒ la maglia dichiarava un caso in meno di quelli
    #   che faceva davvero — un conto che non torna e' un conto che non si
    #   puo' citare.
    quanti = len(casi) + len(casi_guasto) + quanti_amm + quanti_gr + 2
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice sa dire VERDE, sa dire ROSSO e sa dire "
          "«non lo so»" % (quanti, quanti))
    print("⛔ e sa distinguere «l'iniezione ha morso» da «ero gia' rossa» (§1.52)")
    print("⚠ e questa certificazione copre la MISURA, non la sessione: quella "
          "la copre il giro vero con `--senza-sorgente`")
    return 0


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c5u1",
                   help="⛔ un inquilino NUOVO: si cancella e si ricrea a ogni "
                        "giro. «Da zero» comprende «da zero rispetto a me "
                        "stesso di ieri» (LEZIONI.md, la cura di C1)")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8512)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--resta", type=float, default=TETTO_NASCITA + FINESTRA_MISURA,
                   help="quanto il cliente resta attaccato a raccogliere suono. "
                        "⭐ = TETTO_NASCITA (26 s) + FINESTRA_MISURA (25 s) = "
                        "51 s: il sink non puo' comparire prima che la sessione "
                        "nasca, e il cliente deve essere ANCORA ATTACCATO "
                        "quando compare — `[M]` e' la ragione dei 41 blocchi "
                        "invece di ~4 878, il cliente se n'era gia' andato")
    p.add_argument("--ampiezza", type=float, default=1.0,
                   help="ampiezza dell'onda, 0..1 di fondo scala. ⭐ Serve alla "
                        "TARATURA: e' con questa che si sono misurate le due "
                        "popolazioni scritte in testa")
    p.add_argument("--hertz", type=float, default=440.0)
    p.add_argument("--senza-sorgente", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: non si suona niente. L'esito si "
                        "legge AL CONTRARIO — qui il verde e' un rosso")
    p.add_argument("--attesa-ammesso", type=float, default=45.0,
                   help="quanto si aspetta che il cliente dica AMMESSO. "
                        "Scaduto: «non ho potuto guardare», MAI verde. "
                        "⚠ Resta 45 s apposta: l'AMMISSIONE e' la stretta di "
                        "mano RCP e viene PRIMA della sessione — il ritardo "
                        "del palco (26 s) lo copre `--attesa-sink`, non "
                        "questo. ⛔ Confonderli vorrebbe dire aspettare il "
                        "palco nella finestra sbagliata")
    p.add_argument("--attesa-sink", type=float, default=TETTO_NASCITA,
                   help="quanto si aspetta che compaia il sink «remotix». "
                        "⭐ = TETTO_NASCITA: `[M]` il sink si vede in 3 s e la "
                        "sessione nasce in 1,105 s sulla scatola curata; 26 s "
                        "sono la nascita piu' lenta mai misurata (13 s) × 2 — "
                        "vedi TETTO_NASCITA in testa")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    # ═══ IL TERRENO — e ogni pezzo che manca e' un «non lo so», mai un verde ══
    if os.geteuid() != 0:
        print("⛔ va eseguito da amministratore dentro la scatola (crea un utente)")
        return 2
    if not os.path.exists(a.cliente):
        print("⛔ non trovo il cliente di prova: %s" % a.cliente)
        print("   ⇒ non ho potuto guardare")
        return 3
    for arnese in ("/usr/bin/pw-play", "/usr/bin/pw-cli"):
        if not os.path.exists(arnese):
            print("⛔ manca %s (pacchetto `pipewire-bin`): senza, non so ne' "
                  "fare suono ne' vedere il sink" % arnese)
            print("   ⇒ non ho potuto guardare")
            return 3

    print("== C5 — il suono c'e' e non e' silenzio ==")
    print("   inquilino NUOVO «%s» · porta %d · resto attaccato %.0f s"
          % (a.utente, a.porta, a.resta))
    print("   il metro: soglia RMS %.0f su %.0f (%.1f %% f.s., %.0f dBFS) · "
          "almeno %d blocchi · almeno il %.0f %% sopra soglia"
          % (SOGLIA_RMS, FONDO_SCALA, 100 * SOGLIA_RMS / FONDO_SCALA,
             in_db(SOGLIA_RMS), MIN_BLOCCHI, 100 * MIN_FRAZIONE))
    if a.senza_sorgente:
        print("   ⛔⛔ GUASTO INNESTATO: la sorgente NON si accende. "
              "L'esito si legge al contrario.")
    else:
        print("   la sorgente: onda a %.0f Hz, ampiezza %.4f, suonata dentro il "
              "sink «%s» del prodotto" % (a.hertz, a.ampiezza, NOME_SINK))
    print()

    chi = a.utente
    blocchi_file = "/tmp/c5-%s-blocchi.jsonl" % chi
    cliente_log = "/tmp/c5-%s-cliente.log" % chi
    onda_file = "/tmp/c5-%s-onda.wav" % chi
    tono = None
    esito = 3

    try:
        # ═══ L'INQUILINO — si CANCELLA prima di crearlo ═══════════════════
        # ⛔ «Da zero» comprende «da zero rispetto a me stesso di ieri»: un
        #    `id -u X || useradd X` renderebbe l'inquilino nuovo solo la PRIMA
        #    volta che questo banco gira in vita sua.
        if not sgombra(chi):
            print("  ⚠ «%s» del giro precedente non se n'e' andato: il campo "
                  "non e' libero, e lo dico invece di far finta di niente" % chi)
        esegui(["/bin/sh", "-c",
                "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi)],
               tetto=60)
        # ⛔ I gruppi della scheda non stanno piu' qui dentro: `usermod -aG
        #    video,render` inchiodava due nomi e non rileggeva.  Li da'
        #    l'attrezzo, qui sotto, che li LEGGE dai nodi e poi VERIFICA.
        f = esegui(["/bin/sh", "-c",
                    "useradd -m -s /bin/bash %s "
                    "&& printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
                   tetto=60)
        if f is None or f.returncode != 0:
            print("⛔ non sono riuscito a creare l'inquilino «%s»: %s"
                  % (chi, (f.stderr.strip()[:120] if f else "il comando non e' partito")))
            print("   ⇒ non ho potuto guardare")
            return 3
        # ⛔⛔ E SENZA I GRUPPI DELLA SCHEDA NON SI MISURA: `[M]` la sessione
        #     nasce cieca (0 su 4), e C5 misurerebbe il suono di un desktop
        #     che non esiste.  ⇒ 3, ⛔ mai rosso (§1.51).
        e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="  ")
        if e_gr != 0:
            # ⭐ Si propaga l'esito dell'attrezzo, non un 3 inchiodato: «non ho
            #   potuto guardare» (3) e «uso sbagliato» (2) hanno nomi diversi.
            print("  %s" % perche_gr)
            print("  ⇒ non misuro — ⛔ e NON e' un rosso (§4.5): esito %d"
                  % e_gr)
            return e_gr
        # ⛔ `esegui` torna `None` a scadenza: senza questa guardia era un
        #    `AttributeError` ⇒ traccia ⇒ Python esce **1** ⇒ il gancio legge
        #    ROSSO, e sarebbe un guasto del BANCO che accusa il prodotto
        #    (`LEZIONI.md` §1.51).  ⚠ Probabilita' bassa, forma sbagliata.
        letto = esegui(["id", "-u", chi])
        if letto is None or letto.returncode != 0 or not letto.stdout.strip():
            print("⛔ ho creato «%s» ma non riesco a leggerne l'uid: e' il "
                  "BANCO che non risponde, non il prodotto" % chi)
            print("   ⇒ non ho potuto guardare")
            return 3
        uid = int(letto.stdout.strip())
        print("  inquilino «%s» creato, uid %d" % (chi, uid))

        # ═══ L'ONDA — e si riscrive a ogni giro ═══════════════════════════
        for vecchio in (blocchi_file, cliente_log, onda_file):
            try:
                os.unlink(vecchio)
            except OSError:
                pass
        if not a.senza_sorgente:
            # ⚠ Piu' lunga di quel che serve, e il margine e' dichiarato: il
            #   tono parte quando il sink si vede e deve arrivare oltre la fine
            #   del cliente.  ⛔ Se finisse prima, la coda del giro sarebbe
            #   silenzio e la frazione crollerebbe — un rosso del BANCO, non del
            #   prodotto (`LEZIONI.md` §1.45).
            # ⚠ E questo margine protegge la CODA, non la TESTA: fra
            #   l'ammissione e la comparsa del sink ci sono secondi di silenzio
            #   dentro la finestra del cliente (fino a ~3 s, e piu' se la scatola e' carica), e nessun
            #   margine li copre.  ⇒ Oggi non mordono perche' `src/audio.c` non
            #   spedisce i blocchi muti — vedi `MIN_FRAZIONE` in testa.  ⛔ E'
            #   una dipendenza fra questa maglia e un'opzione del prodotto, ed
            #   e' scritta qui invece di essere scoperta il giorno del rosso.
            durata = a.resta + 15.0
            picco = scrivi_onda(onda_file, durata, a.ampiezza, a.hertz)
            print("  onda scritta: %.0f s a %.0f Hz, picco alla sorgente %d su "
                  "32767 (%s)" % (durata, a.hertz, picco, onda_file))

        # ═══ IL CLIENTE — si chiede PCM, o non si puo' misurare l'energia ══
        with open(cliente_log, "w") as reg:
            cli = subprocess.Popen(
                ["python3", "-u", a.cliente,
                 "--indirizzo", a.indirizzo, "--porta", str(a.porta),
                 "--utente", chi, "--parola", a.parola,
                 "--audio-codec", "pcm",
                 "--audio-scrivi", blocchi_file,
                 "--resta", str(a.resta)],
                stdout=reg, stderr=subprocess.STDOUT)

        # ⛔ Si aspetta l'EVENTO «AMMESSO», non l'orologio.
        # ⛔⛔ E si aspetta la RIGA, non la parola: `"AMMESSO" in …` sarebbe
        #     vero anche sui due messaggi di RIFIUTO ⇒ questo ciclo sarebbe
        #     uscito **subito e contento** proprio quando il server aveva
        #     respinto il cliente (§1.44).  Vedi `e_stato_ammesso()` in testa.
        # ⭐ Il ciclo esce solo su `True`.  ⚠ `False` NON e' una condizione
        #   d'uscita: nei primi decimi di secondo il cliente ha gia' stampato
        #   «→ CIAO» e non e' ancora stato ammesso — sarebbe un'uscita
        #   anticipata su una sessione che sta ancora nascendo.  ⇒ Chi esce
        #   presto sul rifiuto e' il cliente stesso, che muore (`sys.exit(2)`),
        #   e lo prende il `cli.poll()` qui sotto.
        ammesso = None
        scadenza = time.time() + a.attesa_ammesso
        while time.time() < scadenza:
            try:
                with open(cliente_log, "r", errors="replace") as h:
                    ammesso = e_stato_ammesso(h.read())
                    if ammesso is True:
                        break
            except OSError:
                pass
            if cli.poll() is not None:
                break
            time.sleep(0.5)
        if ammesso is not True:
            # ⛔ «Non ammesso» da solo e' un silenzio: si porta il MOTIVO
            #    accanto al sintomo (la cura di C1).
            motivo = "?"
            try:
                with open(cliente_log, "r", errors="replace") as h:
                    for riga in reversed(h.read().strip().splitlines()):
                        riga = riga.strip()
                        if riga and not riga.startswith("=="):
                            motivo = riga[:100]
                            break
            except OSError:
                pass
            # ⭐ E i due «no» si dicono per nome: «respinto» e «muto» non sono
            #   la stessa cosa, e mescolarli e' meta' del difetto di §1.44.
            print("  ⛔ %s in %.0f s — perche': %s"
                  % ("il cliente e' stato RESPINTO dal server"
                     if ammesso is False
                     else "il cliente non ha detto NIENTE",
                     a.attesa_ammesso, motivo))
            print("\n  ⚠ NON GIUDICO: non ho aperto la sessione, quindi non ho "
                  "modo di dire se il suono ci sarebbe stato.")
            print("     ⛔ E questo NON e' un rosso: e' l'esito 3 (§4.5).")
            return 3
        print("  il cliente e' stato AMMESSO")

        # ═══ IL SINK — e i tre casi sono tre esiti diversi ════════════════
        #
        # ⛔⛔ E SI RICORDA SE PIPEWIRE HA RISPOSTO ALMENO UNA VOLTA, non solo
        #     l'ULTIMA risposta.  ⚠ Fino al 27 ago 2026 `visto` veniva
        #     sovrascritto a ogni giro, e `sink_c_e` torna `None` quando
        #     PipeWire non risponde — cosa che nei primi secondi succede per
        #     forza, perche' `/run/user/<uid>` non c'e' ancora.  ⇒ L'esito era
        #     deciso dall'ultimo colpo:
        #       · risponde «niente sink» per tutta l'attesa e all'ultimo tace
        #         ⇒ **3** invece di **1** (un rosso del prodotto perso);
        #       · e' morto per tutta l'attesa e risponde all'ultimo
        #         ⇒ **1** invece di **3** (un rosso INVENTATO sul prodotto).
        #     ⛔ Sono i due esiti che questa maglia dichiara di tenere separati
        #     apposta (vedi in testa).
        visto = None
        ha_risposto = False
        t0 = time.time()
        scadenza = t0 + a.attesa_sink
        while time.time() < scadenza:
            visto = sink_c_e(chi, uid)
            if visto is not None:
                ha_risposto = True
            if visto:
                break
            time.sleep(1.0)
        if not ha_risposto:
            print("  ⛔ il PipeWire di «%s» non ha risposto NEMMENO UNA VOLTA "
                  "in %.0f s" % (chi, a.attesa_sink))
            print("\n  ⚠ NON GIUDICO: e' il terreno che non parla, non il "
                  "prodotto.  ⛔ E non e' un rosso (§4.5).")
            return 3
        if not visto:
            print("  ⛔ PipeWire ha risposto (almeno una volta), e il sink «%s» "
                  "NON c'e' dopo %.0f s" % (NOME_SINK, a.attesa_sink))
            print("\n  ⛔⛔ ROSSO — il prodotto non ha aperto la via del suono.")
            print("     ⇒ `src/suono.c` crea un `support.null-audio-sink` "
                  "chiamato «%s»: non c'e'." % NOME_SINK)
            return 1
        print("  ⭐ il sink «%s» c'e' dopo %.0f s" % (NOME_SINK, time.time() - t0))

        # ═══ LA SORGENTE ══════════════════════════════════════════════════
        if a.senza_sorgente:
            print("  ⛔ GUASTO INNESTATO: non suono niente")
        else:
            tono = subprocess.Popen(
                ["runuser", "-u", chi, "--", "env",
                 "XDG_RUNTIME_DIR=/run/user/%d" % uid,
                 "pw-play", "--target=%s" % NOME_SINK, onda_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  la sorgente suona (pw-play su «%s»)" % NOME_SINK)

        # ⛔ Il tetto governa l'ATTESA DEL CLIENTE, non il lavoro: se il cliente
        #    ha gia' scritto i suoi blocchi, si giudicano lo stesso — si giudica
        #    il RISULTATO, non il codice d'uscita (`LEZIONI.md` §1.50).
        try:
            cli.wait(timeout=a.resta * 3 + 60)
        except subprocess.TimeoutExpired:
            print("  ⚠ il cliente non e' uscito da solo: lo chiudo e guardo "
                  "quel che ha scritto")
            cli.kill()
            cli.wait(timeout=30)

        # ═══ IL GIUDIZIO ══════════════════════════════════════════════════
        blocchi = leggi_blocchi(blocchi_file)
        verdetto, m = giudica(blocchi)
        print()
        print("  %s" % riga_misure(m))
        # ⭐ Il secondo testimone: quel che il PRODOTTO dice di aver spedito.
        #   ⚠ Si STAMPA e non si giudica — e' un confronto per chi diagnostica,
        #     non un criterio.
        for riga in coda_registro(a.registro, chi):
            print("  [registro] %s" % riga)
        print("  ⇒ %s" % (m["motivo"] or "—"))

        # ═══ E il margine, che si stampa SEMPRE ═══════════════════════════
        if m["rms"]:
            print("  margine sulla soglia: %.2f volte (%.1f dB) — ⚠ e si stampa "
                  "sempre: e' il numero che avvisa PRIMA che la soglia diventi "
                  "un rosso falso" % (m["rms"] / SOGLIA_RMS,
                                      in_db(m["rms"]) - in_db(SOGLIA_RMS)))

        print()
        # ═══ E col guasto innestato l'esito si legge AL CONTRARIO ═════════
        if a.senza_sorgente:
            # ═══════════════════════════════════════════════════════════════
            # ⛔⛔ E NON BASTA IL COLORE DEL VERDETTO — `LEZIONI.md` §1.52.
            #
            # ⚠ Fino al 27 ago 2026 l'unico predicato qui era `verdetto is
            #   False`.  ⛔ Ma C5 su GNOME e' rossa **per conto suo**: `[M]`
            #   §7-bis.18, arrivano **41 blocchi** invece di ~4 878 ⇒ motivo
            #   `POCHI`.  E senza sorgente ne arrivano **0** ⇒ motivo `NIENTE`.
            #   ⇒ Tutt'e due `False`, ⇒ si usciva **0**, ⇒ il gancio scriveva
            #   `ha_visto_il_guasto: true` **senza aver mai confrontato 41 con
            #   0**.  ⛔ La certificazione della rete poggiava su un difetto
            #   del prodotto, che e' §1.52 parola per parola.
            #
            # ⭐ La cura e' la stessa che C9 ha gia': si pretendono DUE cose —
            #   il verdetto rosso **e** una differenza misurabile.  Qui la
            #   differenza e' il conto dei blocchi: senza sorgente ne devono
            #   arrivare **ZERO**.  ⛔ E non e' una pretesa gratuita: la cura
            #   del silenzio di `src/audio.c` (`audio_taci_silenzio`, accesa in
            #   modo predefinito) NON spedisce i blocchi muti — quindi «nessuna
            #   sorgente» vuol dire davvero «nessun blocco».
            # ═══════════════════════════════════════════════════════════════
            quanti = m["blocchi"]
            if guasto_visto(verdetto, m):
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO: senza sorgente non "
                      "arriva un solo blocco (%s)" % (m["motivo"] or "")[:60])
                print("   ⇒ questa maglia SA dare rosso sui dati veri, ⭐ e il "
                      "rosso viene DAL GUASTO: 0 blocchi, non «pochi».")
                return 0
            if verdetto is False:
                print("⛔⛔ ROSSO, ma NON per colpa del guasto: senza sorgente "
                      "sono arrivati lo stesso %s blocchi." % quanti)
                print("    ⇒ %s" % (m["motivo"] or ""))
                print("    ⛔ C5 era GIA' rossa per conto suo, e l'iniezione non")
                print("      ha tolto niente: dire «il guasto e' stato visto»")
                print("      certificherebbe la rete su un difetto del PRODOTTO")
                print("      (`LEZIONI.md` §1.52).")
                return 1
            if verdetto is None:
                print("⛔ non ho potuto giudicare: non posso dire se il guasto "
                      "si sarebbe visto")
                return 3
            print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: senza sorgente "
                  "C5 dice comunque VERDE.")
            print("    ⇒ o il suono arriva da un'altra parte, o questa maglia "
                  "non guarda nel posto giusto — e in tutt'e due i casi non ci "
                  "si puo' fidare di lei.")
            return 1

        if verdetto is None:
            print("  ⚠ NON GIUDICO — %s" % (m["motivo"] or ""))
            print("     ⛔ E questo non e' un verde: e' un esito suo (§4.5).")
            return 3
        if verdetto is False:
            print("  ⛔⛔ ROSSO — il suono non c'e', o e' silenzio.")
            print("     %s" % (m["motivo"] or ""))
            return 1
        print("  ⭐ VERDE — il suono arriva al cliente e NON e' silenzio.")
        print("     ⚠ E C5 verde non vuol dire «la sessione sta bene»: C5 non "
              "guarda un pixel (vedi in testa).")
        return 0

    finally:
        if tono is not None and tono.poll() is None:
            tono.kill()
        sgombra(chi)


def coda_registro(percorso, chi):
    """Le righe del PRODOTTO su questo inquilino — ⭐ un secondo testimone.

    ⛔ Si STAMPANO e non si giudicano: sono il conto di chi spedisce, e C5
       giudica quel che ARRIVA.  ⚠ Averli tutti e due accanto e' quel che fa
       capire, il giorno del rosso, da che parte del filo sta il guasto.
    """
    fuori = []
    try:
        with open(percorso, "r", errors="replace") as f:
            testo = f.read()
    except OSError:
        return ["⚠ il registro del server non si e' fatto leggere: %s" % percorso]
    for riga in testo.splitlines():
        if "[%s]" % chi not in riga:
            continue
        if "PICCO" in riga or "cura del silenzio" in riga or "conto finale" in riga:
            fuori.append(riga.strip()[:200])
    if not fuori:
        return ["⚠ il registro del server non dice niente di «%s»: ⛔ non e' "
                "uno zero, e' un silenzio" % chi]
    return fuori[-3:]


if __name__ == "__main__":
    sys.exit(main())
