#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b90-filo — ⭐⭐⭐ IL SECONDO BUDGET, QUELLO DI **RETE**: il metro del filo,
              tarato prima, e i numeri che ne escono.

`DECISIONI.md` §3.1-bis punto 2 lo dichiara aperto e mai misurato: *«un secondo
budget, di rete, accanto a quello di GPU: dieci sessioni x 30 Mbit/s sono 300
Mbit/s sul filo del server.  Da misurare in fase 10.»*  E il fatto della fase 9
che rende la domanda urgente: `[M]` il caso duro in H.264 chiede **44,6 Mbit/s
= 223 % del pavimento** (fase 9 §14.2).  ⇒ per dieci il conto non e' 300, e'
mezzo gigabit.

═══════════════════════════════════════════════════════════════════════════════
1 · ⛔ DOVE SI CONTANO I BYTE — e la differenza fra i posti **E'** il risultato
═══════════════════════════════════════════════════════════════════════════════

Ci sono quattro posti in cui si puo' contare, e contano quattro cose diverse.
Questo banco li legge **tutti e quattro insieme**, perche' un numero solo non
dice di che cosa e' il numero.

  | posto | dove si legge | che cosa comprende |
  |---|---|---|
  | **il carico utile** | righe `SPEDITO` del registro del server | i byte dei fotogrammi, e basta |
  | ⭐ **per SESSIONE** | `nft`, contatore per **porta del cliente** | + intestazioni QUIC, ACK, **ritrasmissioni**, audio PCM, IP+UDP |
  | **per MACCHINA, mio** | `nft`, contatore sulla mia porta di servizio | la somma delle mie sessioni |
  | **l'interfaccia** | `/sys/class/net/lo/statistics/tx_bytes` | ⛔ **tutto quel che passa**, anche dei vicini |

  ⛔ E QUEL CHE NESSUNO DEI QUATTRO CONTA: le **ritrasmissioni scartate dal
     nucleo**, il traffico che non arriva mai al dispositivo, e — sul rame — la
     cornice ethernet.  Il primo di questi qui non esiste (`lo` non perde), il
     terzo si somma a mano (vedi sotto).

⭐ **L'UNITA' E' LA STESSA PER `nft` E PER L'INTERFACCIA, ed e' MISURATA, non
   dedotta.**  `[M]` 24 agosto 2026: 1 000 datagrammi da 1 000 byte di carico
   ⇒ `nft` **1 028 000** byte, `lo/tx_bytes` **1 028 000** byte per gli stessi
   pacchetti.  1 028 = 1 000 + 8 (UDP) + 20 (IP).  ⇒ tutt'e due contano la
   **lunghezza IP**.

⛔⛔ **E QUEL CHE NESSUNO DEI DUE VEDE VA SCRITTO ACCANTO A OGNI NUMERO**: su un
    filo di RAME ogni pacchetto costa **38 byte in piu'** che qui non compaiono
    (14 di intestazione ethernet + 4 di FCS + 8 di preambolo + 12 di spazio fra
    pacchetti).  Con datagrammi QUIC da ~1 250 byte fanno **+3,0 %**.
    ⇒ ogni Mbit/s di questo banco vale **1,030 Mbit/s di rame**.

⚠ E il secondo limite dichiarato: qui il cliente e il server stanno sulla
  **stessa macchina**, quindi il filo e' `lo`, dove la MTU e' 65536.  Il numero
  vale come **domanda di banda del prodotto**, non come promessa su una linea
  vera — ed e' esattamente la grandezza che serve al budget, perche' il budget
  chiede *«quanto chiede una sessione»*, non *«quanto sopporta un cavo»*.

═══════════════════════════════════════════════════════════════════════════════
2 · ⛔ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33)
═══════════════════════════════════════════════════════════════════════════════

In fase 9 la misura andata male e' andata male proprio cosi': una grandezza mai
messa alla prova sui casi estremi (`pkt_lost` ordinava i due casi **al
contrario**).  ⇒ qui il metro si tara **iniettando un flusso di banda nota**
(`10-b90-getto.c`, in C perche' un getto in Python sarebbe il collo e
misurerebbe se stesso) a piu' ritmi, e si calcolano **pendenza e costante**
della retta «letto = a x chiesto + b».  Se il metro sbaglia del 15 %, quel 15 %
si scrive accanto a ogni numero che produrra'.

⛔ E si tara **per sessione** e **per macchina insieme**: il getto prende una
   porta d'origine fissa, quindi il contatore per sessione lo deve ritrovare
   **da solo**, e la somma delle sessioni deve tornare col totale della mia
   porta e col totale dell'interfaccia meno il rumore dei vicini.

═══════════════════════════════════════════════════════════════════════════════
3 · ⛔ IL RUMORE DEI VICINI SI CONTA, NON SI SPERA
═══════════════════════════════════════════════════════════════════════════════

`lo` e' di tutti: gli altri agenti della fase 10 ci fanno passare le loro
sessioni nello stesso minuto.  ⛔ Un banco che confrontasse la somma delle sue
sessioni col contatore dell'interfaccia darebbe **rosso** ogni volta che un
vicino lavora, e il rosso non sarebbe suo.
⇒ La catena di `nft` ha **tre** contatori in fila (le regole `counter` non
  fermano il pacchetto, quindi contano tutte e tre):

      mio_giu   = server -> cliente sulla mia porta
      mio_su    = cliente -> server sulla mia porta
      tutto     = ogni pacchetto IP che esce da `lo`, di chiunque

  e allora **altrui = tutto - mio_giu - mio_su**, che si stampa accanto a ogni
  riga.  ⭐ E `tutto` contro `lo/tx_bytes` e' il controllo del metro su se
  stesso: due contatori indipendenti sugli stessi pacchetti.

═══════════════════════════════════════════════════════════════════════════════
4 · ⛔ «NON HO MISURATO» NON E' «ZERO» — le quattro guardie, e ognuna da' ROSSO
═══════════════════════════════════════════════════════════════════════════════

  G1 · **il contatore letto PRIMA che il flusso parta.**  Zero byte non e'
       «0 Mbit/s»: e' «non c'era niente da misurare».  Il banco si RIFIUTA.
  G2 · **il contatore che si azzera o va indietro.**  Un `nft flush` di un
       vicino, un riavvio del server, un `reset` fuori posto: la differenza
       diventa negativa (o enorme, se qualcuno la mettesse senza segno).  Il
       banco si RIFIUTA — nessun numero negativo, nessun numero enorme.
  G3 · **la scena che non si muove.**  Byte per fotogramma e fotogrammi
       consegnati accanto a ogni riga (`LEZIONI.md` §1.30): una scena ferma
       abbassa il numero e non lo dichiara.
  G4 · **la somma per sessione che non torna** col totale della mia porta oltre
       la tolleranza dichiarata ⇒ ROSSO.  ⭐ Se non torna, o sono le
       intestazioni, o e' una lettura sbagliata: si dice quale.

═══════════════════════════════════════════════════════════════════════════════
I CODICI D'USCITA
═══════════════════════════════════════════════════════════════════════════════

    0   CONFORME
    1   NON CONFORME — c'e' almeno un rosso
    2   uso sbagliato, terreno assente, o la rete non si e' potuta rimettere
    3   ⛔ NON HO NIENTE DA GIUDICARE — una guardia si e' rifiutata.
        ⚠ Non e' un verde.

═══════════════════════════════════════════════════════════════════════════════
`[M]` I NUMERI USCITI DA QUI — 24 agosto 2026, i5-13500T · Intel UHD 730
      (`renderD128`, l'integrata), tela 2560x1080, H.264, cure di fase 9
      ACCESE salvo dove scritto, sotto lucchetto della GPU
═══════════════════════════════════════════════════════════════════════════════

⭐ IL METRO E' ESATTO, e non «vicino»: getto a 5 · 20 · 60 Mbit/s (12x di
   escursione) ⇒ scarto sui byte **+0,0000 %** su tutt'e tre, pendenza
   **1,000000**, costante **0**, e il metro conta gli stessi **datagrammi** che
   il getto dichiara di aver mandato.  I conti si chiudono a saldo zero:
   `interfaccia = mio + tara + ICMP + vicini`.

| scena, 30 s | ⭐ **MEDIA sul filo** | picco | ×10 | fotogrammi | byte/fot |
|---|---|---|---|---|---|
| ferma | **0,0029** Mbit/s | 0,010 | **0,03** | 1 | 316 |
| desktop vero | **0,531** Mbit/s | 0,756 | **5,3** | 673 | 2 099 |
| duro (`duro.mp4`) | **4,478** Mbit/s | 21,9 | **44,8** | 907 | 16 884 |

  · il **carico utile** del desktop vero e' 0,374 Mbit/s ⇒ ⭐ **il filo costa il
    +42 %** in piu' del video (QUIC + ACK + audio + IP/UDP).  ⛔ Il budget si
    fa sul filo, non sul video;
  · i datagrammi sono da **1 467-1 472 byte** ⇒ sul RAME ci sarebbero **+38
    byte a pacchetto**, cioe' **+2,6 %**: i numeri di `lo` si traducono.

⭐⭐⭐ E LA SCENA FERMA E' LA SORPRESA, perche' fase 9 §14.2 la dava a **2,427
      Mbit/s** e qui fa **0,0029**.  ⛔ Non si e' dedotto perche': si e' spenta
      la cura e si e' guardato.

| scena ferma, 30 s | Mbit/s sul filo | pacchetti |
|---|---|---|
| cure ACCESE (oggi) | **0,0024** | 6 |
| ⛔ `--niente-audio-silenzio` | **2,4275** | 6 060 |

  ⇒ ⭐⭐ **la cura del silenzio dell'audio toglie 992x**, e i **2,4275** ritrovano
    i **2,427** di fase 9 §14.2 alla terza cifra: il metro nuovo e la misura
    vecchia dicono lo stesso numero sullo stesso prodotto con la cura spenta.
  ⇒ ⭐⭐⭐ **×10 sessioni ferme: 0,024 Mbit/s oggi contro 24,3 Mbit/s prima
    della fase 9.**  Il costo del NIENTE, per dieci, e' passato da un ottavo
    del budget a niente.

⛔⛔⭐ IL DIFETTO CHE NESSUNO AVEVA NOMINATO — **le due cure si combattono**

  `[M]` `registro.log`, riga scritta dal prodotto stesso:
      `linea-morta ... causa=silenzio silenzio_ms=10004 soglia_silenzio_ms=10000
       prove=16 persi=0 spediti=0 permille=0`
  ⇒ su un desktop FERMO, su `lo` (perdita **zero**), la sessione viene **chiusa
    dopo 10 secondi**.  ⛔ E l'A/B qui sopra dice perche': con
    `--niente-audio-silenzio` la stessa sessione ferma **sopravvive i 30 s
    interi** (6 060 pacchetti).  ⇒ **la cura dell'audio ha tolto il traffico
    che teneva il cliente a rispondere, e la linea morta — tarata quando quel
    traffico c'era — sfratta chi non ha piu' niente da dire.**
  ⚠ `[?]` misurato col cliente `01-b3-cliente.py` (aioquic, `--resta`, nessun
    input).  Se un BROWSER vero mandi abbastanza da tenersi vivo **non e'
    stato provato**: e' la prova che manca, e vuole il testimone dell'utente.

⭐⭐ LA CONTESA — 60 Mbit/s sulla sola porta, scena dura, cure ACCESE

| sessioni che spedivano | totale | per sessione | soglia | abbandoni | chiavi | ritmo giu'/su' |
|---|---|---|---|---|---|---|
| **1** | 9,19 Mbit/s | 9,10 | 0 | 0 | 0 | 2 / 2 |
| **1** (2 chieste) | 24,09 | 23,88 | 0 | 0 | 0 | 5 / 5 |
| ⛔ **2** (3 chieste) | **48,61** | **27,30 · 20,89** | ⛔ **8** | ⛔ **8** | ⛔ **8** | ⛔ **38 / 38** |

  ⇒ ⭐⭐⭐ **CHI PAGA: TUTTI, E NESSUNO SA PERCHE'.**  A una sessione sola sul
    filo stretto **nessuna cura scatta**.  A due, il totale arriva all'**81 %
    del filo** e scattano **tutte**: 8 passaggi sopra la soglia della coda, 8
    abbandoni, 8 chiavi rifatte, 38 discese e 38 risalite del ritmo.
  ⇒ ⛔ Le cure sono tarate su **una** sessione che vede una rete cattiva.  Due
    sessioni che si contendono il filo **si vedono a vicenda come una rete
    cattiva**, ognuna cala il ritmo, e ⛔ **nessuna riga del registro dice che
    il problema e' il vicino**.
  ⇒ ⚠ E la spartizione **non e' equa**: 27,30 contro 20,89, cioe' **+31 %** a
    chi e' arrivato prima.

⭐ IL TETTO DEL FILO — e non e' lui a decidere

  · `enp7s0` **10 000 Mbit/s** negoziati (⛔ letto da `/sys`, `ethtool` non c'e');
  · UDP nudo su `lo`, misurato: **11,9 Gbit/s con UN filo**, 72,6 con otto —
    non satura mai.  ⇒ ⭐ **il filo non e' il vincolo**, e i numeri di `lo` non
    sono distorti da lui.
  · `[?]` quanto QUIC **cifrato** regga in spazio utente NON e' misurato: il
    getto non cifra, e la distanza fra i due e' il costo del protocollo.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ LA RICONCILIAZIONE DEL 44,6 — `[M]` 24-25 agosto 2026, incarico 10-b7,
      porta 8170, utente `provadec2`, i5-13500T · Intel UHD 730 (`renderD128`),
      2560x1080, H.264, 30 s per braccio, sotto lucchetto della GPU
═══════════════════════════════════════════════════════════════════════════════

⛔ LA DOMANDA.  Fase 9 §14.2 misurava il caso duro a **44,574 Mbit/s**; fase 10
   §6.3 lo misurava a **4,478**.  ⇒ dieci volte, e finche' non si sapeva da dove
   veniva la differenza **nessuno dei due numeri si poteva usare**.

⛔⛔ E LA PRIMA COSA DA DIRE E' CHE NON ERANO NEMMENO LA STESSA GRANDEZZA.  `[R]`
    fase 9 §14.2 contava i byte delle righe `SPEDITO` (**carico utile del video
    e basta**); la colonna «filo `lo`» della stessa tabella dice **48,42**, ed e'
    quella confrontabile col metro di oggi.  ⚠ Il che PEGGIORA la discordanza:
    48,42 contro 4,478 fa **undici** volte, non dieci.

| braccio | scena | lettore | cure | ⭐ MEDIA sul filo | carico utile | fot / 30 s | byte/fot |
|---|---|---|---|---|---|---|---|
| **A1** | film-grana | firefox | spente | 2,427 | ⛔ 0,000 | ⛔ **0** | — |
| **A2** | film-grana | mpv | spente | **51,506** | **46,931** | 674 | 263 427 |
| **A3** | film-grana | mpv | ACCESE | **49,627** | 47,209 | 670 | 266 132 |
| **A4** | duro | mpv | ACCESE | **9,647** | 8,990 | 908 | 37 420 |

⭐⭐⭐ 1 · **IL NUMERO DI FASE 9 E' VERO**, ed e' il primo dei tre esiti che
      l'incarico dichiarava possibili.  A2 contro §14.2, grandezza per
      grandezza: carico utile **46,931 contro 44,574 (1,05x)** · filo **51,506
      contro 48,42 (1,06x)** · byte per fotogramma **263 427 contro 239 129
      (1,10x)**.  ⇒ Un altro giorno, un altro banco, un altro metro, un altro
      lettore: **il 6 %**.  ⛔ Non c'e' niente da correggere in `CODER.md`
      §1-bis ne' in `DECISIONI.md`.

⭐⭐⭐ 2 · **NON SONO LE CURE.**  A2 → A3 (stessa scena, cure spente → accese)
      fa **0,96x**: le cinque cure della fase 9 tolgono il **4 %** al caso duro,
      non il 90 %.

⭐⭐⭐ 3 · **E' LA SCENA, E LO E' PER CINQUE VOLTE SU DIECI.**  A3 → A4 (stesse
      cure, `film-grana.webm` → `duro.mp4`) fa **0,19x**.  ⇒ `duro.mp4` (H.264
      19,4 Mbit/s, movimento vero) si comprime **cinque volte meglio** della
      grana pura (VP8 58,2 Mbit/s, rumore che nessun codificatore riduce).
      ⛔ Le due «scene dure» **non erano la stessa sollecitazione**, ed e'
      esattamente quel che §6.3 sospettava.

⚠⚠ 4 · **E IL RESTO E' DI §6.3 STESSA, che si misura piu' leggera di quanto sia.**
     A4 (`duro`, cure accese) da' **9,647 Mbit/s e 37 420 byte/fot**; §6.3 dava
     **4,478 e 16 884** sulla stessa scena con lo stesso prodotto.  ⭐ E i 37 420
     ritrovano i **37 081** che `09-b82-mostra.sh` aveva misurato il 24 agosto,
     cioe' **il numero di §6.3 e' quello anomalo**, non questo.
     ⇒ La spartizione completa dei dieci-undici volte: **5,1x la scena · 2,2x
       la misura di §6.3 · 1,04x le cure**, e 5,1 x 2,2 x 1,04 = **11,7**.

✅ 5 · **E IL LETTORE NON SI E' POTUTO RIFARE**, `[?]` dichiarato.  Fase 9
     mostrava le sue scene con **firefox-esr**; A1 lo rimette in piedi riga per
     riga e da' **ZERO fotogrammi in 30 s** — perche' Firefox su questa macchina
     e' rotto **per tutti, dentro e fuori REMOTIX** (fase 9 §20.1-ter, ✅ e non
     e' nostro).  ⭐ Il rapporto di A2 col 44,6 e' quindi marcato `[?]`
     CONDIZIONATO, mai `[M]`: la condizione e' che il filmato e' 2560x1080 come
     la tela, quindi `object-fit: fill` e `mpv --fullscreen` mostrano gli stessi
     pixel senza scalare — **un argomento, non una misura**.
     ⚠ E A1 vale come controllo positivo suo malgrado: **2,427 Mbit/s**, cioe'
       i **2,427** che fase 9 §14.2 dava alla riga «ferma», ritrovati alla terza
       cifra su un desktop che non dipingeva.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ IL CASO PEGGIORE VERO — `[M]` 24 agosto 2026, otto scene, cure ACCESE
      (il prodotto di oggi), e **nessuna media fra scene diverse**
═══════════════════════════════════════════════════════════════════════════════

| scena | entropia? | ⭐ MEDIA sul filo | picco | carico utile | fot / 30 s | byte/fot |
|---|---|---|---|---|---|---|
| **rumore** (`/dev/urandom` come yuv420p) | ⭐ sì | ⛔ **225,044** | **315,270** | 218,537 | 529 | **1 555 098** |
| **grana** (la scena di fase 9) | ⭐ sì | **49,619** | 65,017 | 47,206 | 671 | 265 957 |
| **mandel** (frattale, dettaglio fine) | ⭐ sì | **18,850** | 24,249 | 17,771 | 905 | 74 340 |
| **vita** (Conway, dettaglio binario) | ⭐ sì | **12,529** | 29,698 | 11,729 | 905 | 49 068 |
| **duro** (il «duro» della fase 10) | ⭐ sì | **9,941** | 47,522 | 9,271 | 908 | 38 609 |
| desktop vero | non dichiarata | 0,530 | 0,864 | 0,333 | 668 | 1 873 |
| ⛔ bandiera (tinte piatte) | ⛔ **SMASCHERATA** | 0,476 | 0,528 | 0,077 | 1 161 | **250** |
| ⛔ testo che scorre | ⛔ **SMASCHERATA** | 0,370 | 0,378 | 0,021 | 907 | **87** |

⭐⭐ E LA SORPRESA E' LA PENULTIMA RIGA: **il testo fitto che scorre costa 87
    byte per fotogramma**, cioe' **ventidue volte MENO** di un desktop fermo con
    la sua icona che lampeggia (1 873).  ⛔ Era stata scelta come scena dura —
    «il caso che l'utente fa davvero» — e i vettori di movimento di H.264 se la
    mangiano: uno scorrimento uniforme e' la cosa piu' facile che esista per un
    codificatore.  ⇒ G6 l'ha smascherata **sul campo**, non solo in
    `--certifica`, ed e' la prova che la guardia serve.

⭐⭐⭐ LA RIGA CHE CHIUDE, e il metro e' il ferro:
  · **il caso peggiore per sessione: 225,0 Mbit/s** (picco 315,3);
  · **×10 sessioni: 2 250 Mbit/s** di media, 3 153 se andassero in picco insieme;
  · contro il filo `[M]` misurato (UDP nudo su `lo`, 11 900 Mbit/s) ⇒ **il 19 %**:
    ⭐ **il filo non e' il vincolo nemmeno cosi'**, e la conclusione del primo
    giro regge — ma con un margine di 5x, non di 200x;
  · ⛔⛔ contro il TETTO DEL PRODOTTO (`--tetto-banda-mbit`, pavimento 20):
    **il caso peggiore ne chiede il 1 125 % DA SOLO**, e il tetto e' **per
    figlio** — `[R]` `tetto_pavimento_mbit` e' una statica di `codificatore.c`,
    che vive nel FIGLIO (`figlio.c:5999`), e in tutto `src/` non esiste nessun
    contatore aggregato.  ⇒ **dieci figli lo pagano dieci volte: 200 Mbit/s.**

⚠ `[?]` I BUCHI DICHIARATI DI QUESTA CAMPAGNA
  · **il lettore paga sulla stessa GPU**: `rumore.mp4` e' un H.264 da 500
    Mbit/s e mpv lo decodifica con la `renderD128`, la stessa che codifica il
    nostro flusso.  ⇒ i 17,6 fot/s di `rumore` (contro i 30 delle altre) sono
    in parte contesa col decodificatore, e NON e' stato separato;
  · **e' il caso peggiore SINTETICO**: fase 9 §16.1 misurava la grana pura sul
    percorso vero col browser dell'utente a **21,5-23,1 Mbit/s**, cioe' meta'
    del banco.  ⇒ questi numeri sono un **limite superiore**, non una previsione;
  · **`enp7s0` non e' stata sfiorata**: tutto su `lo`, MTU 65536.

Uso (dal portatile):
    python3 banchi/10-b90-filo.py --certifica     ⭐ QUI, senza macchina
    python3 banchi/10-b90-filo.py terreno
    python3 banchi/10-b90-filo.py tara     [--secondi 8]
    python3 banchi/10-b90-filo.py scene    [--secondi 30]
    python3 banchi/10-b90-filo.py tetto    [--secondi 5]
    python3 banchi/10-b90-filo.py contesa  [--quante 3] [--stretta 60]
    python3 banchi/10-b90-filo.py fase9    [--secondi 30]   ⭐ la riconciliazione
    python3 banchi/10-b90-filo.py entropia [--secondi 30] [--scene a,b,c]
    python3 banchi/10-b90-filo.py chiudi           ⛔ e si VERIFICA
  ⚠ e `--attesa N` per quanto si aspetta il lucchetto della GPU (5400 di suo:
    il 24 agosto 2026 la coda era di nove agenti e non bastava).
"""
import argparse
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "8020"))
UTENTE = os.environ.get("UTENTE", "provadec2")
UID_B = int(os.environ.get("UID_B", "1101"))
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "dec2-filo-2026")
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
ALBERO = os.environ.get("ALBERO", "/media/REMOTIX/src/10a4-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10a4")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10a4-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10a4")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
# ⛔⭐ IL NOME DELL'AGENTE VIENE DALL'AMBIENTE — 24 agosto 2026, secondo giro.
#     Era `"10-a4"` fisso, e con un nome fisso il lucchetto della GPU dice
#     «ce l'ha 10-a4» a chiunque lo prenda: il secondo agente che riusa questo
#     banco toglierebbe **il lucchetto di un altro** credendo di togliere il
#     proprio, e i due giri si falserebbero in silenzio (`LEZIONI.md` §1.26).
NOME = os.environ.get("CHI", "10-a4")

QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
                                "ab31ac36-86ed-4f24-8d71-e41da4a7da6e/scratchpad/b90")

DEV = "lo"
VIETATA = "enp7s0"          # ⛔ ci passano l'ssh e la sessione dell'utente: mai
# ⛔ la MIA tabella nft, e nessun'altra si tocca.  ⚠ Dall'ambiente per la
#    stessa ragione di `NOME`: due agenti che riusano questo banco con la
#    stessa tabella si azzererebbero i contatori a vicenda — e `metro_azzera()`
#    non ha modo di accorgersene, darebbe **numeri bassi e plausibili**.
TABELLA = os.environ.get("TABELLA", "remotix10a4")
# ⛔ Le porte che NON sono mie: si contano prima e dopo, e non si toccano mai.
VICINE = [p for p in ("7700", "7730", "7900", "7910", "7920", "8000", "8010",
                      "8020", "8030", "8040", "8100", "8130", "8170")
          if p != str(PORTA)]

# ⭐ Le scene: il file, perche' c'e', CON CHE LETTORE si mostra, e se chi la
#    sceglie la DICHIARA ad alta entropia (⇒ G6 la giudica).
#
# ⛔⛔ IL LETTORE E' UN CAMPO DEL PROFILO, non un dettaglio d'attuazione, e il
#     24 agosto 2026 e' stato misurato perche': fase 9 mostrava i suoi filmati
#     con **firefox-esr** (una pagina `object-fit: fill`, cioe' il video
#     STIRATO su tutta la tela), la fase 10 li mostra con **mpv --fullscreen**.
#     Sono due immagini diverse sullo stesso file, e chi le confronta senza
#     dirlo confronta due scene.
SCENE = {
    "ferma":   {"file": None, "lettore": None, "alta": False,
                "contenuto": "nessuna",
                "perche": "il costo che dieci sessioni pagano anche quando "
                          "nessuno lavora"},
    "desktop": {"file": "/media/REMOTIX/src/08-D/scena-utente.webm",
                "lettore": "mpv", "alta": False, "contenuto": "scena-utente",
                "perche": "la scena in cui vive l'utente: cambia a strappi"},
    "duro":    {"file": "/media/REMOTIX/tmp/09-scena/duro.mp4",
                "lettore": "mpv", "alta": True, "contenuto": "duro",
                "perche": "movimento continuo a pieno ritmo — il piu' duro "
                          "che la fase 10 avesse"},
    # ⛔⭐ LA SCENA DI FASE 9, e c'e' per una ragione sola: **il confronto**.
    #     `[M]` fase 9 §14.2 misura 44,574 Mbit/s sul «film con la grana», che
    #     e' `film-grana.webm`.  ⚠ `duro.mp4` NON e' quel file: il metro di
    #     `09-b82-mostra.sh` li da' a 18 600 e 37 081 byte per fotogramma, cioe'
    #     `duro` e' il DOPPIO.  ⇒ misurare `duro` e confrontarlo con i 44,6
    #     sarebbe confrontare due scene diverse — la forma piu' facile di
    #     numero plausibile e falso.
    "grana":   {"file": "/media/REMOTIX/tmp/09c/film-grana.webm",
                "lettore": "mpv", "alta": True, "contenuto": "film-grana",
                "perche": "⭐ LA SCENA DI FASE 9 §14.2 col lettore di OGGI"},
    # ⭐⭐ E LA STESSA SCENA COL LETTORE DI FASE 9 — e' la ricostruzione, e
    #     serve a rispondere alla domanda «da dove viene il 44,6».
    "grana-ff": {"file": "/media/REMOTIX/tmp/09c/film-grana.webm",
                 "lettore": "firefox", "alta": True, "contenuto": "film-grana",
                 "perche": "⭐⭐ LA SCENA DI FASE 9 §14.2 ricostruita RIGA PER "
                           "RIGA: firefox-esr, object-fit fill, 2560x1080"},
    # ═══ ⭐⭐⭐ LE QUATTRO FORME DI ENTROPIA — incarico 10-b7 ═══════════════
    # ⛔ Il primo giro dichiarava: «nessuna delle mie scene ha entropia vera».
    #    ⇒ queste quattro esistono per chiudere quel `[?]`, e sono QUATTRO
    #    perche' fase 9 §14.2 ha gia' dimostrato che il rapporto fra scene NON
    #    e' una costante (0,36x sul retinato, 0,76x sulla grana, 1,7x IN SU sul
    #    desktop vero): una media di scene diverse non descrive niente.
    "rumore":  {"file": "/media/REMOTIX/tmp/10b7/scene/rumore.mp4",
                "lettore": "mpv", "alta": True, "contenuto": "rumore",
                "perche": "⭐ IL SOFFITTO: /dev/urandom letto come yuv420p — "
                          "non esiste niente di piu' duro su uno schermo"},
    "testo":   {"file": "/media/REMOTIX/tmp/10b7/scene/testo.mp4",
                "lettore": "mpv", "alta": True, "contenuto": "testo",
                "perche": "testo fitto che scorre (sorgente vero, monospazio "
                          "16, 200 px/s) — il caso che l'utente fa DAVVERO"},
    "mandel":  {"file": "/media/REMOTIX/tmp/10b7/scene/mandel.mp4",
                "lettore": "mpv", "alta": True, "contenuto": "mandel",
                "perche": "dettaglio fine e continuo che si muove sempre — il "
                          "sostituto onesto della fotografia, che qui non c'e'"},
    "vita":    {"file": "/media/REMOTIX/tmp/10b7/scene/vita.mp4",
                "lettore": "mpv", "alta": True, "contenuto": "vita",
                "perche": "dettaglio binario fittissimo senza direzione di "
                          "moto: i vettori di movimento di H.264 non aiutano"},
    # ⛔⭐ IL CONTROLLO NEGATIVO, e sta qui apposta: **dichiarata ad alta
    #     entropia e non lo e'**.  `[M]` `09-b82-mostra.sh`, 24 agosto: 321
    #     fotogrammi da **268 byte**.  ⇒ una finestra viva, a schermo intero,
    #     che si muove a 40 fot/s — e costa quanto un desktop fermo.
    #     Serve a far vedere G6 mordere sul campo, non solo in `--certifica`.
    "bandiera": {"file": "/media/REMOTIX/tmp/02-cattura/bandiera-1920x1080.mp4",
                 "lettore": "mpv", "alta": True, "contenuto": "bandiera",
                 "perche": "⛔ CONTROLLO NEGATIVO: tinte piatte spacciate per "
                           "caso duro — G6 deve smascherarla"},
}

# ── le tolleranze, DICHIARATE prima di misurare ────────────────────────────
TOLL_SOMMA = 0.02      # G4: somma delle sessioni contro il totale della mia porta
TOLL_METRO = 0.02      # `nft tutto` contro `lo/tx_bytes`
FOND_MIN_FOT = 5       # G3: sotto tanti fotogrammi la scena «non si muove»


# ═══════════════════════════════════════════════════════════════════════════
# GLI ANELLI VERSO LA MACCHINA
# ═══════════════════════════════════════════════════════════════════════════
def rem(comando, tetto=600):
    """⛔ Niente redirezione ATTORNO a ssh: la richiesta di sudo va sullo stderr."""
    try:
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                           capture_output=True, timeout=tetto)
    except subprocess.TimeoutExpired:
        return (124, "", "⛔ ssh scaduto dopo %d s" % tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=600):
    """⛔ Un solo `sudo`, e la catena intera dentro `bash -c`: `sudo -S` copre
       solo il PRIMO anello (cura n. 1 del 23 agosto, `09-b70` in testa)."""
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def dentro(comando, tetto=900):
    """Dentro il contenitore, da root: li' c'e' `aioquic` e c'e' `gcc`."""
    return root("bash /media/REMOTIX/enter.sh --root '%s'" % comando, tetto)


ok = lambda *a: print("   \033[1;32mOK\033[0m  %s" % " ".join(str(x) for x in a), flush=True)
ko = lambda *a: print("   \033[1;31mNO\033[0m  %s" % " ".join(str(x) for x in a), flush=True)
avv = lambda *a: print("   \033[1;33m⚠\033[0m   %s" % " ".join(str(x) for x in a), flush=True)
inf = lambda *a: print("   --  %s" % " ".join(str(x) for x in a), flush=True)


def log(t):
    print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL LUCCHETTO DELLA GPU — ogni giro da cui esce un numero
# ═══════════════════════════════════════════════════════════════════════════
def _carica(nome, file_):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Lucchetto(object):
    """⛔ Due lucchetti, e sono DUE POSTI DIVERSI: la GPU e il `netem`.  Chi
       mette una disciplina sull'interfaccia deve prendere anche il secondo,
       perche' la radice di un'interfaccia e' UNA e il secondo che la mette
       cancella quella del primo **in silenzio**."""

    def __init__(self, gpu=True, netem=False, secondi=1800, attesa=3600):
        self.gpu, self.netem = gpu, netem
        self.secondi, self.attesa = secondi, attesa
        self.presi = []

    def __enter__(self):
        for posto, quale in (("/media/REMOTIX/tmp/.lucchetto-gpu.d", self.gpu),
                             ("/media/REMOTIX/tmp/.lucchetto-netem.d", self.netem)):
            if not quale:
                continue
            os.environ["LUCCHETTO"] = posto
            luc = _carica("luc_" + posto.rsplit("/", 1)[-1], "09-lucchetto.py")
            luc.prendi(NOME, secondi=self.secondi, attesa=self.attesa)
            self.presi.append((posto, luc))
        return self

    def __exit__(self, *e):
        for posto, luc in reversed(self.presi):
            os.environ["LUCCHETTO"] = posto
            luc.molla(NOME)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# IL METRO — `nft`, e si INSTALLA, si AZZERA e si LEGGE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Le tre regole in fila contano TUTTE E TRE lo stesso pacchetto: `counter` e
#    `update` non sono verdetti, non fermano niente.  ⇒ `tutto` comprende anche
#    `mio_giu` e `mio_su`, e «altrui» e' la sottrazione.
#
# ⚠ E IL COSTO CHE FA PAGARE AI VICINI SI DICHIARA: la catena sta su un gancio
#    `postrouting`, quindi ogni pacchetto IP che esce da `lo` — anche quelli
#    degli altri agenti — attraversa quattro regole in piu'.  Sono decine di
#    nanosecondi a pacchetto: trascurabile a qualche migliaio di pacchetti al
#    secondo, e la tabella si toglie con `chiudi`.  ⛔ Ma si SCRIVE, invece di
#    sperare che nessuno se ne accorga.
#
# ⛔ La tabella e' MIA (`remotix10a4`) e non si tocca nient'altro: `nft flush
#    ruleset` metterebbe fuori uso ogni altro agente, e non e' scritto in
#    nessuna riga di questo file.
NFT = "/usr/sbin/nft"


RICETTA = """\
table inet %(T)s {
	set giu { type inet_service; size 1024; counter; flags dynamic; timeout 4h; }
	set su  { type inet_service; size 1024; counter; flags dynamic; timeout 4h; }
	counter mio_giu {}
	counter mio_su {}
	counter tutto {}
	counter tara {}
	counter irraggiungibili {}
	chain uscita {
		type filter hook postrouting priority 0; policy accept;
		oif "%(D)s" udp sport %(P)d counter name "mio_giu" update @giu { udp dport }
		oif "%(D)s" udp dport %(P)d counter name "mio_su"  update @su  { udp sport }
		oif "%(D)s" udp dport %(Q)d counter name "tara"    update @su  { udp sport }
		oif "%(D)s" meta l4proto icmp counter name "irraggiungibili"
		oif "%(D)s" counter name "tutto"
	}
}
"""
# ⭐⭐ IL CONTATORE `icmp` NON E' UN DETTAGLIO, e' IL PAREGGIO DEI CONTI.
#     Il getto della taratura va verso una porta che non ascolta nessuno, e il
#     nucleo risponde con un ICMP «porta irraggiungibile» per ogni datagramma.
#     `[M]` 24 agosto 2026: sono **576 byte per datagramma**, cioe' quasi meta'
#     del traffico che l'interfaccia vede durante la taratura.
#     ⛔ Senza questa riga quei byte finirebbero in «altrui», e il banco
#        avrebbe scritto *«i vicini hanno fatto passare 1,5 MB»* su una
#        macchina in cui i vicini non avevano fatto niente — un numero
#        plausibile e falso, che e' la peggiore delle due specie.
#     ⇒ Con questa riga i conti si chiudono ESATTAMENTE:
#           tutto = mio_giu + mio_su + tara + icmp + altrui


def metro_installa():
    """⛔ La ricetta si spedisce come FILE e si carica con `nft -f`, non come
       una fila di comandi dentro `bash -c`: le graffe di `nft` sono anche le
       graffe di bash, e `bash` le prende per un gruppo di comandi.  `[M]` 24
       agosto 2026: `syntax error near unexpected token '}'`, cioe' un metro
       che non si installa — e sarebbe stato uno zero con la faccia di uno zero."""
    import base64
    testo = RICETTA % {"T": TABELLA, "D": DEV, "P": PORTA, "Q": PORTA + 1000}
    b64 = base64.b64encode(testo.encode()).decode()
    rc, out, err = root("bash -c \"%s delete table inet %s 2>/dev/null; "
                        "echo %s | base64 -d > %s/nft.ricetta; "
                        "%s -f %s/nft.ricetta\""
                        % (NFT, TABELLA, b64, LAV, NFT, LAV))
    if rc != 0:
        return False, (out + err)[-400:]
    rc, out, _ = root("%s list table inet %s 2>&1 | grep -c counter || true"
                      % (NFT, TABELLA))
    return (out.strip() not in ("0", "")), "installato (%s righe con «counter»)" % out.strip()


def metro_via():
    root("%s delete table inet %s 2>/dev/null; true" % (NFT, TABELLA))
    rc, out, _ = root("%s list tables 2>/dev/null | grep -c %s || true" % (NFT, TABELLA))
    return out.strip() in ("0", "")


def metro_azzera():
    root("bash -c \"%s reset counters table inet %s >/dev/null 2>&1; "
         "%s reset set inet %s giu >/dev/null 2>&1; "
         "%s reset set inet %s su >/dev/null 2>&1; true\""
         % (NFT, TABELLA, NFT, TABELLA, NFT, TABELLA))


R_CONT = re.compile(r"counter (\w+) \{[^}]*?packets (\d+) bytes (\d+)", re.S)
R_ELEM = re.compile(r"(\d+) counter packets (\d+) bytes (\d+)")
R_SPED = re.compile(r"SPEDITO: (?:CHIAVE|delta) [^\n]*?(\d+) byte")


def leggi(registro=None, riga0=0):
    """⭐ UNA lettura sola di TUTTI i contatori, il piu' vicino possibile allo
       stesso istante: due ssh separati sono due istanti diversi, e a 40 Mbit/s
       mezzo secondo di sfalso e' 2,5 MB di errore.

       ⛔ Torna `None` se non ha potuto leggere.  «Non ho misurato» non e' zero."""
    pezzi = [
        "echo @@T $(date +%s.%N)",
        "echo @@LO $(cat /sys/class/net/" + DEV + "/statistics/tx_bytes) "
        "$(cat /sys/class/net/" + DEV + "/statistics/tx_packets)",
        "echo @@NFT; " + NFT + " list table inet " + TABELLA + " 2>/dev/null",
    ]
    if registro:
        pezzi.append("echo @@REG; tail -n +%d %s 2>/dev/null | grep -c 'SPEDITO' || true"
                     % (riga0 + 1, registro))
        pezzi.append("echo @@BYTE; tail -n +%d %s 2>/dev/null | grep 'SPEDITO' | "
                     "grep -oE '[0-9]+ byte di dati' | grep -oE '^[0-9]+' | "
                     # ⛔⭐ IL `\\$1` DELL'`awk` VA PROTETTO DUE VOLTE, e il 24
                     #     agosto 2026 e' costato mezz'ora.  La riga attraversa
                     #     TRE shell (quella di ssh, `bash -c` di sudo, e awk):
                     #     dentro `bash -c "..."` la prima espande `$1` a
                     #     **niente**, awk diventa `{s+=; n++}`, va in errore di
                     #     sintassi e non stampa NULLA.  ⚠ E «non stampa nulla»
                     #     arrivava qui come `byte_utili = None`, cioe' un buco
                     #     silenzioso nel conto dei byte per fotogramma — la
                     #     grandezza che smaschera le scene ferme (G3).
                     "awk '{s+=\\$1; n++} END{print s+0, n+0}'"
                     % (riga0 + 1, registro))
        pezzi.append("echo @@RIGHE; wc -l < %s 2>/dev/null || echo 0" % registro)
    rc, out, err = root("bash -c \"%s\"" % "; ".join(pezzi).replace('"', '\\"'), 120)
    if rc != 0 or "@@LO" not in out:
        return None
    L = {"t": None, "lo_tx": None, "lo_pkt": None, "cont": {},
         "giu": {}, "su": {}, "spediti": None, "byte_utili": None, "righe": None}
    corpo = out
    try:
        L["t"] = float(re.search(r"@@T ([\d.]+)", corpo).group(1))
        m = re.search(r"@@LO (\d+) (\d+)", corpo)
        L["lo_tx"], L["lo_pkt"] = int(m.group(1)), int(m.group(2))
    except (AttributeError, ValueError):
        return None
    nft = corpo.split("@@NFT", 1)[1].split("@@REG", 1)[0] if "@@NFT" in corpo else ""
    for nome, p, b in R_CONT.findall(nft):
        L["cont"][nome] = (int(b), int(p))
    for quale in ("giu", "su"):
        m = re.search(r"set %s \{(.*?)\n\t\}" % quale, nft, re.S)
        if m and "elements" in m.group(1):
            for porta, p, b in R_ELEM.findall(m.group(1)):
                L[quale][int(porta)] = (int(b), int(p))
    if registro and "@@REG" in corpo:
        try:
            L["spediti"] = int(corpo.split("@@REG", 1)[1].split("@@BYTE", 1)[0].strip()
                               .split()[0])
            bb = corpo.split("@@BYTE", 1)[1].split("@@RIGHE", 1)[0].split()
            L["byte_utili"] = int(bb[0]) if bb else None
            L["righe"] = int(corpo.split("@@RIGHE", 1)[1].strip().split()[0])
        except (IndexError, ValueError):
            pass
    if not L["cont"]:
        return None
    return L


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LE QUATTRO GUARDIE — funzioni PURE, cosi' `--certifica` puo' innestare
#     il guasto senza la macchina.  ⭐ Ognuna torna `(valore, motivo)`, e
#     `valore is None` vuol dire «mi rifiuto», non «zero».
# ═══════════════════════════════════════════════════════════════════════════
def g2_monotono(prima, dopo):
    """G2 · il contatore che si azzera o va indietro."""
    if prima is None or dopo is None:
        return (None, "⛔ una delle due letture non c'e': non ho misurato")
    if dopo["t"] is None or prima["t"] is None or dopo["t"] <= prima["t"]:
        return (None, "⛔ il tempo non e' andato avanti (%s → %s)"
                % (prima["t"], dopo["t"]))
    for campo in ("lo_tx", "lo_pkt"):
        if prima[campo] is None or dopo[campo] is None:
            return (None, "⛔ %s non letto" % campo)
        if dopo[campo] < prima[campo]:
            return (None, "⛔ «%s» E' ANDATO INDIETRO (%d → %d): il contatore si e' "
                          "azzerato sotto i piedi, NON produco un numero"
                    % (campo, prima[campo], dopo[campo]))
    for nome in set(prima["cont"]) | set(dopo["cont"]):
        a = prima["cont"].get(nome, (0, 0))[0]
        b = dopo["cont"].get(nome)
        if b is None:
            return (None, "⛔ il contatore «%s» e' SPARITO fra le due letture" % nome)
        if b[0] < a:
            return (None, "⛔ il contatore «%s» E' ANDATO INDIETRO (%d → %d): "
                          "qualcuno l'ha azzerato, NON produco un numero"
                    % (nome, a, b[0]))
    return (True, "i contatori sono andati avanti tutti")


def varco(prima, dopo):
    """La differenza fra due letture, DOPO G2.  Torna `(dizionario, motivo)`."""
    buono, perche = g2_monotono(prima, dopo)
    if buono is not True:
        return (None, perche)
    d = {"secondi": dopo["t"] - prima["t"],
         "lo_tx": dopo["lo_tx"] - prima["lo_tx"],
         "lo_pkt": dopo["lo_pkt"] - prima["lo_pkt"]}
    for nome in dopo["cont"]:
        b, p = dopo["cont"][nome]
        a, q = prima["cont"].get(nome, (0, 0))
        d[nome] = b - a
        d[nome + "_pkt"] = p - q
    for quale in ("giu", "su"):
        s = {}
        for porta, (b, p) in dopo[quale].items():
            a, q = prima[quale].get(porta, (0, 0))
            if b - a > 0:
                s[porta] = (b - a, p - q)
        d["ses_" + quale] = s
    for campo in ("spediti", "byte_utili"):
        if dopo.get(campo) is not None and prima.get(campo) is not None:
            d[campo] = dopo[campo] - prima[campo]
        else:
            d[campo] = None
    # ⭐ IL PAREGGIO DEI CONTI: quel che resta dopo aver tolto tutto quel che so
    #    riconoscere e' il traffico DEGLI ALTRI AGENTI su `lo`.  Si stampa, non
    #    si spera che sia zero.
    d["altrui"] = (d.get("tutto", 0) - d.get("mio_giu", 0) - d.get("mio_su", 0)
                   - d.get("tara", 0) - d.get("irraggiungibili", 0))
    return (d, "ok")


def g1_flusso_partito(d, minimo_byte=10000):
    """G1 · il contatore letto PRIMA che il flusso parta ⇒ zero byte.
       ⛔ Il banco si RIFIUTA, non dichiara «0 Mbit/s»."""
    if d is None:
        return (None, "⛔ non c'e' nessun varco da guardare")
    mio = d.get("mio_giu", 0) + d.get("mio_su", 0)
    if mio <= 0:
        return (None, "⛔ ZERO byte sulla mia porta in %.2f s: il flusso NON E' "
                      "PARTITO (o l'ho letto prima).  «0 Mbit/s» sarebbe una "
                      "bugia con la faccia di una misura" % d["secondi"])
    if mio < minimo_byte:
        return (None, "⛔ solo %d byte sulla mia porta in %.2f s (soglia %d): "
                      "troppo poco per chiamarlo un flusso, mi rifiuto"
                % (mio, d["secondi"], minimo_byte))
    return (True, "%d byte sulla mia porta in %.2f s" % (mio, d["secondi"]))


def g3_scena_si_muove(d, minimo_fot=FOND_MIN_FOT):
    """G3 · la scena che non si muove, smascherata dai byte per fotogramma."""
    if d is None:
        return (None, "⛔ non c'e' nessun varco")
    fot = d.get("spediti")
    if fot is None:
        return (None, "⛔ il registro del server non e' stato letto: non so "
                      "quanta sollecitazione e' arrivata (LEZIONI §1.30)")
    bpf = (d["byte_utili"] / fot) if (fot and d.get("byte_utili")) else 0
    if fot < minimo_fot:
        return (False, "⛔ SCENA FERMA: %d fotogrammi in %.1f s (sotto %d) — "
                       "qualunque Mbit/s esca di qui e' il costo del NIENTE, "
                       "non della scena" % (fot, d["secondi"], minimo_fot))
    return (True, "%d fotogrammi in %.1f s, %.0f byte/fotogramma"
            % (fot, d["secondi"], bpf))


def g4_somma_torna(d, toll=TOLL_SOMMA):
    """G4 · la somma per sessione contro il totale della mia porta."""
    if d is None:
        return (None, "⛔ non c'e' nessun varco")
    tot = d.get("mio_giu", 0) + d.get("mio_su", 0)
    somma = sum(b for b, _ in d.get("ses_giu", {}).values()) + \
            sum(b for b, _ in d.get("ses_su", {}).values())
    if tot <= 0:
        return (None, "⛔ il totale della mia porta e' zero: non c'e' niente da "
                      "far tornare")
    scarto = (somma - tot) / float(tot)
    riga = ("somma delle %d sessioni %d byte, totale della porta %d byte, "
            "scarto %+.3f %%" % (len(d.get("ses_giu", {})) + len(d.get("ses_su", {})),
                                 somma, tot, scarto * 100))
    if abs(scarto) > toll:
        return (False, "⛔ LA SOMMA NON TORNA — %s (tolleranza %.1f %%).  ⇒ o un "
                       "insieme dinamico ha perso un elemento (troppe porte, o "
                       "una scadenza), o una lettura e' sbagliata" % (riga, toll * 100))
    return (True, riga)


def g5_metro_su_se_stesso(d, toll=TOLL_METRO):
    """⭐ `nft tutto` contro `lo/tx_bytes`: due contatori indipendenti sugli
       stessi pacchetti.  Se divergono, il metro non e' un metro."""
    if d is None:
        return (None, "⛔ non c'e' nessun varco")
    a, b = d.get("tutto", 0), d.get("lo_tx", 0)
    if b <= 0:
        return (None, "⛔ l'interfaccia non ha visto passare niente")
    scarto = (a - b) / float(b)
    riga = "nft «tutto» %d byte, %s/tx_bytes %d byte, scarto %+.3f %%" % (
        a, DEV, b, scarto * 100)
    if abs(scarto) > toll:
        return (False, "⛔ I DUE CONTATORI NON DICONO LA STESSA COSA — %s" % riga)
    return (True, riga)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LE TRE GUARDIE NUOVE — 24 agosto 2026, incarico 10-b7
#
# Nascono da una discordanza dichiarata e non lisciata: la fase 9 §14.2 misura
# il «caso duro» a **44,574 Mbit/s** e la fase 10 §6.3 lo misura a **4,478**.
# ⛔ Dieci volte.  E la lezione §1.28 dice che due banchi che non concordano
#    possono avere ragione tutt'e due — stanno misurando **due grandezze
#    diverse**.  ⇒ Queste tre guardie servono a non far succedere piu' che un
#    numero attraversi una fase con addosso il nome di un altro.
# ═══════════════════════════════════════════════════════════════════════════

# ⛔ LA SOGLIA DELL'ENTROPIA, DICHIARATA PRIMA DI MISURARE, e con la scala su
#    cui e' stata scelta accanto — `[M]` fase 9 §14.2 e `09-b82-mostra.sh`,
#    tutti a 2560x1080, H.264, QP 26:
#
#      tinte piatte (bandiera a schermo intero) ........      268 byte/fot
#      desktop vero (`scena-utente.webm`) .............. 1 924-2 099
#      gradiente retinato (`barra`) ....................    23 695
#      film con la GRANA (il caso duro di fase 9) ......   239 129
#
# ⇒ Chi dichiara «alta entropia» deve battere **il gradiente retinato**: sotto
#   quella riga la scena si comprime come un gradiente, e chiamarla «caso
#   peggiore» e' un numero plausibile e falso.  ⭐ E la soglia si scala coi
#   PIXEL, o su una tela piccola respingerebbe scene durissime.
SOGLIA_ENTROPIA_BPF = 20000.0        # byte/fotogramma a 2560x1080
PIXEL_RIFERIMENTO = 2560 * 1080


def g6_entropia_vera(d, dichiarata_alta, tela="2560x1080",
                     soglia_bpf=SOGLIA_ENTROPIA_BPF):
    """G6 · ⛔ «ALTA ENTROPIA» DICHIARATA E SMENTITA DAI BYTE PER FOTOGRAMMA.

    Il primo giro della fase 10 ha dichiarato onestamente *«nessuna delle mie
    scene ha entropia vera — le bande di colore si comprimono benissimo»*.
    ⛔ Ma la dichiarazione era **a parole**: nessun predicato la controllava, e
       una scena battezzata «dura» da chi la sceglie entra nel budget come
       caso peggiore anche quando costa quanto un gradiente.
    ⇒ Qui la dichiarazione ha un giudice, e il giudice sono **i byte per
      fotogramma**, non l'aggettivo.

    ⚠ E NON e' G3 sotto un altro nome: G3 chiede *«la scena si muove?»* (il
      CONTO dei fotogrammi), G6 chiede *«la scena e' dura?»* (il PESO di
      ciascuno).  `[M]` 24 agosto, `09-b82-mostra.sh`: la bandiera a schermo
      intero fa **321 fotogrammi da 268 byte** — G3 verde, G6 rossa, e sono
      tutt'e due la verita'.

    Torna `(True|False|None, spiegazione)`."""
    if d is None:
        return (None, "⛔ non c'e' nessun varco da guardare")
    fot = d.get("spediti")
    if fot is None:
        return (None, "⛔ il registro del server non e' stato letto: non so "
                      "quanto pesa un fotogramma, e NON dico che pesa poco")
    if not fot:
        return (None, "⛔ zero fotogrammi: non ho misurato l'entropia, ho "
                      "misurato l'assenza di una scena (e' G3 che lo dice)")
    bu = d.get("byte_utili")
    if bu is None:
        return (None, "⛔ i byte utili non sono stati letti: mi rifiuto di "
                      "giudicare l'entropia sul filo, che porta anche l'audio")
    bpf = bu / float(fot)
    try:
        l, h = tela.split("x")
        scala = (int(l) * int(h)) / float(PIXEL_RIFERIMENTO)
    except (ValueError, ZeroDivisionError):
        return (None, "⛔ tela «%s» illeggibile: non so scalare la soglia" % tela)
    soglia = soglia_bpf * scala
    riga = ("%.0f byte/fotogramma su %d fotogrammi (soglia %.0f a %s, scalata "
            "sui pixel)" % (bpf, fot, soglia, tela))
    if not dichiarata_alta:
        return (True, "%s — la scena NON e' dichiarata ad alta entropia, non "
                      "la giudico" % riga)
    if bpf < soglia:
        return (False, "⛔ SCENA DICHIARATA «AD ALTA ENTROPIA» E SMASCHERATA: "
                       "%s ⇒ si comprime come un gradiente.  NON entra nel "
                       "budget come caso peggiore" % riga)
    return (True, "⭐ entropia confermata dai byte: %s" % riga)


# ⛔⛔ I CAMPI CHE FANNO DI DUE MISURE «LA STESSA COSA».  Cambiarne uno solo
#     cambia la grandezza: il confronto non e' piu' lecito, e il banco deve
#     RIFIUTARLO invece di produrre un numero che sembra una risposta.
CAMPI_PROFILO = ("scena", "tela", "codec", "lettore", "cure")


def g7_confronto_leale(a, b, campi=CAMPI_PROFILO):
    """G7 · ⛔⛔ DUE MISURE SI CONFRONTANO SOLO SE SONO DELLA STESSA COSA.

    `a` e `b` sono due **profili**: che scena, che tela, che codec, con che
    lettore, con le cure accese o spente.  ⇒ Se un campo differisce, il
    confronto e' fra due grandezze diverse e questa funzione torna `False`
    dicendo **quale** — e il chiamante non stampa il rapporto.

    ⛔⛔ E IL CAMPO `cure` HA UNA VOCE TUTTA SUA, perche' e' un divieto scritto
        (`CODER.md` §2-bis): un numero letto **con le cure accese** non si
        confronta con uno preso **a cure spente**.  Il banco che lo facesse
        attribuirebbe alla scena quel che ha fatto il regolatore del ritmo.
        ⚠ Qui non e' un consiglio: e' impossibile.  Non c'e' nessuna opzione
          per forzarlo, ed e' voluto.

    ⭐ E se un campo MANCA in uno dei due profili, torna `None`: «non so se
      sono la stessa cosa» non e' «sono la stessa cosa» — e' la forma di E8.

    Torna `(True|False|None, spiegazione)`."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return (None, "⛔ uno dei due profili non c'e': non ho niente da "
                      "confrontare, e non fingo di si'")
    manca = [c for c in campi if a.get(c) is None or b.get(c) is None]
    if manca:
        return (None, "⛔ NON SO SE SONO LA STESSA COSA: il campo/i %s non e' "
                      "dichiarato in uno dei due profili.  Un confronto su un "
                      "campo ignoto non e' un confronto" % ", ".join(manca))
    diversi = [(c, a[c], b[c]) for c in campi if a[c] != b[c]]
    if not diversi:
        return (True, "⭐ stessa scena, stessa tela, stesso codec, stesso "
                      "lettore, stesse cure: il confronto e' lecito")
    if any(c == "cure" for c, _, _ in diversi):
        x = [d for d in diversi if d[0] == "cure"][0]
        return (False, "⛔⛔ DIVIETO DI `CODER.md` §2-bis — cure «%s» contro "
                       "cure «%s»: un numero con le cure accese NON si "
                       "confronta con uno a cure spente.  Il rapporto che ne "
                       "uscirebbe attribuirebbe alla scena quel che ha fatto "
                       "una cura.%s" % (x[1], x[2],
                                        "" if len(diversi) == 1 else
                                        "  ⚠ E non e' l'unica differenza: %s"
                                        % ", ".join("%s «%s»≠«%s»" % d
                                                    for d in diversi if d[0] != "cure")))
    return (False, "⛔ RICOSTRUZIONE SBAGLIATA — %s.  ⇒ non e' la stessa "
                   "sollecitazione, e il confronto si RIFIUTA"
            % ", ".join("%s «%s» contro «%s»" % d for d in diversi))


def mbit(byte, secondi):
    """⛔ `None` se non si puo': non si divide per zero e non si inventa."""
    if byte is None or secondi is None or secondi <= 0:
        return None
    return byte * 8.0 / secondi / 1e6


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO
# ═══════════════════════════════════════════════════════════════════════════
def amb():
    return dict(os.environ,
                MACCHINA=MACCHINA, PAROLA_SUDO=PAROLA_SUDO, IND=IND,
                PORTA=str(PORTA), UTENTE=UTENTE, UID_B=str(UID_B),
                PAROLA_UTENTE=PAROLA_UTENTE, ALBERO=ALBERO, LAV=LAV,
                DENTRO_ALB=DENTRO_ALB, DENTRO_LAV=DENTRO_LAV, UNITA=UNITA)


def terreno(passo):
    """⛔ NON si riscrive `07-b64-terreno.sh`: gli si passa il MIO ambiente.
       ⚠ Solo il passo «porta» e' mio, perche' devo spedire attrezzi che quel
       copione non conosce (`10-b90-sessione.sh`, `09-b82-mostra.sh`, il getto
       in C).  Tutto il resto e' suo, riga per riga."""
    if passo == "porta":
        return terreno_porta()
    p = subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), passo],
                       env=amb())
    return p.returncode == 0


# ⛔ Il tar deve portare anche `banchi/rcp`: `src/costruisci.sh` confronta
#    `rcp.c`/`rcp.h`/`autenticazione.c` con la copia gemella (rilievo R12.3), e
#    senza quella cartella la costruzione FALLISCE.
DA_PORTARE = ["src", "banchi/rcp",
              "banchi/01-b3-cliente.py", "banchi/01-b8-sblocca.py",
              "banchi/01-b4-validatore.py",
              "banchi/07-b64-terreno.sh", "banchi/07-b64-scena.py",
              "banchi/07-b64-orecchio.py",
              "banchi/09-b82-mostra.sh", "banchi/09-b72-video.sh",
              "banchi/10-b90-sessione.sh", "banchi/10-b90-firefox.sh",
              "banchi/10-b90-getto.c"]


def terreno_porta():
    radice = os.path.dirname(QUI)
    log("1 · I sorgenti in %s" % ALBERO)
    # ⛔ Le due copie di rcp.c si controllano QUI, non a 200 km di distanza.
    for f in ("rcp.c", "rcp.h", "autenticazione.c"):
        a = os.path.join(radice, "src", f)
        b = os.path.join(radice, "banchi", "rcp", f)
        if subprocess.run(["cmp", "-s", a, b]).returncode != 0:
            ko("⛔ src/%s e banchi/rcp/%s DIVERGONO: la costruzione fallirebbe (R12.3)" % (f, f))
            return False
    ok("le due copie di rcp.c/rcp.h/autenticazione.c sono allineate")
    rc, out, _ = (0, subprocess.run(["git", "-C", radice, "rev-parse", "--short", "HEAD"],
                                    capture_output=True).stdout.decode().strip(), "")
    inf("HEAD = %s" % out)
    cmd = ("tar -C %s --exclude='*.o' --exclude='src/remotix' -czf - %s | "
           "ssh -o BatchMode=yes %s \"mkdir -p %s && tar -C %s -xzf -\""
           % (radice, " ".join(DA_PORTARE), MACCHINA, ALBERO, ALBERO))
    if subprocess.run(["bash", "-c", cmd]).returncode != 0:
        ko("⛔ i sorgenti non sono arrivati")
        return False
    ok("sorgenti in %s" % ALBERO)

    log("2 · Compilo dentro il contenitore")
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root "
                        "'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 "
                        "NGHTTP3=/srv/src/b2/nghttp3 bash %s/src/costruisci.sh 2>&1 | tail -20'"
                        % DENTRO_ALB, 1800)
    print(out[-1500:])
    if rc != 0:
        ko("⛔ la compilazione e' fallita: NON accendo niente")
        return False
    rc, out, _ = root("md5sum %s/src/remotix %s/src/rcp.c 2>&1" % (ALBERO, ALBERO))
    inf("⛔ CHE COSA HO COSTRUITO — %s" % out.strip().replace("\n", " | "))
    return True


def vicine_conta():
    rc, out, _ = rem("ss -uln 2>/dev/null")
    r = []
    for p in VICINE:
        r.append("%s:%d" % (p, out.count(":%s " % p)))
    return " ".join(r)


def registro():
    return "%s/registro.log" % LAV


def righe_registro():
    """⛔ Torna `None`, non 0: «non ho letto» e «non c'e' niente» sono due cose.

    ⛔⛔ E IL `< file` STA DENTRO `bash -c`, non in coda al comando di `sudo`.
        E' la cura n. 2 del 23 agosto (`09-b70` in testa): una redirezione in
        coda RUBA lo stdin a `sudo -S`, che allora non legge piu' la parola.
        `[M]` 24 agosto 2026, su questo banco: `wc -l < registro.log` in coda
        tornava **vuoto**, cioe' `None`, su un registro di 25 righe.  ⚠ Qui il
        `None` ha funzionato da parafulmine — ma se avesse tornato 0 avrebbe
        fatto rileggere il registro DALL'ACCENSIONE DEL SERVER, ed e'
        esattamente il difetto che costo' un giro in fase 9."""
    rc, out, _ = root("bash -c \"wc -l < %s 2>/dev/null || true\"" % registro())
    s = out.strip()
    return int(s) if s.isdigit() else None


# ═══════════════════════════════════════════════════════════════════════════
# IL GETTO — si compila DENTRO il contenitore e ci gira DENTRO
# ═══════════════════════════════════════════════════════════════════════════
GETTO = "%s/banchi/10-b90-getto" % ALBERO
GETTO_DENTRO = "%s/banchi/10-b90-getto" % DENTRO_ALB


def getto_compila():
    rc, out, err = dentro("gcc -O2 -pthread -o %s %s/banchi/10-b90-getto.c"
                          % (GETTO_DENTRO, DENTRO_ALB), 300)
    if rc != 0:
        return False, (out + err)[-500:]
    rc, out, _ = root("test -x %s && echo SI || echo NO" % GETTO)
    return ("SI" in out), out.strip()


# ⭐⭐ IL POZZO — e non e' un dettaglio, e' una CORREZIONE DEL METRO.
#
# ⛔ Un getto verso una porta che non ascolta nessuno fa nascere un ICMP «porta
#    irraggiungibile» per ogni datagramma, e `[M]` 24 agosto 2026 quell'ICMP
#    pesa **576 byte**, cioe' il **47 %** del datagramma che l'ha causato.
#    ⇒ Nella TARATURA non da' fastidio (il contatore della porta non lo vede, e
#      i conti si chiudono lo stesso).  ⛔ Nel TETTO si': la macchina spende
#      meta' del suo lavoro a fabbricare risposte d'errore, e il tetto che ne
#      esce e' **piu' basso di quello vero** — un numero prudente per il motivo
#      sbagliato, che e' comunque un numero falso.
#
# ⇒ Si apre un socket che ASCOLTA e non legge mai: la coda si riempie, il
#   nucleo butta via in silenzio, e nessun ICMP nasce.  ⚠ E lo si VERIFICA col
#   contatore `irraggiungibili`, invece di darlo per fatto.
POZZO_PID = LAV + "/.b90-pozzo.pid"


def pozzo_apri():
    pozzo_chiudi()
    prog = ("import socket,time;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);"
            "s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1<<20);"
            "s.bind((chr(48)+chr(46)+chr(48)+chr(46)+chr(48)+chr(46)+chr(48),%d));"
            "time.sleep(36000)" % tara_regola())
    root("bash -c \"setsid python3 -c '%s' >/dev/null 2>&1 & echo \\$! > %s\""
         % (prog, POZZO_PID))
    rc, out, _ = root("bash -c \"ss -uln | grep -c ':%d ' || true\"" % tara_regola())
    return out.strip() not in ("0", "")


def pozzo_chiudi():
    rc, out, _ = root("cat %s 2>/dev/null || true" % POZZO_PID)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % POZZO_PID)


def getto(porta_mia, carico, mbit_chiesti, secondi, fili=1):
    """⭐ Torna il dizionario del getto, o `None` se non ha girato."""
    rc, out, err = dentro("%s --dest 127.0.0.1:%d --porta-mia %d --carico %d "
                          "--mbit %.4f --secondi %.2f --fili %d"
                          % (GETTO_DENTRO, tara_regola(), porta_mia, carico,
                             mbit_chiesti, secondi, fili), int(secondi) + 240)
    for riga in out.splitlines():
        riga = riga.strip()
        if riga.startswith("{"):
            try:
                return json.loads(riga)
            except ValueError:
                pass
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 1 · LA TARATURA — pendenza e costante, come per lo sfalso di fase 9
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ IL GETTO VA VERSO LA PORTA 9 (`discard`), che non ascolta nessuno.  Il
#    nucleo risponde con un ICMP «porta irraggiungibile» per ogni datagramma, e
#    quell'ICMP passa da `lo` come tutto il resto: lo vede `tutto`, lo vede
#    `lo/tx_bytes`, e NON lo vede il contatore della mia porta.
#    ⚠ Se ne tiene conto invece di ignorarlo: e' la ragione per cui la taratura
#      si giudica sul contatore **della mia porta**, e la riga dell'interfaccia
#      si stampa accanto con la sua spiegazione.
#
# ⇒ Per far contare il getto alla mia porta, il getto **parte** dalla mia porta
#   di servizio?  No: la porta di servizio e' del server.  ⇒ si guasta la cosa
#   giusta: il getto va **verso** la porta PORTA+1000 e la regola di taratura si
#   installa apposta.  Vedi `tara_regola()`.
def tara_regola():
    """⭐ La porta della taratura e' gia' nella ricetta (`RICETTA`, contatore
       «tara» + insieme `su`): qui si dice solo qual e'.  ⚠ Il getto va VERSO
       questa porta, che non ascolta nessuno: il nucleo risponde con un ICMP
       «porta irraggiungibile» per ogni datagramma, e quell'ICMP lo vedono
       `tutto` e `lo/tx_bytes` ma NON il contatore «tara».  ⇒ la taratura si
       giudica su «tara», e la riga dell'interfaccia si stampa accanto con la
       sua spiegazione invece di essere ignorata."""
    return PORTA + 1000


def tara(secondi=8, ritmi=(5, 20, 60), carico=1200):
    log("1 · ⛔ LA TARATURA DEL METRO — si inietta un ritmo NOTO e si guarda "
        "se il metro lo ritrova")
    inf("il getto: %d byte di carico, %d s per punto, ritmi %s Mbit/s"
        % (carico, secondi, ", ".join(str(r) for r in ritmi)))
    p_tara = tara_regola()
    inf("porta della taratura: %d (contatore «tara», e la sessione e' la porta "
        "d'origine del getto)" % p_tara)

    punti, rossi = [], []
    for i, r in enumerate(ritmi):
        metro_azzera()
        prima = leggi()
        g = getto(30001 + i * 10, carico, r, secondi)
        dopo = leggi()
        if g is None:
            ko("⛔ il getto a %g Mbit/s non ha risposto: NON tengo il punto" % r)
            rossi.append("getto muto a %g" % r)
            continue
        d, perche = varco(prima, dopo)
        if d is None:
            ko("⛔ %g Mbit/s: %s" % (r, perche))
            rossi.append(perche)
            continue
        letto = d.get("tara", 0)
        atteso = g["byte_L3"]
        if atteso <= 0:
            ko("⛔ %g Mbit/s: il getto dice zero byte" % r)
            rossi.append("getto a zero")
            continue
        scarto = (letto - atteso) / float(atteso)
        # ⭐ IL RITMO SI GIUDICA SULLA DURATA DEL GETTO, non sulla mia finestra:
        #    fra le mie due letture ci sono due `ssh`, e mezzo secondo di
        #    sfalso a 60 Mbit/s sono 3,7 MB di errore che NON e' del metro.
        m_ritmo = mbit(letto, g["secondi"])
        pareggio = (d.get("tutto", 0) - d.get("mio_giu", 0) - d.get("mio_su", 0)
                    - d.get("tara", 0) - d.get("irraggiungibili", 0))
        punti.append({"chiesti": r, "getto_mbit_L3": g["mbit_L3"],
                      "atteso_byte": atteso, "letto_byte": letto,
                      "scarto": scarto, "letto_mbit_finestra": mbit(letto, d["secondi"]),
                      "letto_mbit_ritmo": m_ritmo,
                      "datagrammi": g["datagrammi"],
                      "pkt_letti": d.get("tara_pkt", 0),
                      "lo_tx": d["lo_tx"], "icmp": d.get("irraggiungibili", 0),
                      "altrui": pareggio})
        (ok if abs(scarto) <= 0.02 else ko)(
            "%5g Mbit/s chiesti → getto %.3f · metro %.3f · scarto sui BYTE "
            "%+.4f %% · %d datagrammi (il metro ne conta %d)"
            % (r, g["mbit_L3"], m_ritmo or 0, scarto * 100, g["datagrammi"],
               d.get("tara_pkt", 0)))
        inf("      il pareggio dei conti su %s: interfaccia %d = mio %d + tara %d"
            " + ICMP %d + ⭐ vicini %d"
            % (DEV, d["lo_tx"], d.get("mio_giu", 0) + d.get("mio_su", 0),
               d.get("tara", 0), d.get("irraggiungibili", 0), pareggio))

    if len(punti) < 2:
        ko("⛔ meno di due punti: NON posso tarare niente")
        return None, rossi + ["meno di due punti"]

    # ⭐ La retta «letto = a x atteso + b», e si guardano tutt'e due i numeri.
    xs = [p["atteso_byte"] for p in punti]
    ys = [p["letto_byte"] for p in punti]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else float("nan")
    b = my - a * mx
    peggio = max(abs(p["scarto"]) for p in punti)
    log("⭐ LA RETTA DEL METRO")
    inf("pendenza  a = %.6f   (1,000000 = il metro ritrova esattamente quel "
        "che entra)" % a)
    inf("costante  b = %+.1f byte" % b)
    inf("scarto peggiore sui %d punti: %+.3f %%" % (len(punti), peggio * 100))
    if abs(a - 1.0) <= 0.01 and peggio <= 0.02:
        ok("⭐ IL METRO E' TARATO: pendenza a 1 %% da 1, scarto peggiore sotto il 2 %%")
    else:
        ko("⛔ IL METRO SBAGLIA: pendenza %.4f, scarto peggiore %+.2f %% — "
           "questo scarto va scritto accanto a OGNI numero" % (a, peggio * 100))
        rossi.append("metro fuori taratura")
    return {"punti": punti, "pendenza": a, "costante": b, "peggio": peggio}, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 2 · LE SESSIONI
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ UN POSTO PER UTENTE — e questo cambia la forma della prova di contesa
#
# `[R]` `rcp.c:2800-2860`: il posto si chiede **per utente**, e un secondo
# client dello STESSO utente viene congedato con `0x0F GIA_ATTIVA_REMOTA`.
# ⇒ Tre sessioni insieme vogliono **tre utenti**, non tre clienti.
# ⚠ Chi non lo sapesse misurerebbe «tre sessioni» avendone aperta **una**, e i
#   numeri sarebbero quelli di una sessione sola con la faccia di tre — un
#   risultato plausibile e falso.
#
# ⛔ Gli uid stanno LONTANI dalla fila che stanno usando gli altri agenti
#    (1100-1110): 1121, 1122, 1123 sono miei e si vede che sono miei.
UTENTI = [(UTENTE, UID_B),
          ("provadec2b", 1121),
          ("provadec2c", 1122),
          ("provadec2d", 1123)]


def utenti_crea(quanti):
    """⛔ Non si riscrive `07-b64-terreno.sh`: gli si passa un ambiente diverso
       per ogni utente.  La parola e' la stessa per tutti, cosi' `$LAV/parola`
       resta uno solo e i clienti la leggono tutti di li'."""
    for nome, uid in UTENTI[:quanti]:
        a = amb()
        a["UTENTE"], a["UID_B"] = nome, str(uid)
        p = subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "utente"],
                           env=a, capture_output=True)
        if p.returncode != 0:
            ko("⛔ l'utente %s (uid %d) non si e' creato" % (nome, uid))
            return False
        ok("utente %s (uid %d)" % (nome, uid))
    return True


def sessione_apri(nome, secondi, tela="2560x1080", utente=None):
    """Apre una sessione LUNGA in sottofondo — `10-b90-sessione.sh`, che chiude SOLO i miei."""
    l, h = tela.split("x")
    args = ("--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
            "--video-codec h264 --audio-codec pcm --larghezza %s --altezza %s "
            "--resta %d" % (IND, PORTA, utente or UTENTE, DENTRO_LAV, l, h, secondi))
    rc, out, err = root("bash -c \"LAV=%s DENTRO_ALB=%s sh %s/banchi/10-b90-sessione.sh "
                        "%s %s\"" % (LAV, DENTRO_ALB, ALBERO, nome, args), 400)
    return ("SESSIONE APERTA" in out), (out + err)[-600:]


def sessioni_chiudi():
    # ⛔ SOLO i miei: l'ago e' il MIO albero, non il nome del copione (vedi il
    #    riquadro in testa a `10-b90-sessione.sh`).
    root("bash -c \"LAV=%s DENTRO_ALB=%s sh %s/banchi/10-b90-sessione.sh x spegni\""
         % (LAV, DENTRO_ALB, ALBERO), 180)


def porte_clienti():
    """⭐ Le porte dei clienti vivi, LETTE DAL METRO.

    ⛔⭐ E NON DA `ss`, e il 24 agosto 2026 il perche' e' stato misurato:
        `aioquic` usa un socket UDP **non connesso**, quindi `ss -uanp` lo
        mostra come `UNCONN 0.0.0.0:NNNNN` **senza controparte**.  ⇒ non c'e'
        modo di appaiarlo alla mia porta di servizio, e la ricerca tornava
        sempre «nessuna» su sessioni vivissime — uno zero che voleva dire «non
        so guardare», con la faccia di «non c'e' nessuno».
        ⚠ L'insieme dinamico di `nft`, invece, si popola dal TRAFFICO: una
          porta c'e' perche' ci sono passati dei byte, che e' esattamente il
          fatto che interessa."""
    L = leggi()
    if L is None:
        return None
    return sorted(L["giu"].keys())


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ QUANTE SESSIONI STANNO DAVVERO SPEDENDO — e non «quante ne ho aperte»
#
# `[M]` 24 agosto 2026, e questo banco l'ha pagato due volte nello stesso giro:
#   · braccio a UNA sessione ⇒ **zero byte in 30 s** (G1 si e' rifiutata, e ha
#     fatto bene: «0 Mbit/s» sarebbe stato una bugia);
#   · braccio a TRE sessioni ⇒ `sessioni_vive = 3` ma **`sessioni_viste = 1`**.
#
# ⛔ «La sessione si e' aperta» e «la sessione sta spedendo video» sono due
#    fatti diversi, e fra i due c'e' un desktop GNOME intero da montare: per un
#    utente appena creato ci vogliono decine di secondi prima che una finestra
#    dipinga.  ⚠ E' la forma E8 di `LEZIONI.md` §1.9 applicata a un braccio di
#    prova: il braccio «n=3» che ne misura una sola non da' errore, da' un
#    numero — e quel numero e' la meta' della domanda.
#
# ⇒ Si ASPETTA che l'insieme dinamico di `nft` veda N porte diverse muoversi, e
#   se non le vede si DICHIARA quante ce n'erano davvero invece di chiamarlo
#   «n». ⭐ E il metro dell'attesa e' lo stesso metro della misura: non un
#   secondo strumento che potrebbe dire un'altra cosa.
def quante_spediscono(secondi=3, minimo_byte=20000):
    """⭐ Torna l'elenco delle porte che hanno ricevuto piu' di `minimo_byte`
       in `secondi`, o `None` se non ho potuto leggere."""
    a = leggi()
    if a is None:
        return None
    time.sleep(secondi)
    b = leggi()
    d, _ = varco(a, b)
    if d is None:
        return None
    return sorted(p for p, (byte, _) in d["ses_giu"].items() if byte >= minimo_byte)


def attendi_sessioni(n, tetto_s=120, passo=6):
    """⛔ Aspetta che N sessioni spediscano DAVVERO.  Torna (quante, elenco)."""
    fine = time.time() + tetto_s
    ultime = []
    while time.time() < fine:
        p = quante_spediscono()
        if p is None:
            avv("⚠ non ho potuto leggere il metro mentre aspettavo le sessioni")
            return (None, [])
        ultime = p
        if len(p) >= n:
            ok("⭐ %d sessioni spediscono davvero (porte %s)"
               % (len(p), ", ".join(str(x) for x in p)))
            return (len(p), p)
        inf("aspetto: spediscono in %d su %d (porte %s)..."
            % (len(p), n, ", ".join(str(x) for x in p) or "nessuna"))
        time.sleep(passo)
    ko("⛔ dopo %d s spediscono in %d su %d: questo braccio NON e' «n=%d», e lo "
       "dico invece di chiamarlo cosi'" % (tetto_s, len(ultime), n, n))
    return (len(ultime), ultime)


def scena_accendi(quale, utente=None):
    """⛔ Non «il processo c'e'»: `09-b82-mostra.sh` conta i fotogrammi."""
    utente = utente or UTENTE
    s = SCENE[quale]
    file_ = s["file"]
    if file_ is None:
        return True, "scena ferma: non accendo niente"
    # ⛔⛔ IL LETTORE DI FASE 9 E' UN'ALTRA COSA, e va acceso com'era lui.
    #     `09-b72-video.sh` mette il filmato in una pagina di firefox-esr con
    #     `object-fit: fill`, cioe' **stirato su tutta la tela**, e ci
    #     rientra da solo a schermo intero ogni secondo.  ⚠ mpv, invece, tiene
    #     le proporzioni e mette le bande nere.  ⇒ Sullo stesso file sono due
    #     immagini diverse, e il confronto col numero di fase 9 vale solo con
    #     il lettore di fase 9 (G7, campo «lettore»).
    if s["lettore"] == "firefox":
        # ⛔ Si PREPARA con `10-b90-firefox.sh` (profilo, preferenze e pagina
        #    di fase 9, riga per riga) e si LANCIA con `09-b82-mostra.sh`, che
        #    legge l'ambiente vero e conta i fotogrammi.  ⚠ Non con
        #    `09-b72-video.sh accendi`, che l'ambiente se lo inventa.
        rc, out, err = root("bash -c \"sh %s/banchi/10-b90-firefox.sh %s %s\""
                            % (ALBERO, utente, file_), 300)
        pronto = [r for r in (out + err).splitlines() if r.startswith("PRONTO ")]
        if not pronto:
            return False, ("⛔ il lettore di fase 9 non si e' preparato: %s"
                           % (out + err).strip()[-800:])
        _, profilo, pagina = pronto[-1].split()
        rc, out, err = root(
            "bash -c \"REGISTRO=%s SECONDI=8 bash %s/banchi/09-b82-mostra.sh %s "
            "env MOZ_ENABLE_WAYLAND=1 GDK_BACKEND=wayland firefox-esr "
            "--profile %s --kiosk file://%s\""
            % (registro(), ALBERO, utente, profilo, pagina), 300)
        # ⛔ E NON BASTA CHE FIREFOX SIA VIVO — e' esattamente il difetto che
        #    `09-b82-mostra.sh` e' nato per curare (fase 9, tre volte in due
        #    giorni).  ⚠ Firefox ci mette piu' di mpv: la finestra si guarda
        #    DOPO che ha avuto il tempo di aprirsi, o si legge il suo avvio.
        time.sleep(10)
        buono, m = scena_dipinge(8)
        return (buono is True), ("firefox di fase 9 — %s\n%s"
                                 % (m, (out + err)[-900:]))
    rc, out, err = root("bash -c \"REGISTRO=%s SECONDI=6 bash %s/banchi/09-b82-mostra.sh "
                        "%s mpv --fullscreen --loop --no-audio --really-quiet %s\""
                        % (registro(), ALBERO, utente, file_), 300)
    return (rc == 0), (out + err)[-1500:]


def uid_di(nome):
    for n, u in UTENTI:
        if n == nome:
            return u
    return UID_B


def scena_dipinge(secondi=6, minimo_fot=None):
    """⭐ «La finestra c'e'» si legge nei FOTOGRAMMI SPEDITI, non in `ps`.

    ⛔ E' la stessa regola di `09-b82-mostra.sh`, riscritta qui perche' il
       braccio con firefox non passa di li'.  ⚠ E il verdetto e' il CONTO, non
       i byte: la bandiera a tinte piatte fa 40 fotogrammi al secondo da 268
       byte l'uno — chi guardasse i byte direbbe «la finestra non c'e'» su una
       finestra che c'e' per intero."""
    minimo_fot = minimo_fot if minimo_fot is not None else FOND_MIN_FOT
    riga0 = righe_registro()
    if riga0 is None:
        return (None, "⛔ il registro non si e' letto: NON dico che dipinge e "
                      "non dico che non dipinge")
    a = leggi(registro(), riga0)
    if a is None:
        return (None, "⛔ non ho potuto leggere il metro")
    time.sleep(secondi)
    b = leggi(registro(), riga0)
    if b is None:
        return (None, "⛔ non ho potuto rileggere il metro")
    d, perche = varco(a, b)
    if d is None:
        return (None, perche)
    fot = d.get("spediti")
    if fot is None:
        return (None, "⛔ i fotogrammi non si sono letti")
    if fot < minimo_fot:
        return (False, "⛔ %d fotogrammi in %.1f s: la finestra NON dipinge "
                       "sul nostro monitor" % (fot, d["secondi"]))
    return (True, "%d fotogrammi in %.1f s, %s byte/fotogramma"
            % (fot, d["secondi"],
               "%.0f" % (d["byte_utili"] / fot) if d.get("byte_utili") else "—"))


def scena_spegni(quanti=1):
    for nome, uid in UTENTI[:quanti]:
        root("bash -c \"bash %s/banchi/09-b82-mostra.sh --ferma %s\"" % (ALBERO, nome), 120)
        # ⛔ E ANCHE FIREFOX, con l'UID GIUSTO — pagato in fase 9 il 23 agosto:
        #    `09-b72-video.sh -- spegni` senza `UID_B` prende il riposo 1001 e
        #    ammazza il firefox di un ALTRO utente, lasciando acceso il proprio.
        #    ⚠ In fase 10 quell'«altro utente» e' l'agente del banco accanto.
        root("bash -c \"UID_B=%d sh %s/banchi/09-b72-video.sh -- spegni; true\""
             % (uid, ALBERO), 120)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 3 · LE TRE SCENE — mediano e picco, coi fotogrammi accanto
# ═══════════════════════════════════════════════════════════════════════════
def campiona(secondi, passo=1.0, reg=None, riga0=0):
    """⭐ Si campiona OGNI SECONDO, non una volta sola: il mediano e il picco
       sono due numeri diversi e un totale diviso per la durata non li da'."""
    letture = [leggi(reg, riga0)]
    if letture[0] is None:
        return None
    fine = time.time() + secondi
    while time.time() < fine:
        time.sleep(max(0.0, min(passo, fine - time.time())))
        L = leggi(reg, riga0)
        if L is None:
            return None
        letture.append(L)
    return letture


def serie(letture):
    """Da N letture ⇒ N-1 varchi, con la guardia G2 su ognuno."""
    fuori = []
    for a, b in zip(letture, letture[1:]):
        d, perche = varco(a, b)
        if d is None:
            return None, perche
        fuori.append(d)
    return fuori, "ok"


def scene(secondi=30, quali=None, tela="2560x1080", cure="accese"):
    """⛔ `cure` non e' un ornamento: entra nel profilo di OGNI riga, e G7 lo
       usa per rifiutare i confronti sleali.  Chi la cambia deve averla
       cambiata **anche nel server** (`ab_cure()` lo fa)."""
    log("2 · ⭐ LE SCENE — bit/s mediano e di picco, coi fotogrammi accanto")
    quali = quali or ["ferma", "desktop", "duro"]
    esiti, rossi = {}, []
    inf("⛔ le cure di fase 9 in questo giro: **%s** — e il profilo di ogni "
        "riga se lo porta dietro" % cure)

    ap, det = sessione_apri("filo", secondi * (len(quali) + 3) + 240, tela)
    if not ap:
        ko("⛔ la sessione non si e' aperta:")
        print(det)
        return None, ["sessione non aperta"]
    ok("sessione aperta, tela %s, codec h264" % tela)
    time.sleep(6)
    porte = porte_clienti()
    inf("porta del cliente, letta da ss: %s" % (porte or "⚠ non letta"))

    try:
        for quale in quali:
            file_ = SCENE[quale]["file"]
            log("scena «%s» — %s" % (quale, SCENE[quale]["perche"]))
            if file_:
                acceso, det = scena_accendi(quale)
                for riga in det.splitlines():
                    if "fondo:" in riga or "dopo:" in riga or "G4" in riga or "⛔" in riga:
                        inf(riga.strip())
                time.sleep(3)
            riga0 = righe_registro()
            if riga0 is None:
                ko("⛔ non ho potuto leggere il registro: NON giudico questa scena")
                rossi.append("registro non letto su %s" % quale)
                continue
            metro_azzera()
            letture = campiona(secondi, 1.0, registro(), riga0)
            if letture is None:
                ko("⛔ una lettura e' mancata: NON giudico questa scena")
                rossi.append("lettura mancata su %s" % quale)
                if file_:
                    scena_spegni()
                continue
            spie = spie_conta(riga0)
            varchi, perche2 = serie(letture)
            d_tot, perche3 = varco(letture[0], letture[-1])
            if varchi is None or d_tot is None:
                ko("⛔ %s" % (perche2 if varchi is None else perche3))
                rossi.append(perche2 if varchi is None else perche3)
                if file_:
                    scena_spegni()
                continue

            # ── le guardie, TUTTE, e prima dei numeri ──────────────────────
            g1, m1 = g1_flusso_partito(d_tot)
            g3, m3 = g3_scena_si_muove(d_tot,
                                       minimo_fot=0 if quale == "ferma" else FOND_MIN_FOT)
            g4, m4 = g4_somma_torna(d_tot)
            g5, m5 = g5_metro_su_se_stesso(d_tot)
            g6, m6 = g6_entropia_vera(d_tot, SCENE[quale]["alta"], tela)
            for etichetta, (g, m) in (("G1 flusso partito", (g1, m1)),
                                      ("G3 la scena si muove", (g3, m3)),
                                      ("G4 la somma torna", (g4, m4)),
                                      ("G5 il metro su se stesso", (g5, m5)),
                                      ("G6 l'entropia dichiarata", (g6, m6))):
                (ok if g is True else (avv if g is None else ko))("%s · %s" % (etichetta, m))
            if g1 is None:
                rossi.append("G1 su %s: %s" % (quale, m1))
                if file_:
                    scena_spegni()
                continue
            if g4 is False or g5 is False:
                rossi.append("G4/G5 su %s" % quale)

            # ── i numeri ───────────────────────────────────────────────────
            gius = [mbit(d.get("mio_giu", 0), d["secondi"]) for d in varchi]
            gius = [x for x in gius if x is not None]
            sus = [mbit(d.get("mio_su", 0), d["secondi"]) for d in varchi]
            sus = [x for x in sus if x is not None]
            tot = [g + s for g, s in zip(gius, sus)]
            fot = d_tot.get("spediti") or 0
            bu = d_tot.get("byte_utili") or 0
            e = {
                "scena": quale, "secondi": d_tot["secondi"],
                # ⛔⛔ IL PROFILO VIAGGIA COL NUMERO, e non e' cortesia: e' la
                #     sola cosa che impedisce che fra sei settimane qualcuno
                #     confronti questo numero con un altro preso su un'altra
                #     scena, con un altro lettore o con le cure spente — cioe'
                #     esattamente la discordanza da dieci volte che questo
                #     banco e' stato mandato a sciogliere.
                # ⛔ «scena» e' il CONTENUTO, non la chiave: `grana` e
                #    `grana-ff` sono lo stesso film mostrato in due modi, e la
                #    differenza fra i due sta tutta nel campo «lettore».
                #    ⚠ Se il contenuto stesse nella chiave, G7 respingerebbe
                #      il confronto per la ragione sbagliata e non isolerebbe
                #      piu' niente.
                "profilo": {"scena": SCENE[quale]["contenuto"], "tela": tela,
                            "codec": "h264",
                            "lettore": SCENE[quale]["lettore"],
                            "cure": cure, "file": SCENE[quale]["file"],
                            "chiave": quale},
                "entropia_dichiarata_alta": SCENE[quale]["alta"],
                "entropia_confermata": g6,
                "giu_mediano": statistics.median(gius) if gius else None,
                "giu_picco": max(gius) if gius else None,
                "su_mediano": statistics.median(sus) if sus else None,
                "tot_mediano": statistics.median(tot) if tot else None,
                "tot_picco": max(tot) if tot else None,
                "fotogrammi": fot,
                "byte_per_fot": (bu / fot) if fot else None,
                "byte_utili": bu,
                "utile_mbit": mbit(bu, d_tot["secondi"]),
                # ⭐⭐ I BYTE PER DATAGRAMMA, e questo numero decide se i numeri
                #     di `lo` si possono tradurre sul RAME.  Su `lo` la MTU e'
                #     65536: se ngtcp2 ne approfittasse, un fotogramma
                #     viaggerebbe in pochi pacchettoni e la cornice ethernet
                #     (38 byte a pacchetto) sarebbe trascurabile — ma su un
                #     cavo vero quegli stessi byte diventerebbero decine di
                #     pacchetti da 1500, e il costo salirebbe.
                #     ⇒ Si legge, non si suppone.
                "giu_pacchetti": d_tot.get("mio_giu_pkt"),
                "giu_byte_per_pacchetto":
                    (d_tot.get("mio_giu", 0) / d_tot["mio_giu_pkt"])
                    if d_tot.get("mio_giu_pkt") else None,
                "su_pacchetti": d_tot.get("mio_su_pkt"),
                "su_byte_per_pacchetto":
                    (d_tot.get("mio_su", 0) / d_tot["mio_su_pkt"])
                    if d_tot.get("mio_su_pkt") else None,
                "altrui_mbit": mbit(d_tot["altrui"], d_tot["secondi"]),
                "sessioni": len(d_tot["ses_giu"]),
                "scena_si_muove": g3,
                # ⭐⭐ IL MEDIANO NON BASTA, E IL 24 AGOSTO 2026 L'HA DIMOSTRATO:
                #     `[M]` sul caso duro il mediano dice 0,72 Mbit/s e il picco
                #     21,9 — cioe' la distribuzione e' a DUE GOBBE e nessuno dei
                #     due numeri descrive la scena.  ⇒ si porta anche la MEDIA
                #     (byte totali / durata), che e' quel che il budget deve
                #     sommare, e la SERIE al secondo, che e' l'unica cosa che
                #     fa vedere la forma.
                "tot_medio": mbit(d_tot.get("mio_giu", 0) + d_tot.get("mio_su", 0),
                                  d_tot["secondi"]),
                "serie": [{"s": round(d["secondi"], 3),
                           "giu_mbit": mbit(d.get("mio_giu", 0), d["secondi"]),
                           "fot": d.get("spediti"),
                           "byte": d.get("mio_giu", 0)} for d in varchi],
                # ⛔ E LE SPIE DELLE CURE, perche' un ritmo che scende puo'
                #    essere la scena o puo' essere una CURA che ha deciso.  Le
                #    due si distinguono solo guardando se la cura ha parlato.
                "spie": spie,
            }
            esiti[quale] = e
            log("⭐ «%s»: %.3f Mbit/s mediano · %.3f di picco (giu' %.3f / su' %.3f)"
                % (quale, e["tot_mediano"] or 0, e["tot_picco"] or 0,
                   e["giu_mediano"] or 0, e["su_mediano"] or 0))
            inf("⭐ media sui %.0f s: %.3f Mbit/s — e il MEDIANO e' %.3f: se i "
                "due sono lontani la distribuzione ha due gobbe e il mediano "
                "NON descrive la scena"
                % (e["secondi"], e["tot_medio"] or 0, e["tot_mediano"] or 0))
            # ⛔ Il sovrapprezzo si calcola sulla MEDIA, non sul mediano: sono
            #    byte contro byte, e il mediano di una distribuzione a due gobbe
            #    darebbe un «-82 %», cioe' un filo che porta MENO del suo
            #    carico — un'assurdita' che il 24 agosto e' comparsa davvero.
            inf("carico utile %.3f Mbit/s ⇒ ⭐ il filo costa il %s in piu' "
                "(QUIC + ACK + ritrasmissioni + audio + IP/UDP)"
                % (e["utile_mbit"] or 0,
                   "%+.0f %%" % ((e["tot_medio"] / e["utile_mbit"] - 1) * 100)
                   if (e["utile_mbit"] or 0) > 0.001 and e["tot_medio"] else "—"))
            inf("le spie delle cure in questa scena: %s"
                % ", ".join("%s=%s" % (k, v) for k, v in sorted(spie.items())))
            inf("sollecitazione arrivata: %d fotogrammi, %s byte/fotogramma"
                % (fot, "%.0f" % e["byte_per_fot"] if e["byte_per_fot"] else "—"))
            inf("⭐ i datagrammi: giu' %s pacchetti da %s byte · su' %s da %s "
                "⇒ sul RAME ci sarebbero +38 byte a pacchetto, cioe' %s"
                % (e["giu_pacchetti"],
                   "%.0f" % e["giu_byte_per_pacchetto"] if e["giu_byte_per_pacchetto"] else "—",
                   e["su_pacchetti"],
                   "%.0f" % e["su_byte_per_pacchetto"] if e["su_byte_per_pacchetto"] else "—",
                   "%+.1f %%" % (38.0 * 100 / e["giu_byte_per_pacchetto"])
                   if e["giu_byte_per_pacchetto"] else "—"))
            inf("rumore dei vicini su %s durante la scena: %.3f Mbit/s"
                % (DEV, e["altrui_mbit"] or 0))
            if file_:
                scena_spegni()
                time.sleep(2)
    finally:
        sessioni_chiudi()
    return esiti, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ 3-bis · L'A/B DELL'AUDIO — «il costo del NIENTE», e da dove viene
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `[M]` fase 9 §14.2, scena ferma: **2,427 Mbit/s sul filo**, e la fase 9
#    stessa scrive che *«a desktop fermo il 100 % di quel che passa e' QUIC +
#    l'audio PCM, che da solo chiede 1,536 Mbit/s»*.
# ⭐ `[M]` 24 agosto 2026, questo banco, stessa scena e stessa tela: **0,003
#    Mbit/s**.  ⇒ ottocento volte meno.
#
# ⛔⛔ E QUI NON SI DEDUCE.  «Sara' la cura del silenzio dell'audio» e' una
#     spiegazione plausibile, ed e' esattamente il genere di frase che
#     `LEZIONI.md` §2.3-quater chiama *«un fatto che era una deduzione mai
#     misurata»* (forma E5).  ⇒ si SPEGNE la cura e si guarda il numero.
#
# ⚠ E si dichiara che si spengono: `CODER.md` §2-bis dice che le cure della
#   fase 9 sono ACCESE per predefinito, e un banco che le confronta col passato
#   **le spegne a mano e lo scrive**.
def ab_audio(secondi=30, tela="2560x1080"):
    log("3-bis · ⭐⭐⭐ L'A/B DELL'AUDIO — da dove vengono gli 800× della scena ferma")
    esiti, rossi = {}, []
    bracci = [("cure ACCESE (il predefinito di oggi)", ""),
              ("⛔ silenzio dell'audio SPENTO a mano", "--niente-audio-silenzio")]
    for nome, opz in bracci:
        log("braccio: %s" % nome)
        a = amb()
        a["OPZIONI_SERVER"] = opz
        if subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"],
                          env=a, capture_output=True).returncode != 0:
            ko("⛔ il server non si e' riacceso con «%s»" % opz)
            rossi.append("accensione fallita con «%s»" % opz)
            continue
        buono, m = metro_installa()
        if not buono:
            ko("⛔ il metro non si e' reinstallato: %s" % m)
            rossi.append("metro")
            continue
        ap, det = sessione_apri("ab", secondi + 240, tela)
        if not ap:
            ko("⛔ la sessione non si e' aperta")
            print(det[-400:])
            rossi.append("sessione a «%s»" % opz)
            continue
        time.sleep(8)
        riga0 = righe_registro()
        metro_azzera()
        letture = campiona(secondi, 1.0, registro(), riga0)
        sessioni_chiudi()
        if letture is None or riga0 is None:
            ko("⛔ non ho misurato: NON giudico questo braccio")
            rossi.append("lettura a «%s»" % opz)
            continue
        d, perche = varco(letture[0], letture[-1])
        if d is None:
            ko("⛔ %s" % perche)
            rossi.append(perche)
            continue
        # ⛔ Qui G1 NON si applica come rifiuto: la domanda E' quanto poco passa.
        #    ⚠ Ma zero-zero resta un rifiuto: se non passa NIENTE il cliente non
        #      c'era, e allora non ho misurato il silenzio, ho misurato l'assenza.
        mio = d.get("mio_giu", 0) + d.get("mio_su", 0)
        if mio <= 0:
            ko("⛔ ZERO byte: il cliente non c'era, e questo non e' «silenzio»")
            rossi.append("zero byte a «%s»" % opz)
            continue
        e = {"braccio": nome, "opzioni": opz, "secondi": d["secondi"],
             "mbit": mbit(mio, d["secondi"]),
             "byte": mio, "pacchetti": d.get("mio_giu_pkt"),
             "fotogrammi": d.get("spediti"), "byte_utili": d.get("byte_utili")}
        esiti[opz or "predefinito"] = e
        ok("%s → ⭐ **%.4f Mbit/s** (%d byte in %.1f s, %s pacchetti, %s fotogrammi)"
           % (nome, e["mbit"], mio, d["secondi"], d.get("mio_giu_pkt"),
              d.get("spediti")))
    # ⭐ Il rapporto, che e' la risposta
    a = esiti.get("predefinito", {}).get("mbit")
    b = esiti.get("--niente-audio-silenzio", {}).get("mbit")
    if a and b:
        log("⭐⭐⭐ LA RISPOSTA")
        inf("con la cura %.4f Mbit/s · senza %.4f Mbit/s ⇒ ⭐ **la cura toglie "
            "%.0f×**, cioe' %.3f Mbit/s per sessione ferma" % (a, b, b / a, b - a))
        inf("×10 sessioni ferme: **%.2f Mbit/s** con la cura, **%.2f** senza"
            % (a * 10, b * 10))
    else:
        avv("⚠ uno dei due bracci non ha prodotto un numero: NON dichiaro il rapporto")
    # ⛔ E SI RIMETTE IL SERVER COM'ERA, o il passo dopo misura un altro prodotto.
    subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"], env=amb(),
                   capture_output=True)
    metro_installa()
    ok("server rimesso ai predefiniti")
    return esiti, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ 3-ter · LA RICONCILIAZIONE — «da dove viene il 44,6», incarico 10-b7
#
# ⛔ IL FATTO DA CUI PARTE.  Due misure della stessa cosa, e differiscono di
#    DIECI VOLTE:
#
#   | | il «caso duro» | byte/fotogramma |
#   |---|---|---|
#   | fase 9 §14.2, H.264, 2560x1080  | **44,574 Mbit/s** = 223 % del pavimento | 239 129 |
#   | fase 10 §6.3, H.264, 2560x1080  | **4,478 Mbit/s**                        |  16 884 |
#
# ⛔⛔ E LA PRIMA COSA DA DIRE E' CHE NON SONO NEMMENO LA STESSA GRANDEZZA.
#     `[R]` fase 9 §14.2 contava i byte delle righe `SPEDITO` del registro,
#     cioe' **il carico utile del video e basta**; la colonna «filo `lo`» della
#     stessa tabella dice **48,42**, ed e' quella confrontabile col metro di
#     oggi.  ⇒ Il 44,574 e' un numero di VIDEO, il 4,478 un numero di FILO: il
#     primo e' sempre piu' piccolo del secondo sulla stessa sessione.  ⚠ Ma
#     questo peggiora la discordanza invece di spiegarla: 48,42 contro 4,478
#     e' undici volte, non dieci.
#
# ⇒ ⭐ ALLORA LA DIFFERENZA STA NELLA SOLLECITAZIONE, e sono TRE variabili
#   cambiate insieme fra le due misure.  Questo passo le separa una per volta,
#   ed e' l'unico modo di dire **come si spartisce**:
#
#     A1 · grana + firefox + cure SPENTE  ⇒ la ricostruzione di fase 9
#     A2 · grana + mpv     + cure SPENTE  ⇒ A1-A2 e' il LETTORE
#     A3 · grana + mpv     + cure ACCESE  ⇒ A2-A3 sono le CURE
#     A4 · duro  + mpv     + cure ACCESE  ⇒ A3-A4 e' la SCENA (= §6.3)
#
# ⛔ Le cure si accendono e si spengono nel SERVER, e poi si RILEGGONO dalle
#    righe che il server scrive da se': dichiararle sarebbe la forma E8.
# ═══════════════════════════════════════════════════════════════════════════

# ⛔ Le quattro cure della fase 9 spente in un colpo solo — e sono QUATTRO
#    opzioni perche' quattro sono le cure, non perche' una sarebbe bastata.
#    ⚠ `--qualita-risale` e `--tetto-banda-mbit` sono gia' spente di suo (I6),
#      quindi non compaiono: metterle sarebbe far credere che le stia togliendo.
CURE_SPENTE = ("--niente-ritmo-adattivo --niente-linea-morta "
               "--niente-audio-silenzio --sgombra-soglia-ms 0")

# ⭐ Le quattro spie nel registro d'avvio del server, e la parola che le decide.
#    ⛔ Si LEGGONO, non si dichiarano: e' l'unica differenza fra «ho spento le
#       cure» e «credo di aver spento le cure» (`LEZIONI.md` §1.9, forma E8).
# ⛔⛔ E L'AGO DELLA SOGLIA PORTA IL «(§5.1)» APPOSTA — pagato il 24 agosto 2026.
#     Con le cure ACCESE il server scrive DUE righe che contengono «soglia
#     della coda video»: quella che decide, e una seconda che spiega che la
#     soglia e' il prerequisito del regolatore («e la soglia della coda video
#     e' accesa a 100 ms»).  ⚠ La seconda dice «accesa» in minuscolo, quindi
#     l'ago prendeva l'ultima riga e tornava **IGNOTA** su una cura accesissima.
#     ⇒ Rosso su prodotto sano: il banco si e' rifiutato di misurare per un
#       difetto suo.  Ed e' andata BENE cosi': il rifiuto e' stato rumoroso.
SPIE_CURE = {
    "soglia_coda":  ("soglia della coda video (§5.1)", "ACCESA", "SPENTA"),
    "ritmo":        ("il regolatore del ritmo e'", "ACCESO", "SPENTO"),
    "linea_morta":  ("la LINEA MORTA e'", "ACCESA", "SPENTA"),
    "audio_silenzio": ("il silenzio dell'audio che il padre PASSERA'", "ACCESO", "SPENTO"),
}


def cure_lette(righe_testa=60):
    """⭐ Che cosa il SERVER dice di avere acceso — letto, non dedotto.

    Torna un dizionario `{cura: True|False}`, oppure `None` se non ha potuto
    leggere.  ⛔ Una cura che non si ritrova nel registro vale `None` e non
    `False`: «la riga non c'e'» e «la cura e' spenta» sono due fatti diversi,
    ed e' esattamente la coppia che `LEZIONI.md` §1.9 chiama E8."""
    rc, out, _ = root("bash -c \"head -n %d %s 2>/dev/null || true\""
                      % (righe_testa, registro()), 60)
    if not out.strip():
        return None
    # ⛔ L'ULTIMA accensione, non la prima: il registro non si azzera fra un
    #    braccio e l'altro, e leggere la testa del file darebbe le cure di
    #    mezz'ora fa con la faccia di quelle di adesso.
    rc, out, _ = root("bash -c \"awk '/avvio +REMOTIX/{n=NR} {r[NR]=\\$0} "
                      "END{for(i=n;i<=NR && i<n+%d;i++) print r[i]}' %s\""
                      % (righe_testa, registro()), 60)
    if not out.strip():
        return None
    d = {}
    for cura, (ago, acceso, spento) in SPIE_CURE.items():
        riga = [r for r in out.splitlines() if ago in r]
        if not riga:
            d[cura] = None
            continue
        pezzo = riga[-1].split(ago, 1)[1][:80]
        if acceso in pezzo:
            d[cura] = True
        elif spento in pezzo:
            d[cura] = False
        else:
            d[cura] = None
    return d


def cure_verifica(attese):
    """⛔ `attese` e' `"accese"` o `"spente"`.  ROSSO se il server ne dice
       un'altra — e ROSSO anche se non si e' potuto leggere."""
    lette = cure_lette()
    if lette is None:
        return (None, "⛔ non ho potuto leggere le righe d'avvio: NON dichiaro "
                      "in che stato sono le cure, e quindi non misuro")
    vuole = (attese == "accese")
    fuori = {k: v for k, v in lette.items() if v is not vuole}
    riga = " · ".join("%s=%s" % (k, {True: "ACCESA", False: "spenta",
                                     None: "⛔IGNOTA"}[v])
                      for k, v in sorted(lette.items()))
    if any(v is None for v in lette.values()):
        return (None, "⛔ una cura non si e' letta nel registro: %s.  «La riga "
                      "non c'e'» non e' «la cura e' spenta»" % riga)
    if fuori:
        return (False, "⛔⛔ IL SERVER NON HA LE CURE CHE HO CHIESTO — chieste "
                       "«%s», in vigore: %s.  ⇒ questo braccio misurerebbe un "
                       "prodotto diverso da quello che dichiara" % (attese, riga))
    return (True, "cure «%s», verificate nelle righe del server: %s"
            % (attese, riga))


def server_con(cure, opzioni_extra=""):
    """Riaccende il server con le cure chieste e ne VERIFICA lo stato letto."""
    opz = (CURE_SPENTE if cure == "spente" else "")
    if opzioni_extra:
        opz = (opz + " " + opzioni_extra).strip()
    a = amb()
    a["OPZIONI_SERVER"] = opz
    p = subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"],
                       env=a, capture_output=True)
    if p.returncode != 0:
        return (False, "⛔ il server non si e' riacceso con «%s»: %s"
                % (opz, p.stdout.decode("utf-8", "replace")[-500:]))
    buono, m = metro_installa()
    if not buono:
        return (False, "⛔ il metro non si e' reinstallato: %s" % m)
    g, msg = cure_verifica(cure)
    return (g is True), msg


# ⛔⛔ I NUMERI DI FASE 9 §14.2, TRASCRITTI QUI CON IL LORO PROFILO ACCANTO.
#     ⚠ Senza il profilo sarebbero tre numeri buoni per qualunque confronto, ed
#       e' cosi' che una discordanza da dieci volte attraversa una fase intera.
FASE9 = {
    "profilo": {"scena": "film-grana", "tela": "2560x1080", "codec": "h264",
                "lettore": "firefox", "cure": "spente",
                "file": "/media/REMOTIX/tmp/09c/film-grana.webm",
                "chiave": "grana-ff"},
    "utile_mbit": 44.574,     # riga «carico video H.264» — SOLO i byte SPEDITO
    "filo_mbit": 48.42,       # colonna «filo lo» — /proc/net/dev, tutto il traffico
    "fot_s": 23.30,
    "byte_per_fot": 239129,
    "dove": "fasi/09-la-qualita-e-la-degradazione.md §14.2, 23 ago 2026 14:25:55 UTC",
}


def fase9(secondi=30, tela="2560x1080", quali=None):
    """⭐⭐⭐ LA RICONCILIAZIONE — quattro bracci, una variabile per volta."""
    log("3-ter · ⭐⭐⭐ DA DOVE VIENE IL 44,6 — la scena di fase 9, col metro di oggi")
    inf("⛔ il numero di fase 9 e' un CARICO UTILE (%.3f Mbit/s), il filo della "
        "stessa riga e' %.2f — e il metro di oggi conta il FILO.  ⇒ il "
        "confronto giusto e' filo contro filo"
        % (FASE9["utile_mbit"], FASE9["filo_mbit"]))
    bracci = quali or [("A1", "grana-ff", "spente"),
                       ("A2", "grana", "spente"),
                       ("A3", "grana", "accese"),
                       ("A4", "duro", "accese")]
    esiti, rossi = {}, []
    for etichetta, quale, cure in bracci:
        log("braccio %s — scena «%s», lettore «%s», cure %s"
            % (etichetta, quale, SCENE[quale]["lettore"], cure))
        buono, m = server_con(cure)
        (ok if buono else ko)(m)
        if not buono:
            rossi.append("%s: %s" % (etichetta, m[:150]))
            continue
        t, r = scene(secondi=secondi, quali=[quale], tela=tela, cure=cure)
        rossi += ["%s: %s" % (etichetta, x) for x in r]
        if not t or quale not in t:
            ko("⛔ il braccio %s non ha prodotto un numero" % etichetta)
            rossi.append("%s senza numero" % etichetta)
            continue
        e = t[quale]
        e["braccio"] = etichetta
        esiti[etichetta] = e
        ok("%s ⇒ ⭐ **%.3f Mbit/s sul filo** · carico utile %.3f · %d "
           "fotogrammi · %s byte/fot"
           % (etichetta, e.get("tot_medio") or 0, e.get("utile_mbit") or 0,
              e["fotogrammi"],
              "%.0f" % e["byte_per_fot"] if e["byte_per_fot"] else "—"))

    # ── ⛔ IL CONFRONTO COL PASSATO, E PASSA DA G7 ─────────────────────────
    log("⛔ IL CONFRONTO CON FASE 9 §14.2 — e G7 decide se e' lecito")
    for etichetta in ("A1", "A2", "A3", "A4"):
        e = esiti.get(etichetta)
        if not e:
            continue
        # ⛔⛔ E PRIMA DI G7 VIENE G3, e il 24 agosto 2026 questo ordine e'
        #     stato pagato sul campo: il braccio A1 (firefox) ha dato **2,427
        #     Mbit/s** con un profilo che combaciava con fase 9 riga per riga —
        #     e ZERO fotogrammi, perche' firefox su questa macchina non dipinge
        #     piu' (fase 9 §20.1-ter, ✅ e non e' nostro).
        #     ⇒ G7 avrebbe detto «confronto lecito» e il banco avrebbe stampato
        #       «oggi 0,05× di fase 9» su una scena che non c'era.  ⚠ Un numero
        #       plausibile e falso, di nuovo, e con tutte le guardie del filo
        #       verdi: e' il filo che passa, non e' il video.
        if e.get("scena_si_muove") is not True:
            ko("%s · ⛔ LA SCENA NON SI E' MOSSA (%s fotogrammi): non confronto "
               "niente con fase 9.  Un profilo che combacia su una scena che "
               "non c'e' e' la peggiore delle due specie"
               % (etichetta, e.get("fotogrammi")))
            e["confronto_lecito"] = None
            continue
        g, m = g7_confronto_leale(e["profilo"], FASE9["profilo"])
        (ok if g is True else (avv if g is None else ko))("%s · %s" % (etichetta, m))
        e["confronto_lecito"] = g
        # ⛔⭐⭐ IL CONFRONTO CONDIZIONATO, e non e' una scappatoia: e' l'unica
        #      strada onesta rimasta dopo il 24 agosto 2026.
        #
        #      ✅ Firefox e' ROTTO su questa macchina — **per tutti, dentro e
        #      fuori REMOTIX** (fase 9 §20.1-ter: `--headless --screenshot` da
        #      `nicfio`, senza nessun Wayland, si pianta uguale).  ⇒ il lettore
        #      con cui fase 9 ha misurato le sue cinque scene **non e' piu'
        #      riproducibile**, e nessun banco potra' piu' chiudere quel campo.
        #
        #      ⇒ Allora: se l'UNICA differenza e' il lettore, il rapporto si
        #      stampa lo stesso — ma marcato `[?]` e con la condizione scritta
        #      accanto, mai `[M]`.  ⛔ E la condizione va detta per intero: il
        #      filmato e' 2560x1080 come la tela, quindi `object-fit: fill` di
        #      firefox e `mpv --fullscreen` mostrano **gli stessi pixel senza
        #      scalare** — e' un ARGOMENTO, non una misura.
        solo_lettore = (g is False and
                        [c for c in CAMPI_PROFILO
                         if e["profilo"].get(c) != FASE9["profilo"].get(c)] == ["lettore"])
        if g is not True and not solo_lettore:
            inf("⇒ per %s NON stampo nessun rapporto col 44,6: sarebbe un "
                "numero che sembra una risposta" % etichetta)
            continue
        if solo_lettore:
            avv("⚠ %s: l'unica differenza e' il LETTORE (%s contro %s).  ✅ E "
                "firefox non e' piu' riproducibile su questa macchina (fase 9 "
                "§20.1-ter, e non e' nostro) ⇒ stampo il rapporto marcato "
                "`[?]`, con la condizione: il filmato e' 2560x1080 come la "
                "tela, quindi i due lettori mostrano gli stessi pixel senza "
                "scalare — ARGOMENTO, non misura"
                % (etichetta, e["profilo"].get("lettore"),
                   FASE9["profilo"].get("lettore")))
            e["confronto_lecito"] = "condizionato"
        u, f = e.get("utile_mbit"), e.get("tot_medio")
        if not u or not f:
            avv("⚠ %s: manca un numero, non calcolo il rapporto" % etichetta)
            continue
        inf("⭐⭐ %s CONTRO FASE 9 §14.2, grandezza per grandezza%s:"
            % (etichetta, "  ⚠ `[?]` CONDIZIONATO" if solo_lettore else ""))
        inf("    carico utile: oggi %.3f — fase 9 %.3f  ⇒ **%.2f×**"
            % (u, FASE9["utile_mbit"], u / FASE9["utile_mbit"]))
        inf("    filo:         oggi %.3f — fase 9 %.3f  ⇒ **%.2f×**"
            % (f, FASE9["filo_mbit"], f / FASE9["filo_mbit"]))
        if e.get("byte_per_fot"):
            inf("    byte/fotogramma: oggi %.0f — fase 9 %d  ⇒ **%.2f×**"
                % (e["byte_per_fot"], FASE9["byte_per_fot"],
                   e["byte_per_fot"] / float(FASE9["byte_per_fot"])))
        e["rapporto_utile"] = u / FASE9["utile_mbit"]
        e["rapporto_filo"] = f / FASE9["filo_mbit"]

    # ── ⭐ COME SI SPARTISCE, e questo E' il risultato ─────────────────────
    log("⭐⭐⭐ COME SI SPARTISCE LA DIFFERENZA — una variabile per volta")

    def coppia(nome, x, y, che):
        a, b = esiti.get(x), esiti.get(y)
        if not a or not b:
            avv("⚠ %s: manca %s — NON dichiaro questo pezzo"
                % (nome, x if not a else y))
            return None
        fermi = [n for n, e in ((x, a), (y, b))
                 if e.get("scena_si_muove") is not True]
        if fermi:
            ko("⛔ %s: in %s la scena non si e' mossa — questo pezzo NON si "
               "spartisce" % (nome, " e ".join(fermi)))
            return None
        # ⛔ G7 anche qui, e stavolta a campo VARIABILE: due bracci che
        #    differiscono per PIU' di una cosa non isolano niente.
        g, m = g7_confronto_leale(a["profilo"], b["profilo"],
                                  campi=[c for c in CAMPI_PROFILO if c != che])
        if g is not True:
            ko("⛔ %s: i due bracci differiscono anche in altro — %s" % (nome, m))
            return None
        fa, fb = a.get("tot_medio"), b.get("tot_medio")
        if not fa or not fb:
            avv("⚠ %s: manca un numero" % nome)
            return None
        inf("⭐ %-22s %s %.3f → %s %.3f Mbit/s  ⇒ **%.2f×**"
            % (nome, x, fa, y, fb, fb / fa))
        return fb / fa

    q = {"lettore": coppia("il LETTORE", "A1", "A2", "lettore"),
         "cure": coppia("le CURE", "A2", "A3", "cure"),
         "scena": coppia("la SCENA", "A3", "A4", "scena")}
    # ⛔ E IL «DA UN CAPO ALL'ALTRO» PARTE DAL PRIMO BRACCIO CHE HA DIPINTO,
    #    non dal primo dell'elenco: `[M]` 24 agosto 2026 A1 ha dato 2,427
    #    Mbit/s con ZERO fotogrammi, e «A1 → A4 = 0,3×» sarebbe stato il
    #    rapporto fra il costo del niente e una scena vera.  ⚠ Un numero che
    #    sembra una risposta, in fondo alla tabella giusta.
    vivi = [x for x in ("A1", "A2", "A3", "A4")
            if esiti.get(x) and esiti[x].get("scena_si_muove") is True
            and esiti[x].get("tot_medio")]
    if len(vivi) >= 2:
        p, u = esiti[vivi[0]], esiti[vivi[-1]]
        inf("⭐⭐⭐ e da un capo all'altro (bracci che hanno DIPINTO): %s %.3f → "
            "%s %.3f Mbit/s ⇒ **%.1f×**"
            % (vivi[0], p["tot_medio"], vivi[-1], u["tot_medio"],
               p["tot_medio"] / u["tot_medio"]))
    else:
        avv("⚠ meno di due bracci hanno dipinto: NON dichiaro il capo-a-capo")
    return {"bracci": esiti, "spartizione": q, "fase9": FASE9}, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ 3-quater · IL CASO PEGGIORE VERO — quanto chiede UNA sessione
#
# `[?]` Il primo giro della fase 10 dichiara: *«nessuna delle mie scene ha
# entropia vera — le bande di colore si comprimono benissimo»*.  ⇒ Nessuno ha
# mai misurato quanto puo' chiedere una sessione sola nel caso peggiore onesto.
#
# ⛔ E NON SI FA UNA MEDIA.  Fase 9 §14.2 ha gia' dimostrato che il rapporto
#    fra due scene non e' una costante: 0,36x sul gradiente retinato, 0,76x sul
#    film con la grana, ⛔ **1,7x IN SU** sul desktop vero.  ⇒ si misurano piu'
#    scene, si stampa la riga di ciascuna, e il caso peggiore e' **il massimo**,
#    non la media.
#
# ⭐ E ogni scena dichiarata «ad alta entropia» passa da G6: chi la battezza
#   non e' chi la giudica.
#
# ⚠⚠ `[?]` IL BUCO DICHIARATO, e vale per TUTTE le scene di questo banco e per
#     quelle di fase 9 §14.2: **il lettore paga anche lui sulla stessa GPU**.
#     `rumore.mp4` e' un H.264 da 500 Mbit/s, e mpv lo decodifica con la
#     `renderD128` — la stessa che codifica il nostro flusso.  ⇒ una parte del
#     ritmo che si legge non e' del codificatore: e' contesa col decodificatore.
#     ⛔ Non e' stato separato, e NON si finge che non ci sia: la grandezza che
#        questo banco misura e' **quanto chiede il prodotto mentre l'utente
#        guarda un video**, che e' il caso vero, non «quanto costerebbe la
#        stessa immagine se arrivasse dal nulla».
# ═══════════════════════════════════════════════════════════════════════════
def entropia(secondi=30, tela="2560x1080", quali=None, cure="accese"):
    quali = quali or ["desktop", "duro", "grana", "testo", "mandel", "vita",
                      "rumore", "bandiera"]
    log("3-quater · ⭐⭐⭐ IL CASO PEGGIORE VERO — %d scene, e nessuna media"
        % len(quali))
    buono, m = server_con(cure)
    (ok if buono else ko)(m)
    if not buono:
        return None, ["il server non ha le cure chieste: %s" % m[:150]]
    # ⛔ Le scene che non ci sono si DICHIARANO e si tolgono, invece di far
    #    fallire il braccio a meta' campagna con un rosso che sembra un difetto.
    vive = []
    for q in quali:
        f = SCENE[q]["file"]
        if f is None:
            vive.append(q)
            continue
        rc, out, _ = rem("test -s '%s' && echo SI || echo NO" % f)
        if "SI" in out:
            vive.append(q)
        else:
            avv("⚠ la scena «%s» non c'e' (%s): la TOLGO e lo dico, invece di "
                "misurare un'assenza" % (q, f))
    t, rossi = scene(secondi=secondi, quali=vive, tela=tela, cure=cure)
    if not t:
        return None, rossi

    # ── ⭐ LA TABELLA, ordinata per quanto chiede ──────────────────────────
    log("⭐⭐⭐ QUANTO CHIEDE UNA SESSIONE — ordinate dalla piu' dura")
    print("   | scena | entropia? | ⭐ MEDIA sul filo | picco | carico utile | "
          "fot | byte/fot |")
    print("   |---|---|---|---|---|---|---|")
    righe = sorted(t.values(), key=lambda e: -(e.get("tot_medio") or 0))
    for e in righe:
        print("   | %s | %s | **%.3f** | %.3f | %.3f | %d | %s |"
              % (e["scena"],
                 {True: "⭐ sì", False: "⛔ SMASCHERATA",
                  None: "⚠ ignota"}.get(e.get("entropia_confermata"), "—")
                 if e.get("entropia_dichiarata_alta") else "non dichiarata",
                 e.get("tot_medio") or 0, e.get("tot_picco") or 0,
                 e.get("utile_mbit") or 0, e["fotogrammi"],
                 "%.0f" % e["byte_per_fot"] if e["byte_per_fot"] else "—"))

    # ── ⛔ IL CASO PEGGIORE: il MASSIMO fra quelle CONFERMATE ──────────────
    #    ⚠ Una scena smascherata da G6 NON entra: e' il punto di tutta la
    #      guardia.  E se nessuna e' confermata, il banco NON dichiara un caso
    #      peggiore — dice che non ce l'ha.
    buone = [e for e in righe if e.get("entropia_confermata") is True
             and e.get("tot_medio")]
    fuori = {"tabella": t, "caso_peggiore": None}
    if not buone:
        ko("⛔ NESSUNA scena ha superato G6: non ho un caso peggiore da "
           "dichiarare, e NON metto al suo posto la meno leggera")
        rossi.append("nessuna scena ad alta entropia confermata")
        return fuori, rossi
    peggio = max(buone, key=lambda e: e["tot_medio"])
    fuori["caso_peggiore"] = peggio
    log("⭐⭐⭐ LA RIGA CHE CHIUDE")
    inf("il CASO PEGGIORE per sessione: scena «%s» ⇒ **%.3f Mbit/s** sul filo "
        "(picco %.3f), %s byte/fotogramma"
        % (peggio["scena"], peggio["tot_medio"], peggio.get("tot_picco") or 0,
           "%.0f" % peggio["byte_per_fot"] if peggio["byte_per_fot"] else "—"))
    inf("⭐ ×10 sessioni sul caso peggiore: **%.1f Mbit/s** di media, **%.1f** "
        "se andassero tutte in picco insieme"
        % (peggio["tot_medio"] * 10, (peggio.get("tot_picco") or 0) * 10))
    # ⛔ E il confronto col filo si fa col numero MISURATO, non col dichiarato.
    inf("⛔ contro il filo: `enp7s0` dichiara 10 000 Mbit/s e UDP nudo su «%s» "
        "ne ha fatti `[M]` 11 900 con un filo solo ⇒ dieci sessioni sul caso "
        "peggiore sono lo **%.2f %%** del filo misurato" % (DEV,
        peggio["tot_medio"] * 10 * 100 / 11900.0))
    # ⛔⛔ E IL TETTO DEL PRODOTTO — che e' PER FIGLIO, e nessuno somma.
    inf("⛔⛔ e contro il TETTO DEL PRODOTTO (`--tetto-banda-mbit`, pavimento "
        "20 Mbit/s): il caso peggiore ne chiede il **%.0f %%** DA SOLO — e il "
        "tetto e' PER FIGLIO: dieci figli lo pagano dieci volte (200 Mbit/s), "
        "perche' in tutto `src/` non c'e' nessun contatore aggregato"
        % (peggio["tot_medio"] * 100 / 20.0))
    return fuori, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · IL TETTO DEL FILO — si MISURA, non si deduce
# ═══════════════════════════════════════════════════════════════════════════
def tetto(secondi=5, fili_max=8, carico=1200):
    log("3 · ⭐ IL TETTO DEL FILO — «una scheda che dichiara 10 Gbit/s non porta "
        "10 Gbit/s di QUIC in spazio utente»")
    rc, out, _ = rem("cat /sys/class/net/%s/speed /sys/class/net/%s/duplex "
                     "/sys/class/net/%s/mtu 2>/dev/null" % (VIETATA, VIETATA, VIETATA))
    p = out.split()
    inf("⛔ `ethtool` NON c'e' su questa macchina (preambolo): la velocita' "
        "negoziata si legge da /sys")
    inf("%s: %s Mbit/s, %s duplex, MTU %s" % (VIETATA, p[0] if p else "?",
                                              p[1] if len(p) > 1 else "?",
                                              p[2] if len(p) > 2 else "?"))
    rc, out, _ = rem("nproc; grep -m1 'model name' /proc/cpuinfo | cut -d: -f2")
    inf("CPU: %s" % " · ".join(x.strip() for x in out.splitlines()))

    p_tara = tara_regola()
    aperto = pozzo_apri()
    (ok if aperto else avv)("il pozzo sulla %d: %s" % (
        p_tara, "aperto — nessun ICMP nascera'" if aperto
        else "⚠ NON aperto: il tetto uscira' PIU' BASSO del vero"))
    righe, rossi = [], []
    n = 1
    while n <= fili_max:
        metro_azzera()
        prima = leggi()
        g = getto(31001, carico, 0, secondi, fili=n)
        dopo = leggi()
        if g is None:
            ko("⛔ il getto a %d fili non ha risposto" % n)
            rossi.append("getto muto a %d fili" % n)
            break
        d, perche = varco(prima, dopo)
        if d is None:
            ko("⛔ %d fili: %s" % (n, perche))
            rossi.append(perche)
            break
        # ⛔ Il ritmo si divide per la durata DEL GETTO, non per la mia
        #    finestra: fra le due letture ci sono due `ssh`, e a 10 Gbit/s
        #    mezzo secondo di sfalso vale 600 MB.  ⚠ I BYTE invece sono esatti
        #    (la taratura lo dimostra a 0,0000 %): l'unico errore possibile qui
        #    e' l'orologio, e si toglie usando quello giusto.
        letto = mbit(d.get("tara", 0), g["secondi"])
        righe.append({"fili": n, "getto_mbit": g["mbit_L3"], "metro_mbit": letto,
                      "datagrammi": g["datagrammi"],
                      "icmp": d.get("irraggiungibili", 0)})
        ok("%d filo/i → getto %.0f Mbit/s · metro %.0f Mbit/s · %d datagrammi "
           "· ICMP %d byte %s"
           % (n, g["mbit_L3"], letto or 0, g["datagrammi"],
              d.get("irraggiungibili", 0),
              "⭐ (il pozzo tiene)" if d.get("irraggiungibili", 0) == 0
              else "⚠ il pozzo NON tiene: il tetto esce piu' basso del vero"))
        n *= 2
    pozzo_chiudi()
    if not righe:
        return None, rossi + ["nessun punto"]
    massimo = max(r["metro_mbit"] or 0 for r in righe)
    log("⭐ IL TETTO MISURATO — UDP nudo su `%s`, %d byte per datagramma" % (DEV, carico))
    inf("massimo: **%.0f Mbit/s** (%.2f Gbit/s) con %d fili"
        % (massimo, massimo / 1000.0,
           max(righe, key=lambda r: r["metro_mbit"] or 0)["fili"]))
    avv("⛔ E' un limite SUPERIORE per QUIC: questo getto non cifra, non tiene "
        "stato e non ritrasmette.  Il tetto vero di QUIC sta sotto, e la "
        "distanza fra i due e' il costo del protocollo.")
    return {"nic_mbit": int(p[0]) if p and p[0].strip().isdigit() else None,
            "punti": righe, "massimo_mbit": massimo}, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 5 · LA CONTESA — «quando il filo e' pieno, CHI PAGA?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ Le cure della fase 9 (soglia sulla coda 100 ms, regolatore del ritmo,
#     linea morta) sono ACCESE per predefinito e sono tarate su **una** sessione
#     che vede una rete cattiva.  Dieci sessioni che si contendono lo stesso
#     filo si vedono a vicenda **come una rete cattiva**: ognuna cala il ritmo,
#     e nessuna sa che il vicino e' il problema.
#
# ⛔⛔ QUI SERVE ANCHE IL LUCCHETTO DEL `netem`: la disciplina di
#     un'interfaccia e' UNA SOLA e il secondo che la mette cancella la radice
#     del primo, in silenzio.
#
# ⭐ E la disciplina e' quella di `07-b65-datagram.py`: `prio` a quattro bande,
#    la stretta sulla quarta, due filtri `u32` sulla SOLA mia porta.  ⛔ `lo`
#    la usano tutti: una stretta sulla radice strozzerebbe anche i vicini.
GUARDIANO = LAV + "/.b90-guardiano.pid"


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def guardiano_arma(secondi):
    guardiano_disarma()
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    ok("guardiano armato per %d s (pid %s): la rete torna com'era ANCHE se muoio"
       % (secondi, out.strip() or "?"))


def guardiano_disarma():
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True):
    guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    pulita = "netem" not in q and "tbf" not in q and "prio" not in q
    if dillo:
        (ok if pulita else ko)("«%s» adesso e': %s" % (DEV, q or "(nessuna)"))
        inf("%s (ssh + la sessione dell'utente): %s"
            % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return pulita


def stringi(mbit_s):
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem rate %dmbit"
        % (DEV, mbit_s),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    for c in passi:
        rc, _, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc ha rifiutato: %s" % err[:200]
    return True, qdisc()


# ⛔ Gli aghi sono le righe VERE del prodotto, trovate in `webtransport.c` e
#    `rcp.c`, non parole generiche: `[M]` 24 agosto 2026 l'ago «ritmo» da solo
#    trovava una riga di **documentazione** all'accensione del server e contava
#    1 su un server che non aveva ancora spedito niente.
SPIE = {
    "soglia_sopra": "la coda del video passa SOPRA la soglia",   # webtransport.c:3803
    "soglia_sotto": "la coda del video torna SOTTO la soglia",   # webtransport.c:3788
    "ritmo_scende": "il ritmo SCENDE",                           # webtransport.c:4419
    "ritmo_risale": "il ritmo RISALE",                           # webtransport.c:4445
    "linea_morta": "linea-morta ",                               # webtransport.c:4668
    "abbandoni": "ABBANDONATO NELLA CODA",                       # rcp.c:3867
    "chiavi": "SPEDITO: CHIAVE",                                 # rcp.c:4199
}


def spie_conta(riga0):
    fuori = {}
    for nome, ago in SPIE.items():
        rc, out, _ = root("bash -c \"tail -n +%d %s 2>/dev/null | grep -cF '%s' || true\""
                          % (riga0 + 1, registro(), ago))
        s = out.strip().split()
        fuori[nome] = int(s[0]) if s and s[0].isdigit() else None
    return fuori


def contesa(quante=3, stretta=60, secondi=25, tela="2560x1080"):
    log("4 · ⭐⭐ LA CONTESA — «quando il filo e' pieno, CHI PAGA?»")
    inf("stretta %d Mbit/s sulla SOLA porta %d, %d s per braccio, scena «duro»"
        % (stretta, PORTA, secondi))
    avv("⛔ le cure della fase 9 sono ACCESE per predefinito (CODER §2-bis): "
        "questo giro NON le spegne, perche' la domanda e' proprio che cosa "
        "fanno quando il vicino e' il problema")
    esiti, rossi = {}, []
    if not utenti_crea(quante):
        return None, ["gli utenti della contesa non si sono creati"]
    guardiano_arma(secondi * (quante + 2) * 3 + 900)
    try:
        buono, q = stringi(stretta)
        if not buono:
            ko(q)
            return None, [q]
        ok("stretta messa: %s" % q.replace("\n", " | "))
        for n in range(1, quante + 1):
            log("braccio: **%d sessione/i insieme** sullo stesso filo da %d Mbit/s"
                % (n, stretta))
            vive = 0
            for i in range(n):
                ap, det = sessione_apri("c%d" % i, secondi + 240, tela,
                                        utente=UTENTI[i][0])
                if not ap:
                    ko("⛔ la sessione di %s non si e' aperta" % UTENTI[i][0])
                    print(det[-400:])
                    rossi.append("sessione %s non aperta a n=%d" % (UTENTI[i][0], n))
                else:
                    vive += 1
                time.sleep(2)
            time.sleep(5)
            porte = porte_clienti()
            inf("porte dei clienti: %s" % (porte or "⚠ nessuna"))
            # ⛔ Se non sono nate tutte, il braccio NON e' quel che dice di
            #    essere: si dichiara e non si finge.
            if vive != n:
                ko("⛔ volevo %d sessioni e ne ho %d: questo braccio NON e' «n=%d»"
                   % (n, vive, n))
            for i in range(n):
                scena_accendi("duro", utente=UTENTI[i][0])
            # ⛔ E QUI SI ASPETTA CHE SPEDISCANO, non che «siano partite».
            quante_ok, porte_vere = attendi_sessioni(n)
            riga0 = righe_registro()
            if riga0 is None:
                ko("⛔ registro non letto: NON giudico questo braccio")
                rossi.append("registro non letto a n=%d" % n)
                sessioni_chiudi()
                continue
            metro_azzera()
            letture = campiona(secondi, 1.0, registro(), riga0)
            spie = spie_conta(riga0)
            scena_spegni(n)
            sessioni_chiudi()
            if letture is None:
                ko("⛔ una lettura e' mancata: NON giudico questo braccio")
                rossi.append("lettura mancata a n=%d" % n)
                continue
            d, perche = varco(letture[0], letture[-1])
            if d is None:
                ko("⛔ %s" % perche)
                rossi.append(perche)
                continue
            g1, m1 = g1_flusso_partito(d)
            if g1 is None:
                ko("G1 · %s" % m1)
                rossi.append("G1 a n=%d" % n)
                continue
            per_ses = sorted(((mbit(b, d["secondi"]), p)
                              for p, (b, _) in d["ses_giu"].items()), reverse=True)
            tot = mbit(d.get("mio_giu", 0) + d.get("mio_su", 0), d["secondi"])
            esiti[n] = {"sessioni_chieste": n, "sessioni_vive": vive,
                        "sessioni_che_spedivano": quante_ok,
                        "sessioni_viste": len(per_ses), "totale_mbit": tot,
                        "per_sessione": [{"porta": p, "mbit": m} for m, p in per_ses],
                        "fotogrammi": d.get("spediti"),
                        "byte_per_fot": (d["byte_utili"] / d["spediti"])
                                        if (d.get("spediti") and d.get("byte_utili")) else None,
                        "spie": spie}
            (ok if len(per_ses) == n else ko)(
                "%d chieste, ⭐ **%d che spedivano** · totale **%.2f Mbit/s** · "
                "per sessione: %s"
                % (n, len(per_ses), tot or 0,
                   ", ".join("%.2f" % m for m, _ in per_ses) or "—"))
            if len(per_ses) != n:
                rossi.append("braccio n=%d ne ha viste %d: NON e' «n=%d»"
                             % (n, len(per_ses), n))
            inf("fotogrammi consegnati in tutto: %s · byte/fotogramma %s"
                % (d.get("spediti"),
                   "%.0f" % esiti[n]["byte_per_fot"] if esiti[n]["byte_per_fot"] else "—"))
            inf("le spie delle cure: %s"
                % ", ".join("%s=%s" % (k, v) for k, v in sorted(spie.items())))
    finally:
        sessioni_chiudi()
        if not rimetti():
            rossi.append("⛔ la rete NON si e' rimessa")
    return esiti, rossi


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO `--certifica` — un banco non e' finito finche' non lo si e'
#      visto dare ROSSO.  I guasti si INNESTANO e si FANNO GIRARE.
# ═══════════════════════════════════════════════════════════════════════════
def _lettura(t, lo_tx, mio_giu, mio_su, tutto, ses_giu=None, ses_su=None,
             spediti=None, byte_utili=None, lo_pkt=0):
    return {"t": t, "lo_tx": lo_tx, "lo_pkt": lo_pkt,
            "cont": {"mio_giu": (mio_giu, 0), "mio_su": (mio_su, 0),
                     "tutto": (tutto, 0)},
            "giu": {p: (b, 0) for p, b in (ses_giu or {}).items()},
            "su": {p: (b, 0) for p, b in (ses_su or {}).items()},
            "spediti": spediti, "byte_utili": byte_utili, "righe": 0}


def certifica():
    log("⛔⛔ `--certifica` — SANO → GUASTO → RISANATO, e i guasti GIRANO")
    conti = {"sano": 0, "guasto": 0, "risanato": 0}
    rossi = []

    def prova(nome, atteso, fatto, mostra=""):
        buono = (atteso == fatto)
        (ok if buono else ko)("%-46s atteso %-8s ⇒ %s   %s"
                              % (nome, atteso, fatto, mostra))
        if not buono:
            rossi.append(nome)
        return buono

    # ── G1 · il contatore letto PRIMA che il flusso parta ──────────────────
    log("G1 · il contatore letto PRIMA che il flusso parta ⇒ zero byte")
    A = _lettura(1000.0, 1_000_000, 100_000, 10_000, 1_200_000,
                 {50001: 100_000}, {50001: 10_000}, spediti=300, byte_utili=600_000)
    B = _lettura(1010.0, 1_500_000, 600_000, 60_000, 1_800_000,
                 {50001: 600_000}, {50001: 60_000}, spediti=900, byte_utili=1_800_000)
    d, _ = varco(A, B)
    g, m = g1_flusso_partito(d)
    conti["sano"] += prova("sano: 660 000 byte in 10 s", True, g, m)
    # ⛔ IL GUASTO: le due letture sono IDENTICHE (l'ho letto prima che partisse)
    Bg = _lettura(1010.0, 1_000_000, 100_000, 10_000, 1_200_000,
                  {50001: 100_000}, {50001: 10_000}, spediti=300, byte_utili=600_000)
    dg, _ = varco(A, Bg)
    g, m = g1_flusso_partito(dg)
    conti["guasto"] += prova("⛔ guasto: zero byte ⇒ si RIFIUTA (None)", None, g, m)
    # ⚠ e il quasi-zero: un filo di rumore non e' un flusso
    Bq = _lettura(1010.0, 1_002_000, 100_900, 10_100, 1_202_000,
                  {50001: 100_900}, {50001: 10_100}, spediti=1, byte_utili=300)
    dq, _ = varco(A, Bq)
    g, m = g1_flusso_partito(dq)
    conti["guasto"] += prova("⛔ guasto: 1 000 byte in 10 s ⇒ si RIFIUTA", None, g, m)
    d, _ = varco(A, B)
    g, m = g1_flusso_partito(d)
    conti["risanato"] += prova("risanato", True, g, m)

    # ── G2 · il contatore che si azzera o va indietro ──────────────────────
    log("G2 · il contatore che si AZZERA o va INDIETRO")
    d, m = varco(A, B)
    conti["sano"] += prova("sano: i contatori vanno avanti", True, d is not None, m)
    # ⛔ IL GUASTO 1: `nft` azzerato da un vicino ⇒ i contatori tornano a zero
    Bz = _lettura(1010.0, 1_500_000, 5_000, 500, 6_000,
                  {50001: 5_000}, {50001: 500}, spediti=900, byte_utili=1_800_000)
    dz, mz = varco(A, Bz)
    conti["guasto"] += prova("⛔ guasto: nft azzerato ⇒ None, non un negativo",
                             None, dz, mz)
    # ⛔ IL GUASTO 2: l'interfaccia va indietro (riavvio, o lettura di un'altra
    #    macchina).  ⚠ Senza questa guardia un `unsigned` darebbe 18 exabyte.
    Bi = _lettura(1010.0, 900_000, 600_000, 60_000, 1_800_000,
                  {50001: 600_000}, {50001: 60_000}, spediti=900, byte_utili=1_800_000)
    di, mi = varco(A, Bi)
    conti["guasto"] += prova("⛔ guasto: lo/tx_bytes indietro ⇒ None", None, di, mi)
    # ⛔ IL GUASTO 3: il tempo non e' andato avanti (due letture nello stesso
    #    istante) ⇒ divisione per zero, cioe' un numero infinito
    Bt = _lettura(1000.0, 1_500_000, 600_000, 60_000, 1_800_000,
                  {50001: 600_000}, {50001: 60_000}, spediti=900, byte_utili=1_800_000)
    dt, mt = varco(A, Bt)
    conti["guasto"] += prova("⛔ guasto: due letture allo stesso istante ⇒ None",
                             None, dt, mt)
    d, m = varco(A, B)
    conti["risanato"] += prova("risanato", True, d is not None, m)

    # ── G3 · la scena che non si muove ─────────────────────────────────────
    log("G3 · la scena che NON SI MUOVE, smascherata dai byte per fotogramma")
    d, _ = varco(A, B)
    g, m = g3_scena_si_muove(d)
    conti["sano"] += prova("sano: 600 fotogrammi in 10 s", True, g, m)
    # ⛔ IL GUASTO: il filo passa lo stesso (QUIC + audio PCM) ma la scena e'
    #    ferma: 2 fotogrammi in 10 s.  ⚠ Senza G3 il banco scriverebbe
    #    «il desktop vero costa 0,5 Mbit/s» su un desktop che non c'era.
    Bf = _lettura(1010.0, 1_500_000, 600_000, 60_000, 1_800_000,
                  {50001: 600_000}, {50001: 60_000}, spediti=302, byte_utili=601_000)
    df, _ = varco(A, Bf)
    g, m = g3_scena_si_muove(df)
    conti["guasto"] += prova("⛔ guasto: 2 fotogrammi in 10 s ⇒ FALSO", False, g, m)
    # ⛔ IL GUASTO 2: il registro non e' stato letto ⇒ NON si dice «zero»
    Bn = _lettura(1010.0, 1_500_000, 600_000, 60_000, 1_800_000,
                  {50001: 600_000}, {50001: 60_000}, spediti=None, byte_utili=None)
    dn, _ = varco(A, Bn)
    g, m = g3_scena_si_muove(dn)
    conti["guasto"] += prova("⛔ guasto: registro non letto ⇒ si RIFIUTA", None, g, m)
    d, _ = varco(A, B)
    g, m = g3_scena_si_muove(d)
    conti["risanato"] += prova("risanato", True, g, m)

    # ── G4 · la somma per sessione che non torna ───────────────────────────
    log("G4 · la SOMMA per sessione contro il totale della mia porta")
    A3 = _lettura(1000.0, 0, 0, 0, 0, {}, {})
    B3 = _lettura(1010.0, 1_000_000, 900_000, 90_000, 1_000_000,
                  {50001: 300_000, 50002: 300_000, 50003: 300_000},
                  {50001: 30_000, 50002: 30_000, 50003: 30_000},
                  spediti=900, byte_utili=800_000)
    d3, _ = varco(A3, B3)
    g, m = g4_somma_torna(d3)
    conti["sano"] += prova("sano: tre sessioni, la somma torna", True, g, m)
    # ⛔ IL GUASTO: l'insieme dinamico ha perso una sessione (troppe porte, o
    #    una scadenza scaduta) ⇒ la somma e' un terzo sotto il totale
    B3g = _lettura(1010.0, 1_000_000, 900_000, 90_000, 1_000_000,
                   {50001: 300_000, 50002: 300_000},
                   {50001: 30_000, 50002: 30_000},
                   spediti=900, byte_utili=800_000)
    d3g, _ = varco(A3, B3g)
    g, m = g4_somma_torna(d3g)
    conti["guasto"] += prova("⛔ guasto: una sessione persa ⇒ ROSSO", False, g, m)
    # ⚠ e il caso al limite: 1,5 % di scarto sta DENTRO la tolleranza del 2 %
    B3l = _lettura(1010.0, 1_000_000, 900_000, 90_000, 1_000_000,
                   {50001: 300_000, 50002: 300_000, 50003: 285_150},
                   {50001: 30_000, 50002: 30_000, 50003: 30_000},
                   spediti=900, byte_utili=800_000)
    d3l, _ = varco(A3, B3l)
    g, m = g4_somma_torna(d3l)
    conti["sano"] += prova("sano al limite: -1,5 % sta dentro il 2 %", True, g, m)
    d3, _ = varco(A3, B3)
    g, m = g4_somma_torna(d3)
    conti["risanato"] += prova("risanato", True, g, m)

    # ── G5 · il metro contro se stesso ─────────────────────────────────────
    log("G5 · `nft tutto` contro `%s/tx_bytes` — due contatori, stessi pacchetti" % DEV)
    g, m = g5_metro_su_se_stesso(d3)
    conti["sano"] += prova("sano: i due contatori coincidono", True, g, m)
    # ⛔ IL GUASTO: una regola `nft` cancellata a meta' giro ⇒ `tutto` conta
    #    meta' di quel che l'interfaccia ha visto passare
    B5 = _lettura(1010.0, 1_000_000, 900_000, 90_000, 500_000,
                  {50001: 300_000, 50002: 300_000, 50003: 300_000},
                  {50001: 30_000, 50002: 30_000, 50003: 30_000},
                  spediti=900, byte_utili=800_000)
    d5, _ = varco(A3, B5)
    g, m = g5_metro_su_se_stesso(d5)
    conti["guasto"] += prova("⛔ guasto: regola nft persa ⇒ ROSSO", False, g, m)
    g, m = g5_metro_su_se_stesso(d3)
    conti["risanato"] += prova("risanato", True, g, m)

    # ══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ G6 · L'ENTROPIA DICHIARATA, e i byte per fotogramma che la smentiscono
    # ══════════════════════════════════════════════════════════════════════
    log("G6 · ⛔ una scena battezzata «ad alta entropia» che si comprime benissimo")
    # sano: la grana di fase 9 — 239 129 byte/fotogramma su 700 fotogrammi
    Ag = _lettura(1000.0, 10_000_000, 1_000_000, 100_000, 11_000_000,
                  {50001: 1_000_000}, {50001: 100_000},
                  spediti=0, byte_utili=0)
    Bg = _lettura(1030.0, 190_000_000, 175_000_000, 3_000_000, 195_000_000,
                  {50001: 175_000_000}, {50001: 3_000_000},
                  spediti=700, byte_utili=700 * 239_129)
    dg, _ = varco(Ag, Bg)
    g, m = g6_entropia_vera(dg, True)
    conti["sano"] += prova("sano: 239 129 byte/fot dichiarati alti ⇒ CONFERMATO",
                           True, g, m)
    # ⛔ IL GUASTO 1 — LA BANDIERA: 900 fotogrammi vivissimi da 268 byte l'uno.
    #    ⚠ G3 dice VERDE (la scena si muove per davvero, 30 al secondo) e G6
    #      dice ROSSO: sono due domande diverse, e senza la seconda la bandiera
    #      entrerebbe nel budget come «caso peggiore» a 0,06 Mbit/s.
    Bb = _lettura(1030.0, 20_000_000, 5_000_000, 500_000, 21_000_000,
                  {50001: 5_000_000}, {50001: 500_000},
                  spediti=900, byte_utili=900 * 268)
    db, _ = varco(Ag, Bb)
    g3b, m3b = g3_scena_si_muove(db)
    conti["sano"] += prova("  ⚠ e G3 sulla stessa scena dice VERDE (si muove)",
                           True, g3b, m3b)
    g, m = g6_entropia_vera(db, True)
    conti["guasto"] += prova("⛔ guasto: 268 byte/fot spacciati per duri ⇒ FALSO",
                             False, g, m)
    # ⛔ IL GUASTO 2 — il gradiente retinato, 23 695 byte/fot: e' la scena piu'
    #    dura di fase 9 DOPO la grana, e sta appena SOPRA la soglia.  ⚠ Serve a
    #    far vedere che la soglia non e' messa a caso: qui deve passare.
    Br = _lettura(1030.0, 40_000_000, 25_000_000, 800_000, 41_000_000,
                  {50001: 25_000_000}, {50001: 800_000},
                  spediti=900, byte_utili=900 * 23_695)
    dr, _ = varco(Ag, Br)
    g, m = g6_entropia_vera(dr, True)
    conti["sano"] += prova("  sano al margine: 23 695 byte/fot ⇒ passa", True, g, m)
    # ⛔ IL GUASTO 3 — la stessa scena su una tela PICCOLA: 1280x540 ha un
    #    quarto dei pixel, e una soglia fissa la respingerebbe a torto.
    g, m = g6_entropia_vera(dr, True, tela="1280x540")
    conti["guasto"] += prova("  la soglia scala coi pixel (1280x540)", True, g, m)
    # ⛔ IL GUASTO 4 — il registro non letto: `None`, non «e' facile»
    Bn = _lettura(1030.0, 190_000_000, 175_000_000, 3_000_000, 195_000_000,
                  {50001: 175_000_000}, {50001: 3_000_000},
                  spediti=None, byte_utili=None)
    dn, _ = varco(Ag, Bn)
    g, m = g6_entropia_vera(dn, True)
    conti["guasto"] += prova("⛔ guasto: registro non letto ⇒ None, non «bassa»",
                             None, g, m)
    # ⛔ IL GUASTO 5 — zero fotogrammi: non e' entropia bassa, e' assenza
    Bz2 = _lettura(1030.0, 12_000_000, 1_500_000, 150_000, 13_000_000,
                   {50001: 1_500_000}, {50001: 150_000},
                   spediti=0, byte_utili=0)
    dz2, _ = varco(Ag, Bz2)
    g, m = g6_entropia_vera(dz2, True)
    conti["guasto"] += prova("⛔ guasto: zero fotogrammi ⇒ None (e' G3 che parla)",
                             None, g, m)
    g, m = g6_entropia_vera(dg, True)
    conti["risanato"] += prova("risanato", True, g, m)

    # ══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ G7 · IL CONFRONTO SLEALE — la ricostruzione sbagliata e il §2-bis
    # ══════════════════════════════════════════════════════════════════════
    log("G7 · ⛔⛔ due misure si confrontano solo se sono della STESSA cosa")
    p9 = dict(FASE9["profilo"])
    conti["sano"] += prova("sano: profilo identico a fase 9 ⇒ lecito",
                           True, *(g7_confronto_leale(dict(p9), p9)))
    # ⛔ IL GUASTO 1 — LA RICOSTRUZIONE SBAGLIATA: tela diversa
    conti["guasto"] += prova(
        "⛔ guasto: tela 1920x1080 contro 2560x1080 ⇒ RIFIUTA", False,
        *(g7_confronto_leale(dict(p9, tela="1920x1080"), p9)))
    # ⛔ IL GUASTO 2 — lettore diverso: lo STESSO file mostrato in due modi
    conti["guasto"] += prova(
        "⛔ guasto: mpv contro firefox sullo stesso file ⇒ RIFIUTA", False,
        *(g7_confronto_leale(dict(p9, lettore="mpv"), p9)))
    # ⛔ IL GUASTO 3 — scena diversa: e' la discordanza da DIECI VOLTE, in una riga
    conti["guasto"] += prova(
        "⛔ guasto: «duro» contro «grana» ⇒ RIFIUTA (e' il 44,6 contro il 4,5)",
        False, *(g7_confronto_leale(dict(p9, scena="duro"), p9)))
    # ⛔⛔ IL GUASTO 4 — IL DIVIETO DI `CODER.md` §2-bis: cure accese contro spente
    g, m = g7_confronto_leale(dict(p9, cure="accese"), p9)
    conti["guasto"] += prova("⛔⛔ guasto: cure ACCESE contro SPENTE ⇒ §2-bis",
                             False, g, m)
    conti["guasto"] += prova("   e la riga lo dice a chiare lettere", True,
                             "§2-bis" in m, m[:70])
    # ⛔ IL GUASTO 5 — piu' cose diverse insieme, cure comprese: vince il §2-bis
    #    ma le altre differenze si dicono lo stesso.
    g, m = g7_confronto_leale(dict(p9, cure="accese", scena="duro"), p9)
    conti["guasto"] += prova("⛔ guasto: cure E scena ⇒ §2-bis, e nomina l'altra",
                             True, ("§2-bis" in m and "scena" in m), m[:70])
    # ⛔ IL GUASTO 6 — un campo NON DICHIARATO: `None`, non «uguale»
    conti["guasto"] += prova(
        "⛔ guasto: campo «cure» assente ⇒ None, non «uguali»", None,
        *(g7_confronto_leale(dict(p9, cure=None), p9)))
    conti["guasto"] += prova(
        "⛔ guasto: profilo mancante del tutto ⇒ None", None,
        *(g7_confronto_leale(None, p9)))
    conti["risanato"] += prova("risanato", True,
                               *(g7_confronto_leale(dict(p9), p9)))
    # ⭐ E IL CONFRONTO A CAMPO VARIABILE — quello che isola UNA variabile:
    #   due bracci che differiscono per il lettore E per le cure non isolano
    #   niente, e `coppia()` in `fase9()` lo chiede proprio cosi'.
    campi_senza_lettore = [c for c in CAMPI_PROFILO if c != "lettore"]
    conti["sano"] += prova(
        "sano: isolo il LETTORE, il resto combacia ⇒ lecito", True,
        *(g7_confronto_leale(dict(p9, lettore="mpv"), p9,
                             campi=campi_senza_lettore)))
    conti["guasto"] += prova(
        "⛔ guasto: isolo il lettore ma cambiano anche le cure ⇒ §2-bis", False,
        *(g7_confronto_leale(dict(p9, lettore="mpv", cure="accese"), p9,
                             campi=campi_senza_lettore)))

    # ══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LE CURE SI LEGGONO DAL PRODOTTO — e «non ho letto» non e' «spenta»
    # ══════════════════════════════════════════════════════════════════════
    log("⛔ `cure_verifica()` — il braccio che crede di aver spento le cure")
    vero = {"soglia_coda": True, "ritmo": True, "linea_morta": True,
            "audio_silenzio": True}
    falso = {k: False for k in vero}

    def finto(lette, attese):
        # ⛔ Si prova la LOGICA del verdetto senza la macchina: `cure_lette()`
        #    e' l'anello che parla con ssh, e qui si innesta il suo esito.
        globale = globals()
        vecchia = globale["cure_lette"]
        globale["cure_lette"] = lambda *a, **k: lette
        try:
            return cure_verifica(attese)
        finally:
            globale["cure_lette"] = vecchia

    conti["sano"] += prova("sano: chieste accese, il server dice accese",
                           True, *finto(vero, "accese"))
    conti["sano"] += prova("sano: chieste spente, il server dice spente",
                           True, *finto(falso, "spente"))
    # ⛔⛔ IL GUASTO CHE CONTA: ho chiesto spente e il server le ha ACCESE.
    #     ⚠ Senza questo controllo il braccio «cure spente» misurerebbe il
    #       prodotto curato e lo scriverebbe «cure spente»: e' il modo esatto
    #       in cui la discordanza da dieci volte si sarebbe riprodotta.
    conti["guasto"] += prova("⛔⛔ guasto: chieste SPENTE, il server le ha ACCESE",
                             False, *finto(vero, "spente"))
    conti["guasto"] += prova("⛔ guasto: UNA sola cura fuori posto ⇒ ROSSO",
                             False, *finto(dict(falso, ritmo=True), "spente"))
    conti["guasto"] += prova("⛔ guasto: una cura IGNOTA ⇒ None, non «spenta»",
                             None, *finto(dict(falso, linea_morta=None), "spente"))
    conti["guasto"] += prova("⛔ guasto: registro illeggibile ⇒ None",
                             None, *finto(None, "spente"))
    conti["risanato"] += prova("risanato", True, *finto(falso, "spente"))

    # ── `mbit()` non inventa ───────────────────────────────────────────────
    log("⛔ `mbit()` — «None non e' zero», e non si divide per zero")
    conti["sano"] += prova("sano: 1 250 000 byte in 1 s = 10 Mbit/s",
                           10.0, mbit(1_250_000, 1.0))
    conti["guasto"] += prova("⛔ guasto: byte None ⇒ None", None, mbit(None, 1.0))
    conti["guasto"] += prova("⛔ guasto: 0 secondi ⇒ None (non infinito)",
                             None, mbit(1_250_000, 0))
    conti["guasto"] += prova("⛔ guasto: secondi negativi ⇒ None",
                             None, mbit(1_250_000, -1))
    conti["risanato"] += prova("risanato", 10.0, mbit(1_250_000, 1.0))

    log("IL CONTO")
    inf("sano %d · guasto %d · risanato %d" % (conti["sano"], conti["guasto"],
                                               conti["risanato"]))
    if rossi:
        ko("⛔ %d prove della certificazione NON hanno fatto quel che era scritto: %s"
           % (len(rossi), ", ".join(rossi)))
        return 1
    ok("⭐ tutte le guardie hanno dato ROSSO sul loro guasto e verde sul sano")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# LA CHIUSURA — ⛔ si VERIFICA, non si dichiara
# ═══════════════════════════════════════════════════════════════════════════
def chiudi():
    log("⛔ LA CHIUSURA — «la lasci come l'hai trovata», e si verifica")
    sessioni_chiudi()
    scena_spegni()
    terreno("spegni")
    pulita = rimetti()
    via = metro_via()
    (ok if via else ko)("la tabella nft «%s» %s" % (TABELLA, "non c'e' piu'" if via
                                                    else "⛔ C'E' ANCORA"))
    rc, out, _ = rem("ss -uln 2>/dev/null | grep ':%d ' || true" % PORTA)
    (ok if not out.strip() else ko)("porta %d: %s" % (PORTA, out.strip() or "chiusa"))
    rc, out, _ = rem("pgrep -a remotix 2>/dev/null | grep -F '%s' || true" % ALBERO)
    (ok if not out.strip() else ko)("processi miei: %s" % (out.strip() or "nessuno"))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % DEV)
    inf("tc qdisc %s: %s" % (DEV, out.strip().replace("\n", " | ")))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s | head -1" % VIETATA)
    inf("tc qdisc %s: %s" % (VIETATA, out.strip()))
    inf("le porte dei vicini (si contano, non si toccano): %s" % vicine_conta())
    return 0 if (pulita and via) else 1


# ═══════════════════════════════════════════════════════════════════════════
def salva(nome, roba):
    os.makedirs(FUORI, exist_ok=True)
    p = os.path.join(FUORI, nome)
    with open(p, "w") as f:
        json.dump(roba, f, indent=1, ensure_ascii=False)
    inf("scritto %s" % p)


def principale():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("passo", nargs="?", default="stato",
                    choices=["stato", "terreno", "tara", "scene", "tetto",
                             "contesa", "audio", "fase9", "entropia",
                             "tutto", "chiudi", "rimetti"])
    ap.add_argument("--certifica", action="store_true")
    ap.add_argument("--secondi", type=float, default=30)
    ap.add_argument("--quante", type=int, default=3)
    ap.add_argument("--stretta", type=int, default=60)
    ap.add_argument("--tela", default="2560x1080")
    # ⛔ Serve a NON tenere il lucchetto per rifare quel che e' gia' fatto:
    #    gli altri agenti sono in coda dietro di me, e un giro che ripete la
    #    taratura per abitudine ruba minuti a chi aspetta.
    ap.add_argument("--salta", default="",
                    help="passi da saltare in «tutto», separati da virgola")
    ap.add_argument("--scene", default="",
                    help="quali scene misurare in «entropia», separate da virgola")
    # ⛔⭐ QUANTO SONO DISPOSTO AD ASPETTARE IL MIO TURNO, e non e' un dettaglio
    #     di comodita': `attesa` era **5400 s fissi**, e il 24 agosto 2026 un
    #     altro agente ha tenuto il lucchetto della GPU per 5 400 s **e l'ha
    #     rinnovato**.  ⇒ un giro che aspetta meno di quanto dura il turno di
    #     chi c'e' muore con un'eccezione invece di misurare, e la coda si
    #     rompe proprio quando e' piu' lunga.  ⚠ Aspettare NON e' gratis: chi
    #     alza questo numero deve sapere che sta in coda, non che sta fermo.
    ap.add_argument("--attesa", type=int, default=5400,
                    help="secondi che sono disposto ad aspettare il lucchetto")
    ap.add_argument("--senza-lucchetto", action="store_true",
                    help="⛔ SOLO per la messa a punto: i numeri di un giro "
                         "senza lucchetto NON valgono e non si riferiscono")
    a = ap.parse_args()

    if a.certifica:
        return certifica()

    if a.passo == "stato":
        log("Stato del banco 10-a4 — porta %d, utente %s" % (PORTA, UTENTE))
        inf("le porte dei vicini: %s" % vicine_conta())
        inf("unita': %s" % rem("systemctl is-active %s.service" % UNITA)[1].strip())
        inf("tc %s: %s" % (DEV, qdisc().replace("\n", " | ")))
        rc, out, _ = root("%s list tables 2>/dev/null || true" % NFT)
        inf("tabelle nft: %s" % (out.strip().replace("\n", " | ") or "(nessuna)"))
        return 0

    if a.passo == "rimetti":
        return 0 if rimetti() else 2

    if a.passo == "chiudi":
        return chiudi()

    if a.passo == "terreno":
        log("Il terreno — porta %d, utente %s (uid %d)" % (PORTA, UTENTE, UID_B))
        inf("le porte dei vicini PRIMA: %s" % vicine_conta())
        for passo in ("porta", "utente", "accendi"):
            if not terreno(passo):
                ko("⛔ terreno «%s» fallito" % passo)
                return 2
        buono, m = metro_installa()
        (ok if buono else ko)("il metro nft: %s" % m)
        if not buono:
            return 2
        buono, m = getto_compila()
        (ok if buono else ko)("il getto compilato dentro il contenitore: %s" % m)
        if not buono:
            return 2
        inf("le porte dei vicini DOPO: %s" % vicine_conta())
        return 0

    # ── da qui in giu' escono NUMERI: serve il lucchetto ───────────────────
    netem = a.passo in ("contesa", "tutto")
    if a.senza_lucchetto:
        avv("⛔⛔ SENZA LUCCHETTO: quel che esce di qui NON VALE e non si riferisce")
        L = Lucchetto(gpu=False, netem=False)
    else:
        L = Lucchetto(gpu=True, netem=netem, secondi=3600, attesa=a.attesa)

    fuori, rossi = {}, []
    with L:
        buono, m = metro_installa()
        if not buono:
            ko("⛔ il metro non si e' installato: %s" % m)
            return 2
        # ⛔ SI SALVA DOPO OGNI PASSO, non alla fine.  Un giro sotto lucchetto
        #    che muore all'ultimo braccio butterebbe via anche i numeri gia'
        #    buoni, e il lucchetto si aspetta mezz'ora.
        for nome, quando, fai in (
                ("tara", ("tara", "tutto"),
                 lambda: tara(secondi=max(5, int(a.secondi / 4)))),
                ("tetto", ("tetto", "tutto"), lambda: tetto()),
                ("audio", ("audio", "tutto"),
                 lambda: ab_audio(secondi=int(a.secondi), tela=a.tela)),
                ("scene", ("scene", "tutto"),
                 lambda: scene(secondi=int(a.secondi), tela=a.tela)),
                # ⭐⭐⭐ I DUE PASSI DELL'INCARICO 10-b7 — la riconciliazione
                #      col 44,6 e il caso peggiore vero.  ⛔ NON stanno in
                #      «tutto»: cambiano le cure NEL SERVER, e un giro che li
                #      infilasse in mezzo agli altri lascerebbe i passi
                #      successivi a misurare un prodotto diverso.
                ("fase9", ("fase9",),
                 lambda: fase9(secondi=int(a.secondi), tela=a.tela)),
                ("entropia", ("entropia",),
                 lambda: entropia(secondi=int(a.secondi), tela=a.tela,
                                  quali=(a.scene.split(",") if a.scene else None))),
                ("contesa", ("contesa", "tutto"),
                 lambda: contesa(quante=a.quante, stretta=a.stretta,
                                 secondi=int(a.secondi), tela=a.tela))):
            if a.passo not in quando or nome in a.salta.split(","):
                continue
            t, r = fai()
            fuori[nome] = t
            rossi += r
            salva("10-b90-%s.json" % nome, {nome: t})
        # ⛔⛔ E IL SERVER SI RIMETTE COM'ERA, DENTRO IL LUCCHETTO.  I passi
        #     «fase9» ed «entropia» spengono le cure a meta' strada: chi
        #     arrivasse dopo trovando un server a cure spente misurerebbe un
        #     prodotto che non e' quello del 24 agosto, e nessuna riga glielo
        #     direbbe.  ⚠ E si VERIFICA leggendo, non si dichiara.
        if a.passo in ("fase9", "entropia"):
            buono, m = server_con("accese")
            (ok if buono else ko)("il server rimesso ai predefiniti: %s" % m)
            if not buono:
                rossi.append("il server NON e' tornato ai predefiniti")

    salva("10-b90-%s.json" % a.passo, fuori)

    # ── ⭐ LA RIGA CHE CONTA: x10, quanto fa ───────────────────────────────
    sc = fuori.get("scene") or {}
    te = fuori.get("tetto") or {}
    if sc:
        log("⭐⭐⭐ LA RIGA CHE CONTA — ×10, quanto fa")
        print("   | scena | ⭐ MEDIA | picco | ×10 media | ×10 picco | "
              "fotogrammi | byte/fot |")
        print("   |---|---|---|---|---|---|---|")
        for nome in ("ferma", "desktop", "grana", "duro"):
            e = sc.get(nome)
            if not e:
                continue
            print("   | %s | %.3f | %.3f | **%.1f** | **%.1f** | %d | %s |"
                  % (nome, e.get("tot_medio") or 0, e["tot_picco"] or 0,
                     (e.get("tot_medio") or 0) * 10, (e["tot_picco"] or 0) * 10,
                     e["fotogrammi"],
                     "%.0f" % e["byte_per_fot"] if e["byte_per_fot"] else "—"))
        if te and te.get("massimo_mbit"):
            inf("contro il filo: NIC %s Mbit/s dichiarati · UDP nudo misurato "
                "%.0f Mbit/s (limite SUPERIORE per QUIC)"
                % (te.get("nic_mbit"), te["massimo_mbit"]))

    if rossi:
        ko("⛔ %d rossi: %s" % (len(rossi), " | ".join(str(x)[:120] for x in rossi)))
        return 1
    ok("nessun rosso")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
