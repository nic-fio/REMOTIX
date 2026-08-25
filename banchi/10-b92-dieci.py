#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b92-dieci — LA SALITA: le sessioni si accendono UNA ALLA VOLTA, da 1 a 10, e
               a **ogni gradino** si misura **ciascuna** di quelle gia' vive.

    porta 8100 · utenti `provamt1`…`provamt10` (uid 1110-1119) + `provamt11`
    albero `/media/REMOTIX/src/10a6-src` · lavoro `/media/REMOTIX/tmp/10a6`
    unita' `remotix-8100` · terreno: `banchi/10-b91-terreno-dieci.sh`

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ CHE FORMA HA, E PERCHE' NON E' «DIECI FUNZIONANO SI'/NO»
═══════════════════════════════════════════════════════════════════════════════

`DECISIONI.md` §4.6-bis, alla lettera: *«Non si fa degradare chi sta gia'
lavorando per far entrare chi arriva.  Sarebbe la scelta apparentemente gentile,
ma punisce in silenzio chi non ha fatto niente — ed e' precisamente cio' che I1
vieta»*.

⇒ Un banco che accende dieci sessioni insieme e dice «reggono» **non risponde a
  questa domanda**.  La domanda e' *«che cosa succede alla PRIMA quando arriva
  la SESTA»*, e per rispondere serve una **curva**: la stessa sessione, misurata
  a ogni gradino, appaiata con se stessa.

  | gradino | chi c'e' | che cosa si misura |
  |---|---|---|
  | 1 | s1 | s1 |
  | 2 | s1 s2 | s1 **e** s2 |
  | … | … | … |
  | 10 | s1 … s10 | ⭐ tutte e dieci, una riga a testa |
  | 11 | s1 … s11 | ⭐ l'UNDICESIMO: che cosa riceve, e come lascia gli altri |

  Il numero che esce dalla fase e': ⭐ **fps di s1 al gradino 1** contro **fps di
  s1 al gradino 10**.  Appaiato, non a occhio.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE CINQUE FORME D'ERRORE CHE QUESTO BANCO HA DOVUTO CHIUDERE PRIMA DI GIRARE
═══════════════════════════════════════════════════════════════════════════════

Sono quelle dell'incarico, e ciascuna ha il suo caso in `--certifica` — ⛔ e il
caso e' stato **fatto girare**, non immaginato (`LEZIONI.md` §1.29, `REVIEWER.md`
E14: *«il banco tace invece di dare rosso»*, nove difetti su nove in fase 9).

 1. ⛔ **Una sessione che non si apre.**  ⇒ ROSSO, e la salita **si ferma**.
    Un banco che continuasse contandone nove misurerebbe il gradino 10 con nove
    sessioni e scriverebbe «dieci ci stanno» sotto un numero che vale nove.
 2. ⛔ **Un cliente che muore a meta'.**  ⇒ i suoi numeri sono `None`, **non
    zero**, e `None` non entra in nessuna media (`CODER.md` §3.10).
 3. ⛔⛔ **Un palco orfano del giro precedente.**  In fase 9 non dava rosso:
    dava **un numero plausibile**, e stava per far accusare tre cure innocenti.
    ⇒ Si smaschera **prima** di misurare, in `10-b91-terreno-dieci.sh stato`, e
    la salita si rifiuta di partire se ce n'e' uno.
 4. ⛔⛔ **Il conto di un gradino letto dal gradino precedente.**  E' successo
    davvero in fase 9: tre profili di fila hanno riferito **gli stessi identici
    numeri**.  ⇒ ⭐ **L'ANCORA**, ed e' doppia (vedi `fetta()` e `p_ancora()`):
      · la finestra di ogni gradino e' `[t0, t1]` sull'orologio MONOTONO della
        macchina, letto **fresco** a ogni confine, e si pretende `t0(N) > t1(N-1)`;
      · i `numero` di §6.2 crescono di uno per ogni fotogramma che il server
        decide di spedire ⇒ ⛔ **l'insieme dei `numero` del gradino N e quello
        del gradino N-1, per la stessa sessione, DEVONO essere disgiunti**, e il
        primo del gradino N dev'essere maggiore dell'ultimo del precedente.
      ⚠ Due gradini che riportassero gli stessi numeri sono, per costruzione,
        impossibili da non vedere.
 5. ⛔ **Dieci desktop FERMI dichiarati come dieci sessioni al lavoro.**
    `LEZIONI.md` §1.30: *«Diciotto pacchetti non sono una prova»*; `[M]` fase 9,
    su un desktop quasi fermo i fotogrammi pesavano **242-283 byte** e «la
    perdita non aveva niente da rompere».  ⇒ Ogni riga porta **byte per
    fotogramma** e **fotogrammi consegnati**, e un gradino in cui una sessione
    sta sotto `BYTE_VIVI` non e' verde: e' uno schermo nero.

═══════════════════════════════════════════════════════════════════════════════
⭐ IL MECCANISMO ACCANTO AL SINTOMO — `LEZIONI.md` §1.31, e vale un fattore 5
═══════════════════════════════════════════════════════════════════════════════

`[M]` fase 9: la **spirale di chiavi** parte fra lo 0,00 % e lo 0,10 % di
perdita — cioe' al primo pacchetto perso — mentre i fotogrammi/s restano buoni
fino allo 0,53-0,75 %.  ⇒ Un banco che guardasse solo i fotogrammi/s **darebbe
verde su un prodotto che sta gia' degenerando**.

⇒ Qui la **quota di fotogrammi chiave** sta nella stessa riga dei fotogrammi/s,
  sempre, e ha un predicato suo (`p_quota_chiavi`).  Il sintomo dice quando
  l'utente se ne accorge; il meccanismo dice quando e' cominciato.

═══════════════════════════════════════════════════════════════════════════════
⚠ I GIRI CORTI SOTTOSTIMANO — `LEZIONI.md` §1.32
═══════════════════════════════════════════════════════════════════════════════

`[M]` fase 9: un fenomeno che a 10 s si vedeva nel **35 %** dei giri, a 50 s si
vedeva nel **90 %** — innesco a senso unico, λ = 0,053/s.  ⇒ Ogni gradino dura
`--durata` secondi **a regime** (predefinito 45), e ⭐ **il gradino pieno si
rifa' a DOPPIA durata** (`--doppia`): se la frazione segue l'esposizione, il
numero corto sottostimava, e si dice.

═══════════════════════════════════════════════════════════════════════════════
⛔ CHE COSA QUESTO BANCO **NON** SA VEDERE — si dichiara in testa
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **L'IMMAGINE.**  Conta fotogrammi, chiavi, byte, ritardo, memoria, GPU e
    CPU.  Non sa dire *«si vede peggio»*: quel verdetto e' dell'utente sul
    desktop vero (`v1` fase 10 fu azzerata proprio per questo).
 2. ⛔ **IL BROWSER.**  Il cliente prende i byte dal filo e **non decodifica e
    non dipinge**.  `[M]` fase 8: sulla catena vera il worker dipinge il **73 %
    di meno** a saturazione.  ⇒ I fotogrammi/s di qui sono un **tetto**.
 3. ⛔⛔ **LA RETE VERA, e qui e' il buco piu' grosso.**  I dieci clienti girano
    **sulla stessa macchina** del server, dentro il contenitore: il traffico
    passa da `lo` (MTU 65536), che non ha ne' il tetto del gigabit ne' code di
    router.  ⇒ Il **budget di rete** di `DECISIONI.md` §3.1-bis punto 2 —
    dieci sessioni × 30 Mbit/s = **300 Mbit/s sul filo del server** — qui si
    **conta**, non si **prova**: si legge quanti bit/s le dieci sessioni
    CHIEDEREBBERO, e si dice a che frazione del budget starebbero.  ⚠ Chi vuole
    provarlo davvero deve mettere dieci clienti su macchine diverse.

    ⛔⛔ E IL CONTATORE DI `lo` NON E' MIO — `[M]` 24 agosto 2026.  Sulla
        macchina di prova ci sono **altri sei agenti**, e i loro clienti girano
        nello stesso contenitore sullo stesso `lo`: con **una** mia sessione da
        1,6 Mbit/s il contatore di `lo` diceva **35,6 Mbit/s**.  ⇒ Il budget di
        rete si somma dalle righe `rete-quic <ip:porta>` delle **mie**
        connessioni, e `lo` si stampa solo come contorno, dichiarato altrui.
        ⚠ E' la stessa forma di `LEZIONI.md` §1.26: non un rosso, un numero
          plausibile — ventidue volte piu' grande del vero.

 3-bis. ⛔⛔ **LA SCENA DEVE MORDERE, e il predefinito e' quello che SATURA.**
    `[M]` primo giro vero, `--movimento barra` (una barra bianca che attraversa
    uno sfondo fermo): **2 448 byte per fotogramma**, 0,77 Mbit/s per sessione.
    ⇒ Dieci sessioni cosi' sono 7,7 Mbit/s e non chiedono niente a nessuno: un
    banco che ci scrivesse sopra «dieci ci stanno» darebbe *«un giudizio che
    sembra un risultato»* (`LEZIONI.md` §1.30).  ⭐ `PIANO.md` fase 10 dice
    invece *«si SATURA il codificatore di proposito»* ⇒ predefinito
    `--movimento pieno`: ventiquattro bande che scorrono, schermo intero
    danneggiato a ogni fotogramma, `[M]` **5 600 byte per fotogramma**.
    ⚠ E si dichiara da tutt'e due i lati: il numero che ne esce e' un
      **pavimento** — quante sessioni stanno insieme quando ciascuna chiede il
      massimo — non una previsione per dieci utenti che leggono la posta.
 4. ⚠ **IL COSTO DEI CLIENTI, che pero' si MISURA.**  Dieci clienti Python
    sullo stesso ferro possono diventare loro il collo (l'incarico lo chiede per
    nome).  ⇒ La sonda misura la CPU dei clienti **a parte** da quella del
    server, e `p_clienti_non_sono_il_collo` da' rosso se i clienti si prendono
    piu' di `QUOTA_CLIENTI` della macchina.  ⛔ Se quel predicato e' rosso,
    **nessun numero di quel gradino e' attribuibile al prodotto**.
 5. ⚠ **LA RIGA `ciclo:` DEL FIGLIO NON E' ATTRIBUIBILE.**  `figlio.c:7343` la
    scrive senza dire di quale figlio e', e con dieci figli che appendono allo
    stesso registro le righe si mescolano.  ⇒ Le «attese a vuoto» — la colonna
    che in fase 9 separava Mutter da noi — qui si leggono **in somma**, e si
    dichiarano tali.  ⭐ Quel che INVECE e' attribuibile e' la riga
    `rete-quic <ip:porta>` di `webtransport.c:4975`, che porta la provenienza:
    e `rcp.c:2869` — *«posto PRESO da %s via %s»* — lega la provenienza
    all'UTENTE.  ⇒ La mappa utente→provenienza si legge dal registro.
 6. ⛔ **CHI ALTRO STA SULLA MACCHINA.**  La GPU e' una.  Il banco prende il
    **lucchetto** per tutta la salita e conta comunque, in ogni fotografia, i
    processi con un descrittore su `renderD128` che **non sono miei**.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA NON E' RISCRITTO — si importa
═══════════════════════════════════════════════════════════════════════════════

  · la **riduzione** da giornale a numeri — fotogrammi/s, finestra peggiore,
    chiavi/delta, byte, buchi nel `numero` — e' `misura()` di
    `banchi/09-b70-ritmo.py`, gia' certificata: si importa, e ⛔ **si verifica
    subito dopo l'import con un giornale a valore noto** (`LEZIONI.md` §1.33 —
    il metro si tara prima).  Un'importazione che riuscisse a meta' darebbe
    numeri, non misure.
  · il **terreno** e' `banchi/10-b91-terreno-dieci.sh`, che a sua volta non
    riscrive `07-b64-terreno.sh`.
  · il **lucchetto della GPU** e' `banchi/09-lucchetto.py`.
  · e QUATTRO attrezzi si spediscono sulla macchina in base64, perche' devono
    girare **dove stanno i dati**: `10-b92-cliente.py` (il cliente col
    giornale), `10-b92-fetta.py` (il ritaglio di un gradino),
    `10-b92-sonda.py` (la fotografia della macchina) e `10-b92-conti.py` (il
    registro del server letto in una passata sola).
  · il **cliente** e' `banchi/01-b3-cliente.py`, importato come modulo e con
    **una sola** funzione sostituita — vedi `CLIENTE` qui sotto.

═══════════════════════════════════════════════════════════════════════════════
I CODICI D'USCITA
═══════════════════════════════════════════════════════════════════════════════

    0   CONFORME — ogni predicato ha fatto quel che era scritto prima
    1   NON CONFORME — c'e' almeno un rosso
    2   uso sbagliato, terreno assente, lucchetto non preso
    3   ⛔ NON HO NIENTE DA GIUDICARE — un gradino non ha prodotto numeri, o un
        predicato si e' rifiutato.  ⚠ Non e' un verde.

L'ORDINE, e non e' un elenco di comodo:

    1. bash banchi/10-b91-terreno-dieci.sh porta      # sorgenti + compila
    2. bash banchi/10-b91-terreno-dieci.sh utenti     # i dieci (+ l'undicesimo)
    3. bash banchi/10-b91-terreno-dieci.sh accendi    # UN solo server, la 8100
    4. python3 banchi/10-b92-dieci.py --certifica     ⭐ i guasti, senza macchina
    5. python3 banchi/10-b92-dieci.py taratura        ⛔ i metri, PRIMA
    6. python3 banchi/10-b92-dieci.py uno-per-volta   ⛔ ciascuno da solo
    7. python3 banchi/10-b92-dieci.py salita --quanti 11 --durata 45 --doppia
    8. bash banchi/10-b91-terreno-dieci.sh spegni     # e si VERIFICA con `ss -uln`

⭐⭐ I TRE BRACCI (B3, 24 agosto 2026) — e il primo dei tre e' il CONTROLLO:
    python3 banchi/10-b92-dieci.py salita --scena satura --quanti 11  ⛔ l'ANCORA
    python3 banchi/10-b92-dieci.py salita --scena vero   --quanti 11
    python3 banchi/10-b92-dieci.py salita --scena ferma  --quanti 11
    python3 banchi/10-b92-dieci.py legge  --durata 40    ⭐ una sessione, e
                                          #  «quanto il desktop cambia» girato
                                          #  come una manopola

Gli altri passi:
    python3 banchi/10-b92-dieci.py stato      # il terreno, e i palchi orfani
    python3 banchi/10-b92-dieci.py sgombra    # chiude i MIEI palchi
    MOVIMENTO=barra python3 …  salita …       # ⚠ il caso LEGGERO, che non satura
    …  salita --senza-lucchetto               # ⛔ solo per la messa a punto:
                                              #    quei numeri non si riferiscono
"""
import argparse
import base64
import importlib.util
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "8100"))
QUANTI = int(os.environ.get("QUANTI", "10"))
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10a6")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10a6-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10a6-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10a6")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
SCENA_BIN = os.environ.get("SCENA_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/10-b92")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
IO_SONO = os.environ.get("IO_SONO", "10-a6")
# ⭐⭐ IL LUCCHETTO PRESO DA FUORI — B3, 24 agosto 2026, e la ragione e' misurata.
#
# ⛔ Alla fase 10 sulla macchina lavorano DIECI agenti, e il lucchetto della GPU
#    e' uno.  `[M]` 24 agosto, sera: fra una richiesta e l'altra sono passati
#    **due turni di 85 minuti**, e un incarico che ha bisogno di QUATTRO giri
#    (tre bracci piu' la legge) si metterebbe in coda quattro volte — cioe' sei
#    ore di attesa per un'ora e mezza di misura.
# ⇒ Chi ha piu' giri da fare prende il lucchetto UNA volta, li fa tutti dentro
#   lo stesso turno, e lo molla.  ⚠ Non e' un permesso di tenerlo di piu': e' il
#   riconoscimento che quattro attese sono peggio, per TUTTI, di un'attesa sola.
#
# ⛔ E non e' `--senza-lucchetto`: li' i numeri non varrebbero.  Qui il lucchetto
#    **e' mio**, lo tiene il lanciatore, e `10-b0-terreno.sh` lo verifica con
#    `LUCCHETTO_MIO=1` — cioe' pretende che sia mio, non che sia libero.
LUCCHETTO_ESTERNO = os.environ.get("LUCCHETTO_ESTERNO", "0") == "1"

# ⛔ Gli utenti sono MIEI e l'uid segue il nome per costruzione, come nel
#    terreno: `provamtN` → 1109+N.  Due tabelle in due file divergono.
UID_BASE = 1109


def utente(i):
    return "provamt%d" % i


def uid(i):
    return UID_BASE + i


# ⛔ Le porte che NON sono mie: si contano, non si toccano.
VICINE = ["7700", "7730", "7900", "7910", "7920", "8000", "8010", "8020",
          "8030", "8040", "8050", "8060", "8070", "8080", "8090"]

# ⭐ La scheda su cui si misura, e non e' una preferenza: `DECISIONI.md`
#    §4.6-quinquies — *«i test vanno fatti sulla GPU integrata, altrimenti
#    "trucchiamo" il gioco»*.  ⛔ `0000:03:00.0` (la RX 6800) e' chiusa da una
#    regola udev, e se comparisse in una fotografia vorrebbe dire che la regola
#    non c'e' piu': il banco lo DICE invece di sommare i due numeri.
PDEV_BUONO = os.environ.get("PDEV", "0000:00:02.0")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, E CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.33: una soglia si tara sui DUE ESTREMI NOTI prima di
#    crederci, e quando decide qualcosa di irreversibile si mette **sopra** il
#    centro fra i due.  ⚠ Qui nessuna soglia stacca nessuno: decidono solo il
#    colore di una riga di rapporto, e il margine si dichiara da tutt'e due i
#    lati.
PAVIMENTO_FPS = 25.0        # `DECISIONI.md` §2.1 — 480p · 25 fps, il fondo scala
PAVIMENTO_FINESTRA = 20.0   # ⚠ l'80 % del pavimento: non e' un secondo metro,
                            #   serve a non dare rosso a una finestra che cade a
                            #   cavallo di un singolo singhiozzo
QUOTA_DELTA = 0.90          # §3.3: si degrada NEL TEMPO.  Sotto, il flusso sta
                            #   degenerando in chiavi — `[M]` 21 ago: 144/144
BYTE_VIVI = 4000            # ⛔ IL PREDICATO DEGLI SCHERMI NERI.  `[M]` fase 9,
                            #   §1.30: un desktop quasi fermo fa fotogrammi da
                            #   **242-283 byte**; un trascinamento di finestra
                            #   picca a **3 801**.
                            #   ⭐⭐ E IL TERZO ESTREMO L'HA DATO QUESTO BANCO,
                            #   il 24 agosto 2026: la scena `barra` a 1080p fa
                            #   `[M]` **2 448 byte per fotogramma** — cioe' sta
                            #   SOTTO la soglia, e il predicato le ha dato ROSSO
                            #   al primo giro vero.  ⚠ Il rosso era giusto e non
                            #   era del prodotto: era del BANCO, che stava
                            #   misurando dieci desktop quasi fermi.  ⇒ Da li'
                            #   il predefinito e' `--movimento pieno` (vedi
                            #   `MOVIMENTO` piu' sotto), che fa `[M]` decine di
                            #   migliaia di byte.
                            #   ⛔ La soglia sta SOPRA i due estremi che NON
                            #   mordono (2 448 e 3 801) e molto sotto quello che
                            #   morde — `LEZIONI.md` §1.33: si prova la
                            #   grandezza sugli estremi noti prima di tararla.
I1_TOLLERANZA = 0.10        # ⚠ il rumore fra due misure della stessa macchina a
                            #   distanza di minuti.  ⛔ Non e' «10 % di calo e'
                            #   accettabile»: e' «sotto il 10 % non so
                            #   distinguerlo dal rumore», ed e' per questo che
                            #   `p_I1` con un calo fra il 10 % e il 15 % NON da'
                            #   verde: si rifiuta e lo dice.
I1_SICURO = 0.15            # oltre, il calo e' un fatto e non un rumore
QUOTA_CLIENTI = 0.35        # ⛔ oltre, i dieci clienti sono il collo e nessun
                            #   numero di quel gradino e' del prodotto
MINIMO_FOTOGRAMMI = 30      # sotto, non c'e' niente da ridurre (come 09-b70)
ASSESTAMENTO_S = 8.0        # ⛔ i primi secondi di una sessione nuova sono
                            #   apertura, prima chiave e prima tela: si tolgono
                            #   e si DICE quanto si e' tolto (`REVIEWER.md` E9)
TELA = os.environ.get("TELA", "1920x1080")
# ⛔⛔ IL MOVIMENTO DELLA SCENA, E IL PREDEFINITO **SATURA** — e il numero che
#     l'ha deciso e' misurato, non scelto.
#
# `[M]` 24 agosto 2026, primo giro vero con `--movimento barra` su due sessioni:
#       39,3 fotogrammi/s, **2 448 byte per fotogramma**, 0,77 Mbit/s.  ⇒ Un
#       desktop con una barra che si muove su uno sfondo fermo produce delta
#       minuscoli: dieci sessioni cosi' sono **7,7 Mbit/s in tutto**, e non
#       chiedono niente ne' alla GPU ne' al filo.
#       ⚠ E' esattamente `LEZIONI.md` §1.30: *«Diciotto pacchetti non sono una
#         prova»*.  Un banco che dichiarasse «dieci ci stanno» su quei numeri
#         darebbe un giudizio che sembra un risultato.
#
# ⭐ `PIANO.md` fase 10 dice che cosa deve fare questo banco, e lo dice con due
#    parole: *«si SATURA il codificatore di proposito»*.  ⇒ `--movimento pieno`:
#    ventiquattro bande di colore che scorrono, tutto lo schermo danneggiato a
#    ogni fotogramma.  E' il caso DURO, non il desktop medio.
# ⚠ E si dichiara da tutt'e due i lati: il numero che ne esce e' un **pavimento**
#   — quante sessioni stanno insieme quando ciascuna chiede il massimo — non una
#   previsione di quante ne reggerebbe con dieci utenti che leggono la posta.
#   Il caso leggero e' `--movimento barra`, e i suoi numeri stanno qui sopra.
MOVIMENTO = os.environ.get("MOVIMENTO", "pieno")
CODEC_CHIESTO = os.environ.get("CODEC", "h264")   # ⛔ quel che Firefox dipinge

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LE TRE SCENE — aggiunte il 24 agosto 2026 (incarico B3)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il primo giro ha misurato la salita con la SOLA scena `satura`, e ne sono
#    usciti i **sei** di `fasi/10-…md` §6.5.  ⭐ Quel sei e' il numero del CASO
#    PEGGIORE, e non e' il caso in cui vive l'utente: `[M]` §6.4-bis dice che una
#    sessione FERMA costa **GPU zero** (RC6 100 %, GT 0 MHz) e che il caso
#    leggero vale **2 448 byte per fotogramma** contro i 5 130 del desktop vero.
#    ⇒ **Nessuno sapeva quanti desktop VERI stessero insieme**, ed e' il numero
#      che il prodotto dovra' rispettare.
#
#   | scena    | che cos'e'                                        | perche' c'e' |
#   |----------|---------------------------------------------------|--------------|
#   | `ferma`  | il desktop aperto, nessuno tocca niente            | ⭐ e' il caso piu' comune in un multi-tenant vero: gente collegata che legge |
#   | `vero`   | due finestre vere + la scena IN FINESTRA a STRAPPI | e' la scena in cui vive l'utente — ⭐ **la stessa definizione di `10-b89` §6.4-bis**, per poterle confrontare |
#   | `satura` | quella del primo giro, a schermo intero            | ⭐ **l'ANCORA**: deve ridare **sei**, o le due misure non sono confrontabili |
#
# ⛔⛔ IL TERZO BRACCIO NON E' UN LUSSO: E' IL CONTROLLO.  Se rifacendo la scena
#     satura non si ritrova il sei del primo giro, e' cambiato **qualcos'altro
#     insieme alla scena**, e il numero nuovo non vale.  ⇒ `p_ancora_ritrova`.
#
# ⛔ E il braccio `satura` gira per la STESSA STRADA di prima, riga per riga:
#    nessun ESC, nessuna finestra, nessuno strappo.  ⚠ Un'ancora «migliorata» non
#    e' piu' un'ancora.
SCENA = os.environ.get("SCENA", "satura")          # satura | vero | ferma
# ⛔⛔ LE FINESTRE VERE, E IL NOME STA IN UN POSTO SOLO — `[M]` 24 agosto 2026,
#     e questa riga esiste perche' il braccio «vero» e' morto al primo gradino
#     con `NameError: name 'FINESTRE' is not defined`: il nome era definito
#     **dentro** l'attrezzo spedito (`SCENE`, che e' una stringa) e non nel
#     modulo che lo usa.  ⚠ E' costato un giro di lucchetto, cioe' novanta
#     minuti di coda.
# ⛔ La classe di caratteri non e' un vezzo: `pkill -f 'nautilus|…'` lanciato da
#    una shell la cui riga di comando CONTIENE «nautilus» ammazza la shell
#    stessa, e la pulizia finisce a meta' **in silenzio**.
FINESTRE = "nautilu[s]|gnome-termina[l]"
SHM_BASE = os.environ.get("SHM_BASE", "10b92")     # ⛔ /dev/shm e' UNO per macchina
FINESTRA_VERO = os.environ.get("FINESTRA_VERO", "1280x720")
# ⭐ Lo strappo: quiete e accensione sono quelli di `10-b89` (§6.4-bis), perche'
#    le due misure devono poter stare nella stessa tabella.
STRAPPO_QUIETE = float(os.environ.get("STRAPPO_QUIETE", "1.0"))
STRAPPO_ACCENSIONE = float(os.environ.get("STRAPPO_ACCENSIONE", "0.30"))
# ⛔ Il numero che l'ancora deve ritrovare, e viene dal PRIMO GIRO, non da qui:
#    `fasi/10-multi-tenant-e-il-budget.md` §6.5 e §S.2 — sei sessioni sature a
#    38-39 fot/s, la settima a 23-29, l'ottava a 1,5.
CAPIENZA_ANCORA = int(os.environ.get("CAPIENZA_ANCORA", "6"))
# ⚠ Un braccio d'ancora e' confrontabile se ritrova il sei **esatto**: ±1 non e'
#   una tolleranza, e' un'altra misura.
# ⛔ LE SOGLIE DELLE SCENE NUOVE, e ciascuna tarata sui DUE ESTREMI NOTI.
#
# ⛔⛔ E QUI C'E' UNA FERITA GIA' PAGATA, che va scritta prima del codice:
#     `10-b89` (§SOGLIA_BYTE_MORDE) ha misurato che i byte per fotogramma
#     **NON separano** una scena `pieno` sana da una **congelata**: `[M]` 1 789
#     sana contro **1 368** congelata, un fattore 1,3.  E' `REVIEWER.md` **E15**.
#     ⇒ Il predicato della scena `vero` guarda **in quest'ordine**:
#        1. i **DISEGNI della scena** (il contatore in `/dev/shm`, che e' la
#           grandezza vera: quanto la scena ha davvero cambiato lo schermo);
#        2. il **RITMO** consegnato — che e' quel che ordina i due estremi;
#        3. i **BYTE per fotogramma** — la colonna di `LEZIONI.md` §1.30, che
#           dice quanto la scena chiedeva, e che da sola non basterebbe.
#     ⚠ Portarne una sola sarebbe un giudizio che sembra un risultato.
BYTE_VERO_VIVI = 600        # ⭐ lo stesso pavimento di `10-b89`: `[M]` un
                            #   fotogramma di desktop FERMO ne pesa 455, e il
                            #   caso buttato di fase 9 ne pesava 242-283
FPS_VERO_MINIMO = 3.0       # ⛔ sotto, gli strappi non stanno arrivando: con
                            #   quiete 1,0 + accensione 0,30 ci sono ~0,77
                            #   strappi al secondo, e ciascuno deve produrre
                            #   piu' di un fotogramma
DISEGNI_VIVI = 2.0          # ⛔ disegni/s della scena sotto i quali «a strappi»
                            #   non e' a strappi: e' ferma
RESA_MINIMA = 0.45          # ⛔ LA RESA: quanti dei disegni della scena
                            #   arrivano al cliente.  `[M]` 24 agosto 2026, a
                            #   macchina scarica la resa e' **0,64** su tutte e
                            #   due le strade misurate — la salita satura
                            #   (pendenza 0,6395) e la manopola a una sessione
                            #   (0,6403).  ⛔ La soglia sta sotto quel valore e
                            #   MOLTO sopra il crollo: `[M]` alla nona sessione
                            #   satura la resa e' 0,023.  ⚠ Non e' «il 45 % va
                            #   bene»: e' «sotto il 45 % il prodotto sta
                            #   perdendo piu' di un terzo di quel che riusciva a
                            #   consegnare a macchina scarica»
FPS_FERMA_MASSIMO = 3.0     # ⛔ sopra, «ferma» NON e' ferma: c'e' un
                            #   salvaschermo, un orologio o una notifica sotto,
                            #   e va DICHIARATO invece di essere contato come
                            #   «il desktop fermo costa zero» (`10-b89` usa 2,0
                            #   su UNA sessione; qui il margine sta un filo piu'
                            #   largo perche' con undici palchi le notifiche di
                            #   sistema arrivano davvero)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA RADICE — un solo `sudo`, e la catena dentro la SUA shell
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ La forma sbagliata e' MUTA, e `09-b70-ritmo.py` la spiega per esteso: un
#    `< file` o un `| grep` in coda non lo prende il comando, lo prende `sudo`,
#    che allora non riceve piu' la parola sullo stdin, esce 1, e un `|| echo 0`
#    trasforma l'errore in un numero plausibile.  `[M]` 23 agosto 2026: un
#    contatore cumulativo dall'accensione del server invece che dal giro —
#    **4 041 invece di 1 604**.
def catena_root(comando):
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (PAROLA_SUDO, shlex.quote(comando)))


def rem(comando, tetto=120):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=120):
    return rem(catena_root(comando), tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA RIDUZIONE SI IMPORTA DA 09-b70 — E POI SI TARA
# ═══════════════════════════════════════════════════════════════════════════
B70 = None


def _importa_b70():
    """⛔ Importare e dare per scontato che l'import abbia funzionato e' la
       forma d'errore che questo progetto ha gia' pagato.  ⇒ Si importa, si
       controlla che ci siano i nomi che servono, e ⛔ **si inietta un giornale
       a valore NOTO e si verifica che il metro lo ritrovi** (`LEZIONI.md`
       §1.33: un metro non tarato produce numeri, non misure).
    """
    perc = os.path.join(QUI, "09-b70-ritmo.py")
    if not os.path.exists(perc):
        raise SystemExit("⛔ NON MISURO: manca «%s», che porta `misura()`" % perc)
    spec = importlib.util.spec_from_file_location("b70", perc)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for nome in ("misura", "_finestra_minima", "_mediana", "CODEC_NUMERO"):
        if not hasattr(m, nome):
            raise SystemExit("⛔ NON MISURO: «%s» non c'e' in 09-b70-ritmo.py"
                             % nome)
    return m


def tara_riduzione(m, dillo=True):
    """⛔ IL METRO SI TARA PRIMA — si inietta un valore noto e si guarda se torna.

    Il giornale iniettato: **200 fotogrammi a esattamente 40 ms l'uno**, di cui
    **20 chiavi** (una ogni dieci), da **10 000 byte** l'uno, con un ritardo
    **noto** di **37,5 ms** fra cattura e arrivo.

    ⭐⭐ E LA TARATURA HA GIA' PAGATO IL SUO PREZZO, la prima volta che e' girata.
        L'atteso che avevo scritto era **25,00** fotogrammi/s: duecento
        fotogrammi a 40 ms sono cinque volte 40 in un secondo.  ⛔ Il metro ne
        ha detti **25,13**, e aveva ragione lui: duecento fotogrammi coprono
        **centonovantanove** intervalli, cioe' 7,960 s, e 200/7,960 = 25,126.
        ⚠ `misura()` di 09-b70 divide i fotogrammi per l'INTERVALLO FRA IL
        PRIMO E L'ULTIMO, non per la durata chiesta ⇒ **sovrastima di
        1/(N−1)**: +0,50 % a 200 fotogrammi, +0,11 % a 900, +0,07 % a 1 400.
        ⭐ Non e' un difetto — e' la definizione — ma e' una **distorsione
        sistematica al rialzo** che va saputa prima di confrontare due gradini
        con un numero diverso di fotogrammi, ed e' esattamente il genere di cosa
        che si scopre tarando e non si scopre leggendo il codice.
        ⇒ L'atteso qui e' l'aritmetica VERA, non quella che sembrava.

    ⇒ Attesi, e sono aritmetica, non opinione:
       200/7,960 = 25,126 fotogrammi/s · 25 nella finestra peggiore ·
       quota delta 0,90 · 10 000 byte/fotogramma · ritardo mediano 37,5 ms ·
       zero buchi nel `numero`.
    """
    QUANTE, PASSO, RIT = 200, 40.0, 37.5
    g = []
    for k in range(QUANTE):
        arrivo = 1000.0 + k * PASSO
        g.append({"numero": 1000 + k, "chiave": (k % 10 == 0), "tipo": 0x0301,
                  "codec": 3, "l": 1920, "a": 1080, "byte": 10000,
                  "istante_us": int((arrivo - RIT) * 1000),
                  "arrivo_ms": arrivo})
    atteso_fps = round(QUANTE / ((QUANTE - 1) * PASSO / 1000.0), 2)
    n = m.misura(g, 8.0, scaldata_s=0.0)
    r = ritardi(g)
    prove = [
        ("fotogrammi/s", n.get("fps"), atteso_fps, 0.01),
        ("finestra peggiore", n.get("fps_finestra_min"), 25.0, 0.01),
        ("quota delta", n.get("quota_delta"), 0.90, 0.001),
        ("byte per fotogramma", n.get("byte_per_fotogramma"), 10000, 1),
        ("buchi nel numero", n.get("buchi_numero"), 0, 0),
        ("ritardo mediano ms", r.get("mediano_ms"), RIT, 0.05),
    ]
    guai = []
    for nome, visto, atteso, tol in prove:
        if visto is None or abs(visto - atteso) > tol:
            guai.append("%s: atteso %s, visto %s" % (nome, atteso, visto))
    if dillo:
        for nome, visto, atteso, _t in prove:
            _inf("taratura · %-20s atteso %-8s visto %s" % (nome, atteso, visto))
    return (len(guai) == 0), guai


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL RITARDO — e la premessa che lo rende misurabile si scrive qui
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `RCP.md` §6.2: *«l'`istante` e' l'orologio monotono del server; il client
#    NON DEVE confrontarlo con il proprio»*.  ⚠ E' una regola per un CLIENT
#    VERO, che sta su un'altra macchina e su un altro orologio.
#
# ⭐ Qui la premessa e' diversa e si dichiara: i dieci clienti girano dentro
#    `enter.sh`, che e' un **chroot con `--rbind`** sullo **stesso kernel** del
#    server (`/media/REMOTIX/enter.sh`, righe 31-40: monta `/proc`, `/sys` e
#    `/dev` dell'host).  ⇒ `CLOCK_MONOTONIC` e' **letteralmente lo stesso
#    contatore** per il server, per i dieci clienti e per la sonda.  La
#    sottrazione e' lecita, ed e' il ritardo **cattura → consegnato sul filo**.
#
# ⛔ E la premessa si CONTROLLA invece di crederci: un ritardo mediano
#    **negativo** vuol dire che i due orologi non sono quelli che credo ⇒ si
#    torna `None` e non si giudica.  ⚠ Cosi' il giorno in cui qualcuno facesse
#    girare i clienti su un'altra macchina, il banco tace invece di scrivere un
#    numero senza senso.
def ritardi(giornale):
    """Cattura → arrivo sul filo, in ms.  ⛔ `None` se la premessa non regge."""
    if not giornale:
        return {"mediano_ms": None, "p95_ms": None, "massimo_ms": None,
                "minimo_ms": None, "quanti": 0,
                "esito": "NON HO NIENTE DA GIUDICARE — giornale vuoto"}
    v = sorted(f["arrivo_ms"] - f["istante_us"] / 1000.0 for f in giornale)
    med = statistics.median(v)
    if med < 0:
        # ⛔ Non e' «ritardo zero»: e' «gli orologi non sono confrontabili».
        return {"mediano_ms": None, "p95_ms": None, "massimo_ms": None,
                "minimo_ms": round(v[0], 1), "quanti": len(v),
                "esito": "⛔ NON GIUDICO — il ritardo mediano e' NEGATIVO "
                         "(%.1f ms): i due orologi non sono lo stesso "
                         "CLOCK_MONOTONIC, e la sottrazione non vuol dire "
                         "niente" % med}
    return {"mediano_ms": round(med, 1),
            "p95_ms": round(v[min(len(v) - 1, int(0.95 * (len(v) - 1)))], 1),
            "massimo_ms": round(v[-1], 1), "minimo_ms": round(v[0], 1),
            "quanti": len(v), "esito": "misurato"}


def conto_scarno(giornale, durata, rifiutato):
    """⭐ IL CONTO POSSIBILE QUANDO LA RIDUZIONE SI RIFIUTA — solo per `ferma`.

    ⛔ Non e' un modo di aggirare il rifiuto di `misura()`: e' il riconoscimento
       che su un desktop **fermo** «pochissimi fotogrammi» e' il RISULTATO, non
       un guasto della prova.  `[M]` §6.4-bis: **un** fotogramma in 40,8 s.

    ⛔ E quel che non si puo' calcolare resta `None` e si vede da fuori:
       · `fps_finestra_min` — il peggior secondo di un secondo solo non esiste;
       · `quota_delta` — con tre fotogrammi «una chiave su tre» non e' una
         spirale, e' aritmetica di numeri piccoli;
       · `buchi_numero` — con due fotogrammi in quarantacinque secondi un salto
         nel `numero` e' quel che il prodotto FA, non un buco.
       ⚠ Ciascuna di queste colonne, messa a zero, avrebbe dato un rosso
         plausibile a un braccio che sta misurando la cosa giusta.
    """
    n = {"esito": "misurato",
         "conto_scarno": "⚠ la riduzione di 09-b70 si e' rifiutata (%s) e ha "
                         "ragione: qui si contano SOLO fotogrammi, byte, chiavi "
                         "e ritardo" % rifiutato.get("esito", "?"),
         "chiesto_s": durata, "fotogrammi_grezzi": len(giornale),
         "fotogrammi": len(giornale), "vissuto_s": None,
         "fps": round(len(giornale) / durata, 4) if durata > 0 else None,
         "fps_finestra_min": None, "quota_delta": None, "buchi_numero": None}
    byte = sum(int(f.get("byte") or 0) for f in giornale)
    n["byte_totali"] = byte
    n["byte_per_fotogramma"] = round(byte / len(giornale)) if giornale else 0
    n["mbit_s_carico"] = round(byte * 8 / durata / 1e6, 4) if durata > 0 else None
    n["chiavi"] = sum(1 for f in giornale if f.get("chiave"))
    n["delta"] = len(giornale) - n["chiavi"]
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL CLIENTE — `01-b3-cliente.py` con UNA funzione sostituita, e non di piu'
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ PERCHE' NON SI USA `--registra`, che pure esiste.
#
#     `01-b3-cliente.py --registra` scrive la traccia di §11.1, ma la tiene
#     **tutta in memoria** fino all'uscita (`Registratore.blocchi`), e
#     `_video_stream` conserva anche i **pixel** di ogni fotogramma
#     (`v_fotogrammi`).  ⚠ `09-b70-ritmo.py` lo dichiara: *«a 20 Mbit/s per 30 s
#     sono ~75 MB»*.  ⇒ Dieci clienti per dieci minuti sarebbero **decine di
#     gigabyte di RAM** — cioe' il banco avvelenerebbe proprio la grandezza che
#     questa fase esiste per misurare, la **memoria**.
#
# ⛔ E c'e' una seconda ragione, che vale anche di piu': la traccia si scrive
#    **all'uscita**.  Un gradino misurato dalla traccia vorrebbe dire fermare i
#    clienti a ogni gradino — cioe' staccare e riattaccare le sessioni, cioe'
#    non avere piu' «chi era gia' dentro».  ⭐ Il giornale, invece, si scrive
#    **mentre la sessione vive**, e i gradini si ritagliano dopo.
#
# ⇒ ⭐ Si sostituisce **una sola** funzione, `Cliente._video_stream`, con una
#   che scrive UNA RIGA per fotogramma e **non tiene niente**.  Tutto il resto
#   di `01-b3-cliente.py` — la stretta di mano, `ATTACCA`, `ADATTA_TELA`, il
#   vaglio dell'audio, i codici d'uscita — resta il suo, non riscritto.
#
# ⚠ E il prezzo si dichiara, sono tre:
#   T1. il giornale NON distingue uno stream **azzerato** (§5.1, forma A) da uno
#       finito con FIN: `aioquic` su questo cammino non lo dice, ed e' lo stesso
#       limite che ha `01-b3-cliente.py` oggi.  ⇒ Gli abbandoni si leggono dal
#       registro del server, non da qui.
#   T2. l'arbitro di §11.1 (`01-b4-validatore.py`) **non entra in questo banco**:
#       non c'e' nessuna traccia da giudicare.  ⇒ Il formato del filo non e'
#       verificato qui; lo verificano i banchi che usano `--registra`.
#   T3. `a_blocchi` dell'audio si limita a 64 voci: senza, dieci clienti che
#       ricevono PCM per dieci minuti terrebbero **oltre un gigabyte**.
CLIENTE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b92-cliente — `01-b3-cliente.py` con UNA funzione sostituita.

⛔ Scrive UNA RIGA per fotogramma finito, subito, e non tiene niente in memoria.
   La riga porta l'orologio MONOTONO della macchina (lo stesso del server e
   della sonda: il contenitore e' un chroot sullo stesso kernel), cosi' i
   gradini si ritagliano dopo, sullo stesso asse dei tempi per tutti i clienti.
"""
import argparse, asyncio, collections, importlib.util, json, os, struct, sys, time


def carica(percorso):
    spec = importlib.util.spec_from_file_location("cli3", percorso)
    m = importlib.util.module_from_spec(spec)
    sys.modules["cli3"] = m
    # ⭐ `__name__` e' «cli3», non «__main__»: il blocco finale di
    #    `01-b3-cliente.py` NON gira, e le classi restano quelle sue.
    spec.loader.exec_module(m)
    return m


class Giornale:
    def __init__(self, percorso):
        self.f = open(percorso, "w", buffering=1)   # riga per riga
        self.scritti = 0
        self.corti = 0

    def riga(self, numero, chiave, tipo, codec, l, a, byte, istante_us):
        # ⛔ `time.clock_gettime(CLOCK_MONOTONIC)` e non `time.time()`: l'ora del
        #    mondo salta (ntp), quella monotona no, ed e' quella del server.
        arrivo = time.clock_gettime(time.CLOCK_MONOTONIC) * 1000.0
        self.f.write(json.dumps({"numero": numero, "chiave": bool(chiave),
                                 "tipo": tipo, "codec": codec, "l": l, "a": a,
                                 "byte": byte, "istante_us": istante_us,
                                 "arrivo_ms": arrivo}) + "\n")
        self.scritti += 1


G = None


def _video_stream(self, sid, dati, fine):
    """⭐ La sostituta.  Stessa lettura di §6.2 di `01-b3-cliente.py:1013`,
       ⛔ ma senza `self.reg` (niente traccia in memoria) e senza
       `self.v_fotogrammi` (niente pixel conservati)."""
    b = self.v_in.setdefault(sid, bytearray())
    b += dati
    if not fine:
        return
    del self.v_in[sid]
    if len(b) < 28:
        # ⚠ Non e' un fotogramma e non e' niente: si conta a parte.
        G.corti += 1
        return
    tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI",
                                                            bytes(b[:28]))
    G.riga(numero, tipo == 0x0301, tipo, codec, l, a, len(b) - 28, istante)


class Argomenti:
    """⛔ Un campo che il cliente chiede e io non ho dichiarato ALZA.

    ⚠ `01-b3-cliente.py` costruisce i suoi argomenti nel blocco `__main__`, che
      qui non gira.  ⇒ Li dichiaro io, uno per uno.  Il giorno in cui quel file
      ne aggiungesse uno, questo cliente muore con un `AttributeError` che dice
      il nome — che e' quel che deve fare: **indovinare un predefinito sarebbe
      misurare una configurazione che nessuno ha chiesto**.
    """
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __getattr__(self, n):
        raise AttributeError(
            "⛔ `01-b3-cliente.py` chiede l'argomento «%s», che questo "
            "involucro non dichiara: aggiungilo invece di indovinarlo" % n)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--cliente", required=True, help="01-b3-cliente.py")
    p.add_argument("--giornale", required=True)
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--utente", required=True)
    p.add_argument("--parola-file", required=True)
    p.add_argument("--tela", default="1920x1080")
    p.add_argument("--video-codec", default="h264")
    p.add_argument("--audio-codec", default="pcm")
    p.add_argument("--resta", type=float, default=60.0)
    p.add_argument("--segnale", default="")
    a = p.parse_args()

    global G
    G = Giornale(a.giornale)
    m = carica(a.cliente)
    m.Cliente._video_stream = _video_stream

    lar, alt = (int(x) for x in a.tela.lower().split("x"))
    with open(a.parola_file) as f:
        parola = f.read().strip()

    arg = Argomenti(
        indirizzo=a.indirizzo, porta=a.porta, percorso="/rcp/1",
        utente=a.utente, parola=parola,
        larghezza=lar, altezza=alt, disposizione="it",
        registra=None, adatta=[(lar, alt, 0.0)], vista=None,
        puntatore_vecchia=None, chiave_dopo=0, attesa_tela=10.0,
        video_scrivi="", video_codec=a.video_codec, video_profondita="8,10",
        audio_codec=a.audio_codec, audio_scrivi="",
        appunti_copia="", appunti_attendi=0, appunti_scrivi="",
        resta=a.resta, vivo=0, segnale=(a.segnale or None))

    # ⛔ T3: l'audio non deve crescere.  `a_blocchi` e' una lista che cresce a
    #    ogni blocco (`01-b3-cliente.py:1093`) e nessuno la svuota.
    vecchio_init = m.Cliente.__init__

    def init(self, *args, **kw):
        vecchio_init(self, *args, **kw)
        self.a_blocchi = collections.deque(maxlen=64)
    m.Cliente.__init__ = init

    try:
        rc = asyncio.run(m.principale(arg))
    except Exception as e:
        print("   ⛔ %s: %s" % (type(e).__name__, e), flush=True)
        rc = 2
    print("   [giornale] %d fotogrammi scritti in %s (%d stream corti)"
          % (G.scritti, a.giornale, G.corti), flush=True)
    G.f.close()
    return rc


if __name__ == "__main__":
    sys.exit(principale())
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA FETTA — il ritaglio di un gradino, e gira SULLA MACCHINA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il giornale di dieci minuti a 60 fps e' ~4 MB per cliente: portarlo intero
#    sull'ssh a ogni gradino sarebbe mezzo giga di rete per dieci fette.  ⇒ Si
#    ritaglia sul posto e si comprime.
FETTA = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b92-fetta — ritaglia da un giornale la finestra [t0, t1] in ms monotoni.

⛔ IL RITAGLIO E' L'ANCORA (vedi `p_ancora` nel banco): il gradino N vede SOLO i
   fotogrammi arrivati fra `t0` e `t1`, e `t0` viene letto dall'orologio della
   macchina **dopo** che il gradino N-1 e' finito.  ⇒ Leggere il gradino
   precedente non e' un errore da evitare: e' impossibile.
"""
import json, sys

percorso, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
g, righe, fuori = [], 0, 0
try:
    with open(percorso) as f:
        for riga in f:
            righe += 1
            try:
                v = json.loads(riga)
            except Exception:
                continue           # ⚠ l'ultima riga puo' essere a meta'
            if t0 <= v["arrivo_ms"] <= t1:
                g.append(v)
            else:
                fuori += 1
except FileNotFoundError:
    # ⛔ «Il file non c'e'» non e' «zero fotogrammi»: sono due cose diverse
    #    (`CODER.md` §3.10) e il banco deve poterle distinguere.
    print(json.dumps({"esito": "NIENTE DA LEGGERE — il giornale «%s» non "
                               "esiste" % percorso}))
    sys.exit(0)
g.sort(key=lambda x: x["arrivo_ms"])
print(json.dumps({"esito": "letto", "righe_nel_file": righe,
                  "fuori_finestra": fuori, "giornale": g}))
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA SONDA — UNA fotografia della macchina, in un istante solo
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Perche' una sola fotografia e non cinque comandi: cinque `ssh` sono cinque
#    istanti diversi, e la memoria, la GPU, la CPU e i byte sul filo di cinque
#    istanti diversi non fanno un ritratto — fanno un collage.
#
# ⛔⛔ LA MEMORIA E' **PSS**, e non e' un dettaglio.  Dieci `gnome-shell`
#     condividono le stesse librerie e le stesse pagine di sola lettura: la
#     somma dei dieci `RSS` conta quelle pagine **dieci volte**.  ⭐ Il `Pss` di
#     `/proc/<pid>/smaps_rollup` divide ogni pagina condivisa fra chi la usa, e
#     la somma dei `Pss` **e'** la memoria vera.  ⚠ La differenza fra i due
#     numeri e' proprio quel che si vuole sapere quando si chiede «quanto costa
#     la decima sessione»: si stampano tutt'e due.
#
# ⛔⛔ LA GPU SI DEDUPLICA PER `drm-client-id`, o si conta piu' volte.  Un
#     processo tiene lo stesso contesto DRM aperto su piu' descrittori: `[M]` 24
#     agosto 2026, `gnome-shell` mostrava **quattro** descrittori su
#     `renderD128` con lo **stesso** `drm-client-id 291` e lo stesso
#     `drm-engine-render: 440141676 ns`.  Sommare gli fdinfo darebbe **quattro
#     volte** l'occupazione vera.  ⇒ Chiave `(pdev, client-id)`, e si tiene una
#     voce sola.
SONDA = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b92-sonda — una fotografia della macchina: orologio, GPU, PSS, CPU, filo.

⛔ Va eseguita DA ROOT: `smaps_rollup` e gli `fdinfo` altrui non si leggono da
   utente, e una lettura NEGATA non e' una lettura che dice zero (`CODER.md`
   §3.10).  ⇒ Ogni sezione porta il conto di quel che NON ha potuto leggere.
"""
import json, os, sys, time

PDEV = sys.argv[1] if len(sys.argv) > 1 else "0000:00:02.0"
UID_MIEI = set(int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []))
UNITA = sys.argv[3] if len(sys.argv) > 3 else ""


def pids():
    for n in os.listdir("/proc"):
        if n.isdigit():
            yield int(n)


def leggi(p):
    try:
        with open(p) as f:
            return f.read()
    except Exception:
        return None


def uid_di(pid):
    t = leggi("/proc/%d/status" % pid)
    if not t:
        return None
    for r in t.splitlines():
        if r.startswith("Uid:"):
            return int(r.split()[1])
    return None


t_inizio = time.clock_gettime(time.CLOCK_MONOTONIC)
fuori = {"t_ms": t_inizio * 1000.0, "ora": time.time()}

# ── CPU della macchina ────────────────────────────────────────────────────
st = leggi("/proc/stat") or ""
cpu = st.splitlines()[0].split() if st else []
if cpu and cpu[0] == "cpu":
    v = [int(x) for x in cpu[1:11]]
    fuori["cpu"] = {"totale": sum(v), "inattivo": v[3] + v[4], "nuclei": os.cpu_count()}
else:
    fuori["cpu"] = {"esito": "⛔ /proc/stat non letto"}

# ── I byte sul filo ───────────────────────────────────────────────────────
rete = {}
nd = leggi("/proc/net/dev") or ""
for r in nd.splitlines()[2:]:
    nome, _, resto = r.partition(":")
    c = resto.split()
    if len(c) >= 16:
        rete[nome.strip()] = {"rx_byte": int(c[0]), "rx_pacchetti": int(c[1]),
                              "tx_byte": int(c[8]), "tx_pacchetti": int(c[9])}
fuori["rete"] = rete

# ── I processi: uid, cpu, rss, pss ────────────────────────────────────────
#    ⛔ `smaps_rollup` costa: si legge SOLO per i processi che interessano —
#       i miei uid piu' l'albero del mio server.  Leggerlo per tutte le
#       centinaia di pid della macchina raddoppierebbe il costo della sonda, e
#       il costo della sonda entra nella misura che la sonda fa.
albero = set()
if UNITA:
    t = leggi("/sys/fs/cgroup/system.slice/%s.service/cgroup.procs" % UNITA)
    if t:
        albero = set(int(x) for x in t.split())
fuori["albero_server"] = sorted(albero)

proc = {"per_uid": {}, "server": {"pss_kib": 0, "rss_kib": 0, "cpu_jiffies": 0,
                                  "quanti": 0},
        "clienti": {"pss_kib": 0, "rss_kib": 0, "cpu_jiffies": 0, "quanti": 0},
        "negati": 0, "letti": 0}
for pid in pids():
    u = uid_di(pid)
    if u is None:
        continue
    mio = u in UID_MIEI
    del_server = pid in albero
    # ⭐ I clienti girano da root dentro il contenitore e si riconoscono dalla
    #    riga di comando: e' l'unico modo, e si dichiara.
    cmd = (leggi("/proc/%d/cmdline" % pid) or "").replace("\x00", " ")
    cliente = "10-b92-cliente.py" in cmd
    if not (mio or del_server or cliente):
        continue
    stat = leggi("/proc/%d/stat" % pid)
    jif = 0
    if stat:
        c = stat.rpartition(") ")[2].split()
        if len(c) > 13:
            jif = int(c[11]) + int(c[12])      # utime + stime
    roll = leggi("/proc/%d/smaps_rollup" % pid)
    pss = rss = None
    if roll:
        for r in roll.splitlines():
            if r.startswith("Pss:"):
                pss = int(r.split()[1])
            elif r.startswith("Rss:"):
                rss = int(r.split()[1])
    if pss is None:
        proc["negati"] += 1
    else:
        proc["letti"] += 1
    dove = None
    if cliente:
        dove = proc["clienti"]
    elif del_server:
        dove = proc["server"]
    if dove is not None:
        dove["pss_kib"] += pss or 0
        dove["rss_kib"] += rss or 0
        dove["cpu_jiffies"] += jif
        dove["quanti"] += 1
    if mio:
        d = proc["per_uid"].setdefault(str(u), {"pss_kib": 0, "rss_kib": 0,
                                                "cpu_jiffies": 0, "quanti": 0})
        d["pss_kib"] += pss or 0
        d["rss_kib"] += rss or 0
        d["cpu_jiffies"] += jif
        d["quanti"] += 1
fuori["processi"] = proc

# ── LA GPU: fdinfo di i915, deduplicato per (pdev, drm-client-id) ─────────
gpu = {"motori": {}, "capacita": {}, "clienti": 0, "per_uid": {},
       "per_contesto": {}, "contesti_miei": {},
       "altri_pdev": {}, "estranei": 0, "estranei_pid": []}
visti = set()
for pid in pids():
    d = "/proc/%d/fd" % pid
    try:
        fds = os.listdir(d)
    except Exception:
        continue
    for fd in fds:
        try:
            b = os.readlink(os.path.join(d, fd))
        except Exception:
            continue
        if "/dev/dri/" not in b:
            continue
        t = leggi("/proc/%d/fdinfo/%s" % (pid, fd))
        if not t:
            continue
        campi = {}
        for r in t.splitlines():
            k, _, v = r.partition(":")
            campi[k.strip()] = v.strip()
        pdev = campi.get("drm-pdev")
        cid = campi.get("drm-client-id")
        if not pdev or not cid:
            continue
        if pdev != PDEV:
            # ⛔ La discreta e' chiusa da una regola udev
            #    (`DECISIONI.md` §4.6-quinquies): se compare, si DICHIARA e non
            #    si somma.  Sommare vorrebbe dire misurare su due schede
            #    credendo di misurarne una.
            gpu["altri_pdev"][pdev] = gpu["altri_pdev"].get(pdev, 0) + 1
            continue
        chiave = (pdev, cid)
        if chiave in visti:
            continue                    # ⭐ la deduplicazione che vale 4x
        visti.add(chiave)
        gpu["clienti"] += 1
        u = uid_di(pid)
        mio = u in UID_MIEI
        if not mio and pid not in albero:
            gpu["estranei"] += 1
            if len(gpu["estranei_pid"]) < 12:
                gpu["estranei_pid"].append(
                    [pid, (leggi("/proc/%d/comm" % pid) or "?").strip(), u])
        for k, v in campi.items():
            # ⛔⛔ `drm-engine-capacity-video: 2` NON E' UN TEMPO, E' UN CONTO.
            #
            #     ⚠ Comincia per `drm-engine-` come gli altri, e chi lo somma
            #       insieme ai nanosecondi si ritrova un motore fantasma
            #       chiamato «capacity-video» che sta sempre allo 0,0 % — cioe'
            #       un numero plausibile e senza senso.  ⭐ E quel 2 e' la cosa
            #       piu' importante della riga: **i VDBOX di questa scheda sono
            #       DUE**, quindi il motore `video` puo' arrivare al **200 %**
            #       del tempo di parete, e un tetto messo a 100 darebbe rosso
            #       proprio quando la scheda comincia a lavorare sul serio.
            #     ⇒ Il fatto e' di `banchi/10-b87-metro-gpu.py` (agente A2, 24
            #       agosto 2026), che l'ha verificato guardando il file su
            #       questo kernel.  Qui si legge, non si riscrive la sua tabella.
            if k.startswith("drm-engine-capacity-"):
                m = k[len("drm-engine-capacity-"):]
                try:
                    gpu["capacita"][m] = max(gpu["capacita"].get(m, 1),
                                             int(v.split()[0]))
                except (ValueError, IndexError):
                    pass
                continue
            if k.startswith("drm-engine-"):
                m = k[len("drm-engine-"):]
                ns = int(v.split()[0]) if v.split() and v.split()[0].isdigit() else 0
                gpu["motori"][m] = gpu["motori"].get(m, 0) + ns
                # ⛔⛔ E ANCHE PER CONTESTO, che e' la sola forma in cui quei
                #     nanosecondi si possono SOTTRARRE.  Vedi il riquadro di
                #     `fra()`: la somma su una platea che cambia non e' un delta.
                gpu["per_contesto"].setdefault(cid, {})[m] = ns
                if mio:
                    gpu["per_uid"].setdefault(str(u), {})
                    gpu["per_uid"][str(u)][m] = \
                        gpu["per_uid"][str(u)].get(m, 0) + ns
        gpu["contesti_miei"][cid] = bool(mio)
# ⭐⭐ E IL CONTESTO DELLA GT, che senza il banco misura una grandezza che si
#     muove sotto i piedi.  `banchi/10-b87-metro-gpu.py` §CLOCK, `[M]` 24 agosto
#     2026: **la stessa identica codifica** (30,9 fotogrammi/s consegnati in
#     tutt'e due i casi) da' `video = 26,35 %` con la GT a 300 MHz e `6,99 %`
#     con la GT a 1550 MHz — un fattore **3,8**.  ⛔ `drm-engine-*` conta il
#     TEMPO OCCUPATO, non il LAVORO FATTO, e il governatore muove la frequenza
#     col carico.  ⇒ Un'occupazione letta a carico leggero SOVRASTIMA, e il
#     numero di sessioni che ci stanno non si estrapola da un carico leggero.
# ⭐ `rc6_residency_ms` e' una SECONDA misura, indipendente dagli fdinfo: quanto
#    la GT e' stata del tutto spenta.  `100 − rc6` fa da tetto superiore.
def _intero(p):
    t = leggi(p)
    try:
        return int((t or "").strip())
    except ValueError:
        return None


fuori["gt"] = {"cur_mhz": _intero("/sys/class/drm/card0/gt_cur_freq_mhz"),
               "act_mhz": _intero("/sys/class/drm/card0/gt_act_freq_mhz"),
               "min_mhz": _intero("/sys/class/drm/card0/gt_min_freq_mhz"),
               "max_mhz": _intero("/sys/class/drm/card0/gt_max_freq_mhz"),
               "rc6_ms": _intero("/sys/class/drm/card0/gt/gt0/rc6_residency_ms")}
fuori["gpu"] = gpu

# ⭐ E LA SONDA DICHIARA QUANTO PESA: il suo costo entra nella misura che fa.
fuori["costo_ms"] = round(
    (time.clock_gettime(time.CLOCK_MONOTONIC) - t_inizio) * 1000.0, 1)
print(json.dumps(fuori))
'''



# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL LETTORE DEL REGISTRO — una passata sola su cento megabyte
# ═══════════════════════════════════════════════════════════════════════════
CONTI = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b92-conti — i conti del server nella finestra [riga0, riga1], IN UNA PASSATA.

⛔ La finestra e' un intervallo di RIGHE, non di tempo: le righe di partenza e
   d'arrivo le legge il banco con `wc -l` prima e dopo il gradino.  Senza, i
   conti sarebbero cumulativi dall'accensione del server — il difetto che in
   fase 9 e' costato 4 041 invece di 1 604.

⛔⛔ E UNA PASSATA SOLA, che non e' eleganza: con undici sessioni a 60
    fotogrammi/s il server scrive una riga per fotogramma spedito, e in venti
    minuti il registro passa i cento megabyte.  Otto `tail | head | grep` per
    gradino sarebbero piu' di un giga di lettura per un pugno di numeri.
"""
import json
import re
import sys

percorso, r0, r1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
# ⛔⭐ IL CONFINE E' UNA POSIZIONE IN BYTE, non un numero di riga — e la ragione
#     e' una misura: con undici sessioni a 60 fotogrammi/s il server scrive una
#     riga per fotogramma spedito, `[M]` ~130 KB/s, cioe' oltre CENTO MEGABYTE
#     in venti minuti.  Contare le righe per ritrovare il confine vorrebbe dire
#     scorrere tutto il file a ogni gradino: undici volte cento megabyte, dentro
#     il giro che sta misurando.  ⇒ `seek()`, che costa zero.
# ⚠ E il prezzo si dichiara: la prima riga letta puo' essere TAGLIATA A META' se
#   il confine e' caduto in mezzo a una riga.  Non e' un problema — nessuna
#   delle espressioni qui sotto puo' agganciarsi a mezza riga — ma va saputo.

RETE = re.compile(r"rete-quic (\S+) .*?persi_d=(\d+) .*?spediti_d=(\d+) "
                  r".*?byte_spediti=(\d+) .*?cwnd=(\d+) .*?srtt_us=(\d+)")
CICLO = re.compile(r"ciclo: (\d+) fotogrammi consegnati \((\d+) chiavi\), "
                   r"(\d+) attese a vuoto")
RITMO = re.compile(r"(\d+)/s chiesti")
SPIRALE = (("chiave_aspetta", "§5.2 vieta di abbandonarla"),
           ("delta_non_spedito", "FOTOGRAMMA NON SPEDITO"),
           ("abbandonato_in_coda", "ABBANDONATO NELLA CODA"),
           ("involo_pieno", "NON potra' essere abbandonato"))

per_prov = {}
spirale = dict((k, 0) for k, _ in SPIRALE)
ciclo_primo, ciclo_ultimo, righe_ciclo = None, None, 0
ritmo, negati, occupati, lette = None, [], None, 0
try:
    # ⛔ IN BINARIO, e il tratto si legge TUTTO IN UNA VOLTA.
    #
    # ⚠ La strada che sembrava ovvia — aprire in testo, `seek(r0)` e poi
    #   `for riga in f` guardando `f.tell()` — **alza**: su un file di testo
    #   `tell()` dentro un ciclo di lettura da `ValueError: telling position
    #   disabled by next() call`, perche' l'iteratore legge avanti a blocchi.
    #   ⇒ Si prende il tratto in byte e lo si spezza in righe qui: a 130 KB/s
    #     un gradino da quarantacinque secondi sono sei megabyte, che stanno in
    #     memoria senza pensarci.
    with open(percorso, "rb") as f:
        f.seek(r0)
        tratto = f.read(max(0, r1 - r0))
    if True:
        for riga in tratto.decode("utf-8", "replace").splitlines():
            lette += 1
            if "rete-quic " in riga:
                m = RETE.search(riga)
                if m:
                    d = per_prov.setdefault(m.group(1),
                                            {"righe": 0, "spediti_d": 0,
                                             "persi_d": 0, "byte_primo": None,
                                             "byte_ultimo": 0, "cwnd": [],
                                             "srtt_us": []})
                    d["righe"] += 1
                    d["persi_d"] += int(m.group(2))
                    d["spediti_d"] += int(m.group(3))
                    b = int(m.group(4))
                    if d["byte_primo"] is None:
                        d["byte_primo"] = b
                    d["byte_ultimo"] = b
                    d["cwnd"].append(int(m.group(5)))
                    d["srtt_us"].append(int(m.group(6)))
                continue
            if "ciclo: " in riga:
                m = CICLO.search(riga)
                if m:
                    righe_ciclo += 1
                    v = [int(x) for x in m.groups()]
                    if ciclo_primo is None:
                        ciclo_primo = v
                    ciclo_ultimo = v
                    if ritmo is None:
                        r = RITMO.search(riga)
                        if r:
                            ritmo = int(r.group(1))
                continue
            if "posto NEGATO" in riga:
                negati.append(riga.strip()[-200:])
            if "occupati adesso: " in riga:
                m = re.search(r"occupati adesso: (\d+)", riga)
                if m:
                    occupati = int(m.group(1))
            for chiave, aco in SPIRALE:
                if aco in riga:
                    spirale[chiave] += 1
except FileNotFoundError:
    print(json.dumps({"esito": "NIENTE DA LEGGERE — il registro non c'e'"}))
    sys.exit(0)

fuori = {"esito": "letto", "byte0": r0, "byte1": r1, "righe_lette": lette,
         "per_provenienza": per_prov, "spirale_in_somma": spirale,
         "ritmo_chiesto": ritmo, "posti_negati": negati[:5],
         "posti_occupati": occupati}
# ⚠ Le righe `ciclo:` NON portano il nome del figlio: con dieci figli che
#   appendono allo stesso registro si mescolano.  ⇒ Si riferiscono IN SOMMA, e
#   la somma si DICHIARA tale, invece di far credere che sia di qualcuno.
if righe_ciclo >= 2:
    fuori["cattura_in_somma"] = {
        "righe_ciclo": righe_ciclo,
        "avvertenza": "⚠ somma di TUTTI i figli: le righe «ciclo:» non "
                      "dicono di chi sono (figlio.c:7343)",
        "attese_a_vuoto_prima": ciclo_primo[2],
        "attese_a_vuoto_dopo": ciclo_ultimo[2]}
else:
    fuori["cattura_in_somma"] = {"esito": "NIENTE DA LEGGERE — meno di due "
                                          "righe «ciclo:» nella finestra"}
print(json.dumps(fuori))
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL QUINTO ATTREZZO — LE TRE SCENE, e il contatore che dice quanto la
#     scena ha DAVVERO cambiato lo schermo
# ═══════════════════════════════════════════════════════════════════════════
SCENE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b92-scene — le tre scene di undici utenti, e il loro contatore di DISEGNI.

⛔ Gira DA ROOT sulla macchina: `setpriv` fa scendere all'uid della sessione,
   che e' l'unico che possa parlare col suo compositore.

⛔⛔ E LO `shm` E' PER UTENTE.  `/dev/shm` e' UNO su tutta la macchina: due
    sessioni con lo stesso nome si leggerebbero i disegni a vicenda, e **nessuna
    delle due darebbe rosso** — darebbero un numero plausibile.

⭐ IL CONTATORE `disegni` E' LA GRANDEZZA CHE LA FASE CERCA.  Il registro del
   server dice quanti fotogrammi sono **usciti**; questo dice quanti ne ha
   **chiesti la scena**.  Fra i due c'e' tutto quel che il prodotto fa, e senza
   il primo non si puo' dire *«il costo cresce con quanto il desktop cambia»*:
   si potrebbe solo dire *«il costo cresce col costo»*.

   ⛔ E si legge col SEQLOCK (`03-marca.py`, campo `seq`): un campione con `seq`
     dispari e' meta' nuovo e meta' vecchio, e va riletto, non usato.

uso (da root):
  scene.py accendi <i> <uid> <utente> <scena> <shm> <monitor|-> <WxH> <scenabin> <lav>
  scene.py strappi <pid> <quiete> <accensione> <marchio>     ⭐ il ciclo STOP/CONT
  scene.py spegni  <uid>[,<uid>…]
  scene.py conta   <uid1,uid2,…>
  scene.py disegni <shm1,shm2,…>
"""
import json, os, signal, struct, subprocess, sys, time

# ⛔ Copiato alla lettera da `banchi/03-marca.py` e `09-b71-agente.py`, che sono
#    i lettori certificati.  Una copia che diverge e' un lettore che mente.
FORMATO = "<4I Q 5Q 5Q 10I i 3I 64s 32s 64s 64s 4Q 4I"
TAGLIA = struct.calcsize(FORMATO)
I_SEQ, I_DISEGNI = 4, 5
I_LARG, I_ALT, I_PID = 16, 17, 25

# ⛔⛔ LA CLASSE DI CARATTERI NON E' UN VEZZO.  `pkill -f 'nautilus|…'` lanciato
#     da una shell la cui riga di comando CONTIENE «nautilus» ammazza la shell
#     stessa, e la pulizia finisce a meta' **in silenzio**.  `[/]` e `[a]`
#     combaciano col processo vero e non col testo del modello.
FINESTRE = "nautilu[s]|gnome-termina[l]"


def giu(uid, utente, argomenti, log):
    """L'ambiente si COMPONE da zero, una variabile per volta (`CODER.md` §4.5)."""
    riga = ("setsid nohup setpriv --reuid=%d --regid=%d --init-groups "
            "env -i HOME=/home/%s USER=%s LANG=C.UTF-8 "
            "PATH=/usr/local/bin:/usr/bin:/bin XDG_RUNTIME_DIR=/run/user/%d "
            "WAYLAND_DISPLAY=wayland-0 GDK_BACKEND=wayland "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus %s >>%s 2>&1 &"
            % (uid, uid, utente, utente, uid, uid, argomenti, log))
    subprocess.run(["bash", "-c", riga])


def quanti(modello, uid):
    p = subprocess.run(["pgrep", "-u", str(uid), "-c", "-f", modello],
                       capture_output=True)
    t = p.stdout.decode().strip()
    return int(t) if t.isdigit() else 0


def esc(uid, lav):
    """⛔ La sessione headless di GNOME sta nella VISTA D'INSIEME e ci resta: le
       finestre sarebbero **anteprime rimpicciolite** (`09-b72`, 23 agosto).
       ⚠ Torna `None` se non ha potuto mandarlo: «non ho premuto» non e'
       «premuto senza effetto»."""
    try:
        p = subprocess.run(["python3", "%s/09-b72-tasto.py" % lav,
                            "--uid", str(uid), "--tasti", "1"],
                           capture_output=True, timeout=90)
    except Exception:
        return None
    return "TASTI MANDATI" in p.stdout.decode("utf-8", "replace")


def leggi_shm(nome):
    """⛔ `None` se non si e' letto: «non ho misurato» non e' «zero disegni»."""
    perc = "/dev/shm/" + nome
    try:
        with open(perc, "rb") as f:
            crudo = f.read(TAGLIA)
    except Exception as e:
        return {"esito": "non letto: %s" % e}
    if len(crudo) < TAGLIA:
        return {"esito": "blocco troncato (%d byte su %d)" % (len(crudo), TAGLIA)}
    for _ in range(200):
        a = struct.unpack(FORMATO, crudo)
        if a[I_SEQ] % 2 == 0:
            with open(perc, "rb") as f:
                b = struct.unpack(FORMATO, f.read(TAGLIA))
            if b[I_SEQ] == a[I_SEQ]:
                return {"disegni": a[I_DISEGNI], "larghezza": a[I_LARG],
                        "altezza": a[I_ALT], "pid": a[I_PID], "seq": a[I_SEQ]}
        time.sleep(0.0005)
        with open(perc, "rb") as f:
            crudo = f.read(TAGLIA)
    # ⛔⛔ LA TRAPPOLA DEL SEQLOCK QUANDO SI CONGELA IL SUO SCRITTORE — ed e'
    #     scritta per esteso in `09-b71-agente.py`, che l'ha pagata per primo.
    #
    #     La scena della scena «vero» sta in `SIGSTOP` per i tre quarti del
    #     tempo, ed e' voluto: sono gli STRAPPI.  Se il segnale e' caduto in
    #     mezzo a `stato_pubblica()`, `seq` resta DISPARI per tutta la quiete.
    #     ⚠ Un lettore che si rifiutasse e basta direbbe «non ho letto» sui tre
    #       quarti dei campioni, e il braccio «vero» non avrebbe piu' la
    #       colonna che lo giudica.
    #
    # ⭐ La cura e' quella di 09-b71: a scrittore FERMO la memoria **non cambia
    #    piu'**, quindi il campione e' stabile anche se incoerente.  ⇒ Si legge
    #    due volte a 5 ms di distanza: se e' identico, il blocco e' fermo e il
    #    contatore vale, sbagliato **al piu' di un disegno** su decine di
    #    migliaia.  ⛔ E il fatto si dichiara nel risultato, non si nasconde.
    with open(perc, "rb") as f:
        a1 = f.read(TAGLIA)
    time.sleep(0.005)
    with open(perc, "rb") as f:
        a2 = f.read(TAGLIA)
    if a1 == a2 and len(a1) == TAGLIA:
        a = struct.unpack(FORMATO, a1)
        return {"disegni": a[I_DISEGNI], "larghezza": a[I_LARG],
                "altezza": a[I_ALT], "pid": a[I_PID], "seq": a[I_SEQ],
                "campione_congelato": True}
    return {"esito": "seq sempre dispari E il blocco cambia: campione mai "
                     "coerente, e non e' nemmeno fermo"}


passo = sys.argv[1]

if passo == "disegni":
    # ⛔ L'ORA LA PORTA LA LETTURA STESSA, e sullo STESSO orologio monotono
    #    dell'ancora della sonda: dividere i disegni per la durata CHIESTA del
    #    gradino invece che per quella VERA e' come contare i fotogrammi di una
    #    finestra e i secondi di un'altra.
    fuori = {"t_ms": round(time.clock_gettime(time.CLOCK_MONOTONIC) * 1000, 3)}
    for nome in sys.argv[2].split(","):
        if nome:
            fuori[nome] = leggi_shm(nome)
    print(json.dumps(fuori))

elif passo == "conta":
    fuori = {}
    for t in sys.argv[2].split(","):
        if not t:
            continue
        u = int(t)
        fuori[t] = {
            "scena": quanti("04-b30-scen[a] --", u),
            "finestre": quanti(FINESTRE, u),
            "palco": quanti("gnome-shel[l]|mutte[r]|gnome-sessio[n]", u),
            # ⛔ Il ciclo degli strappi gira DA ROOT (deve mandare i segnali):
            #    non si conta per uid, si conta per marchio.
        }
    p = subprocess.run(["pgrep", "-a", "-f", "10-b92-scene[.]py strappi"],
                       capture_output=True)
    marchi = {}
    for r in p.stdout.decode().splitlines():
        pezzi = r.split()
        if len(pezzi) >= 7:
            marchi[pezzi[-1]] = marchi.get(pezzi[-1], 0) + 1
    for t in fuori:
        fuori[t]["strappi"] = marchi.get(t, 0)
    print(json.dumps(fuori))

elif passo == "strappi":
    # ⭐ IL CICLO DELLO STRAPPO, ed e' lo stimolo di `09-b71`: `SIGSTOP`/
    #    `SIGCONT`.  ⛔ Non aggiunge niente al conto — la scena non nasce, non
    #    negozia nessuna superficie nuova: **riprende a disegnare**, che e' quel
    #    che fa un desktop vero quando l'utente trascina una finestra.
    pid, quiete, accensione = int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    while True:
        try:
            os.kill(pid, 0)
        except OSError:
            break
        try:
            os.kill(pid, signal.SIGSTOP)
            time.sleep(quiete)
            os.kill(pid, signal.SIGCONT)
            time.sleep(accensione)
        except OSError:
            break

elif passo == "spegni":
    for t in sys.argv[2].split(","):
        if not t:
            continue
        u = int(t)
        subprocess.run(["pkill", "-u", t, "-f", "04-b30-scen[a]"])
        subprocess.run(["pkill", "-u", t, "-f", FINESTRE])
        subprocess.run(["bash", "-c",
                        "pkill -f '10-b92-scene[.]py strappi .* %s$' ; true" % t])
    # ⛔ E un processo CONGELATO non muore col `SIGTERM`: se il ciclo degli
    #    strappi e' stato ucciso mentre la scena era in `SIGSTOP`, la scena
    #    resterebbe ferma per sempre.  ⇒ prima `SIGCONT`, poi `-9`.
    time.sleep(0.6)
    for t in sys.argv[2].split(","):
        if t:
            subprocess.run(["bash", "-c",
                            "pkill -CONT -u %s -f '04-b30-scen[a]'; "
                            "pkill -9 -u %s -f '04-b30-scen[a]|%s'; true"
                            % (t, t, FINESTRE)])
    print("SPENTO")

elif passo == "accendi":
    (i, uid, utente, scena, shm, monitor, finestra, scenabin, lav) = (
        int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5],
        sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9], sys.argv[10])
    log = "%s/scena-%d.log" % (lav, i)
    fuori = {"scena": scena, "i": i}

    # ⭐ CHE COSA C'ERA PRIMA — si CONTA prima di spegnere.  ⚠ Spegnere e poi
    #    contare zero non prova niente: proverebbe solo che `pkill` funziona.
    fuori["trovati_prima"] = quanti("04-b30-scen[a]|%s" % FINESTRE, uid)
    # ⛔ Si parte SEMPRE da terra: quel che e' rimasto acceso dal giro prima non
    #    e' «la scena di adesso», e non darebbe rosso — darebbe un numero.
    subprocess.run(["bash", "-c",
                    "pkill -CONT -u %d -f '04-b30-scen[a]'; "
                    "pkill -u %d -f '04-b30-scen[a]|%s'; "
                    "pkill -f '10-b92-scene[.]py strappi .* %d$'; true"
                    % (uid, uid, FINESTRE, uid)])
    time.sleep(1.2)

    if scena == "ferma":
        # ⛔ «ferma» non e' «una scena che non si muove»: e' NESSUNA scena, e si
        #    VERIFICA che non sia rimasto niente acceso.
        vivi = quanti("04-b30-scen[a]|%s" % FINESTRE, uid)
        fuori["esci_dalla_vista"] = esc(uid, lav)
        fuori["disegnano"] = vivi
        fuori["ok"] = (vivi == 0)
        fuori["detto"] = ("nessuna scena, nessuna finestra (ne avevo trovati %d "
                          "dal giro prima)" % fuori["trovati_prima"]
                          if vivi == 0
                          else "⛔ «ferma» NON e' ferma: %d processi che "
                               "disegnano sono rimasti accesi" % vivi)
        print(json.dumps(fuori))
        sys.exit(0 if vivi == 0 else 1)

    if scena == "vero":
        # 1. le finestre VERE, e si CONTA chi e' vivo: un'applicazione che muore
        #    subito e una che non c'e' hanno la stessa faccia (`LEZIONI.md` §1.9)
        for a in ("nautilus", "gnome-terminal"):
            giu(uid, utente, a, log)
        time.sleep(6.0)
        fuori["finestre_vive"] = quanti(FINESTRE, uid)
        if fuori["finestre_vive"] == 0:
            fuori["ok"] = False
            fuori["detto"] = "⛔ nessuna finestra viva: «desktop vero» sarebbe " \
                             "uno schermo vuoto con una scena sopra"
            print(json.dumps(fuori))
            sys.exit(1)
        argomenti = ("%s --finestra %s --movimento pieno --shm /%s --giro b92-%d"
                     % (scenabin, finestra, shm, i))
    else:
        # `satura`: la strada del PRIMO GIRO, riga per riga.  ⛔ Nessun ESC,
        #  nessuna finestra, nessuno strappo: un'ancora «migliorata» non e' piu'
        #  un'ancora.
        argomenti = ("%s --uscita %s --movimento pieno --shm /%s --giro b92-%d"
                     % (scenabin, monitor, shm, i))

    giu(uid, utente, argomenti, log)
    time.sleep(2.5)
    p = subprocess.run(["pgrep", "-u", str(uid), "-f", "04-b30-scen[a] --"],
                       capture_output=True)
    pids = [int(x) for x in p.stdout.decode().split()]
    if not pids:
        fuori["ok"] = False
        fuori["detto"] = "⛔ la scena non e' partita"
        try:
            with open(log) as f:
                fuori["registro"] = f.read()[-400:]
        except Exception:
            pass
        print(json.dumps(fuori))
        sys.exit(1)
    fuori["pid_scena"] = pids[0]

    if scena == "vero":
        fuori["esci_dalla_vista"] = esc(uid, lav)
        subprocess.run(["bash", "-c",
                        "setsid nohup python3 %s/10-b92-scene.py strappi %d "
                        "%.3f %.3f %d >>%s 2>&1 &"
                        % (lav, pids[0], float(os.environ.get("QUIETE", "1.0")),
                           float(os.environ.get("ACCENSIONE", "0.30")), uid, log)])
        time.sleep(1.0)
        p = subprocess.run(["bash", "-c",
                            "pgrep -c -f '10-b92-scene[.]py strappi .* %d$' "
                            "|| true" % uid], capture_output=True)
        t = p.stdout.decode().strip()
        fuori["strappi_vivi"] = int(t) if t.isdigit() else 0
        if not fuori["strappi_vivi"]:
            fuori["ok"] = False
            fuori["detto"] = ("⛔ il ciclo degli strappi non e' partito: la "
                              "scena «vero» sarebbe a movimento CONTINUO, cioe' "
                              "un'altra scena")
            print(json.dumps(fuori))
            sys.exit(1)
    fuori["ok"] = True
    fuori["detto"] = ("scena «%s» accesa (pid %d)%s"
                      % (scena, pids[0],
                         "" if scena != "vero"
                         else " · %d finestre vere · strappi %.2f/%.2f s"
                              % (fuori["finestre_vive"],
                                 float(os.environ.get("QUIETE", "1.0")),
                                 float(os.environ.get("ACCENSIONE", "0.30")))))
    print(json.dumps(fuori))

else:
    print(json.dumps({"esito": "passo «%s» sconosciuto" % passo}))
    sys.exit(2)
'''


# ═══════════════════════════════════════════════════════════════════════════
def spedisci(sorgente, nome):
    """⛔ In base64: le virgolette di un heredoc dentro un `sudo -S` dentro un
       `ssh` sono tre livelli di quoting, e uno sbagliato non da' un errore —
       da' un file troncato.  ⛔ E la catena e' UNA SOLA `root()`: `mkdir`,
       `printf`, `base64 -d` e il `>` vivono tutti nella shell di root."""
    b = base64.b64encode(sorgente.encode("utf-8")).decode("ascii")
    root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/%s"
         % (LAV, b, LAV, nome))
    rc, out, _ = root("wc -c < %s/%s" % (LAV, nome))
    t = out.strip()
    return t.isdigit() and int(t) > 500


def sonda(quanti):
    """Una fotografia.  ⛔ `None` se non si e' letta: non un dizionario vuoto."""
    uids = ",".join(str(uid(i)) for i in range(1, quanti + 1))
    rc, out, err = root("python3 %s/10-b92-sonda.py %s %s %s"
                        % (LAV, PDEV_BUONO, uids, UNITA), 180)
    try:
        return json.loads(out)
    except Exception as e:
        _dub("⛔ la sonda non ha risposto (rc=%s): %s — %s"
             % (rc, e, (out + err)[-200:]))
        return None


def fra(a, b, quanti_uid):
    """I DELTA fra due fotografie.  ⛔ `None` ovunque non si sia potuto leggere."""
    if not a or not b:
        return {"esito": "⛔ NON HO NIENTE DA GIUDICARE — manca una delle due "
                         "fotografie"}
    secondi = (b["t_ms"] - a["t_ms"]) / 1000.0
    if secondi <= 0:
        return {"esito": "⛔ NON GIUDICO — le due fotografie non sono in ordine "
                         "(%.1f s)" % secondi}
    d = {"secondi": round(secondi, 2), "esito": "misurato"}
    # ── CPU ──
    ca, cb = a.get("cpu", {}), b.get("cpu", {})
    if "totale" in ca and "totale" in cb and cb["totale"] > ca["totale"]:
        tot = cb["totale"] - ca["totale"]
        ina = cb["inattivo"] - ca["inattivo"]
        d["cpu_occupata_pc"] = round(100.0 * (tot - ina) / tot, 1)
        d["cpu_nuclei"] = cb.get("nuclei")
    else:
        d["cpu_occupata_pc"] = None
    # ── CPU del server e dei clienti, separate ──
    hz = 100.0    # ⚠ USER_HZ: 100 su ogni Linux corrente; si dichiara
    for chi in ("server", "clienti"):
        pa = a["processi"][chi]["cpu_jiffies"]
        pb = b["processi"][chi]["cpu_jiffies"]
        d["cpu_%s_nuclei" % chi] = round((pb - pa) / hz / secondi, 2)
    d["cpu_clienti_quota"] = (
        round(d["cpu_clienti_nuclei"] / d["cpu_nuclei"], 3)
        if d.get("cpu_nuclei") else None)
    # ── MEMORIA: PSS (e RSS accanto, per far vedere la differenza) ──
    d["pss_server_mib"] = round(b["processi"]["server"]["pss_kib"] / 1024.0, 1)
    d["rss_server_mib"] = round(b["processi"]["server"]["rss_kib"] / 1024.0, 1)
    d["pss_clienti_mib"] = round(b["processi"]["clienti"]["pss_kib"] / 1024.0, 1)
    pss_u = sum(v["pss_kib"] for v in b["processi"]["per_uid"].values())
    rss_u = sum(v["rss_kib"] for v in b["processi"]["per_uid"].values())
    d["pss_sessioni_mib"] = round(pss_u / 1024.0, 1)
    d["rss_sessioni_mib"] = round(rss_u / 1024.0, 1)
    d["pss_totale_mib"] = round((pss_u + b["processi"]["server"]["pss_kib"]) / 1024.0, 1)
    d["uid_con_processi"] = len(b["processi"]["per_uid"])
    d["pss_negati"] = b["processi"]["negati"]
    # ── GPU ──
    ga, gb = a.get("gpu", {}), b.get("gpu", {})
    cap = gb.get("capacita", {}) or ga.get("capacita", {}) or {}
    # ⛔⛔ IL DELTA SI FA PER CONTESTO, E NON E' UN DETTAGLIO — `[M]` 24 agosto
    #     2026, gradino 1 del giro vero: `render −76,4 %`, `video −44,3 %`.
    #
    #     I `drm-engine-*` sono contatori CUMULATIVI **per contesto DRM**, e il
    #     contesto muore col processo.  ⇒ Sottrarre due SOMME prese su due
    #     platee diverse non da' il lavoro fatto: da' il lavoro fatto **meno
    #     tutto quel cumulativo che se n'e' andato in mezzo**.  Al gradino 1 se
    #     n'erano andati i palchi chiusi poco prima, e il metro ha scritto
    #     un'occupazione **negativa**.
    #     ⚠ Un numero negativo almeno si vede.  Il caso cattivo e' l'altro: un
    #       contesto che NASCE fra le due fotografie porta dentro il suo
    #       cumulativo dall'inizio dei tempi e gonfia il delta senza che nulla
    #       lo dica.  ⇒ Si sommano solo i contesti presenti in TUTT'E DUE, e
    #       quelli nati e morti si contano e si dichiarano.
    ca = ga.get("per_contesto", {}) or {}
    cb = gb.get("per_contesto", {}) or {}
    comuni = set(ca) & set(cb)
    motori, uso = {}, {}
    for m in set(list(ga.get("motori", {})) + list(gb.get("motori", {}))):
        ns = 0
        for cid in comuni:
            ns += cb[cid].get(m, 0) - ca[cid].get(m, 0)
        # ⚠ DUE percentuali, e non si confondono (`10-b87-metro-gpu.py`):
        #   · `gpu_pc`  = motori-equivalenti ×100 — con capacita' 2 il massimo
        #     e' 200, non 100;
        #   · `gpu_uso` = frazione della capacita' di quel motore, 0..100.
        #   ⛔ Chi le confonde sbaglia il budget di un fattore due.
        motori[m] = round(100.0 * ns / 1e9 / secondi, 1)
        uso[m] = round(motori[m] / max(1, cap.get(m, 1)), 1)
    d["gpu_pc"] = motori
    d["gpu_uso_pc"] = uso
    d["gpu_capacita"] = cap
    d["gpu_contesti"] = {"comuni": len(comuni), "nati": len(set(cb) - set(ca)),
                         "morti": len(set(ca) - set(cb))}
    # ⛔ E un delta NEGATIVO resta impossibile anche cosi': se compare, il metro
    #    non e' quello che credo e il gradino NON si giudica.
    d["gpu_negativi"] = {m: v for m, v in motori.items() if v < -0.05}
    # ⭐ Il contesto della GT: l'occupazione dipende dalla frequenza, e senza
    #    questa riga il numero si muove sotto i piedi di chi legge.
    ta, tb = a.get("gt") or {}, b.get("gt") or {}
    rc6 = None
    if ta.get("rc6_ms") is not None and tb.get("rc6_ms") is not None:
        dr = tb["rc6_ms"] - ta["rc6_ms"]
        if dr >= 0:
            rc6 = round(dr / (secondi * 1000.0) * 100.0, 1)
    d["gt"] = {"act_mhz": tb.get("act_mhz"), "cur_mhz": tb.get("cur_mhz"),
               "min_mhz": tb.get("min_mhz"), "max_mhz": tb.get("max_mhz"),
               "bloccata": (tb.get("min_mhz") is not None
                            and tb.get("min_mhz") == tb.get("max_mhz")),
               "rc6_pc": rc6,
               "sveglia_pc": None if rc6 is None else round(100.0 - rc6, 1)}
    d["gpu_clienti"] = gb.get("clienti")
    d["gpu_estranei"] = gb.get("estranei")
    d["gpu_estranei_pid"] = gb.get("estranei_pid")
    d["gpu_altri_pdev"] = gb.get("altri_pdev")
    # ⛔ IL CONTROLLO DEL METRO DELLA GPU, e sta QUI perche' e' qui che il
    #    numero si consuma: un motore e' UNO e serve una richiesta per volta ⇒
    #    la somma di tutti i clienti su un motore NON PUO' superare il tempo di
    #    parete.  Oltre il 105 % il metro sta contando due volte (tipicamente:
    #    la deduplicazione per `drm-client-id` non ha funzionato).
    # ⛔ Il tetto di un motore e' 100 % × la sua CAPACITA', non 100 %.
    d["gpu_metro_sano"] = (
        not d["gpu_negativi"]
        and all(v <= 100.0 * max(1, cap.get(m, 1)) + 5.0
                for m, v in motori.items()))
    # ── IL FILO ──
    ra, rb = a.get("rete", {}), b.get("rete", {})
    filo = {}
    for dev in ("lo", "enp7s0"):
        if dev in ra and dev in rb:
            by = rb[dev]["tx_byte"] - ra[dev]["tx_byte"]
            pk = rb[dev]["tx_pacchetti"] - ra[dev]["tx_pacchetti"]
            filo[dev] = {"mbit_s": round(by * 8 / secondi / 1e6, 2),
                         "byte_per_pacchetto": round(by / pk, 1) if pk else None}
    d["filo"] = filo
    d["costo_sonda_ms"] = [a.get("costo_ms"), b.get("costo_ms")]
    return d


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL REGISTRO DEL SERVER — quel che il cliente non puo' sapere
# ═══════════════════════════════════════════════════════════════════════════
def registro_righe():
    """A che PUNTO e' il registro adesso, in byte — ⛔ o `None` se non l'ho letto.

    ⛔ Uno zero che vuol dire «non ho letto» e uno che vuol dire «non e'
       successo niente» non devono avere la stessa faccia (`LEZIONI.md` §1.9):
       il server e' acceso, e un server acceso ha gia' scritto.
    """
    rc, out, err = root("stat -c %%s %s/registro.log" % LAV)
    t = out.strip()
    if rc != 0 or not t.isdigit():
        _dub("⛔ il registro del server NON si e' letto (rc=%s): «%s»"
             % (rc, (t + " " + err.strip())[:120]))
        return None
    n = int(t)
    if n <= 0:
        _dub("⛔ il registro e' a ZERO byte col server acceso: e' una lettura "
             "fallita, non una misura (il server acceso ha gia' scritto)")
        return None
    return n


def mappa_provenienze():
    """utente → «ip:porta», dalla riga `posto PRESO da %s via %s` (`rcp.c:2869`).

    ⭐ E' l'unico ponte fra le righe `rete-quic <ip:porta>` — che sono per
       CONNESSIONE — e i miei dieci utenti.  ⚠ Si prende l'ULTIMA occorrenza per
       utente: un utente che si riattacca cambia porta.
    """
    rc, out, _ = root("grep -a 'posto PRESO da' %s/registro.log | tail -200"
                      % LAV)
    m, occupati = {}, None
    for r in out.splitlines():
        g = re.search(r"posto PRESO da (\S+) via (\S+)", r)
        if g:
            m[g.group(1)] = g.group(2)
        # ⚠ «occupati adesso» sta sulla stessa riga, e si legge da TUTTO il
        #   registro e non dalla finestra del gradino: il posto si prende
        #   all'attacco, cioe' PRIMA dell'assestamento, e dentro la finestra
        #   quella riga non c'e' mai.  ⛔ Cercarla li' darebbe `None` per
        #   sempre — un «non lo so» travestito da «nessuno occupa niente».
        g2 = re.search(r"occupati adesso: (\d+)", r)
        if g2:
            occupati = int(g2.group(1))
    return m, occupati


def conti_server(riga0, riga1, provenienze):
    """I conti del server nella finestra [riga0, riga1] del registro.

    ⛔ LA PRIMA COSA CHE FA E' RIFIUTARSI se `riga0` non e' un numero buono:
       senza la riga di partenza i conti sarebbero CUMULATIVI dall'accensione —
       il difetto che in fase 9 e' costato **4 041 invece di 1 604**.

    ⛔⛔ E SI LEGGE IN UNA PASSATA SOLA — vedi il riquadro di `10-b92-conti.py`.
    """
    if riga0 is None or riga1 is None or riga1 <= riga0:
        return {"esito": "⛔ NON HO LETTO — confini del registro «%s»→«%s» "
                         "byte" % (riga0, riga1)}
    rc, out, err = root("python3 %s/10-b92-conti.py %s/registro.log %d %d"
                        % (LAV, LAV, riga0, riga1), 900)
    try:
        fuori = json.loads(out)
    except Exception as e:
        return {"esito": "⛔ NON HO LETTO — il lettore del registro non ha "
                         "risposto: %s — %s" % (e, (out + err)[-160:])}
    if fuori.get("esito") != "letto":
        return fuori
    # ⭐ Il ponte fra le righe `rete-quic <ip:porta>` — che sono per CONNESSIONE
    #    — e i miei utenti: lo da' `rcp.c:2869`, «posto PRESO da %s via %s».
    per_prov = fuori.pop("per_provenienza", {})
    per_utente = {}
    for u, prov in provenienze.items():
        d = per_prov.get(prov)
        if not d or d["righe"] < 2:
            per_utente[u] = {"esito": "NIENTE DA LEGGERE — meno di due righe "
                                      "«rete-quic» per «%s» in questa finestra"
                                      % prov}
            continue
        byte = d["byte_ultimo"] - (d["byte_primo"] or 0)
        per_utente[u] = {
            "provenienza": prov, "righe": d["righe"],
            "pacchetti_spediti": d["spediti_d"], "persi": d["persi_d"],
            "byte_spediti_nel_giro": byte,
            "mbit_s": round(byte * 8 / max(1, d["righe"] - 1) / 1e6, 2),
            "cwnd_mediana": statistics.median(d["cwnd"]),
            "srtt_ms_mediano": round(statistics.median(d["srtt_us"]) / 1000.0, 2)}
    fuori["per_utente"] = per_utente
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE SESSIONI — si aprono una alla volta, e ciascuna porta la SUA scena
# ═══════════════════════════════════════════════════════════════════════════
def giornale_di(i):
    return "%s/giornale-%d.jsonl" % (LAV, i)


def registro_di(i):
    return "%s/cliente-%d.log" % (LAV, i)


def giornale_dentro(i):
    """⛔⛔ IL PERCORSO CHE STA NELLA RIGA DI COMANDO, non quello che vedo io.

    ⚠ E' costato un giro: il cliente gira DENTRO il contenitore, e nella sua
      `/proc/<pid>/cmdline` c'e' `/srv/remotix/tmp/10a6/...`, non
      `/media/REMOTIX/tmp/10a6/...` — sono la stessa cartella vista da due
      lati di un `--bind`.  Un `pgrep -f` col percorso di fuori non trova mai
      niente ⇒ ogni sessione sarebbe dichiarata **morta appena aperta**, e il
      banco avrebbe dato rosso al prodotto per un percorso sbagliato mio.
    """
    return "%s/giornale-%d.jsonl" % (DENTRO_LAV, i)


def cerca_giornale(i):
    """⛔⛔ IL MOTIVO PER CUI QUESTA FUNZIONE ESISTE — `[M]` 24 agosto 2026.

    `pgrep -f` cerca dentro la riga di comando di **tutti** i processi, e la
    riga di comando che lo lancia — `ssh … sudo -S bash -c "pgrep -f -- '…'"` —
    **contiene il modello**.  ⇒ `pgrep` trova la propria shell, e risponde
    «vivo» sempre: anche su un cliente morto da un minuto.

    `[M]` Il sintomo, in un giro vero: undici sessioni su undici hanno stampato
    *«non se n'e' andata da sola»* dopo essersene andate benissimo.  ⚠ E il
    danno vero non e' quella riga: e' che il predicato *«il cliente e' morto a
    meta' ⇒ `None`, non zero»* **non poteva scattare piu'** — il banco avrebbe
    misurato una fetta vuota chiamandola «zero fotogrammi consegnati», cioe'
    avrebbe accusato il prodotto di un cliente caduto.  E' `REVIEWER.md` E14,
    «il banco tace invece di dare rosso», arrivata da una direzione che non
    avevo guardato.

    ⭐ La cura e' vecchia quanto `ps`, e in questo progetto sta gia' scritta in
       `09-b71-sessione.sh` (`pgrep -f '01-b3-cliente[.]py'`): si spezza il
       modello con una **classe di caratteri**.  `[/]srv/...` combacia con
       `/srv/...` ma il testo `[/]srv` non compare in nessuna riga di comando —
       compresa la propria.
    ⚠ Le scene invece si cercano con `pgrep -u <uid>`, e li' il problema non
      c'e': il `pgrep` gira da root, l'uid filtra via se stesso.
    """
    p = giornale_dentro(i)
    return "--giornale [%s]%s" % (p[0], p[1:])


def vivo(i):
    """`True` se il cliente `i` e' ancora in piedi.  ⛔ Si CHIEDE al nucleo per
       nome del file che solo quel cliente porta (`CODER.md` §3.7)."""
    rc, out, _ = root("pgrep -f -- '%s' >/dev/null 2>&1 && echo vivo "
                      "|| echo morto" % cerca_giornale(i))
    return "vivo" in out


def apri_sessione(i, resta_s):
    """⛔ Torna `(True, ...)` SOLO quando il registro del cliente porta la riga
       «SESSIONE».  Un processo che esiste non e' una sessione aperta
       (`LEZIONI.md` §1.9: «partita» e «arrivata in fondo» hanno la stessa
       faccia finche' non si guarda il registro)."""
    u, log, gio = utente(i), registro_di(i), giornale_di(i)
    seg = "%s/segnale-%d" % (LAV, i)
    root("rm -f %s %s %s" % (log, gio, seg))
    dentro = ("python3 -u %s/10-b92-cliente.py "
              "--cliente %s/banchi/01-b3-cliente.py --giornale %s "
              "--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
              "--tela %s --video-codec %s --audio-codec pcm --resta %d "
              "--segnale %s"
              % (DENTRO_LAV, DENTRO_ALB, DENTRO_LAV + "/giornale-%d.jsonl" % i,
                 IND, PORTA, u, DENTRO_LAV, TELA, CODEC_CHIESTO, int(resta_s),
                 DENTRO_LAV + "/segnale-%d" % i))
    root("setsid nohup bash /media/REMOTIX/enter.sh --root %s >> %s 2>&1 & "
         "echo avviato" % (shlex.quote(dentro), log))
    # ⛔ IL RESPIRO PRIMA DI GUARDARE, e non e' prudenza: e' che «non e' ancora
    #    nato» e «e' morto» hanno la stessa faccia in `pgrep`.  Fra il `setsid`
    #    e il primo processo che si vede ci sono l'`ssh`, il `sudo`, l'ingresso
    #    nel contenitore e l'import di `aioquic` — e con dieci sessioni grafiche
    #    gia' accese non e' un secondo.  ⇒ Per i primi GRAZIA giri si guarda solo
    #    il segnale; dopo, anche se e' vivo.
    GRAZIA = 12
    # ⛔⛔ QUATTRO MINUTI, NON DUE — e la differenza fra i due numeri e' una
    #     ATTRIBUZIONE, non una comodita'.
    #
    #     Aprire la sessione numero undici vuol dire far nascere l'undicesimo
    #     `gnome-session` su una macchina dove altri dieci stanno gia' saturando
    #     la GPU.  ⚠ Con un tetto stretto, una sessione **lenta** e una sessione
    #     **rotta** darebbero la stessa riga — «NON si e' aperta» — e la salita
    #     si fermerebbe dando rosso al prodotto per un tetto scelto da me.
    #   ⇒ Il tetto sta largo, e ⭐ il TEMPO DI APERTURA si misura e si stampa: e'
    #     una delle risposte che la fase cerca (*«a quale numero si ferma»*), e
    #     una curva che sale e' un'informazione, non un guasto.
    TETTO_APERTURA = 240
    for giro in range(TETTO_APERTURA):
        time.sleep(1.0)
        rc, out, _ = root("test -f %s && echo si || echo no" % seg)
        if "si" in out:
            rc, out, _ = root("grep -am1 SESSIONE %s || true" % log)
            return True, out.strip()[:160]
        if giro >= GRAZIA and not vivo(i):
            rc, out, _ = root("tail -20 %s || true" % log)
            return False, ("⛔ il cliente %d e' MORTO prima di aprire la "
                           "sessione — il suo registro:\n%s" % (i, out[-800:]))
    rc, out, _ = root("tail -20 %s || true" % log)
    return False, ("⛔ la sessione %d NON si e' aperta in %d s — il suo "
                   "registro:\n%s" % (i, TETTO_APERTURA, out[-800:]))


def uscita_del(i):
    """Il monitor su cui la scena deve andare, CHIESTO al compositore.

    ⛔ Non si deduce dal registro del server: con dieci figli che appendono allo
       stesso file le righe `monitor «…»` si mescolano e non si sa di chi sono.
       ⭐ Si chiede a `04-b30-scena --uscite`, che parla col compositore DI
       QUESTO utente — `CODER.md` §3.9, si chiede per nome.
    """
    n = uid(i)
    rc, out, err = root(
        "setpriv --reuid=%d --regid=%d --init-groups env -i HOME=/home/%s "
        "USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
        "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 %s --uscite"
        % (n, n, utente(i), utente(i), n, SCENA_BIN), 60)
    nomi = re.findall("«([^»]+)»", out + err)
    return nomi[0] if nomi else None


def shm_di(i):
    """⛔ `/dev/shm` e' UNO su tutta la macchina: il nome porta dentro sia il
       banco sia la sessione, o due sessioni si leggerebbero i disegni a vicenda
       **senza dare rosso**."""
    return "%s-%d" % (SHM_BASE, i)


def accendi_scena_vera_o_ferma(i, scena):
    """⭐ LE DUE SCENE NUOVE — «desktop vero» e «ferma».  ⛔ Girano
       sull'attrezzo `10-b92-scene.py`, che sta DOVE STANNO I DATI: le finestre,
       l'ESC che esce dalla vista d'insieme e il ciclo degli strappi non si
       possono guidare da un `ssh` per colpo."""
    n = uid(i)
    for tentativo in range(3):
        usc = uscita_del(i) or "-"
        rc, out, err = root(
            "QUIETE=%.3f ACCENSIONE=%.3f python3 %s/10-b92-scene.py accendi "
            "%d %d %s %s %s %s %s %s %s"
            % (STRAPPO_QUIETE, STRAPPO_ACCENSIONE, LAV, i, n, utente(i), scena,
               shm_di(i), usc, FINESTRA_VERO, SCENA_BIN, LAV), 300)
        try:
            d = json.loads(out.strip().splitlines()[-1])
        except Exception:
            d = {"ok": False, "detto": "⛔ l'attrezzo non ha risposto: %s"
                                       % (out + err).strip()[-200:]}
        if d.get("ok"):
            _inf("s%d · %s" % (i, d.get("detto")))
            if d.get("trovati_prima"):
                _dub("⚠ s%d aveva %d processi che disegnavano dal giro prima: "
                     "spenti PRIMA di misurare (e detto)"
                     % (i, d["trovati_prima"]))
            if d.get("esci_dalla_vista") is False:
                _dub("⚠ s%d: l'ESC per uscire dalla vista d'insieme NON e' "
                     "arrivato — le finestre potrebbero essere anteprime "
                     "rimpicciolite (09-b72)" % i)
            return usc if usc != "-" else "in-finestra"
        _dub("⚠ la scena «%s» di s%d non e' partita al tentativo %d — %s"
             % (scena, i, tentativo + 1, str(d.get("detto"))[-200:]))
        time.sleep(3.0)
    return None


def accendi_scena(i, movimento=None):
    """⛔ «Scena viva» non e' «scena spenta»: a scena spenta il compositore
       consegna pochissimo, e un ritmo basso a monte somiglia in tutto a un
       ritmo abbassato da noi (09-b70, `scena_accendi`).

    ⭐ Dal 24 agosto 2026 ci sono TRE scene, e il braccio `satura` scende per la
       strada di sempre — riga per riga — perche' e' l'**ancora**."""
    if SCENA in ("vero", "ferma"):
        return accendi_scena_vera_o_ferma(i, SCENA)
    movimento = movimento or MOVIMENTO
    n = uid(i)
    # ⛔⛔ SI RIPROVA, E NON E' PIGRIZIA — `[M]` 24 agosto 2026.
    #
    #     Al primo giro vero con la scena satura, la scena di s1 **non e'
    #     partita**: il palco era nato due secondi prima, e il compositore non
    #     era ancora pronto a dare l'uscita.  ⚠ Il banco allora saltava il
    #     gradino — e s1 restava senza scena **per tutto il resto della
    #     salita**, cioe' dentro il conto come sessione «viva» ma ferma.
    #     ⇒ Tre tentativi, e il registro della scena si CONSERVA: una scena che
    #       non parte deve poter dire perche'.
    log = "%s/scena-%d.log" % (LAV, i)
    for tentativo in range(3):
        usc = uscita_del(i)
        if not usc:
            time.sleep(3.0)
            continue
        root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
             "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
             "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
             "%s --uscita %s --movimento %s --shm /%s --giro b92-%d "
             ">> %s 2>&1 & echo acceso"
             % (n, n, utente(i), utente(i), n, SCENA_BIN, usc, movimento,
                shm_di(i), i, log))
        time.sleep(2.5)
        rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
        if out.strip():
            return usc
        rc, out, _ = root("tail -3 %s 2>/dev/null || true" % log)
        _dub("⚠ la scena di s%d non e' partita al tentativo %d — dice: %s"
             % (i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


def assicura_scene(quanti_vive):
    """⛔⛔ IL CARICO DEVE RESTARE ADDOSSO PER TUTTA LA SALITA.

    Una scena che muore a meta' non fa cadere niente: fa **calare il carico**,
    e al gradino dopo la macchina sembra piu' larga di quel che e'.  ⚠ E' la
    forma peggiore, quella che non da' rosso: `LEZIONI.md` §1.30 al contrario —
    invece di una prova che non morde da subito, una prova che **smette** di
    mordere a meta' e regala un verde a chi arriva dopo.

    ⇒ A ogni gradino si guarda chi disegna, e chi non disegna si RIACCENDE.
      ⭐ E il fatto si dichiara: un gradino in cui una scena e' stata riaccesa
      non e' un gradino uguale agli altri.
    """
    _v, scene, _m = chi_c_e(quanti_vive)
    riaccese = []
    for i in range(1, quanti_vive + 1):
        if not scene.get(i):
            if accendi_scena(i):
                riaccese.append(i)
    if riaccese:
        _dub("⚠ RIACCESE le scene di %s: erano morte, e senza di loro quelle "
             "sessioni sarebbero state dieci schermi fermi contati come dieci "
             "desktop al lavoro" % ", ".join("s%d" % i for i in riaccese))
    return riaccese


def chi_c_e(quanti):
    """⭐ CHI E' VIVO E CHI DISEGNA, in UNA domanda sola.

    ⛔ La prima stesura aveva DUE funzioni, una per «chi e' vivo» e una per «chi
       disegna», e ciascuna faceva un `ssh` per sessione: a undici sessioni
       ventidue giri di rete, cioe' mezzo minuto, fra la fine della finestra e
       la lettura delle fette.  ⚠ Non falsavano la misura — la finestra e' gia'
       chiusa — ma allungavano il giro di un minuto per gradino, e un giro piu'
       lungo e' un giro che il lucchetto tiene fermo per tutti gli altri.

    ⭐ E «disegna» vuol dire cose DIVERSE nelle tre scene, e non e' una
      sottigliezza: per `ferma` la scena giusta e' **nessuna scena**, e un
      `pgrep` che cercasse `04-b30-scena` direbbe «ferma» ⇒ il banco
      riaccenderebbe una scena in un braccio che esiste per non averla.
      ⇒ Per `ferma` la domanda e' *«il PALCO e' in piedi?»*, che e' la premessa
        vera di quel braccio: senza `gnome-shell` non c'e' nessun desktop fermo,
        c'e' il nulla.
    """
    righe = []
    for i in range(1, quanti + 1):
        if SCENA == "ferma":
            chi_disegna = "pgrep -u %d -f 'gnome-shel[l]|mutte[r]'" % uid(i)
        elif SCENA == "vero":
            # ⛔ TUTT'E TRE i pezzi: la scena, il ciclo degli strappi e almeno
            #    una finestra vera.  Se ne manca uno, «desktop vero» e' un'altra
            #    scena, e chiamarla con lo stesso nome sarebbe la forma peggiore.
            chi_disegna = ("pgrep -u %d -f '04-b30-scen[a] --' >/dev/null 2>&1 "
                           "&& pgrep -f '10-b92-scene[.]py strappi .* %d$' "
                           ">/dev/null 2>&1 && pgrep -u %d -f '%s'"
                           % (uid(i), uid(i), uid(i), FINESTRE))
        else:
            chi_disegna = "pgrep -u %d -f '04-b30-scena --uscita'" % uid(i)
        righe.append(
            "printf '%%d ' %d; "
            "pgrep -f -- '%s' >/dev/null 2>&1 && printf vivo || "
            "printf morto; printf ' '; "
            "%s >/dev/null 2>&1 && "
            "printf disegna || printf ferma; printf '\\n'"
            % (i, cerca_giornale(i), chi_disegna))
    rc, out, _ = root(" ; ".join(righe), 180)
    vive, scene = {}, {}
    for r in out.splitlines():
        p = r.split()
        if len(p) == 3 and p[0].isdigit():
            vive[int(p[0])] = (p[1] == "vivo")
            scene[int(p[0])] = (p[2] == "disegna")
    # ⛔ Chi non ha risposto NON e' «morto»: e' «non lo so», e si dichiara.
    manca = [i for i in range(1, quanti + 1) if i not in vive]
    return vive, scene, manca


# ⛔ La stessa classe di caratteri, e per la stessa ragione: `FINESTRE` porta
#    dentro `nautilu[s]`, e senza le parentesi il `pkill` ammazzerebbe la shell
#    che lo esegue, lasciando la pulizia a meta' IN SILENZIO.
def spegni_scene(quanti):
    uidi = ",".join(str(uid(i)) for i in range(1, quanti + 1))
    root("python3 %s/10-b92-scene.py spegni %s || true" % (LAV, uidi), 300)
    for i in range(1, quanti + 1):
        root("pkill -u %d -f 04-b30-scena; true" % uid(i))


def disegni_tutte(quanti):
    """⭐⭐ QUANTO LA SCENA HA DAVVERO CAMBIATO LO SCHERMO.

    ⛔ E' la grandezza che la domanda del budget aspetta — *«il costo cresce con
       quanto il desktop cambia, e come?»*.  Senza di lei si potrebbe solo
       correlare il costo col costo: i fotogrammi consegnati sono gia' un'uscita
       del prodotto, non un ingresso della prova.

    ⛔ Torna `{i: {...}}` con `disegni` cumulativi, o l'`esito` di chi non ha
       letto.  ⚠ `None` non e' zero: una scena che non pubblica il suo blocco
       non e' una scena che non disegna.
    """
    nomi = ",".join(shm_di(i) for i in range(1, quanti + 1))
    rc, out, err = root("python3 %s/10-b92-scene.py disegni %s" % (LAV, nomi), 120)
    try:
        d = json.loads(out.strip().splitlines()[-1])
    except Exception:
        return None
    fuori = dict((i, d.get(shm_di(i), {"esito": "manca la voce"}))
                 for i in range(1, quanti + 1))
    fuori["t_ms"] = d.get("t_ms")
    return fuori


def fra_disegni(a, b, i, secondi):
    """Il DELTA dei disegni fra le due ancore del gradino, per la sessione `i`.

    ⛔ Torna `None` (e il perche') dove non ha potuto: un contatore che riparte
       da zero vuol dire **scena rinata a meta' gradino**, e un delta negativo
       preso per buono sarebbe un numero plausibile e falso.
    """
    if not a or not b:
        return {"disegni_s": None, "esito": "non ho le due letture"}
    # ⭐ La durata VERA della finestra dei disegni, dall'orologio che la lettura
    #   si porta dietro.  ⚠ Se manca, si ripiega sulla durata chiesta e SI DICE.
    ripiego = False
    if a.get("t_ms") is not None and b.get("t_ms") is not None:
        secondi = (b["t_ms"] - a["t_ms"]) / 1000.0
    else:
        ripiego = True
    if secondi <= 0:
        return {"disegni_s": None,
                "esito": "⛔ NON GIUDICO: la finestra dei disegni non avanza"}
    va, vb = a.get(i) or {}, b.get(i) or {}
    if "disegni" not in va or "disegni" not in vb:
        return {"disegni_s": None,
                "esito": "⛔ NON LETTO: %s / %s" % (va.get("esito"), vb.get("esito"))}
    if vb["disegni"] < va["disegni"] or vb.get("pid") != va.get("pid"):
        return {"disegni_s": None,
                "esito": "⛔ NON GIUDICO: il contatore e' tornato indietro "
                         "(%d → %d) o la scena e' rinata (pid %s → %s): la "
                         "scena e' cambiata DENTRO il gradino"
                         % (va["disegni"], vb["disegni"], va.get("pid"),
                            vb.get("pid"))}
    d = vb["disegni"] - va["disegni"]
    area = (vb.get("larghezza") or 0) * (vb.get("altezza") or 0)
    return {"disegni": d, "disegni_s": round(d / secondi, 2),
            "finestra_s": round(secondi, 2),
            # ⚠ Un campione preso a scena CONGELATA (seq dispari, blocco fermo)
            #   puo' essere indietro **di un disegno**: si dichiara, e su decine
            #   di migliaia non sposta niente.  Tacerlo sarebbe la forma cattiva.
            "campione_congelato": bool(va.get("campione_congelato")
                                       or vb.get("campione_congelato")),
            "durata_ripiegata": ripiego,
            "tela_scena": "%sx%s" % (vb.get("larghezza"), vb.get("altezza")),
            "mpixel_ridisegnati_s": round(d * area / secondi / 1e6, 2)}


# ⛔⛔ IL PALCO SOPRAVVIVE AL DISTACCO, ED E' GIUSTO COSI' — invariante I4.
#
#    `[M]` 24 agosto 2026: chiuso il cliente di `provamt1`, restano vivi
#    `remotix-figlio`, `gnome-session-binary`, `dconf-service` e compagnia.  ⭐ E'
#    il prodotto che fa il suo mestiere: *«il palco appartiene alla sessione, non
#    alla connessione»* (`CODER.md` §2, I4).
#
# ⚠ Ma per il BANCO e' un guaio, ed e' lo stesso di `LEZIONI.md` §1.29: un giro
#   che comincia con dei palchi gia' in piedi non misura l'apertura, non misura
#   la memoria di dieci sessioni nuove, e **non da' rosso — da' un numero
#   plausibile**.  ⇒ Fra un giro e l'altro il palco si chiude a mano, e si dice.
#
# ⛔ E si chiude **per uid mio e per nome del processo**, mai per nome globale:
#   sulla macchina ci sono i palchi di altri sei agenti, e un `pkill gnome-shell`
#   li ammazzerebbe tutti.
PALCO_NOMI = "gnome-shell|gnome-session|gnome-settings|mutter|Xwayland|dconf|" \
             "04-b30-scena|remotix-figlio|ssh-agent|at-spi|gvfs|gjs|goa-|" \
             "tracker|evolution|xdg-|gsd-|gcr-|dbus-run"


def chiudi_palco(i):
    """⛔ Chiude il palco di UN utente mio, lasciando in piedi il fondo di
       `enable-linger` (`systemd --user`, PipeWire, dbus): quello serve alla
       sessione dopo, e ammazzarlo vorrebbe dire misurare un terreno diverso."""
    root("pkill -u %d -f -- '%s'; true" % (uid(i), PALCO_NOMI))


def chiudi_palchi(quanti, dillo=True):
    for i in range(1, quanti + 1):
        chiudi_palco(i)
    time.sleep(3)
    resti = []
    for i in range(1, quanti + 1):
        rc, out, _ = root("pgrep -u %d -a 2>/dev/null | grep -cE "
                          "'gnome-shell|gnome-session|mutter|Xwayland|"
                          "04-b30-scena|remotix' || true" % uid(i))
        if out.strip().isdigit() and int(out.strip()) > 0:
            resti.append("%s:%s" % (utente(i), out.strip()))
    if dillo:
        if resti:
            _dub("⚠ dopo la chiusura restano processi del palco: %s"
                 % " ".join(resti))
        else:
            _ok("i palchi dei %d utenti sono chiusi (il fondo di `linger` resta "
                "in piedi apposta)" % quanti)
    return not resti


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna (passa, perche)
# ═══════════════════════════════════════════════════════════════════════════
#
#   True  — l'atteso ha retto
#   False — ⛔ rosso
#   None  — ⚠ NON GIUDICO, e non e' un verde educato: e' un esito suo, e fa
#           uscire il banco 3.
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def ha_misurato(n):
    return bool(n) and n.get("esito") == "misurato"


def p_scena_viva(n):
    """⛔ IL PREDICATO DEGLI SCHERMI NERI — `LEZIONI.md` §1.30.

    Dieci desktop fermi non sono dieci sessioni: sono dieci schermi neri, e i
    fotogrammi/s di dieci schermi neri sono ottimi.  ⇒ Si guarda quanto PESA un
    fotogramma: `[M]` fase 9, un desktop quasi fermo ne fa da 242-283 byte.
    """
    if not ha_misurato(n):
        return _muto("non misurato")
    b = n["byte_per_fotogramma"]
    if b < BYTE_VIVI:
        return _no("⛔ %d byte per fotogramma, sotto i %d: questo NON e' un "
                   "desktop al lavoro, e' uno schermo quasi fermo — i suoi "
                   "fotogrammi/s non provano niente" % (b, BYTE_VIVI))
    return _si("%d byte/fotogramma · %d fotogrammi · %s Mbit/s di carico: la "
               "scena morde" % (b, n["fotogrammi"], n["mbit_s_carico"]))


def p_scena_morde(n, scena=None):
    """⛔⛔ IL PREDICATO DELLA SCENA, E CAMBIA CON LA SCENA — B3, 24 agosto 2026.

    ⭐ Tre bracci, tre atteso diversi, e il modo di sbagliare di ciascuno e'
      **l'opposto** di quello dell'altro:

      | braccio  | il modo di sbagliare che va smascherato | la colonna che lo vede |
      |----------|-----------------------------------------|------------------------|
      | `satura` | dieci schermi neri contati come dieci desktop al lavoro | i **byte per fotogramma** |
      | `vero`   | ⛔ un desktop vero che **non si muove** e allora «costa poco» | i **disegni**, poi il **ritmo**, poi i **byte** |
      | `ferma`  | ⛔ un desktop «fermo» che invece **si muove** — un salvaschermo, un orologio, una notifica | il **ritmo** consegnato |

    ⛔⛔ E L'ORDINE DELLE COLONNE PER `vero` NON E' UNA PREFERENZA: e' una ferita
        gia' pagata.  `10-b89` (§SOGLIA_BYTE_MORDE, 24 agosto) ha misurato che i
        byte per fotogramma **NON separano** la scena `pieno` sana (1 789) dalla
        stessa scena **congelata** (1 368): un fattore 1,3, e nessuna soglia su
        quella grandezza poteva ordinarli.  E' `REVIEWER.md` **E15**.
        ⇒ Prima i **disegni** — che sono la grandezza vera, «quanto la scena ha
          cambiato lo schermo» — poi il **ritmo**, e i byte restano accanto come
          la colonna di `LEZIONI.md` §1.30: quanto la scena CHIEDEVA.
    """
    scena = scena or SCENA
    if not ha_misurato(n):
        return _muto("non misurato")
    dis = (n.get("disegni") or {})
    ds, byte, fps = dis.get("disegni_s"), n["byte_per_fotogramma"], n["fps"]

    if scena == "ferma":
        if fps > FPS_FERMA_MASSIMO:
            return _no("⛔ «FERMA» NON E' FERMA: %.2f fotogrammi/s (sopra %.1f) "
                       "e %d byte per fotogramma — c'e' qualcosa che si muove "
                       "sotto (salvaschermo, orologio, notifica).  ⚠ Il numero "
                       "di questo gradino NON e' il costo di un desktop fermo"
                       % (fps, FPS_FERMA_MASSIMO, byte))
        return _si("il desktop e' davvero fermo: %d fotogrammi in tutto "
                   "(%.2f/s), %d byte l'uno, %s Mbit/s"
                   % (n["fotogrammi"], fps, byte, n["mbit_s_carico"]))

    if scena == "vero":
        if ds is None:
            return _muto("⚠ NON GIUDICO la scena: i disegni non si sono letti "
                         "(%s).  ⛔ «non ho misurato» non e' «non ha disegnato»"
                         % dis.get("esito"))
        if ds < DISEGNI_VIVI:
            return _no("⛔ IL «DESKTOP VERO» NON SI MUOVE: %.2f disegni/s "
                       "(sotto %.1f) — e guarda che cosa avrebbero detto le "
                       "altre due colonne: %.2f fotogrammi/s e %d byte per "
                       "fotogramma.  ⚠ Contarlo come «costa poco» sarebbe "
                       "misurare uno schermo fermo e chiamarlo desktop"
                       % (ds, DISEGNI_VIVI, fps, byte))
        if fps < FPS_VERO_MINIMO:
            return _no("⛔ la scena disegna (%.2f/s) ma al cliente arrivano "
                       "%.2f fotogrammi/s (sotto %.1f): gli strappi non stanno "
                       "arrivando fino in fondo — %d byte per fotogramma"
                       % (ds, fps, FPS_VERO_MINIMO, byte))
        if byte < BYTE_VERO_VIVI:
            return _no("⛔ %d byte per fotogramma, sotto i %d: `[M]` un "
                       "fotogramma di desktop FERMO ne pesa 455.  Questo NON e' "
                       "un desktop al lavoro (%.2f disegni/s, %.2f fot/s)"
                       % (byte, BYTE_VERO_VIVI, ds, fps))
        return _si("%.2f disegni/s della scena su %s ⇒ %s Mpixel ridisegnati/s "
                   "· %d byte/fotogramma · %.2f fot/s · %s Mbit/s"
                   % (ds, dis.get("tela_scena"), dis.get("mpixel_ridisegnati_s"),
                      byte, fps, n["mbit_s_carico"]))

    return p_scena_viva(n)


def p_ritmo(n):
    """⭐ Il pavimento di `DECISIONI.md` §2.1: 25 fotogrammi/s.  E sono DUE
       numeri, perche' la media da sola assolve: 30 s fatti di 10 a 45/s e 20 a
       17,5/s danno 26,7/s di media e venti secondi a scatti."""
    if not ha_misurato(n):
        return _muto("non misurato")
    # ⛔ IL PAVIMENTO DI §2.1 E' DI UN DESKTOP CHE LAVORA, non di uno fermo.
    #    Su un desktop **fermo** «pochi fotogrammi al secondo» e' il RISULTATO —
    #    `[M]` §6.4-bis, un fotogramma in 40,8 s — e dargli rosso vorrebbe dire
    #    accusare il prodotto di aver fatto esattamente la cosa giusta: non
    #    spedire niente quando non cambia niente.
    if SCENA == "ferma":
        return _muto("⚠ NON GIUDICO il ritmo sul braccio «ferma»: il pavimento "
                     "di %.0f/s (§2.1) e' di un desktop che LAVORA.  Qui i "
                     "fotogrammi consegnati sono %d (%.3f/s), ed e' quel che "
                     "deve succedere" % (PAVIMENTO_FPS, n["fotogrammi"], n["fps"]))
    # ⛔⛔ E SUL BRACCIO «VERO» IL PAVIMENTO ASSOLUTO E' IL METRO SBAGLIATO —
    #     `[M]` 24 agosto 2026, 22:28, primo gradino del braccio: **10,61
    #     fotogrammi/s**, e il predicato ha dato ROSSO con una sola sessione
    #     sulla macchina, GPU al 2,2 %.
    #     ⚠ Quel rosso non era del prodotto: la scena a STRAPPI disegna il 23 %
    #       del tempo, e `[M]` ne ha chiesti **14,62 al secondo**.  Un desktop
    #       che cambia dieci volte al secondo e riceve dieci fotogrammi al
    #       secondo **non ha nessun difetto**: ne ha uno se ne riceve tre.
    #     ⇒ Il metro giusto non e' un numero assoluto: e' **quanto di quel che
    #       la scena ha ridisegnato e' arrivato**.  ⛔ E il pavimento assoluto
    #       resta per le scene che chiedono in continuazione, dove vuol dire
    #       quel che `DECISIONI.md` §2.1 intendeva.
    #     ⭐ E' la stessa lezione di `REVIEWER.md` E15 da un altro capo: la
    #       grandezza che ordina i casi non e' sempre quella che sembra.
    if SCENA == "vero":
        ds = (n.get("disegni") or {}).get("disegni_s")
        if ds is None:
            return _muto("⚠ NON GIUDICO: senza i disegni della scena non so "
                         "quanti fotogrammi il desktop stesse CHIEDENDO")
        if ds <= 0:
            return _muto("⚠ la scena non ha disegnato: non c'e' una domanda da "
                         "confrontare con la consegna")
        reso = n["fps"] / ds
        if reso < RESA_MINIMA:
            return _no("⛔ ne arriva %.0f %% di quel che la scena ha "
                       "ridisegnato: %.2f fotogrammi/s consegnati contro %.2f "
                       "disegni/s (sotto il %.0f %%)"
                       % (100 * reso, n["fps"], ds, 100 * RESA_MINIMA))
        return _si("%.2f fot/s consegnati su %.2f disegni/s ⇒ resa %.0f %% "
                   "(peggior secondo %s/s)" % (n["fps"], ds, 100 * reso,
                                               n["fps_finestra_min"]))
    if n["fps"] < PAVIMENTO_FPS:
        return _no("⛔ %.2f/s di media, sotto il pavimento di %.0f/s (§2.1)"
                   % (n["fps"], PAVIMENTO_FPS))
    if n["fps_finestra_min"] is not None and n["fps_finestra_min"] < PAVIMENTO_FINESTRA:
        return _no("⛔ media %.2f/s ma il PEGGIOR SECONDO ne ha %d: sotto i %d "
                   "della finestra — la media sta assolvendo uno strappo"
                   % (n["fps"], n["fps_finestra_min"], PAVIMENTO_FINESTRA))
    return _si("%.2f/s di media, peggior secondo %s/s"
               % (n["fps"], n["fps_finestra_min"]))


def p_quota_chiavi(n):
    """⛔⭐ IL MECCANISMO ACCANTO AL SINTOMO — `LEZIONI.md` §1.31.

    `[M]` fase 9: la spirale di chiavi parte **cinque volte prima** del calo dei
    fotogrammi/s.  Un banco che guardasse solo il ritmo darebbe verde su un
    prodotto che sta gia' degenerando in sole chiavi — degradazione nello spazio
    **e** nel tempo insieme, che §3.3 vieta.
    """
    if not ha_misurato(n):
        return _muto("non misurato")
    if n.get("quota_delta") is None:
        return _muto("⚠ NON GIUDICO: %d fotogrammi in tutto — con numeri cosi' "
                     "piccoli «una chiave su tre» non e' una spirale, e' "
                     "aritmetica" % n["fotogrammi"])
    if n["quota_delta"] < QUOTA_DELTA:
        return _no("⛔ SPIRALE DI CHIAVI: %d chiavi su %d fotogrammi (quota "
                   "delta %.3f, sotto %.2f) — il flusso sta degenerando, e i "
                   "fotogrammi/s non se ne sono ancora accorti"
                   % (n["chiavi"], n["fotogrammi"], n["quota_delta"], QUOTA_DELTA))
    return _si("%d chiavi su %d (quota delta %.3f)"
               % (n["chiavi"], n["fotogrammi"], n["quota_delta"]))


def p_I1(primo, adesso, quale, gradino, cpu_satura):
    """⛔⛔ L'INVARIANTE I1 — `DECISIONI.md` §4.6-bis, appaiato.

    *«Non si fa degradare chi sta gia' lavorando per far entrare chi arriva.»*
    ⇒ Si confronta la STESSA sessione con SE STESSA: il gradino in cui e'
    entrata contro il gradino di adesso.

    ⛔ E il predicato SI RIFIUTA dove la premessa manca, invece di accusare:
      · se uno dei due giri non ha numeri;
      · ⭐ se la macchina e' a CPU satura, perche' allora anche **la scena** gira
        piu' piano e il calo non e' attribuibile a noi — sarebbe la ferita di
        `LEZIONI.md` §1.26, *«un candidato misurato non e' una licenza di
        attribuzione»*;
      · se il calo sta fra la tolleranza e il sicuro: li' non so distinguerlo
        dal rumore, e un verde educato sarebbe peggio di un «non so».
    """
    if not ha_misurato(primo) or not ha_misurato(adesso):
        return _muto("uno dei due giri non ha numeri (s%d)" % quale)
    # ⛔ SUL BRACCIO «FERMA» I1 NON SI GIUDICA SUL RITMO, e non e' indulgenza.
    #    `[M]` §6.4-bis: un desktop fermo consegna **un fotogramma in 40,8 s**.
    #    Fra «uno» e «due» c'e' il +100 %, fra «due» e «uno» il −50 %: sarebbe
    #    rumore confrontato con rumore, e ogni gradino darebbe un rosso o un
    #    verde a caso.  ⇒ Su quel braccio la domanda «chi c'era peggiora?» si
    #    legge nelle RISORSE (memoria, CPU, GPU), che sono nella riga MACCHINA.
    if SCENA == "ferma":
        return _muto("⚠ NON GIUDICO I1 sul ritmo nel braccio «ferma»: %.3f/s → "
                     "%.3f/s sono numeri troppo piccoli perche' un rapporto fra "
                     "loro voglia dire qualcosa (s%d)"
                     % (primo["fps"], adesso["fps"], quale))
    if not primo["fps"]:
        return _muto("il primo giro di s%d ha zero fotogrammi/s: non c'e' un "
                     "rapporto da fare" % quale)
    calo = (primo["fps"] - adesso["fps"]) / primo["fps"]
    dett = ("s%d: %.2f/s al gradino %d → %.2f/s al gradino %d (%+.1f %%) · "
            "quota delta %.3f → %.3f"
            % (quale, primo["fps"], primo["gradino"], adesso["fps"], gradino,
               -100.0 * calo, primo["quota_delta"], adesso["quota_delta"]))
    if cpu_satura:
        return _muto("⚠ NON ATTRIBUISCO — la macchina e' a CPU satura, quindi "
                     "anche la scena a monte gira piu' piano: %s" % dett)
    if calo <= I1_TOLLERANZA:
        return _si(dett)
    if calo < I1_SICURO:
        return _muto("⚠ calo del %.1f %%, fra la tolleranza (%.0f %%) e il "
                     "sicuro (%.0f %%): NON lo distinguo dal rumore — %s"
                     % (100 * calo, 100 * I1_TOLLERANZA, 100 * I1_SICURO, dett))
    return _no("⛔ I1 VIOLATO — chi era gia' dentro e' PEGGIORATO: %s" % dett)


def p_clienti_non_sono_il_collo(d):
    """⛔ L'incarico lo chiede per nome: dieci clienti sulla stessa macchina
       possono diventare LORO il collo di bottiglia.  ⇒ Si misura e si dichiara,
       o si attribuisce alla macchina di prova un difetto che e' del banco."""
    q = d.get("cpu_clienti_quota")
    if q is None:
        return _muto("la CPU dei clienti non si e' letta")
    if q > QUOTA_CLIENTI:
        return _no("⛔ i clienti si prendono il %.1f %% della macchina (%.2f "
                   "nuclei su %s): oltre il %.0f %%, NESSUN numero di questo "
                   "gradino e' attribuibile al prodotto"
                   % (100 * q, d["cpu_clienti_nuclei"], d.get("cpu_nuclei"),
                      100 * QUOTA_CLIENTI))
    return _si("i clienti costano %.2f nuclei (%.1f %% della macchina), il "
               "server %.2f" % (d["cpu_clienti_nuclei"], 100 * q,
                                d.get("cpu_server_nuclei")))


def p_metro_gpu(d):
    """⛔ IL METRO SI CONTROLLA DOVE IL NUMERO SI CONSUMA (`LEZIONI.md` §1.29).

    Un motore della GPU e' uno solo e serve una richiesta per volta: la somma di
    tutti i clienti su un motore non puo' superare il tempo di parete.  Sopra il
    105 % il metro sta contando due volte — quasi sempre perche' la
    deduplicazione per `drm-client-id` non ha funzionato.
    """
    if not d.get("gpu_pc"):
        return _muto("nessun motore della GPU letto")
    if d.get("gpu_negativi"):
        # ⛔ Non e' un rosso sul prodotto: e' un «non giudico» sul METRO.  Un
        #    motore non puo' lavorare per un tempo negativo; vuol dire che fra
        #    le due fotografie e' morto un contesto che portava un cumulativo.
        return _muto("⛔ NON GIUDICO — occupazione NEGATIVA su %s: fra le due "
                     "fotografie sono morti %s contesti e ne sono nati %s.  I "
                     "`drm-engine-*` sono cumulativi PER CONTESTO, e una somma "
                     "su una platea che cambia non e' un delta"
                     % (json.dumps(d["gpu_negativi"]),
                        (d.get("gpu_contesti") or {}).get("morti"),
                        (d.get("gpu_contesti") or {}).get("nati")))
    if not d.get("gpu_metro_sano"):
        return _no("⛔ IL METRO DELLA GPU NON E' SANO: %s con capacita' %s — un "
                   "motore non puo' stare oltre il 100 %% del tempo di parete "
                   "PER OGNI MOTORE che ha; sto contando lo stesso contesto piu' "
                   "volte" % (json.dumps(d["gpu_pc"]),
                              json.dumps(d.get("gpu_capacita"))))
    if d.get("gpu_altri_pdev"):
        return _no("⛔ ci sono descrittori su una scheda che NON e' %s: %s — "
                   "`DECISIONI.md` §4.6-quinquies vieta di misurare sulla "
                   "discreta, e la regola udev potrebbe essere saltata"
                   % (PDEV_BUONO, json.dumps(d["gpu_altri_pdev"])))
    return _si("motori (%% del tempo di parete): %s · uso della capacita': %s "
               "(capacita' %s) · GT %s MHz (min %s max %s) · RC6 %s %% · %s "
               "contesti, di cui %s NON miei · platea %s"
               % (json.dumps(d["gpu_pc"]), json.dumps(d.get("gpu_uso_pc")),
                  json.dumps(d.get("gpu_capacita")),
                  (d.get("gt") or {}).get("act_mhz"),
                  (d.get("gt") or {}).get("min_mhz"),
                  (d.get("gt") or {}).get("max_mhz"),
                  (d.get("gt") or {}).get("rc6_pc"),
                  d.get("gpu_clienti"), d.get("gpu_estranei"),
                  json.dumps(d.get("gpu_contesti"))))


def p_gpu_vede_la_codifica(d, fotogrammi):
    """⛔⛔ IL METRO DELLA GPU SI TARA DOVE IL NUMERO SI CONSUMA.

    `[M]` 24 agosto 2026, a macchina ferma: `drm-engine-video` sta a **0,0 %**,
    e va bene — nessuno codifica.  ⚠ Ma uno **zero mentre passano migliaia di
    fotogrammi H.264** non e' «la GPU non lavora»: e' una delle due cose, e sono
    tutt'e due gravi e diverse fra loro —

      · o il metro e' CIECO (l'`fdinfo` del figlio non si legge, il motore ha un
        altro nome su questo kernel, la deduplicazione butta la voce giusta);
      · o ⛔ **il codificatore e' ripiegato in CPU senza dirlo**, che e' la forma
        d'errore **E2** di `REVIEWER.md` e la ferita che `LEZIONI.md` §1.8 dice
        di dichiarare invece di subire.

    ⇒ Il predicato non sceglie fra le due: **si rifiuta**, e le nomina tutt'e
      due.  ⭐ Il numero che le separa e' la CPU del server, che sta nella stessa
      riga: un ripiego in CPU si vede li'.
    """
    if not d.get("gpu_pc"):
        return _muto("nessun motore della GPU letto")
    video = max(d["gpu_pc"].get("video", 0.0),
                d["gpu_pc"].get("video-enhance", 0.0))
    if fotogrammi <= 0:
        return _muto("nessun fotogramma consegnato: non c'e' niente da vedere")
    if video <= 0.0:
        return _muto("⛔ NON GIUDICO — %d fotogrammi consegnati e il motore "
                     "VIDEO della GPU sta a 0,0 %%: o il metro e' cieco, o il "
                     "codificatore e' ripiegato in CPU senza dirlo (E2).  La "
                     "CPU del server in questo gradino: %s nuclei"
                     % (fotogrammi, d.get("cpu_server_nuclei")))
    return _si("il motore video sta al %.1f %% mentre passano %d fotogrammi: il "
               "metro vede la codifica, e la codifica e' in GPU"
               % (video, fotogrammi))


def p_ancora(fette, quale, gradino):
    """⛔⛔ L'ANCORA CONTRO IL CONTO LETTO DAL GRADINO PRECEDENTE.

    ⚠ E' successo davvero in fase 9: tre profili di fila hanno riferito gli
      stessi identici numeri, perche' la riga di «conto finale» arrivava fino a
      29 s tardi e il gradino leggeva quella del gradino prima.

    ⇒ Qui i `numero` di §6.2 crescono di uno per ogni fotogramma che il server
      DECIDE di spedire.  ⇒ Se il gradino N e il gradino N-1, per la stessa
      sessione, condividono anche un solo `numero`, uno dei due sta leggendo
      l'altro.  ⛔ Non e' una statistica: e' un fatto, e non ha tolleranza.
    """
    prima = fette.get((gradino - 1, quale))
    ora = fette.get((gradino, quale))
    if not ora or not ora.get("numeri"):
        return _muto("il gradino %d non ha numeri per s%d" % (gradino, quale))
    if not prima or not prima.get("numeri"):
        return _si("primo gradino di s%d: niente da confrontare (numeri "
                   "%d…%d)" % (quale, ora["numeri"][0], ora["numeri"][1]))
    if ora["numeri"][0] <= prima["numeri"][1]:
        return _no("⛔ LO STESSO CONTO DUE VOLTE: s%d al gradino %d porta i "
                   "`numero` %d…%d, e al gradino %d portava %d…%d — si "
                   "sovrappongono"
                   % (quale, gradino, ora["numeri"][0], ora["numeri"][1],
                      gradino - 1, prima["numeri"][0], prima["numeri"][1]))
    return _si("numeri %d…%d, dopo i %d…%d del gradino prima"
               % (ora["numeri"][0], ora["numeri"][1], prima["numeri"][0],
                  prima["numeri"][1]))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA FETTA DI UN GRADINO
# ═══════════════════════════════════════════════════════════════════════════
def fetta(i, t0, t1, durata):
    """Il giornale di s`i` fra `t0` e `t1`, ridotto con `misura()` di 09-b70."""
    rc, out, err = root("python3 %s/10-b92-fetta.py %s %.3f %.3f | gzip | "
                        "base64 -w0" % (LAV, giornale_di(i), t0, t1), 300)
    try:
        import gzip
        crudo = json.loads(gzip.decompress(base64.b64decode(out.strip())))
    except Exception as e:
        return {"esito": "⛔ la fetta non si e' letta: %s — %s"
                         % (e, (out + err)[-160:])}
    if crudo.get("esito") != "letto":
        return {"esito": crudo.get("esito", "?")}
    g = crudo["giornale"]
    # ⛔ `scaldata_s=0`: la scaldata di QUESTA sessione e' gia' fuori dalla
    #    finestra (si aspetta ASSESTAMENTO_S dopo ogni apertura).  Toglierne
    #    altra qui vorrebbe dire togliere due volte.
    n = B70.misura(g, durata, scaldata_s=0.0)
    # ⛔⛔ IL BRACCIO «FERMA» CADE SOTTO IL MINIMO DELLA RIDUZIONE, ED E' GIUSTO.
    #
    #    `misura()` di 09-b70 si rifiuta sotto i 30 fotogrammi a regime, e ha
    #    ragione: sotto quel numero non c'e' niente da RIDURRE — nessun peggior
    #    secondo, nessuna quota di chiavi che voglia dire qualcosa.
    #    ⚠ Ma su un desktop **fermo** quello e' il caso NORMALE, non un guasto:
    #      `[M]` §6.4-bis, **un fotogramma in 40,8 s**.  ⇒ Se il braccio `ferma`
    #      usasse `ha_misurato()` cosi' com'e', ogni suo gradino sarebbe «non
    #      misurato» e l'intero braccio non direbbe niente.
    #    ⇒ Si CONTA quel che si puo' contare — fotogrammi, byte, chiavi,
    #      ritardo — e ⛔ **le colonne che non si possono calcolare restano
    #      `None`**, non zero, e il fatto si porta scritto dentro il risultato.
    if SCENA == "ferma" and n.get("esito") != "misurato":
        n = conto_scarno(g, durata, n)
    n["ritardo"] = ritardi(g)
    n["righe_nel_file"] = crudo.get("righe_nel_file")
    if g:
        num = sorted(f["numero"] for f in g)
        n["numeri"] = [num[0], num[-1]]
        n["finestra_ms"] = [round(g[0]["arrivo_ms"] - t0, 1),
                            round(t1 - g[-1]["arrivo_ms"], 1)]
    return n


def stampa_riga(i, n):
    """⛔ §6.2 di `LEZIONI.md`: si stampano TUTTE le grandezze.  Una tabella con
       una colonna sola non e' una misura corta: e' una misura ORIENTATA."""
    if not ha_misurato(n):
        _dub("s%-2d  %s" % (i, n.get("esito", "?")))
        return
    r = n["ritardo"]
    # ⛔ «-» dove il numero non c'e': un `None` stampato come 0 sarebbe una
    #    colonna che mente, e il braccio «ferma» ne ha tre per costruzione.
    def q(v, forma="%s"):
        return "-" if v is None else forma % v
    d = (n.get("disegni") or {}).get("disegni_s")
    _inf("s%-2d  %6.2f/s (peggior sec %3s)  chiavi %3d/%-5d q.delta %5s  "
         "%6d B/fot  %8s Mbit/s  ritardo med %s ms p95 %s max %s  buchi %s  "
         "disegni %s/s"
         % (i, n["fps"], q(n.get("fps_finestra_min")), n["chiavi"],
            n["fotogrammi"], q(n.get("quota_delta"), "%.3f"),
            n["byte_per_fotogramma"], q(n.get("mbit_s_carico"), "%.4f"),
            r["mediano_ms"], r["p95_ms"], r["massimo_ms"],
            q(n.get("buchi_numero")), q(d, "%.2f")))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL TERRENO
# ═══════════════════════════════════════════════════════════════════════════
def terreno(quanti):
    _log("IL TERRENO — porta %d · %d utenti · albero %s" % (PORTA, quanti, ALB))
    guai = []
    rc, out, _ = root("ss -uln | grep -c ':%d ' || true" % PORTA)
    if out.strip() == "0":
        guai.append("nessuno ascolta sulla %d: «bash banchi/10-b91-terreno-"
                    "dieci.sh accendi»" % PORTA)
    conto = []
    for p in VICINE:
        rc, o, _ = root("ss -uln | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    _inf("ascoltatori NON miei (si contano, non si toccano): %s" % " ".join(conto))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    rc, out, _ = root("test -s %s/banchi/01-b3-cliente.py && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("l'albero «%s» non porta 01-b3-cliente.py" % ALB)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENA_BIN)
    if "si" not in out:
        guai.append("la scena «%s» non e' eseguibile" % SCENA_BIN)
    for sorg, nome in ((CLIENTE, "10-b92-cliente.py"), (FETTA, "10-b92-fetta.py"),
                       (SONDA, "10-b92-sonda.py"), (CONTI, "10-b92-conti.py"),
                       (SCENE, "10-b92-scene.py")):
        if not spedisci(sorg, nome):
            guai.append("«%s» non si e' scritto in %s" % (nome, LAV))
    # ⛔ E l'ESC che esce dalla vista d'insieme e' `09-b72-tasto.py`, che non e'
    #    scritto qui dentro: si spedisce **il file vero**, non una copia.  ⚠ Una
    #    copia che diverge e' un attrezzo che mente (`LEZIONI.md` §1.35).
    if SCENA in ("vero", "ferma"):
        perc = os.path.join(QUI, "09-b72-tasto.py")
        if not os.path.exists(perc):
            guai.append("manca «%s»: senza l'ESC la sessione resta nella vista "
                        "d'insieme e le finestre sono anteprime (09-b72)" % perc)
        else:
            with open(perc) as f:
                if not spedisci(f.read(), "09-b72-tasto.py"):
                    guai.append("«09-b72-tasto.py» non si e' scritto in %s" % LAV)
    # ⛔⛔ IL PALCO ORFANO — si guarda PRIMA di misurare.
    #
    # ⚠⚠ E QUI IL BANCO HA SBAGLIATO UNA VOLTA, IL 24 AGOSTO 2026, PRIMA DI
    #    MISURARE QUALSIASI COSA.  La prima stesura contava **tutti** i processi
    #    dell'uid, e ha dato rosso su undici utenti su undici.  ⛔ Ma quei
    #    processi non erano un palco orfano: erano `systemd --user`, `(sd-pam)`,
    #    `dbus-daemon` e compagnia, cioe' **quel che `enable-linger` fa nascere
    #    apposta** — `[M]` **sette processi per utente**, prima che nessuna
    #    sessione grafica esista.  ⇒ Un banco che li avesse chiamati «orfani»
    #    avrebbe preteso di sgomberare proprio la cosa che il terreno esiste per
    #    tenere in piedi.
    # ⇒ ⭐ L'orfano si riconosce dai processi del PALCO, per nome, e sono quelli
    #   che il prodotto fa nascere: `gnome-shell`, `gnome-session`, `mutter`,
    #   `Xwayland`, il figlio `remotix` e la mia scena.  ⚠ La stessa lista sta in
    #   `10-b91-terreno-dieci.sh`: due liste in due file divergono, e questa e'
    #   la prima cosa da unire se una terza ne avesse bisogno.
    PALCO = "gnome-shell|gnome-session|mutter|Xwayland|04-b30-scena|remotix"
    orfani, base = [], {}
    for i in range(1, quanti + 1):
        rc, tutti, _ = root("pgrep -u %d -c 2>/dev/null || echo 0" % uid(i))
        base[utente(i)] = tutti.strip()
        rc, out, _ = root("pgrep -u %d -a 2>/dev/null | grep -E '%s' || true"
                          % (uid(i), PALCO))
        righe = [x.strip() for x in out.splitlines() if x.strip()]
        if righe:
            orfani.append("%s (uid %d): %d processi del PALCO — %s"
                          % (utente(i), uid(i), len(righe),
                             " / ".join(x[:60] for x in righe[:3])))
    _inf("processi per utente prima della salita (⭐ e' il fondo che "
         "`enable-linger` tiene acceso, non un palco): %s"
         % " ".join("%s:%s" % (k.replace("provamt", "s"), v)
                    for k, v in base.items()))
    if orfani:
        guai.append("⛔⛔ PALCO ORFANO del giro precedente — in fase 9 un palco "
                    "orfano non dava rosso, dava UN NUMERO PLAUSIBILE:\n        "
                    + "\n        ".join(orfani)
                    + "\n        ⇒ «bash banchi/10-b91-terreno-dieci.sh sgombra»")
    for g in guai:
        _ko(g)
    if not guai:
        _ok("il terreno c'e', ed e' mio: nessun palco orfano, i quattro attrezzi "
            "sono sulla macchina")
    return not guai


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL LUCCHETTO DELLA GPU
# ═══════════════════════════════════════════════════════════════════════════
def _lucchetto():
    os.environ["LUCCHETTO"] = LUCCHETTO
    spec = importlib.util.spec_from_file_location(
        "luc", os.path.join(QUI, "09-lucchetto.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ UNO PER VOLTA — ciascuno arriva a SESSIONE da solo, PRIMA della salita
# ═══════════════════════════════════════════════════════════════════════════
def uno_per_volta(quanti, secondi=14):
    _log("⛔ CIASCUNO DEI %d ARRIVA A «SESSIONE» DA SOLO" % quanti)
    _inf("⚠ senza questo passo, un rosso al gradino 5 della salita non si sa se "
         "e' del numero cinque o del quinto utente provvisto male")
    esiti, guai = [], []
    for i in range(1, quanti + 1):
        t0 = time.time()
        aperta, detto = apri_sessione(i, secondi)
        ms = int(1000 * (time.time() - t0))
        if not aperta:
            _ko("s%d (%s): %s" % (i, utente(i), detto))
            guai.append(i)
            esiti.append({"i": i, "aperta": False, "perche": detto})
            # ⛔ NON si continua contandone gli altri: se questo utente non si
            #    apre da solo, la salita misurerebbe una popolazione diversa da
            #    quella che dichiara.
            break
        _ok("s%d (%s) aperta in %d ms — %s" % (i, utente(i), ms, detto))
        esiti.append({"i": i, "aperta": True, "ms": ms, "detto": detto})
        # ⛔ Si aspetta che se ne vada DA SOLA: un `kill -9` non manda il
        #    CONGEDO, il posto resta occupato e il giro dopo si becca
        #    `GIA_ATTIVA_REMOTA` (`09-b71-sessione.sh`, `[M]` 23 ago).
        for _ in range(int(secondi) + 40):
            time.sleep(1.0)
            if not vivo(i):
                break
        else:
            _dub("s%d non se n'e' andata da sola: la salita potrebbe trovarne "
                 "il posto occupato" % i)
        # ⛔ E il palco si chiude, o il prossimo utente non e' piu' «da solo»:
        #    il palco sopravvive al distacco (I4) e a fine giro sarebbero dieci
        #    palchi in piedi invece di uno.
        chiudi_palco(i)
        time.sleep(2)
    return esiti, guai


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA SALITA
# ═══════════════════════════════════════════════════════════════════════════
def salita(quanti, durata, doppia, resta):
    esiti = {"quanti": quanti, "durata_s": durata, "gradini": [],
             "tela": TELA, "codec": CODEC_CHIESTO, "scena": SCENA,
             "strappo": {"quiete_s": STRAPPO_QUIETE,
                         "accensione_s": STRAPPO_ACCENSIONE,
                         "finestra": FINESTRA_VERO} if SCENA == "vero" else None}
    fette = {}          # (gradino, sessione) → numeri
    prima_volta = {}    # sessione → i numeri del gradino in cui e' entrata
    rossi, muti = [], []
    provenienze = {}

    _log("LA SALITA — da 1 a %d sessioni, %s a testa, gradini da %d s a regime"
         % (quanti, TELA, durata))
    _inf("⛔ le cure della fase 9 sono ACCESE per predefinito (`CODER.md` "
         "§2-bis): soglia 100 ms, regolatore del ritmo, linea morta, sfratto "
         "15 000 ms, silenzio dell'audio.  Questo banco NON le spegne e non "
         "confronta col passato")
    _inf("⛔ i clienti girano SULLA MACCHINA DI PROVA (chroot `enter.sh`): il "
         "filo e' `lo`, non una rete vera.  Il loro costo si misura a parte")
    if SCENA == "satura":
        _inf("⭐ BRACCIO «SATURA» — L'ANCORA.  ⚠ «pieno» satura il codificatore "
             "di proposito (PIANO.md fase 10): il numero che ne esce e' un "
             "PAVIMENTO, non il desktop medio.  ⛔ Deve ritrovare il SEI del "
             "primo giro (§6.5), o le altre due scene non hanno metro")
    elif SCENA == "vero":
        _inf("⭐ BRACCIO «VERO» — due finestre vere (nautilus + gnome-terminal) "
             "piu' la scena IN FINESTRA %s a STRAPPI (%.2f s ferma / %.2f s "
             "accesa), e l'ESC per uscire dalla vista d'insieme.  ⭐ E' la "
             "stessa definizione di `10-b89` §6.4-bis, per poterle confrontare"
             % (FINESTRA_VERO, STRAPPO_QUIETE, STRAPPO_ACCENSIONE))
    else:
        _inf("⭐ BRACCIO «FERMA» — il desktop aperto e nessuno che tocca niente. "
             "⛔ E' il caso PIU' COMUNE in un multi-tenant vero, e `[M]` §6.4-bis "
             "dice che costa GPU ZERO: RC6 100 %, GT 0 MHz")
    _inf("⚠ i tre bracci differiscono anche per l'ESC: «satura» NON lo manda, "
         "perche' e' la strada del primo giro riga per riga, e un'ancora "
         "«migliorata» non e' piu' un'ancora.  Dichiarato, non nascosto")

    for g in range(1, quanti + 1):
        _log("GRADINO %d/%d — arriva s%d (%s)" % (g, quanti, g, utente(g)))
        t_apre = time.time()
        aperta, detto = apri_sessione(g, resta)
        ms_apre = int(1000 * (time.time() - t_apre))
        if not aperta:
            # ⛔ ROSSO, E LA SALITA SI FERMA.  Un banco che continuasse
            #    contandone nove misurerebbe il gradino 10 con nove sessioni.
            _ko(detto)
            esiti["gradini"].append({"gradino": g, "aperta": False,
                                     "perche": detto})
            rossi.append("gradino %d · la sessione non si apre" % g)
            esiti["fermata_al_gradino"] = g
            break
        # ⭐ Il tempo di apertura dell'ennesima sessione: una delle risposte
        #    che `PIANO.md` fase 10 cerca.  ⚠ Ci sta dentro anche l'attesa del
        #    mio `pgrep` a un secondo di passo, quindi e' un TETTO, non un
        #    cronometro: `uno-per-volta` da' lo stesso numero a macchina vuota.
        _ok("s%d aperta in %d ms (⚠ tetto, non cronometro) — %s"
            % (g, ms_apre, detto))
        esiti.setdefault("apertura_ms", {})[g] = ms_apre
        usc = accendi_scena(g)
        if not usc:
            # ⛔ Non si salta il gradino e basta: quella sessione resterebbe
            #    senza scena per TUTTA la salita, cioe' dentro il conto come
            #    viva e ferma.  Si dichiara, e `assicura_scene` riprovera' a
            #    ogni gradino.
            _ko("⛔ la scena di s%d non parte: quella sessione NON si giudica "
                "finche' non riparte" % g)
            muti.append("gradino %d · la scena di s%d non parte" % (g, g))
            # ⛔⛔ E AL PRIMO GRADINO LA SALITA SI FERMA, non prosegue.
            #     Al gradino 1 non c'e' nessun'altra sessione da misurare: una
            #     salita che continuasse misurerebbe undici gradini di uno
            #     schermo fermo e terrebbe il lucchetto della GPU per mezz'ora
            #     per non dire niente.  ⚠ E' la stessa forma di «la prova non
            #     morde» (`LEZIONI.md` §1.30), vista dal lato del costo.
            if g == 1:
                _ko("⛔ NON PROSEGUO: al primo gradino la scena e' tutto quel "
                    "che c'e' da misurare")
                rossi.append("gradino 1 · la scena non parte: salita fermata")
                esiti["fermata_al_gradino"] = 1
                break
        else:
            _inf("scena «%s» di s%d sul monitor %s ⭐ (il predefinito SATURA: "
                 "PIANO.md fase 10)" % (MOVIMENTO, g, usc))
        provenienze, posti = mappa_provenienze()

        for etichetta, quanto in ([("normale", durata)] +
                                  ([("doppia", 2 * durata)]
                                   if (doppia and g == quanti) else [])):
            if etichetta == "doppia":
                _log("⭐ GRADINO %d, SECONDA DURATA (%d s) — `LEZIONI.md` "
                     "§1.32: i giri corti sottostimano" % (g, quanto))
            riaccese = assicura_scene(g)
            _inf("assestamento %.0f s (apertura, prima chiave, prima tela: si "
                 "tolgono e si dice)" % ASSESTAMENTO_S)
            time.sleep(ASSESTAMENTO_S)

            # ⛔⛔ L'ANCORA, e la porta la SONDA STESSA.
            #
            # ⭐ La fotografia dichiara il proprio `t_ms` — l'orologio monotono
            #    della macchina all'istante in cui e' stata scattata — e quello
            #    e' il confine del gradino.  ⇒ La finestra dei fotogrammi e la
            #    finestra di CPU, GPU, memoria e byte sul filo sono **la stessa
            #    finestra**, non due finestre vicine.  ⚠ Un `orologio()` a parte
            #    sarebbe un secondo giro di ssh, cioe' uno o due secondi di
            #    scarto fra le due — su quarantacinque, il 4 %.
            f0 = sonda(quanti)
            r0 = registro_righe()
            # ⭐ I DISEGNI DELLA SCENA: l'INGRESSO della prova, accanto
            #   all'uscita.  ⛔ Fuori dal braccio `ferma`, dove non c'e' nessuna
            #   scena e il contatore non esiste — e «non esiste» va detto, non
            #   scritto zero.
            dis0 = disegni_tutte(g) if SCENA != "ferma" else None
            if f0 is None or f0.get("t_ms") is None:
                _ko("⛔ non ho l'ancora del gradino %d: NON misuro" % g)
                muti.append("gradino %d · niente ancora" % g)
                continue
            t0 = f0["t_ms"]
            # ⛔ E L'ANCORA DEVE AVANZARE.  Se il confine di questo gradino non
            #    sta DOPO quello del gradino prima, la fetta prenderebbe i
            #    fotogrammi di quello — ed e' il difetto che in fase 9 ha fatto
            #    riferire a tre profili di fila gli stessi identici numeri.
            if esiti.get("ultimo_t1") is not None and t0 <= esiti["ultimo_t1"]:
                _ko("⛔ L'ANCORA NON AVANZA: il gradino %d comincia a %.0f e il "
                    "precedente finiva a %.0f — NON misuro"
                    % (g, t0, esiti["ultimo_t1"]))
                rossi.append("gradino %d · l'ancora non avanza" % g)
                break
            time.sleep(quanto)
            dis1 = disegni_tutte(g) if SCENA != "ferma" else None
            f1 = sonda(quanti)
            r1 = registro_righe()
            if f1 is None or f1.get("t_ms") is None:
                _ko("⛔ l'ancora finale del gradino %d non si legge" % g)
                muti.append("gradino %d · niente ancora finale" % g)
                continue
            t1 = f1["t_ms"]
            esiti["ultimo_t1"] = t1

            d = fra(f0, f1, quanti)
            # ⛔ Chi e' vivo e chi disegna: una scena morta e «il prodotto ha
            #    smesso di consegnare» hanno lo stesso aspetto, e solo uno dei
            #    due e' un difetto del prodotto.
            vive, scene, non_so = chi_c_e(g)
            if non_so:
                _dub("⚠ di %s non ho saputo dire se sono vive: NON le giudico"
                     % ", ".join("s%d" % i for i in non_so))
                for i in non_so:
                    vive[i], scene[i] = True, False
            morte = [i for i in range(1, g + 1) if not scene.get(i)]
            if morte:
                _dub("⚠ le scene di %s NON disegnano piu': quelle sessioni non "
                     "si giudicano in questo gradino"
                     % ", ".join("s%d" % i for i in morte))
            voce = {"gradino": g, "quale": etichetta, "durata_s": quanto,
                    "t0": t0, "t1": t1, "macchina": d, "vive": vive,
                    "scene": scene, "riaccese": riaccese,
                    "sessioni": {}, "predicati": []}

            _inf("MACCHINA  CPU %s %% (%s nuclei)  ·  server %s nuclei · "
                 "clienti %s nuclei"
                 % (d.get("cpu_occupata_pc"), d.get("cpu_nuclei"),
                    d.get("cpu_server_nuclei"), d.get("cpu_clienti_nuclei")))
            _inf("MEMORIA   PSS sessioni %s MiB · PSS server %s MiB · PSS "
                 "totale %s MiB   ⚠ per confronto, RSS sommati: %s MiB (la "
                 "differenza e' quel che dieci desktop CONDIVIDONO)"
                 % (d.get("pss_sessioni_mib"), d.get("pss_server_mib"),
                    d.get("pss_totale_mib"),
                    round((d.get("rss_sessioni_mib") or 0)
                          + (d.get("rss_server_mib") or 0), 1)))
            _inf("GPU       %s  ⇒ uso della capacita' %s  (capacita' %s)"
                 % (json.dumps(d.get("gpu_pc")), json.dumps(d.get("gpu_uso_pc")),
                    json.dumps(d.get("gpu_capacita"))))
            _inf("          GT %s MHz (min %s, max %s%s) · RC6 %s %% ⇒ sveglia "
                 "%s %%  ⛔ l'occupazione dipende dalla FREQUENZA: `[M]` la "
                 "stessa codifica da' 26,35 %% a 300 MHz e 6,99 %% a 1550 "
                 "(10-b87 §CLOCK)"
                 % ((d.get("gt") or {}).get("act_mhz"),
                    (d.get("gt") or {}).get("min_mhz"),
                    (d.get("gt") or {}).get("max_mhz"),
                    ", BLOCCATA" if (d.get("gt") or {}).get("bloccata") else "",
                    (d.get("gt") or {}).get("rc6_pc"),
                    (d.get("gt") or {}).get("sveglia_pc")))
            _inf("          %s contesti su %s, di cui %s NON miei (i palchi "
                 "degli altri agenti)"
                 % (d.get("gpu_clienti"), PDEV_BUONO, d.get("gpu_estranei")))
            _inf("FILO      %s"
                 % json.dumps(d.get("filo")))
            _inf("          ⛔⛔ QUEI BYTE NON SONO MIEI.  `lo` porta anche i "
                 "clienti degli ALTRI agenti, che girano sulla stessa macchina: "
                 "`[M]` 24 ago, con UNA mia sessione da 1,6 Mbit/s il contatore "
                 "di `lo` diceva 35,6 Mbit/s.  ⇒ Il budget di rete si somma "
                 "dalle righe `rete-quic` delle MIE sessioni, piu' sotto.")
            _inf("          ⚠ e comunque `lo` ha MTU 65536 e nessun tetto di "
                 "gigabit: la rete vera questo banco non la prova")

            cpu_satura = (d.get("cpu_occupata_pc") or 0) >= 90.0
            for i in range(1, g + 1):
                if not vive.get(i):
                    # ⛔ `None`, non zero.  «Il cliente e' morto» non e' «non ha
                    #    consegnato niente»: sono due cose, e solo la seconda
                    #    sarebbe un difetto del prodotto.
                    voce["sessioni"][i] = {
                        "esito": "⛔ NON HO NIENTE DA GIUDICARE — il cliente %d "
                                 "e' MORTO durante il gradino: i suoi numeri "
                                 "sono None, non zero" % i}
                    _dub("s%-2d  ⛔ il cliente e' morto durante il gradino: "
                         "None, non zero" % i)
                    muti.append("gradino %d · s%d · cliente morto" % (g, i))
                    continue
                if not scene.get(i):
                    voce["sessioni"][i] = {
                        "esito": "⛔ NON HO NIENTE DA GIUDICARE — la SCENA di "
                                 "s%d non disegnava piu' in questo gradino: "
                                 "pochi byte per fotogramma sarebbero un difetto "
                                 "MIO, non del prodotto" % i}
                    _dub("s%-2d  ⛔ la scena non disegna: non giudico" % i)
                    muti.append("gradino %d · s%d · scena morta" % (g, i))
                    continue
                n = fetta(i, t0, t1, quanto)
                n["gradino"] = g
                # ⭐ QUANTO LA SCENA HA DAVVERO CAMBIATO LO SCHERMO, accanto a
                #   quel che ne e' uscito.  ⛔ `{"disegni_s": None, ...}` dove non
                #   si e' letto: mai zero.
                n["disegni"] = ({"disegni_s": 0.0,
                                 "esito": "braccio «ferma»: NESSUNA scena, e "
                                          "zero e' un fatto per costruzione, "
                                          "non una lettura"}
                                if SCENA == "ferma"
                                else fra_disegni(dis0, dis1, i, quanto))
                voce["sessioni"][i] = n
                if etichetta == "normale":
                    fette[(g, i)] = n
                    if i not in prima_volta and ha_misurato(n):
                        prima_volta[i] = n
                stampa_riga(i, n)

            # ── I predicati, e ciascuno con il suo nome ──
            def registra(nome, esito, dove=""):
                passa, perche = esito
                voce["predicati"].append({"predicato": nome, "passa": passa,
                                          "perche": perche})
                (_ok if passa else (_dub if passa is None else _ko))(
                    "%s%s: %s" % (nome, dove, perche))
                marca = "gradino %d%s · %s%s" % (
                    g, "" if etichetta == "normale" else " (doppia)", nome, dove)
                if passa is False:
                    rossi.append(marca)
                elif passa is None:
                    muti.append("%s — %s" % (marca, perche))

            registra("il metro della GPU e' sano", p_metro_gpu(d))
            consegnati = sum(x["fotogrammi"] for x in voce["sessioni"].values()
                             if ha_misurato(x))
            registra("il metro della GPU vede la codifica",
                     p_gpu_vede_la_codifica(d, consegnati))
            registra("i clienti non sono il collo",
                     p_clienti_non_sono_il_collo(d))
            for i in range(1, g + 1):
                n = voce["sessioni"].get(i)
                registra("la scena «%s» morde" % SCENA, p_scena_morde(n),
                         " · s%d" % i)
                registra("il ritmo tiene il pavimento", p_ritmo(n), " · s%d" % i)
                registra("niente spirale di chiavi", p_quota_chiavi(n),
                         " · s%d" % i)
                if etichetta == "normale":
                    registra("l'ancora del gradino", p_ancora(fette, i, g),
                             " · s%d" % i)
                # ⛔⛔ I1: chi era gia' dentro non peggiora.
                if i < g and i in prima_volta:
                    registra("⛔ I1 — chi era gia' dentro NON peggiora",
                             p_I1(prima_volta[i], n, i, g, cpu_satura),
                             " · s%d" % i)

            voce["server"] = conti_server(r0, r1, provenienze)
            if voce["server"].get("posti_occupati") is None:
                voce["server"]["posti_occupati"] = posti
            _inf("SERVER    posti occupati %s · negati %s · spirale (in somma, "
                 "⚠ NON attribuibile ai singoli figli) %s"
                 % (voce["server"].get("posti_occupati"),
                    len(voce["server"].get("posti_negati") or []),
                    json.dumps(voce["server"].get("spirale_in_somma"))))
            mio_filo, quante = 0.0, 0
            for u, v in sorted((voce["server"].get("per_utente") or {}).items()):
                if "provenienza" in v:
                    mio_filo += v["mbit_s"]
                    quante += 1
                    _inf("          %-10s %s · %s Mbit/s sul filo · %d "
                         "pacchetti (%d persi) · cwnd mediana %s · srtt %s ms"
                         % (u, v["provenienza"], v["mbit_s"],
                            v["pacchetti_spediti"], v["persi"],
                            v["cwnd_mediana"], v["srtt_ms_mediano"]))
            carico = sum(x["mbit_s_carico"] for x in voce["sessioni"].values()
                         if ha_misurato(x))
            voce["mio_filo_mbit_s"] = round(mio_filo, 2)
            voce["mio_carico_mbit_s"] = round(carico, 2)
            _inf("          ⭐ IL MIO FILO: %.2f Mbit/s su %d sessioni (dai "
                 "contatori QUIC del server) · carico utile %.2f Mbit/s (dai "
                 "giornali dei clienti) — la differenza e' involucro, riscontri "
                 "e ritrasmissioni" % (mio_filo, quante, carico))
            esiti["gradini"].append(voce)

    return esiti, rossi, muti, fette, prima_volta


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ QUANTI NE STANNO — e l'ANCORA che dice se il numero e' confrontabile
# ═══════════════════════════════════════════════════════════════════════════
def capienza(esiti):
    """⭐ IL NUMERO CHE LA FASE CERCA: il gradino piu' alto in cui **tutte** le
       sessioni vive stanno sopra il pavimento di §2.1 e **nessuna** di quelle
       che c'erano gia' e' peggiorata.

    ⛔ E non e' «il gradino prima del primo rosso»: e' il piu' alto che regge,
       perche' un gradino singolo che si rifiuta (`None`) non e' un gradino che
       cede.  ⚠ Un `None` non alza e non abbassa: si conta a parte e si dichiara.

    ⛔ Torna `(numero, perche', dettaglio)`, e `numero` e' `None` sul braccio
       `ferma`: li' il ritmo consegnato e' ~0 **per costruzione**, e un
       pavimento di 25 fot/s su quella grandezza non vuol dire niente.  ⇒ Su
       quel braccio la capienza la pongono le RISORSE, e si leggono a parte.
    """
    if SCENA == "ferma":
        return (None, "⚠ NON DEFINITA sul braccio «ferma»: il pavimento di %.0f "
                      "fot/s (§2.1) e' di un desktop che LAVORA, e qui non se "
                      "ne consegna nessuno per costruzione.  ⇒ Quel che si legge "
                      "in questo braccio sono le RISORSE, non la capienza"
                % PAVIMENTO_FPS, {})
    gradini = [v for v in esiti.get("gradini", [])
               if v.get("quale") == "normale" and v.get("sessioni")]
    regge, dett = 0, {}
    for v in gradini:
        g = v["gradino"]
        sotto, muti_qui, viste = [], [], 0
        for i, n in sorted(v["sessioni"].items()):
            if not ha_misurato(n):
                muti_qui.append(i)
                continue
            viste += 1
            if n["fps"] < PAVIMENTO_FPS:
                sotto.append("s%d:%.2f/s" % (i, n["fps"]))
        rossi_i1 = [p for p in v.get("predicati", [])
                    if p["passa"] is False and "I1" in p["predicato"]]
        dett[g] = {"viste": viste, "sotto_pavimento": sotto,
                   "non_giudicate": muti_qui, "rossi_I1": len(rossi_i1)}
        if viste == 0:
            continue
        if not sotto and not rossi_i1:
            regge = g
        # ⛔ E non si continua a cercare piu' su: la prima volta che cede, cede.
        #    ⚠ Un gradino che tornasse verde dopo uno rosso vorrebbe dire che la
        #      macchina si e' ripresa da sola, e allora il rosso era rumore — ma
        #      qui il rosso di sotto NON e' rumore: e' che a quel gradino c'era
        #      una sessione in meno.
        elif regge:
            break
    return (regge, "⭐ `[M]` %d sessioni «%s» stanno insieme su questa macchina "
                   "(Intel UHD 730 INTEGRATA): a %d tutte sopra il pavimento di "
                   "%.0f fot/s e nessun I1 violato" % (regge, SCENA, regge,
                                                       PAVIMENTO_FPS), dett)


def p_ancora_ritrova(numero):
    """⛔⛔ IL CONTROLLO CHE RENDE CONFRONTABILI LE ALTRE DUE MISURE.

    Il braccio `satura` non serve a scoprire niente: serve a **rifare** la
    misura del primo giro con lo stesso codice, sullo stesso ferro, nello stesso
    pomeriggio.  ⇒ Se non ritrova il **sei** di `fasi/10-…md` §6.5, allora fra i
    due giri e' cambiato **qualcos'altro insieme alla scena** — il carico della
    macchina, un palco orfano, una cura, un utente provvisto male — e ⛔ **i
    numeri dei bracci `vero` e `ferma` non si possono confrontare con niente**.

    ⚠ E la tolleranza e' ZERO, ed e' voluto: «cinque invece di sei» non e' un
      arrotondamento, e' un'altra macchina.
    """
    if SCENA != "satura":
        return _muto("questo non e' il braccio d'ancora (scena «%s»)" % SCENA)
    if numero is None:
        return _muto("⛔ la capienza non si e' calcolata: non ho niente da "
                     "confrontare col primo giro")
    if numero != CAPIENZA_ANCORA:
        return _no("⛔⛔ L'ANCORA NON RITROVA IL NUMERO DEL PRIMO GIRO: adesso "
                   "ne stanno %d, il 24 agosto ne stavano %d (§6.5).  ⇒ Fra i "
                   "due giri e' cambiato qualcos'altro insieme alla scena, e "
                   "⛔ IL CONFRONTO FRA LE TRE SCENE NON VALE: i numeri di "
                   "«vero» e «ferma» non hanno un metro"
                   % (numero, CAPIENZA_ANCORA))
    return _si("⭐ l'ancora ritrova il %d del primo giro (§6.5): le tre scene "
               "sono confrontabili fra loro" % numero)


def legge_del_costo(punti):
    """⭐⭐ «IL COSTO CRESCE CON QUANTO IL DESKTOP CAMBIA — E COME?»

    Una retta ai minimi quadrati su `(x, y)`, con **pendenza, intercetta ed
    errore**.  ⛔ E l'errore non e' un ornamento: se il costo fosse
    proporzionale il budget si puo' calcolare, e se ha un gradino no — e i due
    casi si distinguono guardando **quanto la retta sbaglia**, non quanto e'
    bella.

    ⛔ `None` sotto i tre punti: due punti stanno su una retta sempre, e una
       retta per due punti non e' una legge, e' una definizione.
    """
    p = [(x, y) for x, y in punti if x is not None and y is not None]
    if len(p) < 3:
        return None
    n = len(p)
    mx = sum(x for x, _ in p) / n
    my = sum(y for _, y in p) / n
    sxx = sum((x - mx) ** 2 for x, _ in p)
    if sxx <= 0:
        return None
    pend = sum((x - mx) * (y - my) for x, y in p) / sxx
    inter = my - pend * mx
    resti = [y - (inter + pend * x) for x, y in p]
    sst = sum((y - my) ** 2 for _, y in p)
    sse = sum(r * r for r in resti)
    return {"punti": n, "pendenza": pend, "intercetta": inter,
            "r2": (1 - sse / sst) if sst > 0 else None,
            "errore_massimo": max(abs(r) for r in resti),
            "errore_relativo_max": (max(abs(r) for r in resti) / my
                                    if my else None)}


def riassunto(esiti, fette, prima_volta, quanti):
    """⭐ LA CURVA — ed e' il risultato della fase, non la somma dei verdi."""
    _log("⭐ LA CURVA — la stessa sessione, gradino per gradino")
    gradini = [v for v in esiti["gradini"]
               if v.get("quale") == "normale" and v.get("sessioni")]
    if not gradini:
        _dub("nessun gradino ha prodotto numeri")
        return
    # ⛔⭐ TRE CURVE, NON UNA — `LEZIONI.md` §1.31: il sintomo dice quando
    #     l'utente se ne accorge, il MECCANISMO dice quando e' cominciato, e fra
    #     i due c'e' un fattore cinque.  ⇒ I fotogrammi/s (sintomo) non escono
    #     mai da soli: accanto ci sono la quota di CHIAVI (meccanismo) e il
    #     RITARDO, sulla stessa griglia e con le stesse colonne.
    def griglia(titolo, prendi, forma):
        print("\n   %s" % titolo)
        print("        %s" % "  ".join("g%-4d" % v["gradino"] for v in gradini))
        for i in range(1, quanti + 1):
            celle, visto = [], False
            for v in gradini:
                n = v["sessioni"].get(i)
                if ha_misurato(n):
                    try:
                        celle.append(forma % prendi(n))
                        visto = True
                        continue
                    except Exception:
                        pass
                celle.append("    -")
            if visto:
                print("   s%-2d  %s" % (i, " ".join(celle)))

    griglia("FOTOGRAMMI/S — il sintomo", lambda n: n["fps"], "%6.2f")
    griglia("CHIAVI SU CENTO — ⭐ il MECCANISMO (§1.31): parte prima del calo",
            lambda n: 100.0 * n["chiavi"] / n["fotogrammi"], "%6.1f")
    griglia("RITARDO MEDIANO ms — cattura → consegnato sul filo",
            lambda n: n["ritardo"]["mediano_ms"], "%6.1f")
    griglia("BYTE PER FOTOGRAMMA — ⛔ quanta sollecitazione e' ARRIVATA (§1.30)",
            lambda n: n["byte_per_fotogramma"] / 1000.0, "%6.1f")
    _inf("⚠ «-» vuol dire «non c'era» oppure «non ho misurato»: NON zero")

    # ⭐ LA MACCHINA, gradino per gradino: e' qui che si legge QUALE RISORSA
    #    FINISCE PER PRIMA.
    print("\n   LA MACCHINA — e quale risorsa finisce per prima")
    print("        %-4s %6s %7s %7s %7s %9s %9s %9s %7s"
          % ("g", "CPU%", "GPUvid%", "GPUveh%", "GPUren%", "PSS MiB",
             "mio Mbit", "lo Mbit", "clienti"))
    for v in gradini:
        m = v["macchina"]
        gp = m.get("gpu_uso_pc") or {}
        print("        %-4d %6s %7s %7s %7s %9s %9s %9s %7s"
              % (v["gradino"], m.get("cpu_occupata_pc"), gp.get("video"),
                 gp.get("video-enhance"), gp.get("render"),
                 m.get("pss_totale_mib"), v.get("mio_filo_mbit_s"),
                 (m.get("filo") or {}).get("lo", {}).get("mbit_s"),
                 m.get("cpu_clienti_nuclei")))
    _inf("⛔ «lo Mbit» NON e' mio: ci passano anche i clienti degli altri "
         "agenti.  ⭐ «mio Mbit» viene dai contatori QUIC del server, sessione "
         "per sessione, ed e' l'unico numero attribuibile")
    _inf("⚠ le colonne GPU sono l'USO DELLA CAPACITA' (0..100 %), non i "
         "motori-equivalenti: il `video` di questa scheda ha DUE VDBOX")
    # ⭐ Il numero della fase.
    if 1 in prima_volta and gradini:
        ultimo = gradini[-1]
        n = ultimo["sessioni"].get(1)
        if ha_misurato(n):
            p = prima_volta[1]
            _ok("⭐ IL NUMERO DELLA FASE — s1 da sola: %.2f/s, %d B/fot, "
                "ritardo mediano %s ms · s1 con %d sessioni vive: %.2f/s, "
                "%d B/fot, ritardo mediano %s ms  (%+.1f %% di ritmo)"
                % (p["fps"], p["byte_per_fotogramma"],
                   p["ritardo"]["mediano_ms"], ultimo["gradino"], n["fps"],
                   n["byte_per_fotogramma"], n["ritardo"]["mediano_ms"],
                   100.0 * (n["fps"] - p["fps"]) / p["fps"]))
    ap = esiti.get("apertura_ms") or {}
    if ap:
        _inf("⭐ APERTURA della sessione ennesima (ms, tetto): %s"
             % " ".join("s%s:%s" % (k, v) for k, v in sorted(ap.items())))
    # ⭐ La risorsa che finisce per prima.
    ultimo = gradini[-1]["macchina"]
    _inf("A %d sessioni: CPU %s %% · GPU %s · PSS %s MiB · filo %s"
         % (gradini[-1]["gradino"], ultimo.get("cpu_occupata_pc"),
            json.dumps(ultimo.get("gpu_pc")), ultimo.get("pss_totale_mib"),
            json.dumps(ultimo.get("filo"))))
    # ⭐ Il budget di rete di §3.1-bis punto 2, CONTATO (non provato).
    mio = gradini[-1].get("mio_filo_mbit_s")
    n_sess = len([1 for x in gradini[-1]["sessioni"].values() if ha_misurato(x)])
    if mio and n_sess:
        _inf("⭐ IL BUDGET DI RETE (`DECISIONI.md` §3.1-bis punto 2, e "
             "`README.md`: 10 × 30 = 300 Mbit/s sul filo del server).")
        _inf("   `[M]` %d sessioni sature chiedono **%.1f Mbit/s** in tutto, "
             "cioe' **%.2f Mbit/s a testa** — dai contatori QUIC del server, "
             "non da `lo`." % (n_sess, mio, mio / n_sess))
        _inf("   ⇒ Dieci sessioni cosi' chiederebbero **%.0f Mbit/s**: il "
             "%.0f %% del budget dichiarato e il %.0f %% di un filo da 1 "
             "Gbit/s." % (10 * mio / n_sess, 100.0 * (10 * mio / n_sess) / 300.0,
                          100.0 * (10 * mio / n_sess) / 1000.0))
        _inf("   ⛔ E' un CONTO, non una prova: su `lo` non c'e' ne' il tetto "
             "del gigabit ne' una coda di router.  Chi vuole provarlo deve "
             "mettere dieci clienti su macchine diverse.")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ QUANTI NE STANNO, SU QUESTA SCENA — e se il numero e' confrontabile
    # ═══════════════════════════════════════════════════════════════════════
    numero, perche, dett = capienza(esiti)
    esiti["capienza"] = {"scena": SCENA, "numero": numero, "perche": perche,
                         "per_gradino": dett}
    _log("⭐⭐ QUANTI NE STANNO — scena «%s»" % SCENA)
    (_ok if numero else _dub)(perche)
    for g in sorted(dett):
        v = dett[g]
        _inf("   gradino %-2d  %d misurate · sotto il pavimento: %s · I1 rossi "
             "%d · non giudicate %s"
             % (g, v["viste"], ", ".join(v["sotto_pavimento"]) or "nessuna",
                v["rossi_I1"], v["non_giudicate"] or "nessuna"))
    passa, det = p_ancora_ritrova(numero)
    esiti["ancora_ritrova"] = {"passa": passa, "perche": det}
    (_ok if passa else (_dub if passa is None else _ko))("l'ANCORA: %s" % det)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ IL DIRUPO — e la domanda non e' «c'e'?», e' «a QUALE numero?»
    # ═══════════════════════════════════════════════════════════════════════
    _log("⭐ IL DIRUPO — dove il ritmo NON scende, precipita")
    _inf("`[M]` primo giro, scena satura: fra la sesta e l'ottava sessione si "
         "passa da 38 a 1,5 fot/s.  ⛔ Non e' un ginocchio, e' un precipizio, e "
         "un prodotto che ha un dirupo deve fermarsi PRIMA del dirupo")
    medie = []
    for v in gradini:
        vivi = [x["fps"] for x in v["sessioni"].values() if ha_misurato(x)]
        medie.append((v["gradino"],
                      round(statistics.mean(vivi), 2) if vivi else None))
    esiti["media_fps_per_gradino"] = medie
    _inf("media dei fotogrammi/s per gradino: %s"
         % "  ".join("g%d:%s" % (g, m) for g, m in medie))
    dirupo = None
    for k in range(1, len(medie)):
        a, b = medie[k - 1][1], medie[k][1]
        if a and b and b < 0.5 * a:
            dirupo = (medie[k][0], a, b)
            break
    esiti["dirupo"] = dirupo
    if dirupo:
        _ko("⛔ DIRUPO al gradino %d: da %.2f a %.2f fot/s di media, cioe' "
            "meno %.0f %% in UNA sessione" % (dirupo[0], dirupo[1], dirupo[2],
                                              100 * (1 - dirupo[2] / dirupo[1])))
    else:
        _ok("⭐ nessun dirupo (nessun gradino dimezza la media del precedente) "
            "fino al gradino %d" % (medie[-1][0] if medie else 0))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA LEGGE — il costo cresce con quanto il desktop cambia, e COME
    # ═══════════════════════════════════════════════════════════════════════
    _log("⭐⭐ IL COSTO CONTRO QUANTO IL DESKTOP CAMBIA")
    _inf("⛔ l'INGRESSO e' quanto la SCENA ha ridisegnato (dal suo blocco in "
         "/dev/shm), non quanto il prodotto ha consegnato: correlare l'uscita "
         "con l'uscita direbbe solo che il costo cresce col costo")
    righe = []
    print("\n        %-4s %10s %10s %10s %8s %8s"
          % ("g", "Mpx ridis", "Mpx cons", "GPUren%", "Mbit/s", "fot/s"))
    for v in gradini:
        chiede = cons = 0.0
        visto = False
        for n in v["sessioni"].values():
            if not ha_misurato(n):
                continue
            mp = (n.get("disegni") or {}).get("mpixel_ridisegnati_s")
            if mp is not None:
                chiede += mp
                visto = True
            l, a = (n.get("tela") or "1920x1080").split("x") \
                if isinstance(n.get("tela"), str) else ("1920", "1080")
            cons += int(l) * int(a) * n["fps"] / 1e6
        gp = (v["macchina"].get("gpu_uso_pc") or {}).get("render")
        vivi = [x["fps"] for x in v["sessioni"].values() if ha_misurato(x)]
        riga = {"gradino": v["gradino"],
                "mpixel_ridisegnati_s": round(chiede, 2) if visto else None,
                "mpixel_consegnati_s": round(cons, 2),
                "gpu_render_pc": gp, "mbit_s": v.get("mio_carico_mbit_s"),
                "fps_medio": round(statistics.mean(vivi), 2) if vivi else None}
        righe.append(riga)
        print("        %-4d %10s %10.1f %10s %8s %8s"
              % (v["gradino"], riga["mpixel_ridisegnati_s"], cons, gp,
                 riga["mbit_s"], riga["fps_medio"]))
    esiti["costo_contro_cambiamento"] = righe
    # ⛔ La legge si cerca SOLO sotto la capienza: sopra, il costo non cresce
    #    piu' con la domanda — e' la macchina che smette di consegnare, e una
    #    retta tirata attraverso il dirupo descriverebbe il dirupo, non la legge.
    tetto = numero or len(righe)
    dentro = [r for r in righe if r["gradino"] <= tetto]
    for nome, chiave in (("GPU render %", "gpu_render_pc"),
                         ("Mpixel consegnati/s", "mpixel_consegnati_s"),
                         ("Mbit/s di carico", "mbit_s")):
        L = legge_del_costo([(r["mpixel_ridisegnati_s"], r[chiave])
                             for r in dentro])
        if L is None:
            _dub("⚠ «%s»: meno di tre punti utili sotto la capienza — NON "
                 "tiro una retta attraverso due punti" % nome)
            continue
        esiti.setdefault("leggi", {})[chiave] = L
        _inf("⭐ %-22s = %.4g + %.4g × (Mpixel ridisegnati/s)   ·  R² %.4f  ·  "
             "errore max %.3g (%.1f %% della media)  ·  %d punti"
             % (nome, L["intercetta"], L["pendenza"], L["r2"] or 0,
                L["errore_massimo"], 100 * (L["errore_relativo_max"] or 0),
                L["punti"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LA LEGGE — UNA sessione, e quanto il desktop cambia si GIRA COME UNA
#       MANOPOLA.  ⛔ Serve a rispondere alla domanda che il budget aspetta.
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Perche' non basta la salita.  Nella salita cambiano DUE cose insieme — il
#    numero delle sessioni e il carico totale — e da due variabili che si
#    muovono insieme non si tira fuori una legge: si tira fuori una
#    correlazione.  ⇒ Qui **una sola** sessione, e si gira **una sola**
#    manopola: la frazione di tempo in cui la scena disegna.
#
# ⭐ E la manopola non e' quel che si CHIEDE: e' quel che si MISURA.  Il ciclo
#    `SIGSTOP`/`SIGCONT` chiede un ciclo di lavoro; quanto la scena abbia
#    davvero ridisegnato lo dice il suo contatore, e ⛔ e' quello a finire
#    sull'asse x — la differenza fra i due e' proprio quel che il compositore
#    decide di non fare.
LIVELLI = [
    ("ferma",     None, None),      # ⛔ nessuna scena: l'origine della retta
    ("strappi-1", 2.70, 0.30),      # ~10 % del tempo a disegnare
    ("strappi-2", 1.00, 0.30),      # ~23 % — ⭐ ed e' lo strappo del braccio «vero»
    ("strappi-3", 0.30, 0.30),      # ~50 %
    ("continua",  0.00, None),      # 100 %: la scena del braccio «satura»
]


def strappi_regola(i, quiete, accensione):
    """Accende (o spegne) il ciclo degli strappi su una scena gia' viva.

    ⛔ E prima di tutto il `SIGCONT`: se il ciclo precedente e' stato ucciso
       mentre la scena era congelata, la scena resterebbe ferma **per sempre** —
       e il livello dopo misurerebbe zero chiamandolo «continua»."""
    root("pkill -f '10-b92-scene[.]py strappi .* %d$'; true" % uid(i))
    time.sleep(0.5)
    root("pkill -CONT -u %d -f '04-b30-scen[a]'; true" % uid(i))
    if not quiete:
        return True, "movimento continuo (nessuno strappo)"
    rc, out, _ = root("pgrep -u %d -f '04-b30-scen[a] --' | head -1" % uid(i))
    pid = out.strip()
    if not pid.isdigit():
        return False, "⛔ non trovo il pid della scena: non innesto lo strappo"
    root("setsid nohup python3 %s/10-b92-scene.py strappi %s %.3f %.3f %d "
         ">> %s/scena-%d.log 2>&1 & echo acceso"
         % (LAV, pid, quiete, accensione, uid(i), LAV, i))
    time.sleep(1.0)
    rc, out, _ = root("pgrep -c -f '10-b92-scene[.]py strappi .* %d$' || true"
                      % uid(i))
    if out.strip() == "0" or not out.strip().isdigit():
        return False, "⛔ il ciclo degli strappi non e' partito"
    return True, ("strappi %.2f s fermo / %.2f s acceso ⇒ ciclo di lavoro "
                  "chiesto %.0f %%" % (quiete, accensione,
                                       100 * accensione / (quiete + accensione)))


def giro_legge(durata, resta):
    """UNA sessione, cinque livelli di cambiamento, e la retta con l'errore."""
    esiti = {"scena": "manopola", "durata_s": durata, "livelli": []}
    _log("⭐⭐ LA LEGGE — una sessione sola, e la manopola e' QUANTO CAMBIA")
    aperta, detto = apri_sessione(1, resta)
    if not aperta:
        _ko(detto)
        return esiti, ["la sessione non si apre"], []
    _ok("s1 aperta — %s" % detto)
    rossi, muti = [], []
    # ⭐ La scena si accende UNA VOLTA e resta la stessa per tutti i livelli:
    #   cosi' fra un livello e l'altro cambia SOLO il ciclo di lavoro.  ⛔ Una
    #   scena rinata a ogni livello porterebbe con se' un'apertura, una prima
    #   chiave e una tela nuova, cioe' tre cose insieme alla manopola.
    vecchia, globals()["SCENA"] = SCENA, "satura"
    usc = accendi_scena(1)
    globals()["SCENA"] = vecchia
    if not usc:
        _ko("⛔ la scena non parte: non misuro")
        return esiti, ["la scena non parte"], []
    for nome, quiete, accensione in LIVELLI:
        _log("LIVELLO «%s»" % nome)
        if nome == "ferma":
            root("pkill -f '10-b92-scene[.]py strappi .* %d$'; true" % uid(1))
            root("pkill -u %d -f '04-b30-scen[a]'; true" % uid(1))
            time.sleep(2.0)
            _inf("nessuna scena: e' l'origine della retta")
        else:
            if nome == "strappi-1":
                # la scena era stata spenta dal livello «ferma»: si riaccende
                vecchia, globals()["SCENA"] = SCENA, "satura"
                usc = accendi_scena(1)
                globals()["SCENA"] = vecchia
                if not usc:
                    _ko("⛔ la scena non riparte: salto i livelli che restano")
                    muti.append("la scena non riparte dopo «ferma»")
                    break
            ok, det = strappi_regola(1, quiete, accensione)
            (_ok if ok else _ko)(det)
            if not ok:
                muti.append("livello %s: %s" % (nome, det))
                continue
        _inf("assestamento %.0f s" % ASSESTAMENTO_S)
        time.sleep(ASSESTAMENTO_S)
        f0, d0 = sonda(1), disegni_tutte(1)
        if f0 is None or f0.get("t_ms") is None:
            _ko("⛔ niente ancora: non misuro il livello «%s»" % nome)
            muti.append("livello %s: niente ancora" % nome)
            continue
        time.sleep(durata)
        d1, f1 = disegni_tutte(1), sonda(1)
        if f1 is None or f1.get("t_ms") is None:
            _ko("⛔ niente ancora finale sul livello «%s»" % nome)
            muti.append("livello %s: niente ancora finale" % nome)
            continue
        d = fra(f0, f1, 1)
        n = fetta(1, f0["t_ms"], f1["t_ms"], durata)
        dis = ({"disegni_s": 0.0, "esito": "nessuna scena, per costruzione"}
               if nome == "ferma" else fra_disegni(d0, d1, 1, durata))
        gp = (d.get("gpu_uso_pc") or {}).get("render")
        mp = None
        if ha_misurato(n):
            l, h = (n.get("tela") or TELA).split("x")
            mp = round(int(l) * int(h) * n["fps"] / 1e6, 2)
        voce = {"livello": nome, "quiete_s": quiete, "accensione_s": accensione,
                "disegni_s": dis.get("disegni_s"),
                "mpixel_ridisegnati_s": dis.get("mpixel_ridisegnati_s"),
                "disegni_esito": dis.get("esito"),
                "fps": n.get("fps"), "byte_per_fotogramma": n.get("byte_per_fotogramma"),
                "mbit_s_carico": n.get("mbit_s_carico"),
                "mpixel_consegnati_s": mp,
                "gpu_render_pc": gp,
                "gpu_video_pc": (d.get("gpu_uso_pc") or {}).get("video"),
                "gpu_vebox_pc": (d.get("gpu_uso_pc") or {}).get("video-enhance"),
                "gt_mhz": (d.get("gt") or {}).get("act_mhz"),
                "rc6_pc": (d.get("gt") or {}).get("rc6_pc"),
                "cpu_pc": d.get("cpu_occupata_pc"),
                "esito_fetta": n.get("esito")}
        esiti["livelli"].append(voce)
        _inf("%-10s  disegni %8s/s (%s Mpx ridis/s)  ⇒  %6s fot/s · %6s Mpx "
             "cons/s · GPUren %5s %% · GPUvid %5s %% · VEBOX %5s %% · GT %s MHz "
             "· %s Mbit/s"
             % (nome, voce["disegni_s"], voce["mpixel_ridisegnati_s"],
                voce["fps"], mp, gp, voce["gpu_video_pc"], voce["gpu_vebox_pc"],
                voce["gt_mhz"], voce["mbit_s_carico"]))
    # ── LA RETTA ─────────────────────────────────────────────────────────
    _log("⭐⭐ LA LEGGE — e l'errore dice se il budget si puo' calcolare")
    for nome, chiave in (("GPU render %", "gpu_render_pc"),
                         ("GPU video %", "gpu_video_pc"),
                         ("Mpixel consegnati/s", "mpixel_consegnati_s"),
                         ("Mbit/s di carico", "mbit_s_carico")):
        L = legge_del_costo([(v["mpixel_ridisegnati_s"], v[chiave])
                             for v in esiti["livelli"]])
        if L is None:
            _dub("⚠ «%s»: meno di tre punti utili — NON tiro una retta" % nome)
            continue
        esiti.setdefault("leggi", {})[chiave] = L
        _inf("⭐ %-22s = %.4g + %.4g × (Mpixel ridisegnati/s)  ·  R² %.4f  ·  "
             "errore max %.3g (%.1f %% della media)  ·  %d punti"
             % (nome, L["intercetta"], L["pendenza"], L["r2"] or 0,
                L["errore_massimo"], 100 * (L["errore_relativo_max"] or 0),
                L["punti"]))
    _inf("⛔ E il ferro accanto al numero, sempre: Intel UHD 730 INTEGRATA "
         "(`renderD128`), i5-13500T.  ⚠ E la GT non e' bloccata: "
         "`drm-engine-*` misura TEMPO OCCUPATO, e il tempo dipende dalla "
         "frequenza (10-b87 §CLOCK, fattore 3,8)")
    return esiti, rossi, muti


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — ⛔ e ogni caso e' stato FATTO GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def _fab(quanti, fps=30.0, byte=25000, chiave_ogni=30, primo_numero=1000,
         ritardo_ms=40.0, t0=1000.0):
    """Un giornale finto, a valori scelti."""
    g, passo = [], 1000.0 / fps
    for k in range(quanti):
        arrivo = t0 + k * passo
        g.append({"numero": primo_numero + k,
                  "chiave": (chiave_ogni > 0 and k % chiave_ogni == 0),
                  "tipo": 0x0301, "codec": 3, "l": 1920, "a": 1080,
                  "byte": byte, "istante_us": int((arrivo - ritardo_ms) * 1000),
                  "arrivo_ms": arrivo})
    return g


def certifica():
    print("== ⭐ `10-b92-dieci.py --certifica` — i guasti si INNESTANO e si "
          "FANNO GIRARE\n")
    global B70
    B70 = _importa_b70()
    esiti, rossi = [], []

    def caso(nome, atteso, visto, ok):
        esiti.append({"caso": nome, "atteso": atteso, "visto": visto, "ok": ok})
        print("  %s %s" % ("⭐" if ok else "⛔", nome))
        print("      atteso: %s" % (atteso,))
        print("      visto:  %s" % (visto,))
        if not ok:
            rossi.append(nome)

    # ── 0 · IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33) ───────────────────
    print("  ── 0 · il metro si tara PRIMA: giornale a valore NOTO ──")
    sano, guai = tara_riduzione(B70, dillo=True)
    caso("0 · la riduzione importata ritrova i valori iniettati",
         "200/7,960 = 25,13/s · quota delta 0,90 · 10 000 B/fot · "
         "ritardo mediano 37,5 ms  (⭐ e il 25,00 che avevo scritto era MIO: "
         "vedi il riquadro di `tara_riduzione`)",
         "tutto ritrovato" if sano else guai, sano)

    # ── 1 · una sessione che non si apre ⇒ la salita si FERMA ─────────────
    print("\n  ── 1 · una sessione che non si apre ⇒ ROSSO, e non si continua ──")
    # ⛔ Il guasto si innesta sostituendo `apri_sessione`, e la salita gira per
    #    davvero contro un finto server: e' l'unico modo di provare che il
    #    `break` c'e'.  ⚠ Provarlo leggendo il codice sarebbe immaginarlo.
    globals()["_finta_salita_fallisce_al"] = 3
    fatti = giro_finto(quanti=5, fallisce_al=3)
    ok = (fatti["fermata_al_gradino"] == 3 and
          len(fatti["gradini"]) == 3 and
          any("non si apre" in x for x in fatti["rossi"]))
    caso("1 · la salita si ferma al gradino che non si apre",
         "fermata_al_gradino = 3, tre gradini in tutto, un rosso «non si apre»",
         "fermata a %s, %d gradini, rossi %s"
         % (fatti.get("fermata_al_gradino"), len(fatti["gradini"]),
            fatti["rossi"][:2]), ok)

    # ── 1d · l'ANCORA CHE NON AVANZA ⇒ la salita si ferma ────────────────
    print("\n  ── 1d · ⛔ l'ancora che non avanza (l'orologio non si legge) ──")
    fatti = giro_finto(quanti=4, ancora_ferma=True)
    ok = any("l'ancora non avanza" in x for x in fatti["rossi"])
    caso("1d · ⛔ GUASTO: il confine del gradino non avanza → ROSSO e stop",
         "un rosso «l'ancora non avanza», e la salita si ferma",
         "%d gradini · rossi %s" % (len(fatti["gradini"]), fatti["rossi"][:2]),
         ok)

    # ── 2 · un cliente che muore a meta' ⇒ None, non zero ─────────────────
    print("\n  ── 2 · un cliente che muore a meta' ⇒ `None`, non zero ──")
    fatti = giro_finto(quanti=4, muore_al=(3, 2))   # s2 muore al gradino 3
    n = fatti["gradini"][2]["sessioni"][2]
    ok = (not ha_misurato(n) and "MORTO" in n.get("esito", "")
          and "None" in n.get("esito", ""))
    caso("2 · il cliente morto da' `None`, e lo dice",
         "esito che nomina «MORTO» e «None», e NON un fps a zero",
         n.get("esito", "?")[:110], ok)
    # ⛔ E il controllo negativo: se tornasse zero, la media mentirebbe.
    vivi = [x for x in fatti["gradini"][2]["sessioni"].values() if ha_misurato(x)]
    media = statistics.mean(x["fps"] for x in vivi) if vivi else None
    ok2 = media is not None and media > 29.0
    caso("2b · la media dei vivi non e' abbassata dal morto",
         "media > 29/s (i vivi vanno a 30/s); con uno zero farebbe ~22,5",
         media, ok2)

    # ── 3 · il palco orfano, smascherato PRIMA di misurare ────────────────
    print("\n  ── 3 · un palco orfano del giro precedente ──")
    # ⛔ Qui si prova la LOGICA del riconoscimento contro l'uscita di `pgrep`,
    #    che e' l'unica cosa che si puo' provare senza la macchina.
    def finto_pgrep(uscite):
        def r(comando, tetto=120):
            for chiave, risposta in uscite:
                if chiave in comando:
                    return (0, risposta, "")
            return (0, "", "")
        return r
    vecchio = globals()["root"]
    try:
        globals()["root"] = finto_pgrep([
            ("ss -uln | grep -c ':%d " % PORTA, "1"),
            ("ss -uln | grep -c ", "0"),
            ("test -s %s/parola" % LAV, "si"),
            ("test -s %s/banchi" % ALB, "si"),
            ("test -x", "si"),
            ("wc -c <", "9999"),
            ("mkdir -p", ""),
            ("pgrep -u %d -a" % uid(4), "9911 gnome-shell --wayland"),
            ("pgrep -u %d -c" % uid(4), "12"),
            ("pgrep -u", "7"),
        ])
        sano = terreno(5)
    finally:
        globals()["root"] = vecchio
    caso("3 · il terreno si RIFIUTA se un uid mio ha ancora processi",
         "terreno() torna False e nomina il palco orfano", sano, sano is False)

    # ── 4 · il conto letto dal gradino precedente ─────────────────────────
    print("\n  ── 4 · il conto di un gradino letto dal gradino PRECEDENTE ──")
    sane = {(1, 1): {"numeri": [1000, 1300]}, (2, 1): {"numeri": [1301, 1600]}}
    guaste = {(1, 1): {"numeri": [1000, 1300]}, (2, 1): {"numeri": [1000, 1300]}}
    p_sano = p_ancora(sane, 1, 2)
    p_gua = p_ancora(guaste, 1, 2)
    caso("4 · sano → verde", "passa = True", p_sano, p_sano[0] is True)
    caso("4b · ⛔ GUASTO: stessi `numero` in due gradini → ROSSO",
         "passa = False, e il perche' nomina «LO STESSO CONTO DUE VOLTE»",
         p_gua, p_gua[0] is False and "DUE VOLTE" in p_gua[1])
    # ⛔ E il risanato: il guasto tolto, torna verde.
    risanato = p_ancora(sane, 1, 2)
    caso("4c · risanato → verde", "passa = True", risanato, risanato[0] is True)

    # ── 5 · dieci desktop FERMI dichiarati come dieci al lavoro ───────────
    print("\n  ── 5 · dieci desktop FERMI, e i fotogrammi/s sono ottimi ──")
    fermo = B70.misura(_fab(1800, fps=60.0, byte=270, chiave_ogni=0), 30.0,
                       scaldata_s=0.0)
    fermo["ritardo"] = ritardi(_fab(1800, fps=60.0, byte=270))
    p_r = p_ritmo(fermo)
    p_s = p_scena_viva(fermo)
    caso("5 · ⛔ IL RITMO DA' VERDE su uno schermo quasi fermo",
         "p_ritmo passa (60/s), e da solo assolverebbe", p_r, p_r[0] is True)
    caso("5b · ⭐ e i BYTE lo smascherano",
         "p_scena_viva = False, e nomina «schermo quasi fermo»",
         p_s, p_s[0] is False and "fermo" in p_s[1])
    vivo = B70.misura(_fab(900, fps=30.0, byte=25000, chiave_ogni=0), 30.0,
                      scaldata_s=0.0)
    caso("5c · risanato: la stessa funzione su una scena che morde",
         "p_scena_viva = True", p_scena_viva(vivo), p_scena_viva(vivo)[0] is True)

    # ── 6 · la spirale di chiavi, che il ritmo NON vede ───────────────────
    print("\n  ── 6 · ⭐ il MECCANISMO accanto al SINTOMO (§1.31) ──")
    spirale = B70.misura(_fab(900, fps=30.0, byte=25000, chiave_ogni=3), 30.0,
                         scaldata_s=0.0)
    p_r = p_ritmo(spirale)
    p_q = p_quota_chiavi(spirale)
    caso("6 · ⛔ 30/s pieni, e un fotogramma su tre e' una CHIAVE",
         "p_ritmo passa (il sintomo tace)", p_r, p_r[0] is True)
    caso("6b · ⭐ e p_quota_chiavi da' ROSSO",
         "passa = False, e nomina «SPIRALE DI CHIAVI»",
         p_q, p_q[0] is False and "SPIRALE" in p_q[1])
    p_q2 = p_quota_chiavi(B70.misura(_fab(900, chiave_ogni=60), 30.0,
                                     scaldata_s=0.0))
    caso("6c · risanato: una chiave ogni 60 → verde", "passa = True",
         p_q2, p_q2[0] is True)

    # ── 7 · I1, e i tre esiti ─────────────────────────────────────────────
    print("\n  ── 7 · ⛔ I1 — chi era gia' dentro non peggiora (§4.6-bis) ──")
    p1 = B70.misura(_fab(900, fps=30.0), 30.0, scaldata_s=0.0); p1["gradino"] = 1
    uguale = B70.misura(_fab(900, fps=29.5, primo_numero=9000), 30.0, scaldata_s=0.0)
    caduto = B70.misura(_fab(600, fps=20.0, primo_numero=9000), 30.0, scaldata_s=0.0)
    mezzo = B70.misura(_fab(800, fps=26.5, primo_numero=9000), 30.0, scaldata_s=0.0)
    a = p_I1(p1, uguale, 1, 10, False)
    b = p_I1(p1, caduto, 1, 10, False)
    c = p_I1(p1, mezzo, 1, 10, False)
    d = p_I1(p1, caduto, 1, 10, True)
    caso("7 · sano: 30 → 29,5/s", "passa = True", a, a[0] is True)
    caso("7b · ⛔ GUASTO: 30 → 20/s", "passa = False, «I1 VIOLATO»",
         b, b[0] is False and "I1 VIOLATO" in b[1])
    caso("7c · ⚠ 30 → 26,5/s: fra la tolleranza e il sicuro",
         "passa = None (non lo distinguo dal rumore)", c, c[0] is None)
    caso("7d · ⚠ lo stesso crollo, ma a CPU SATURA",
         "passa = None: NON attribuisco quel che puo' essere della scena",
         d, d[0] is None and "NON ATTRIBUISCO" in d[1])

    # ── 8 · il metro della GPU che conta due volte ────────────────────────
    print("\n  ── 8 · il metro della GPU: la deduplicazione per `drm-client-id` ──")
    sano_g = {"gpu_pc": {"video": 61.0, "render": 44.0},
              "gpu_uso_pc": {"video": 30.5, "render": 44.0},
              "gpu_capacita": {"video": 2}, "gt": {"act_mhz": 900},
              "gpu_metro_sano": True, "gpu_negativi": {},
              "gpu_clienti": 12, "gpu_estranei": 0, "gpu_altri_pdev": {}}
    gua_g = {"gpu_pc": {"video": 244.0}, "gpu_capacita": {"video": 2},
             "gpu_metro_sano": False, "gpu_negativi": {},
             "gt": {"act_mhz": 900}, "gpu_clienti": 48, "gpu_estranei": 0, "gpu_altri_pdev": {}}
    disc = {"gpu_pc": {"video": 30.0}, "gpu_capacita": {"video": 2},
            "gpu_metro_sano": True, "gpu_negativi": {},
            "gt": {"act_mhz": 900}, "gpu_clienti": 3, "gpu_estranei": 0,
            "gpu_altri_pdev": {"0000:03:00.0": 4}}
    caso("8 · sano → verde", "passa = True", p_metro_gpu(sano_g),
         p_metro_gpu(sano_g)[0] is True)
    caso("8b · ⛔ GUASTO: 244 % sul video con capacita' 2 (tetto 205) → ROSSO",
         "passa = False, «IL METRO DELLA GPU NON E' SANO»",
         p_metro_gpu(gua_g), p_metro_gpu(gua_g)[0] is False)
    caso("8c · ⛔ GUASTO: descrittori sulla scheda DISCRETA → ROSSO",
         "passa = False, e nomina §4.6-quinquies", p_metro_gpu(disc),
         p_metro_gpu(disc)[0] is False and "quinquies" in p_metro_gpu(disc)[1])

    # ── 8g · i DUE VDBOX: il tetto e' 200 %, non 100 % ────────────────────
    print("\n  ── 8g · `drm-engine-capacity-video: 2` — i VDBOX sono DUE ──")

    def _foto(t_ms, video_ns, cap):
        return {"t_ms": t_ms, "cpu": {"totale": 0, "inattivo": 0, "nuclei": 20},
                "rete": {}, "gt": {"act_mhz": 900, "min_mhz": 300,
                                   "max_mhz": 1550, "rc6_ms": 0},
                "processi": {"per_uid": {}, "negati": 0,
                             "server": {"pss_kib": 0, "rss_kib": 0,
                                        "cpu_jiffies": 0, "quanti": 0},
                             "clienti": {"pss_kib": 0, "rss_kib": 0,
                                         "cpu_jiffies": 0, "quanti": 0}},
                # ⛔ `per_contesto` DEVE esserci: dal 24 agosto il delta si fa
                #    per contesto, e una fotografia senza quel campo darebbe
                #    zero — cioe' un metro che tace invece di misurare.
                "gpu": {"motori": {"video": video_ns},
                        "per_contesto": {"c1": {"video": video_ns}},
                        "contesti_miei": {"c1": True},
                        "capacita": {"video": cap},
                        "clienti": 4, "per_uid": {}, "altri_pdev": {},
                        "estranei": 0, "estranei_pid": []},
                "costo_ms": 1.0}

    # 18 s di motore in 10 s di parete = 180 %.  Con DUE VDBOX e' il 90 % della
    # capacita', ed e' sano.  Con UNO solo sarebbe impossibile.
    due = fra(_foto(0, 0, 2), _foto(10000, 18 * 10 ** 9, 2), 10)
    uno = fra(_foto(0, 0, 1), _foto(10000, 18 * 10 ** 9, 1), 10)
    caso("8g · 180 % sul video con capacita' 2 → SANO (e' il 90 % della "
         "capacita')",
         "gpu_metro_sano = True, gpu_uso_pc video = 90,0",
         (due["gpu_metro_sano"], due["gpu_uso_pc"]),
         due["gpu_metro_sano"] is True and due["gpu_uso_pc"]["video"] == 90.0)
    caso("8h · ⛔ GUASTO: 180 % sul video con capacita' 1 → NON SANO",
         "gpu_metro_sano = False", uno["gpu_metro_sano"],
         uno["gpu_metro_sano"] is False)
    # ⛔ E il fantasma: «capacity-video» non deve comparire fra i motori.
    caso("8i · ⭐ «capacity-video» NON e' un motore",
         "fra i motori ci sta solo «video»", sorted(due["gpu_pc"]),
         sorted(due["gpu_pc"]) == ["video"])
    caso("8j · ⭐ e il contesto della GT arriva fino al giudizio",
         "act_mhz 900, min 300, max 1550, non bloccata",
         due["gt"], due["gt"]["act_mhz"] == 900
         and due["gt"]["bloccata"] is False)

    # ── 8k · ⛔⛔ IL DELTA SU UNA PLATEA CHE CAMBIA ────────────────────────
    print("\n  ── 8k · ⛔ un contesto che MUORE fra le due fotografie ──")

    def _foto2(t_ms, per_contesto):
        f = _foto(t_ms, 0, 2)
        f["gpu"]["per_contesto"] = per_contesto
        f["gpu"]["motori"] = {}
        for v in per_contesto.values():
            for k, ns in v.items():
                f["gpu"]["motori"][k] = f["gpu"]["motori"].get(k, 0) + ns
        f["gpu"]["contesti_miei"] = dict((c, True) for c in per_contesto)
        return f

    # Il contesto «7» porta 30 s di cumulativo e MUORE; il «1» lavora 2 s.
    prima = {"1": {"render": 0}, "7": {"render": 30 * 10 ** 9}}
    dopo = {"1": {"render": 2 * 10 ** 9}}
    vecchio_modo = fra(_foto2(0, prima), _foto2(10000, dopo), 1)
    caso("8k · ⭐ il contesto morto NON entra nel delta",
         "render = 20,0 % (i 2 s del contesto vivo su 10 s), e NON un numero "
         "negativo",
         vecchio_modo["gpu_pc"], vecchio_modo["gpu_pc"].get("render") == 20.0)
    caso("8l · ⭐ e la platea si DICHIARA",
         "1 contesto comune, 0 nati, 1 morto", vecchio_modo["gpu_contesti"],
         vecchio_modo["gpu_contesti"] == {"comuni": 1, "nati": 0, "morti": 1})
    # ⛔ E il guasto vero: un delta negativo, che col vecchio modo compariva.
    #    Si fabbrica a mano per far girare il ramo che lo rifiuta.
    negativo = dict(vecchio_modo)
    negativo["gpu_negativi"] = {"render": -76.4}
    negativo["gpu_metro_sano"] = False
    p = p_metro_gpu(negativo)
    caso("8m · ⛔ GUASTO: occupazione NEGATIVA → NON GIUDICO (non un rosso sul "
         "prodotto)",
         "passa = None, e nomina «una somma su una platea che cambia non e' un "
         "delta»", p,
         p[0] is None and "platea che cambia" in p[1])

    # ── 8d · il metro della GPU CIECO, o il codificatore ripiegato in CPU ──
    print("\n  ── 8d · zero sul motore video MENTRE passano i fotogrammi ──")
    lavora = {"gpu_pc": {"video": 58.0}, "gpu_metro_sano": True, "gpu_negativi": {},
              "gpu_clienti": 12, "gpu_estranei": 0, "gpu_altri_pdev": {},
              "cpu_server_nuclei": 4.2}
    cieco = {"gpu_pc": {"video": 0.0, "render": 12.0}, "gpu_metro_sano": True,
             "gpu_clienti": 12, "gpu_estranei": 0, "gpu_altri_pdev": {},
             "cpu_server_nuclei": 14.9}
    caso("8d · sano: motore video al 58 % con 9 000 fotogrammi → verde",
         "passa = True", p_gpu_vede_la_codifica(lavora, 9000),
         p_gpu_vede_la_codifica(lavora, 9000)[0] is True)
    caso("8e · ⛔ GUASTO: 0,0 % sul video con 9 000 fotogrammi → NON GIUDICO",
         "passa = None, e nomina tutt'e due le cause (metro cieco / ripiego "
         "in CPU, E2)", p_gpu_vede_la_codifica(cieco, 9000),
         p_gpu_vede_la_codifica(cieco, 9000)[0] is None
         and "E2" in p_gpu_vede_la_codifica(cieco, 9000)[1])
    caso("8f · zero fotogrammi e zero GPU → non c'e' niente da vedere",
         "passa = None, e NON accusa nessuno",
         p_gpu_vede_la_codifica(cieco, 0),
         p_gpu_vede_la_codifica(cieco, 0)[0] is None)

    # ── 9 · i dieci clienti che diventano loro il collo ───────────────────
    print("\n  ── 9 · ⛔ i clienti come collo di bottiglia (l'incarico lo chiede) ──")
    ok_c = {"cpu_clienti_quota": 0.11, "cpu_clienti_nuclei": 2.2,
            "cpu_server_nuclei": 5.1, "cpu_nuclei": 20}
    ko_c = {"cpu_clienti_quota": 0.62, "cpu_clienti_nuclei": 12.4,
            "cpu_server_nuclei": 5.1, "cpu_nuclei": 20}
    no_c = {"cpu_clienti_quota": None}
    caso("9 · sano → verde", "passa = True", p_clienti_non_sono_il_collo(ok_c),
         p_clienti_non_sono_il_collo(ok_c)[0] is True)
    caso("9b · ⛔ GUASTO: i clienti prendono il 62 % → ROSSO",
         "passa = False, «NESSUN numero di questo gradino e' attribuibile»",
         p_clienti_non_sono_il_collo(ko_c),
         p_clienti_non_sono_il_collo(ko_c)[0] is False)
    caso("9c · ⚠ la CPU non si e' letta → `None`, non verde",
         "passa = None", p_clienti_non_sono_il_collo(no_c),
         p_clienti_non_sono_il_collo(no_c)[0] is None)

    # ── 10 · il metro del RITARDO, e la premessa che lo regge ─────────────
    print("\n  ── 10 · il metro del ritardo: iniezione di un valore NOTO ──")
    for noto in (5.0, 40.0, 137.0):
        r = ritardi(_fab(300, ritardo_ms=noto))
        ok = r["mediano_ms"] is not None and abs(r["mediano_ms"] - noto) <= 0.6
        caso("10 · %g ms iniettati → %s ms ritrovati" % (noto, r["mediano_ms"]),
             "mediana = %g ms ±0,6" % noto, r["mediano_ms"], ok)
    # ⛔ E il guasto: orologi che non sono lo stesso ⇒ `None`, non zero.
    storto = _fab(300, ritardo_ms=-250.0)
    r = ritardi(storto)
    caso("10b · ⛔ GUASTO: orologi non confrontabili (ritardo negativo)",
         "mediano_ms = None, e il perche' nomina CLOCK_MONOTONIC",
         r["esito"][:100],
         r["mediano_ms"] is None and "CLOCK_MONOTONIC" in r["esito"])

    # ── 11 · «non ho letto» non e' «zero» ─────────────────────────────────
    print("\n  ── 11 · «non ho letto» non e' «zero» (`CODER.md` §3.10) ──")
    v = conti_server(None, 900, {})
    caso("11 · registro non letto → il conto si RIFIUTA",
         "esito che nomina «NON HO LETTO», e nessun numero",
         v.get("esito"), "NON HO LETTO" in v.get("esito", ""))
    v2 = fra(None, {"t_ms": 1}, 10)
    caso("11b · una fotografia mancante → i delta si RIFIUTANO",
         "esito «NON HO NIENTE DA GIUDICARE»", v2.get("esito"),
         "NON HO NIENTE" in v2.get("esito", ""))
    v3 = fra({"t_ms": 2000}, {"t_ms": 1000}, 10)
    caso("11c · due fotografie fuori ordine → si RIFIUTANO",
         "esito «NON GIUDICO»", v3.get("esito"),
         "NON GIUDICO" in v3.get("esito", ""))

    # ── 12 · ⛔⛔ LA SCENA «DESKTOP VERO» CHE NON SI MUOVE ─────────────────
    print("\n  ── 12 · ⛔ «desktop vero» che NON si muove ⇒ non «costa poco» ──")

    def _con_disegni(g, durata, ds, tela="1280x720"):
        n = B70.misura(g, durata, scaldata_s=0.0)
        n["ritardo"] = ritardi(g)
        l, a = tela.split("x")
        n["disegni"] = ({"disegni_s": ds, "tela_scena": tela,
                         "mpixel_ridisegnati_s": round(ds * int(l) * int(a) / 1e6, 2)}
                        if ds is not None
                        else {"disegni_s": None, "esito": "non letto"})
        return n

    vecchia_scena = SCENA
    try:
        globals()["SCENA"] = "vero"
        # ⭐ I DUE ESTREMI SONO QUELLI MISURATI, non inventati: `10-b89`, 24 ago
        #   — scena `pieno` SANA **1 789** byte/fotogramma, la stessa scena
        #   **CONGELATA** 1 368.
        sana = _con_disegni(_fab(700, fps=18.0, byte=1789, chiave_ogni=0),
                            40.0, 13.8)
        congelata = _con_disegni(_fab(40, fps=1.0, byte=1368, chiave_ogni=0),
                                 40.0, 0.0)
        p = p_scena_morde(sana)
        caso("12 · sano: 13,8 disegni/s, 18 fot/s, 1 789 B/fot → verde",
             "passa = True", p, p[0] is True)
        p = p_scena_morde(congelata)
        caso("12b · ⛔ GUASTO: la scena e' CONGELATA (0 disegni/s) → ROSSO",
             "passa = False, e la ragione nomina i DISEGNI, non i byte",
             p, p[0] is False and "NON SI MUOVE" in p[1])
        # ⛔⛔ E LA PROVA CHE L'ORDINE DELLE COLONNE CONTA — `REVIEWER.md` E15.
        #     Coi soli byte, la scena congelata avrebbe preso VERDE: 1 368 sta
        #     sopra il pavimento di 600, come i 1 789 della sana.
        soli_byte = (congelata["byte_per_fotogramma"] >= BYTE_VERO_VIVI)
        caso("12b-bis · ⭐⭐ E I SOLI BYTE NON L'AVREBBERO VISTA (E15)",
             "1 368 byte/fotogramma della scena CONGELATA stanno SOPRA il "
             "pavimento di %d ⇒ un predicato sui soli byte avrebbe dato VERDE"
             % BYTE_VERO_VIVI,
             "byte congelata %d ≥ %d: %s"
             % (congelata["byte_per_fotogramma"], BYTE_VERO_VIVI, soli_byte),
             soli_byte is True)
        # e il terzo modo di sbagliare: la scena disegna ma non arriva niente
        muta = _con_disegni(_fab(60, fps=1.5, byte=5000, chiave_ogni=0), 40.0, 14.0)
        p = p_scena_morde(muta)
        caso("12c · ⛔ GUASTO: la scena disegna (14/s) e al cliente arrivano "
             "1,5 fot/s → ROSSO",
             "passa = False, e nomina «gli strappi non stanno arrivando»",
             p, p[0] is False and "strappi" in p[1])
        # ⛔ e «non ho letto i disegni» non e' «non ha disegnato»
        cieco = _con_disegni(_fab(700, fps=18.0, byte=1789, chiave_ogni=0),
                             40.0, None)
        p = p_scena_morde(cieco)
        caso("12d · ⚠ i disegni non si leggono → NON GIUDICO (non un rosso)",
             "passa = None", p, p[0] is None)
        p = p_scena_morde(sana)
        caso("12e · risanato: la scena torna a muoversi → verde",
             "passa = True", p, p[0] is True)

        # ── 12f · ⛔⛔ IL PAVIMENTO ASSOLUTO SUL BRACCIO «VERO» ────────────
        #    `[M]` 24 agosto 2026, 22:28: il primo gradino del braccio «vero»
        #    ha preso ROSSO con **una sola sessione** e la GPU al 2,2 %, perche'
        #    consegnava 10,61 fot/s contro un pavimento di 25.  ⚠ Il rosso non
        #    era del prodotto: la scena a strappi ne CHIEDEVA 14,62.
        p = p_ritmo(sana)
        caso("12f · ⭐ un desktop a STRAPPI che consegna quel che disegna → "
             "VERDE, e il pavimento assoluto dei 25/s non c'entra",
             "passa = True, e la ragione parla di RESA, non di pavimento",
             p, p[0] is True and "resa" in p[1])
        magro = _con_disegni(_fab(120, fps=3.0, byte=5000, chiave_ogni=0),
                             40.0, 14.0)
        p = p_ritmo(magro)
        caso("12g · ⛔ GUASTO: la scena chiede 14 disegni/s e ne arrivano 3 "
             "(resa 21 %) → ROSSO",
             "passa = False, e nomina la resa", p,
             p[0] is False and "ridisegnato" in p[1])
        p = p_ritmo(cieco)
        caso("12h · ⚠ senza i disegni non so che cosa il desktop CHIEDESSE "
             "→ NON GIUDICO", "passa = None", p, p[0] is None)

        # ── 13 · la scena «ferma» CHE SI MUOVE ────────────────────────────
        print("\n  ── 13 · ⛔ «ferma» che si MUOVE (salvaschermo, orologio) ──")
        globals()["SCENA"] = "ferma"
        g_ferma = _fab(2, fps=0.05, byte=266, chiave_ogni=1)
        ferma_n = conto_scarno(g_ferma, 40.0, {"esito": "sotto il minimo"})
        ferma_n["ritardo"] = ritardi(g_ferma)
        ferma_n["disegni"] = {"disegni_s": 0.0, "esito": "nessuna scena"}
        p = p_scena_morde(ferma_n)
        caso("13 · sano: 2 fotogrammi in 40 s → verde", "passa = True",
             p, p[0] is True)
        g_mossa = _fab(1000, fps=25.0, byte=4000, chiave_ogni=0)
        mossa = B70.misura(g_mossa, 40.0, scaldata_s=0.0)
        mossa["ritardo"] = ritardi(g_mossa)
        mossa["disegni"] = {"disegni_s": 0.0, "esito": "nessuna scena"}
        p = p_scena_morde(mossa)
        caso("13b · ⛔ GUASTO: «ferma» che consegna 25 fot/s → ROSSO",
             "passa = False, e nomina salvaschermo/orologio/notifica",
             p, p[0] is False and "NON E' FERMA" in p[1])
        # ⛔ e il pavimento di §2.1 NON deve dare rosso a un desktop fermo
        p = p_ritmo(ferma_n)
        caso("13c · ⚠ il pavimento di 25 fot/s NON accusa un desktop fermo",
             "p_ritmo passa = None, e dice che quel pavimento e' di un desktop "
             "che LAVORA", p, p[0] is None)
        p = p_quota_chiavi(ferma_n)
        caso("13d · ⚠ «una chiave su due» su due fotogrammi non e' una spirale",
             "p_quota_chiavi passa = None", p, p[0] is None)
        p = p_I1(ferma_n, mossa, 1, 5, False)
        caso("13e · ⚠ I1 sul ritmo NON si giudica nel braccio «ferma»",
             "passa = None", p, p[0] is None)
        p = p_scena_morde(ferma_n)
        caso("13f · risanato: il desktop torna fermo → verde", "passa = True",
             p, p[0] is True)

        # ── 14 · ⛔⛔ L'ANCORA CHE NON RITROVA IL SEI ──────────────────────
        print("\n  ── 14 · ⛔ il braccio d'ancora che NON ritrova il sei ──")
        globals()["SCENA"] = "satura"
        p = p_ancora_ritrova(CAPIENZA_ANCORA)
        caso("14 · sano: l'ancora ne ritrova %d → verde" % CAPIENZA_ANCORA,
             "passa = True", p, p[0] is True)
        p = p_ancora_ritrova(CAPIENZA_ANCORA - 1)
        caso("14b · ⛔ GUASTO: l'ancora ne ritrova %d → ROSSO e il confronto "
             "si RIFIUTA" % (CAPIENZA_ANCORA - 1),
             "passa = False, e nomina «IL CONFRONTO FRA LE TRE SCENE NON VALE»",
             p, p[0] is False and "NON VALE" in p[1])
        p = p_ancora_ritrova(CAPIENZA_ANCORA + 2)
        caso("14c · ⛔ GUASTO anche AL RIALZO: otto invece di sei → ROSSO",
             "passa = False (⚠ un numero piu' alto non e' un bel risultato: e' "
             "un'altra macchina)", p, p[0] is False)
        p = p_ancora_ritrova(None)
        caso("14d · ⚠ capienza non calcolata → NON GIUDICO", "passa = None",
             p, p[0] is None)
        p = p_ancora_ritrova(CAPIENZA_ANCORA)
        caso("14e · risanato → verde", "passa = True", p, p[0] is True)

        # ── 15 · LA CAPIENZA, e chi la fa scendere ────────────────────────
        print("\n  ── 15 · ⭐ la capienza: il gradino piu' alto che REGGE ──")

        def _salita_finta(cade_al, i1_dal=None):
            gr = []
            for g in range(1, 9):
                ses, pred = {}, []
                for i in range(1, g + 1):
                    fps = 38.0 if g < cade_al else 1.5
                    n = B70.misura(_fab(int(fps * 40), fps=fps, byte=5600,
                                        chiave_ogni=0, primo_numero=1000 * g),
                                   40.0, scaldata_s=0.0)
                    ses[i] = n
                if i1_dal and g >= i1_dal:
                    pred.append({"predicato": "⛔ I1 — chi era gia' dentro NON "
                                              "peggiora", "passa": False,
                                 "perche": "finto"})
                gr.append({"gradino": g, "quale": "normale", "sessioni": ses,
                           "predicati": pred})
            return {"gradini": gr}

        n_cap, perche_cap, _d = capienza(_salita_finta(7))
        caso("15 · sano: cede al settimo ⇒ capienza 6", "numero = 6",
             (n_cap, perche_cap[:60]), n_cap == 6)
        # ⛔ E il guasto: I1 rosso al quinto, e il ritmo che NON se n'e' accorto.
        n2, p2, _d = capienza(_salita_finta(99, i1_dal=5))
        caso("15b · ⛔ GUASTO: I1 violato dal quinto, ritmo ancora a 38/s ⇒ la "
             "capienza scende a 4",
             "numero = 4 (⭐ il ritmo da solo avrebbe detto 8)",
             (n2, p2[:60]), n2 == 4)
        globals()["SCENA"] = "ferma"
        n3, p3, _d = capienza(_salita_finta(7))
        caso("15c · ⚠ sul braccio «ferma» la capienza NON si definisce",
             "numero = None, e dice perche'", (n3, p3[:70]),
             n3 is None and "NON DEFINITA" in p3)
    finally:
        globals()["SCENA"] = vecchia_scena

    # ── 16 · LA LEGGE, e i due modi di sbagliarla ─────────────────────────
    print("\n  ── 16 · ⭐ la retta del costo, con pendenza ed errore ──")
    retta = legge_del_costo([(0.0, 1.0), (10.0, 3.0), (20.0, 5.0), (30.0, 7.0)])
    ok = (retta and abs(retta["pendenza"] - 0.2) < 1e-9
          and abs(retta["intercetta"] - 1.0) < 1e-9 and retta["r2"] > 0.9999)
    caso("16 · un costo PROPORZIONALE si ritrova esatto",
         "pendenza 0,2 · intercetta 1,0 · R² 1,0 · errore max 0",
         retta, bool(ok))
    # ⛔ E il GRADINO: se il costo ha uno scalino, la retta lo deve DENUNCIARE
    #    con l'errore, non nasconderlo con un R² che sembra buono.
    gradino = legge_del_costo([(0.0, 1.0), (10.0, 1.1), (20.0, 9.0), (30.0, 9.1)])
    ok = gradino and gradino["errore_relativo_max"] > 0.15
    caso("16b · ⛔ un costo A GRADINO: l'errore lo denuncia",
         "errore relativo massimo sopra il 15 % ⇒ il budget NON si calcola "
         "con questa retta", gradino, bool(ok))
    caso("16c · ⛔ due punti soli → NIENTE retta",
         "torna None: una retta per due punti non e' una legge, e' una "
         "definizione", legge_del_costo([(0.0, 1.0), (10.0, 3.0)]),
         legge_del_costo([(0.0, 1.0), (10.0, 3.0)]) is None)
    caso("16d · ⛔ un `None` fra i punti non diventa zero",
         "tre punti di cui uno con y = None ⇒ restano due ⇒ None",
         legge_del_costo([(0.0, 1.0), (10.0, None), (20.0, 5.0)]),
         legge_del_costo([(0.0, 1.0), (10.0, None), (20.0, 5.0)]) is None)

    # ── 17 · IL CONTO SCARNO — e le colonne che restano `None` ────────────
    print("\n  ── 17 · ⛔ sotto il minimo si CONTA, ma non si INVENTA ──")
    gs = _fab(3, fps=0.075, byte=266, chiave_ogni=1)
    rifiuto = B70.misura(gs, 40.0, scaldata_s=0.0)
    caso("17 · la riduzione di 09-b70 si RIFIUTA sotto i 30 fotogrammi, ed e' "
         "giusto", "esito «NON HO NIENTE DA GIUDICARE»",
         rifiuto.get("esito"), "NON HO NIENTE" in rifiuto.get("esito", ""))
    sc = conto_scarno(gs, 40.0, rifiuto)
    ok = (sc["esito"] == "misurato" and sc["fotogrammi"] == 3
          and sc["byte_per_fotogramma"] == 266
          and sc["quota_delta"] is None and sc["fps_finestra_min"] is None
          and sc["buchi_numero"] is None)
    caso("17b · ⭐ il conto scarno conta fotogrammi e byte, e lascia `None` "
         "dove non si puo' calcolare",
         "3 fotogrammi · 266 B/fot · quota_delta, peggior secondo e buchi = None",
         {k: sc[k] for k in ("fotogrammi", "byte_per_fotogramma", "quota_delta",
                             "fps_finestra_min", "buchi_numero")}, ok)

    # ── 18 · ⛔ IL METRO DEI DISEGNI SI TARA PRIMA (`LEZIONI.md` §1.33) ────
    print("\n  ── 18 · il lettore del blocco della scena: valori NOTI iniettati ──")
    import struct as _st
    ns = {}
    exec(compile(SCENE.split("passo = sys.argv[1]")[0], "10-b92-scene.py",
                 "exec"), ns)
    FRM = ns["FORMATO"]
    quanti_campi = len(_st.unpack(FRM, b"\0" * _st.calcsize(FRM)))
    campi = [0] * quanti_campi
    campi[ns["I_SEQ"]] = 2            # seq PARI: campione coerente
    campi[ns["I_DISEGNI"]] = 123456
    campi[ns["I_LARG"]], campi[ns["I_ALT"]] = 1280, 720
    campi[ns["I_PID"]] = 4242
    vals = [campi[i] if i not in (29, 30, 31, 32) else b"x"
            for i in range(quanti_campi)]
    perc = "/dev/shm/10b92-certifica-lettore"
    try:
        with open(perc, "wb") as f:
            f.write(_st.pack(FRM, *vals))
        letto = ns["leggi_shm"]("10b92-certifica-lettore")
        ok = (letto.get("disegni") == 123456 and letto.get("larghezza") == 1280
              and letto.get("altezza") == 720 and letto.get("pid") == 4242)
        caso("18 · il lettore dei DISEGNI ritrova i valori iniettati",
             "disegni 123 456 · 1280x720 · pid 4242", letto, ok)
        # ⛔ E il guasto: `seq` DISPARI vuol dire campione a meta' — non si usa.
        campi[ns["I_SEQ"]] = 3
        vals = [campi[i] if i not in (29, 30, 31, 32) else b"x"
                for i in range(quanti_campi)]
        with open(perc, "wb") as f:
            f.write(_st.pack(FRM, *vals))
        letto = ns["leggi_shm"]("10b92-certifica-lettore")
        # ⭐ `seq` dispari MA blocco FERMO: e' lo stato in cui vive la scena
        #   «vero» durante la quiete dello strappo (SIGSTOP a meta' di
        #   `stato_pubblica`).  ⇒ Il valore vale, e il fatto si DICHIARA.
        caso("18b · ⭐ `seq` DISPARI ma blocco FERMO (scena in SIGSTOP) → il "
             "valore vale, e si dichiara",
             "disegni 123 456, e `campione_congelato` = True",
             letto, letto.get("disegni") == 123456
             and letto.get("campione_congelato") is True)
        # ⛔ E IL GUASTO VERO: `seq` dispari **e** il blocco che CAMBIA — cioe'
        #    uno scrittore vivo che non chiude mai la scrittura.  ⇒ Li' non c'e'
        #    nessun valore da prendere, e il lettore si RIFIUTA.
        import threading
        ferma = threading.Event()

        def _scrittore_impazzito():
            k = 0
            while not ferma.is_set():
                c = list(campi)
                c[ns["I_SEQ"]] = 3
                c[ns["I_DISEGNI"]] = 900000 + k
                k += 1
                v = [c[i] if i not in (29, 30, 31, 32) else b"x"
                     for i in range(quanti_campi)]
                try:
                    # ⛔ `r+b` e non `wb`: `wb` TRONCA, e il lettore
                    #    rifiuterebbe per «blocco troncato» invece che per il
                    #    guasto che si sta innestando.  ⚠ Un guasto che scatta
                    #    per il motivo sbagliato non ha certificato niente.
                    with open(perc, "r+b") as f:
                        f.seek(0)
                        f.write(_st.pack(FRM, *v))
                except OSError:
                    return
                time.sleep(0.0002)

        t = threading.Thread(target=_scrittore_impazzito, daemon=True)
        t.start()
        try:
            letto = ns["leggi_shm"]("10b92-certifica-lettore")
        finally:
            ferma.set()
            t.join(timeout=2)
        caso("18b-bis · ⛔ GUASTO: `seq` dispari E il blocco CAMBIA → si RIFIUTA",
             "nessun `disegni`: non e' coerente e non e' nemmeno fermo",
             letto, "disegni" not in letto
             and "non e' nemmeno fermo" in str(letto.get("esito")))
    finally:
        try:
            os.unlink(perc)
        except OSError:
            pass
    letto = ns["leggi_shm"]("10b92-non-esiste-affatto")
    caso("18c · ⛔ il blocco che NON C'E' → `None`, non zero disegni",
         "nessun `disegni`, e un `esito` che dice perche'", letto,
         "disegni" not in letto and bool(letto.get("esito")))

    print("\n== %d casi · %d rossi" % (len(esiti), len(rossi)))
    for r in rossi:
        print("   ⛔ %s" % r)
    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "10-b92-certifica.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    if rossi:
        return 1
    print("== ⭐ OGNI PREDICATO E' STATO VISTO FALLIRE, E POI RISANARE")
    return 0


def giro_finto(quanti, fallisce_al=None, muore_al=None, ancora_ferma=False):
    """⛔ La SALITA VERA, contro una macchina finta.

    ⚠ Non e' una simulazione della salita: e' `salita()` stessa, con le sole
      quattro funzioni che toccano la macchina sostituite.  ⇒ Il `break` che
      ferma la salita, il `None` del cliente morto e l'ordine dei predicati sono
      quelli che gireranno per davvero.  Provarli su una copia sarebbe
      certificare un altro programma.
    """
    orig = {n: globals()[n] for n in
            ("apri_sessione", "accendi_scena", "assicura_scene", "sonda",
             "chi_c_e", "fetta", "registro_righe", "conti_server",
             "mappa_provenienze", "spegni_scene", "disegni_tutte")}
    stato = {"t": 100000.0}

    def f_apri(i, resta):
        if fallisce_al is not None and i == fallisce_al:
            return False, ("⛔ la sessione %d NON si e' aperta in 120 s "
                           "(guasto innestato)" % i)
        return True, "SESSIONE stato=1 tela=1920x1080"

    def f_sonda(q):
        # ⛔ La fotografia porta l'ANCORA: e' lei che fa avanzare il confine del
        #    gradino.  ⚠ Con `ancora_ferma` non avanza — ed e' il guasto.
        if not ancora_ferma:
            stato["t"] += 1000.0
        return {"t_ms": stato["t"], "cpu": {"totale": 0, "inattivo": 0,
                                            "nuclei": 20},
                "rete": {}, "processi": {"per_uid": {}, "negati": 0,
                                         "server": {"pss_kib": 0, "rss_kib": 0,
                                                    "cpu_jiffies": 0, "quanti": 0},
                                         "clienti": {"pss_kib": 0, "rss_kib": 0,
                                                     "cpu_jiffies": 0, "quanti": 0}},
                "gpu": {"motori": {}, "clienti": 0, "per_uid": {},
                        "altri_pdev": {}, "estranei": 0, "estranei_pid": []},
                "costo_ms": 1.0}

    def f_vive(q):
        v = {}
        for i in range(1, q + 1):
            v[i] = not (muore_al and muore_al[1] == i)
        return v

    contatore = {"n": 5000}

    def f_fetta(i, t0, t1, durata):
        contatore["n"] += 2000
        g = _fab(900, fps=30.0, byte=25000, chiave_ogni=60,
                 primo_numero=contatore["n"])
        n = B70.misura(g, durata, scaldata_s=0.0)
        n["ritardo"] = ritardi(g)
        num = sorted(x["numero"] for x in g)
        n["numeri"] = [num[0], num[-1]]
        return n

    try:
        globals()["apri_sessione"] = f_apri
        globals()["accendi_scena"] = lambda i, m=None: "FINTO-0"
        globals()["assicura_scene"] = lambda q: []
        globals()["sonda"] = f_sonda
        globals()["chi_c_e"] = lambda q: (
            f_vive(q), {i: True for i in range(1, q + 1)}, [])
        globals()["fetta"] = f_fetta
        globals()["registro_righe"] = lambda: 1000
        globals()["conti_server"] = lambda a, b, c: {"esito": "finto",
                                                     "posti_occupati": None,
                                                     "posti_negati": [],
                                                     "spirale_in_somma": {},
                                                     "per_utente": {}}
        globals()["mappa_provenienze"] = lambda: ({}, None)
        globals()["spegni_scene"] = lambda q: None
        # ⛔ E ANCHE IL LETTORE DEI DISEGNI, o `--certifica` andrebbe a
        #    bussare alla macchina di prova — che e' proprio quel che il modo
        #    dichiara di NON fare.  ⚠ Se ne accorge solo chi guarda l'orologio.
        globals()["disegni_tutte"] = lambda q: dict(
            [(i, {"disegni": 1000 + 500 * i, "larghezza": 1920,
                  "altezza": 1080, "pid": 42 + i, "seq": 2})
             for i in range(1, q + 1)] + [("t_ms", stato["t"])])
        vecchio_sleep = time.sleep
        time.sleep = lambda s: None
        try:
            esiti, rossi, muti, fette, prima = salita(quanti, 1, False, 10)
        finally:
            time.sleep = vecchio_sleep
    finally:
        for n, v in orig.items():
            globals()[n] = v
    esiti["rossi"] = rossi
    esiti["muti"] = muti
    return esiti


def controllo_terreno_fase():
    """⛔ IL CONTROLLO DEL TERRENO DELLA FASE — `banchi/10-b0-terreno.sh`, 21
       predicati, `[M]` 30 guasti su 30 lo fanno mordere.

    ⛔⛔ E SI CHIAMA COL LUCCHETTO GIA' IN MANO (`LUCCHETTO_MIO=1`): «il
        lucchetto e' libero» non basta, dev'essere **mio**.  Un banco che
        misurasse la GPU mentre un altro la satura non darebbe rosso — darebbe
        un numero plausibile (`LEZIONI.md` §1.26).

    Esce 0 regge · 1 non regge · ⛔ **2 non ho potuto verificare**, che non e'
    un verde.
    """
    perc = os.path.join(QUI, "10-b0-terreno.sh")
    if not os.path.exists(perc):
        _dub("⚠ manca «%s»: NON ho controllato il terreno della fase" % perc)
        return False
    amb = dict(os.environ)
    amb.update({"CHI": IO_SONO, "LUCCHETTO_MIO": "1", "PORTA": str(PORTA),
                "UTENTE": utente(1), "ALBERO": ALB, "LAV": LAV,
                "LUCCHETTO": LUCCHETTO, "MACCHINA": MACCHINA,
                "PAROLA_SUDO": PAROLA_SUDO, "IND": IND})
    p = subprocess.run(["bash", perc], env=amb)
    if p.returncode == 0:
        _ok("⭐ il terreno della fase regge (10-b0-terreno.sh, 21 predicati)")
        return True
    _ko("⛔ 10-b0-terreno.sh esce %d: %s"
        % (p.returncode, "IL TERRENO NON REGGE" if p.returncode == 1
           else "NON HO POTUTO VERIFICARE — e non e' un verde"))
    return False


def durata_del_giro(a):
    """Quanto dura la salita, con margine — ⛔ e il numero e' UNO SOLO.

    Serve a due cose che devono finire insieme: il `--resta` dei clienti e il
    lucchetto della GPU.  ⚠ Due formule vicine sarebbero due numeri che
    divergono, e il primo che scade rovina il giro dell'altro.

    ⭐ Il conto: per ogni gradino ci vogliono `durata` secondi di misura, piu'
    l'apertura di una sessione grafica nuova (⚠ sotto carico non e' un secondo:
    `[M]` da 2 a 40 s), l'assestamento, due fotografie e una fetta per ogni
    sessione viva.  ⇒ 120 s a gradino di margine, che e' abbondante e si paga
    solo se serve.
    """
    return int((a.durata + 120) * a.quanti
               + (2 * a.durata + 120 if a.doppia else 0) + 600)


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    global B70
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "taratura", "uno-per-volta", "salita",
                            "legge", "stato", "sgombra"])
    p.add_argument("--scena", choices=["satura", "vero", "ferma"], default=None,
                   help="⭐ satura = l'ANCORA del primo giro (predefinito) · "
                        "vero = due finestre vere + la scena in finestra a "
                        "strappi · ferma = il desktop aperto e basta")
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca.  Non tocca la macchina di prova")
    p.add_argument("--quanti", type=int, default=QUANTI)
    p.add_argument("--durata", type=int, default=45,
                   help="secondi a regime per gradino (⚠ §1.32: i giri corti "
                        "sottostimano)")
    p.add_argument("--doppia", action="store_true",
                   help="⭐ rifa' il gradino pieno a DOPPIA durata: se il "
                        "risultato segue l'esposizione, il numero corto "
                        "sottostimava")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⛔ solo per la messa a punto: i numeri di un giro "
                        "senza lucchetto NON valgono e non si riferiscono")
    a = p.parse_args()
    if a.scena:
        globals()["SCENA"] = a.scena

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)
    B70 = _importa_b70()

    if a.passo == "stato":
        return 0 if terreno(a.quanti) else 2
    if a.passo == "sgombra":
        rc, out, err = root("true")
        subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                        "sgombra"])
        return 0
    if a.passo == "taratura":
        _log("⛔ IL METRO SI TARA PRIMA — `LEZIONI.md` §1.33")
        sano, guai = tara_riduzione(B70)
        if not sano:
            for g in guai:
                _ko(g)
            return 1
        _ok("la riduzione importata da 09-b70 ritrova i valori iniettati")
        if not terreno(a.quanti):
            return 2
        _log("⭐ LA SONDA, sulla macchina vera — e dichiara il proprio costo")
        f0 = sonda(a.quanti)
        if not f0:
            return 2
        time.sleep(5)
        f1 = sonda(a.quanti)
        d = fra(f0, f1, a.quanti)
        _inf("costo della sonda: %s ms" % d.get("costo_sonda_ms"))
        _inf(json.dumps(d, ensure_ascii=False)[:900])
        passa, perche = p_metro_gpu(d)
        (_ok if passa else (_dub if passa is None else _ko))(
            "il metro della GPU: %s" % perche)
        return 0 if passa is not False else 1
    if a.passo == "uno-per-volta":
        _log("⛔ prima di misurare, i palchi del giro precedente si CHIUDONO "
             "(I4: sopravvivono al distacco, ed e' giusto — ma non sono miei "
             "da misurare)")
        chiudi_palchi(a.quanti)
        if not terreno(a.quanti):
            return 2
        esiti, guai = uno_per_volta(a.quanti)
        with open(os.path.join(FUORI, "10-b92-uno-per-volta.json"), "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1)
        return 1 if guai else 0

    if a.passo == "legge":
        # ⭐ UNA sessione, cinque livelli: il lucchetto serve lo stesso — e' pur
        #   sempre un carico di GPU, e mentre gira nessun altro puo' misurare.
        _log("10-b92 · LA LEGGE — porta %d · UNA sessione · tela %s" % (PORTA, TELA))
        luc = None
        quanto = int((a.durata + 90) * len(LIVELLI) + 600)
        if LUCCHETTO_ESTERNO and not a.senza_lucchetto:
            _ok("⭐ il lucchetto della GPU e' gia' MIO: lo tiene il lanciatore")
        elif not a.senza_lucchetto:
            luc = _lucchetto()
            _inf("⛔ chiedo il lucchetto della GPU per %d s" % quanto)
            try:
                luc.prendi(IO_SONO, secondi=quanto, attesa=7200)
            except Exception as e:
                _ko("⛔ NON MISURO: %s" % e)
                return 2
        try:
            # ⛔⛔ PRIMA IL LUCCHETTO, POI GLI UTENTI: gli utenti `provamt*` sono
            #     CONDIVISI fra gli agenti di questo giro, e chiudere i palchi
            #     di qualcun altro mentre sta misurando gli rovina il giro.
            chiudi_palchi(a.quanti)
            # ⚠ Se il terreno non regge si esce 2, e il `finally` qui sotto
            #   molla il lucchetto: chi aspetta non deve pagare il mio rifiuto.
            if not a.senza_lucchetto and not controllo_terreno_fase():
                return 2
            if not terreno(1):
                return 2
            esiti, rossi, muti = giro_legge(a.durata, quanto)
        finally:
            _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
            root("pkill -f '10-b92-scene[.]py strappi'; true")
            spegni_scene(1)
            root("pkill -f '10-b92-cliente[.]py --cliente'; true")
            time.sleep(2)
            chiudi_palchi(a.quanti)
            if luc:
                luc.molla(IO_SONO)
        with open(os.path.join(FUORI, "10-b92-legge.json"), "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
        _inf("esiti in %s/10-b92-legge.json" % FUORI)
        for r in rossi:
            _ko(r)
        for m in muti:
            _dub(m)
        return 1 if rossi else (3 if muti else 0)

    # ── LA SALITA ─────────────────────────────────────────────────────────
    _log("10-b92 · LA SALITA — porta %d · %d sessioni · scena «%s» · tela %s · "
         "codec «%s»" % (PORTA, a.quanti, SCENA, TELA, CODEC_CHIESTO))
    sano, guai = tara_riduzione(B70, dillo=False)
    if not sano:
        for g in guai:
            _ko("⛔ il metro non e' tarato: %s" % g)
        return 2
    _ok("il metro e' tarato (giornale a valore noto ritrovato)")

    # ⛔⛔ IL LUCCHETTO DELLA GPU — sono l'agente che carica di piu' la
    #     macchina, e mentre giro nessun altro puo' misurare niente.
    luc = None
    if LUCCHETTO_ESTERNO and not a.senza_lucchetto:
        _ok("⭐ il lucchetto della GPU e' gia' MIO: lo tiene il lanciatore "
            "(«%s»).  ⛔ Non lo prendo e non lo mollo io — lo verifica "
            "`10-b0-terreno.sh` con LUCCHETTO_MIO=1" % IO_SONO)
    elif not a.senza_lucchetto:
        luc = _lucchetto()
        # ⛔ Il lucchetto si prende per il tempo del giro e si molla subito:
        #    sono l'agente che carica di piu' la macchina, e mentre giro nessun
        #    altro puo' misurare niente.  ⚠ Chiederne il doppio «per sicurezza»
        #    vorrebbe dire fermare gli altri per un'ora a vuoto — ma chiederne
        #    troppo poco e' peggio: chi arriva dopo la scadenza **scassina**, e
        #    da quel momento due carichi di GPU si falsano in silenzio.
        #    ⇒ Lo stesso numero di `--resta`: il lucchetto e la vita dei clienti
        #      finiscono insieme, ed e' l'unico modo perche' non se ne vada uno
        #      prima dell'altro.
        quanto = durata_del_giro(a)
        _inf("⛔ chiedo il lucchetto della GPU per %d s (%d min): e' il tempo "
             "stimato del giro piu' dieci minuti" % (quanto, quanto // 60))
        # ⛔ L'attesa e' LUNGA apposta: alla fase 10 sulla macchina lavorano
        #    dieci agenti insieme, e `[M]` 24 agosto 2026 il lucchetto e' stato
        #    chiesto da un altro per **98 minuti di fila**.  ⚠ Un'attesa corta
        #    non fa arrivare prima: fa ALZARE dopo un'ora di coda, e l'ora e'
        #    persa lo stesso.
        # ⭐ E se proprio non arriva il turno, si esce **2** con una riga che lo
        #   dice: un banco che misurasse senza lucchetto produrrebbe numeri che
        #   non si possono riferire (`LEZIONI.md` §1.26).
        try:
            luc.prendi(IO_SONO, secondi=quanto, attesa=7200)
        except Exception as e:
            _ko("⛔ NON MISURO: %s" % e)
            return 2
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono e non si "
             "riferiscono")

    esiti, rossi, muti, fette, prima = {}, [], [], {}, {}
    try:
        # ⛔⛔ PRIMA IL LUCCHETTO, POI GLI UTENTI — la regola del secondo giro
        #     della fase 10: `provamt1…provamt11` sono CONDIVISI fra gli agenti,
        #     e chiudere i palchi mentre un altro sta misurando gli rovina il
        #     giro **senza dargli rosso**.  ⇒ Chiusura e terreno stanno DENTRO
        #     il possesso, non prima.
        _log("⛔ prima di misurare, i palchi del giro precedente si CHIUDONO")
        chiudi_palchi(a.quanti)
        # ⛔ E POI IL CONTROLLO DEL TERRENO DELLA FASE, col lucchetto in mano.
        # ⚠ Se non regge si esce 2, e il `finally` qui sotto molla il
        #   lucchetto: chi aspetta non deve pagare il mio rifiuto.
        if not a.senza_lucchetto and not controllo_terreno_fase():
            return 2
        if not terreno(a.quanti):
            return 2
        # ⚠ Il cliente deve restare attaccato per TUTTA la salita, non per il
        #   suo gradino: il gradino 10 misura anche s1.  ⛔ E il margine e'
        #   largo apposta — un cliente che se ne va un minuto prima dell'ultimo
        #   gradino non da' rosso: fa sparire la riga di s1 proprio dal gradino
        #   che la fase esiste per misurare.
        resta = durata_del_giro(a)
        esiti, rossi, muti, fette, prima = salita(a.quanti, a.durata, a.doppia,
                                                  resta)
        riassunto(esiti, fette, prima, a.quanti)
    finally:
        _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
        spegni_scene(a.quanti)
        # ⛔ La stessa classe di caratteri del riquadro di
        #    `cerca_giornale`: senza, `pkill` ammazzerebbe la shell che lo sta
        #    eseguendo, e la pulizia finirebbe a meta' in silenzio.
        root("pkill -f '10-b92-cliente[.]py --cliente'; true")
        time.sleep(3)
        chiudi_palchi(a.quanti)
        if luc:
            luc.molla(IO_SONO)

    with open(os.path.join(FUORI, "10-b92-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
    _inf("esiti in %s/10-b92-esiti.json" % FUORI)

    _log("IL VERDETTO — %d gradini · %d rossi · %d non giudicati"
         % (len(esiti.get("gradini", [])), len(rossi), len(muti)))
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
