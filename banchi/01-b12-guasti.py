#!/usr/bin/env python3
"""01-b12-guasti.py — ⛔ B12: un guasto costruito a mano PER OGNI BANCO.

    python3 01-b12-guasti.py --elenco               i dodici guasti
    python3 01-b12-guasti.py --verifica B7          l'appiglio c'e' ed e' unico?
    python3 01-b12-guasti.py --applica  B7          innesta il guasto
    python3 01-b12-guasti.py --togli    B7          lo toglie, e lo VERIFICA
    python3 01-b12-guasti.py --giudica  esiti.jsonl il verdetto, e il registro
    python3 01-b12-guasti.py --registro             chi e' certificato, e quando
    python3 01-b12-guasti.py --impronte B7          i file su cui poggia B7, oggi
    python3 01-b12-guasti.py --unisci ALTRA.jsonl   unisce le due copie del registro
    python3 01-b12-guasti.py --unisci-col-server    va a prendere quella del server
    python3 01-b12-guasti.py --unisci-col-server --rispecchia   ...e gliela rimanda

⚠ `--applica`, `--togli` e `--verifica` girano DENTRO il contenitore: toccano
  le copie che stanno in `examples/`.  `--giudica` e `--registro` girano
  dovunque.  L'orchestratore e' `01-b12-lancia.sh`.

===========================================================================
⛔ PERCHE' ESISTE, E NON E' UNA FORMALITA'

`PIANO.md` §0.3 regola 4, e `LEZIONI.md` §1.2: **il banco si certifica prima di
essere creduto.**

  ⛔ *«Un banco che non e' mai diventato rosso non e' pulito: e' NON
     CERTIFICATO.»*

`fasi/01-filo-nudo.md` B12-C1: ⛔ **un guasto costruito a mano PER OGNI BANCO, e
sono dodici.**  *La prima stesura ne costruiva quattro per dodici banchi, e i
due scoperti erano i banchi dei due difetti piu' cari di v1* (R3.7, R4.6).

===========================================================================
⛔ LE QUATTRO TRAPPOLE DI UN BANCO CHE CERTIFICA ALTRI BANCHI

  1. **il rosso per la ragione sbagliata.**  Un guasto che rompe la
     compilazione fa diventare rosso QUALUNQUE banco, e certifica **zero**.
     ⛔ Da cui: ogni guasto dichiara la **marca** che deve comparire nell'uscita
     del banco rosso, e senza quella marca la certificazione **non vale**;
     ⛔ **e la marca ha DUE meta', e la seconda e' quella che si dimentica**:
     l'uscita rossa la deve dire **e il giro SANO NON la deve gia' dire**.
     Una marca che compare in tutt'e due i giri non e' una marca, e' un modo
     di certificare senza guardare — la nota del guasto C2 lo scriveva gia',
     e `giudica()` non lo verificava.  *Rilievo R12-A.3, 11 agosto 2026: la
     seconda meta' era gia' scritta la stessa notte in
     `01-b8-cronometro.py:1571` (`gia = frase in testo_sano`), e il criterio
     piu' debole era proprio nel banco che certifica gli altri undici.*
     ⛔ Da cui, qui: `giudica()` pretende `guasto.marca_vista` **e**
     `not sano.marca_vista`, e un guasto **senza marca non certifica niente**
     invece di saltare il controllo;
  2. **il guasto che non e' stato innestato.**  Un appiglio che non si trova
     lascia il codice sano, il banco resta verde, e chi legge conclude *«il
     banco non vede il guasto»* — cioe' l'accusa esattamente opposta.  ⛔ Da
     cui: l'appiglio si conta **prima**, e dev'essere **esattamente uno**;
  3. **il guasto che sopravvive.**  Un interruttore che fa mentire il server e
     resta acceso avvelena ogni misura successiva, e nessuno sapra' che c'era.
     ⛔ Da cui: `--togli` **riverifica il file byte per byte** contro
     l'impronta di prima, e non si fida di aver tolto;
  4. **il verde di partenza mai guardato.**  «E' diventato rosso» non vuol dire
     niente se non era verde prima.  ⛔ Da cui il giro e' **sano → guasto →
     sano**, e sono tre esecuzioni, non una.

===========================================================================
⛔ CHE COSA VUOL DIRE «CERTIFICATO», QUI DENTRO

Un banco e' certificato quando, **nello stesso giro**:

  · sano   ha dato l'esito che si aspettava da un server sano;
  · guasto ha dato un esito DIVERSO, **e la sua uscita porta la marca** che
           dice che ha visto proprio quel guasto;
  · sano   ci e' tornato: il guasto e' stato tolto e il banco e' tornato verde.

⛔ Due su tre non bastano, e il piu' insidioso da perdere e' il terzo: senza,
   «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo stesso
   aspetto.

⭐ E la certificazione **si scrive su file, con la data**: `01-b12-registro.jsonl`.
   Un banco certificato tre giorni fa su un codice che nel frattempo e'
   cambiato **non e' certificato oggi**, e il registro porta anche l'impronta
   dei file su cui la certificazione e' stata fatta.

===========================================================================
⛔ IL REGISTRO CONSERVA LA STORIA, NON LA SOVRASCRIVE

*Rilievo R12-A.4, 11 agosto 2026.*  Il campo si chiamava `mai_provati` ed era
calcolato **per giro**: `set(GUASTI) - set(per_sigla)`.  Cosi' B13, che alle
21:19 era `non_certificati` — cioe' **provato e non riuscito** — alle 23:01 era
`mai_provati`; e B7 e C2, certificati alle 21:19, alle 23:01 erano
`mai_provati`.  Sullo **stesso** codice.

  ⛔ *«Provato e non riuscito» e «mai provato» hanno due cure diverse, e il
     registro le fondeva nella piu' innocente.  Chi legge l'ultima riga — che
     e' quel che fa chiunque legga un registro — sapeva MENO di quel che il
     progetto sapeva due ore prima.*

Da cui tre cose, tutte qui sotto:

  · il campo si chiama `non_provati_in_questo_giro`, che e' quel che e';
  · `mostra_registro()` legge **tutte** le righe, le ordina per data (⚠ e
    l'ordine di scrittura NON e' l'ordine del tempo: nel file di stasera la
    riga piu' vecchia sta sotto quella piu' nuova) e ricostruisce **lo stato
    corrente di ogni banco** dall'ultima riga che ne dice qualcosa.  La parola
    *«mai»* si usa solo quando **nessun** giro l'ha mai provato;
  · e lo stato corrente si confronta con le **impronte di oggi**: una
    certificazione fatta su file che nel frattempo sono cambiati si stampa
    **scaduta**, che non e' «certificato» e non e' «mai provato».
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
ESEMPI = os.path.join(QUI, "b2", "ngtcp2", "examples")
# ⛔ Il nome comincia con `01-b12-` come tutto il resto di questo banco: i
#    file di questa fase hanno il proprietario scritto nel nome, e un
#    registro chiamato altrimenti sarebbe di nessuno.
REGISTRO = os.path.join(QUI, "01-b12-registro.jsonl")

# ⛔ LA CARTELLA DELLE COPIE, E PERCHE' NON SI GUASTA MAI UN ORIGINALE.
#
#    Tre dei guasti sono su programmi Python di altri banchi.  Guastarli in
#    casa loro vorrebbe dire due cose che il mandato vieta: toccare file di
#    altri, e — peggio — lasciare un banco guasto se questo programma morisse a
#    meta'.  ⭐ Qui si copiano **per intero** i banchi che servono in
#    `01-b12-copie/`, si guasta la COPIA, e si lancia la copia.
#
# ⚠ E la copia dev'essere INTERA, non del solo file guastato: `01-b4-lancia.py`
#   cerca il validatore accanto a se stesso, e una copia parziale girerebbe
#   contro il validatore SANO — stampando un verde e certificando niente.
COPIE = os.path.join(QUI, "01-b12-copie")

# ⛔ E DOVE SI TIENE L'ORIGINALE DI UN FILE CHE NON SI PUO' RICOSTRUIRE.
#
#    Un guasto di tipo `copia-di-file` (oggi: B13) non sostituisce una stringa
#    dentro un sorgente — **sovrascrive un file intero**.  Li' `--togli` non
#    puo' rifare l'operazione all'incontrario: deve rimettere i byte di prima,
#    e per rimetterli deve averli.  ⭐ Qui si tiene la copia dell'originale
#    **con la sua impronta accanto**, e `--togli` non si dichiara riuscito
#    finche' l'impronta non torna quella.
ORIGINALI = os.path.join(COPIE, "originali")

# La cartella dei certificati.  ⚠ E' un percorso di ESECUZIONE, non del sorgente:
# vive dentro il contenitore, e chi lancia lo puo' cambiare con `--certificati`.
CERT_PREDEFINITA = "/media/REMOTIX/b2-certificati"

# Che cosa serve a ciascun banco per girare da solo dentro `01-b12-copie/`.
CORREDO = {
    "B4": ["01-b4-lancia.py", "01-b4-validatore.py", "01-b4-registrazioni.py"],
    "B9": ["01-b9-letture.py", "01-b3-cliente.py"],
    "C2": ["01-c2-diagnosi.py", "01-b3-cliente.py"],
    # ⛔⭐ I BANCHI DELLA FASE 3 VOGLIONO IL CORREDO INTERO, E NON E' PIGNOLERIA
    #     — 13 agosto 2026, alla messa a catalogo.
    #
    # Quei banchi risolvono i propri fratelli con `dirname(__file__)` e **senza
    # nessuna variabile d'ambiente**: `03-scena-accendi.sh:105` compila
    # `"$QUI/03-scena.c"`, `03-scena-certifica.sh:48-51` prende accendi, marca e
    # metro da `$QUI`, e `03-marca-certifica.py:53-56` carica `03-marca.py` con
    # `importlib` dalla propria cartella.
    #
    #   ⛔ *Copiare il solo file guastato e lanciare l'originale vorrebbe dire
    #      compilare il sorgente SANO con il guasto fermo in una cartella che
    #      nessuno legge: il banco resterebbe **verde**, e la riga direbbe «non
    #      e' diventato rosso» di un guasto **mai innestato** — la trappola n.2
    #      di questo file, nella sua forma piu' silenziosa.*
    #
    # ⚠ E `02-giudizio-metro.py` sta nel corredo pur non chiamandosi `03-`: M6 e
    #   il `giro` di M8 sono verdetti SUOI, non della scena.
    "03-scena": ["03-scena.c", "03-scena-accendi.sh", "03-scena-certifica.sh",
                 "03-marca.py", "03-marca-certifica.py", "03-deposita.py",
                 "02-giudizio-metro.py"],
    "03-marca": ["03-marca.py", "03-marca-certifica.py", "03-scena.c",
                 "03-scena-accendi.sh", "03-scena-certifica.sh",
                 "03-deposita.py", "02-giudizio-metro.py"],
    "03-deposita": ["03-deposita.py", "03-scena-certifica.sh", "03-scena.c",
                    "03-scena-accendi.sh", "03-marca.py",
                    "03-marca-certifica.py", "02-giudizio-metro.py"],
    # ⚠ B17 col guasto (B): il banco gira `--certifica` su CHUWI senza rete, e
    #   carica i fratelli dalla PROPRIA cartella.
    "03-b17": ["03-b17-ritardo.py", "03-b17-ponte.py", "03-marca.py",
               "02-pagina-misura-cdp.py"],
    # ⚠ B14: `costruisci_e_spedisci()` compila `$QUI/03-b14-metro.c`, quindi il
    #   metro guasto dev'essere accanto alla copia del banco.
    "03-b14": ["03-b14-cadenza.py", "03-b14-metro.c", "03-b14-scena.c",
               "03-marca.py"],
    # ⛔⭐ B15 E B18: `02-filo-fotogramma.py` NON e' un di piu' — 13 agosto 2026
    #     sera, MISURATO invece che letto.  `certifica()` di tutt'e due chiude
    #     confrontando le costanti di §6.2 (`INTESTAZIONE`, `CHIAVE`, `DELTA`)
    #     con quelle di quel file, caricandolo con `_porta()` **dalla propria
    #     cartella**.  ⚠ Senza, quel controllo non fallisce: cade nel ramo
    #     «non ho potuto confrontare» — che in B15 conta **una falla** (e il
    #     giro sano uscirebbe 2 invece di 0), e in B18 non ne conta nessuna,
    #     cioe' sparisce in silenzio.  ⇒ Copiare il solo banco vorrebbe dire
    #     certificarne uno su un atteso sbagliato e l'altro su un controllo in
    #     meno, e le due forme d'errore sono diverse solo nel sintomo.
    "03-b15": ["03-b15-movimento.py", "02-filo-fotogramma.py"],
    "03-b18": ["03-b18-credito.py", "02-filo-fotogramma.py"],
}

# ===========================================================================
# ⛔ SU CHE COSA POGGIA DAVVERO LA CERTIFICAZIONE DI OGNI BANCO — rilievo R12-A.5
#
# Il registro annotava una sola impronta, `sha256(banchi/rcp/rcp.c)`, per tutti
# e dodici.  Ma i tre guasti che sono stati davvero eseguiti si innestano su
# `01-b4-validatore.py`, `01-b3-cliente.py` e `01-c2-diagnosi.py`, e i banchi
# che devono diventare rossi sono `01-b4-lancia.py`, `01-b9-letture.py`,
# `01-c2-diagnosi.py`: ⛔ **nessuno di quei file entrava nell'impronta**, e
# `rcp.c` non partecipa alla certificazione di B4 e di B9 in nessun modo.
#
#   ⛔ *Un denominatore che promette una cosa e ne misura un'altra e' PEGGIO di
#      nessun denominatore, perche' da' alla riga l'aria di essere gia' stata
#      controllata: si riscrive `01-b4-validatore.py` da capo, `rcp.c` non si
#      tocca, e la riga «B4 certificato, impronta d839839f…» resta valida a
#      vista mentre il banco certificato non esiste piu'.*
#
# ⭐ Da cui: ogni guasto dichiara **i file su cui la sua certificazione poggia**
#    — quello guastato E quello che deve diventare rosso — e il registro porta
#    l'impronta di ciascuno.  `--registro` le ricalcola oggi e dice quali
#    certificazioni sono **scadute**.
#
# ⚠ E un file che non si legge da qui (i documenti non stanno sulla macchina di
#   prova, i banchi di B4 non stanno nel contenitore) vale `None`, e due `None`
#   NON sono uguali: «non ho potuto guardare» non e' «non e' cambiato».
# ⛔⛔ IL BINARIO DEL PRODOTTO CONTA, E FINO AL 12 AGOSTO 2026 NON LO CONTAVA
#     NESSUNO — trovato dal giro di ricertificazione della sera, ed e' un buco
#     nello strumento che tutta la giornata ha usato come garanzia.
#
#     Nessun banco che misura il PRODOTTO (B10, B13, P1, P5, P5R) aveva
#     `main.c` o il `Makefile` fra le impronte.  ⇒ Una ricostruzione che
#     cambia il binario **non faceva scadere niente**, e il registro
#     continuava a dire «vale oggi» di una riga misurata su un altro binario.
#     `[M]` la sera del 12 agosto: `src/main.c` e `Makefile` cambiati alle
#     22:18, il prodotto sul server un commit indietro, e il catalogo che
#     diceva **15 su 15**.
#
#     ⚠ E' la forma E8 applicata alla garanzia stessa: «certificato» e «non
#     ho guardato la cosa che conta» avevano lo stesso aspetto.  Da qui in poi
#     un banco del prodotto porta anche i due file che decidono che cosa il
#     binario CONTIENE — e scade quando il prodotto si ricostruisce, che e'
#     esattamente quel che deve fare.
#
# ⛔⛔ E LA SECONDA META' DEL BUCO ERA PIU' GRAVE DELLA PRIMA, e si e' vista
#     solo perche' la prima e' stata curata: aggiunti qui i due file, il conto
#     e' rimasto **15 su 15**.  Il confronto guardava solo le impronte che la
#     RIGA porta, quindi ⛔ **aggiungere un file che conta non invalidava
#     niente**.  La cura sta in `confronta_impronte()`, col suo riquadro, e il
#     banco che la certifica e' `--prova-impronte`.
#     ⇒ Il conto onesto, la stessa sera: **da 15 su 15 a 10 su 15**.
#
# ⛔⭐ E IL NOME DI CATALOGO E' QUELLO DELLA MACCHINA DEL PRODOTTO — cura della
#     notte fra il 12 e il 13 agosto 2026, e la prima stesura di questa riga
#     l'aveva sbagliato.
#
#     Era `["../src/main.c", "../src/Makefile"]`, cioe' il posto in cui i due
#     file stanno **su CHUWI** (`banchi/../src/`).  `[M]`: sul server i banchi
#     stanno in `/media/REMOTIX/src/` e il prodotto in `/media/REMOTIX/src/
#     remotix/`, quindi `../src/main.c` diventa `/src/main.c` e **non esiste**.
#     ⇒ Ogni giro fatto **dal server** — cioe' B10 e B13 — avrebbe scritto due
#     impronte `None`, e la riga sarebbe nata «non riverificabile» il giorno
#     stesso: severita' giusta applicata a un file che c'era, solo altrove.
#
#     ⭐ E' identica alla cura gia' fatta per `remotix/pagina.c` (ALTRI_POSTI,
#        qui sotto), e si risolve nello stesso modo: il nome di catalogo e'
#        quello della macchina del prodotto, e l'altro posto si dichiara.
FILE_DEL_BINARIO = ["remotix/main.c", "remotix/Makefile"]

FILE_CHE_CONTANO = {
    "B2":  ["01-b2-sonda-trasporto.py", "01-b2-ngtcp2-wt-innesta.py"],
    "B3":  ["01-b3-cliente.py", "01-b3-rcp-innesta.py", "rcp/rcp.c"],
    "B4":  ["01-b4-lancia.py", "01-b4-validatore.py", "01-b4-registrazioni.py"],
    "B5":  ["01-b5-violazioni.py", "rcp/rcp.c"],
    "B6":  ["01-b6-tetti.py", "rcp/rcp.c"],
    "B7":  ["01-b7-congedo.py", "rcp/rcp.c"],
    "B8":  ["01-b8-cronometro.py", "rcp/rcp.c"],
    "B9":  ["01-b9-letture.py", "01-b3-cliente.py", "../RCP.md"],
    # ⛔ La certificazione di B10 poggia sul banco che deve diventare rosso —
    #    che dall'11 agosto 2026 sera ESISTE — e non solo sul modulo guastato.
    "B10": ["01-b10-secondo-utente.py", "01-b10-lancia.sh",
            "rcp/autenticazione.c"] + FILE_DEL_BINARIO,
    "B11": ["01-b11-guasto-innesta.py", "01-b11-pagina.html"],
    "B13": ["01-b13-proprieta.py", "rcp/rcp.c"] + FILE_DEL_BINARIO,
    "C2":  ["01-c2-diagnosi.py"],
    # ⚠ P1 e P5 — sera dell'11 agosto 2026.  `remotix/pagina.c` e' il sorgente
    #   DEL PRODOTTO, e si legge solo dalla macchina di prova: da `banchi/`, su
    #   CHUWI, il prodotto sta in `../src/`, e quindi qui vale `None`.  ⛔ E'
    #   la stessa scena di `../RCP.md` per B9, al contrario: ognuno dei due
    #   banchi si certifica da una macchina sola, e `--provabile` lo dice
    #   invece di lasciarlo scoprire a un rosso (R12-A.31).
    "P1":  ["01-p1-prodotto.sh", "01-p1-dentro.sh", "remotix/pagina.c"] + FILE_DEL_BINARIO,
    # ⚠ `01-p5-guasto-catalogo.py` entra il 12 agosto 2026, su segnalazione di
    #   chi l'ha scritto: innesta il guasto P5 leggendo le stringhe **da questo
    #   catalogo** invece di ricopiarle, e senza la sua impronta la riga di P5
    #   direbbe «certificato» senza sapere con che attrezzo.
    "P5":  ["01-p5-lancia.sh", "01-p5-registro.py", "01-p5-guasto-catalogo.py",
            "remotix/pagina.c"] + FILE_DEL_BINARIO,
    # ⚠ P5R — 12 agosto 2026.  Senza questa riga la certificazione di P5R
    #   esisteva ma NON portava impronte, cioe' era «non riverificabile»: una
    #   riga che dice «certificato» e non sa dire **su che byte**.  ⛔ E
    #   `--provabile P5R` usciva **0** proprio perche' non c'era niente da
    #   confrontare — un verde vacuo, che e' peggio di un rosso.  Chiesta da
    #   chi ha misurato il guasto, aggiunta dal coordinatore.
    #   ⛔ E il file che conta e' `pagina.html`, non `pagina.c`: il guasto del
    #     RITIRO vive nella pagina servita, e `src/pagina.c:590` la legge una
    #     volta sola all'accensione — sono due file diversi e due guasti
    #     ortogonali (misurato in tutt'e due i versi il 12 agosto).
    "P5R": ["01-p5-lancia.sh", "01-p5-registro.py", "01-p5-guasto-ritiro.py",
            "remotix/pagina.html"] + FILE_DEL_BINARIO,

    # =======================================================================
    # ⭐ I BANCHI DELLA FASE 3 — messi a catalogo il 13 agosto 2026 alla
    #    chiusura della fase, con le voci scritte e i guasti costruiti ma
    #    ⛔ **NESSUNA MARCA MISURATA**, e quindi nessuno certificato.
    #
    # ⭐⭐ LA SERA DEL 13 AGOSTO TRE DI LORO SONO STATI CERTIFICATI DAVVERO —
    #     `03-b14`, `03-marca` e i due che entrano stasera, `03-b15` e
    #     `03-b18` — e le loro marche sono MISURATE in due meta', sano e
    #     guasto, su giri veri.  Le note dicono con che numeri.
    # ⛔ Gli altri restano col campo `marca` VUOTO **di proposito**: finche' e'
    #    vuoto `--giudica` li rifiuta, ed e' giusto cosi'.  Non sono «puliti»:
    #    sono banchi che nessuno ha ancora messo alla prova.
    # =======================================================================
    # ⚠ Un `*-esiti.jsonl` NON entra qui, in nessuna di queste voci: e'
    #   l'USCITA del banco e cambia a ogni giro, quindi ogni certificazione
    #   nascerebbe scaduta il minuto dopo.  Nessuna delle quindici voci di
    #   prima ne include uno.
    "03-scena": ["03-scena.c", "03-scena-accendi.sh", "03-scena-certifica.sh",
                 "03-marca.py", "03-marca-certifica.py",
                 "02-giudizio-metro.py", "03-deposita.py"],
    "03-marca": ["03-marca.py", "03-marca-certifica.py", "03-scena.c",
                 "03-scena-certifica.sh"],
    "03-deposita": ["03-deposita.py", "03-scena-certifica.sh"],
    # ⛔ B14 non misura un byte del prodotto: il suo soggetto e' **Mutter**.
    #    `FILE_DEL_BINARIO` qui sarebbe una scadenza regalata.
    "03-b14": ["03-b14-cadenza.py", "03-b14-metro.c", "03-b14-scena.c"],
    # ⚠ B16 non tocca il prodotto compilato ne' il servente C: apre
    #   `src/pagina.html` da un `http.server` di Python, con Chrome vero.
    "03-b16": ["03-b16-dipinti.py", "02-pagina-misura-cdp.py",
               "remotix/pagina.html"],
    # ⛔ B17 e' l'unico dei quattro che misura la CATENA VERA, e la sua lista e'
    #    la piu' lunga apposta: ogni nome e' un tratto della catena che il
    #    numero attraversa — il `pts` (figlio.c), il filo (webtransport.c), la
    #    decodifica e il disegno (pagina.html), e le intestazioni COOP/COEP che
    #    sono esattamente cio' che il controllo P6 misura (pagina.c).
    #    ⚠ Ogni nome e' anche una scadenza in piu': e' il prezzo di una
    #    certificazione che dice davvero su quali byte ha misurato.
    # ⛔⛔ `remotix/codificatore.c` e `.h` ENTRANO il 13 agosto 2026 sera — ed e'
    #    la cura del PUNTO CIECO, non un'aggiunta di completezza.
    #
    #    Fino a stasera **nessuna** voce del catalogo nominava il codificatore:
    #    lo si poteva riscrivere da capo a fondo e il conto avrebbe detto «tutto
    #    verde».  ⚠ E si vede ADESSO perche' adesso il lavoro va proprio li':
    #    la codifica HEVC in hardware.
    #
    #    ⛔ Va nella lista di B17 e di B19 e **non altrove**, e la ragione e' la
    #    stessa che tiene `03-b15` senza `remotix/*`: qui ci vanno i file su cui
    #    il banco MISURA.  B17 e B19 misurano la catena vera, e il codificatore
    #    e' il tratto che pesa 39 dei 74,58 ms — il piu' grosso di tutti.
    #    Metterlo dove non si misura sarebbe una scadenza regalata.
    #
    #    ⚠⚠ E QUEL CHE QUESTA RIGA NON FA, detto qui perche' non venga letta per
    #    piu' di quel che e': B17 e B19 sono **MAI PROVATI**.  ⇒ Da stasera la
    #    rete c'e' **sulla carta**; nei fatti ci sara' il giorno in cui B17
    #    viene certificato.  Il punto cieco non e' chiuso: e' **nominato**.
    "03-b17": ["03-b17-ritardo.py", "03-b17-ponte.py", "03-b17-accendi.sh",
               "03-b17-lancia.sh", "03-marca.py", "03-scena.c",
               "02-pagina-misura-cdp.py", "remotix/figlio.c",
               "remotix/webtransport.c", "remotix/pagina.c",
               "remotix/codificatore.c", "remotix/codificatore.h",
               "remotix/pagina.html"] + FILE_DEL_BINARIO,
    # ⚠ B19 sono DUE file, e a catalogo va quello che misura la catena vera.
    #   ⭐ Il gemello `03-b19-dipinti-worker.py` non esce piu' «SEMPRE 0»: la
    #     cura del 13 agosto sera gli ha messo l'esito nel codice d'uscita
    #     (vedi la nota della voce), e adesso sa dire di no anche lui.
    "03-b19": ["03-b19-ritardo-worker.py", "03-b17-ponte.py", "03-marca.py",
               "03-scena.c", "03-b17-accendi.sh", "02-pagina-misura-cdp.py",
               "remotix/codificatore.c", "remotix/codificatore.h",
               "remotix/pagina.html"] + FILE_DEL_BINARIO,

    # =======================================================================
    # ⭐ GLI ULTIMI DUE BANCHI NUOVI — 13 agosto 2026 sera.
    #
    # `03-b15` e `03-b18` erano rimasti fuori dalle certificazioni del giorno
    # perche' i loro file si muovevano ancora alle 17:58 e alle 18:04 mentre
    # gli altri sette erano fermi.  ⭐ Adesso sono fermi, e la loro scena e' la
    # piu' economica di tutta la fase 3: `--certifica` gira **su CHUWI, senza
    # rete, senza contenitore e senza prodotto** — aioquic si importa tardi,
    # dentro le funzioni del giro dal vivo — e ci mette circa un secondo.
    # ⛔ Da cui: qui l'unica cosa che si certifica e' **la certificazione**,
    #    cioe' che i controlli sappiano dire di no ai propri verbali guasti.
    #    Il giro DAL VIVO sulla 7603 e sulla 7607 resta `[?]`, e le due cose
    #    non si arrotondano.
    #
    # ⛔ E NIENTE `FILE_DEL_BINARIO` E NIENTE `remotix/*`: `--certifica` non
    #    tocca un byte del prodotto — gira su verbali FABBRICATI A MANO.
    #    Metterceli sarebbe una scadenza regalata, cioe' una severita' che non
    #    descrive niente: la certificazione cadrebbe per un file su cui non ha
    #    mai misurato.  ⚠ Il giorno in cui si certifichera' il giro DAL VIVO,
    #    quelle righe andranno aggiunte — e quel giorno la voce sara' un'altra.
    # =======================================================================
    "03-b15": ["03-b15-movimento.py", "02-filo-fotogramma.py"],
    "03-b18": ["03-b18-credito.py", "02-filo-fotogramma.py"],
}

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

MARCA = "REMOTIX B12 GUASTO"


# ===========================================================================
# IL CATALOGO.  ⛔ Dodici guasti, uno per banco, e ciascuno dice:
#
#   dove       il file da guastare — ⛔ SEMPRE una COPIA, mai l'originale;
#   appiglio   la stringa da sostituire, che dev'essere UNICA nel file;
#   guasto     con che cosa si sostituisce;
#   dimostra   che cosa il banco starebbe per non vedere;
#   marca      la stringa che l'uscita del banco rosso DEVE contenere, o il
#              rosso e' di un'altra causa;
#   costa      «leggero» = si applica e si gira · «ricostruisce» = fra
#              l'innesto e il giro ci va una compilazione ·
#              «copia-di-file» = si sovrascrive un file intero e si tiene
#              l'originale da parte · «gia-fatto» = il guasto vive nel banco.
# ===========================================================================
GUASTI = {}


def guasto(sigla, banco, titolo, dove, appiglio, sostituto, dimostra, marca,
           costa, riferimento, nota="", atteso_sano=0, sostituisci_con=""):
    # ⛔ `atteso_sano` non e' sempre 0, e darlo per scontato sarebbe la forma
    #    B0.4 al contrario: **B13 sul codice sano esce 3**, perche' due delle
    #    sei proprieta' non hanno un imputato da misurare.  Un giudice che
    #    pretendesse lo zero direbbe «il banco era gia' rosso» di un banco che
    #    sta facendo esattamente quel che deve — e non certificherebbe mai
    #    nessun banco che dichiara delle `[?]`.
    GUASTI[sigla] = {
        "sigla": sigla, "banco": banco, "titolo": titolo, "dove": dove,
        "appiglio": appiglio, "sostituto": sostituto, "dimostra": dimostra,
        "marca": marca, "costa": costa, "riferimento": riferimento,
        "nota": nota, "atteso_sano": atteso_sano,
        "sostituisci_con": sostituisci_con,
        "file_che_contano": FILE_CHE_CONTANO.get(sigla, []),
    }


# ── B7 — ⛔ IL GUASTO CHE `fasi/01-filo-nudo.md` NOMINA PER PRIMO ───────────
guasto(
    "B7", "B7", "si toglie la spedizione del CONGEDO e si LASCIA il codice "
                "nella chiusura",
    os.path.join(ESEMPI, "rcp.c"),
    "\tmanda_messaggio(s, T_CONGEDO, corpo, w.len);\n",
    "\t/* " + MARCA + " B7 — la spedizione del CONGEDO tolta, e il codice\n"
    "\t * nella chiusura della sessione LASCIATO al suo posto (§3.1 punto 3).\n"
    "\t * Se B7 resta verde sta facendo una || dove serve una &&. */\n",
    "⛔ §3.1 vuole DUE strade e B7 le deve pretendere **tutt'e due**: il "
    "`CONGEDO` sul canale di controllo E il codice del motivo nella chiusura "
    "della sessione.  Con questo guasto ne resta una sola.  ⭐ Un banco che le "
    "contasse in `or` — «almeno una delle due e' arrivata» — resterebbe VERDE, "
    "e sarebbe **nato per non accorgersene**: il motivo continuerebbe ad "
    "arrivare, e la strada che salva le diagnosi quando lo stream e' rotto "
    "sarebbe sparita in silenzio",
    # ⛔ LA MARCA ERA «CONGEDO», E NON ERA UNA MARCA — rilievo R12-A.3.
    #    `01-b7-congedo.py` nomina `CONGEDO` **37 volte**: e' il soggetto del
    #    banco, e compare nel giro SANO a ogni riga.  Con quella marca, B7
    #    rosso per una compilazione fallita — cioe' la trappola n.1 che questo
    #    file dichiara di chiudere — avrebbe avuto `marca_vista = true` lo
    #    stesso, e la certificazione del 10 agosto 2026 alle 21:19 e' stata
    #    esattamente questo.
    # ⭐ La marca giusta e' la riga che B7 stampa SOLO quando la strada 2 non e'
    #    arrivata: `esigenze()` mette `«assente»` in `es.motivo is None`, e la
    #    riga rossa la stampa (righe 1281-1283).  Nel giro sano tutti i casi
    #    `server→client` hanno «congedo» fra le strade esigibili e il motivo
    #    arriva, quindi quella riga non c'e'.
    "il motivo nel CONGEDO sul canale: assente",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §3.1, §8.1",
)

# ── B4 — il validatore che legge `lunghezza` come u16 ──────────────────────
guasto(
    "B4", "B4", "il validatore legge `lunghezza` come u16 invece che u32",
    os.path.join(COPIE, "01-b4-validatore.py"),
    'lung_msg = le.u32("la lunghezza")',
    'lung_msg = le.u16("la lunghezza")  # ' + MARCA + ' B4',
    "§6.1 mette `u16 tipo` e `u32 lunghezza`.  Letta come `u16`, la lunghezza "
    "vale sempre i **due byte alti** — cioe' quasi sempre zero — e il "
    "validatore trova ogni corpo «piu' lungo di quel che dichiara».  ⛔ Il "
    "banco di B4 deve accorgersene, e il modo in cui deve accorgersene e' "
    "**il byte accusato**: senza il confronto del byte, un validatore che "
    "sbaglia dappertutto darebbe lo stesso «non conforme» su tutte le "
    "registrazioni che devono essere non conformi, cioe' il numero giusto "
    "per la ragione sbagliata",
    # ⛔ LA MARCA ERA VUOTA, E B4 E' STATO CERTIFICATO LO STESSO — R12-A.3.
    #    Il campo vuoto faceva saltare a `giudica()` l'intero controllo (`if
    #    g.get("marca") and …`), cioe' **la trappola n.1 disinnescata dal
    #    proprio guardiano**: la riga «B4 certificato» del 10 agosto 2026 alle
    #    23:01 non distingue il rosso del guasto dal rosso di un file che non
    #    si apre.
    # ⭐ La marca e' la riga che il catalogo stesso indica due frasi piu' su —
    #    **il byte accusato** — e con `u16` il validatore accusa sempre il
    #    byte 36 invece del byte vero.  Misurata l'11 agosto 2026: 0 volte nel
    #    giro sano, 7 nel giro col guasto.
    "⛔ atteso il byte",
    "leggero",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §6.1",
    nota="⛔ Il file guastato e' la COPIA in `01-b12-copie/`, e il banco di B4 "
         "va lanciato contro la copia: `01-b4-validatore.py` non si tocca.",
)

# ── B3 — non si libera la struttura per connessione (il difetto di v1) ─────
guasto(
    "B3", "B3", "non si libera la struttura per connessione — il difetto che "
                "uccise v1 alla SECONDA connessione",
    os.path.join(ESEMPI, "http3_server_proto_codec.cc"),
    # ⛔⭐ L'APPIGLIO ERA SBAGLIATO, E SI SAREBBE VISTO SOLO AL PRIMO GIRO VERO
    #     — rilievo R12-A.41, 11 agosto 2026.
    #
    # Era `"  rcp_libera(rcp_);\n  rcp_ = nullptr;\n"`, con **due** spazi di
    # rientro.  `[M]`: nel file vero il rientro e' di **quattro**, e la stringa
    # compare **zero** volte — mentre `rcp_libera(rcp_)` da sola ne compare
    # **due**.  ⇒ Il guasto non si sarebbe innestato, e la nota del catalogo
    # avvertiva del pericolo opposto (l'appiglio troppo comune) senza
    # accorgersi che quello scritto non c'era affatto.
    #
    # ⭐ Il punto giusto e' UNO dei due, e lo dice il file stesso: la riga sopra
    #    porta il commento *«il posto nel registro delle sessioni si libera
    #    QUI»*.  Prendendo il commento dentro l'appiglio, il punto diventa
    #    unico senza dover scegliere fra due righe identiche.
    # ⚠ `if (0 && rcp_)` invece di cancellare: il blocco resta sotto gli occhi
    #   del compilatore (niente «codice irraggiungibile», niente variabile non
    #   usata) e `--togli` torna a un testo identico all'originale.
    "  // ⭐ REMOTIX B3 — il posto nel registro delle sessioni si libera QUI.\n"
    "  if (rcp_) {\n",
    "  /* " + MARCA + " B3 — il posto nel registro delle sessioni NON si\n"
    "   * libera piu': e' il difetto di v1, dove la prima connessione passa\n"
    "   * e le successive trovano il registro pieno. */\n"
    "  if (0 && rcp_) {\n",
    "`LEZIONI.md` §2.1: in v1 un certificato condiviso uccideva il server "
    "**alla seconda** connessione, e una prova a collegamento singolo **resta "
    "verde per sempre**.  ⛔ B3 esiste per questo, e questo guasto e' la forma "
    "esatta del difetto che B3 e' nato per trovare: se B3 resta verde, la "
    "seconda connessione non la sta guardando nessuno",
    # ⛔ LA MARCA E' MISURATA — 11 agosto 2026, e il sintomo e' quello di v1
    #    alla lettera.  Innestato il guasto, la PRIMA connessione passa e la
    #    SECONDA si vede rispondere:
    #      «⛔ RuntimeError: CONGEDO invece di SESSIONE:
    #        motivo 0x0f = GIA_ATTIVA_REMOTA»
    # ⭐ Cioe' il posto della prima non si e' liberato, e il server crede che
    #    l'utente sia ancora collegato altrove.  E' esattamente «la prima passa,
    #    la seconda no».
    # ⚠ E la marca NON e' il solo nome del motivo: `GIA_ATTIVA_REMOTA` e' anche
    #   l'esito ATTESO del terzo giro di B3 (le due connessioni vive insieme),
    #   dove comparirebbe in verde.  La frase scelta porta con se' «invece di
    #   SESSIONE», che esiste solo quando quel motivo arriva dove NON doveva.
    "CONGEDO invece di SESSIONE: motivo 0x0f = GIA_ATTIVA_REMOTA",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · LEZIONI.md §2.1 · RCP.md §11",
    nota="⚠ L'appiglio sta nell'ospite, non in `rcp.c`: `rcp_libera()` in "
         "`rcp.c` non ha chiamanti — li innesta `01-b3-rcp-innesta.py` nel "
         "`.cc`.  Se l'appiglio compare piu' di una volta il guasto NON si "
         "applica: toglierne uno solo lascerebbe il posto liberato altrove e "
         "il guasto sarebbe a meta'.\n"
         "       ⛔ **Senza marca, e quindi non certificabile** (R12-A.3): la "
         "riga che B3 stampa alla seconda connessione va misurata su un giro "
         "vero prima di poterla scrivere qui.  Finche' questo campo e' vuoto "
         "`--giudica` rifiuta di certificare B3, invece di saltare il "
         "controllo come faceva.",
)

# ── B5 — una violazione che il server smette di punire ─────────────────────
guasto(
    "B5", "B5", "una capacita' RIPETUTA nel `CIAO` non e' piu' "
                "`ERRORE_PROTOCOLLO`: il controllo dei duplicati SPENTO",
    os.path.join(ESEMPI, "rcp.c"),
    # ⛔⭐ IL GUASTO E' STATO RIFATTO L'11 AGOSTO 2026 — rilievo R12-A.37.
    #
    # L'appiglio era `"nome ripetuto"`, cioe' una stringa di COMMENTO, e il
    # sostituto ci appiccicava accanto la marca.  ⛔ Quel guasto **non rompeva
    # niente**: il codice compilato restava identico byte per byte, il server
    # continuava a congedare con `ERRORE_PROTOCOLLO`, e B5 sarebbe rimasto
    # verde nel passo 2/3 — cioe' avrebbe dichiarato «il banco non vede il
    # guasto» su un banco sano e un guasto che non c'era.
    # ⭐ Il guasto vero e' il RAMO: `if (ripetuto)` spento, `congeda()` mai
    #    chiamato.  Il `0 &&` lascia la condizione sotto gli occhi del
    #    compilatore, quindi niente avvisi su variabile non usata, e il
    #    `--togli` torna a un testo identico all'originale.
    "if (ripetuto) {",
    "if (0 && ripetuto) { /* " + MARCA + " B5 — il controllo dei duplicati\n"
    "\t\t                    * di §4.3 SPENTO: la ripetizione passa. */",
    "§4.3: *«un nome ripetuto due volte e' `ERRORE_PROTOCOLLO`. «Vince "
    "l'ultimo» e «vince il primo» sono due implementazioni diverse dello "
    "stesso documento»*.  ⛔ E' una violazione che **non produce nessun "
    "sintomo**: la connessione prosegue e la negoziazione riesce.  Se B5 non "
    "la vede, non la vedra' piu' nessuno",
    # ⛔ LA MARCA E' MISURATA, NON SCELTA — 11 agosto 2026.
    #    Innestato il guasto, `01-b5-violazioni.py` stampa due righe nuove:
    #      «NO  capacita-ripetuta   chiusura-wt=(assente)  sessione VIVA»
    #      «NO      §3.1 punto 3 su «capacita-ripetuta»: la chiusura della
    #               sessione porta assente, atteso 0x0b»
    # ⭐ E si prende la SECONDA.  Il nome del caso da solo — «capacita-ripetuta»
    #    — compare anche nel giro sano, in verde: sarebbe la stessa trappola
    #    gia' pagata su B6 con «ciao-presto» e su B7 con «CONGEDO».  La frase
    #    scelta esiste solo quando quel caso CADE.
    "§3.1 punto 3 su «capacita-ripetuta»",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.3",
    nota="⭐ ESEGUIBILE dall'11 agosto 2026 (R12-A.37).  ⚠ E la marca qui "
         "sotto NON e' stata scelta a tavolino: e' stata **misurata** "
         "innestando il guasto e leggendo che cosa il banco stampa, poi "
         "verificata assente dal giro sano.  Una marca dedotta e' la forma E5 "
         "— un fatto che era una deduzione mai riverificata.",
)

# ── B6 — il tetto che scatta PRIMA ─────────────────────────────────────────
guasto(
    "B6", "B6", "`TETTO_CIAO` da 5000 a 500 ms: il tetto scatta PRIMA",
    os.path.join(ESEMPI, "rcp.c"),
    "#define TETTO_CIAO 5000",
    "#define TETTO_CIAO 500 /* " + MARCA + " B6 */",
    "⛔ La meta' del requisito che nessuno scrive e' **«non prima»**.  Un "
    "server che congedasse subito con `TEMPO_SCADUTO` darebbe "
    "`TEMPO_SCADUTO` in tutt'e tre i casi, e un banco che guarda **solo il "
    "motivo** lo promuoverebbe a pieni voti.  Con questo guasto il caso "
    "`ciao-presto` — che tace il 70 % del tetto e poi manda `CIAO` — deve "
    "vedersi rifiutare un messaggio che §4.6 obbliga a servire",
    # ⛔ LA MARCA ERA «ciao-presto», CHE E' IL NOME DI UN CASO — R12-A.3.
    #    `01-b6-tetti.py:1177` lo stampa con `riga(ok, c["nome"], …)` a **ogni**
    #    giro, sano compreso: una marca che compare in tutt'e due i giri non e'
    #    una marca.
    # ⭐ La riga che solo il giro rosso puo' produrre e' quella dell'atteso del
    #    controllo che dice NO (`01-b6-tetti.py:1096`), stampata soltanto
    #    quando un caso `-presto` cade — cioe' quando il tetto scatta PRIMA,
    #    che e' esattamente quel che questo guasto costruisce.
    "⭐ nessuna caduta",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.6",
    nota="⚠ Catalogato e non eseguito: `01-b12-lancia.sh` non ha una riga di "
         "comando per B6, e il guasto va innestato in `rcp/rcp.c` e non nella "
         "copia di `examples/` — `01-b6-lancia.sh` ricopia il sorgente a ogni "
         "giro e cancellerebbe il guasto, e il confronto fra i due `#define` "
         "che B6 fa al passo 2 lo vedrebbe comunque.  ⛔ Finche' non e' "
         "eseguito B6 resta NON CERTIFICATO, e non «pulito».",
)

# ── B8 — il secondo fisso che sparisce ─────────────────────────────────────
guasto(
    "B8", "B8", "il ritardo fisso di un secondo prima di rispondere a "
                "`CREDENZIALI` viene tolto",
    os.path.join(ESEMPI, "rcp.c"),
    # ⛔⭐ E QUESTO APPIGLIO NON ESISTEVA — rilievo R12-A.38, 11 agosto 2026.
    #
    # Era `RITARDO_CREDENZIALI`, e in `rcp.c` quel nome **non compare nemmeno
    # una volta**: la costante si chiama `RITARDO_FISSO` (riga 70).  ⇒ Il
    # guasto non si sarebbe innestato nemmeno volendo, e la voce
    # «catalogata e non eseguita» nascondeva questo, non solo il ban.
    # ⚠ E come per B5, il sostituto era un COMMENTO accanto al nome: anche col
    #   nome giusto non avrebbe tolto nessun ritardo.
    # ⭐ Il guasto vero e' il NUMERO: il secondo fisso di §4.4-bis portato a
    #    zero.  Da li' «utente inesistente» risponde in un millisecondo e
    #    «parola sbagliata» in cinquanta — e il TEMPISMO torna a essere un
    #    canale, che e' precisamente cio' che B8 esiste per vedere.
    "#define RITARDO_FISSO 1000",
    "#define RITARDO_FISSO 0 /* " + MARCA + " B8 */",
    "§4.4-bis: *«il secondo fisso toglie il TEMPISMO come canale — senza, "
    "«utente inesistente» risponde in un millisecondo e «parola sbagliata» in "
    "cinquanta»*.  ⛔ E' una proprieta' di **sicurezza che nessun altro banco "
    "vede**, e una regressione che la togliesse non farebbe fallire niente",
    # ⛔⭐ LA MARCA, e fino alla sera dell'11 agosto 2026 era VUOTA — cioe' B8
    #     non era certificabile nemmeno con un giro perfetto: `--giudica`
    #     rifiuta un guasto senza marca, e ha ragione («il banco e' diventato
    #     rosso» non si attribuisce a niente, e una compilazione fallita rende
    #     rosso qualunque banco).
    #
    # ⭐ La frase e' quella del PRIMO criterio del verdetto — «nessuna risposta
    #    di PAM prima di 1000 ms» — e la dice solo chi ha visto una risposta
    #    sotto il secondo.  Col ritardo fisso a zero e' precisamente quel che
    #    succede, ed e' il punto in cui il guasto morde.
    # ⛔ E la seconda meta' del criterio la regge da se': nel giro SANO quella
    #    riga non c'e' (la stampa alternativa dice «N su N ≥ 1000 ms»), quindi
    #    non e' una marca che compare in tutt'e due i giri.
    # ⚠ Si tiene anche il «La piu' veloce:» apposta: senza, la stessa
    #   sottostringa comparirebbe nella riga con cui `--certifica` dichiara di
    #   NON aver visto la frase, e la marca si vedrebbe per il motivo sbagliato.
    "risposte sotto il secondo. La piu' veloce:",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.4-bis",
    # ⛔⭐ IL GIRO SANO DI B8 ESCE **5**, NON 0 — e non e' un atteso allargato
    #     finche' torna, che e' la strada disonesta che B13 ha insegnato a non
    #     prendere.  E' il quinto esito, che B8 dichiara da se': *«il BAN passa
    #     per intero, ma le mediane SI SEPARANO»*, e ⛔ **l'esito 5 si da' SOLO
    #     quando l'imputato e' stato MISURATO ed e' PAM** — se fosse un ritardo
    #     nostro, o non misurabile, lo stesso giro uscirebbe 1.
    #
    # `[M]` 11 agosto 2026, NIC-OS, porta 7471, giro `20260811-130957`:
    #   50 risposte su 50 ≥ 1000 ms (la piu' veloce 1073,0 ms) · mediane
    #   inesistente 2210,5 · sbagliata 2104,5 · giusta 1088,9 ms ·
    #   ⭐ «inesistente − sbagliata», l'unica coppia che direbbe se un nome
    #   utente esiste, +106,0 ms [-239,7; +500,2] ⇒ NON si separa ·
    #   il server dichiara di aver aspettato oltre il secondo fisso +1009 ms sui
    #   respinti e +86 ms sugli ammessi ⇒ la firma di `pam_faildelay`.
    #
    # ⛔ E LA DISTINZIONE FRA I DUE ESITI E' QUEL CHE RENDE QUESTA
    #    CERTIFICAZIONE UNA MISURA: il guasto porta `RITARDO_FISSO` a zero, le
    #    risposte scendono sotto il secondo, e quello e' un **rosso pieno (1)**,
    #    non un 5.  ⇒ sano 5 → guasto 1 → risano 5, e i due numeri non si
    #    possono confondere.  ⚠ Se un giorno il `[?]` di PAM si chiudesse, il
    #    giro sano diventerebbe 0 e QUESTA RIGA diventerebbe rossa: e' il modo
    #    giusto di accorgersene.
    atteso_sano=5,
    nota="⭐ IL GUASTO E' VERO E INNESTABILE dall'11 agosto 2026 (R12-A.38), "
         "e la sua efficacia e' MISURATA: col ritardo a zero, sull'innesto, "
         "«giusta» risponde in **58 ms** e «inesistente» in **2959** — il "
         "tempismo torna a essere un canale spalancato.\n"
         "       ⭐⭐ E B8 E' CERTIFICATO — 11 agosto 2026, sera, `[M]` "
         "NIC-OS, porta 7471, `5 → 1 → 5`.  Il registro: giro «sano» "
         "`20260811-133820`, «guasto» `20260811-134105`, «risano» "
         "`20260811-134334`, verdetto scritto alle 13:46:12.\n"
         "         sano   uscita **5** · 50 risposte su 50 ≥ 1000 ms (la piu' "
         "veloce 1000,8) · mediane 2123 · 2198 · 1086 ms · la marca compare "
         "**0** volte;\n"
         "         guasto uscita **1** · ⛔ **17 risposte sotto il secondo, la "
         "piu' veloce 49,7 ms**, e la mediana di «giusta» passa da 1085,9 a "
         "**56,3 ms** · la marca compare;\n"
         "         risano uscita **5** · di nuovo 0 volte.\n"
         "       ⭐ E il rosso NON viene da una compilazione fallita — la "
         "trappola n.1 di questo file: il binario e' stato ricostruito e "
         "verificato in tutt'e tre i passi, e i 15 guasti a mano del giudice di "
         "B8 restano 15 su 15 in ognuno.\n"
         "       ⛔ COM'E' STATO POSSIBILE, e la cura vale piu' del punto: fino "
         "a stasera `01-b12-lancia.sh` **riscriveva a mano** la sequenza di "
         "B8, e la copia era incompleta in tre punti — le **due vite del "
         "server** (la persistenza del ban, invariante I7, vuole un riavvio), "
         "la **lettura della pagina** (§4.4-bis punto 1) e lo **sblocco su un "
         "ban VERO** (senza, «tolto» e «non c'era» hanno la stessa faccia).  "
         "⇒ Il giro sano usciva rosso su otto punti che parlavano "
         "dell'orchestratore, non del banco.  ⭐ Adesso `gira()` **chiama "
         "`01-b8-lancia.sh`**, come fa da sempre con C2, e la marca la legge "
         "dal file che il verdetto di B8 scrive da se'.\n"
         "       ⚠ E l'ATTESO SANO E' 5, NON 0, ed e' scritto nel catalogo "
         "invece che allargato a posteriori: e' il quinto esito di B8 — «il ban "
         "passa per intero, ma le mediane si separano» — e ⛔ si da' SOLO "
         "quando l'imputato e' stato MISURATO ed e' **PAM**.  Il guasto, "
         "invece, da' un rosso pieno (1): i due numeri non si confondono, e il "
         "giorno in cui il `[?]` di PAM si chiudesse il sano diventerebbe 0 e "
         "questa riga diventerebbe rossa — che e' il modo giusto di "
         "accorgersene.\n"
         "       ⚠ QUEL CHE QUESTA CERTIFICAZIONE NON COPRE, detto qui perche' "
         "e' qui che si legge la parola «certificato»: il bersaglio e' "
         "l'**innesto**, non il prodotto; la pagina si legge con un socket e "
         "non con un browser; e le mediane restano separate — il `[?]` di PAM "
         "resta aperto, e il ban non lo chiude."
)

# ── B9 — ⛔ il cliente di prova che ha letto il C ───────────────────────────
guasto(
    "B9", "B9", "⛔ si cancella dal cliente di prova la riga che il censimento "
                "cita alla voce L4",
    os.path.join(COPIE, "01-b3-cliente.py"),
    "            corpo = bytes(self.arrivati[6:6 + lung])\n",
    "            grezzo = bytes(self.arrivati[6:6 + lung])\n"
    "            # " + MARCA + " B9 — «ha letto il C»: la coda in piu' si\n"
    "            # taglia invece di essere consegnata, cioe' la lettura A di\n"
    "            # §6.1 — quella che ha scelto il validatore.  ⛔ L'appiglio\n"
    "            # che `01-b9-letture.py` cita nella voce L4 SPARISCE, ed e'\n"
    "            # il punto: il censimento non descrive piu' questo cliente.\n"
    "            corpo = grezzo\n",
    "⛔ Il valore di B9 non e' che il cliente di prova funzioni: e' che sia "
    "**un secondo lettore indipendente**.  Se chi lo scrive guarda il C, le "
    "sue scelte diventano quelle del server e la concordanza fra i due non "
    "vale piu' niente — e ⭐ **nessun altro banco puo' accorgersene**, perche' "
    "tutti gli altri diventerebbero piu' verdi, non meno.  Questo guasto "
    "cambia una delle scelte censite: `01-b9-letture.py` deve accorgersi che "
    "il testo del cliente non e' piu' quello che ha censito, e **rifiutarsi "
    "di dare il verde**",
    "il testo e' cambiato sotto il banco",
    "leggero",
    "fasi/01-filo-nudo.md B12-C1 e B9 · PIANO.md §1.1",
    nota="⛔ CHE COSA QUESTA CERTIFICAZIONE DICE, E CHE COSA NON DICE — "
         "rilievo R12-A.8, e il titolo di questa voce e' stato corretto per "
         "questo.\n"
         "       Il guasto **cancella la citazione** che la voce L4 porta "
         "(`corpo = bytes(self.arrivati[6:6 + lung])`), e B9 diventa rosso "
         "perche' il testo che ha censito non c'e' piu'.  ⭐ E' una cosa vera "
         "e vale la pena averla misurata: e' la difesa contro il censimento "
         "che invecchia in silenzio, ed e' quel che B9 dichiara di saper fare "
         "(righe 45-46 del suo file).\n"
         "       ⚠ **Non e' pero' «B9 vede un secondo lettore che si e' "
         "allineato al primo»**, che e' la frase piu' grossa.  Caso concreto, "
         "costruito dal revisore e verificato: si cambia la lettura A→B "
         "**lasciando intatta, riga per riga, la stringa citata** e "
         "aggiungendo il troncamento nelle righe successive → B9 esce **0, 12 "
         "su 12**, e continua a stampare «⭐ SCELTO … passa il corpo cosi' "
         "com'e' (lettura B, tollerante)», che a quel punto e' falso.\n"
         "       ⛔ Il guasto che coprirebbe QUELLA frase e' un secondo guasto "
         "— cambiare il comportamento senza toccare la citazione — e va "
         "costruito contro `01-b9-letture.py`, che non e' di questo mandato. "
         "Qui si dichiara invece di lasciarlo credere.",
)

# ── B10 — la guardia ereditata da v1 ───────────────────────────────────────
guasto(
    "B10", "B10", "si rimette la guardia che rifiuta chi non possiede il "
                  "processo",
    # ⛔ SU UNA COPIA INTERA DELL'ALBERO DEL PRODOTTO, non su `src/remotix` e
    #    non su `examples/`.  Due ragioni, e nessuna delle due e' di comodo:
    #      · il banco di B10 misura il PRODOTTO (`SPECIFICHE.md` §5.5 parla del
    #        servizio di sistema), quindi il guasto va dove il prodotto vive;
    #      · costruire il guasto dentro `/srv/src/remotix` riscriverebbe il
    #        binario che gli altri banchi stanno misurando, e per qualche
    #        minuto lascerebbe sotto i loro piedi un server bugiardo.
    #    La copia la rifa' da zero `01-b10-lancia.sh guasto`, e la butta in
    #    fondo.  ⚠ Da CHUWI questo percorso non esiste: il guasto si applica
    #    **sul server**, ed e' li' che ha senso.
    os.path.join(QUI, "sera-b10-remotix", "autenticazione.c"),
    # ⛔⭐ L'APPIGLIO VECCHIO ERA UNA STRINGA DI COMMENTO — la stessa trappola
    #     che l'11 agosto 2026 aveva svuotato il guasto di B5.  `dove` era
    #     `examples/autenticazione.c` e l'appiglio `autenticazione_utente_atteso`,
    #     che in quel file compare **soltanto nel commento** che racconta la
    #     guardia tolta: il sostituto ci appiccicava accanto la marca, il
    #     codice compilato restava identico byte per byte, e il banco sarebbe
    #     rimasto verde per il motivo giusto — non c'era nessun guasto.
    #     ⭐ Adesso l'appiglio e' CODICE, e il sostituto rimette la guardia di
    #        v1 alla lettera: `getpwuid(geteuid())` e il confronto col nome,
    #        **prima** di `pam_start`.  Il rifiuto e' silenzioso, come in v1:
    #        e' l'assenza di righe di PAM nel registro che B10 deve leggere.
    "bool rcp_autentica(const char *utente, const char *parola)\n"
    "{\n"
    "\tif (!utente || !*utente || !parola)\n"
    "\t\treturn false;\n",
    "/* " + MARCA + " B10 — la guardia di v1 rimessa: il server torna a\n"
    " * servire soltanto chi possiede il processo, e a tutti gli altri dice\n"
    " * «credenziali errate» senza nemmeno interpellare PAM. */\n"
    "#include <pwd.h>\n"
    "#include <unistd.h>\n"
    "\n"
    "static const char *autenticazione_utente_atteso(void)\n"
    "{\n"
    "\tstruct passwd *p = getpwuid(geteuid());\n"
    "\treturn p ? p->pw_name : \"\";\n"
    "}\n"
    "\n"
    "bool rcp_autentica(const char *utente, const char *parola)\n"
    "{\n"
    "\tif (!utente || !*utente || !parola)\n"
    "\t\treturn false;\n"
    "\t/* " + MARCA + " B10 */\n"
    "\tif (strcmp(utente, autenticazione_utente_atteso()) != 0)\n"
    "\t\treturn false;\n",
    "`SPECIFICHE.md` §5.5 vuole il multi-tenant; v1 aveva una guardia che "
    "rifiutava chiunque non fosse il proprietario del processo.  ⛔ B10 esiste "
    "per vederla, e *«non entra» ha quattro cause* (R3.26): se B10 resta "
    "verde con la guardia rimessa, sta guardando la causa sbagliata",
    # ⭐ LA MARCA, e non e' una parola qualsiasi: e' la riga che
    #    `01-b10-secondo-utente.py` stampa **soltanto** quando riconosce la
    #    causa (1) — il server ha rifiutato e PAM non e' stata nemmeno
    #    interrogata, mentre `pamtester` con la stessa parola e lo stesso
    #    servizio riesce.  ⛔ Le altre tre cause hanno altre marche, e nel giro
    #    sano questa non compare mai (verificato: 0 nel sano, ≥1 nel guasto).
    "CAUSA-1-GUARDIA-PRE-PAM",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 e B10 · SPECIFICHE.md §5.5",
    nota="⭐ ESEGUITO PER LA PRIMA VOLTA la sera dell'11 agosto 2026, insieme "
         "al banco che lo deve vedere (`01-b10-secondo-utente.py`, "
         "`01-b10-lancia.sh`).\n"
         "       ⛔ LA RICOSTRUZIONE NON E' `ninja`: il prodotto si costruisce "
         "con `GEMELLO=nessuno bash <copia>/costruisci.sh`, e "
         "`attrezzi-misura-marca.sh` sa fare solo `ninja -C .../build "
         "bsslserver`, cioe' l'innesto.  Finche' `01-b12-lancia.sh` non impara "
         "a costruire il prodotto, questa certificazione si fa dal lanciatore "
         "del banco:  `BERSAGLIO=prodotto bash "
         "/media/REMOTIX/src/01-b10-lancia.sh certifica`  (sano → guasto → "
         "risanato, sulle porte 7491/7492).\n"
         "       ⚠ E `GEMELLO=nessuno` va DICHIARATO: la copia guasta diverge "
         "apposta da `banchi/rcp/autenticazione.c`, e il Makefile fermerebbe "
         "la costruzione (R12.3).  Il prodotto vero non si tocca, e i sorgenti "
         "della copia si confrontano con i suoi prima di guastarli.",
)

# ── B11 — la pagina che non applica §3 ─────────────────────────────────────
guasto(
    "B11", "B11", "il server guasto di B11 esiste gia': "
                  "`01-b11-guasto-innesta.py`",
    os.path.join(ESEMPI, "rcp.c"),
    "", "",
    "⭐ B11 e' l'unico banco che nasce **con il proprio guasto dentro**: "
    "`01-b11-guasto-innesta.py` costruisce un server che sbaglia apposta in "
    "dodici modi, e `01-b11-lancia.sh` gira la pagina **prima contro il "
    "server sano** — dove i casi che si aspettano un congedo devono cadere "
    "tutti — e poi contro quello guasto.  ⛔ E' la forma che B12 chiede, gia' "
    "in casa: qui si dichiara, non si rifa'",
    "",
    "gia-fatto",
    "fasi/01-filo-nudo.md B11 · banchi/01-b11-guasto-innesta.py",
    nota="⭐ PROVATO PER LA PRIMA VOLTA l'11 agosto 2026 — e non era «mai "
         "provato», era **mai lanciato**.  ⚠ Va lanciato **dalla macchina di "
         "chi guarda**, non dal server: `01-b11-lancia.sh` cerca "
         "`v1/strumenti/sshpw.py`, che sul server non c'e'.  Lanciato di la' "
         "muore al passo 2 senza aver applicato nessun guasto (verificato: "
         "zero marche nei sorgenti e nel binario, porta 7447 libera).\n"
         "       ⭐ **IL CONTROLLO CHE DICE NO FUNZIONA**, ed e' la meta' che "
         "vale: la pagina contro il server **SANO** esce NON-CONFORME con "
         "**9 punti che non passano**.  ⇒ «tutti verdi» contro il server "
         "guasto non e' compatibile con una pagina che dichiara conforme "
         "qualunque cosa.\n"
         "       ⛔ MA B11 NON E' CERTIFICATO, e per un punto solo, nominato: "
         "contro il server guasto il caso **`respinto-non-riprovare`** "
         "restituisce **`canale-rotto`** dove l'atteso dice **`muta`** "
         "(Firefox 140.13.0esr).  ⚠ La pagina distingue un `FIN` da un "
         "`RESET_STREAM` **apposta** — e' la cura del rilievo R6.12, che "
         "prima li confondeva e lasciava `fin-sul-controllo` verde senza "
         "distinguere il fatto che dichiara di misurare.\n"
         "       ⛔ E QUI NON SI ALLARGA L'ATTESO finche' torna: e' "
         "esattamente quel che B13 ha insegnato a non fare.  Le due strade "
         "oneste sono **misurare che cosa manda davvero il server guasto** "
         "(FIN o reset, dal registro del server) e poi correggere l'atteso "
         "**o** la pagina — e finche' non e' fatto B11 resta NON "
         "CERTIFICATO, non «quasi».\n"
         "       ⚠ E il giro e' su **un motore solo**: Chrome non l'ha "
         "guardato, quindi non si sa se il punto sia della pagina o del "
         "trasporto di Firefox.",
)

# ── B13 — un certificato solo, in due file ─────────────────────────────────
guasto(
    "B13", "B13", "i due certificati diventano UNO: `pagina.pem` viene "
                  "sostituito con `sessione.pem`",
    "{CERT}/pagina.pem",
    "", "",
    "⛔ §4.1-bis: *«un server che ne genera uno solo a scadenza breve passa "
    "tutti i banchi — e l'avviso ricompare quattordici giorni dopo, quando "
    "nessuno collegherebbe le due cose»*.  ⭐ Questo guasto non tocca una riga "
    "di codice: fa diventare **uno** i due certificati che devono essere due, "
    "e B13.1 deve vedere **due impronte uguali**",
    "LE IMPRONTE COMBACIANO",
    "copia-di-file",
    "fasi/01-filo-nudo.md B13.1 · RCP.md §4.1-bis",
    # ⛔⭐ RESTA 3, E LA NOTTE FRA L'11 E IL 12 AGOSTO 2026 QUALCUNO — io — L'HA
    #     PORTATO A 1 PER MEZZ'ORA.  La riga e' tenuta perche' l'errore e'
    #     istruttivo e perche' e' PROPRIO quello che questo file vieta in fondo
    #     alla nota qui sotto.
    #
    # ⛔ I NUMERI DI B13 NON SONO UN CONTEGGIO DI GUASTI, e leggerli cosi' e'
    #    stato l'errore (`01-b13-proprieta.py`, in fondo a `principale`):
    #
    #      0  tutte e sei le proprieta' passano
    #      1  ⛔ c'e' ALMENO UNA proprieta' ROSSA
    #      3  ⭐ nessun rosso, ma restano dei buchi DICHIARATI ([?] o ??)
    #
    #    ⇒ `atteso_sano=3` non vuol dire «aspettati tre guasti»: vuol dire
    #    **«sul codice sano B13 non ha nessun rosso»**, ed e' la dichiarazione
    #    giusta.  Portarlo a 1 dichiara normale un rosso — e in piu' rende il
    #    banco NON CERTIFICABILE, perche' con un rosso gia' li' il guasto non
    #    puo' piu' cambiare il numero: `[M]` giro delle 22:5x, sano 1 · guasto 1
    #    · risano 1, e il giudice ha rifiutato con «col guasto il banco ha dato
    #    lo stesso esito del sano», che era vero.
    #
    # ⭐ `[M]` la notte fra l'11 e il 12 agosto 2026, giro sano sotto B12, le sei
    #    proprieta' una per una:
    #
    #      B13.1  OK      3 cose guardate
    #      B13.2  OK  22.523 cose guardate  (la parola d'ordine non e' in nessun
    #                                        registro: il difetto del 10 agosto
    #                                        e' chiuso)
    #      B13.3  [?]     8 cose guardate   (nessun imputato: i certificati li fa
    #                                        un BANCO, non il codice)
    #      B13.4  NO      2 cose guardate   ⛔ ed e' L'UNICO rosso
    #      B13.5  ??      3 cose guardate   (il trasporto concede tutto: quella
    #                                        meta' non e' misurabile da qui)
    #      B13.6  OK      4 cose guardate
    #
    # ⛔ E IL ROSSO CHE RESTA NON E' DEL PRODOTTO: e' B13.4, «la pagina servita
    #    in TCP», che sotto B12 viene chiesta al server dell'INNESTO — e la
    #    pagina e' un mestiere del PRODOTTO.  Il sintomo e' `SSLError:
    #    WRONG_VERSION_NUMBER`.  ⭐ E non e' una scoperta di stanotte: lo scrive
    #    `01-b13-proprieta.py` in fondo alla propria certificazione — «quel che
    #    resta fuori: la pagina in TCP (B13.4), che oggi non ha imputato».
    #
    # ⚠ E PERCHE' PRIMA ERANO TRE: l'ipotesi e' che due dei tre rossi venissero
    #   dall'innesto DISALLINEATO — `b2/ngtcp2/examples/rcp.c` fermo al codice di
    #   stamattina mentre `rcp/rcp.c` portava la cura del congedo — e siano
    #   cadute quando l'innesto e' stato riallineato e ricostruito la notte fra
    #   l'11 e il 12.  ⛔ IPOTESI, NON MISURA: l'uscita del giro delle 15:19 non
    #   e' stata conservata, e senza quella il confronto non si puo' fare.  Si
    #   scrive qui perche' chi rilegge sappia che cosa NON e' stato provato.
    #
    # ⇒ QUINDI SOTTO B12 B13 NON SI CERTIFICA, e il motivo ha un nome: **B13.4
    #   e' rossa perche' la si chiede al server sbagliato**.  ⛔ Non si cura
    #   riscrivendo questo numero: e' la stessa regola del 10 agosto qui sotto,
    #   e la seconda volta che questo banco la fa pagare.
    #
    # ⭐⭐ E LA CURA C'E', ED E' STATA ESEGUITA — `[M]` la notte fra l'11 e il
    #    12 agosto 2026, `01-b13-sera-certifica.sh certifica`: **lo stesso ciclo
    #    con lo STESSO guasto, ma contro il PRODOTTO** sulla 7481, che la pagina
    #    la serve davvero (due ascoltatori, `pagina.html` 34.089 byte).
    #
    #      sano 3 · guasto 1 · risanato 3
    #      marca «LE IMPRONTE COMBACIANO»: 0 · 1 · 0  (contata sui tre file
    #                                                  d'uscita di quel giro)
    #
    #    ⇒ Il giro sano esce **3**, cioe' ESATTAMENTE l'atteso dichiarato qui:
    #    contro il prodotto B13.4 ha un imputato e smette di essere un rosso.
    #    ⭐ E la lezione e' che il numero era giusto e la SCENA era sbagliata —
    #    non il contrario.
    #
    # ⚠ Quindi la riga di registro di B13 viene da `01-b13-sera-certifica.sh`,
    #   non da `01-b12-lancia.sh`, ed e' scritto qui perche' chi rilegge non
    #   vada a cercare un giro di B12 che non esiste.  ⏳ Quel che resta da fare
    #   e' dare a `01-b12-lancia.sh` un modo di essere puntato sul prodotto:
    #   finche' non ce l'ha, questi due strumenti misurano due scene diverse e
    #   solo uno dei due puo' certificare B13.
    atteso_sano=3,
    sostituisci_con="{CERT}/sessione.pem",
    nota="⛔ IL GUASTO E' STATO RIFATTO L'11 AGOSTO 2026 — rilievi R12-A.1 e "
         "R12-A.2, e le due cose erano diverse.\n"
         "       ⛔ **A.1 — non era innestabile.**  Era di tipo "
         "`riga-di-comando`; `applica()` chiama `verifica()`, che per quel "
         "tipo usciva **subito con 0**, e `0 != 1` cadeva nel ramo «l'appiglio "
         "non e' unico — il guasto NON si innesta».  In "
         "`01-b12-lancia.sh` l'uscita ≠ 0 faceva `continue`: **i passi 2/3 e "
         "3/3 di B13 non si sono mai eseguiti**, e il ramo di `gira()` che "
         "commutava `base=pagina` era codice morto.\n"
         "       ⛔ **A.2 — e non era il guasto giusto.**  Accendere il server "
         "con `pagina.pem` cambia il certificato **presentato sul filo**, "
         "mentre `proprieta_1` legge le impronte dei **due file su disco** "
         "(`impronta_der(pagina.pem)` contro `impronta_der(sessione.pem)`): "
         "la riga di comando non tocca nessuno dei due, `imp_p == imp_s` "
         "restava falso e la marca «LE IMPRONTE COMBACIANO» non si sarebbe "
         "stampata mai.  A vedere quel guasto e' `proprieta_3` — un'altra "
         "proprieta' e un altro difetto — e `giudica()` avrebbe scritto «il "
         "banco e' rosso ma la sua uscita non nomina la marca» su un guasto "
         "che aveva funzionato.\n"
         "       ⭐ Il difetto che B13.1 esiste per trovare — *un server che "
         "genera UN certificato solo* — si costruisce dove B13.1 guarda: "
         "**sui due file**.  Da cui il tipo `copia-di-file`, l'originale "
         "tenuto in `01-b12-copie/originali/` con la sua impronta accanto, e "
         "un `--togli` che non si dichiara riuscito finche' i byte non sono "
         "tornati quelli.\n"
         "       ⚠ `atteso_sano = 3`: sul codice sano B13 dovrebbe uscire 3 e non 0, "
         "perche' B13.3 e B13.4 dichiarano di non avere un imputato (la pagina "
         "in TCP non esiste, e nessun codice genera certificati).  ⛔ E' un "
         "esito dichiarato, non un rosso — e va scritto qui, o la "
         "certificazione leggerebbe «era gia' rosso».\n"
         "       ⛔ `[M]` 10 agosto 2026, 23:30: **B13 sul codice sano esce 1**, "
         "non 3, perche' B13.2 ha trovato la parola d'ordine dentro un "
         "registro vero — `/srv/src/sonda/racc.log`.  ⭐ Da cui una regola che "
         "vale per tutto B12: **un banco il cui soggetto e' davvero rotto non "
         "si puo' certificare**, e la cosa giusta e' lasciarlo NON CERTIFICATO "
         "invece di allargare l'atteso finche' torna.  Si certifica il giorno "
         "in cui quel registro non contiene piu' la parola.",
)

# ── C2 — il diagnosta cieco su una delle due sonde ─────────────────────────
guasto(
    "C2", "C2", "⛔ al diagnosta si toglie la sonda TCP: resta con una sonda "
                "sola",
    os.path.join(COPIE, "01-c2-diagnosi.py"),
    "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "    s.settimeout(attesa)\n",
    "    return \"silenzio\"  # " + MARCA + " C2: la sonda TCP accecata\n"
    "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "    s.settimeout(attesa)\n",
    "⛔ **E' il difetto storico**: R3.17 racconta che il primo controllo "
    "positivo del progetto era cieco proprio perche' guardava un trasporto "
    "solo.  Con la sonda TCP che dice sempre «silenzio», la scena «UDP "
    "filtrato col TCP che risponde» diventa indistinguibile da «la macchina "
    "non c'e'», e C2 **deve** cadere su quella scena.  ⭐ Se non cadesse, C2 "
    "starebbe distinguendo le tre diagnosi con qualcosa che non e' la coppia "
    "di sonde",
    "IRRAGGIUNGIBILE",
    "leggero",
    "fasi/01-filo-nudo.md B12-C2, rilievo R3.17",
    nota="⭐ La marca e' `IRRAGGIUNGIBILE`, ed e' scelta apposta: e' il nome che "
         "C2 puo' produrre SOLO quando gli manca una delle due sonde.  ⛔ Una "
         "marca come «udp-filtrato» sarebbe comparsa anche nel giro sano — e "
         "una marca che compare in tutt'e due i giri non e' una marca, e' un "
         "modo di certificare senza guardare.",
)

# ── B2 — il credito degli stream che sparisce dai parametri ────────────────
guasto(
    "B2", "B2", "si toglie il credito di 19 stream unidirezionali dai "
                "parametri di trasporto",
    os.path.join(ESEMPI, "..", "examples", "server.cc"),
    # ⛔ DICIANNOVE, NON SEDICI — e il numero e' cambiato l'11 agosto 2026
    #    (R12-A.42) perche' certificando B2 il banco e' risultato rosso SUL
    #    CODICE SANO: §2.3 vuole 16 **disponibili**, e HTTP/3 se ne prende 3
    #    prima che RCP ne veda uno.  Con 16 dichiarati la sonda ne misurava 13.
    "params.initial_max_streams_uni = 19;",
    "/* " + MARCA + " B2 */",
    "§2.3 obbliga il server a concedere **almeno 16** stream unidirezionali. "
    "L'esempio di ngtcp2 ne concede tre di suo, e l'innesto B2 li porta a "
    "sedici.  ⛔ Tolta quella riga, il credito torna a tre e **niente si rompe "
    "adesso**: il sintomo arriverebbe alla fase 4, come «il desktop non "
    "risponde».  La sonda del trasporto di B2 — e B13.5 — devono vederlo qui",
    # ⛔ LA MARCA ERA «initial_max_streams_uni» — R12-A.3: e' il nome del
    #    parametro, e `01-b2-sonda-trasporto.py:169` lo STAMPA sempre, con il
    #    numero accanto, anche quando il numero e' giusto.
    # ⭐ La riga che solo il rosso produce e' il verdetto del controllo, che la
    #    sonda scrive con `NO ` davanti al nome (righe 186-190).
    # ⛔ LA MARCA E' MISURATA, E LE DUE PRIME SCELTE ERANO SBAGLIATE —
    #    11 agosto 2026.
    #    · «NO  credito INIZIALE stream unidirezionali» (quella in catalogo):
    #      il banco quella frase **non la stampa piu'**, e nessuno se n'era
    #      accorto perche' B2 non era mai stato provato;
    #    · «NO  credito uni DISPONIBILE…»: ⛔ fra `NO` e il testo ci sono i
    #      codici di colore ANSI, e `marca_vista()` cerca con `grep -F` sul
    #      file COLORATO — non combacerebbe mai.  ⚠ E la stessa frase senza
    #      `NO` compare anche nel giro sano, preceduta da `OK`.
    # ⭐ La riga scelta e' quella dell'ELENCO FINALE dei controlli che non
    #    passano: senza colori, e presente solo quando qualcosa non passa.
    #    `[M]` sano 0 · guasto 1 · risano 0.
    "- credito uni DISPONIBILE a RCP all'apertura",
    "ricostruisce",
    "fasi/01-filo-nudo.md B13.5 · RCP.md §2.3",
    nota="⚠ Catalogato e non eseguito in questo giro: costa una ricostruzione "
         "intera del server d'esempio, e il banco che lo vede (la sonda del "
         "trasporto) e' di B2, non di questo mandato.",
)


# ===========================================================================
# ⛔ P1 e P5 — I DUE BANCHI CHE ESISTEVANO E NON AVEVANO NESSUN GUASTO.
#
# Rilievo R12-A.50, sera dell'11 agosto 2026, e il `README.md` lo scriveva con
# un numero: *«P1 e P5 non sono nel catalogo di B12: i banchi sono 14, le voci
# 12»*.  ⛔ Non erano «puliti»: erano due banchi **mai diventati rossi**, cioe'
# la definizione stessa di NON CERTIFICATO — e sono i due che guardano il
# PRODOTTO, l'unica cosa di questa fase che un utente vedrebbe.
#
# ⛔ E IL DENOMINATORE VERO E' UN ALTRO ANCORA, misurato prima di scrivere
#    queste due voci (`ls banchi/ | sed 's/^\\(01-[a-z0-9]*\\)-.*/\\1/' | sort -u`):
#
#      · 14 prefissi di BANCO in `banchi/`  — B2 B3 B4 B5 B6 B7 B8 B9 B11 B12
#        B13 C2 P1 P5 — piu' `01-b0-` (gli attrezzi comuni: terreno, bersaglio,
#        chiamate) e sette `01-s…` (le sonde S1b S2 S3a S5 S6 S7 e S-telefono,
#        che sono MISURE del Gruppo 1, non banchi che si certificano);
#      · 14 voci nel catalogo dopo queste due, ma **non le stesse quattordici**:
#        il catalogo comprende **B10**, che non ha nessuno script, ed esclude
#        **B12**, che non certifica se' stesso.
#
#    ⇒ I banchi scritti che il catalogo puo' certificare sono **13** (i 14
#      prefissi meno B12), e le voci che hanno un banco dietro sono **13** (le
#      14 meno B10).  ⚠ Due insiemi che adesso coincidono — mentre prima di
#      stasera erano 12 e 12 **diversi**, ed e' precisamente il modo in cui un
#      conteggio smette di essere una misura (`fasi/01-filo-nudo.md`, il
#      riquadro sul denominatore).
#
# ⛔ E TUTT'E DUE I GUASTI SI INNESTANO SU UNA **COPIA INTERA** DEL PRODOTTO,
#    mai su `/media/REMOTIX/src/remotix/`.  La ragione non e' la stessa dei tre
#    guasti Python di sopra (quelli sono banchi di altri): qui e' che P1
#    **ricostruisce il binario come primo passo del proprio giro**, e guastare
#    il prodotto di casa lascerebbe, per i minuti del passo 2/3, un binario
#    bugiardo sotto i piedi di chiunque altro riaccendesse il server.  ⚠ La
#    sera dell'11 agosto 2026 sulla macchina di prova c'era un `remotix` vivo
#    sulla 7448 di un altro giro, e cinque agenti al lavoro insieme.
#
#      cp -a /media/REMOTIX/src/remotix \
#            /media/REMOTIX/src/01-b12-copie/p1-remotix
#      PORTA=7501 PORTA_MORTA=7502 PREFISSO_TMP=sera-p15 \
#        SORG=/media/REMOTIX/src/01-b12-copie/p1-remotix \
#        bash /media/REMOTIX/src/01-p1-prodotto.sh
#
#    ⛔ La copia si rifa' PRIMA di ogni giro sano, per la ragione scritta su
#       `prepara_copia()`: una copia rimasta da un giro precedente si porta
#       dietro il guasto di quel giro, e il banco parte **gia' rosso**.
# ===========================================================================

# ── P1 — ⛔ l'isolamento fra origini SPENTO, e il NOME dell'intestazione resta ─
guasto(
    "P1", "P1", "⛔ `Cross-Origin-Opener-Policy` da `same-origin` a "
                "`unsafe-none`: l'isolamento fra origini SPENTO",
    os.path.join(COPIE, "p1-remotix", "pagina.c"),
    '"Cross-Origin-Opener-Policy: same-origin\\r\\n"',
    '"Cross-Origin-Opener-Policy: unsafe-none\\r\\n" /* ' + MARCA + ' P1 — '
    'SPECIFICHE.md §11.5: l\'isolamento fra origini spento, e il NOME '
    'dell\'intestazione lasciato al suo posto apposta. */',
    "⛔ `SPECIFICHE.md` §11.5 non chiede che l'intestazione ci sia: chiede che "
    "**valga `same-origin`**.  Con `unsafe-none` l'intestazione c'e', il "
    "browser la legge, e l'isolamento non esiste: su Firefox e Safari i "
    "cronometri della pagina tornano su una griglia da 1 ms — su un tetto di "
    "50 — e la memoria condivisa sparisce.  ⭐ E' una regressione che **non "
    "rompe niente adesso**: la pagina si serve, il 200 arriva, la stretta di "
    "mano riesce.  Il sintomo arriverebbe alla fase 2, come «il video va a "
    "scatti su Firefox», e nessuno collegherebbe le due cose",
    # ⛔⭐ PERCHE' IL VALORE E NON LA RIGA INTERA — ed e' la trappola n.1 di
    #     questo file, evitata prima di innestare invece che dopo.
    #
    # La prima stesura di questo guasto toglieva la riga (`""` al posto della
    # stringa).  ⛔ Ma `remotix/costruisci.sh` **cerca «Cross-Origin-Opener-
    # Policy» dentro il binario prodotto** e si ferma se non la trova, e la
    # cerca anche `01-p1-prodotto.sh` fra le sue otto marche: il guasto avrebbe
    # reso P1 rosso su `costruzione.esito` e su `binario.marche` — cioe' su una
    # COMPILAZIONE FALLITA, che rende rosso qualunque banco e certifica ZERO.
    # ⭐ Cambiando il VALORE e lasciando il NOME, il binario porta ancora la
    #    marca, il costruttore esce 0, e l'unico controllo che si muove e'
    #    quello che guarda l'intestazione servita davvero.
    #
    # ⛔ LA MARCA E' MISURATA, NON SCELTA — `[M]` 11 agosto 2026, macchina
    #    NIC-OS, porta 7501, copia in `01-b12-copie/p1-remotix`, tre giri alle
    #    12:56:20 · 12:56:56 · 12:57:24 UTC (registro `01-p1-esiti.jsonl`):
    #
    #      sano   uscita 0 · VERDE 34 su 34 · la marca compare **0** volte
    #      guasto uscita 1 · ROSSO 33 su 34 · la marca compare **2** volte
    #      risano uscita 0 · VERDE 34 su 34 · la marca compare **0** volte
    #
    # ⭐ E il rosso e' di UN controllo solo — `fumo.isolamento.coop` — mentre
    #    `costruzione.esito` resta 0 e `binario.marche` resta 8/8: cioe' il
    #    guasto NON e' passato per una compilazione fallita, che e' la trappola
    #    n.1 di questo file.  ⚠ Il nome del caso da solo («isolamento.coop»)
    #    compare in tutt'e due i giri, e sarebbe la stessa trappola gia' pagata
    #    su B6 con «ciao-presto» e su B7 con «CONGEDO»; la riga scelta porta il
    #    «MANCA:» che solo il giro rosso stampa.
    "MANCA: Cross-Origin-Opener-Policy: same-origin",
    # ⭐ «leggero» e non «ricostruisce», e non e' una svista: P1 **ricostruisce
    #    da se'** come primo passo del proprio giro (e' meta' di quel che P1
    #    esiste per misurare).  Fra l'innesto e il giro non ci va nessuna
    #    compilazione fatta da qui.
    "leggero",
    "fasi/01-filo-nudo.md B12-C1 · SPECIFICHE.md §11.5 · README.md «CHE COSA "
    "FARE ADESSO» punto 5",
    nota="⛔ CHE COSA QUESTA CERTIFICAZIONE DICE, E CHE COSA NON DICE.\n"
         "       Dice che P1 vede una regressione del PRODOTTO che passa per "
         "il filo, dalla costruzione fino all'intestazione servita: il guasto "
         "sta in `pagina.c`, il binario si ricostruisce, il server si accende, "
         "e a diventare rosso e' il controllo che legge la risposta con "
         "`curl`.  ⭐ Cioe' e' il giro intero di P1, non un pezzo.\n"
         "       ⚠ **Non dice** che P1 veda un binario stantio: quello lo "
         "guarda il controllo C4, che nel giro sano e' gia' verde e che questo "
         "guasto non muove.  ⛔ E non dice niente su RCP, sull'autenticazione "
         "e sul ban: P1 dichiara apertamente di fermarsi prima del filo RCP.\n"
         "       ⚠ Il guasto si innesta nella COPIA "
         "`01-b12-copie/p1-remotix/pagina.c`, e P1 va lanciato con `SORG` su "
         "quella copia: il prodotto in `/media/REMOTIX/src/remotix` non si "
         "tocca mai.\n"
         "       ⚠ E si certifica **solo dalla macchina di prova**: "
         "`remotix/pagina.c` da `banchi/` non esiste (su CHUWI il prodotto sta "
         "in `../src/`), e `--provabile P1` da qui stampa «MANCA».",
)

# ── P5 — ⛔ la pagina pubblica un'impronta DIVERSA da quella dell'endpoint ────
guasto(
    "P5", "P5", "⛔ la pagina pubblica un'impronta di sessione DIVERSA da "
                "quella che `/impronta` dichiara — il difetto R1.14",
    os.path.join(COPIE, "p5-remotix", "pagina.c"),
    'a = sostituisci(p->html, "__IMPRONTA__", p->cert->impronta);',
    'a = sostituisci(p->html, "__IMPRONTA__", '
    '"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="); /* ' + MARCA + ' P5 — '
    'RCP.md §4.1-bis: la pagina porta un\'impronta ben formata e SBAGLIATA, '
    'mentre /impronta continua a dichiarare quella vera. */',
    "⛔ §4.1-bis, rilievo R1.14: se l'impronta scritta nella pagina e quella "
    "del certificato di sessione divergono, **la sessione WebTransport non si "
    "apre e nessun errore nomina l'impronta**.  Il sintomo che arriva a chi "
    "guarda e' *«WebTransport non si connette»*, che ha almeno quattro cause "
    "diverse.  ⭐ P5 e' l'unico banco che fa il confronto dalla parte del "
    "browser vero, su due motori: se resta verde, quel difetto lo trovera' un "
    "utente.  ⚠ E l'impronta storpiata e' **ben formata** apposta — 44 "
    "caratteri, base64 valido: un valore rotto farebbe fallire il banco sulla "
    "lunghezza, e allora il rosso non direbbe niente sul CONFRONTO",
    # ⛔ LA MARCA E' MISURATA, NON DEDOTTA — `[M]` 11 agosto 2026, macchina
    #    CHUWI (i browser stanno di qua), bersaglio la copia sulla **7501**,
    #    due giri veri alle 13:01:22 e alle 13:06:18 UTC:
    #
    #      sano   la frase compare **0** volte
    #      guasto la frase compare **1** volta, ed e' il punto 3 che cade:
    #             «la pagina pubblica «AAAA…=» e l'endpoint dice «PJ03…=»»
    #
    # ⭐ E la seconda meta' del criterio regge: nel giro sano il punto 3 stampa
    #    la riga OPPOSTA — «⭐ la pagina pubblica la stessa impronta
    #    dell'endpoint (§4.1-bis)» — e la frase scelta non c'e'.
    # ⚠ Il nome del segno («__IMPRONTA__») e la parola «impronta» da sola
    #   compaiono in tutt'e due i giri decine di volte: sarebbero la trappola
    #   gia' pagata su B7 con «CONGEDO».
    "sono due impronte diverse per lo stesso certificato di sessione",
    # ⛔ «ricostruisce», e la differenza con P1 e' misurata, non stimata: P1
    #    ricostruisce da se' come primo passo del proprio giro, P5 **no** —
    #    P5 trova un server gia' acceso e lo interroga.  Fra l'innesto e il
    #    giro ci vanno DUE cose: `costruisci.sh` sulla copia, e il server
    #    riacceso su quel binario.  Chiamarlo «leggero» farebbe girare P5
    #    contro il binario di prima, che e' il difetto n.2 di questo file —
    #    il guasto che non e' stato innestato, con l'aria di esserlo.
    "ricostruisce",
    "fasi/01-filo-nudo.md P5 · RCP.md §4.1-bis (R1.14) · README.md «CHE COSA "
    "FARE ADESSO» punto 5",
    nota="⭐⭐⭐ **P5 E' CERTIFICATO — `[M]` la notte fra l'11 e il 12 agosto "
         "2026, contro la copia sulla 7501: 0 → 1 → 0.**  Giro sano VERDE su "
         "tutt'e due i motori, giro col guasto ROSSO con la marca, giro "
         "risanato VERDE — e la frase-marca compare **0 volte nel sano, 1 nel "
         "guasto, 0 nel risanato**, contate sui tre giri di quella notte e non "
         "su una misura di ieri.\n"
         "       ⭐ E il binario risanato e' tornato `d69df441…`, cioe' **lo "
         "stesso byte per byte** di quello del giro sano: il guasto non e' "
         "rimasto addosso al codice, e non e' dedotto dal verde.\n"
         "       ⛔⭐ **E IL GUASTO DIMOSTRA MENO DI QUEL CHE IL SUO TITOLO "
         "DICE, ed e' giusto scriverlo.**  Con l'impronta falsa nella pagina, "
         "le gambe `p-sessione` restano CONFORMI su tutt'e due i motori: la "
         "sessione WebTransport **si apre lo stesso**.  ⭐ La ragione e' del "
         "PRODOTTO ed e' §4.1-bis applicato: `pagina.html` **ritira "
         "`/impronta` prima di ogni tentativo** e usa quella, tenendo "
         "l'impronta servita solo come ripiego — e quando le due divergono lo "
         "DICE («il certificato e' stato ruotato…»).  ⇒ Quel che questo guasto "
         "prova e' che **P5 vede la divergenza**, che e' cio' per cui P5 "
         "esiste; ⛔ NON prova che la divergenza uccida la sessione, perche' su "
         "questo prodotto non la uccide.  ⚠ Il sintomo descritto in R1.14 "
         "resta quello di un prodotto che l'impronta NON la ritira.\n"
         "       ⭐ **AGGIORNATO LA NOTTE FRA L'11 E IL 12 AGOSTO 2026 — I "
         "QUATTRO OSTACOLI DELL'ELENCO IN FONDO SONO CADUTI TUTTI E QUATTRO.**\n"
         "       ⭐ **1 — il congedo di Firefox: CURATO NEL PRODOTTO E "
         "MISURATO.**  L'imputato era la pagina (`congeda_corrente` azzerato un "
         "millisecondo dopo `SESSIONE`), su tutt'e due i motori; la cura e' in "
         "`src/pagina.html` e in `src/rcp.c` (il `posto LASCIATO` che sulla "
         "strada del congedo non veniva scritto).  Fuori fase e dichiarata: "
         "`DECISIONI.md` §1.12.\n"
         "       ⭐ **2 — la scena: CURATA.**  Due schede, cosi' `ctrl+w` chiude "
         "la SCHEDA e non fa uscire Firefox; il contatore pretende `motivo "
         "0x01`; la scena si ripulisce prima di ogni browser; e la striscia dei "
         "dati di Firefox non sposta piu' la pagina sotto i clic misurati.\n"
         "       ⭐ **3 — lo sblocco: CURATO.**  `SSH_ROOT` sceglie il portatore "
         "dei comandi privilegiati (`v1/strumenti/sshpw.py` digita la password "
         "su un pty).  ⇒ **La gamba N2 gira, per la prima volta.**\n"
         "       ⭐⭐ **E IL RISULTATO CHE CONTA**: `[M]` la gamba `p-sessione` "
         "e' **CONFORME su TUTT'E DUE i motori** — 15 controlli, 0 guasti, "
         "`violazione-31` a zero, il posto preso e lasciato.\n"
         "       ⭐ **4 — i tre giri sano → guasto → sano: FATTI**, la notte "
         "fra l'11 e il 12 agosto 2026, contro la copia sulla **7501** accesa "
         "con `01-p5-accendi.sh`.  ⛔ Fra un passo e l'altro sono andate DUE "
         "cose e non una — `costruisci.sh` sulla copia **e** il server "
         "riacceso — e che siano andate lo dice l'impronta del binario, che "
         "cambia (`d69df441…` → `117911ca…` → `d69df441…`) invece di essere "
         "creduta.\n"
         "       ⛔ E il primo tentativo di giro sano e' uscito ROSSO con "
         "tutt'e quattro le gambe CONFORMI: il registro del server aveva un "
         "buco di **37.120 byte NUL** — `svuota-registro` chiamato a server "
         "vivo — e `grep` diventato cieco leggeva «NON LETTO» dove c'era il "
         "nostro indirizzo, mandando lo sblocco sul SERVER.  Curato in tre "
         "punti e rimisurato (`LEZIONI.md` §1.9 punto 9).\n"
         "       ⚠ *Quel che segue e' la fotografia della sera dell'11, tenuta "
         "perche' spiega da dove si partiva — e perche' il verdetto vecchio si "
         "corregge con una misura nuova, non cancellandolo.*\n"
         "       ⛔ **P5 E' PROVATO E NON RIUSCITO — e non «non provabile qui», che e' "
         "l'altra cosa** (R12-A.31).  Il guasto e' stato innestato, "
         "ricostruito e girato per davvero la sera dell'11 agosto 2026.\n"
         "       ⛔ **IL MOTIVO NON E' DEL GUASTO: E' CHE IL GIRO SANO DI P5 "
         "NON E' VERDE.**  `[M]` 11 agosto 2026, 13:01:22 UTC, contro la copia "
         "sulla 7501 (server acceso apposta, ban e socket suoi), Chrome "
         "151.0.7922.108 e Firefox 140.13.0esr, schermo `:79` 1280x1024:\n"
         "         · ⭐ **le quattro gambe N1 passano tutte e quattro**: "
         "l'impronta giusta APRE la sessione e quella storpiata FALLISCE, su "
         "tutt'e due i motori.  Cioe' il controllo che dice NO funziona;\n"
         "         · ⭐ **e su Chrome la stretta di mano arriva fino in fondo**: "
         "14 controlli su 15 — pagina servita, canale di controllo, "
         "negoziazione, `CREDENZIALI`, PAM «ammesso», `AMMESSO`, posto preso, "
         "`SESSIONE`.  Il secondo fisso di §4.4-bis misurato a **1063 ms**;\n"
         "         · ⛔ **il punto che cadeva era UNO: il congedo** — e "
         "⭐ **l'imputato adesso ha un nome, ed era il BANCO**.  Vedi il "
         "riquadro «L'ARBITRATO» qui sotto;\n"
         "         · ⚠ **su Firefox, in quel primo giro, il verdetto era SENZA "
         "DENOMINATORE**: il "
         "marcatore d'inizio della gamba `p-sessione` non e' mai arrivato al "
         "server (`marcatori: inizio ×0`), quindi il segmento di quel motore e' "
         "vuoto e non c'e' niente da giudicare.  ⚠ L'avviso del certificato "
         "**era** stato superato (il marcatore d'avvio era arrivato): a non "
         "arrivare e' la navigazione dentro la gamba.\n"
         "       ⭐⭐ **E LA CAUSA L'HA TROVATA UNA FOTOGRAFIA** — "
         "`01-p5-copie/firefox-p-sessione-1-pagina.png`, ed e' la seconda "
         "volta che succede a questo banco.  Nello scatto Firefox e' fermo "
         "sulla pagina del marcatore d'**avvio** (`/p5-firefox-avvio-…`, che "
         "il server serve con «non c'e'»), e ci sono **tre schede**: due "
         "residue della sonda N1 («B2 — la sonda della sessione») piu' quella "
         "d'avvio.  ⇒ `naviga()` ha battuto `ctrl+l`, l'URL e `Invio` **e la "
         "pagina non e' cambiata**.\n"
         "       ⛔ E il difetto ha un nome preciso, che si legge nel "
         "lanciatore: `fuoco \"REMOTIX\"` — l'unica riga che porta il fuoco "
         "sulla finestra giusta — sta **dentro il ramo di N2**.  Con "
         "`COMANDO_VIVO=no` quel ramo si salta, e si arriva alla gamba `P` "
         "**senza aver mai dato il fuoco a nessuna finestra**.  ⚠ Su Chrome "
         "non si e' visto perche' la finestra nuova prende il fuoco da se'.\n"
         "       ⛔ Cioe' il rosso di Firefox e' **del banco, non del "
         "prodotto**, e la cura e' una riga spostata: `fuoco` va chiamato "
         "prima di OGNI gamba, non dentro il ramo di una sola.  ⚠ Non e' stata "
         "applicata stasera: cambiare il pilota fra un giro e l'altro vorrebbe "
         "dire misurare due banchi diversi e chiamarli sano e guasto.\n"
         "       ══════════════════════════════════════════════════════════\n"
         "       ⛔⭐ **L'ARBITRATO — di chi era il congedo che non arrivava**\n"
         "       `banchi/01-p5-congedo.sh`, scritto apposta, `[M]` 11 agosto "
         "2026 ore 13:26 UTC, Chrome contro la copia sulla 7501.  Due scene "
         "nello stesso giro, e il testimone e' il **registro del server** "
         "(§8.1 parla di byte che escono, e a vederli arrivare e' chi riceve):\n"
         "         · **A — si naviga via** dalla barra (`ctrl+l`): «pagehide» "
         "scatta di sicuro ⇒ congedo **1**, posto LASCIATO **1**;\n"
         "         · **B — `ctrl+w`**, e il gesto e' verificato (finestre col "
         "titolo REMOTIX **1 → 0**) ⇒ congedo **1**, posto LASCIATO **1**, "
         "`STACCATO per silenzio` **0**.\n"
         "       ⭐⭐ ⇒ **LA PAGINA FA QUEL CHE §8.1 LE IMPONE.**  Il congedo "
         "esce per la strada 2 di §3.1 (il codice di chiusura), che e' "
         "esattamente quel che `src/pagina.html:325` dichiara di aspettarsi da "
         "Chrome.\n"
         "       ⛔ **L'imputato era il PILOTA di `01-p5-lancia.sh`**: la riga "
         "del `ctrl+w` batteva `xdotool` **senza la funzione `X`**, cioe' su un "
         "`DISPLAY` che non e' lo schermo finto.  Il tasto non arrivava, "
         "«pagehide» non scattava, e il banco scriveva *«nessun congedo, per "
         "nessuna delle due strade di §3.1»* — ⛔ **un'accusa al prodotto per un "
         "gesto mai fatto**, la settima veste di `LEZIONI.md` §1.9, e la "
         "seconda volta in questa fase dopo B3 (dove il colpevole era il "
         "buffer di Python).\n"
         "       ⚠ E il PRIMO giro dell'arbitrato ha sbagliato a sua volta, "
         "e si scrive: la scena A leggeva **zero** congedi perche' il segmento "
         "si chiudeva sul marcatore di fine, mentre li' «pagehide» scatta "
         "**mentre quella richiesta e' in volo** — la riga del congedo cadeva "
         "fuori.  Uno zero da segmento sbagliato ha la stessa faccia di uno "
         "zero vero.  Curato (`da()` invece di `fra()`) e rimisurato.\n"
         "       ══════════════════════════════════════════════════════════\n"
         "       ⭐ **LA CURA E' STATA APPLICATA, E I GIRI RIFATTI** — "
         "`X` davanti al `ctrl+w`, e `fuoco` portato **fuori dal ramo di N2**, "
         "davanti a ogni gamba.  `[M]` giro sano delle 13:29:41 UTC:\n"
         "         · ⭐⭐ **Chrome passa a CONFORME** — era NON-CONFORME;\n"
         "         · ⭐ **Firefox adesso MISURA** — era senza denominatore — e "
         "arriva a `SESSIONE`: **14 controlli su 15**, secondo fisso 1069 ms;\n"
         "         · ⛔ **ma su Firefox il congedo non esce lo stesso**, e "
         "⚠ **questa volta non e' il pilota**: dal registro del server, il "
         "client chiude con un **`FIN` nudo sul canale di controllo** "
         "(`⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2`), il "
         "posto e' `LASCIATO` in modo **ordinato** e `STACCATO per silenzio` "
         "vale **0** — cioe' il gesto e' arrivato e la sessione si e' chiusa "
         "bene, **senza dire perche'**.  §8.1 lo impone senza condizioni.\n"
         "       ⛔ **E' un rilievo di PRODOTTO (o del trasporto di Firefox), "
         "non di banco**, e i due non si distinguono dal registro del server: "
         "«la pagina non ha spedito» e «Firefox ha buttato via quel che la "
         "pagina ha spedito dentro `pagehide`» arrivano identici da questa "
         "parte.  ⭐ A separarli serve il registro del **browser**, e non e' "
         "roba di questo mandato.  ⚠ Nota che la pagina prevede il caso "
         "opposto — *«Chrome butta un messaggio spedito subito prima di "
         "chiudere, quindi la strada che regge e' il codice di chiusura»* — e "
         "su Firefox **non regge nessuna delle due**.\n"
         "       ⇒ Sano **1**, guasto **1**: lo stesso esito, e `giudica()` lo "
         "chiamerebbe «il difetto che B12 esiste per trovare».  ⛔ **Non lo "
         "e'**, e la marca lo dimostra: la frase del guasto compare 1 volta nel "
         "giro rosso e 0 in quello sano.  Il banco **vede** il guasto; e' il "
         "suo punto di partenza a non essere verde.  ⭐ E' la stessa forma di "
         "B8 e di B13, e la regola e' quella gia' scritta li': **un banco il "
         "cui giro sano non e' verde non si certifica**, e la cosa giusta e' "
         "lasciarlo NON CERTIFICATO invece di allargare l'atteso finche' "
         "torna.\n"
         "       ⚠ **Il terzo passo (risano) non e' stato fatto**, e si "
         "dichiara: con un sano gia' rosso non aggiungeva niente al verdetto. "
         "⭐ Che il guasto non sia rimasto addosso e' provato in modo piu' "
         "diretto: `--togli` ha riverificato il file, la copia e' tornata "
         "`md5 77f744cd…` — identica al prodotto — e la pagina servita sul filo "
         "e' tornata a pubblicare l'impronta vera.\n"
         "       ⭐ CHE COSA MANCA, in ordine di costo, perche' il prossimo "
         "giro non ricominci da capo:\n"
         "         1. ⛔ **il congedo di Firefox** — ed e' l'UNICO punto che "
         "separa P5 dal verde, adesso che Chrome e' CONFORME.  Va letto dal "
         "registro del **browser**: la pagina non spedisce, o Firefox butta via "
         "quel che spedisce dentro «pagehide»?  ⚠ E se l'imputato e' il "
         "prodotto, **non si cura dentro un giro di certificazione**: si scrive "
         "il rilievo e lo decide chi decide;\n"
         "         2. ⭐ **fatto**: `X` davanti al `ctrl+w` e `fuoco` fuori dal "
         "ramo di N2.  ⚠ Resta da aggiungere il nome del motore fra i titoli "
         "che `fuoco_prodotto` prova, e la ragione per cui non e' stato fatto "
         "stasera e' scritta accanto alla funzione;\n"
         "         3. **lo sblocco**: `01-p5-lancia.sh` chiama `enter.sh` "
         "dentro un `ssh -o BatchMode=yes`, che non ha nessuno che digiti la "
         "password di `sudo`.  ⇒ `COMANDO_VIVO=no`, e la gamba **N2 e' stata "
         "SALTATA in tutt'e due i giri**: questo giro non ha nessun controllo "
         "che dica NO sull'autenticazione, ⭐ e in cambio non ha speso nessun "
         "tentativo fallito, quindi nessun ban;\n"
         "         4. e allora, e solo allora, i tre giri sano → guasto → "
         "sano.\n"
         "       ⚠ La ricetta della scena, misurata e funzionante:\n"
         "         cp -a /srv/src/remotix /srv/src/01-b12-copie/p5-remotix\n"
         "         bash /srv/src/01-b12-copie/p5-remotix/costruisci.sh\n"
         "         <accendere sulla 7501 con --ban e --comando-socket propri>\n"
         "         IND=192.168.0.2 PORTA=7501 SOCK=/srv/src/tmp/sera-p15.sock \\\n"
         "           LOG_SERVER=/media/REMOTIX/src/tmp/sera-p15-browser.log \\\n"
         "           SCHERMO=:79 PORTA_LOC=8859 bash banchi/01-p5-lancia.sh\n"
         "       ⛔ E il guasto si innesta nella COPIA, mai nel prodotto: P5 "
         "vuole il server RIACCESO fra un passo e l'altro, e riaccendere il "
         "prodotto di casa con un guasto dentro lo metterebbe sotto i piedi di "
         "chiunque altro.",
)


# ── P5R — ⛔ IL GUASTO CHE TOGLIE LA CURA, NON IL VALORE ────────────────────
#
# Scritto il 12 agosto 2026 per il difetto D11: il guasto P5 qui sopra
# «copriva meno di quel che prometteva» — con l'impronta falsa la sessione si
# apre lo stesso, perche' la pagina RITIRA `/impronta` prima di ogni tentativo.
# ⇒ Questo toglie il ritiro.  Voce scritta da chi ha misurato
# (`banchi/01-p5-guasto-ritiro.py`), incollata dal coordinatore.
guasto(
    "P5R", "P5", "⛔ la pagina non RITIRA piu' l'impronta prima del tentativo "
                 "— la cura di §4.1-bis tolta, non il valore",
    os.path.join(COPIE, "..", "01-p5-copia-7522", "pagina.html"),
    "  const b64 = await impronta();",
    "  const b64 = IMPRONTA_SERVITA; /* " + MARCA + " P5-ritiro — "
    "RCP.md §4.1-bis: il RITIRO tolto, non il valore.  La pagina non chiede "
    "piu' /impronta e usa per sempre quella servita. */",
    "⛔ §4.1-bis chiude R1.14 con **due** cose, e il guasto P5 ne prova una "
    "sola.  Che un'impronta divergente uccida la sessione lo prova la gamba "
    "N1; che la pagina **ne ritiri una fresca prima di ogni tentativo** non lo "
    "provava nessuno — ed e' la meta' che il prodotto potrebbe perdere in una "
    "riga.  ⭐ La prova che questo guasto guarda un'altra cosa e' misurata: "
    "col ritiro tolto, il controllo del guasto P5 — *«la pagina pubblica la "
    "stessa impronta dell'endpoint»* — resta **VERDE**, perche' il valore non "
    "e' toccato.  ⇒ I due guasti sono complementari, e nessuno dei due copre "
    "R1.14 da solo",
    # ⛔ LA MARCA E' MISURATA — `[M]` 12 agosto 2026, tre giri veri contro la
    #    copia sulla **7522** (accesa apposta con prefisso, ban e socket
    #    propri: la 7501 non e' stata toccata), browser su CHUWI, Chrome 151 e
    #    Firefox 140.13.0esr — `0 → 4 → 0`, la marca 0 · 4 · 0 volte.
    #    ⭐ E che il guasto sia entrato e uscito lo dice la PAGINA CHIESTA AL
    #      SERVER: sha256 `a2cda27c…` → `3b0080b1…` → `a2cda27c…`.
    "NESSUN RITIRO DI /impronta IN QUESTA GAMBA",
    # ⚠ «ricostruisce» SBAGLIA PER ECCESSO, ed e' voluto.  Il genere onesto
    #   sarebbe **`riaccendi`**: `pagina.html` non entra in nessun binario
    #   (`src/pagina.c:590` lo legge una volta sola all'accensione), quindi
    #   compilare non serve — ma «leggero» farebbe girare P5 contro la pagina
    #   di PRIMA, che e' il difetto n.2 di questo file.  Finche' `riaccendi`
    #   non esiste si tiene il sovrainsieme: si sbaglia per eccesso, mai per
    #   difetto, che e' il verso in cui un guasto si perde.
    "ricostruisce",
    "fasi/rapporti/DIFETTI-12-agosto.md D11 · RCP.md §4.1-bis (R1.14)",
    nota="⛔ CHE COSA QUESTA CERTIFICAZIONE NON DICE.  Col guasto dentro la "
         "sessione WebTransport **si apre lo stesso**: il bersaglio e' appena "
         "riacceso, quindi l'impronta servita con la pagina e' fresca e "
         "coincide.  ⇒ Questo guasto prova che P5 vede sparire **la cura**, "
         "non che la sessione muoia.\n"
         "       ⚠ E la `[?]` che resta, scritta come non saputa: **la "
         "rotazione vera non e' stata misurata**.  Il difetto che R1.14 "
         "descrive e' una scheda aperta da due settimane su un certificato "
         "ruotato, e per vederlo servirebbe far ruotare il certificato di "
         "sessione **sotto una pagina gia' caricata**.  Non e' stato fatto, e "
         "questa voce non lo spaccia per fatto.",
)


# ===========================================================================
# ⭐⭐ I BANCHI DELLA FASE 3 — messi a catalogo il 13 agosto 2026
#
# ⛔ E SI ERA ENTRATI DA NON CERTIFICATI, tutti e sette.  Il campo `marca` di
#    queste voci nasceva **vuoto**, e non per dimenticanza: la regola di questo
#    file e' che una marca **si misura innestando il guasto e leggendo che cosa
#    il banco stampa**, poi si verifica ASSENTE dal giro sano.  Una marca
#    dedotta dal sorgente e' la forma **E5** — un fatto che era una deduzione
#    mai riverificata — ed e' esattamente cio' che il rilievo R12-A.3 ha pagato
#    su B4 e su B7.  ⇒ Qui si scrive **dove guardare**, non che cosa si vedra'.
#
# ⚠ Da cui: `--giudica` li rifiuta finche' il campo e' vuoto, e il conto onesto
#   li conta **MAI PROVATI**.  Non sono «puliti»: sono banchi nuovi che nessuno
#   ha ancora messo alla prova.
#
# ⭐⭐⭐ LA SERA DEL 13 AGOSTO LE «DOVE GUARDARE» SONO STATE ANDATE A GUARDARE,
#      e il metodo ha retto: le candidate scritte per `03-b14` e per `03-marca`
#      erano **giuste tutt'e due**, misurate 0 nel sano e >0 nel guasto su giri
#      veri.  ⇒ Scrivere «dove guardare» invece di indovinare la stringa non ha
#      rallentato niente: ha fatto trovare la marca al primo colpo, e con la
#      prova che nel sano non c'era.
# ⛔ E DUE VOCI SONO ENTRATE STASERA — `03-b15` e `03-b18` — nate gia' con la
#    marca MISURATA, che e' il modo in cui una voce dovrebbe nascere.
# ⚠ Restano col campo vuoto `03-b16`, `03-b17`, `03-b19`, `03-deposita` e
#   `03-scena`.  ⛔ E `03-b17` non e' «da fare»: il suo giro SANO su CHUWI e'
#   BOCCIATO 30 su 31, tre giri su tre, sempre sullo stesso controllo e **del
#   ponte** — la sua nota lo dice, e la cosa giusta e' lasciarlo NON
#   CERTIFICATO invece di allargare l'atteso finche' torna.
#
# ⛔ E i tre SENZA NUMERO sono quelli che si dimenticano — `03-scena`,
#    `03-marca`, `03-deposita` — proprio perche' non hanno un numero che li
#    chiami.  Due dei tre non giudicano il prodotto: sono **lo strumento** e
#    **la scena**, cioe' la meta' di cui `PIANO.md` §0.4 dice che *«un difetto
#    nel banco non lo trova niente, e avvelena ogni misura successiva perche'
#    da' fiducia»*.
# ===========================================================================

# ── 03-scena — l'istante della marca si congela ────────────────────────────
guasto(
    "03-scena", "03-scena",
    "l'istante dipinto nella marca si prende UNA VOLTA SOLA: ogni fotogramma "
    "dichiara di essere stato composto all'istante del primo",
    os.path.join(COPIE, "03-scena.c"),
    "\tuint64_t istante = ora_monotonica_us();\n",
    "\t/* " + MARCA + " 03-scena — l'istante della marca si prende UNA VOLTA\n"
    "\t * SOLA: il numero del disegno continua a crescere, i pixel continuano\n"
    "\t * a cambiare, e ogni fotogramma dichiara l'istante del primo.  Se il\n"
    "\t * controllo P7 resta verde, «la scena si muove» sta guardando il\n"
    "\t * CONTATORE e non l'orologio. */\n"
    "\tstatic uint64_t istante_congelato_b12 = 0;\n"
    "\tif (!istante_congelato_b12) istante_congelato_b12 = ora_monotonica_us();\n"
    "\tuint64_t istante = istante_congelato_b12;\n",
    "⛔ L'istante dipinto nella marca e' **la partenza dell'anello del "
    "ritardo**: la mediana di 74,58 ms della fase 3 nasce da li'.  ⭐ E questo "
    "guasto e' scelto perche' **non produce nessun sintomo**: i pixel "
    "cambiano, il conto dei disegni cresce, il CRC e' giusto, e P1, P4, P6, "
    "M6 e M8 restano tutti verdi — P6 in particolare, perche' l'istantanea "
    "riceve la STESSA variabile e dichiarato e dipinto continuano a "
    "coincidere.  ⇒ L'unico che puo' vederlo e' `P7 la scena si muove`, che "
    "confronta gli istanti in senso STRETTO.  Se P7 non lo vede, ogni misura "
    "di ritardo della fase 3 poggia su un orologio che non e' un orologio",
    # ⛔ NON MISURATA — e va misurata prima di poter certificare 03-scena.
    # ⭐ Dove guardare: la riga «misura» di P7, che `Conto.esito()` stampa come
    #    JSON PURO, senza codici ANSI in mezzo — e quello conta, perche'
    #    `marca_vista()` cerca la stringa nel file COLORATO e una marca che
    #    attraversi un codice ANSI non combacerebbe mai (e' la ragione per cui
    #    la riga con «NO» non si puo' usare).  Candidata da verificare:
    #    «"delta_istante_us": [0» — nel giro sano quei delta sono positivi.
    "",
    "ricostruisce",
    "fasi/03-movimento.md, step 2 «La scena che si dichiara» · "
    "LEZIONI.md §1.1 e §1.7 · fasi/00-ambiente.md",
    nota="⛔ **03-scena NON e' un banco che giudica il prodotto: e' la SCENA**, "
         "e il prodotto non e' nemmeno in campo (la catena e' "
         "`03-scena.c → libx265 → ffmpeg`).  ⭐ E' a catalogo per la ragione "
         "opposta a quella degli altri: un attrezzo di scena che sbaglia non "
         "fa diventare rosso niente — **avvelena ogni misura che ci si "
         "appoggia**.  E ci si appoggiano `03-b14`, `03-b15`, `03-b17` e "
         "`03-b18`.\n"
         "⚠ IL GUASTO SI INNESTA NELLA COPIA E IL GIRO SI LANCIA DALLA COPIA: "
         "`03-scena-accendi.sh` compila `$QUI/03-scena.c` senza nessuna "
         "variabile d'ambiente, quindi un giro lanciato dall'originale "
         "compilerebbe il sorgente SANO e resterebbe verde col guasto in mano. "
         "Da cui il CORREDO intero.\n"
         "⚠ E va dato un `PORTA=` diverso da quello del giro sano: la cartella "
         "di lavoro e il binario si chiamano `/tmp/remotix-03-scena-$PORTA`, e "
         "due passi sulla stessa porta si riuserebbero il binario.\n"
         "⚠ Effetto collaterale letto e dichiarato: con l'istante congelato "
         "anche `ultimo_disegno_us` si ferma, e `03-marca.py` calcola una "
         "durata ≤ 0 ⇒ `disegni_al_secondo` esce `null` nella lettura da "
         "fuori.  Non fa cadere nessun controllo, ma si vede.\n"
         "⭐ E c'e' una SECONDA STRADA gia' in casa, che copre un'altra cosa: "
         "`03-scena.c` porta **il proprio guasto dentro** (`--guasto rientro`) "
         "e `03-scena-certifica.sh` fa gia' sano → guasto → risanato su P13. "
         "E' la forma di B11, e certifica il rilevatore della corsa a vuoto — "
         "non la scena come strumento di tempo.  Le due sono complementari.",
)

# ── 03-marca — il terzo setaccio del lettore disarmato ─────────────────────
guasto(
    "03-marca", "03-marca",
    "⛔ al lettore della marca si disarma il controllo del CRC: resta con due "
    "setacci su tre",
    os.path.join(COPIE, "03-marca.py"),
    "    if crc_letto != crc_atteso:\n",
    "    if False and crc_letto != crc_atteso:   # " + MARCA + " 03-marca —\n"
    "        # il terzo setaccio disarmato: il sync passa, il CRC no.  Il\n"
    "        # lettore restituisce un numero di disegno FALSO invece di\n"
    "        # rifiutare la lettura.\n",
    "⛔ E' **il difetto che non produce nessun sintomo**: sui fotogrammi veri "
    "il pittore continua a scrivere CRC giusti, quindi ogni misura di ritardo "
    "resta identica al microsecondo e nessun altro controllo si muove.  Quel "
    "che sparisce e' **la capacita' di dire di no** — e il lettore che dice "
    "sempre si' e' quello che il suo stesso certificatore dichiara di temere: "
    "*«un rilevatore che dice sempre si' misura zero ed e' felice a torto»*.  "
    "⭐ Il danno concreto ha un nome gia' scritto: con il CRC spento un "
    "fotogramma corrotto verrebbe letto come fresco, cioe' **M6 diventerebbe "
    "cieco proprio sul guasto che esiste per vedere** («il fotogramma e' del "
    "giro prima» travestito da fotogramma nuovo)",
    # ⭐⭐ MISURATA il 13 agosto 2026 sera, e la candidata scritta qui sopra ha
    #     retto: e' la riga «misura» del controllo «P5 un bit invertito», che
    #     nel giro sano e' `{"lette_a_torto": []}` e col guasto si riempie di
    #     celle lette a torto.  Nessun codice ANSI dentro (i colori stanno
    #     sulla riga OK/NO di sopra, verificato con `cat -v`).
    # ⛔ Le DUE META', contate sull'uscita dei tre giri veri:
    #    **0 nel sano, 1 nel guasto, 0 nel risanato**.
    # ⭐ E una terza prova, che vale piu' delle prime due: la marca da' **0**
    #    anche sul giro rosso per CARTELLA VUOTA (l'ambiente che manca, cioe'
    #    la trappola n.1).  ⇒ Questa marca non confonde il guasto col guasto
    #    d'ambiente, ed e' esattamente quel che a un campo `marca` si chiede.
    # ⚠ E DUE COSE DA NON USARE COME MARCA, per non ripetere R12-A.3, e adesso
    #    e' MISURATO e non piu' temuto:
    #    · «P5 un bit invertito» — 1 volta nel giro SANO: e' il nome del
    #      controllo, non il suo esito;
    #    · «marche rotte RIFIUTATE (il CRC le prende); zero lette a torto» —
    #      1 volta nel giro SANO.
    #    · la riga dell'elenco finale — ha i codici ANSI in mezzo.
    '{"lette_a_torto": [{"cella"',
    "leggero",
    "web.md §6.3 controllo P3 · LEZIONI.md §1.2 e §1.9 · "
    "fasi/rapporti/F2-6-giudizio.md (il «giro» di M8)",
    nota="⛔ **03-marca non giudica il prodotto: e' lo STRUMENTO DI MISURA**, e "
         "sopra ci sta il numero della fase.  Ci si appoggiano `03-b17` e "
         "`03-b19` (che lo caricano con `importlib` invece di riscriverlo), "
         "`03-b14` e l'intero `03-scena-certifica.sh`.  ⇒ Se sbaglia, i banchi "
         "del ritardo **continuano a dare un numero**, e il numero e' falso: "
         "nessun sintomo a valle.\n"
         "⚠ Il guasto si innesta nella COPIA e il giro si lancia dalla copia — "
         "`03-marca-certifica.py` carica `03-marca.py` dalla PROPRIA cartella "
         "con `importlib`.  Da cui il CORREDO intero.\n"
         "⚠ E si e' scelto di far cadere **P5** (sei celle invertite a "
         "posizioni fisse, cinque delle quali fuori dal byte del sync ⇒ rosso "
         "deterministico) e non **P3** (il rumore casuale dovrebbe azzeccare "
         "sync E versione: circa un falso positivo atteso su tutto il giro, "
         "cioe' un rosso su cui non si puo' contare).\n"
         "⚠ `ffmpeg` e `libx265` decidono l'esito di P4 e NON sono impronte di "
         "questo catalogo: senza ffmpeg P4 esce «NON MISURATO», che e' una "
         "terza cosa e non un verde.\n"
         "⭐⭐ **CERTIFICATO IL 13 AGOSTO 2026 SERA — ed e' la voce che vale di "
         "piu', perche' su `03-marca.py` poggia la mediana 74,58 ms della "
         "fase.**  Tre giri sulla COPIA di `01-b12-copie/`, con "
         "`--applica`/`--togli` del catalogo stesso: sano **0** (21 controlli, "
         "21 passati) → guasto **1** (21 controlli, 20 passati, **1 fallito, e "
         "il fallito e' P5**, cioe' esattamente il setaccio disarmato) → "
         "risanato **0** (21 su 21).  `03-marca.py` tornato "
         "`5d7fa2783c968076d76c6f84adf53799d1c489f9772b53e009a8f3b41408fce7`, "
         "byte per byte l'originale.  E l'uscita del risanato e' identica riga "
         "per riga a quella del sano (`diff` vuoto).\n"
         "⛔⛔ **E `atteso_sano = 0` VALE SOLO SE `--cartella` HA DENTRO I "
         "FOTOGRAMMI VERI**, ed e' la cosa che chi rifa' la prova deve sapere "
         "prima: con la cartella VUOTA il giro **sano** esce **1** — 17 "
         "controlli invece di 21, con P6 e P7 «NON MISURATO».  ⇒ Misurerebbe "
         "un rosso che non e' il guasto.  ⚠ I giri di stasera hanno usato i "
         "tre fotogrammi 1920x1080 di un giro di `03-scena` del 13 agosto "
         "(`/tmp/remotix-03-scena-7602`), e quella cartella sta su **tmpfs**: "
         "sparisce al riavvio.  Nel giro di norma li produce "
         "`prepara_fotogrammi` dentro `03-scena-certifica.sh:670`, e va "
         "riacceso.\n"
         "⭐ SECONDO SINTOMO TROVATO, e smentisce di poco una frase scritta "
         "qui sopra: col CRC disarmato il controllo «P1 margine di "
         "scorrimento» scende da **10 px a 9**.  Resta VERDE (la soglia "
         "dichiarata e' 4), quindi «nessun altro controllo si muove» regge "
         "come **esito** ma non come **numero** — il CRC e' anche cio' che fa "
         "proseguire la ricerca di posizione, e spento il lettore si "
         "accontenta della prima lettura falsa.  ⚠ Non e' usabile come marca: "
         "quella riga e' verde in tutt'e due i giri.",
)

# ── 03-deposita — il deposito che si tronca invece di crescere ─────────────
guasto(
    "03-deposita", "03-deposita",
    "il deposito degli esiti si apre in scrittura invece che in coda: resta "
    "solo l'ultima riga",
    os.path.join(COPIE, "03-deposita.py"),
    '    with open(esiti, "a") as f:\n',
    '    with open(esiti, "w") as f:   # ' + MARCA + ' 03-deposita — il\n'
    '        # deposito si TRONCA a ogni riga: resta solo l\'ultima, la riga\n'
    '        # stampata a schermo e\' identica a quella del giro sano, e il\n'
    '        # codice d\'uscita resta 0.\n',
    "⛔ Il deposito esiste perche' la cartella di lavoro sta in `/tmp` e su "
    "quella macchina **il rootfs vive in RAM e si azzera al riavvio**: senza, "
    "dopo un riavvio resterebbe *il ricordo che «erano verdi»* e non i numeri. "
    "⭐ Con questo guasto la riga a schermo e' **identica**, il codice "
    "d'uscita resta **0** e il giro esce **tutto verde**: a sparire e' la "
    "storia, cioe' esattamente la cosa per cui il file e' stato scritto",
    # ⛔ NON MISURATA, e qui il motivo e' piu' grave che altrove: vedi la nota.
    "",
    "leggero",
    "LEZIONI.md §2.5-bis (il rootfs in RAM) · fasi/03-movimento.md step 2 · "
    "REVIEWER.md E1 (la catena dichiarata)",
    nota="⛔⛔ **QUESTA VOCE NON E' CERTIFICABILE OGGI, E NON PER LA MARCA "
         "MANCANTE: PERCHE' NON ESISTE IL CONTROLLO CHE POTREBBE DIVENTARE "
         "ROSSO.**  `[M]` 13 agosto 2026, verificato leggendo: nessuno "
         "rilegge `03-scena-esiti.jsonl` — `03-scena-certifica.sh` legge gli "
         "esiti del METRO in `/tmp`, non il deposito.  ⇒ Innestare questo "
         "guasto oggi lascerebbe il giro **tutto verde**, e la riga direbbe "
         "«il banco non vede il guasto» di un banco che **non ha nessun "
         "occhio puntato li'**.\n"
         "⭐ E il controllo che manca costa due righe e non ha bisogno di "
         "niente: contare le righe del deposito PRIMA e DOPO il giro e "
         "pretendere `dopo == prima + 2`, poi rileggere l'ultima riga e "
         "pretendere `quanti_giri == 4` per il giro di M8.  Finche' non c'e', "
         "questa voce sta a catalogo come **dichiarazione di un buco**, che e' "
         "il suo mestiere: e' il gemello negativo che non c'e'.\n"
         "⚠ Un secondo guasto, piu' fine, per quando il controllo esistera': "
         "sostituire il ramo `except` che appende «non si e' letto» con un "
         "`continue` — `quanti_giri` scenderebbe **in silenzio**, che e' il "
         "conto gonfiato al contrario.",
)

# ── 03-b14 — un tetto di sicurezza sulla cadenza chiesta ───────────────────
guasto(
    "03-b14", "03-b14",
    "un tetto «di sicurezza» a 60 sulla cadenza proposta: si chiede 120 e si "
    "negozia 60, e il numero che esce porta l'etichetta sbagliata",
    os.path.join(COPIE, "03-b14-metro.c"),
    "\tstruct spa_fraction massima = SPA_FRACTION(cadenza, 1);\n",
    "\t/* " + MARCA + " 03-b14 — un tetto «di sicurezza» a 60 sulla cadenza\n"
    "\t * proposta: si chiede 120, si negozia 60, e la cella continua a\n"
    "\t * chiamarsi «120».  §1.8: quando si chiede un componente per nome si\n"
    "\t * verifica che abbia obbedito. */\n"
    "\tstruct spa_fraction massima = SPA_FRACTION(cadenza > 60 ? 60 : cadenza, 1);\n",
    "⛔ §1.8: *«quando si chiede un componente per nome si verifica che abbia "
    "obbedito»*.  Con questo tetto la cella B nasce a **60 Hz invece che a "
    "120**, e la cella C — «monitor fermo a 120, freno a 60» — misura in "
    "realta' 60 contro 60.  ⭐ E il guasto e' scelto perche' **tutti i numeri "
    "restano plausibili**: il controllo positivo (10 Hz) continua a "
    "funzionare, quello negativo pure, nessuna cella si rompe, e la "
    "conclusione **M3 diventa falsa senza che una riga sembri strana**.  ⇒ Se "
    "B14 non lo vede, la riga «monitor 120 + freno 90 ⇒ 61,4 consegnati» "
    "l'avrebbe prodotta uno strumento che quei 120 non li ha mai chiesti — "
    "che e' la forma gia' pagata in questa stessa fase, «un verde in catalogo "
    "lo produceva lo STRUMENTO»",
    # ⭐⭐ MISURATA il 13 agosto 2026 sera, e la candidata scritta qui sopra
    #     ha retto: `cella()` la stampa con `ko()`, ed e' la riga «⛔ chiesto
    #     maxFramerate 120, FISSATO 60.000 — il numero che segue NON e' la
    #     misura di 120 (§1.8)».
    # ⛔ Le DUE META', contate sull'uscita dei tre giri veri e non sul sorgente:
    #    **0 nel sano, 1 nel guasto, 0 nel risanato**.
    "chiesto maxFramerate 120, FISSATO 60",
    "ricostruisce",
    "fasi/03-movimento.md step 1 · gnome.md §8.2 e §13 (M3) · "
    "LEZIONI.md §1.1, §1.2, §1.8",
    nota="⭐⭐⭐ **IL BANCO E' STATO CURATO E POI CERTIFICATO — 13 agosto 2026 "
         "sera.**  Fino a stasera questa nota diceva «NON CERTIFICABILE: "
         "`03-b14-cadenza.py` ESCE SEMPRE 0», e diceva il vero: `esegui()` "
         "finiva con `return 0` e `ko()` si limitava a **stampare**, quindi "
         "col guasto dentro il rosso sarebbe rimasto **soltanto nel testo** e "
         "`giudica()` avrebbe scritto «col guasto ha dato lo stesso esito del "
         "sano» — il difetto che B12 esiste per trovare, dentro il banco che "
         "ha prodotto la legge della griglia.\n"
         "⭐ LA CURA: `ko()` conta i rossi e `esegui()` chiude con "
         "`return 1 if ROSSI else 0`; il 2 (versioni, compilatore, `scp`) e il "
         "3 (sessione GNOME assente) restano quel che erano, cioe' "
         "attrezzatura che manca.  ⛔ E il conto sta dentro `ko()` e non "
         "accanto alle 29 chiamate perche' sei rossi escono da `cella()`, che "
         "ritorna presto: scritti a mano se ne sarebbero persi per strada.  ⚠ "
         "Nessuna misura e' stata toccata — per `ko()` non passa nessun numero.\n"
         "⭐⭐ **I TRE GIRI, VERI, SULLA SESSIONE GNOME DI NIC-OS**: sano "
         "**0** → guasto **1** → risanato **0**, con `--secondi 10 "
         "--riscaldamento 3` e la marca a **0 / 1 / 0**.  Il metro guasto e' "
         "tornato `284614ad3d15de42891a6c57342be1e4ff24d8bfb91709884f013f06de"
         "398928`, byte per byte l'originale.  ⛔ E il guasto **compila "
         "pulito** — `gcc -std=gnu11 -Wall -Wextra -O2`, uscita 0, verificato "
         "PRIMA del giro: il rosso non e' quello della trappola n.1.  ⛔ Le "
         "tre porte d'altri contate prima e dopo in tutt'e tre i giri "
         "(7448: 2·2 · 7501: 2·2 · 7561: 2·2) e **nessun monitor lasciato "
         "addosso alla macchina**.\n"
         "⛔⭐ E COL GUASTO NON CADE SOLO LA MARCA: cadono anche «⛔ L'IPOTESI "
         "NON REGGE» e «nemmeno il freno intermedio porta ai 60», perche' il "
         "monitor nasce a 60 e la cella C misura 60 contro 60 — cioe' il "
         "guasto morde esattamente dove la voce diceva che avrebbe morso.\n"
         "⛔⛔ **E `atteso_sano = 0` VALE PER IL GIRO DI NORMA (celle A-D) E "
         "NON PER GLI ALTRI DUE**, e non e' una deduzione: i tre registri gia' "
         "esistenti sono stati ripassati nei verdetti del banco CURATO senza "
         "rimisurare niente.  `03-b14-esiti.jsonl` (il giro che ha prodotto i "
         "**61,4 fps a monitor 120 / freno 90**) da' **0** ⇒ l'atteso e' "
         "giusto.  Ma `03-b14-esiti-scena2.jsonl` darebbe **1** (la cella D "
         "e' crollata a 0,04 fps, con la scena morta e il palco cambiato "
         "sotto) e `03-b14-esiti-griglia.jsonl` darebbe **1** — i suoi DUE "
         "soli punti hanno `scena_sul_mio_monitor = false`, quindi "
         "`verdetto_griglia` li conta **contaminati** e stampa «la legge NON "
         "regge su 0 punti su 0».  ⇒ ⚠ Chi certifichera' `--scena2` o "
         "`--griglia` deve dichiarare l'atteso di QUELLA forma di giro, "
         "oppure ripulire la scena: **non si arrotondano con questa**.\n"
         "⛔ E resta un `[?]` che va detto forte: la **griglia di record e' "
         "contaminata in tutt'e due i punti**.  Il 61,4 viene dalla cella D, "
         "che e' pulita (scena 115,07 sul mio monitor, palco stabile), ma "
         "chiunque citi «la legge della griglia» appoggiandosi a "
         "`03-b14-esiti-griglia.jsonl` sta citando due punti che il banco "
         "stesso rifiuta.  ⚠ Non e' stato toccato niente: e' una misura da "
         "rifare, non un numero da correggere.\n"
         "⚠ La scena: gira su NIC-OS dentro la sessione GNOME headless gia' "
         "viva, che il banco **verifica e non ferma mai**; il soggetto e' "
         "**Mutter**, non il prodotto — nessun server, nessun browser.\n"
         "⚠ Il guasto va innestato nella COPIA del metro e il giro lanciato "
         "dalla copia del banco: `costruisci_e_spedisci()` compila "
         "`$QUI/03-b14-metro.c` con un percorso fisso.\n"
         "⚠ E `03-marca.py` + `03-scena.c` entrano nel conto **solo** col giro "
         "`--scena2`; col giro di norma la scena e' quella EGL di B14.",
)

# ── 03-b16 — la riga di stile che tiene la barra sempre presente ───────────
guasto(
    "03-b16", "03-b16",
    "⛔ si toglie dalla pagina la riga che tiene la barra verticale sempre "
    "presente: la vista cambia sotto la tela quando la tela si accende",
    os.path.join(COPIE, "b16-albero", "src", "pagina.html"),
    "  html { overflow-y: scroll; }",
    "  /* " + MARCA + " 03-b16 — la riga di stile che tiene la barra\n"
    "     verticale sempre presente, tolta.  Niente si rompe: la pagina si\n"
    "     impagina identica finche' la tela resta spenta. */",
    "⛔ E' un difetto che **il prodotto stesso documenta come curato per "
    "caso**, e che nessun'altra pretesa guarda.  Senza quella riga, "
    "accendendo la tela il documento diventa quattro volte piu' alto "
    "(`scrollHeight` da 788 a 1288, misurato e scritto dentro `pagina.html`), "
    "**compare la barra verticale**, `clientWidth` cala di una quindicina di "
    "pixel, alla tela si da' la larghezza vecchia — e riparte la famiglia «la "
    "barra compare e la vista resta quella di prima», cioe' proprio la "
    "famiglia per cui il 13 agosto una cura era stata scritta e poi "
    "**RITIRATA**.  ⭐ A tela spenta non produce **nessun sintomo**, e a "
    "vederlo e' un caso solo: `V3s`, che pretende la larghezza della tela "
    "uguale a quella disponibile",
    # ⭐⭐ MISURATA il 13 agosto 2026 sera: 0 nel sano, 1 nel guasto, 0 nel
    #     risanato.  E' il conto finale di `principale()`, stampato da `ko()`,
    #     e la marca sta tutta DOPO il reset ANSI della riga.
    # ⛔⭐ E LA CANDIDATA SCRITTA QUI SOPRA ERA SBAGLIATA DI UN PEZZO, ed e' il
    #     genere di errore per cui questo campo si MISURA invece di dedurlo:
    #     diceva «sano/V3s: rosso (1 guai)», ma i guai sono **3**.  Scritta col
    #     conteggio dentro, la marca avrebbe dato **0 anche nel giro guasto** e
    #     la certificazione sarebbe caduta per una virgola — cioe' il banco
    #     sarebbe risultato «rosso per un'altra causa» proprio mentre faceva
    #     esattamente il suo mestiere.  ⇒ La marca giusta e' senza il conteggio.
    # ⚠ E NON si usa il testo della pretesa: `Pretese.che()` stampa la STESSA
    #   frase in verde e in rosso, cambiando solo il prefisso OK/NO colorato —
    #   che e' la trappola gia' pagata su B7 con «CONGEDO».
    # ⭐ Seconda marca misurata (0/1/0), piu' forte contro la trappola n.1
    #    perche' un Chrome morto non la puo' stampare — pretende che il caso
    #    arrivi in fondo e legga l'impaginazione:
    #    «impaginazione ACCESA  clientWidth×clientHeight [1361, 773]».
    "sano/V3s: rosso",
    "leggero",
    "fasi/03-movimento.md step 4 · SPECIFICHE.md §6.1-bis · "
    "RCP.md §6.2 e §5.2 · LEZIONI.md §1.1, §1.2",
    nota="⚠ LA COPIA QUI DEV'ESSERE UN ALBERO, NON UN FILE, e `prepara_copia()` "
         "oggi **non lo sa fare**: `03-b16-dipinti.py` legge la pagina come "
         "`RADICE/src/pagina.html` con `RADICE = QUI.parent` e **non ha nessuna "
         "opzione per cambiare sorgente** (la costante `COPIE` dentro quel file "
         "e' definita e mai usata — codice morto).  ⇒ Prima del giro va "
         "costruito a mano `01-b12-copie/b16-albero/` con dentro "
         "`banchi/03-b16-dipinti.py` e `src/pagina.html`, e si lancia la copia "
         "del banco: `RADICE` segue `__file__` e ci va dietro da sola, senza "
         "toccare una riga.\n"
         "⭐ E l'appiglio e' lungo apposta: `overflow-y: scroll` da solo "
         "compare **due** volte in `pagina.html` — la seconda dentro il "
         "commento che racconta la cura — e un appiglio corto avrebbe innestato "
         "il guasto **nel commento**, lasciando il difetto fuori e il banco "
         "verde.\n"
         "⭐ `atteso_sano = 0` e questa volta e' MISURATO, non dedotto: giro "
         "`b16-20260813-144817`, 19 casi, tutti «verde», 0 guai.\n"
         "⚠ Da misurare: che il guasto faccia rosso **V3s e solo V3s**.  La "
         "lettura dice che V3 e V3d confrontano tela e larghezza fra loro e "
         "non con un numero fisso, ma e' una lettura, non una misura.\n"
         "⚠ La scena: niente prodotto (su CHUWI non compila) e niente "
         "WebTransport — la pagina si serve da un `http.server` di Python su "
         "127.0.0.1, i fotogrammi entrano da uno stream finto, e il browser e' "
         "Chrome vero su schermo finto.  E' dichiarato dal banco stesso.\n"
         "⭐⭐ **CERTIFICATO IL 13 AGOSTO 2026 SERA**: 0 → 1 → 0 sull'albero "
         "`01-b12-copie/b16-albero/`, **che adesso esiste** (costruito a mano, "
         "come questa nota gia' chiedeva) — quindi `--verifica`, `--applica` e "
         "`--togli` funzionano su questa voce.  Pagina tornata "
         "`ec169e5d7232ca6a…`, byte per byte quella di casa.\n"
         "⭐ E LA `⚠ Da misurare` DI QUESTA STESSA NOTA E' STATA MISURATA: col "
         "guasto e' rosso **V3s e SOLO V3s**, gli altri 18 casi restano verdi. "
         "La lettura («V3 e V3d confrontano tela e larghezza fra loro e non "
         "con un numero fisso») regge anche alla misura, e non e' piu' una "
         "lettura.  Il difetto vale esattamente **15 px** di `clientWidth` "
         "(1376 → 1361): «una quindicina», verificata.\n"
         "⛔⛔ **E UNA TRAPPOLA N.1 MISURATA SUL CAMPO, che va saputa prima di "
         "leggere un rosso di questo banco**: un primo giro risanato e' uscito "
         "**1 con ZERO righe rosse**, perche' un `Xvfb :90` rimasto in piedi "
         "da un giro ucciso occupava lo schermo.  Il banco lo dice a chiare "
         "lettere — *«lo schermo :90 e' gia' occupato: un altro banco ci sta "
         "sopra»* — ma **alza un `RuntimeError`, e Python esce 1 come per un "
         "caso rosso**.  ⇒ `uscita = 1` di questo banco significa «un caso e' "
         "rosso» **oppure** «lo schermo era occupato», e le due si distinguono "
         "SOLO dalla marca.  ⭐ E' la ragione per cui il campo `marca` non e' "
         "una formalita': quel giro fasullo aveva `marca_vista = false`, e "
         "`--giudica` l'avrebbe rifiutato.  Il giro e' stato buttato e rifatto "
         "a schermo pulito.",
)

# ── 03-b17 — la finestra di sanita' dell'istante spalancata ────────────────
guasto(
    "03-b17", "03-b17",
    "⛔ al banco del ritardo si spalanca la finestra di sanita' dell'istante: "
    "il setaccio che smaschera un rilevatore che INVENTA il tempo",
    os.path.join(COPIE, "03-b17-ritardo.py"),
    "    dentro = [s for s in scarti if -1000000 <= s <= 5000]",
    "    dentro = list(scarti)  # " + MARCA + " 03-b17 — la finestra di\n"
    "    # sanita' dell'istante spalancata: un istante inventato non viene\n"
    "    # piu' preso da nessuno.",
    "⛔ La finestra di P3 e' **il setaccio che smaschera un rilevatore che si "
    "inventa l'istante** invece di leggerlo: e' il controllo caduto in v1, ed "
    "e' cosi' che si riperde in silenzio.  ⭐ Con la finestra tolta il guasto "
    "sintetico «l'istante e' inventato» non viene piu' preso da nessuno — "
    "restano i due setacci che un rilevatore bugiardo **passa** — e il banco "
    "continua a consegnare un numero di ritardo dall'aria perfettamente "
    "normale.  ⇒ Il numero della fase 3 poggia su questo setaccio",
    # ⛔ NON MISURATA.  ⭐ Dove guardare: `certifica()` costruisce la riga e
    #    `dice()` la stampa con `ko()`:
    #      «guasto «P3 l'istante e' inventato» → rossi nessuno (attesi ['P3'])»
    #    Candidata da verificare: «rossi nessuno (attesi ['P3'])».  ⭐ Nel giro
    #    sano la stessa riga dice «→ rossi ['P3'] (attesi ['P3'])», e siccome
    #    nel sano tutti e dieci i guasti sintetici sono presi, la parola
    #    «rossi nessuno» non compare mai.
    "",
    "leggero",
    "fasi/03-movimento.md step 5 · web.md §6.2 e §6.3 · SPECIFICHE.md §3.2 · "
    "RCP.md §6.2 · LEZIONI.md §1.2, §1.13",
    nota="⛔⛔ **IL GIRO SANO DI `--certifica` NON E' VERDE SU CHUWI, E "
         "L'HO MISURATO: 3 GIRI SU 3, USCITA 1, «BOCCIATO — 30 controlli su "
         "31».**  `[M]` 13 agosto 2026 sera, sulla copia in `01-b12-copie/`, "
         "**senza nessun guasto innestato**.  ⛔ E non e' instabilita': cade "
         "sempre lo **stesso** controllo, ed e' del PONTE e non del banco del "
         "ritardo — *«fuori ordine: 0 inversioni su 40 pacchetti tornati "
         "(attese > 0)»*.  Il ponte deve **produrre** disordine per poter "
         "dimostrare di saperlo vedere, e su questa macchina non ne produce.\n"
         "⚠ I sette PROMOSSO 31 su 31 del 13 agosto erano su **NIC-OS**: "
         "`atteso_sano = 0` vale la' e **non qui**, e le due cose non si "
         "arrotondano.  ⇒ Finche' il giro sano non e' verde, 03-b17 **NON SI "
         "CERTIFICA** — e' la regola gia' scritta per B8, per B13 e per P5, e "
         "la cosa giusta e' lasciarlo NON CERTIFICATO invece di allargare "
         "l'atteso finche' torna.\n"
         "⭐ Da cui il primo passo per chi lo riprendera', ed e' piu' corto di "
         "quanto sembri: capire se il ponte non inverte perche' su CHUWI il "
         "giro e' tutto in casa, o perche' il controllo pretende un evento che "
         "nessuno gli fa succedere.  Le due hanno cure diverse.\n"
         "⛔ E LA VOCE VALE PER `--certifica`, NON PER `--misura`: sul giro dal "
         "vivo l'atteso sano **non e' stabilmente 0** — su 13 misure "
         "registrate solo 3 hanno tutti e sette i controlli veri, e il "
         "rapporto di fase lo dichiara («P5 NON ESEGUITO, e adesso lo dice»). "
         "Mettere questa voce sul giro dal vivo vorrebbe dire dichiarare "
         "`atteso_sano = 1`, oppure rifare il sano finche' non torna — cioe' "
         "un verde fragile.  ⚠ `--certifica` gira su CHUWI **senza rete e "
         "senza server**, ed e' il motivo per cui questo guasto si puo' "
         "chiudere in minuti.\n"
         "⛔⭐ **E IL GUASTO PIU' FEDELE ALLO SPIRITO DI B12 E' UN ALTRO, ED "
         "E' BLOCCATO DA UN DIFETTO DEL BANCO** — si scrive qui perche' chi "
         "verra' non ricominci da capo.  Sarebbe: nella COPIA del prodotto "
         "(`03-b17-src/src/figlio.c`, quella che `03-b17-lancia.sh porta` "
         "srotola sul server) far finire nei 28 byte il `pts` del fotogramma "
         "**precedente** — appiglio `\\tpts_us = (uint64_t)fo->pts / 1000u;`, "
         "verificato **unico**.  E' il difetto perfetto: la guardia del "
         "prodotto ripiega solo oltre **un secondo**, quindi uno scarto di un "
         "fotogramma (~41 ms) **passa**, il video si vede identico, e il "
         "numero della fase esce piu' corto del vero.  A vederlo sarebbe il "
         "solo P3, e P1 non si muoverebbe (il ritardo si calcola sulla marca "
         "dei pixel, non sul `pts`).\n"
         "⛔ **Perche' non e' quello scritto qui sopra**: la riga che il banco "
         "stampa per un P3 rosso e' un `json.dumps(...)[:220]`, e i 220 "
         "caratteri **si esauriscono prima** del campo che cambia — sano e "
         "guasto stampano un prefisso della stessa forma.  ⇒ Una marca non "
         "esiste, e senza marca `giudica()` non certifica.  ⭐ La cura e' due "
         "righe: dare a P3 un campo `perche` come ce l'hanno gia' P1, P2 e P5. "
         "Fatto quello, questo guasto va costruito.",
)

# ── 03-b19 — l'interruttore del worker spento dalla parte che funziona ─────
guasto(
    "03-b19", "03-b19",
    "⛔ nella pagina si spegne il ramo del FRAMMENTO che accende il worker: "
    "resta solo la strada a cui il prodotto risponde 404",
    os.path.join(QUI, "03-b17-src", "src", "pagina.html"),
    '  new URLSearchParams(location.hash.replace(/^#/, "")).get("video") === "worker";',
    "  false; /* " + MARCA + " 03-b19 — l'interruttore dal FRAMMENTO spento.\n"
    "            Resta solo `?video=worker`, e il servente risponde 404 a\n"
    "            quello: il worker non nasce piu' per nessuna strada. */",
    "⛔ E' **il difetto senza nessun sintomo per definizione**: il worker e' "
    "*attuato, misurato e tenuto spento* in produzione, quindi togliere quel "
    "ramo non cambia niente per l'utente e non muove nessun altro banco.  ⭐ "
    "Ma il frammento e' **l'unica strada che funziona** — il servente "
    "confronta il percorso con `/` e risponde **404** a `GET /?video=worker`, "
    "misurato il 13 agosto — ed e' per questo che il banco apre "
    "`#video=worker` e non `?video=worker`.  ⇒ Spento quel ramo, la pagina "
    "gira **tutta sul thread principale mentre l'URL dice worker**: il banco "
    "dei dipinti confronterebbe il thread principale **con se stesso** "
    "stampando «indistinguibili», e quello del ritardo misurerebbe *«il "
    "thread principale con l'etichetta del worker»* — la frase e' del banco",
    # ⛔ NON MISURATA.  ⭐ Dove guardare: `misura()` la stampa con `ko()` prima
    #    ancora di misurare, quando `aggancia_worker()` non trova nessun
    #    bersaglio: «⛔ e' stato chiesto «?video=worker» ma nessun bersaglio
    #    «worker» si e' fatto agganciare: NON misuro».  Candidata da
    #    verificare: «nessun bersaglio «worker» si e' fatto agganciare».
    #    ⭐ Nel giro sano al suo posto c'e' «⭐ worker agganciato, e il prologo
    #    e' dentro anche li'».
    "",
    "leggero",
    "fasi/03-movimento.md §7 e §8 · DECISIONI.md §2.8 · web.md §6.1 · "
    "LEZIONI.md §6.2",
    atteso_sano=1,
    nota="⛔ `atteso_sano = 1`, E NON E' UN ATTESO ALLARGATO: e' MISURATO.  "
         "Tutt'e tre i giri `b19-*` registrati sulla 7608 escono 1 perche' "
         "**P5 e' falso** in tutti e tre (e in due anche P3 o P1), e P5 non "
         "eseguito e' una cosa **dichiarata** dal rapporto di fase, non un "
         "difetto scoperto oggi.  ⚠ Un `atteso_sano = 0` avrebbe fatto "
         "scrivere «il banco non partiva dallo stato che il catalogo "
         "dichiara» a un banco che sta facendo il suo mestiere.\n"
         "⭐ E il guasto da' un numero **diverso**: il banco si ferma prima di "
         "misurare, con uscita **4**.  I due non si confondono.\n"
         "⚠ IL GUASTO MORDE SOLO COL GIRO `--video-worker`: senza "
         "quell'interruttore il ramo non viene percorso e il banco resta "
         "verde — e sembrerebbe che non veda.  Va dichiarato a chi lancia.\n"
         "⛔ E B19 SONO DUE FILE, non uno.  A catalogo c'e' "
         "`03-b19-ritardo-worker.py`, l'unico che sa dire di no; il gemello "
         "`03-b19-dipinti-worker.py` e' un banco **comparativo** a se'.  "
         "⭐ **E NON ESCE PIU' SEMPRE 0: curato il 13 agosto 2026 sera**, con "
         "la stessa forma di B14 — `ko()` conta, e `principale()` chiude con "
         "`return 1 if ROSSI else 0`.\n"
         "⭐⭐ E LA CURA E' STATA MISURATA SULLO STESSO IDENTICO GIRO, prima e "
         "dopo: Xvfb :87, Chrome vero, porta 7614, `src/pagina.html` su un "
         "albero a parte, 2 giri da 6 s per strada.  **Prima della cura: "
         "uscita 0** stampando «⛔ il worker DIPINGE MENO: -97,3 dipinti/s "
         "(-74,2 %)».  **Dopo la cura: uscita 1**, stessa scena, stessa riga "
         "rossa.  ⇒ Il difetto c'era davvero e la cura lo chiude.\n"
         "⛔ E `atteso_sano = 1` ANCHE PER IL GEMELLO, ed e' MISURATO tre "
         "volte su tre (129,1 contro 28,4 · 131,1 contro 33,8 · 130,8 contro "
         "37,7 dipinti/s): su CHUWI, a schermo finto e in software, **il "
         "worker dipinge circa un quarto** del thread principale.  ⚠ Quel "
         "rosso e' del PRODOTTO e non del banco — `LEZIONI.md` §6.2 — ed e' "
         "coerente con il fatto che il worker sia tenuto **spento** in "
         "produzione.  ⛔ Un `atteso_sano = 0` qui sarebbe un atteso "
         "allargato al contrario: farebbe scrivere «il banco non partiva "
         "dallo stato dichiarato» a un banco che sta misurando bene.\n"
         "⭐ E i TRE GIRI del gemello sono stati fatti, il 13 agosto sera, "
         "sull'albero di prova `/home/nicfio/b19-albero` — mai su `src/`: "
         "**sano 1 → guasto 3 → risanato 1**, col ramo `?video=worker` della "
         "pagina spento (appiglio `  new URLSearchParams(location.search)."
         "get(\"video\") === \"worker\" ||`, verificato UNICO) e la pagina "
         "tornata `ec169e5d7232ca6a…`, byte per byte quella di casa.  La "
         "marca «ma il worker non e' pronto: NON misuro» ha dato **0 nel "
         "sano, 1 nel guasto, 0 nel risanato**.  ⚠ Non e' a catalogo come "
         "voce propria: e' UN banco per riga, e la riga di `03-b19` e' del "
         "ritardo.  Chi vorra' certificare anche il gemello ha qui tutto "
         "quello che serve.\n"
         "⚠ E il ritardo-worker **non ha un registro proprio**: deposita in "
         "`03-b17-esiti.jsonl` marcandosi `\"banco\": \"B17\"`.  Due banchi "
         "sotto la stessa etichetta e' la forma E2, e va saputo prima di "
         "leggere quel file.\n"
         "⚠ Il `dove` sta sulla MACCHINA DI PROVA (la copia che "
         "`03-b17-lancia.sh porta` srotola): da CHUWI `--provabile 03-b19` "
         "stampa MANCA, ed e' giusto — e' la stessa scena di P1.\n"
         "⛔⛔⭐ **E IL DIFETTO DEL `return 0` NON E' CHIUSO DEL TUTTO: NE "
         "RESTA UN TERZO, E STA PROPRIO IN `03-b19-ritardo-worker.py`, cioe' "
         "nel file che QUESTA voce mette a catalogo.**  Trovato il 13 agosto "
         "2026 sera **cercando il caso che smentisse «adesso i banchi sanno "
         "bocciare»**, e il caso c'era.  `principale()` ha tre strade: "
         "`--certifica` chiude con `return 0 if r[\"esito\"] == \"PROMOSSO\" "
         "else 1` (giusta), `--misura` con `return 0 if all(...) else 1` "
         "(giusta), ⛔ ma `--verdetto <file>` chiama `stampa_verdetto()` — che "
         "stampa i rossi con `ko()` — e poi **`return 0` incondizionato**.  ⇒ "
         "Rileggere un verbale gia' salvato stampa il verdetto giusto e esce "
         "**sempre verde**: e' la stessa forma curata stasera su `03-b14` e "
         "sul gemello dei dipinti.\n"
         "⚠ **NON E' STATO CURATO, E IL MOTIVO E' UNA REGOLA DI CASA**: la "
         "cura sarebbe una riga, ma per provarla servono la macchina di prova "
         "e la scena di P1, che da CHUWI non c'e'.  ⛔ E un banco «curato» che "
         "nessuno ha visto arrossire non e' curato — meglio il difetto "
         "SCRITTO che una cura non eseguita spacciata per fatta.  ⇒ E' il "
         "primo lavoro per chi riprende `03-b19`, e costa una riga piu' un "
         "giro.",
)

# ── 03-b15 — il setaccio del TIPO del primo fotogramma, tolto ──────────────
guasto(
    "03-b15", "03-b15",
    "⛔ a P2 si toglie il setaccio del TIPO del primo fotogramma: un DELTA "
    "subito dopo `SESSIONE` passa per buono, e il banco lo chiama CHIAVE",
    os.path.join(COPIE, "03-b15-movimento.py"),
    "    if primo.tipo != CHIAVE:\n",
    "    # ⭐ " + MARCA + " 03-b15 — tolto il setaccio del TIPO del primo\n"
    "    #   fotogramma: P2 non guarda piu' se il primo dopo SESSIONE e' una\n"
    "    #   CHIAVE 0x0301, e un DELTA in apertura passa per buono.\n"
    "    #   ⛔ Non si vede perche' non ha nessun ALTRO sintomo: il banco gira\n"
    "    #   intero, conta gli stessi fotogrammi e stampa lo stesso verde — i\n"
    "    #   `numero` non hanno buchi e nessun decodificatore protesta.\n"
    "    if False and primo.tipo != CHIAVE:\n",
    "⛔ §5.2 vuole che il PRIMO fotogramma dopo `SESSIONE` sia una CHIAVE "
    "`0x0301`, e P2 e' l'unico che lo guarda.  ⭐ E' il difetto di questo "
    "catalogo nella sua forma piu' pura, perche' **il banco non tace: afferma "
    "il falso** — su un delta `0x0302` in apertura stampa «il primo "
    "fotogramma (`numero` 1) e' una CHIAVE 0x0301».  ⇒ Passerebbe in silenzio "
    "un prodotto che dopo `SESSIONE` manda un delta: il client aprirebbe su "
    "un riferimento che non ha, e il sintomo sarebbe «il desktop compare a "
    "pezzi» — **senza buchi nella successione dei `numero`** (li' guarda P1) "
    "**e senza un errore del decodificatore** che lo denunci.  ⚠ E' proprio "
    "quel che l'intestazione del banco dichiara di sua mano.",
    # ⭐ MISURATA, non dedotta — 13 agosto 2026 sera, su copia in scratchpad,
    #    tre giri: 0 nel sano, 1 nel guasto, 0 nel risanato.
    # ⛔ E NON e' la riga generica «⛔ sul verbale guasto dice VERDE invece di
    #    ROSSO: non sa vedere», che pure darebbe 0/1: quella uscirebbe IDENTICA
    #    per qualunque altro ago non visto, cioe' non distingue questo guasto
    #    da un altro — la trappola R12-A.3 nella sua forma piu' educata.
    # ⭐ Questa invece incastra il `(atteso ROSSO)`, che esiste solo dentro la
    #    certificazione, con la BUGIA che solo questo guasto fa dire.
    "(atteso ROSSO) il primo fotogramma (`numero` 1) e' una CHIAVE 0x0301",
    "leggero",
    "fasi/03-movimento.md step 3 · RCP.md §5.2 e §6.2 · "
    "LEZIONI.md §1.1, §1.2",
    nota="⭐⭐ **CERTIFICATO IL 13 AGOSTO 2026 SERA, E LA SCENA E' LA PIU' "
         "ECONOMICA DELLA FASE 3**: `python3 03-b15-movimento.py --certifica` "
         "gira **su CHUWI**, senza rete, senza contenitore, senza prodotto e "
         "senza aioquic (che si importa tardi, dentro le funzioni del giro dal "
         "vivo), e ci mette circa un secondo.  Tre giri: sano **0** → guasto "
         "**2** → risanato **0**, con il file tornato "
         "`229f041a16a8a589d24eb0d67463da6c4a2e65de9a2bba8ba0b2ff7a6057eead`, "
         "byte per byte l'originale.\n"
         "⛔ E IL 2 ARRIVA DALLA STRADA GIUSTA, verificato invece che sperato: "
         "`certifica()` conta **UNA falla sola**, sull'ago «delta in apertura» "
         "di P2 — non un crollo, non un import fallito, non tre controlli che "
         "cadono insieme.  `principale()` stampa «Non punto un banco non "
         "certificato sull'incognita» e ritorna 2.\n"
         "⛔⭐ **E IL GUASTO E' STATO REFUTATO PRIMA DI ESSERE SCRITTO**: dato "
         "in pasto a tutt'e sei i controlli un verbale col difetto vero (un "
         "delta in apertura), il banco SANO dice `P2 ROSSO` e il banco GUASTO "
         "dice **VERDE su tutti e sei**.  ⇒ Nessun altro controllo lo "
         "raccoglie al posto di P2: il setaccio e' davvero l'unico.\n"
         "⚠ L'appiglio e' lungo di un rientro apposta: `primo.tipo` da solo "
         "compare **3** volte nel file, `    if primo.tipo != CHIAVE:\\n` una "
         "sola (contata, non guardata).\n"
         "⛔ QUEL CHE QUESTA VOCE **NON** CERTIFICA, e va letto: il giro DAL "
         "VIVO sulla 7603 — quello che vuole aioquic, il contenitore e il "
         "prodotto — resta `[?]`.  Qui si certifica **la certificazione**, "
         "cioe' che i sei controlli sappiano dire di no ai propri verbali "
         "guasti.  E' una meta' sola, ed e' quella che si puo' misurare "
         "stasera.\n"
         "⚠ La marca poggia sul formato di stampa di `certifica()` "
         "(`{esito:<11} (atteso {atteso})`) e sulla prima frase del verde di "
         "P2: se qualcuno riscrive quel `print`, la marca muore — ma muore "
         "RUMOROSAMENTE, dando 0 anche nel giro guasto, e `--giudica` se ne "
         "accorge invece di certificare lo stesso.",
)

# ── 03-b18 — il setaccio della CURA di §5.2, disarmato ─────────────────────
guasto(
    "03-b18", "03-b18",
    "⛔ a C6 si disarma il ramo che dice ROSSO: dopo un delta saltato per "
    "mancanza di posto, il banco non guarda piu' se il server ha preparato "
    "la CHIAVE che §5.2 gli impone",
    os.path.join(COPIE, "03-b18-credito.py"),
    "    if not righe_debito_chiave(v):\n",
    "    # ⭐ " + MARCA + " 03-b18 — TOLTO il setaccio di C6 (§5.2): il ramo\n"
    "    #   che dichiara ROSSO quando nessuna delle tre forme di CURA_ARMATA\n"
    "    #   sta nel registro.\n"
    "    #   ⛔ NON SI VEDE perche' `c6_cura` cade sul proprio ritorno VERDE e\n"
    "    #   dice «la cura e' ARMATA» con 0 righe: il banco gira intero, C1-C5\n"
    "    #   restano verdi, e ogni suo numero resta plausibile.\n"
    "    if False and not righe_debito_chiave(v):\n",
    "⛔ E' **l'unico setaccio dell'intero banco che vede il difetto B-18**, e "
    "non e' una lettura: lo dichiara il progetto stesso.  "
    "`03-b18-innesta.py:81` — l'ago che si innesta nel PRODOTTO per fargli "
    "violare §5.2 — porta scritto `\"chi_lo_vede\": \"03-b18 C6-cura — e "
    "NESSUN ALTRO: la sessione regge, il registro dice tutto, nessuna chiave "
    "viene buttata\"`.  ⭐ Disarmato quel ramo, passerebbe in silenzio un "
    "prodotto che salta un delta per mancanza di posto e **non accende** "
    "`serve_chiave`: la sessione regge, il registro scrive tutto, nessuna "
    "CHIAVE viene buttata — e al decodificatore manca per sempre un delta che "
    "col GOP infinito non tornera' mai, mentre §6.2 impedisce al client di "
    "accorgersene perche' nei numeri non resta buco.  ⇒ Sei controlli verdi, "
    "e lo schermo rotto per sempre.",
    # ⭐ MISURATA — 13 agosto 2026 sera: 0 nel sano, 3 nel guasto, 0 nel
    #    risanato (tre, quanti sono gli aghi di C6).
    # ⛔ E ANCHE QUI NON si usa la riga generica «⛔ sul verbale guasto dice
    #    VERDE invece di ROSSO»: darebbe pure lei 0/3, ma uscirebbe uguale per
    #    qualunque altro ago non visto.
    # ⚠ E il pezzo «2 delta saltati per mancanza di posto…» da solo NON basta:
    #   compare anche nel giro sano, nelle righe `sano` e `risanato` di C6.  Il
    #   prefisso `(atteso ROSSO) ` e' obbligatorio, ed e' quel che rende la
    #   marca una marca invece di una frase del banco.
    "(atteso ROSSO) 2 delta saltati per mancanza di posto, e il server ha "
    "preparato la CHIAVE",
    "leggero",
    "fasi/03-movimento.md step 6 · RCP.md §2.3 e §5.2 · "
    "LEZIONI.md §1.1, §1.2",
    nota="⭐⭐ **CERTIFICATO IL 13 AGOSTO 2026 SERA**, stessa scena economica "
         "di `03-b15`: `python3 03-b18-credito.py --certifica` gira **su "
         "CHUWI** senza rete, senza contenitore e senza prodotto, in circa un "
         "secondo.  Tre giri: sano **0** («8 aghi su 8, per 6 controlli») → "
         "guasto **2** («5 aghi su 8») → risanato **0**, con il file tornato "
         "`175f13244000ae6fcc9e50994bffa977f2d87b0dd0fc8a127abd515cf1ebd4af`, "
         "byte per byte l'originale.\n"
         "⛔ E LE TRE FALLE SONO ESATTAMENTE E SOLO I TRE AGHI DI C6 — «B-18 "
         "in piedi», nelle forme «FOTOGRAMMA NON SPEDITO», «girata al palco» e "
         "«il debito resta acceso» — non un crollo che sporca tutto.  Nel giro "
         "sano le righe `NO` sono **zero**.\n"
         "⛔⭐ **DUE ALTERNATIVE SONO STATE PROVATE E SCARTATE, E VALGONO PIU' "
         "DI QUELLA SCELTA** perche' dicono dove il banco NON guarda:\n"
         "   · disarmare `if v.caduta:` di C3 da' uscita 2, ma con **una sola** "
         "falla e il verbale guasto che dice **ancora ROSSO**: il ramo "
         "`if not v.viva:` fa da rete.  Sarebbe un rosso per la ragione "
         "sbagliata — mancata *nominazione*, non cecita';\n"
         "   · ⛔ disarmare `if buttate:` di C3 (§5.2, «nessuna CHIAVE "
         "buttata») da' **uscita 0, 8 aghi su 8**: nessun ago copre quel ramo. "
         "⇒ E' un **punto cieco vero della certificazione di 03-b18**, "
         "misurato stasera e scritto qui perche' non si riperda: quel "
         "controllo esiste e nessuno ha mai provato che sappia dire di no.\n"
         "⚠ L'appiglio e' preso col rientro: `righe_debito_chiave(v)` da solo "
         "compare **3** volte, `    if not righe_debito_chiave(v):\\n` una "
         "sola (contata).\n"
         "⛔ QUEL CHE QUESTA VOCE **NON** CERTIFICA: il giro DAL VIVO sulla "
         "7607 resta `[?]`.  E c'e' un dettaglio che va detto perche' non si "
         "scambi per un rosso sul filo — `certifica()` gira **per prima**, "
         "quindi col guasto dentro il banco esce 2 **senza mai arrivare al "
         "filo**.  E' il comportamento voluto (§1.2), ma vuol dire che il 2 e' "
         "il verdetto della certificazione, non di una misura.\n"
         "⚠ I conteggi della marca («2 delta») nascono dai verbali fabbricati "
         "in `_verbale_sano()`: se qualcuno cambia `REG_CREDITO_DELTA` o il "
         "numero di righe, la marca va RIMISURATA, non ritoccata a mente.",
)


# ===========================================================================
# ⛔ La cartella dei certificati e' un percorso di esecuzione, e chi lancia la
#    puo' cambiare: si tiene in UN posto solo, e le voci del catalogo la
#    nominano con `{CERT}` invece di scriverla due volte.  Due verita' sullo
#    stesso percorso e' la forma con cui i guasti si perdono per strada.
CERT = CERT_PREDEFINITA


def risolvi(p):
    """`{CERT}/pagina.pem` → il percorso vero, con la cartella di oggi."""
    return p.replace("{CERT}", CERT) if p else p


# ⛔⭐ DOVE UN FILE STA SU QUESTA MACCHINA, E NON E' SEMPRE UN POSTO SOLO —
#     cura della notte fra l'11 e il 12 agosto 2026.
#
# `remotix/pagina.c` e' il sorgente DEL PRODOTTO.  Sulla macchina di prova sta
# accanto ai banchi (`/srv/src/remotix/`); su CHUWI — da cui si certificano P1 e
# P5, perche' i browser stanno di qua — lo stesso file sta in `../src/`.  ⛔ Il
# catalogo cercava solo il primo posto, quindi da CHUWI l'impronta valeva `None`
# e `--registro` declassava P5 a «certificazione NON RIVERIFICABILE» — dopo un
# giro 0 → 1 → 0 fatto per intero, con la marca vista solo nel rosso.
#
# ⚠ «Non ho guardato» non e' «non e' cambiato», e quella severita' resta giusta:
#   la cura non e' ammorbidire il giudizio, e' GUARDARE ANCHE NELL'ALTRO POSTO.
#
# ⭐ E che i due posti siano lo stesso file non e' dedotto: `[M]` 11 agosto 2026,
#    `sha256(pagina.c)` = `930b611a906e8051…` su tutt'e tre le copie — quella di
#    CHUWI (`../src/`), quella del server (`remotix/`) e quella su cui il giro
#    ha girato (`01-b12-copie/p5-remotix/`).
#
# ⛔ E la chiave nel registro resta il NOME DI CATALOGO, non il posto in cui si
#    e' trovato: due giri su due macchine diverse devono poter confrontare la
#    stessa riga.  Il posto si dichiara a schermo, non si nasconde e non
#    cambia l'etichetta.
ALTRI_POSTI = {
    "remotix/pagina.c": ["../src/pagina.c"],
    # ⚠ Come sopra, per il guasto P5R: da CHUWI la pagina del prodotto sta in
    #   `../src/`, sulla macchina di prova in `remotix/`.  Se non c'e' ne' di
    #   qua ne' di la', `dove_sta` torna None e la riga dice «non so» invece
    #   di arrotondare — che e' il comportamento giusto e va lasciato stare.
    "remotix/pagina.html": ["../src/pagina.html"],
    # ⚠ E i due file del BINARIO, per la stessa ragione e nello stesso verso:
    #   sul server stanno in `remotix/` accanto ai banchi, su CHUWI in
    #   `../src/`.
    #
    # ⛔ CHE I DUE POSTI SIANO LO STESSO FILE NON SI DEDUCE — e la sera del
    #    12 agosto 2026 NON LO ERANO.  `[M]`, prima di allineare:
    #      main.c    CHUWI 4274017443a3bb72…  ·  NIC-OS dc9acfa5caca4a8d…
    #      Makefile  CHUWI c25a1445dfa71c4a…  ·  NIC-OS 479b2af9f5b6c7ea…
    #    ⇒ Il prodotto del server era costruito (19:46) su sorgenti che il
    #    deposito aveva gia' cambiato alle 22:18 e alle 22:36, ed e' ESATTAMENTE
    #    il difetto che queste due impronte esistono per far scadere.
    #
    # ⭐ `[M]` dopo `attrezzi-allinea-prodotto.sh allinea`, stessa sera:
    #      main.c    4274017443a3bb72…  su tutt'e due
    #      Makefile  c25a1445dfa71c4a…  su tutt'e due
    #    ⇒ Da qui in poi la stessa riga di registro si rilegge uguale dalle due
    #    macchine.  ⚠ E quando i due alberi divergono di nuovo, il nome di
    #    catalogo NON nasconde la divergenza: la fa vedere come impronta
    #    diversa, cioe' come certificazione scaduta — che e' il suo mestiere.
    "remotix/main.c": ["../src/main.c"],
    "remotix/Makefile": ["../src/Makefile"],
    # ⚠ E i due tratti di catena che `03-b17` misura, per la stessa ragione e
    #   nello stesso verso — 13 agosto 2026, alla messa a catalogo dei banchi
    #   della fase 3.  ⛔ Senza queste due righe `--provabile 03-b17` stampava
    #   «MANCA remotix/figlio.c» **da CHUWI, dove il file c'e'**, e la sua
    #   certificazione sarebbe nata «non riverificabile»: cioe' una riga che
    #   dice «certificato» e non sa dire su che byte.  ⭐ E' esattamente la
    #   cura gia' fatta sopra per `pagina.c`, applicata dove serviva adesso.
    "remotix/figlio.c": ["../src/figlio.c"],
    "remotix/webtransport.c": ["../src/webtransport.c"],
    # ⛔ 13 agosto 2026 sera, con `codificatore.c` — il punto cieco.
    "remotix/codificatore.c": ["../src/codificatore.c"],
    "remotix/codificatore.h": ["../src/codificatore.h"],
}


def dove_sta(nome):
    """Il percorso da cui `nome` si legge QUI, o None se non c'e' da nessuna
    parte.  ⚠ Prova prima il posto di catalogo, poi quelli dichiarati sopra."""
    primo = os.path.join(QUI, nome)
    if os.path.exists(primo):
        return primo
    for altro in ALTRI_POSTI.get(nome, []):
        p = os.path.join(QUI, altro)
        if os.path.exists(p):
            return p
    return None


def impronta_file(p):
    if p is None:
        return None
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def provabile(sigla):
    """⛔ Si puo' certificare `sigla` SU QUESTA MACCHINA?

    Stampa una riga `MANCA <nome>` per ogni file su cui la certificazione
    poggia e che qui non c'e'; esce 0 se non ne manca nessuno, 1 altrimenti.

    ⛔ RILIEVO R12-A.31, 11 agosto 2026.  «Non posso provarlo qui» e «l'ho
    provato e non passa» erano la stessa riga di registro.  `[M]`: B9 lanciato
    sul server e' uscito 4 — `RCP.md` **li' non esiste**, perche' su quella
    macchina arrivano i banchi e non i documenti — e il verdetto ha scritto
    «B9 NON certificato».  Un banco sano marchiato rosso manda a cercare un
    difetto che non c'e', e il registro se lo porta dietro con una data.
    ⭐ E' la forma opposta del falso verde.  Costa uguale, e si vede meno.

    ⚠ Guarda `file_che_contano`, non `dove`: `dove` e' il posto in cui il
      guasto si innesta, mentre la certificazione poggia sui file che il banco
      **legge** — ed e' uno di quelli a mancare, non l'appiglio.
    """
    g = GUASTI.get(sigla)
    if not g:
        print(f"MANCA il-guasto-{sigla}-non-e-in-catalogo")
        return 1
    mancanti = 0
    for nome in g.get("file_che_contano", []):
        if dove_sta(nome) is None:
            print(f"MANCA {nome}")
            mancanti += 1
    return 1 if mancanti else 0


def impronte_di(sigla):
    """{nome del file: sha256 | None}.  ⛔ `None` = non si e' potuto guardare.

    ⚠ E due `None` non sono uguali: il confronto fra due giri si fa solo sui
      file che si sono potuti leggere da tutt'e due le parti, e sugli altri si
      dice «non si sa», che non e' «non e' cambiato» (`LEZIONI.md` §1.9).
    """
    fuori = {}
    for nome in GUASTI.get(sigla, {}).get("file_che_contano", []):
        fuori[nome] = impronta_file(dove_sta(nome))
    return fuori


# ===========================================================================
# ⛔⛔ IL CONFRONTO GUARDAVA SOLO QUEL CHE LA RIGA PORTAVA — la seconda meta'
#     del buco del 12 agosto 2026, ed e' la peggiore delle due.
#
# La prima meta' era il catalogo: nessuno dei cinque banchi che misurano il
# PRODOTTO portava `main.c` e il `Makefile` fra le impronte (il riquadro in
# testa a `FILE_CHE_CONTANO`).  ⭐ Aggiunti quei due file, il conto e' rimasto
# **15 su 15** — e li' si e' visto il difetto vero, che stava **qui dentro**:
#
#   ⛔ *Il ciclo girava su `vecchie.items()`, cioe' sulle impronte che la RIGA
#      porta.  Un file aggiunto al catalogo dopo che la riga e' stata scritta
#      non compare in `vecchie`, quindi non veniva guardato da nessuno: ⇒
#      **aggiungere un file che conta non invalidava niente**, e una riga
#      certificata ieri restava verde su un elenco che oggi e' piu' lungo.*
#
# ⚠ E' la forma E8 un piano piu' su di dove l'avevamo gia' pagata: non «il
#   silenzio scambiato per zero» sul contenuto di un file, ma **il denominatore
#   scambiato per quello di oggi**.  La riga rispondeva onestamente alla
#   domanda che le veniva posta — «i file che porti sono cambiati?» — e la
#   domanda era quella sbagliata.  ⛔ La domanda giusta e' *«sai rispondere di
#   tutti i file che contano OGGI?»*, ed e' `LEZIONI.md` §1.9 regola 4: un
#   conteggio senza denominatore non e' una misura.
#
# ⭐ LA CURA NON E' UN QUARTO ESITO: il terzo c'era gia'.  `non-si-sa` esisteva
#    per il caso «la riga non porta NESSUNA impronta» (la riga di P5R delle
#    16:58 del 12 agosto).  «Ne porta MENO di quante ne servono» e' lo stesso
#    difetto in forma piu' subdola — una riga che dice «certificato» e non sa
#    dire su tutti i byte che contano — e va nello stesso esito.
#
# ⛔ E I MANCANTI VENGONO PRIMA DEI CAMBIATI, che non e' un dettaglio d'ordine.
#    «Scaduta» porta con se' una promessa — *«so esattamente che cosa e'
#    cambiato»* — e una riga a cui manca meta' del denominatore quella promessa
#    non la puo' fare: direbbe «cambiato X» tacendo che di Y e Z non sa niente,
#    che e' precisamente il «denominatore che promette una cosa e ne misura
#    un'altra» condannato in testa a questo file.  ⇒ Prima si dichiara che il
#    denominatore e' rotto, e quel che si e' comunque potuto misurare si dice
#    **dentro la stessa spiegazione**, invece di perderlo.
#
# ⚠ Il verso opposto — la riga porta PIU' file di quanti il catalogo ne conti
#   oggi — non e' un buco: si continua a confrontarli tutti, cioe' si e' piu'
#   severi, e un file tolto dal catalogo che nel frattempo e' cambiato fa
#   scadere la riga.  Va bene cosi': e' l'errore dalla parte giusta.
# ===========================================================================
def confronta_impronte(vecchie, nuove):
    """(verdetto, spiegazione).  verdetto: «uguali» · «cambiate» · «non-si-sa»

    ⛔ I TRE ESITI, e il terzo ha tre ragioni diverse:

      uguali      la riga risponde di TUTTI i file che contano oggi, e sono
                  identici a quelli su cui la certificazione e' stata fatta;
      cambiate    ⇒ «scaduta»: i file che la riga porta sono cambiati;
      non-si-sa   ⇒ «non riverificabile», e cioe':
                    · la riga non porta NESSUNA impronta, oppure
                    · ⭐ ne porta MENO di quante il catalogo ne conta oggi,
                      oppure
                    · un file non si legge da questa macchina.

    ⚠ `nuove` dev'essere il conto di OGGI per intero — cioe' `impronte_di()`,
      che mette una chiave per ogni file del catalogo anche quando il valore e'
      `None`.  ⛔ Passare qui un dizionario potato renderebbe il controllo dei
      mancanti cieco esattamente come lo era il ciclo di prima.
    """
    if not vecchie:
        return "non-si-sa", "la certificazione non porta nessuna impronta"
    cambiati, ciechi = [], []
    for nome, vecchia in sorted(vecchie.items()):
        nuova = nuove.get(nome)
        if vecchia is None or nuova is None:
            ciechi.append(nome)
        elif vecchia != nuova:
            cambiati.append(nome)
    # ⛔ IL DENOMINATORE PRIMA DEL RISULTATO — vedi il riquadro qui sopra.
    mancanti = sorted(set(nuove) - set(vecchie))
    if mancanti:
        perche = (f"la riga porta {len(vecchie)} impronte, il catalogo oggi ne "
                  f"conta {len(nuove)}: di «{', '.join(mancanti)}» quella "
                  f"certificazione non sa niente")
        if cambiati:
            perche += (" — e dei file che porta sono gia' cambiati: "
                       + ", ".join(cambiati))
        return "non-si-sa", perche
    if cambiati:
        return "cambiate", "cambiati da allora: " + ", ".join(cambiati)
    if ciechi:
        return "non-si-sa", ("non si sono potuti confrontare: "
                             + ", ".join(ciechi))
    return "uguali", f"{len(vecchie)} file, tutti identici alla certificazione"


def conta(p, ago):
    """Quante volte l'appiglio compare.  ⛔ (None) = non ho potuto guardare."""
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read().count(ago)
    except OSError:
        return None


def prepara_copia(g):
    """Rifa' da zero la copia intera del banco che questo guasto tocca.

    ⛔ Si rifa' SEMPRE, anche se la cartella c'e' gia': una copia rimasta da un
       giro precedente potrebbe portarsi dietro il guasto di quel giro, e il
       banco partirebbe **gia' rosso** — cioe' il verde di partenza, che e' la
       meta' della certificazione, sarebbe perso senza che nessuno lo veda.
    """
    corredo = CORREDO.get(g["sigla"])
    if not corredo:
        return True, ""
    os.makedirs(COPIE, exist_ok=True)
    fatti = []
    for nome in corredo:
        orig = os.path.join(QUI, nome)
        if not os.path.exists(orig):
            return False, f"⛔ l'originale non c'e': {orig}"
        shutil.copy2(orig, os.path.join(COPIE, nome))
        fatti.append(nome)
    # ⛔ E si guarda l'ESITO del costruttore, non la presenza del file: qui
    #    l'esito e' che le impronte della copia e dell'originale combacino.
    for nome in corredo:
        a = impronta_file(os.path.join(QUI, nome))
        b = impronta_file(os.path.join(COPIE, nome))
        if a is None or a != b:
            return False, f"⛔ la copia di {nome} non e' identica all'originale"
    # le registrazioni di B4 stanno in una cartella accanto
    if g["sigla"] == "B4":
        sorgente = os.path.join(QUI, "b4-registrazioni")
        if os.path.isdir(sorgente):
            dest = os.path.join(COPIE, "b4-registrazioni")
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(sorgente, dest)
    return True, "copia intera: " + ", ".join(fatti)


# ---------------------------------------------------------------------------
# ⛔ IL GUASTO CHE SOSTITUISCE UN FILE INTERO (oggi: B13).
#
#    Non c'e' nessuna stringa da contare: quel che qui prende il posto
#    dell'«appiglio unico» e' **che i due file siano diversi**.  Se fossero gia'
#    uguali il guasto non costruirebbe niente, il banco sarebbe gia' rosso, e
#    la certificazione leggerebbe «era gia' rosso» — la trappola n.4.
# ---------------------------------------------------------------------------
def _originale(dove):
    return os.path.join(ORIGINALI, os.path.basename(dove))


def verifica_copia(sigla, silenzioso=False):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    a, b = impronta_file(dove), impronta_file(da)
    if a is None or b is None:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ non si leggono i due file:")
            print(f"        {dove}: {'letto' if a else '⛔ NO'}")
            print(f"        {da}: {'letto' if b else '⛔ NO'}")
            print("        Non e' «sono uguali»: e' che non si e' potuto "
                  "guardare.")
        return -1
    if a == b:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  «{sigla}»: i due file sono GIA' "
                  f"identici ({a[:16]}…)")
            print("        ⛔ Il guasto non costruirebbe niente e il banco "
                  "sarebbe gia' rosso:")
            print("           «e' diventato rosso» non vuol dire niente senza "
                  "il verde di partenza.")
            print("        ⚠ E puo' voler dire che un giro precedente e' morto "
                  "col guasto addosso:")
            print(f"           l'originale, se c'e', sta in {_originale(dove)}")
        return 0
    if not silenzioso:
        print(f"    {VERDE}OK{GRIGIO}  «{sigla}»: i due file sono DIVERSI, "
              f"come devono essere")
        print(f"        {os.path.basename(dove)} {a[:16]}…  "
              f"{os.path.basename(da)} {b[:16]}…")
    return 1


def applica_copia(sigla):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    prima = impronta_file(dove)
    os.makedirs(ORIGINALI, exist_ok=True)
    orig = _originale(dove)
    # ⛔ L'originale si mette da parte PRIMA, e con la sua impronta accanto: un
    #    `--togli` che rimettesse un file senza sapere che impronta doveva
    #    avere si dichiarerebbe riuscito su qualunque cosa.
    shutil.copy2(dove, orig)
    if impronta_file(orig) != prima:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ la copia dell'originale non e' "
              f"identica all'originale: il guasto NON si innesta")
        return 2
    with open(orig + ".sha256", "w", encoding="utf-8") as f:
        f.write(prima + "\n")
    shutil.copy2(da, dove)
    dopo = impronta_file(dove)
    atteso = impronta_file(da)
    if dopo != atteso:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo la copia {dove} non ha "
              f"l'impronta di {da}: il guasto non e' stato innestato")
        return 2
    if dopo == prima:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file non e' cambiato: il guasto "
              f"non e' stato innestato")
        return 2
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» innestato: "
          f"{os.path.basename(dove)} adesso E' {os.path.basename(da)}")
    print(f"        prima {prima[:16]}…  dopo {dopo[:16]}…")
    print(f"        l'originale e' in {orig} (impronta accanto)")
    print(f"        ⛔ e adesso il banco «{g['banco']}» DEVE diventare rosso")
    return 0


def togli_copia(sigla):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    orig = _originale(dove)
    atteso = None
    try:
        with open(orig + ".sha256", encoding="utf-8") as f:
            atteso = f.read().strip()
    except OSError:
        pass
    if atteso is None or not os.path.exists(orig):
        # ⛔ E QUESTO NON E' «niente da togliere».  Se i due file sono uguali e
        #    l'originale non c'e', il guasto e' addosso al codice e nessuno ha
        #    piu' i byte per toglierlo: e' la trappola n.3 al suo peggio, e si
        #    urla invece di uscire 0.
        if impronta_file(dove) is not None and \
                impronta_file(dove) == impronta_file(da):
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ i due file sono IDENTICI e "
                  f"l'originale di {os.path.basename(dove)} NON c'e'")
            print(f"        Il guasto «{sigla}» e' addosso al sistema e da qui "
                  f"non si puo' togliere:")
            print("        va rigenerato il certificato della pagina, e finche' "
                  "non lo e' ogni")
            print("        misura di B13 e di C2 su questa macchina e' "
                  "avvelenata.")
            return 5
        print(f"    --  «{sigla}»: nessun originale da rimettere, e i due file "
              f"sono gia' diversi")
        return 0
    shutil.copy2(orig, dove)
    adesso = impronta_file(dove)
    if adesso != atteso:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo il ripristino l'impronta e' "
              f"{str(adesso)[:16]}… e doveva essere {atteso[:16]}…")
        return 5
    if adesso == impronta_file(da):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ rimesso l'originale, i due "
              f"certificati sono ANCORA identici: non era il file giusto")
        return 5
    for p in (orig, orig + ".sha256"):
        try:
            os.remove(p)
        except OSError:
            pass
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» tolto, e verificato: "
          f"{os.path.basename(dove)} e' tornato {atteso[:16]}… e i due "
          f"certificati sono di nuovo DUE")
    return 0


def verifica(sigla, silenzioso=False):
    g = GUASTI[sigla]
    if g["costa"] == "copia-di-file":
        return verifica_copia(sigla, silenzioso)
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        if not silenzioso:
            print(f"    {GIALLO}[?]{GRIGIO} «{sigla}» non ha un appiglio: "
                  f"e' un guasto di tipo «{g['costa']}»")
        return 0
    ok, testo = prepara_copia(g)
    if not ok:
        print(f"    {ROSSO}NO{GRIGIO}  {testo}")
        return -1
    n = conta(g["dove"], g["appiglio"])
    if n is None:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ non si legge: {g['dove']}")
            print("        Non e' «l'appiglio non c'e'»: e' che non si e' "
                  "potuto guardare.")
        return -1
    if not silenzioso:
        col = VERDE if n == 1 else ROSSO
        print(f"    {col}{'OK' if n == 1 else 'NO'}{GRIGIO}  «{sigla}»: "
              f"l'appiglio compare {n} volta/e in "
              f"{os.path.basename(g['dove'])}")
        if n == 0:
            print("        ⛔ Il guasto NON si potrebbe innestare, e il banco "
                  "resterebbe verde:")
            print("           chi legge concluderebbe «il banco non vede il "
                  "guasto», che e' l'accusa opposta.")
        elif n > 1:
            print("        ⛔ Sostituirne uno solo lascerebbe il guasto a "
                  "meta': non si applica.")
    return n


def applica(sigla):
    g = GUASTI[sigla]
    # ⛔ E IL MOTIVO DEL RIFIUTO DEV'ESSERE QUELLO VERO — rilievo R12-A.1.
    #    Qui c'era una riga sola, «l'appiglio non e' unico», stampata anche
    #    quando il guasto non ha nessun appiglio per costruzione: e' la forma
    #    del rosso puntato sull'imputato sbagliato, dentro lo strumento che
    #    esiste per non puntarlo sbagliato.
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        print(f"    {GIALLO}[?]{GRIGIO} «{sigla}»: guasto di tipo "
              f"«{g['costa']}» — da qui non si innesta, e non e' un errore")
        print("        ⛔ Ma non e' nemmeno una certificazione: chi lo lancia "
              "deve saperlo,")
        print("           e `--giudica` lo conta fra i NON CERTIFICATI.")
        return 4
    if verifica(sigla, silenzioso=True) != 1:
        print(f"    {ROSSO}NO{GRIGIO}  «{sigla}»: lo stato di partenza non e' "
              f"quello che il guasto vuole — NON si innesta")
        verifica(sigla)
        return 2
    if g["costa"] == "copia-di-file":
        return applica_copia(sigla)
    prima = impronta_file(g["dove"])
    with open(g["dove"], encoding="utf-8") as f:
        t = f.read()
    t = t.replace(g["appiglio"], g["sostituto"], 1)
    with open(g["dove"], "w", encoding="utf-8") as f:
        f.write(t)
    dopo = impronta_file(g["dove"])
    # ⛔ E si guarda l'ESITO del costruttore, non la presenza del file: un file
    #    che c'era gia' e non e' cambiato darebbe la stessa faccia.
    if prima == dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file non e' cambiato: il guasto "
              f"non e' stato innestato")
        return 2
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» innestato in "
          f"{os.path.basename(g['dove'])}")
    print(f"        prima {prima[:16]}…  dopo {dopo[:16]}…")
    print(f"        ⛔ e adesso il banco «{g['banco']}» DEVE diventare rosso")
    return 0


def togli(sigla):
    g = GUASTI[sigla]
    if g["costa"] == "copia-di-file":
        return togli_copia(sigla)
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        print(f"    --  «{sigla}»: niente da togliere")
        return 0
    if not os.path.exists(g["dove"]):
        print(f"    --  «{sigla}»: {g['dove']} non c'e' — niente da togliere")
        return 0
    with open(g["dove"], encoding="utf-8") as f:
        t = f.read()
    if g["sostituto"] and g["sostituto"] in t:
        t = t.replace(g["sostituto"], g["appiglio"], 1)
        with open(g["dove"], "w", encoding="utf-8") as f:
            f.write(t)
    # ⛔ E POI SI VERIFICA, invece di fidarsi.  Un `--togli` che non toglie e' il
    #    difetto noto n.1 degli innesti di questa fase.
    resta = conta(g["dove"], MARCA)
    if resta:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ RESTANO {resta} marche «{MARCA}» in "
              f"{os.path.basename(g['dove'])}")
        print("        Un interruttore che fa mentire il codice non deve")
        print("        sopravvivere al giro: qui sopravvive.")
        return 5
    n = conta(g["dove"], g["appiglio"])
    if n != 1:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo il ripristino l'appiglio compare "
              f"{n} volte, non 1: il file non e' quello di prima")
        return 5
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» tolto, e verificato: nessuna "
          f"marca residua, appiglio al suo posto")
    return 0


# ===========================================================================
def giudica(percorso, scena=None):
    """Legge gli esiti dei tre passi e dice CHI e' certificato.

    Ogni riga del file e' `{"sigla":…, "passo":"sano|guasto|risano|saltato",
    "uscita":N, "marca_vista":bool}`.

    ⛔ E `marca_vista` si legge su TUTT'E TRE i passi, non solo sul guasto: la
       seconda meta' del criterio e' che il giro **sano** non dicesse gia' la
       marca (R12-A.3).

    ⛔⭐ E `scena` — CHE COSA E' STATO INTERROGATO — entra nella riga di
        registro, difetto **D6**, 12 agosto 2026.

    Fino a oggi la riga diceva **chi**, **quando** e **su quali byte**, e non
    diceva **contro che cosa**.  ⛔ Finche' l'orchestratore sapeva accendere un
    solo server la cosa non si vedeva; dal 12 agosto `01-b12-lancia.sh` si
    punta anche sul **prodotto**, e senza questo campo due righe «B13
    certificato» scritte contro due server diversi hanno lo stesso aspetto.

      ⛔ *E' la forma **E8** applicata al registro: «vuoto» e «un'altra scena»
         si leggono uguali.  E non e' un'ipotesi — e' gia' successo: contro
         l'INNESTO il giro sano di B13 esce **1** (B13.4, «la pagina servita in
         TCP», che l'innesto non serve) e contro il PRODOTTO esce **3**, che e'
         l'atteso del catalogo.  Il numero era giusto e la SCENA era sbagliata.*

    ⚠ E una riga senza scena non si arrotonda a «innesto»: si scrive
      «non dichiarata», che e' quel che e'.
    """
    try:
        with open(percorso, encoding="utf-8") as f:
            righe = [json.loads(r) for r in f if r.strip()]
    except (OSError, ValueError) as e:
        print(f"    {ROSSO}⛔ gli esiti non si leggono ({e}): non c'e' niente "
              f"da giudicare{GRIGIO}")
        return 2

    per_sigla = {}
    for r in righe:
        per_sigla.setdefault(r["sigla"], {})[r["passo"]] = r

    print("== ⛔ Chi e' CERTIFICATO, e chi no")
    print("   (certificato = verde prima · rosso col guasto, con una marca che")
    print("    il giro SANO non diceva gia' · verde dopo)")
    # ⛔ LA SCENA SI DICHIARA PRIMA DEI NOMI, non dopo i numeri: chi legge un
    #    «certificato» ha diritto di sapere contro che cosa, prima di leggerlo.
    if scena:
        print(f"   ⭐ scena interrogata: {GIALLO}{scena}{GRIGIO}")
    else:
        print(f"   {GIALLO}⚠ SCENA NON DICHIARATA{GRIGIO}: chi ha lanciato "
              f"questo giudizio non ha detto contro")
        print("     che cosa ha misurato, e la riga di registro lo scrivera' "
              "come tale.  ⛔ Non e'")
        print("     «innesto»: e' «non si sa», e le due cose non si "
              "arrotondano (D6).")
    print()
    certificati, no, saltati = [], [], []
    for sigla in sorted(per_sigla):
        p = per_sigla[sigla]
        g = GUASTI.get(sigla, {"banco": sigla, "marca": ""})
        sano = p.get("sano")
        rotto = p.get("guasto")
        risano = p.get("risano")
        motivi = []
        # ⛔ IL BANCO CHE NON SI E' NEMMENO POTUTO LANCIARE — e non e' «mai
        #    provato»: e' provato e non riuscito, per una ragione che ha un
        #    nome.  Tenerli separati e' il rilievo R12-A.4 applicato al giro.
        # ⛔⭐ IL BANCO CHE PORTA IL PROPRIO GUASTO DENTRO — rilievo R12-A.48,
        #     11 agosto 2026, e il modello a tre passi NON gli si applica.
        #
        # B11 e' l'unico cosi': `01-b11-guasto-innesta.py` costruisce un server
        # che sbaglia apposta, e `01-b11-lancia.sh` gira la pagina **prima
        # contro il server SANO** — dove i casi che si aspettano un congedo
        # devono cadere TUTTI — e poi contro quello guasto.
        # ⚠ Il suo giro «sano» dev'essere ROSSO: e' il controllo che dice no.
        #   Infilarlo nel modello sano/verde di B12 vorrebbe dire scrivere
        #   numeri che non descrivono quel che e' successo.
        #
        # ⛔ E QUESTA NON E' UNA SCAPPATOIA: si pretendono ENTRAMBE le meta',
        #    esplicite.  Un giro che porta solo «il guasto e' verde» non
        #    certifica niente — sarebbe compatibile con una pagina che dichiara
        #    conforme qualunque cosa, che e' esattamente cio' che il controllo
        #    che dice no esiste per escludere.
        if p.get("proprio-giro"):
            pg = p["proprio-giro"]
            controllo = bool(pg.get("controllo_rosso"))
            guasto_ok = bool(pg.get("guasto_verde"))
            if g.get("costa") != "gia-fatto":
                no.append(sigla)
                print(f"  {ROSSO}NO{GRIGIO}  {sigla}  NON certificato")
                print(f"        ⛔ ha dichiarato un «proprio giro» ma nel "
                      f"catalogo non e' di tipo «gia-fatto»")
            elif controllo and guasto_ok:
                certificati.append(sigla)
                print(f"  {VERDE}OK{GRIGIO}  {sigla}  ⭐ certificato dal PROPRIO "
                      f"giro ({pg.get('come', 'lanciatore suo')})")
                print(f"        ⭐ il controllo che dice NO e' rosso: "
                      f"{pg.get('controllo', 'la pagina contro il server sano')}")
                print(f"        ⭐ e contro il server guasto e' verde: "
                      f"{pg.get('guasto', '—')}")
                if pg.get("riserva"):
                    print(f"        {GIALLO}⚠ con una riserva scritta: "
                          f"{pg['riserva']}{GRIGIO}")
            else:
                no.append(sigla)
                print(f"  {ROSSO}NO{GRIGIO}  {sigla}  NON certificato")
                if not controllo:
                    print(f"        ⛔ il controllo che dice NO non e' rosso: "
                          f"senza, «verde col guasto» e' compatibile con un "
                          f"banco che dice sempre di si'")
                if not guasto_ok:
                    print(f"        ⛔ contro il server guasto non e' verde: "
                          f"{pg.get('guasto', 'ragione non detta')}")
            continue
        if p.get("saltato"):
            saltati.append(sigla)
            print(f"  {GIALLO}--{GRIGIO}  {sigla}  NON certificato — non "
                  f"lanciato in questo giro")
            print(f"        {p['saltato'].get('perche', 'ragione non detta')}")
            print(f"        guasto: {g.get('titolo', '?')}")
            continue
        # ⛔ LA TRAPPOLA N.1, CHIUSA DAL SUO GUARDIANO — rilievo R12-A.3.
        #    Qui c'era `if g.get("marca") and not rotto.get("marca_vista")`:
        #    con il campo VUOTO l'intero controllo saltava, e sei guasti su
        #    dodici hanno un campo vuoto.  B4 e' stato certificato cosi'.
        if not g.get("marca"):
            motivi.append("⛔ il guasto non dichiara nessuna MARCA: «il banco "
                          "e' diventato rosso» non si puo' attribuire a questo "
                          "guasto, e una compilazione fallita rende rosso "
                          "qualunque banco (trappola n.1)")
        if sano is None:
            motivi.append("il giro SANO non e' stato fatto: «e' diventato "
                          "rosso» non vuol dire niente senza il verde di "
                          "partenza")
        else:
            if sano["uscita"] != g.get("atteso_sano", 0):
                motivi.append(f"il giro SANO esce {sano['uscita']} e ne era "
                              f"atteso {g.get('atteso_sano', 0)}: il banco non "
                              f"partiva dallo stato che il catalogo dichiara, e "
                              f"il guasto non dimostra niente")
            # ⛔ LA SECONDA META' DEL CRITERIO — rilievo R12-A.3.
            #    La stessa riga esiste, scritta la stessa notte, in
            #    `01-b8-cronometro.py:1571`: `gia = frase in testo_sano` … «⛔ ma
            #    il giro SANO lo diceva gia': non prova niente».  Qui non c'era,
            #    e la marca di B7 («CONGEDO», 37 volte nel giro sano) e quella
            #    di B6 («ciao-presto», il nome di un caso) passavano lo stesso.
            if g.get("marca") and sano.get("marca_vista"):
                motivi.append(f"⛔ IL GIRO SANO DICEVA GIA' «{g['marca']}»: "
                              f"una marca che compare in tutt'e due i giri non "
                              f"e' una marca, e' un modo di certificare senza "
                              f"guardare — vederla nel rosso non prova niente")
        if rotto is None:
            motivi.append("il giro col GUASTO non e' stato fatto")
        else:
            if rotto["uscita"] == g.get("atteso_sano", 0):
                motivi.append(f"⛔ COL GUASTO IL BANCO HA DATO LO STESSO ESITO "
                              f"DEL SANO ({rotto['uscita']}): e' il difetto "
                              f"che B12 esiste per trovare")
            if g.get("marca") and not rotto.get("marca_vista"):
                motivi.append(f"⛔ il banco e' rosso ma la sua uscita non "
                              f"nomina «{g['marca']}»: puo' essere rosso per "
                              f"un'altra causa (una compilazione fallita "
                              f"rende rosso qualunque banco)")
        if risano is None:
            motivi.append("il ritorno al SANO non e' stato verificato: «vede "
                          "il guasto» e «e' rimasto rotto» hanno lo stesso "
                          "aspetto")
        elif risano["uscita"] != g.get("atteso_sano", 0):
            # ⛔ E LE DUE RAGIONI NON SONO LA STESSA — difetto trovato l'11
            #    agosto 2026 curando questo file, sul primo giro vero di B13.
            #
            #    «Il banco non e' tornato verde» ha due cause opposte: il
            #    guasto e' rimasto addosso al codice, oppure il banco era gia'
            #    rosso in partenza e ci e' tornato esattamente.  Stampare
            #    «qualcosa e' rimasto addosso al codice» sul secondo caso e'
            #    il rosso puntato sull'imputato sbagliato, e manda a cercare
            #    un guasto residuo che non c'e' — dentro lo strumento che
            #    esiste per non mandare nessuno a cercare nel posto sbagliato.
            if sano is not None and risano["uscita"] == sano["uscita"]:
                motivi.append(f"il banco e' tornato ESATTAMENTE dov'era "
                              f"({risano['uscita']}), ⭐ quindi il guasto non "
                              f"e' rimasto addosso al codice — ma quel punto "
                              f"di partenza non era quello dichiarato, e la "
                              f"certificazione non si puo' dare lo stesso")
            else:
                motivi.append(f"⛔ dopo aver tolto il guasto il banco esce "
                              f"{risano['uscita']} e prima usciva "
                              f"{sano['uscita'] if sano else '?'}: qualcosa "
                              f"e' rimasto addosso al codice")
        if motivi:
            no.append((sigla, motivi))
            print(f"  {ROSSO}NO{GRIGIO}  {sigla}  NON certificato")
            for m in motivi:
                print(f"        {m}")
        else:
            certificati.append(sigla)
            print(f"  {VERDE}OK{GRIGIO}  {sigla}  ⭐ certificato: "
                  f"{sano['uscita']} → {rotto['uscita']} → "
                  f"{risano['uscita']}")
            print(f"        marca «{g['marca']}»: vista nel rosso, e il giro "
                  f"sano NON la diceva")
        print(f"        guasto: {g.get('titolo', '?')}")

    # ── IL DENOMINATORE, E QUI E' LA COSA CHE CONTA ────────────────────────
    non_toccati = sorted(set(GUASTI) - set(per_sigla))
    print()
    print("    == quel che questo giro ha davvero certificato")
    print(f"    --  guasti nel catalogo:            {len(GUASTI)}")
    print(f"    --  guasti provati in questo giro:  {len(per_sigla)}")
    print(f"    {VERDE}{len(certificati):3d}{GRIGIO}  banchi CERTIFICATI: "
          f"{', '.join(certificati) or '—'}")
    print(f"    {ROSSO}{len(no):3d}{GRIGIO}  banchi provati e NON certificati: "
          f"{', '.join(s for s, _ in no) or '—'}")
    print(f"    {GIALLO}{len(saltati):3d}{GRIGIO}  banchi non lanciabili da "
          f"qui: {', '.join(saltati) or '—'}")
    # ⛔ E LA PAROLA E' «NON PROVATI IN QUESTO GIRO», NON «MAI» — R12-A.4.
    #    Il conto e' `set(GUASTI) - set(per_sigla)`, che e' un conto **per
    #    giro**: chiamarlo «mai provati» ha fatto scrivere `mai_provati` su
    #    B7 e C2 due ore dopo averli certificati, e su B13 dopo averlo provato
    #    e bocciato.  Chi legge il registro ha diritto a sapere quel che il
    #    progetto sa, non quel che l'ultimo giro ha toccato.
    print(f"    {GIALLO}{len(non_toccati):3d}{GRIGIO}  banchi NON PROVATI IN "
          f"QUESTO GIRO: {', '.join(non_toccati) or '—'}")
    print("        ⚠ «non provati in questo giro» non e' «mai provati»: quel")
    print("          che si sa di loro sta nelle righe di prima, e lo mette")
    print("          insieme `--registro`.")
    print("        ⛔ E nessuno di questi e' «pulito»: fuori da una "
          "certificazione valida sono NON CERTIFICATI.")

    # ⛔ Il registro, con la data e le impronte dei file che contano davvero.
    sorgente = os.path.join(QUI, "rcp", "rcp.c")
    riga = {
        "quando": datetime.datetime.now().isoformat(timespec="seconds"),
        # ⛔ E DA QUALE MACCHINA, perche' non e' un dettaglio: questo registro
        #    ha lo stesso nome in due posti — sulla macchina dei documenti e su
        #    quella di prova — e le righe finiscono nello stesso file.  ⚠ E'
        #    anche la ragione per cui l'ordine di scrittura non e' l'ordine del
        #    tempo (R12-A.4), e per cui B4 e B9 si possono certificare solo di
        #    qua e C2 e B13 solo di la': i file dei banchi non stanno tutti
        #    sulla stessa macchina.  Una riga senza questo campo non dice se
        #    «non provato» voglia dire «non provabile da li'».
        "macchina": socket.gethostname(),
        # ⛔ CONTRO CHE COSA — difetto D6.  «non dichiarata» e' un valore, non
        #    un buco: le righe scritte prima del 12 agosto 2026 non lo portano,
        #    e `--registro` deve poterle distinguere da quelle che lo portano.
        "scena": scena or "non dichiarata",
        "certificati": certificati,
        "non_certificati": [s for s, _ in no],
        "saltati": saltati,
        "non_provati_in_questo_giro": non_toccati,
        # ⛔ L'impronta PER BANCO, sui file che quella certificazione ha
        #    davvero usato (R12-A.5).  `impronta_rcp_c` resta per continuita'
        #    con le due righe del 10 agosto, ⚠ ma non e' piu' il denominatore:
        #    `rcp.c` non partecipa alla certificazione di B4 e di B9.
        "impronte": {s: impronte_di(s) for s in sorted(per_sigla)},
        "impronta_rcp_c": (impronta_file(sorgente) or "?")[:32],
    }
    try:
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
        print(f"\n    --  scritto in {REGISTRO}")
        print("        ⚠ La certificazione ha una DATA e l'impronta dei file")
        print("          che ha usato: un banco certificato su file che nel")
        print("          frattempo sono cambiati non e' certificato oggi, e")
        print("          `--registro` lo dice invece di lasciarlo credere.")
    except OSError as e:
        print(f"\n    {GIALLO}[?] il registro non si e' scritto: {e}{GRIGIO}")

    # ⛔ ZERO BANCHI PROVATI NON E' «TUTTO A POSTO».
    if not per_sigla:
        print(f"\n    {ROSSO}⛔ B12 non ha provato NESSUN banco: non e' un "
              f"verde{GRIGIO}")
        return 2
    if no or saltati:
        return 1
    if non_toccati:
        return 3
    return 0


# ===========================================================================
# ⛔ IL REGISTRO LETTO COME UNA STORIA, NON COME UN'ULTIMA RIGA — R12-A.4
# ===========================================================================
def _normalizza(r):
    """Una riga vecchia e una nuova, lette con lo stesso metro."""
    return {
        "quando": r.get("quando", "?"),
        "macchina": r.get("macchina", "?"),
        # ⚠ D6, 12 agosto 2026: le righe scritte prima non hanno questo campo,
        #   e la parola giusta e' «non dichiarata» — non «innesto».  Dedurla
        #   dal contesto vorrebbe dire scrivere una misura che nessuno ha fatto.
        "scena": r.get("scena", "non dichiarata (riga scritta prima di D6)"),
        "certificati": r.get("certificati", []),
        "non_certificati": r.get("non_certificati", []),
        "saltati": r.get("saltati", []),
        # ⚠ Le righe scritte prima dell'11 agosto 2026 chiamavano questo campo
        #   `mai_provati`, e la parola era falsa: qui si legge col nome vero.
        "non_provati": r.get("non_provati_in_questo_giro",
                             r.get("mai_provati", [])),
        "impronte": r.get("impronte", {}),
        "impronta_rcp_c": r.get("impronta_rcp_c", "?"),
        "vecchio_nome": "mai_provati" in r,
    }


# ===========================================================================
# ⛔ IL REGISTRO VIVE IN DUE COPIE, E FINO A OGGI SI UNIVANO A MANO — D10
# ===========================================================================
#
# `--giudica` scrive **in fondo alla copia della macchina da cui gira**, e le
# macchine sono due: CHUWI, dove stanno il deposito e i documenti, e NIC-OS,
# dove stanno la sessione grafica e il prodotto.  Nessuna delle due vede il
# file dell'altra.  ⇒ Il conto vero e' l'UNIONE delle due, e fino a oggi
# l'unione la faceva **una persona, a mano**, copiando le righe da una parte
# all'altra (`fasi/01-filo-nudo.md`, R12-A.36, 11 agosto 2026).
#
# ⛔ **Un passo a mano in mezzo a una catena automatica e' un passo che prima o
#    poi qualcuno salta**, e quando lo salta il conto delle certificazioni cala
#    senza che nessuno se ne accorga — perche' una riga che non c'e' non
#    protesta.  ⭐ E non e' un'ipotesi: `[M]` 12 agosto 2026, prima di scrivere
#    una riga di questa cura, le due copie divergevano gia'.  CHUWI ne aveva 40
#    e NIC-OS 37; **cinque righe stavano solo su CHUWI e due solo su NIC-OS**,
#    scritte la sera dell'11 e mai tornate indietro.  L'ultima unione a mano era
#    delle 20:51 di NIC-OS, e da allora il passo era stato saltato **sette
#    volte**.
#
# ---------------------------------------------------------------------------
# ⛔ LE DUE STRADE, E PERCHE' SI PRENDONO TUTT'E DUE
#
# La scelta era fra **uno strumento che unisce** e **uno strumento che si
# rifiuta di rispondere finche' le due copie non sono unite**.  Prese da sole
# non bastano ne' l'una ne' l'altra, e la ragione e' l'**asimmetria delle due
# macchine**:
#
#   · **Il solo rifiuto non e' implementabile onestamente.**  `--registro`
#     «gira dovunque», ed e' precisamente il suo valore.  Ma da NIC-OS — e a
#     maggior ragione da dentro il contenitore — la copia di CHUWI **non e'
#     raggiungibile**: solo CHUWI sa arrivare al server.  Un `--registro` che
#     si rifiutasse di rispondere finche' non ha visto l'altra copia si
#     rifiuterebbe **per sempre**, di la'.  ⛔ E uno strumento che dice sempre
#     di no e' uno strumento che si scavalca — cioe' il passo a mano di prima,
#     con un giro in piu'.
#
#   · **La sola unione non basta a I7.**  `--unisci` resta un comando che
#     qualcuno deve lanciare, e «la protezione di un difetto noto sta nel
#     programma, non in una procedura che si puo' dimenticare» (**I7**).  Uno
#     strumento che unisce e basta sposta il passo manuale, non lo toglie.
#
# ⇒ **Si fanno tutt'e due, e la seconda meta' e' quella che chiude I7**:
#   `--unisci` fa l'unione **dentro il programma**, con le regole scritte qui
#   sotto; e `mostra_registro()` porta una **guardia** che dice, ogni volta e
#   senza rete, se l'unione e' fresca — e quando non lo e' **declassa il
#   verdetto** invece di stampare un conto che ha l'aria di essere completo.
#   ⛔ Il non aver fatto l'unione **si vede**, e si vede nel posto in cui si
#   legge il numero.
#
# ---------------------------------------------------------------------------
# ⭐ QUEL CHE L'UNIONE NON DEVE FARE, E COME SE NE ACCORGE DA SE'
#
#   1. ⛔ **non perde una riga e non ne inventa una.**  Il risultato si
#      **conta**, non si guarda: `unisci()` verifica che ogni riga di ciascuna
#      delle due copie sia presente nel risultato, e che il numero delle righe
#      sia esattamente `in comune + solo di qua + solo di la'`.  Se il conto
#      non torna **non scrive niente** e esce rosso;
#   2. ⛔ **e sa dire di no.**  Due righe che dichiarano **lo stesso giro**
#      (stessa macchina, stessa data) con contenuto **diverso** — impronte
#      diverse, per esempio — non sono un doppione da buttare: sono un
#      **conflitto**, e una delle due mente.  Chi le unisse in silenzio
#      sceglierebbe una delle due verita' senza dirlo.
#      ⭐ E che il pericolo sia reale e' MISURATO, non dedotto: `[M]` 12 agosto
#      2026, prima della cura, la stessa coppia in conflitto dava
#      **«OK C2 CERTIFICATO … e vale oggi»** o **«NO C2 … MA NON OGGI»** a
#      seconda soltanto dell'ORDINE delle due righe nel file, e la parola
#      «conflitto» non compariva mai.  ⇒ `mostra_registro()` ordinava per data,
#      trovava due righe con la stessa data, e teneva l'ultima **in ordine di
#      file** — cioe' sceglieva una delle due verita' a caso.
#      ⛔ Da cui: il conflitto **ferma l'unione** e si stampa per intero, e
#      `mostra_registro()` lo **nomina** invece di risolverlo da se'.
#
# ---------------------------------------------------------------------------
# ⚠ CHE COS'E' L'IDENTITA' DI UNA RIGA, E PERCHE' NON E' IL TESTO
#
# Una riga di registro e' **un giro**, e un giro e' identificato da **chi l'ha
# fatto e quando**: `(macchina, quando)`.  Due righe con la stessa identita' e
# lo stesso contenuto sono **la stessa riga arrivata da due parti** — l'unione
# ne tiene una.  Due righe con la stessa identita' e contenuto diverso sono un
# **conflitto**.  ⛔ Usare il testo come identita' fonderebbe le due cose: il
# conflitto sembrerebbe due righe distinte, e passerebbe.
#
# ⚠ E la marca d'unione (`tipo: "unione"`) e' una riga di servizio, non un
#   giro: non entra nel conto dei certificati, e ha una chiave sua.
# ===========================================================================

# La copia del server, e l'attrezzo che ci arriva.  ⛔ `sshpw.py --get`/`--put`
# usano `scp`: ⚠ **mai una redirezione ATTORNO a `ssh`** (`fasi/00-ambiente.md`
# B3.3), e infatti qui non ce n'e' nessuna — i byte passano da `scp`, non da un
# `cat` remoto catturato.
SERVER_REGISTRO = "/media/REMOTIX/src/01-b12-registro.jsonl"
SSHPW = os.path.join(QUI, "..", "v1", "strumenti", "sshpw.py")


def _chiave(r):
    """L'identita' di una riga: chi l'ha scritta, quando, e di che tipo."""
    return (r.get("tipo", "giro"), r.get("macchina", "?"), r.get("quando", "?"))


def _canonica(r):
    """Il contenuto di una riga, in una forma che non dipende dall'ordine
    delle chiavi: due righe uguali nel contenuto danno la stessa stringa."""
    return json.dumps(r, ensure_ascii=False, sort_keys=True)


def _e_unione(r):
    return r.get("tipo") == "unione"


def leggi_registro(percorso):
    """[dizionario] — ⛔ una riga che non e' JSON e' un ERRORE, non una riga da
    saltare: saltarla sarebbe perdere una certificazione in silenzio, che e'
    esattamente il difetto che questa cura chiude (`LEZIONI.md` §1.9)."""
    fuori = []
    with open(percorso, encoding="utf-8") as f:
        for n, testo in enumerate(f, 1):
            if not testo.strip():
                continue
            try:
                fuori.append(json.loads(testo))
            except ValueError as e:
                raise ValueError(f"{percorso} riga {n}: non e' JSON — {e}")
    return fuori


def impronta_dei_giri(righe):
    """sha256 dell'INSIEME dei giri — ⚠ ordinato, quindi NON dipende
    dall'ordine in cui stanno nel file (che non e' l'ordine del tempo)."""
    giri = sorted(_canonica(r) for r in righe if not _e_unione(r))
    return hashlib.sha256("\n".join(giri).encode("utf-8")).hexdigest()


def trova_conflitti(a, b):
    """[(chiave, [testi diversi])] — le identita' che portano piu' di un
    contenuto.  ⛔ Si guarda anche DENTRO una copia sola: due righe in
    conflitto possono essere arrivate tutt'e due dalla stessa parte."""
    per_chiave = {}
    for r in list(a) + list(b):
        per_chiave.setdefault(_chiave(r), set()).add(_canonica(r))
    return sorted((k, sorted(v)) for k, v in per_chiave.items() if len(v) > 1)


def _spiega_conflitto(testi):
    """I campi su cui due righe con la stessa identita' non vanno d'accordo."""
    letti = [json.loads(t) for t in testi]
    campi = sorted({c for d in letti for c in d})
    fuori = []
    for c in campi:
        valori = {json.dumps(d.get(c), ensure_ascii=False, sort_keys=True)
                  for d in letti}
        if len(valori) > 1:
            fuori.append((c, sorted(valori)))
    return fuori


def unisci(percorso_altra, rispecchia_su=None, impronta_altra_letta=None):
    """⛔ Unisce la copia locale con `percorso_altra`, e non perde ne' inventa.

    Esce 0 se l'unione e' riuscita, 1 se c'e' un conflitto (e allora **non
    scrive niente**), 2 se una delle due copie non si legge.
    """
    print("== ⛔ L'UNIONE DELLE DUE COPIE DEL REGISTRO — D10")
    print(f"   qui:   {REGISTRO}")
    print(f"   altra: {percorso_altra}\n")
    if not os.path.exists(REGISTRO):
        print(f"    {ROSSO}⛔ qui non c'e' nessun registro: non si unisce "
              f"niente{GRIGIO}")
        return 2
    try:
        a = leggi_registro(REGISTRO)
        b = leggi_registro(percorso_altra)
    except (OSError, ValueError) as e:
        print(f"    {ROSSO}⛔ non si legge: {e}{GRIGIO}")
        return 2

    # ── 1. ⛔ IL CONFLITTO PRIMA DI TUTTO, E FERMA L'UNIONE ─────────────────
    conflitti = trova_conflitti(a, b)
    if conflitti:
        print(f"    {ROSSO}⛔ {len(conflitti)} CONFLITTI: l'unione NON si fa, e "
              f"il registro resta com'e'{GRIGIO}\n")
        for (tipo, macchina, quando), testi in conflitti:
            print(f"    ⛔ stesso giro «{macchina}» {quando} ({tipo}), "
                  f"{len(testi)} contenuti DIVERSI:")
            for campo, valori in _spiega_conflitto(testi):
                print(f"         campo «{campo}» —")
                for v in valori:
                    print(f"           · {v[:200]}")
            print()
        print("    ⛔ Due righe che dichiarano LO STESSO GIRO con contenuto")
        print("       diverso non sono un doppione da buttare: una delle due")
        print("       mente.  Chi le unisse in silenzio sceglierebbe una delle")
        print("       due verita' senza dirlo — e fino al 12 agosto 2026")
        print("       `--registro` faceva proprio questo, tenendo quella che")
        print("       capitava piu' in basso nel file.")
        print("    ⇒ Si guarda quale delle due e' vera (le impronte si")
        print("       ricalcolano: `--impronte <SIGLA>`), si toglie l'altra a")
        print("       ragion veduta, e si riunisce.")
        return 1

    # ── 2. L'UNIONE, tenendo l'ordine di qua e accodando quel che manca ─────
    visti = {}                       # chiave → testo canonico
    risultato, presi_da_b = [], []
    for r in a:
        k = _chiave(r)
        if k in visti:               # doppione identico DENTRO questa copia
            continue
        visti[k] = _canonica(r)
        risultato.append(r)
    for r in b:
        k = _chiave(r)
        if k in visti:
            continue
        visti[k] = _canonica(r)
        risultato.append(r)
        presi_da_b.append(r)

    # ── 3. ⛔ IL CONTO, E SI CONTA — NON SI GUARDA ──────────────────────────
    ka = {_chiave(r) for r in a}
    kb = {_chiave(r) for r in b}
    comune, solo_a, solo_b = ka & kb, ka - kb, kb - ka
    print(f"    --  righe di qua:              {len(a):3d}  "
          f"({len(ka)} giri distinti)")
    print(f"    --  righe di la':              {len(b):3d}  "
          f"({len(kb)} giri distinti)")
    print(f"    --  in comune:                 {len(comune):3d}")
    print(f"    --  solo di qua:               {len(solo_a):3d}")
    print(f"    --  solo di la':               {len(solo_b):3d}")
    print(f"    --  risultato dell'unione:     {len(risultato):3d}")
    atteso = len(comune) + len(solo_a) + len(solo_b)
    if len(risultato) != atteso:
        print(f"    {ROSSO}⛔ IL CONTO NON TORNA: attese {atteso} righe, "
              f"l'unione ne ha {len(risultato)}.  NON SI SCRIVE.{GRIGIO}")
        return 1
    # ⛔ E il conto da solo non basta: si verifica che OGNI riga di ciascuna
    #    delle due copie sia davvero dentro il risultato.  Un conto giusto con
    #    una riga scambiata per un'altra darebbe lo stesso numero.
    dentro = {_canonica(r) for r in risultato}
    perse = [(_chiave(r), q) for q, orig in (("qui", a), ("la'", b))
             for r in orig if _canonica(r) not in dentro]
    if perse:
        print(f"    {ROSSO}⛔ {len(perse)} RIGHE ANDREBBERO PERSE: "
              f"{perse[:5]}.  NON SI SCRIVE.{GRIGIO}")
        return 1
    inventate = [_chiave(r) for r in risultato
                 if _canonica(r) not in {_canonica(x) for x in list(a) + list(b)}]
    if inventate:
        print(f"    {ROSSO}⛔ {len(inventate)} RIGHE INVENTATE: "
              f"{inventate[:5]}.  NON SI SCRIVE.{GRIGIO}")
        return 1
    print(f"    {VERDE}⭐ nessuna riga persa, nessuna inventata{GRIGIO} "
          f"(verificato contando, riga per riga)")

    if solo_b:
        print(f"\n    ⭐ {len(solo_b)} righe erano SOLO di la', e adesso ci sono "
              f"anche qui:")
        for r in presi_da_b:
            print(f"       · {r.get('quando','?')} su «{r.get('macchina','?')}» "
                  f"— certificati: "
                  f"{', '.join(r.get('certificati', [])) or '—'} · "
                  f"NON certificati: "
                  f"{', '.join(r.get('non_certificati', [])) or '—'}")
    if solo_a:
        print(f"\n    ⚠ {len(solo_a)} righe stanno solo di qua: l'altra copia "
              f"non le ha.")
        print("       Con `--rispecchia` gliele si rimanda; senza, la sua "
              "meta' dell'unione resta da fare.")

    # ── 4. LA MARCA D'UNIONE.  ⛔ Sta DENTRO il registro e non accanto: un
    #    file di stato a fianco e' precisamente «la riga di configurazione che
    #    si puo' perdere» che **I7** vieta.  Chi copia il registro si porta
    #    dietro anche la prova di quando e' stato unito.
    marca = {
        "tipo": "unione",
        "quando": datetime.datetime.now().isoformat(timespec="seconds"),
        "macchina": socket.gethostname(),
        "con": os.path.abspath(percorso_altra),
        "righe_qui_prima": len(a),
        "righe_di_la": len(b),
        "righe_prese_di_la": len(solo_b),
        "righe_dopo": len(risultato),
        # ⭐ L'impronta dell'INSIEME dei giri dopo l'unione: e' quel che
        #    `mostra_registro()` ricalcola per sapere, senza rete, se dopo
        #    l'ultima unione qualcuno ha scritto altro.
        "impronta_giri": impronta_dei_giri(risultato),
        # ⛔⭐ E L'ELENCO DELLE IDENTITA' UNITE, NON SOLO LA LORO IMPRONTA.
        #
        #    Serviva a `stato_unione()` per dire QUANTI giri sono arrivati dopo
        #    l'unione, e la prima stesura lo deduceva confrontando le date con
        #    quella della marca.  ⛔ Sbagliato, e il caso costruito l'ha fatto
        #    vedere subito: un giro scritto **dopo** l'unione ma con una data
        #    **anteriore** — che e' la norma, non l'eccezione, perche' le due
        #    macchine hanno due orologi e l'11 agosto 2026 il server era
        #    indietro di circa due ore — veniva contato **zero**.  La guardia
        #    diceva «unione vecchia, 0 giri nuovi», cioe' un numero falso
        #    accanto a un verdetto giusto.
        #    ⭐ Con l'elenco delle identita' il confronto e' esatto e non passa
        #       da nessun orologio: nuovo = identita' che l'unione non aveva.
        "giri_uniti": sorted(f"{r.get('macchina','?')}|{r.get('quando','?')}"
                             for r in risultato if not _e_unione(r)),
        # ⚠ E l'impronta dell'altra copia com'era quando l'abbiamo letta:
        #   serve alla prossima unione per dire «di la' e' cambiato qualcosa».
        "impronta_altra": impronta_altra_letta or impronta_dei_giri(b),
        "rispecchiata": bool(rispecchia_su),
    }
    risultato.append(marca)

    # ── 5. SI SCRIVE DI FIANCO E SI RILEGGE, POI SI SOSTITUISCE ────────────
    #    ⛔ Un `open(…, "w")` che muore a meta' lascia un registro troncato, e
    #       un registro troncato e' esattamente «il conto cala e nessuno se ne
    #       accorge».  Si scrive un file nuovo, lo si RILEGGE, e solo se
    #       rilegge giusto prende il posto dell'altro.
    tmp = REGISTRO + ".unione-in-corso"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            for r in risultato:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        riletto = leggi_registro(tmp)
        if len(riletto) != len(risultato) or \
                impronta_dei_giri(riletto) != marca["impronta_giri"]:
            print(f"    {ROSSO}⛔ il file scritto non si rilegge uguale: NON "
                  f"si sostituisce niente{GRIGIO}")
            os.unlink(tmp)
            return 1
        os.replace(tmp, REGISTRO)
    except OSError as e:
        print(f"    {ROSSO}⛔ non si e' scritto: {e}{GRIGIO}")
        return 1
    print(f"\n    --  scritto in {REGISTRO}: "
          f"{len(a)} → {len(risultato) - 1} giri, piu' la marca d'unione")

    # ── 6. E, SE CHIESTO, LA SI RIMANDA DI LA' ─────────────────────────────
    if rispecchia_su:
        return 0 if rispecchia(rispecchia_su, impronta_altra_letta) else 1
    return 0


def prendi_dal_server(dove):
    """Porta qui la copia del server con `scp`.  Vero se c'e' riuscito."""
    esito = os.spawnv(os.P_WAIT, sys.executable,
                      [sys.executable, SSHPW, "--get", SERVER_REGISTRO, dove])
    if esito != 0 or not os.path.exists(dove):
        print(f"    {ROSSO}⛔ la copia del server non e' arrivata (uscita "
              f"{esito}){GRIGIO}")
        print("       ⚠ Da NIC-OS questo comando non serve e non funziona: di "
              "la' l'unione")
        print("         si fa con `--unisci <percorso della copia di CHUWI>`, "
              "portata a mano")
        print("         una volta sola.  ⛔ E' l'asimmetria delle due macchine: "
              "solo CHUWI")
        print("         sa arrivare al server.")
        return False
    return True


def rispecchia(impronta_attesa_di_la, _non_usato=None):
    """⛔ Rimanda al server il registro unito — ma SOLO se di la' non e'
    cambiato niente da quando l'abbiamo letto.

    ⚠ Sulle due macchine lavorano piu' agenti insieme, e un giro finito fra la
      nostra lettura e la nostra scrittura verrebbe **cancellato** da questa
      copia.  Si rilegge l'impronta di la' e, se non e' piu' quella, ci si
      ferma: un'unione rifatta costa un minuto, una certificazione persa non
      si accorge nessuno.
    """
    import tempfile
    print("\n    == ⛔ si rimanda la copia unita al server, se di la' non e' "
          "cambiato niente")
    with tempfile.TemporaryDirectory() as d:
        controllo = os.path.join(d, "controllo.jsonl")
        if not prendi_dal_server(controllo):
            return False
        try:
            adesso = impronta_dei_giri(leggi_registro(controllo))
        except (OSError, ValueError) as e:
            print(f"    {ROSSO}⛔ la copia di controllo non si legge: "
                  f"{e}{GRIGIO}")
            return False
    if adesso != impronta_attesa_di_la:
        print(f"    {ROSSO}⛔ IL SERVER E' CAMBIATO fra la lettura e la "
              f"scrittura: NON si sovrascrive{GRIGIO}")
        print(f"       atteso  {impronta_attesa_di_la[:32]}…")
        print(f"       trovato {adesso[:32]}…")
        print("       ⇒ Qualcuno ha appena scritto un giro di la'.  Si rilancia "
              "`--unisci-col-server`,")
        print("         che stavolta prendera' anche quella riga.  ⭐ L'unione "
              "gia' fatta QUI e' salva.")
        return False
    esito = os.spawnv(os.P_WAIT, sys.executable,
                      [sys.executable, SSHPW, "--put", REGISTRO,
                       SERVER_REGISTRO])
    if esito != 0:
        print(f"    {ROSSO}⛔ la copia non e' arrivata al server (uscita "
              f"{esito}){GRIGIO}")
        return False
    print(f"    {VERDE}⭐ le due copie sono adesso identiche{GRIGIO} "
          f"({SERVER_REGISTRO})")
    return True


def unisci_col_server(rispecchia_pure):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        altra = os.path.join(d, "registro-del-server.jsonl")
        if not prendi_dal_server(altra):
            return 2
        try:
            impronta_la = impronta_dei_giri(leggi_registro(altra))
        except (OSError, ValueError) as e:
            print(f"    {ROSSO}⛔ la copia del server non si legge: {e}{GRIGIO}")
            return 2
        return unisci(altra,
                      rispecchia_su=impronta_la if rispecchia_pure else None,
                      impronta_altra_letta=impronta_la)


def prova_unione():
    """⛔ IL BANCO DELL'UNIONE — «chi scrive un banco lo certifica nello stesso
    giro» (`MANDATO` §3.3, regola nata l'11 agosto 2026).

    Tre casi COSTRUITI APPOSTA, e il verdetto si da' CONTANDO, non guardando:

      1. due copie divergenti, una riga solo di qua e una solo di la'
         → l'unione le tiene tutt'e due, e non ne inventa nessuna;
      2. ⛔ due righe che dichiarano LO STESSO giro con impronte DIVERSE
         → l'unione si FERMA e non scrive niente;
      3. ⭐ il controllo positivo, che e' la meta' che si dimentica: due copie
         identiche → l'unione riesce.  Senza questo caso, uno strumento che
         dicesse sempre «conflitto» passerebbe i primi due.
    """
    import tempfile
    globals_reg = REGISTRO
    esiti = []

    def riga(quando, macchina, cert, sha):
        return {"quando": quando, "macchina": macchina, "certificati": cert,
                "non_certificati": [], "saltati": [],
                "non_provati_in_questo_giro": [],
                "impronte": {c: {"finto.py": sha} for c in cert},
                "impronta_rcp_c": "z" * 32}

    def gira(qua, la):
        d = tempfile.mkdtemp()
        a, b = os.path.join(d, "qua.jsonl"), os.path.join(d, "la.jsonl")
        for p, righe in ((a, qua), (b, la)):
            with open(p, "w", encoding="utf-8") as f:
                for r in righe:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        globals()["REGISTRO"] = a
        codice = unisci(b)
        dopo = leggi_registro(a)
        shutil.rmtree(d)
        return codice, dopo

    comuni = [riga("2026-08-12T08:00:00", "NIC-OS", ["B2"], "a" * 64),
              riga("2026-08-12T08:10:00", "CHUWI", ["B4"], "b" * 64)]
    solo_qua = riga("2026-08-12T09:00:00", "CHUWI", ["P5"], "c" * 64)
    solo_la = riga("2026-08-12T09:30:00", "NIC-OS", ["B7"], "d" * 64)

    print("\n\n########## 1/3 — una riga solo di qua, una solo di la'\n")
    c, dopo = gira(comuni + [solo_qua], comuni + [solo_la])
    giri = [r for r in dopo if not _e_unione(r)]
    tutte = comuni + [solo_qua, solo_la]
    dentro = {_canonica(r) for r in giri}
    perse = [r for r in tutte if _canonica(r) not in dentro]
    inventate = [r for r in giri
                 if _canonica(r) not in {_canonica(x) for x in tutte}]
    print(f"\n    il conto: 3 + 3 → {len(giri)} giri (atteso 4) · "
          f"perse {len(perse)} · inventate {len(inventate)}")
    esiti.append(("una riga di qua e una di la'",
                  c == 0 and len(giri) == 4 and not perse and not inventate))

    print("\n\n########## 2/3 — ⛔ stesso giro, impronte DIVERSE\n")
    stesso = "2026-08-12T11:00:00"
    c, dopo = gira(comuni + [riga(stesso, "NIC-OS", ["C2"], "1" * 64)],
                   comuni + [riga(stesso, "NIC-OS", ["C2"], "9" * 64)])
    print(f"\n    uscita {c} (atteso 1) · righe rimaste {len(dopo)} "
          f"(atteso 3, cioe' com'erano) · marca d'unione "
          f"{'⛔ SCRITTA' if any(_e_unione(r) for r in dopo) else 'no — giusto'}")
    esiti.append(("il conflitto ferma l'unione",
                  c == 1 and len(dopo) == 3
                  and not any(_e_unione(r) for r in dopo)))

    print("\n\n########## 3/3 — ⭐ controllo positivo: due copie identiche\n")
    c, dopo = gira(comuni, comuni)
    giri = [r for r in dopo if not _e_unione(r)]
    print(f"\n    uscita {c} (atteso 0) · giri {len(giri)} (atteso 2) · "
          f"marca d'unione "
          f"{'si' if any(_e_unione(r) for r in dopo) else '⛔ NO'}")
    esiti.append(("il controllo positivo",
                  c == 0 and len(giri) == 2
                  and any(_e_unione(r) for r in dopo)))

    globals()["REGISTRO"] = globals_reg
    print("\n\n    == il verdetto")
    for nome, ok in esiti:
        print(f"    {(VERDE + 'OK ') if ok else (ROSSO + 'NO ')}{GRIGIO} {nome}")
    passati = sum(1 for _, ok in esiti if ok)
    print(f"\n    {VERDE if passati == len(esiti) else ROSSO}"
          f"{passati} casi su {len(esiti)}{GRIGIO}")
    return 0 if passati == len(esiti) else 1


def prova_impronte():
    """⛔ IL BANCO DEL MECCANISMO CHE FA SCADERE LE CERTIFICAZIONI — e chi
    scrive un banco lo certifica nello stesso giro (`MANDATO` §3.3).

    ⭐ Nasce dal buco del 12 agosto 2026: `main.c` e il `Makefile` sono stati
    aggiunti alle impronte dei cinque banchi del prodotto, **e il conto e'
    rimasto 15 su 15**.  Il meccanismo che avrebbe dovuto far scadere quelle
    righe non le ha nemmeno guardate.

    I TRE ESITI si distinguono qui, su casi COSTRUITI e non dedotti:

      1. ⭐ una riga che porta TUTTE le impronte di oggi        → vale oggi
      2. ⛔ una riga che ne porta MENO                          → non riverif.
      3. ⛔ una riga completa, con un'impronta diversa          → scaduta
      4. ⛔ una riga che non porta NESSUNA impronta             → non riverif.
         (il caso che il terzo esito copriva gia': non deve regredire)

    ⭐⭐ 5. E IL CONTROLLO POSITIVO DEL MECCANISMO STESSO, che e' la meta' che
    si dimentica.  I primi quattro casi passano anche su uno strumento che
    dicesse sempre «non riverificabile» — anzi: **un meccanismo fragile passa
    tutti i guasti, perche' rompersi FA diventare rossi**.  ⛔ Quindi si va
    nella direzione opposta: si prende un banco che oggi e' VERDE sul registro
    VERO, gli si aggiunge un file al catalogo, e **quel banco deve diventare
    non riverificabile**.  Se resta verde, il buco e' ancora li'.

    ⛔ E il giro e' a TRE PASSI, come ogni certificazione di questa casa —
    verde → non riverificabile → verde: senza il terzo, «il meccanismo ha visto
    il file nuovo» e «il meccanismo si e' rotto» hanno lo stesso aspetto.

    ⚠ E IL FILE FINTO E' UN FILE VERO, LEGGIBILE, CON UN CONTENUTO.  Un file
      inesistente farebbe diventare rosso il banco per la ragione sbagliata —
      la strada dei «ciechi», che esisteva gia' — e certificherebbe zero sul
      buco vero, che e' il CONTEGGIO.  ⭐ Cosi' invece l'unica cosa che cambia
      fra il passo 1 e il passo 2 e' **quante impronte il catalogo conta**.
    """
    import tempfile
    esiti = []

    def riga(quando, cert, impronte):
        return _normalizza({"quando": quando, "macchina": "banco",
                            "certificati": cert, "impronte": impronte})

    # ⭐ Si lavora su un banco VERO e sulle sue impronte VERE: un caso costruito
    #    su un catalogo finto certificherebbe il catalogo finto.
    campione = "B4"
    oggi = impronte_di(campione)
    print(f"== il banco su cui si costruiscono i casi: {campione}")
    print(f"   il catalogo oggi conta {len(oggi)} file: "
          f"{', '.join(sorted(oggi))}")
    if len(oggi) < 2:
        print(f"    {ROSSO}⛔ servono almeno due file per costruire il caso "
              f"«ne porta meno»{GRIGIO}")
        return 2
    if any(v is None for v in oggi.values()):
        print(f"    {ROSSO}⛔ qualche file di {campione} non si legge da qui: "
              f"i casi non sarebbero costruiti su impronte vere{GRIGIO}")
        return 2

    def prova(nome, impronte, atteso):
        r = riga("2026-08-12T00:00:00", [campione], {campione: impronte})
        _, stato, verdetto, perche = verdetto_di_oggi(campione, [r])
        ok = stato == "certificato" and verdetto == atteso
        print(f"\n  {(VERDE + 'OK ') if ok else (ROSSO + 'NO ')}{GRIGIO} {nome}")
        print(f"      la riga porta {len(impronte)} impronte, il catalogo "
              f"oggi ne conta {len(oggi)}")
        print(f"      verdetto «{verdetto}» (atteso «{atteso}»)")
        print(f"      perche': {perche}")
        esiti.append((nome, ok))

    print("\n\n########## 1/5 — ⭐ la riga porta TUTTE le impronte di oggi\n")
    prova("porta tutto ⇒ vale oggi", dict(oggi), "uguali")

    print("\n\n########## 2/5 — ⛔ la riga ne porta MENO (il buco del 12 "
          "agosto)\n")
    meno = dict(oggi)
    tolto = sorted(meno)[0]
    del meno[tolto]
    print(f"    (si toglie «{tolto}» dalla riga, come se fosse stato aggiunto "
          f"al catalogo dopo)")
    prova("ne porta meno ⇒ NON riverificabile", meno, "non-si-sa")

    print("\n\n########## 3/5 — ⛔ la riga porta tutto, ma un file e' "
          "cambiato\n")
    cambiata = dict(oggi)
    quale = sorted(cambiata)[0]
    cambiata[quale] = "0" * 64
    prova("un file cambiato ⇒ SCADUTA", cambiata, "cambiate")

    print("\n\n########## 4/5 — ⛔ la riga non porta NESSUNA impronta\n")
    prova("nessuna impronta ⇒ NON riverificabile", {}, "non-si-sa")

    # ── ⭐⭐ 5. IL CONTROLLO POSITIVO DEL MECCANISMO ────────────────────────
    print("\n\n########## 5/5 — ⭐⭐ il controllo positivo del MECCANISMO: un "
          "file in piu'")
    print("           nel catalogo deve far diventare NON RIVERIFICABILE un "
          "banco verde\n")
    esito5 = False
    try:
        grezze = leggi_registro(REGISTRO)
    except (OSError, ValueError) as e:
        print(f"    {ROSSO}⛔ il registro vero non si legge ({e}): il "
              f"controllo positivo NON e' stato eseguito{GRIGIO}")
        grezze = None
    if grezze:
        ordinate = sorted([_normalizza(r) for r in grezze
                           if not _e_unione(r)], key=lambda r: r["quando"])
        # ⛔ Serve un banco che OGGI sia verde.  Se non ce n'e' nemmeno uno il
        #    controllo non si puo' fare, e «non l'ho potuto fare» non e' «e'
        #    andato bene»: si esce rossi, non verdi.
        verdi = [s for s in sorted(GUASTI)
                 if verdetto_di_oggi(s, ordinate)[2] == "uguali"]
        print(f"    banchi che oggi valgono, sul registro vero: "
              f"{', '.join(verdi) or '⛔ NESSUNO'}")
        if not verdi:
            print(f"    {ROSSO}⛔ nessun banco verde da cui partire: il "
                  f"controllo positivo NON si puo' eseguire, e questo non "
                  f"e' un verde{GRIGIO}")
        else:
            vittima = verdi[0]
            finto = os.path.join(tempfile.mkdtemp(), "b12-controllo-positivo.txt")
            with open(finto, "w", encoding="utf-8") as f:
                f.write("⭐ file vero, leggibile, e con un contenuto: e' il "
                        "CONTEGGIO che deve mordere, non l'illeggibilita'.\n")
            prima_lista = list(GUASTI[vittima]["file_che_contano"])
            # passo 1 — verde
            v1 = verdetto_di_oggi(vittima, ordinate)[2]
            # passo 2 — col file in piu' nel catalogo
            GUASTI[vittima]["file_che_contano"] = prima_lista + [finto]
            letto = impronte_di(vittima).get(finto)
            v2 = verdetto_di_oggi(vittima, ordinate)[2]
            # passo 3 — tolto, ci deve tornare
            GUASTI[vittima]["file_che_contano"] = prima_lista
            v3 = verdetto_di_oggi(vittima, ordinate)[2]
            shutil.rmtree(os.path.dirname(finto), ignore_errors=True)
            print(f"    la vittima: {vittima} — {len(prima_lista)} file nel "
                  f"catalogo, {len(prima_lista) + 1} col finto")
            print(f"    ⚠ e il file finto E' STATO LETTO: impronta "
                  f"{(letto or '⛔ None — il caso sarebbe quello sbagliato')[:32]}…")
            print(f"    sano «{v1}» → col file in piu' «{v2}» → "
                  f"risanato «{v3}»  (atteso: uguali → non-si-sa → uguali)")
            esito5 = (v1 == "uguali" and v2 == "non-si-sa" and v3 == "uguali"
                      and letto is not None)
            if not esito5 and v2 == "uguali":
                print(f"    {ROSSO}⛔⛔ IL BUCO E' ANCORA QUI: un file "
                      f"aggiunto al catalogo non invalida niente, e una riga")
                print(f"       certificata ieri resta verde su un elenco che "
                      f"oggi e' piu' lungo.{GRIGIO}")
    esiti.append(("⭐⭐ il controllo positivo del meccanismo", esito5))

    print("\n\n    == il verdetto")
    for nome, ok in esiti:
        print(f"    {(VERDE + 'OK ') if ok else (ROSSO + 'NO ')}{GRIGIO} {nome}")
    passati = sum(1 for _, ok in esiti if ok)
    print(f"\n    {VERDE if passati == len(esiti) else ROSSO}"
          f"{passati} casi su {len(esiti)}{GRIGIO}")
    return 0 if passati == len(esiti) else 1


def stato_unione(grezze):
    """⛔ LA GUARDIA — quel che chiude **I7**, e gira SENZA rete.

    Dice se l'unione e' fresca guardando la marca piu' recente e ricalcolando
    l'impronta dei giri di oggi.  ⚠ Quel che NON puo' dire — e infatti non lo
    dice — e' se l'ALTRA copia abbia scritto qualcosa nel frattempo: da qui non
    si vede, e «non lo so» non si arrotonda a «e' a posto».
    """
    marche = sorted((r for r in grezze if _e_unione(r)),
                    key=lambda r: r.get("quando", ""))
    giri_oggi = impronta_dei_giri(grezze)
    if not marche:
        return {"fresca": False, "marca": None, "nuove": None,
                "perche": "l'unione non e' MAI stata fatta da questo programma"}
    ultima = marche[-1]
    if ultima.get("impronta_giri") == giri_oggi:
        return {"fresca": True, "marca": ultima, "nuove": 0,
                "perche": "da allora qui non e' stato scritto nessun giro"}
    # ⛔ Quanti giri sono arrivati dopo — e si contano per IDENTITA', non per
    #    data: le due macchine hanno due orologi, e un giro scritto dopo
    #    l'unione puo' benissimo portare una data anteriore.  (Il primo giro di
    #    questa guardia lo contava per data e diceva «0 giri nuovi» su una
    #    copia che ne aveva uno: il caso costruito l'ha fatto cadere.)
    uniti = set(ultima.get("giri_uniti") or [])
    if not uniti:
        # ⚠ Marca vecchia, senza l'elenco: non si sa QUANTI, e non si tira a
        #   indovinare.  «Non lo so» non si arrotonda a un numero.
        return {"fresca": False, "marca": ultima, "nuove": None,
                "perche": "da allora questa copia e' cambiata, e di quanti "
                          "giri non si puo' dire (la marca non porta l'elenco)"}
    nuove = [r for r in grezze if not _e_unione(r)
             and f"{r.get('macchina','?')}|{r.get('quando','?')}" not in uniti]
    return {"fresca": False, "marca": ultima, "nuove": len(nuove),
            "perche": f"da allora questa copia ha {len(nuove)} giri nuovi che "
                      f"l'altra copia non ha"}


def stampa_stato_unione(st):
    m = st["marca"]
    if st["fresca"]:
        print(f"  {VERDE}⭐ UNIONE FRESCA{GRIGIO} — unito il {m['quando']} su "
              f"«{m['macchina']}» con")
        print(f"     {m['con']}: {st['perche']}.")
    elif m is None:
        print(f"  {ROSSO}⛔ L'UNIONE NON E' MAI STATA FATTA{GRIGIO} da "
              f"`--unisci`: il registro vive in DUE copie,")
        print("     una per macchina, e questa e' una sola delle due.")
    else:
        print(f"  {ROSSO}⛔ UNIONE VECCHIA{GRIGIO} — l'ultima e' del "
              f"{m['quando']} su «{m['macchina']}», e {st['perche']}.")
    print("  ⚠ E di quel che l'ALTRA copia ha scritto dall'unione in poi, da "
          "qui non si sa")
    print("    niente: nessuna delle due macchine vede il file dell'altra.  "
          "⇒ Il conto qui")
    print("    sotto e' **il conto di QUESTA copia**.")
    if not st["fresca"]:
        print(f"  ⇒ Si rimette a posto con:  {ROSSO}python3 "
              f"01-b12-guasti.py --unisci-col-server --rispecchia{GRIGIO}")
        print("    (da CHUWI; da NIC-OS `--unisci <percorso della copia "
              "portata a mano>`)")
    print()


# ===========================================================================
# ⛔ CHE COSA SI SA OGGI DI UN BANCO, IN UNA FUNZIONE SOLA — e sta fuori da
#    `mostra_registro()` apposta.
#
# ⭐ Perche' il banco di questo meccanismo (`--prova-impronte`) deve poter
#    interrogare **la stessa strada** che produce il conto, e non una sua
#    ricostruzione: un controllo positivo che gira su una copia del giudizio
#    certifica la copia.  E' la trappola n.1 di questo file — il verde per la
#    ragione sbagliata — applicata al banco del banco.
#
# Torna `(riga, stato, verdetto, perche)`:
#   stato   None = nessun giro lo nomina · «certificato» · «non certificato» ·
#           «non lanciabile da li'»
#   verdetto  ha senso solo se stato == «certificato»: «uguali» · «cambiate» ·
#             «non-si-sa» (vedi `confronta_impronte`)
# ===========================================================================
def verdetto_di_oggi(sigla, ordinate):
    ultimo = None
    for r in ordinate:
        if sigla in r["certificati"]:
            ultimo = (r, "certificato")
        elif sigla in r["non_certificati"]:
            ultimo = (r, "non certificato")
        elif sigla in r["saltati"]:
            ultimo = (r, "non lanciabile da li'")
    if ultimo is None:
        return None, None, None, None
    r, stato = ultimo
    if stato != "certificato":
        return r, stato, None, None
    verdetto, perche = confronta_impronte(r["impronte"].get(sigla),
                                          impronte_di(sigla))
    return r, stato, verdetto, perche


def punti_ciechi():
    """⛔⛔ QUALI FILE DEL PRODOTTO NON HA SOTTO GLI OCCHI NESSUNO.

    ⭐ Nasce il 13 agosto 2026 sera, e non per curare il punto cieco del
    codificatore — quello si cura a mano, in due righe.  Nasce perche' **quel
    punto cieco e' stato trovato per caso**, rileggendo il piano: nessuno
    strumento sapeva dirlo, e il conto diceva «tutto verde» mentre un file da
    53 000 byte non era guardato da nessuno.

    ⚠ E la domanda giusta non e' «chi lo nomina», e' **«chi lo nomina in una
    certificazione che REGGE OGGI»**: un file guardato solo da banchi mai
    provati e' guardato **sulla carta**.  ⇒ Tre livelli, non due:

        NESSUNO      il file non compare in nessuna lista        ⛔ cieco
        SULLA CARTA  compare, ma solo in banchi non certificati  ⛔ cieco
        COPERTO      compare in almeno un banco certificato oggi ⭐

    Il codice d'uscita e' **1 se c'e' almeno un cieco**: cosi' la domanda si
    puo' mettere in un giro automatico invece di doversela ricordare."""
    sorgente = os.path.join(QUI, "..", "src")
    if not os.path.isdir(sorgente):
        print(f"    {GIALLO}[?]{GRIGIO} `../src` non c'e' da qui: questa "
              f"domanda si fa dalla macchina che ha il prodotto")
        return 3

    # ⚠ Chi e' certificato OGGI si legge dal registro, non si ricorda.
    certificati = set()
    if os.path.exists(REGISTRO):
        try:
            # ⛔ Le stesse due cure di `mostra_registro`, e non per simmetria:
            #    le righe d'unione non sono giri, e l'ordine di scrittura NON
            #    e' l'ordine del tempo (due macchine scrivono lo stesso file).
            grezze = [_normalizza(r) for r in leggi_registro(REGISTRO)
                      if not _e_unione(r)]
            ordinate = sorted(grezze, key=lambda r: r["quando"])
            for sigla in FILE_CHE_CONTANO:
                _, stato, verdetto, _ = verdetto_di_oggi(sigla, ordinate)
                # ⚠ «uguali» e' il verdetto che vale oggi — non «vale».
                #   Il nome sbagliato dava ZERO coperti su tutto: un allarme
                #   totale, che e' il modo piu' rapido di non essere letto.
                if stato == "certificato" and verdetto == "uguali":
                    certificati.add(sigla)
        except (OSError, ValueError) as e:
            print(f"    {ROSSO}⛔ il registro non si legge: {e}{GRIGIO}")
            return 2

    # ⛔ Il nome di catalogo e' `remotix/x.c`, il file sta in `../src/x.c`:
    #    si passa per ALTRI_POSTI, che e' gia' il posto dove questa
    #    corrispondenza e' dichiarata una volta sola.
    guardato_da = {}
    for sigla, lista in FILE_CHE_CONTANO.items():
        for nome in lista:
            p = dove_sta(nome)
            if p:
                guardato_da.setdefault(os.path.realpath(p), []).append(sigla)

    # ⛔ IL GEMELLO, e senza questa riga il conto grida al lupo.
    #    `src/rcp.c` e `banchi/rcp/rcp.c` sono gemelli: il `Makefile` pretende
    #    che siano identici e **nessuno compila** se divergono (e' gia' costato
    #    il blocco di due gruppi).  ⇒ Chi guarda l'uno guarda l'altro.
    #    ⚠ Ma la copertura e' **condizionata**: vale finche' regge il controllo
    #    d'identita' del Makefile, e questo si DICE invece di darlo per fatto.
    GEMELLI = {"rcp.c": "rcp/rcp.c", "rcp.h": "rcp/rcp.h",
               "autenticazione.c": "rcp/autenticazione.c"}

    ciechi, carta, coperti, gemellati = [], [], [], []
    for f in sorted(os.listdir(sorgente)):
        if not f.endswith((".c", ".h", ".html")) and f != "Makefile":
            continue
        vero = os.path.realpath(os.path.join(sorgente, f))
        chi = guardato_da.get(vero, [])
        if not chi and f in GEMELLI:
            g = dove_sta(GEMELLI[f])
            chi_g = guardato_da.get(os.path.realpath(g), []) if g else []
            vivi = [s for s in chi_g if s in certificati]
            if vivi:
                gemellati.append((f, GEMELLI[f], vivi))
                continue
        if not chi:
            ciechi.append((f, []))
        elif not [s for s in chi if s in certificati]:
            carta.append((f, chi))
        else:
            coperti.append((f, [s for s in chi if s in certificati]))

    print(f"\n    == I PUNTI CIECHI DEL PRODOTTO — {len(coperti)} coperti, "
          f"{len(gemellati)} per gemellaggio, {len(carta)} sulla carta, "
          f"{len(ciechi)} ciechi\n")
    for f, chi in ciechi:
        print(f"    {ROSSO}⛔ CIECO      {GRIGIO}{f:22s} "
              f"nessuna voce del catalogo lo nomina")
    for f, chi in carta:
        print(f"    {ROSSO}⛔ SULLA CARTA{GRIGIO} {f:22s} "
              f"lo nomina {', '.join(sorted(chi))} — ma nessuno di quelli "
              f"e' certificato oggi")
    for f, g, chi in sorted(gemellati):
        print(f"    {GIALLO}⚠ gemello    {GRIGIO} {f:22s} "
              f"coperto via «{g}» da {', '.join(sorted(chi))} — ⛔ finche' "
              f"regge il controllo d'identita' del Makefile")
    for f, chi in sorted(coperti):
        print(f"    {VERDE}⭐ coperto   {GRIGIO} {f:22s} "
              f"{', '.join(sorted(chi))}")
    print()
    if ciechi or carta:
        # ⛔ E QUESTA FRASE E' STATA RISTRETTA APPOSTA.  La prima versione
        #    diceva «si possono riscrivere da capo a fondo senza che il conto
        #    cambi di una riga»: vero per la SCADENZA, falso come suona.  Un
        #    banco che gira contro un prodotto rotto diventa rosso lo stesso —
        #    quel che NON succede e' che la certificazione si dichiari
        #    invecchiata.  ⇒ Il difetto e' che una riga verde continua a dire
        #    «certificato» quando non descrive piu' il prodotto che gira.
        print(f"    {ROSSO}⛔ {len(ciechi) + len(carta)} file del prodotto "
              f"possono cambiare senza che NESSUNA certificazione scada"
              f"{GRIGIO}")
        print(f"       ⇒ non vuol dire che un guasto passerebbe inosservato: "
              f"vuol dire che una riga verde\n"
              f"         continuerebbe a dire «certificato» su un prodotto "
              f"che nel frattempo e' un altro.\n")
        return 1
    print(f"    {VERDE}⭐ ogni file del prodotto e' sotto gli occhi di almeno "
          f"una certificazione che regge oggi{GRIGIO}\n")
    return 0


def mostra_registro():
    if not os.path.exists(REGISTRO):
        print(f"    {GIALLO}[?]{GRIGIO} nessun registro in {REGISTRO}: "
              f"⛔ nessun banco di questa fase e' mai stato certificato")
        return 3
    try:
        grezze = leggi_registro(REGISTRO)
    except (OSError, ValueError) as e:
        print(f"    {ROSSO}⛔ il registro non si legge: {e}{GRIGIO}")
        return 2
    if not grezze:
        print(f"    {GIALLO}[?]{GRIGIO} il registro e' vuoto: ⛔ nessun banco "
              f"e' mai stato certificato")
        return 3

    # ── ⛔ LA GUARDIA DELL'UNIONE, PRIMA DEL CONTO — D10, invariante I7 ─────
    #    Si stampa in TESTA e non in coda: chi legge un numero deve sapere di
    #    quale meta' del registro sia il numero, prima di leggerlo.
    st = stato_unione(grezze)
    stampa_stato_unione(st)

    # ── ⛔ E I CONFLITTI SI NOMINANO, NON SI RISOLVONO IN SILENZIO ──────────
    #    Fino al 12 agosto 2026 due righe con la stessa identita' e contenuto
    #    diverso venivano risolte dall'ORDINE nel file, senza una parola: la
    #    stessa coppia dava «certificato» o «non certificato» a seconda di
    #    quale capitava piu' in basso.  `[M]` misurato costruendo il caso.
    conflitti = trova_conflitti(grezze, [])
    if conflitti:
        print(f"  {ROSSO}⛔ {len(conflitti)} CONFLITTI NEL REGISTRO{GRIGIO}: "
              f"righe che dichiarano lo STESSO giro")
        print("     con contenuto diverso.  ⛔ Una delle due mente, e il conto "
              "qui sotto ne")
        print("     sceglierebbe una a caso — quindi NON si conta finche' non "
              "sono risolti.")
        for (tipo, macchina, quando), testi in conflitti:
            print(f"     · «{macchina}» {quando} ({tipo}): {len(testi)} "
                  f"contenuti diversi")
            for campo, _ in _spiega_conflitto(testi):
                print(f"         discordi sul campo «{campo}»")
        print("     ⇒ Si guarda quale e' vera (`--impronte <SIGLA>`), si toglie "
              "l'altra a")
        print("       ragion veduta, e si rilegge.")
        return 2

    # ⚠ La marca d'unione e' una riga di servizio, non un giro: fuori dal conto.
    righe = [_normalizza(r) for r in grezze if not _e_unione(r)]

    # ⛔ E L'ORDINE DI SCRITTURA NON E' L'ORDINE DEL TEMPO.  Nel file del
    #    10 agosto 2026 la riga delle 21:19 sta **sotto** quella delle 23:01,
    #    perche' le due macchine scrivono nello stesso file in momenti diversi.
    #    Chi legge «l'ultima riga» legge la piu' vecchia e non se ne accorge.
    ordinate = sorted(righe, key=lambda r: r["quando"])
    if [r["quando"] for r in ordinate] != [r["quando"] for r in righe]:
        print(f"    {GIALLO}⚠ ATTENZIONE{GRIGIO}: nel file l'ordine di "
              f"scrittura NON e' l'ordine del tempo —")
        print("      la riga in fondo non e' la piu' recente.  Qui sotto sono "
              "ordinate per data.")
        macchine = sorted({r["macchina"] for r in righe})
        if len(macchine) > 1:
            print(f"      ⛔ E LE DATE VENGONO DA {len(macchine)} OROLOGI "
                  f"DIVERSI ({', '.join(macchine)}): l'11 agosto 2026 la")
            print("        macchina di prova era indietro di circa due ore "
                  "sulla macchina dei")
            print("        documenti.  ⚠ Quindi nemmeno l'ordine per data e' "
                  "l'ordine del tempo vero,")
            print("        e due righe di macchine diverse non si possono "
                  "mettere in fila fra loro.")
            print("        Il campo «macchina» e' li' per questo: si legge "
                  "PRIMA della data.")
        print()

    print("== I giri, dal piu' vecchio al piu' recente")
    for r in ordinate:
        print(f"  {r['quando']}  su «{r['macchina']}»  "
              f"rcp.c {r['impronta_rcp_c'][:16]}…")
        # ⛔ D6: la scena sta accanto alla data, non in fondo.  Due righe con
        #    gli stessi nomi e due scene diverse dicono due cose diverse.
        print(f"      scena interrogata      : {r['scena']}")
        print(f"      certificati            : "
              f"{', '.join(r['certificati']) or '—'}")
        print(f"      NON certificati        : "
              f"{', '.join(r['non_certificati']) or '—'}")
        if r["saltati"]:
            print(f"      non lanciabili da li'  : {', '.join(r['saltati'])}")
        print(f"      non provati IN QUEL GIRO: "
              f"{', '.join(r['non_provati']) or '—'}")
        if r["vecchio_nome"]:
            print(f"      {GIALLO}⚠ riga scritta col vecchio campo "
                  f"«mai_provati»{GRIGIO}: la parola era falsa — quei banchi")
            print("        possono essere stati provati in un altro giro, e "
                  "sotto si vede.")

    # ── ⛔ CHE COSA SI SA OGGI DI OGNI BANCO ────────────────────────────────
    print()
    print("== ⛔ Che cosa si sa OGGI di ciascun banco")
    print("   (dall'ultima riga che ne dice qualcosa — non dall'ultima riga "
          "del file)")
    print()
    # ⛔ E «SCADUTA» E «NON VERIFICABILE» SONO DUE COSE DIVERSE, come «provato e
    #    non riuscito» e «mai provato»: la prima dice che i file sono cambiati,
    #    la seconda che la riga non porta nessuna impronta e quindi non si puo'
    #    nemmeno dire se siano cambiati.  Fonderle sarebbe rifare, in piccolo,
    #    l'arrotondamento del rilievo R12-A.4.
    certi_oggi, scaduti, ciechi, non_certi, mai = [], [], [], [], []
    for sigla in sorted(GUASTI):
        r, stato, verdetto, perche = verdetto_di_oggi(sigla, ordinate)
        if stato is None:
            # ⭐ E SOLO QUI la parola «mai» e' vera.
            mai.append(sigla)
            print(f"  {GIALLO}[?]{GRIGIO} {sigla:4s} MAI PROVATO — nessun giro "
                  f"del registro lo nomina")
            continue
        if stato != "certificato":
            non_certi.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} {stato.upper()} il "
                  f"{r['quando']} (su «{r['macchina']}»)")
            continue
        if verdetto == "uguali":
            certi_oggi.append(sigla)
            print(f"  {VERDE}OK {GRIGIO} {sigla:4s} CERTIFICATO il "
                  f"{r['quando']} su «{r['macchina']}» — e vale oggi "
                  f"({perche})")
            # ⛔ D6: e CONTRO CHE COSA.  Un «vale oggi» senza la scena dice su
            #    quali byte la riga poggia e tace su quale server li eseguiva.
            print(f"        scena: {r['scena']}")
        elif verdetto == "cambiate":
            scaduti.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} certificato il "
                  f"{r['quando']} su «{r['macchina']}», ⛔ MA NON OGGI")
            print(f"        {perche}")
            print("        ⛔ Un banco certificato su file che nel frattempo "
                  "sono cambiati non e'")
            print("           certificato: la riga vale per quei byte, non per "
                  "questi.")
        else:
            ciechi.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} certificato il "
                  f"{r['quando']} su «{r['macchina']}», ⛔ MA NON SI PUO' DIRE "
                  f"SE VALGA OGGI")
            print(f"        {perche}")
            print("        ⚠ E «non si sa» non si arrotonda a «certificato»: "
                  "una certificazione")
            print("          che non si puo' riverificare non e' una "
                  "certificazione (LEZIONI.md §1.9).")
            print("        ⛔ E se la ragione e' che la riga porta MENO "
                  "impronte di quante il catalogo")
            print("           ne conta oggi, il giro va RIFATTO: nessuno ha "
                  "mai guardato quei file.")

    # ── ⛔ IL CONTO, E IL SUO DENOMINATORE ──────────────────────────────────
    print()
    print("    == il conto onesto")
    print(f"    --  banchi nel catalogo:                     {len(GUASTI)}")
    print(f"    {VERDE}{len(certi_oggi):3d}{GRIGIO}  CERTIFICATI OGGI: "
          f"{', '.join(certi_oggi) or '—'}")
    print(f"    {ROSSO}{len(scaduti):3d}{GRIGIO}  certificazione SCADUTA "
          f"(i file sono cambiati): {', '.join(scaduti) or '—'}")
    # ⛔ E L'ETICHETTA DICEVA MENO DI QUEL CHE IL NUMERO CONTA — cura del
    #    12 agosto 2026 sera, insieme al ciclo di `confronta_impronte`.
    #    «la riga non porta impronte» nominava UNA sola delle tre ragioni, e
    #    proprio non quella che stava per arrivare: chi avesse letto un 5 in
    #    questa riga sarebbe andato a cercare cinque righe senza impronte, e
    #    le avrebbe trovate con QUATTRO impronte su sei.
    print(f"    {ROSSO}{len(ciechi):3d}{GRIGIO}  certificazione NON "
          f"RIVERIFICABILE (nessuna impronta, o MENO di quante il catalogo ne "
          f"conta oggi, o un file che non si legge da qui): "
          f"{', '.join(ciechi) or '—'}")
    print(f"    {ROSSO}{len(non_certi):3d}{GRIGIO}  provati e NON certificati: "
          f"{', '.join(non_certi) or '—'}")
    print(f"    {GIALLO}{len(mai):3d}{GRIGIO}  MAI PROVATI: "
          f"{', '.join(mai) or '—'}")
    print()
    # ⛔ E UN VERDETTO CHE NON DICE QUANTE COSE HA APPROVATO NON E' UN VERDETTO
    #    (`LEZIONI.md` §1.9 regola 6).  Zero certificati non e' un verde.
    if not certi_oggi:
        print(f"    {ROSSO}⛔ NESSUN banco e' certificato oggi: non e' un "
              f"verde, e non e' «tutto pulito»{GRIGIO}")
        return 3
    print(f"    {VERDE}⭐ {len(certi_oggi)} banchi su {len(GUASTI)} hanno una "
          f"certificazione che regge oggi{GRIGIO}")
    if scaduti or ciechi or non_certi or mai:
        print(f"    {ROSSO}⛔ e gli altri {len(GUASTI) - len(certi_oggi)} NON "
              f"sono «puliti»: sono NON CERTIFICATI{GRIGIO}")
        return 3
    # ⛔ E UN CONTO PIENO SU UNA COPIA NON UNITA NON E' UN VERDE — D10, I7.
    #    Qui e' il punto in cui il passo saltato **si vede**: senza questa
    #    riga, un registro a cui manca meta' della storia potrebbe uscire 0 —
    #    cioe' «tutto certificato» — proprio perche' le righe che dicono di no
    #    stanno nell'altra copia.  ⭐ Una riga che manca non protesta: protesta
    #    questa.
    if not st["fresca"]:
        print(f"    {ROSSO}⛔ ma l'unione delle due copie non e' fresca "
              f"({st['perche']}):{GRIGIO}")
        print("       questo NON e' il conto del progetto, e' il conto di "
              "questa copia.")
        print("       ⇒ `--unisci-col-server --rispecchia`, poi si rilegge.")
        return 3
    return 0


def mostra_impronte(sigla):
    """I file su cui la certificazione di un banco poggia, e la loro impronta."""
    g = GUASTI[sigla]
    print(f"== {sigla} — i file su cui la certificazione poggia")
    print(f"   guasto: {g['titolo']}\n")
    imp = impronte_di(sigla)
    if not imp:
        print(f"    {GIALLO}[?]{GRIGIO} nessun file dichiarato: la "
              f"certificazione di {sigla} non ha denominatore")
        return 3
    ciechi = 0
    for nome, sha in sorted(imp.items()):
        if sha is None:
            ciechi += 1
            print(f"    {GIALLO}[?]{GRIGIO} {nome:34s} ⛔ non si legge da qui "
                  f"— «non ho guardato» non e' «non e' cambiato»")
        else:
            # ⭐ E SI DICHIARA DA DOVE L'HA LETTO quando non e' il posto di
            #    catalogo: un'impronta letta altrove e' una misura buona, ma
            #    solo se chi legge la riga sa su che file e' stata fatta.
            posto = dove_sta(nome)
            atteso = os.path.join(QUI, nome)
            print(f"    --  {nome:34s} {sha[:32]}…")
            if posto and os.path.abspath(posto) != os.path.abspath(atteso):
                print(f"        ⚠ letto da «{os.path.relpath(posto, QUI)}» — su "
                      f"questa macchina il file di catalogo sta li'")
    print(f"\n    --  {len(imp)} file, {len(imp) - ciechi} letti, "
          f"{ciechi} non leggibili da questa macchina")
    return 0 if ciechi == 0 else 3


def elenco():
    print("== ⛔ B12 — un guasto costruito a mano PER OGNI BANCO")
    print(f"   {len(GUASTI)} guasti nel catalogo.\n")
    senza_marca = []
    for sigla in sorted(GUASTI):
        g = GUASTI[sigla]
        print(f"  {sigla:4s} [{g['costa']:15s}] {g['titolo']}")
        print(f"       dove:     {risolvi(g['dove'])}")
        if g["sostituisci_con"]:
            print(f"       con:      {risolvi(g['sostituisci_con'])}")
        print(f"       dimostra: {g['dimostra'][:400]}")
        if g["marca"]:
            print(f"       ⛔ marca che l'uscita rossa DEVE contenere, e che il "
                  f"giro SANO non deve dire: «{g['marca']}»")
        else:
            senza_marca.append(sigla)
            print("       ⛔ NESSUNA MARCA: questo guasto NON PUO' CERTIFICARE. "
                  "Il rosso non si")
            print("          attribuirebbe a lui, e `--giudica` lo rifiuta "
                  "invece di saltare il controllo.")
        print(f"       file su cui la certificazione poggia: "
              f"{', '.join(g['file_che_contano']) or '⛔ nessuno dichiarato'}")
        if g["nota"]:
            print(f"       {g['nota']}")
        print(f"       {g['riferimento']}")
        print()
    leggeri = [s for s, g in GUASTI.items()
               if g["costa"] in ("leggero", "copia-di-file")]
    print(f"  ⭐ I guasti che non vogliono una ricostruzione — "
          f"{', '.join(sorted(leggeri))} —")
    print("     sono quelli che si possono certificare in minuti.")
    # ⛔ E IL DENOMINATORE DEL CATALOGO, che e' la cosa che il catalogo taceva.
    print(f"\n  {ROSSO}⛔ {len(senza_marca)} guasti su {len(GUASTI)} non hanno "
          f"una marca{GRIGIO}: {', '.join(senza_marca) or '—'}")
    print("     Nessuno di questi puo' certificare il proprio banco, e finche' "
          "il campo e'")
    print("     vuoto il banco resta NON CERTIFICATO — non «pulito».")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B12 — un guasto costruito a mano per ogni banco")
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--verifica", metavar="SIGLA")
    p.add_argument("--applica", metavar="SIGLA")
    p.add_argument("--togli", metavar="SIGLA")
    p.add_argument("--giudica", metavar="ESITI")
    p.add_argument("--registro", action="store_true")
    p.add_argument("--punti-ciechi", action="store_true",
                   dest="punti_ciechi",
                   help="quali file del prodotto non sono guardati da nessuna "
                        "certificazione che regge oggi. Esce 1 se ce n'e' "
                        "almeno uno")
    # ⛔ Due domande che l'orchestratore deve poter fare senza rileggersi
    #    questo file da dentro una shell: chi le pone da fuori con `exec()` si
    #    costruisce una seconda verita' sul catalogo, e il giorno in cui le due
    #    divergono nessuno se ne accorge.
    p.add_argument("--marca", metavar="SIGLA",
                   help="la stringa che l'uscita del banco rosso DEVE contenere")
    p.add_argument("--costa", metavar="SIGLA",
                   help="leggero | ricostruisce | copia-di-file | gia-fatto")
    p.add_argument("--impronte", metavar="SIGLA",
                   help="i file su cui la certificazione di quel banco poggia")
    p.add_argument("--provabile", metavar="SIGLA",
                   help="i file su cui la certificazione poggia ci sono, su "
                        "questa macchina?  Stampa «MANCA <nome>» per ognuno "
                        "che non c'e' (R12-A.31)")
    p.add_argument("--certificati", default=CERT_PREDEFINITA,
                   help="la cartella dei certificati (per i guasti «{CERT}»)")
    # ⛔ D6 — LA SCENA SI DICHIARA, e chi la dichiara e' chi l'ha accesa.
    #    Non si deduce qui dentro: `--giudica` legge un file di esiti e non ha
    #    modo di sapere quale server li ha prodotti.  Chiederglielo sarebbe
    #    chiedere a un verbale di ricordarsi la stanza.
    p.add_argument("--scena", default=None,
                   help="contro CHE COSA il giro ha misurato (es. «innesto "
                        "bsslserver :7447» o «prodotto remotix :7526»).  ⛔ "
                        "Finisce nella riga di registro: senza, due righe con "
                        "gli stessi nomi e due scene diverse hanno lo stesso "
                        "aspetto (forma E8 applicata al registro)")
    # ⛔ D10 — L'UNIONE STA NEL PROGRAMMA, non in una procedura da ricordare.
    p.add_argument("--unisci", metavar="ALTRA",
                   help="unisce il registro di qui con la copia in ALTRA. "
                        "⛔ Non perde una riga, non ne inventa una, e davanti a "
                        "due righe dello stesso giro con contenuto diverso si "
                        "FERMA invece di sceglierne una")
    p.add_argument("--unisci-col-server", action="store_true",
                   help=f"va a prendere {SERVER_REGISTRO} con scp e unisce")
    p.add_argument("--rispecchia", action="store_true",
                   help="dopo l'unione rimanda la copia unita al server — e "
                        "solo se di la' non e' cambiato niente nel frattempo")
    p.add_argument("--prova-unione", action="store_true",
                   help="⛔ certifica l'unione su tre casi costruiti apposta: "
                        "due copie divergenti, due righe in conflitto, e il "
                        "controllo positivo")
    # ⛔ Il banco del meccanismo che fa SCADERE le certificazioni — il buco del
    #    12 agosto 2026, dove aggiungere un file che conta non invalidava
    #    niente.  ⭐ Compreso il controllo positivo del meccanismo stesso.
    p.add_argument("--prova-impronte", action="store_true",
                   help="⛔ certifica i TRE esiti (vale oggi · scaduta · non "
                        "riverificabile) su casi costruiti, e ⭐ verifica che "
                        "un file aggiunto al catalogo faccia davvero scadere "
                        "un banco verde")
    a = p.parse_args()
    CERT = a.certificati
    if a.prova_unione:
        sys.exit(prova_unione())
    if a.prova_impronte:
        sys.exit(prova_impronte())
    if a.unisci_col_server:
        sys.exit(unisci_col_server(a.rispecchia))
    if a.unisci:
        sys.exit(unisci(a.unisci))
    if a.impronte:
        if a.impronte not in GUASTI:
            print(f"⛔ sigla sconosciuta: {a.impronte}")
            sys.exit(2)
        sys.exit(mostra_impronte(a.impronte))
    if a.elenco:
        sys.exit(elenco())
    if a.registro:
        sys.exit(mostra_registro())
    if a.punti_ciechi:
        sys.exit(punti_ciechi())
    if a.giudica:
        sys.exit(giudica(a.giudica, a.scena))
    if a.provabile:
        sys.exit(provabile(a.provabile))
    for campo in ("marca", "costa"):
        sigla = getattr(a, campo)
        if sigla:
            if sigla not in GUASTI:
                print("")
                sys.exit(2)
            print(GUASTI[sigla][campo])
            sys.exit(0)
    for azione, f in (("verifica", verifica), ("applica", applica),
                      ("togli", togli)):
        sigla = getattr(a, azione)
        if sigla:
            if sigla not in GUASTI:
                print(f"⛔ sigla sconosciuta: {sigla}.  Le sigle: "
                      f"{', '.join(sorted(GUASTI))}")
                sys.exit(2)
            r = f(sigla)
            sys.exit(0 if (azione == "verifica" and r == 1) or
                     (azione != "verifica" and r == 0) else 1)
    p.print_help()
    sys.exit(2)
