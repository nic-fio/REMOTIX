#!/usr/bin/env python3
"""01-b13-proprieta.py — ⭐ B13: le sei cose che la fase produce e che nessun banco guardava.

    python3 01-b13-proprieta.py --indirizzo 192.168.0.2 --porta 7447 \
        --certificati /media/REMOTIX/b2-certificati --prodotti /srv/src \
        --utente prova --parola parola-di-prova
    python3 01-b13-proprieta.py --elenco        le sei previsioni, senza misurare
    python3 01-b13-proprieta.py --certifica     ⛔ i guasti costruiti a mano, e
                                                il rosso preteso NEL SUO PUNTO
                                                (gira su copie, non tocca niente)

⚠ Gira DENTRO il contenitore: aioquic e openssl stanno li', e i certificati e i
  registri anche.  Lo accende e lo lancia `01-b13-lancia.sh`.

===========================================================================
⛔ DA DOVE VIENE QUESTO BANCO

`fasi/01-filo-nudo.md` B13, rilievo **R3.24**: sei proprieta' che la fase 1
**produce** e che nessuno dei dodici banchi guardava.  Tre hanno un ⛔ scritto
in `RCP.md`.  ⭐ Non sono proprieta' difficili: sono proprieta' che nessuno
aveva **assegnato a un banco**, ed e' la forma di buco piu' comune di tutte.

  1  ⛔ che i due certificati siano DUE (§4.1-bis): impronte e scadenze diverse
  2  ⛔ che la parola d'ordine non sia in NESSUN registro prodotto dal giro
  3  chiave privata a 0600 · `subjectAltName` che combacia · ⛔ un certificato
     d'autorita' installato usato SENZA rigenerare il proprio (§4.1)
  4  la pagina servita in TCP: che si carichi, che pubblichi l'impronta
     CORRENTE, e che l'endpoint dell'impronta aggiornata ESISTA (§4.1-bis)
  5  il credito di almeno 16 stream unidirezionali concessi al client (§2.3)
  6  ⛔ che `stato` valga SEMPRE `NUOVA`

===========================================================================
⛔ IL PRIMO IMPUTATO E' IL BANCO — E QUI IL PERICOLO HA UN NOME

Cinque delle sei proprieta' si misurano **cercando qualcosa e non trovandolo**:
la parola d'ordine che non c'e', il ramo `RIPRESA` che non c'e', il certificato
che non e' stato rigenerato.  ⛔ **Un'assenza non e' una prova**
(`LEZIONI.md` §1.9): un `grep` puntato sulla cartella sbagliata, un file mai
aperto, un percorso che non esiste danno **la stessa faccia** di una proprieta'
rispettata, e danno verde.

⛔ Da cui la regola di questo file: **ogni ricerca che deve fallire ha prima un
   controllo positivo che deve riuscire**.  Si pianta la parola d'ordine in un
   file e si verifica che il `grep` la trovi; si cerca una stringa che nel
   codice c'e' di sicuro prima di dichiarare che `RIPRESA` non c'e'.  Se il
   controllo positivo non passa, la proprieta' **non si giudica**: si dichiara
   non misurata, che e' una terza cosa e ha il suo colore.

===========================================================================
⛔ E LA PROPRIETA' CHE NON SI PUO' MISURARE VA DETTA, NON SALTATA

Tre pezzi di B13 non hanno un imputato, perche' **il codice che dovrebbero
misurare non esiste**:

  · §4.1 dice *«il server se lo genera all'installazione»* e *«se
    l'amministratore ne installa uno emesso da un'autorita', il server DEVE
    usarlo e non DEVE rigenerare il proprio»* — ⛔ oggi i certificati li fa
    `01-b2-certificati.sh`, che e' **un banco**, e il server li riceve sulla
    riga di comando.  Non c'e' nessun codice che generi, ruoti o scelga;
  · §4.1-bis dice che *«e' il server stesso a servire la pagina»* e che
    l'impronta aggiornata si ritira *«dal server che l'ha servita»* — ⛔ oggi
    la pagina la serve un raccoglitore del banco su `127.0.0.1:8899`, e
    l'impronta le arriva come **parametro d'URL** messo li' da uno script.

⛔ Queste NON si segnano come «passa» e NON si saltano: si segnano
   `[?] non misurabile — manca l'imputato`, con la prova che manca (il `grep`
   che non trova nessun generatore, la porta TCP che non ascolta).  ⭐ E' la
   differenza fra un buco dichiarato e un buco che nessuno vedra' piu'.

===========================================================================
⛔ LO STATO INIZIALE (B0.1) E IL CONTO DI §4.4-bis (B0.3)

  · il server dev'essere acceso e rispondere: la proprieta' 6 pretende una
    stretta di mano intera, e senza quella cinque righe su sei sarebbero
    «non ho potuto guardare» travestite da verde;
  · ⭐ **questo banco non fallisce nessuna autenticazione**: usa sempre le
    credenziali buone.  Quindi **non consuma il conto di §4.4-bis** e non
    lascia un ban addosso a chi viene dopo.  ⚠ Il comando di sblocco di
    §4.4-bis **esiste** (`01-b8-sblocca.py`, su `--comando-socket`) ma vuole un
    server acceso con quella opzione: B13 accende il proprio senza, e la sua
    cura e' **riaccenderlo**, che azzera il conto perche' vive nel processo.
    Se all'inizio arriva `TROPPI_TENTATIVI`, il ban e' di un altro banco e
    questo si ferma invece di misurare.
"""
import argparse
import asyncio
import datetime
import hashlib
import os
import re
import socket
import ssl
import struct
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# Gli esiti di una proprieta'.  ⛔ Sono QUATTRO e non due: «non ho potuto
#    guardare» e «non c'e' l'imputato» non sono ne' un passa ne' un non-passa,
#    e schiacciarli su uno dei due e' la forma E8.
PASSA, NON_PASSA, NON_MISURATO, SENZA_IMPUTATO = "OK", "NO", "??", "[?]"

COLORE = {PASSA: VERDE, NON_PASSA: ROSSO, NON_MISURATO: GIALLO,
          SENZA_IMPUTATO: GIALLO}


class Esito:
    """Una proprieta' misurata: un esito, un testo, e le righe di dettaglio."""

    def __init__(self, numero, titolo, dove):
        self.numero, self.titolo, self.dove = numero, titolo, dove
        self.esito = NON_MISURATO
        self.testo = "non misurato"
        self.righe = []
        # ⛔ Il denominatore DI QUESTA proprieta': quante cose ha guardato.
        #    Una proprieta' che ne ha guardate zero non passa: si dichiara.
        self.guardate = 0

    def di(self, esito, testo):
        self.esito, self.testo = esito, testo
        return self

    def riga(self, t):
        self.righe.append(t)
        return self

    def stampa(self):
        c = COLORE[self.esito]
        print(f"  {c}{self.esito:3s}{GRIGIO} B13.{self.numero}  {self.titolo}")
        print(f"        {self.dove}")
        print(f"        {self.testo}")
        for r in self.righe:
            print(f"          {r}")


# ===========================================================================
def corri(cmd, dentro=None):
    """Esegue e restituisce (uscita, testo).  ⛔ Non si guarda solo l'uscita:
    un comando che non c'e' e un comando che dice «no» sono due cose."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                           input=dentro)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"⛔ comando assente: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "⛔ scaduto"


def adesso_utc():
    """L'ora UTC senza fuso, per confrontarla con quel che esce da `openssl`.

    ⚠ `datetime.utcnow()` e' deprecata dalla 3.12 e stampa un avviso a ogni
      giro: un avviso dentro l'uscita di un banco e' rumore che insegna a non
      leggere l'uscita del banco.  Questa e' la stessa cosa, scritta come la
      chiede la libreria di oggi."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def corri_diviso(cmd):
    """Come `corri()`, ma STDOUT e STDERR restano separati: (uscita, out, err).

    ⛔ Rilievo A13, 11 agosto 2026.  `corri()` fonde i due flussi, e su un
       `grep` questo cancella la differenza fra *«non l'ho trovato»* e *«non ho
       potuto leggere»*: le righe «grep: …: Permission denied» finivano dentro
       `out` insieme ai nomi dei file trovati, e poi venivano scartate da
       `os.path.isfile()` — cioe' l'errore spariva **due volte**, e la
       proprieta' concludeva «la parola non compare in nessuno degli N file»
       avendone letti meno di N.
    ⚠ `grep` ha tre stati d'uscita, e sono tre cose: 0 trovato · 1 non trovato ·
      ≥2 **non ho potuto leggere qualcosa**.  Il terzo e' quello che questo file
      buttava.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except FileNotFoundError:
        return 127, "", f"⛔ comando assente: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "⛔ scaduto"


def impronta_der(pem):
    """SHA-256 del DER del certificato, cioe' l'impronta di §4.1-bis.

    ⛔ Non passa da `corri()`, e la ragione e' un difetto gia' pagato: `corri()`
       decodifica l'uscita come UTF-8, e il DER **non e' testo**.  Il primo giro
       del 10 agosto 2026 e' morto con `UnicodeDecodeError` sul secondo byte del
       certificato, e il banco si e' fermato prima di guardare qualunque cosa —
       cioe' ha dato un rosso che non parlava di nessuna delle sei proprieta'.
    """
    try:
        p = subprocess.run(["openssl", "x509", "-in", pem, "-outform", "der"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f"⛔ openssl non ha risposto: {e}"
    if p.returncode != 0:
        return None, ("⛔ openssl esce " + str(p.returncode) + ": "
                      + p.stderr.decode("utf-8", "replace").strip())
    if not p.stdout:
        # ⛔ Uscita zero e zero byte: «riuscito» e «vuoto» non sono la stessa
        #    cosa, e un'impronta di zero byte e' un valore perfettamente
        #    calcolabile — cioe' un numero falso che nessuno riconoscerebbe.
        return None, "⛔ openssl riesce e non stampa niente: DER vuoto"
    return hashlib.sha256(p.stdout).hexdigest(), None


def scadenza(pem):
    u, t = corri(["openssl", "x509", "-in", pem, "-noout", "-enddate"])
    if u != 0:
        return None, t
    m = re.search(r"notAfter=(.+)", t)
    if not m:
        return None, f"⛔ `notAfter` non si legge da «{t.strip()}»"
    try:
        q = datetime.datetime.strptime(m.group(1).strip(), "%b %d %H:%M:%S %Y %Z")
        return q, None
    except ValueError as e:
        return None, f"⛔ data illeggibile: {e}"


def san(pem):
    u, t = corri(["openssl", "x509", "-in", pem, "-noout", "-ext",
                  "subjectAltName"])
    if u != 0:
        return None, t
    m = re.search(r"(IP Address|DNS):([^\s,]+)", t)
    return (m.group(2) if m else None), (None if m else
                                         f"⛔ nessun subjectAltName in {pem}")


def algoritmo(pem):
    u, t = corri(["openssl", "x509", "-in", pem, "-noout", "-text"])
    if u != 0:
        return None
    m = re.search(r"Public Key Algorithm:\s*(\S+)", t)
    c = re.search(r"ASN1 OID:\s*(\S+)", t)
    return f"{m.group(1) if m else '?'}/{c.group(1) if c else '?'}"


# ===========================================================================
# 1 — ⛔ CHE I DUE CERTIFICATI SIANO DUE
# ===========================================================================
def proprieta_1(a):
    e = Esito(1, "che i DUE certificati siano due — impronte e scadenze diverse",
              "RCP.md §4.1-bis: «uno longevo per la pagina, uno a scadenza "
              "breve per la sessione»")
    pagina = os.path.join(a.certificati, "pagina.pem")
    sessione = os.path.join(a.certificati, "sessione.pem")
    dati = {}
    for nome, pem in (("pagina", pagina), ("sessione", sessione)):
        if not os.path.exists(pem):
            return e.di(NON_MISURATO,
                        f"⛔ {pem} non c'e': non e' «ce n'e' uno solo», e' che "
                        f"non si e' potuto guardare")
        imp, err = impronta_der(pem)
        sca, err2 = scadenza(pem)
        if imp is None or sca is None:
            return e.di(NON_MISURATO, f"⛔ {nome}: {err or err2}")
        dati[nome] = (imp, sca)
        e.guardate += 1
        giorni = (sca - adesso_utc()).days
        e.riga(f"{nome:9s} impronta {imp[:24]}…  scade fra {giorni:4d} giorni "
               f"({sca:%d/%m/%Y})  chiave {algoritmo(pem)}")

    imp_p, sca_p = dati["pagina"]
    imp_s, sca_s = dati["sessione"]
    guasti = []
    if imp_p == imp_s:
        guasti.append("⛔ LE IMPRONTE COMBACIANO: e' UN certificato in due file, "
                      "e l'avviso della pagina ricomparira' ogni due settimane")
    if sca_p == sca_s:
        guasti.append("⛔ le scadenze combaciano: quello della pagina ruota "
                      "insieme a quello della sessione")
    # §4.1-bis: il vincolo e' «meno di 14 giorni» per la sessione.
    resta = (sca_s - adesso_utc()).days
    e.guardate += 1
    if resta >= 14:
        guasti.append(f"⛔ il certificato della SESSIONE dura {resta} giorni: "
                      f"§4.1-bis vuole meno di 14")
    if (sca_p - sca_s).days < 14:
        guasti.append(f"⚠ il certificato della PAGINA non e' longevo: dura solo "
                      f"{(sca_p - sca_s).days} giorni piu' dell'altro")
    for g in guasti:
        e.riga(g)
    if guasti:
        return e.di(NON_PASSA, f"{len(guasti)} cose non tornano sui due "
                               f"certificati")
    return e.di(PASSA, "impronte diverse, scadenze diverse, la sessione sotto "
                       "i 14 giorni e la pagina molto piu' lunga")


# ===========================================================================
# 2 — ⛔ LA PAROLA D'ORDINE IN NESSUN REGISTRO
# ===========================================================================
def proprieta_2(a):
    e = Esito(2, "la parola d'ordine in NESSUN registro prodotto dal giro",
              "fasi/01-filo-nudo.md B13.2 · RCP.md §4.4: «non deve comparire in "
              "nessun registro a nessun livello»")
    if not os.path.isdir(a.prodotti):
        return e.di(NON_MISURATO, f"⛔ {a.prodotti} non e' una cartella: il "
                                  f"`grep` non avrebbe dove guardare")

    # ⛔ E PRIMA DI TUTTO: CONTRO CHI E' PUNTATO IL `grep`.
    #
    #    Il primo giro del 10 agosto 2026 ha stampato ROSSO con «la parola
    #    compare in 13 file» — e i tredici file erano **i banchi che la
    #    digitano**: `01-b6-lancia.sh`, `01-b7-congedo.py`, `01-b11-pagina.html`.
    #    ⛔ E' la settima veste del difetto: **il rosso puntato sull'imputato
    #    sbagliato**.  §4.4 vieta la parola nei **registri** — «a nessun
    #    livello, nemmeno in `traccia`» — non nel programma che la deve digitare
    #    per collegarsi.  Un banco che li confonde e' rosso per sempre, e chi
    #    legge impara a non guardarlo.
    #
    # ⭐ Da cui DUE conti, e due colori:
    #      · i REGISTRI e le REGISTRAZIONI (quel che il giro **produce**): se la
    #        parola e' li', e' il difetto di §4.4 — ed e' rosso;
    #      · i SORGENTI dei banchi (quel che il giro **usa**): la parola di
    #        prova ci sta per forza.  Si contano e si dichiarano, e non sono un
    #        rosso — ⚠ ma sarebbero un rosso il giorno in cui uno di quei file
    #        contenesse la parola di un utente vero.
    PRODOTTI = (".log", ".rcpreg", ".jsonl", ".json", ".txt", ".stato", ".pid",
                ".esito", ".attaccato")
    def e_prodotto(nome):
        return nome.endswith(PRODOTTI)

    # ⛔ IL CONTROLLO POSITIVO, PRIMA: uno strumento che non ha mai trovato
    #    niente non e' pulito, e' non certificato (`LEZIONI.md` §1.9).
    #    ⚠ E l'esca ha l'estensione dei PRODOTTI, o certificherebbe un `grep`
    #      puntato sull'insieme sbagliato.
    esca = os.path.join(a.prodotti, "b13-esca-da-cancellare.log")
    trovata_esca = False
    try:
        with open(esca, "w", encoding="utf-8") as f:
            f.write(f"riga di prova con dentro {a.parola} e basta\n")
        u, t, _err = corri_diviso(["grep", "-rl", "--binary-files=text",
                                   a.parola, a.prodotti])
        # ⚠ E il controllo positivo risponde a UNA domanda sola — «questo
        #   strumento sa trovare la parola quando c'e'?» — e non all'altra —
        #   «ha potuto leggere tutto?».  Sono due cose, e A13 lo dice
        #   esattamente cosi': la seconda si guarda piu' sotto, con lo stato
        #   d'uscita del `grep` e i file illeggibili contati a parte.
        trovata_esca = os.path.basename(esca) in t
        esca_uscita = u
    finally:
        # ⛔ L'esca si toglie SEMPRE, anche se il grep e' fallito: un file con
        #    dentro la parola d'ordine e' esattamente quel che questa proprieta'
        #    esiste per impedire.
        try:
            os.remove(esca)
        except OSError:
            pass
    e.guardate += 1
    if not trovata_esca:
        return e.di(NON_MISURATO,
                    "⛔ il controllo positivo NON passa: il `grep` non ha "
                    "trovato la parola nemmeno nel file in cui l'ho piantata. "
                    "Ogni «non l'ho trovata» che seguisse sarebbe muto")
    e.riga(f"⭐ controllo positivo: il `grep` trova la parola piantata apposta "
           f"(uscita {esca_uscita}) — ⚠ e questo dice che SA TROVARE, non che "
           f"abbia potuto leggere tutto: la seconda domanda e' due righe piu' "
           f"sotto")

    # E ora la ricerca vera, su TUTTI i file — e poi divisa in due.
    u, t, err = corri_diviso(["grep", "-rl", "--binary-files=text",
                              a.parola, a.prodotti])
    tutti = [r for r in t.splitlines() if r.strip() and os.path.isfile(r)]
    colpiti = [r for r in tutti if e_prodotto(os.path.basename(r))]
    sorgenti = [r for r in tutti if not e_prodotto(os.path.basename(r))]

    # ⛔ IL DENOMINATORE SI CONTA SU QUEL CHE SI E' POTUTO LEGGERE — A13.
    #    `quanti_file` contava con `os.walk` **anche i file che il `grep` non ha
    #    potuto aprire**, e li presentava come guardati: un denominatore falso
    #    e' peggio di nessun denominatore, perche' da' alla misura l'aria di
    #    essere gia' stata controllata (`LEZIONI.md` §1.9 corollario 5).
    quanti_file = 0
    quanti_prodotti = 0
    negati = []
    negati_prodotti = []
    for radice, _, files in os.walk(a.prodotti):
        for f in files:
            p = os.path.join(radice, f)
            quanti_file += 1
            prodotto = e_prodotto(f)
            if prodotto:
                quanti_prodotti += 1
            if not os.access(p, os.R_OK):
                negati.append(p)
                if prodotto:
                    negati_prodotti.append(p)
    righe_err = [r for r in err.splitlines() if r.strip()]
    e.guardate += quanti_file - len(negati)
    e.riga(f"denominatore: {quanti_file} file sotto {a.prodotti}, di cui "
           f"{quanti_prodotti} sono REGISTRI o REGISTRAZIONI "
           f"({', '.join(PRODOTTI)})")
    e.riga(f"`grep` esce {u} "
           f"({'trovato' if u == 0 else 'non trovato' if u == 1 else '⛔ NON HA POTUTO LEGGERE QUALCOSA'})"
           f" · righe su stderr: {len(righe_err)} · file illeggibili da qui: "
           f"{len(negati)} (di cui registri: {len(negati_prodotti)})")
    for r in righe_err[:4]:
        e.riga(f"⚠ stderr del grep: {r}")
    if u >= 2 or negati_prodotti:
        # ⛔ «Non l'ho trovata» dentro un insieme che non si e' potuto leggere
        #    tutto non e' «non c'e'»: e' la faccia comune di vuoto e proibito.
        return e.di(NON_MISURATO,
                    f"⛔ la ricerca NON ha coperto tutto: `grep` esce {u} e "
                    f"{len(negati_prodotti)} registri su {quanti_prodotti} non "
                    f"sono leggibili da qui.  «La parola non compare» varrebbe "
                    f"solo per i file che ho potuto aprire, e questa proprieta' "
                    f"parla di tutti")
    e.riga(f"⚠ e {len(sorgenti)} sorgenti di banco la contengono, come devono: "
           + (", ".join(os.path.basename(x) for x in sorgenti[:8]) or "—"))
    e.riga("  ⛔ quelli NON sono un rosso: §4.4 vieta la parola nei registri, "
           "non nel programma che la digita")

    # ⭐ E la meta' che nessuno guarda: nelle registrazioni di §11.1 la parola
    #    dev'essere OSCURATA con `0x2A`, e l'impronta dev'essere quella VERA.
    #    Se l'impronta fosse di un'altra stringa, l'oscuramento sarebbe una
    #    finzione e nessuno se ne accorgerebbe.
    vera = hashlib.sha256(a.parola.encode()).digest()
    tracce, oscurate, con_impronta = 0, 0, 0
    for radice, _, files in os.walk(a.prodotti):
        for f in files:
            if not f.endswith(".rcpreg"):
                continue
            tracce += 1
            try:
                with open(os.path.join(radice, f), "rb") as fh:
                    d = fh.read()
            except OSError:
                continue
            if b"\x2A" * 8 in d:
                oscurate += 1
            if vera in d:
                con_impronta += 1
    e.guardate += tracce
    e.riga(f"registrazioni §11.1: {tracce} · con byte 0x2A ripetuti "
           f"{oscurate} · con l'impronta VERA della parola {con_impronta}")
    if tracce and con_impronta == 0:
        e.riga("⚠ nessuna traccia porta l'impronta della parola: o non c'era "
               "una stretta di mano autenticata, o l'oscuramento registra "
               "l'impronta di qualcos'altro — §11.1 la vuole «di quel che "
               "c'era»")

    if colpiti:
        for c in colpiti:
            e.riga(f"⛔ LA PAROLA E' DENTRO UN REGISTRO: {c}")
        return e.di(NON_PASSA, f"la parola d'ordine compare in "
                               f"{len(colpiti)} registri su {quanti_prodotti}")
    if quanti_prodotti == 0:
        return e.di(NON_MISURATO, "⛔ ZERO registri da guardare: non e' "
                                  "«pulito», e' un denominatore vuoto — il "
                                  "giro non ha prodotto niente da leggere")
    return e.di(PASSA, f"la parola non compare in nessuno dei "
                       f"{quanti_prodotti} registri e registrazioni, e il "
                       f"`grep` sa trovarla quando c'e'")


# ===========================================================================
# 3 — LA CHIAVE, IL NOME, E IL CERTIFICATO D'AUTORITA'
# ===========================================================================
def proprieta_3(a, impronta_sul_filo):
    e = Esito(3, "chiave 0600 · subjectAltName che combacia · il certificato "
                 "d'autorita' usato SENZA rigenerare il proprio",
              "RCP.md §4.1")
    guasti, aperti = [], []
    for nome in ("pagina", "sessione"):
        chiave = os.path.join(a.certificati, f"{nome}.key")
        pem = os.path.join(a.certificati, f"{nome}.pem")
        if not os.path.exists(chiave):
            return e.di(NON_MISURATO, f"⛔ {chiave} non c'e'")
        modo = oct(os.stat(chiave).st_mode & 0o777)
        e.guardate += 1
        if modo != "0o600":
            guasti.append(f"⛔ {nome}.key ha permessi {modo}, §4.1 vuole 0600")
        else:
            e.riga(f"{nome}.key  permessi {modo}")
        nomecert, err = san(pem)
        e.guardate += 1
        if nomecert is None:
            guasti.append(f"⛔ {nome}.pem: {err}")
        elif nomecert != a.indirizzo:
            guasti.append(f"⛔ {nome}.pem: subjectAltName «{nomecert}» non e' "
                          f"l'indirizzo su cui il server risponde "
                          f"({a.indirizzo})")
        else:
            e.riga(f"{nome}.pem  subjectAltName {nomecert} — combacia")

    # ⭐ La meta' misurabile della terza riga: il server usa il certificato che
    #    gli e' stato dato, e non ne ha fabbricato un altro.
    imp_file, _ = impronta_der(os.path.join(a.certificati, "sessione.pem"))
    e.guardate += 1
    if impronta_sul_filo is None:
        aperti.append("⚠ l'impronta presentata sul filo non si e' potuta "
                      "leggere: «usa il certificato che gli e' stato dato» "
                      "resta non misurato")
    elif imp_file != impronta_sul_filo:
        guasti.append(f"⛔ il certificato PRESENTATO sul filo non e' "
                      f"sessione.pem: {impronta_sul_filo[:24]}… contro "
                      f"{(imp_file or '?')[:24]}… — il server ne ha usato un "
                      f"altro")
    else:
        e.riga(f"⭐ il certificato presentato sul filo E' sessione.pem "
               f"({imp_file[:24]}…): il server non ne ha rigenerato uno suo")

    # ⛔ E LA META' CHE NON HA IMPUTATO.
    #    §4.1 mette due obblighi sul server — generarselo all'installazione, e
    #    usare quello d'autorita' senza rigenerare il proprio.  Prima di dire
    #    che li rispetta bisogna trovare il codice che li potrebbe violare.
    #
    # ⛔⭐ E QUI LA LOGICA ERA INVERTITA — rilievo A12, 11 agosto 2026.
    #
    #    Fino a stanotte: se NON si trovava nessun generatore, `aperti` cresceva
    #    e l'esito era `SENZA_IMPUTATO` (giallo, giusto); se **si trovava** un
    #    generatore si stampava soltanto «⚠ c'e' un imputato, e va guardato»,
    #    `aperti` restava vuoto, e — senza altri guasti — l'esito era **PASSA**,
    #    col testo «permessi, nome e certificato presentato: tutto al suo posto».
    #
    # ⛔ Cioe': **piu' prove c'erano che qualcuno genera certificati, piu' la
    #    proprieta' era verde.**  Un `grep` che trova un generatore non dice se
    #    quel generatore RISPETTI l'obbligo di §4.1 — «usare quello d'autorita'
    #    e non rigenerare il proprio»: dice che da oggi quell'obbligo ha un
    #    codice che lo puo' violare, cioe' che c'e' qualcosa da misurare e che
    #    questo banco non lo misura.
    #
    # ⚠ E il caso opposto, come vuole `LEZIONI.md` §1.11: se domani il server
    #   imparasse a generarsi il certificato, la ricerca troverebbe righe e
    #   questa proprieta' tornerebbe **gialla** — «c'e' un imputato e non l'ho
    #   interrogato» — invece che verde.  Il giorno in cui §4.1 comincia a voler
    #   dire qualcosa e' precisamente il giorno in cui B13.3 deve smettere di
    #   dire «tutto al suo posto».
    fonti = [os.path.join(QUI, "rcp", "rcp.c"),
             os.path.join(QUI, "01-b3-rcp-innesta.py"),
             os.path.join(QUI, "01-b2-ngtcp2-wt-innesta.py")]
    if getattr(a, "fonti_codice", None):
        fonti = list(a.fonti_codice)
    presenti = [f for f in fonti if os.path.exists(f)]
    generatori = []
    illeggibili = []
    for f in presenti:
        u, t, err = corri_diviso(
            ["grep", "-nEi", r"x509|genera.*certificat|newkey|req -", f])
        if u >= 2:
            illeggibili.append((f, err.strip().splitlines()[:1]))
        elif u == 0 and t.strip():
            generatori.append((f, len(t.strip().splitlines())))
    e.guardate += len(presenti) - len(illeggibili)
    if not presenti:
        aperti.append("⚠ nessuna delle fonti del server e' leggibile da qui: "
                      "la ricerca del generatore non si e' potuta fare")
    elif illeggibili:
        aperti.append("⛔ [?] " + ", ".join(os.path.basename(f)
                                            for f, _ in illeggibili) +
                      ": il `grep` non ha potuto leggerle (uscita ≥ 2).  «Non "
                      "c'e' un generatore» e «non ho potuto guardare» non sono "
                      "la stessa cosa")
    elif generatori:
        for f, n in generatori:
            e.riga(f"⚠ {os.path.basename(f)}: {n} righe che nominano un "
                   f"certificato")
        aperti.append(
            "⛔ [?] C'E' UN IMPUTATO, E QUESTO BANCO NON LO INTERROGA: in " +
            ", ".join(f"{os.path.basename(f)} ({n} righe)"
                      for f, n in generatori) +
            " compaiono righe che nominano un certificato.  §4.1 obbliga il "
            "server a USARE quello d'autorita' e a NON rigenerare il proprio: "
            "un `grep` dice che l'obbligo ha finalmente un codice che lo puo' "
            "violare, non che quel codice lo rispetti.  ⛔ Serve un banco che "
            "installi un certificato d'autorita' e guardi che cosa il server "
            "presenta sul filo dopo — finche' non c'e', questa meta' resta "
            "aperta, e VERDE sarebbe la risposta piu' sbagliata delle tre")
    else:
        aperti.append(
            "⛔ [?] NESSUN IMPUTATO: in " + ", ".join(os.path.basename(f)
                                                      for f in presenti) +
            " non c'e' una riga che generi o scelga un certificato.  I due "
            "certificati li fa `01-b2-certificati.sh`, che e' un BANCO, e il "
            "server li riceve sulla riga di comando: l'obbligo di §4.1 — "
            "«usarlo e non rigenerare il proprio» — oggi non ha codice da "
            "rispettare, quindi non si puo' ne' violare ne' verificare")

    for g in guasti:
        e.riga(g)
    for x in aperti:
        e.riga(x)
    if guasti:
        return e.di(NON_PASSA, f"{len(guasti)} cose non tornano")
    if aperti:
        return e.di(SENZA_IMPUTATO,
                    "le parti misurabili passano; il certificato d'autorita' "
                    "resta aperto perche' manca il codice che dovrebbe "
                    "rispettarlo")
    return e.di(PASSA, "permessi, nome e certificato presentato: tutto al suo "
                       "posto")


# ===========================================================================
# 4 — LA PAGINA SERVITA IN TCP
# ===========================================================================
def proprieta_4(a):
    e = Esito(4, "la pagina servita in TCP: che si carichi, che pubblichi "
                 "l'impronta CORRENTE, e che l'endpoint dell'aggiornata esista",
              "RCP.md §2.2 («due ascoltatori con lo stesso numero») e §4.1-bis")
    # ⛔ Tre cose, e si contano tre: «non si carica» e «si carica con l'impronta
    #    vecchia» hanno cure opposte.
    ascolta = False
    e.guardate += 1
    try:
        with socket.create_connection((a.indirizzo, a.porta), timeout=4):
            ascolta = True
    except OSError as err:
        e.riga(f"⛔ nessuno in ascolto su TCP {a.indirizzo}:{a.porta} — {err}")
    if ascolta:
        e.riga(f"in ascolto su TCP {a.indirizzo}:{a.porta}")

    if not ascolta:
        # ⛔ E si dice DOVE sta oggi la pagina, o «non c'e' la pagina» e «la
        #    pagina sta altrove» hanno lo stesso aspetto.
        e.riga("⚠ oggi la pagina la serve `01-b2-raccogli.py` su "
               "127.0.0.1:8899, cioe' **la macchina del banco**, e l'impronta "
               "le arriva come parametro d'URL messo li' da uno script")
        e.riga("⛔ §4.1-bis dice «e' il server stesso a servire la pagina» e "
               "che l'impronta aggiornata si ritira «dal server che l'ha "
               "servita»: il secondo mestiere che §2.2 assegna al server "
               "**non e' stato scritto**")
        return e.di(SENZA_IMPUTATO,
                    "0 su 3: non c'e' nessun ascoltatore TCP, quindi non c'e' "
                    "ne' la pagina ne' l'endpoint da misurare")

    # Se un giorno ci sara', queste due righe lo misurano.
    import http.client
    corpo, stato = None, None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    e.guardate += 1
    try:
        import http.client
        c = http.client.HTTPSConnection(a.indirizzo, a.porta, context=ctx,
                                        timeout=6)
        c.request("GET", "/")
        r = c.getresponse()
        stato, corpo = r.status, r.read(300000).decode("utf-8", "replace")
    except Exception as err:  # noqa: BLE001
        e.riga(f"⛔ la pagina non si carica: {type(err).__name__}: {err}")
    if corpo is None:
        return e.di(NON_PASSA, "1 su 3: qualcuno ascolta in TCP ma la pagina "
                               "non si carica")
    e.riga(f"la pagina si carica: stato {stato}, {len(corpo)} byte")

    imp, _ = impronta_der(os.path.join(a.certificati, "sessione.pem"))
    import base64
    b64 = base64.b64encode(bytes.fromhex(imp)).decode() if imp else ""
    e.guardate += 1
    corrente = bool(b64 and (b64 in corpo or imp in corpo))
    if corrente:
        e.riga("⭐ la pagina porta l'impronta CORRENTE del certificato di "
               "sessione")
    else:
        e.riga("⛔ la pagina NON porta l'impronta corrente: e' il caso «una "
               "scheda aperta due settimane» di §4.1-bis, ma all'origine")

    e.guardate += 1
    endpoint = False
    for percorso in ("/impronta", "/rcp/impronta", "/.well-known/rcp-impronta"):
        try:
            c = http.client.HTTPSConnection(a.indirizzo, a.porta, context=ctx,
                                            timeout=4)
            c.request("GET", percorso)
            if c.getresponse().status == 200:
                endpoint = True
                e.riga(f"⭐ l'endpoint dell'impronta aggiornata risponde: "
                       f"{percorso}")
                break
        except Exception:  # noqa: BLE001
            continue
    if not endpoint:
        e.riga("⛔ nessuno dei percorsi provati risponde 200: l'endpoint da cui "
               "la pagina ritira l'impronta aggiornata (§4.1-bis) non c'e'")

    quante = sum((ascolta, bool(corpo), corrente, endpoint))
    if quante == 4:
        return e.di(PASSA, "la pagina c'e', porta l'impronta corrente, e "
                           "l'endpoint risponde")
    return e.di(NON_PASSA, f"{quante} su 4")


# ===========================================================================
# 5 e 6 — IL FILO.  Vogliono una connessione, e stanno insieme per non
#         spenderne due (e per non toccare due volte il conto di §4.4-bis).
# ===========================================================================
async def sul_filo(a):
    """Apre, fa la stretta di mano intera, e riporta quel che ha visto.

    Restituisce un dizionario con: `credito_uni`, `stato`, `desktop`,
    `impronta`, `uni_aperti`, `errore`.
    """
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)

    fuori = {"credito_uni": None, "stato": None, "desktop": None,
             "impronta": None, "uni_aperti": None, "errore": None,
             "bannato": False}

    # ⛔ IL CREDITO SI LEGGE DAL PARI, NON DALLA NOSTRA CONFIGURAZIONE — e' la
    #    stessa regola R8.3 di B6.  La spia sta sulla funzione che legge i
    #    parametri di trasporto arrivati.
    from aioquic.quic import connection as qc
    originale = qc.pull_quic_transport_parameters
    visti = {}

    def spia(buf, *args, **kw):
        p = originale(buf, *args, **kw)
        visti["p"] = p
        return p

    qc.pull_quic_transport_parameters = spia
    try:
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536,
                                 idle_timeout=120.0)
        conf.verify_mode = ssl.CERT_NONE
        autorita = f"{a.indirizzo}:{a.porta}"
        gestore = connect(a.indirizzo, a.porta, configuration=conf,
                          create_protocol=b3.Cliente)
        cli = await gestore.__aenter__()
        try:
            await asyncio.wait_for(cli.wait_connected(), timeout=8)

            # l'impronta del certificato presentato, per la proprieta' 3
            cert = getattr(getattr(cli._quic, "tls", None),
                           "_peer_certificate", None)
            if cert is not None:
                try:
                    from cryptography.hazmat.primitives.serialization import Encoding
                    fuori["impronta"] = hashlib.sha256(
                        cert.public_bytes(Encoding.DER)).hexdigest()
                except Exception:  # noqa: BLE001
                    pass

            p = visti.get("p")
            if p is not None:
                fuori["credito_uni"] = getattr(p, "initial_max_streams_uni", None)

            cli.apri_sessione(autorita, "/rcp/1")
            stato = await asyncio.wait_for(cli.accettata, timeout=8)
            if stato != "200":
                fuori["errore"] = f"CONNECT estesa :status={stato}"
                return fuori
            cli.apri_controllo()
            cli.transmit()
            b = b3.inquadra(b3.T["CIAO"], b3.corpo_ciao())
            cli.manda(b)
            await b3.attendi(cli, "ECCOMI")
            cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                  b3.s(a.utente) + b3.s(a.parola)))
            try:
                await b3.attendi(cli, "AMMESSO", attesa=20)
            except RuntimeError as err:
                fuori["errore"] = str(err)
                fuori["bannato"] = "TROPPI_TENTATIVI" in str(err)
                return fuori
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", 1920, 1080, 1920, 1080)
                                  + b3.s("it")))
            _, corpo, _ = await b3.attendi(cli, "SESSIONE")
            fuori["stato"] = corpo[0]
            n = struct.unpack("!H", corpo[9:11])[0]
            fuori["desktop"] = corpo[11:11 + n].decode("utf-8", "replace")

            # ⭐ IL CREDITO «IN OGNI MOMENTO», non solo quello iniziale.
            #    §2.3 vuole «almeno 16 disponibili IN OGNI MOMENTO»: il
            #    parametro iniziale e' l'apertura, non il regime.  Qui si
            #    prova ad APRIRE stream unidirezionali senza scriverci niente
            #    — nessun byte di canale, quindi nessuna violazione di §2.5 —
            #    e si conta quanti identificatori il trasporto concede.
            #
            # ⛔ DUE COSE CHE MANCAVANO, E SONO IL RILIEVO A15 (11 agosto 2026).
            #
            #    1. ⛔ QUESTA PROVA NON PARTE DA ZERO.  aioquic ha gia' aperto i
            #       propri stream unidirezionali di HTTP/3 — il controllo e i
            #       due di QPACK, **tre** — e consumano lo stesso credito.  Con
            #       un server che ne concede esattamente 16 (cioe' quel che
            #       l'innesto di B2 mette) il client puo' aprirne al massimo 13,
            #       e il banco stampava «⛔ il parametro iniziale dice 16 ma se
            #       ne aprono solo 13»: un ROSSO SU UN SERVER CONFORME alla riga
            #       che stava misurando.  Quindi i tre si CONTANO e si sommano.
            #    2. ⛔ E il ramo opposto era altrettanto cieco: se
            #       `create_webtransport_stream()` non sollevasse niente oltre
            #       il limite — se cioe' si limitasse ad allocare un
            #       identificatore — `aperti` varrebbe 16 sempre e il controllo
            #       non potrebbe dire *no* in NESSUN caso.  ⭐ Da cui il
            #       controllo positivo dello strumento: se ne chiedono
            #       **piu' del credito**, e il trasporto DEVE rifiutarne
            #       qualcuno.  Se li concede tutti, questa meta' non ha
            #       misurato niente e lo dichiara.
            gia = None
            try:
                gia = sum(1 for sid in cli._quic._streams if sid % 4 == 2)
            except Exception:  # noqa: BLE001
                gia = None
            fuori["uni_gia"] = gia
            credito = fuori["credito_uni"]
            chiesti = (credito if isinstance(credito, int) else 16) + 4
            aperti = 0
            for _ in range(chiesti):
                try:
                    cli._http.create_webtransport_stream(
                        cli.sessione, is_unidirectional=True)
                    aperti += 1
                except Exception:  # noqa: BLE001
                    break
            cli.transmit()
            fuori["uni_aperti"] = aperti
            fuori["uni_chiesti"] = chiesti
        finally:
            await gestore.__aexit__(None, None, None)
    except Exception as err:  # noqa: BLE001
        fuori["errore"] = f"{type(err).__name__}: {err}"
    finally:
        qc.pull_quic_transport_parameters = originale
    return fuori


def proprieta_5(a, filo):
    e = Esito(5, "il credito di almeno 16 stream unidirezionali concessi al "
                 "client",
              "RCP.md §2.3: «almeno 16 disponibili in ogni momento»")
    c = filo.get("credito_uni")
    e.guardate += 1
    if c is None:
        e.riga("⛔ il parametro non si e' letto dal pari: non e' «vale zero», e' "
               "che non si e' potuto guardare (la spia su "
               "`pull_quic_transport_parameters` non ha catturato niente)")
        return e.di(NON_MISURATO, "credito iniziale non letto")
    e.riga(f"credito INIZIALE letto dal pari: initial_max_streams_uni = {c}")
    if c < 16:
        return e.di(NON_PASSA, f"⛔ {c} < 16: §2.3 dice che «se il credito "
                               f"finisse, l'input non partirebbe affatto» e il "
                               f"sintomo, alla fase 4, sarebbe «il desktop non "
                               f"risponde»")

    aperti = filo.get("uni_aperti")
    chiesti = filo.get("uni_chiesti")
    gia = filo.get("uni_gia")
    if aperti is None or chiesti is None:
        e.riga("⚠ la prova «aprirne oltre il credito» non e' arrivata a farsi: "
               "resta il solo parametro iniziale, cioe' l'apertura e non il "
               "regime")
        return e.di(PASSA, f"{c} concessi all'apertura (il regime non e' stato "
                           f"misurato, e lo dice la riga qui sopra)")
    e.guardate += 1
    e.riga(f"stream unidirezionali gia' aperti da HTTP/3 prima della prova "
           f"(controllo + i due di QPACK): {gia if gia is not None else '⚠ non contati'}")
    e.riga(f"aperti da questa prova: {aperti} su {chiesti} chiesti "
           f"(⛔ chiesti = credito + 4, per poter vedere un rifiuto)")

    # ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO, e viene PRIMA del giudizio:
    #    uno strumento che non sa dire *no* non puo' dire *si'*.
    e.guardate += 1
    if aperti >= chiesti:
        return e.di(NON_MISURATO,
                    f"⛔ il trasporto ha concesso TUTTI i {chiesti} stream "
                    f"chiesti, cioe' {chiesti - c} oltre il credito dichiarato "
                    f"({c}): `create_webtransport_stream()` non fa rispettare "
                    f"il limite da questa parte, si limita ad allocare un "
                    f"identificatore.  ⛔ Allora «se ne aprono N» non misura il "
                    f"credito in nessun caso — ne' per dire si' ne' per dire "
                    f"no — e questa meta' di B13.5 non e' stata misurata")
    e.riga(f"⭐ controllo positivo: chiedendone {chiesti} il trasporto se n'e' "
           f"fermato a {aperti} — sa dire *no*, quindi il suo *si'* vale")

    if gia is None:
        return e.di(NON_MISURATO,
                    "⛔ non ho potuto contare gli stream unidirezionali che "
                    "HTTP/3 aveva gia' aperto: senza quel numero «se ne aprono "
                    "N» e «il credito e' N» sono due cose diverse, e "
                    "confonderle darebbe un rosso su un server conforme")
    totale = gia + aperti
    e.guardate += 1
    if totale < 16:
        return e.di(NON_PASSA,
                    f"⛔ il parametro iniziale dice {c}, ma in tutto se ne "
                    f"aprono {totale} ({gia} di HTTP/3 + {aperti} di questa "
                    f"prova): §2.3 ne vuole almeno 16 disponibili IN OGNI "
                    f"MOMENTO")
    return e.di(PASSA, f"{c} concessi all'apertura, e {totale} aperti davvero a "
                       f"sessione viva ({gia} di HTTP/3 + {aperti} nostri), col "
                       f"trasporto che ha rifiutato il {chiesti}-esimo")


def stato_di_sessione(codice):
    """Che valore il codice mette nel campo `stato` di `SESSIONE` (§4.5).

    Restituisce `(valore, ultime_scritture, errore)`.  ⛔ `valore` e' il testo
    esatto dell'argomento, non un numero: `1` e `ripresa ? 2 : 1` sono due cose
    diverse e devono restare diverse.
    """
    m = re.search(r"manda_messaggio\s*\(\s*\w+\s*,\s*T_SESSIONE\b", codice)
    if not m:
        return None, [], ("non trovo dove il codice manda `SESSIONE` "
                          "(`manda_messaggio(…, T_SESSIONE, …)`): la ricerca "
                          "non sa dove guardare, e un «non l'ho trovato» da qui "
                          "non e' un «non c'e'»")
    prima = codice[:m.start()]
    # il corpo si costruisce con uno `scrittore`, e il PRIMO byte e' `stato`
    inizio = prima.rfind("scrittore")
    if inizio < 0:
        return None, [], ("trovo l'invio di `SESSIONE` ma non lo `scrittore` "
                          "che ne costruisce il corpo: il modo in cui il corpo "
                          "si scrive e' cambiato, e questa ricerca va rifatta")
    blocco = prima[inizio:]
    scritture = re.findall(r"sc_byte\s*\(\s*&?\w+\s*,\s*([^;]*?)\)\s*;", blocco)
    if not scritture:
        return None, [], ("trovo lo `scrittore` del corpo di `SESSIONE` ma "
                          "nessun `sc_byte(...)`: il primo campo non si scrive "
                          "piu' come credo")
    return scritture[0].strip(), [s.strip() for s in scritture[:3]], None


def proprieta_6(a, filo):
    e = Esito(6, "che `stato` valga SEMPRE NUOVA",
              "RCP.md §4.5 (1 = NUOVA, 2 = RIPRESA) · fasi/01-filo-nudo.md "
              "B13.6: «che nessuno abbia scritto per prudenza un ramo RIPRESA»")
    st = filo.get("stato")
    e.guardate += 1
    if st is None:
        e.riga(f"⛔ nessun `SESSIONE` e' arrivato: {filo.get('errore')}")
        return e.di(NON_MISURATO, "sul filo non si e' potuto guardare")
    nome_stato = ("NUOVA" if st == 1 else "RIPRESA" if st == 2
                  else "⛔ FUORI DALLO SPAZIO DEI VALORI di §4.5")
    e.riga(f"sul filo: `SESSIONE.stato` = {st} ({nome_stato})  "
           f"desktop = «{filo.get('desktop')}»")
    if st != 1:
        return e.di(NON_PASSA, f"⛔ `stato` vale {st}: la fase 1 non ha nessuna "
                               f"sessione da riprendere")

    # ⛔ E LA META' CHE IL FILO NON PUO' VEDERE: un ramo `RIPRESA` scritto per
    #    prudenza e mai raggiunto darebbe `1` sul filo tutte le volte.  Si
    #    guarda il codice — e prima si verifica di saperlo leggere.
    #
    # ⛔⭐ DUE COSE CAMBIATE L'11 AGOSTO 2026, E VANNO LETTE INSIEME.
    #
    #  (a) RILIEVO R12.5 — LA COPIA SBAGLIATA.  Questa meta' leggeva
    #      `QUI/rcp/rcp.c`, mentre il server acceso da `01-b13-lancia.sh` e'
    #      compilato da `…/b2/ngtcp2/examples/rcp.c`, che e' un ALTRO file: si
    #      aggiunge un ramo `RIPRESA` alla copia compilata senza ricopiarla
    #      indietro, il server lo esegue, B13 legge l'altro file, non trova la
    #      parola, e stampa «nel codice il ramo RIPRESA non esiste» — verde,
    #      sulla meta' del giudizio che il filo non puo' vedere.  ⭐ Il banco
    #      gemello, `01-b6-lancia.sh:197-206`, per la stessa domanda legge
    #      TUTT'E DUE le copie e pretende che combacino.  Adesso lo fa anche
    #      questo: due banchi della stessa mano non possono rispondere alla
    #      stessa domanda con due forze diverse.
    #
    #  (b) RILIEVO A17 — SI CERCAVA LA PAROLA, NON IL RAMO.  La conclusione era
    #      «nel codice il ramo RIPRESA non esiste» e la prova era `"RIPRESA" in
    #      riga`, riga per riga; il controllo positivo verificava che nel file
    #      comparisse «SESSIONE», cioe' che il file fosse leggibile e fosse
    #      quello giusto — non che una **diramazione** si possa trovare
    #      cercandone il nome (`LEZIONI.md` §1.9 regola 2: il controllo positivo
    #      dev'essere sullo STESSO tipo di cosa che si cerca).  ⛔ Caso concreto:
    #      `corpo[0] = ripresa_possibile ? 2 : 1;` non contiene la stringa
    #      `RIPRESA`, e B13.6 stampava «il ramo RIPRESA non esiste».  L'unica
    #      cosa che faceva diventare rossa questa meta' era che qualcuno avesse
    #      scritto **la parola**.
    #      ⭐ Adesso si cerca LA COSA: il byte che il codice mette nel campo
    #      `stato` di `SESSIONE`, che e' l'unico posto da cui un 2 potrebbe
    #      uscire.  Se e' il letterale `1`, nessun ramo puo' produrre RIPRESA,
    #      **comunque lo si scriva**; se e' qualunque altra cosa — una
    #      variabile, un ternario, una chiamata — un ramo c'e', e la parola non
    #      c'entra.
    copie = [("sorgente", getattr(a, "codice", None)
              or os.path.join(QUI, "rcp", "rcp.c"))]
    if getattr(a, "codice_compilato", None):
        copie.append(("copia compilata", a.codice_compilato))
    letti = {}
    for nome, percorso in copie:
        e.guardate += 1
        if not os.path.exists(percorso):
            e.riga(f"⚠ la {nome} «{percorso}» non si legge da qui")
            continue
        try:
            with open(percorso, encoding="utf-8", errors="replace") as f:
                letti[nome] = (percorso, f.read())
        except OSError as err:
            e.riga(f"⚠ la {nome} «{percorso}» non si apre: {err}")
    if "copia compilata" not in letti and len(copie) > 1:
        return e.di(SENZA_IMPUTATO,
                    "⛔ sul filo vale NUOVA, ma la COPIA COMPILATA di rcp.c non "
                    "si e' potuta leggere: giudicare il codice sull'altra copia "
                    "vorrebbe dire rispondere a «sto leggendo un rcp.c?» invece "
                    "che a «sto leggendo quello che e' dentro il binario che ho "
                    "appena acceso?» (LEZIONI.md §1.9, ottava veste)")
    if not letti:
        return e.di(SENZA_IMPUTATO, "sul filo NUOVA, nel codice non guardato")

    esiti_copie = {}
    for nome, (percorso, codice) in letti.items():
        # ⭐ IL CONTROLLO POSITIVO, e adesso e' sullo STESSO TIPO DI COSA: non
        #    «il file contiene una parola», ma «so trovare il punto in cui il
        #    codice decide questo campo».  Se non lo trovo, non concludo.
        valore, viste, errore = stato_di_sessione(codice)
        e.guardate += 1
        if errore:
            e.riga(f"⛔ {nome} ({os.path.basename(percorso)}): {errore}")
            esiti_copie[nome] = None
            continue
        e.riga(f"⭐ controllo positivo su {nome}: ho TROVATO il punto in cui il "
               f"codice scrive `stato` di SESSIONE — «{valore}»"
               + (f"  (le ultime scritture del corpo: {', '.join(viste)})"
                  if viste else ""))
        esiti_copie[nome] = valore

    valori = {n: v for n, v in esiti_copie.items() if v is not None}
    if not valori:
        return e.di(NON_MISURATO,
                    "⛔ in nessuna copia ho trovato il punto in cui il codice "
                    "decide `stato`: il controllo positivo non passa, e ogni "
                    "«il ramo non esiste» che seguisse sarebbe muto")
    if len(set(valori.values())) > 1:
        return e.di(NON_PASSA,
                    f"⛔ LE DUE COPIE DI rcp.c NON COMBACIANO su `stato`: "
                    + " · ".join(f"{n} → «{v}»" for n, v in valori.items()) +
                    ".  Il server esegue la copia compilata: giudicare "
                    "sull'altra sarebbe giudicare un codice che non gira")

    valore = next(iter(valori.values()))
    e.guardate += 1
    if valore != "1":
        return e.di(NON_PASSA,
                    f"⛔ il codice scrive `stato` = «{valore}», che NON e' il "
                    f"letterale 1: c'e' una diramazione, e un `[?]` "
                    f"implementato a meta' e non provato e' quel che il confine "
                    f"della fase dichiara di voler evitare — comunque sia "
                    f"scritta, e anche se la parola RIPRESA non compare")

    # ⚠ E la parola resta cercata, ma come SEGNALE IN PIU', non come prova: un
    #   `RIPRESA` che comparisse mentre `stato` e' il letterale 1 vorrebbe dire
    #   che qualcuno ha cominciato a scrivere il ramo altrove.
    nominata = {}
    for nome, (_p, codice) in letti.items():
        nominata[nome] = [f"{i + 1}: {r.strip()}"
                          for i, r in enumerate(codice.splitlines())
                          if "RIPRESA" in r and not r.strip().startswith("*")]
    for nome, righe in nominata.items():
        if righe:
            e.riga(f"⚠ {nome}: {len(righe)} righe nominano RIPRESA pur con "
                   f"`stato` = 1 — qualcuno ha cominciato a scrivere il ramo:")
            for r in righe[:4]:
                e.riga(f"   {r}")
    e.riga("nessuna diramazione puo' produrre `stato` = 2: il campo e' il "
           "letterale 1 in " + " e in ".join(letti))
    return e.di(PASSA, "sul filo vale NUOVA, e nel codice — in tutte e "
                       f"{len(letti)} le copie lette — `stato` e' il letterale "
                       "1, quindi nessun ramo RIPRESA puo' esistere")


# ===========================================================================
# ⛔⭐ LA CERTIFICAZIONE DI B13 — `LEZIONI.md` §1.2 e §1.3, e rilievi A1 e A2
# ===========================================================================
# ⛔ PERCHE' ESISTE, E PERCHE' NON POTEVA VENIRE DA B12.
#
# La revisione R12-A ha stabilito due cose su questo banco:
#
#   A1  **B13 non e' certificabile da `01-b12-guasti.py`**: il suo guasto e' di
#       tipo `riga-di-comando`, e `--applica` rifiuta i guasti che non hanno un
#       appiglio nel testo.  Il ramo `B13)` di `gira()` e' codice morto, e i
#       passi 2/3 e 3/3 di B13 non si eseguono mai;
#   A2  **e il guasto catalogato non era nemmeno quello giusto**: «accendere il
#       server con `pagina.pem` al posto di `sessione.pem`» non tocca nessuno
#       dei due file su disco, quindi `proprieta_1` — che confronta le impronte
#       dei FILE — non cambierebbe colore.  A vedere quel guasto e' B13.3 («il
#       certificato PRESENTATO sul filo non e' sessione.pem»), che e' un'altra
#       proprieta' e un altro difetto.  Il guasto che B13.1 vede e' un altro
#       ancora: **copiare `sessione.pem` su `pagina.pem`**.
#
# ⛔ `01-b12-guasti.py` non e' un file di questo autore e non e' stato toccato:
#    i due rilievi restano aperti li', e sono nel rapporto.  ⭐ Quel che si puo'
#    fare da qui e' quel che B8 fa da se': **B13 si certifica da solo**, con i
#    guasti costruiti a mano su COPIE, e senza toccare niente di vero.
#
# ⛔ E la regola del criterio e' quella di B8: non basta che il banco diventi
#    rosso, deve diventarlo **in quel punto** — cioe' l'esito atteso e' scritto
#    guasto per guasto, e un guasto che producesse un rosso di un'altra
#    proprieta' conta come fallito.
def _cert(dove, nome, giorni, indirizzo):
    """Un certificato ECDSA P-256 con SAN IP, per i guasti costruiti a mano."""
    u, t = corri(["openssl", "req", "-x509", "-newkey", "ec",
                  "-pkeyopt", "ec_paramgen_curve:prime256v1",
                  "-keyout", os.path.join(dove, f"{nome}.key"),
                  "-out", os.path.join(dove, f"{nome}.pem"),
                  "-days", str(giorni), "-nodes",
                  "-subj", f"/CN={indirizzo}",
                  "-addext", f"subjectAltName=IP:{indirizzo}"])
    if u != 0:
        return t
    os.chmod(os.path.join(dove, f"{nome}.key"), 0o600)
    return None


def certifica(a):
    import copy as _copy
    import shutil
    import tempfile

    print("== ⛔ LA CERTIFICAZIONE DI B13: un guasto per volta, e il rosso "
          "atteso NEL SUO PUNTO")
    print("   ⚠ Gira su COPIE in una cartella temporanea: non accende nessun "
          "server, non")
    print("     tocca i certificati veri e non consuma il conto di §4.4-bis.")
    base = tempfile.mkdtemp(prefix="b13-certifica-")
    da_root = (os.geteuid() == 0)
    try:
        cert = os.path.join(base, "certificati")
        prod = os.path.join(base, "prodotti")
        fonti = os.path.join(base, "fonti")
        for d in (cert, prod, fonti):
            os.makedirs(d)
        for nome, giorni in (("pagina", 3650), ("sessione", 7)):
            err = _cert(cert, nome, giorni, a.indirizzo)
            if err:
                print(f"   {ROSSO}NO{GRIGIO}  ⛔ openssl non ha costruito "
                      f"{nome}.pem: {err.strip()[:200]}")
                print("        La certificazione NON si e' potuta fare: e non "
                      "e' «passata».")
                return 2
        with open(os.path.join(prod, "b13-finto.log"), "w") as f:
            f.write("una riga di registro senza niente dentro\n")
        codice_sano = ('static void x(void)\n{\n\tscrittore w = {corpo, 8};\n'
                       '\tsc_byte(&w, 1); /* 1 = NUOVA */\n'
                       '\tsc_u32(&w, tl);\n'
                       '\tmanda_messaggio(s, T_SESSIONE, corpo, w.len);\n}\n')
        codice_ramo = codice_sano.replace("sc_byte(&w, 1); /* 1 = NUOVA */",
                                          "sc_byte(&w, ripresa ? 2 : 1);")
        sano_c = os.path.join(fonti, "rcp.c")
        comp_c = os.path.join(fonti, "rcp-compilato.c")
        for p in (sano_c, comp_c):
            with open(p, "w") as f:
                f.write(codice_sano)
        with open(os.path.join(fonti, "senza-generatore.py"), "w") as f:
            f.write("# nessuna riga che generi un certificato\n")
        with open(os.path.join(fonti, "con-generatore.py"), "w") as f:
            f.write("subprocess.run(['openssl', 'req', '-newkey', 'ec'])\n")

        def arg(**cambi):
            b = argparse.Namespace(**vars(a))
            b.certificati, b.prodotti = cert, prod
            b.codice, b.codice_compilato = sano_c, comp_c
            b.fonti_codice = [os.path.join(fonti, "senza-generatore.py")]
            for k, v in cambi.items():
                setattr(b, k, v)
            return b

        FILO_SANO = {"credito_uni": 16, "stato": 1, "desktop": "sconosciuto",
                     "impronta": None, "uni_aperti": 13, "uni_gia": 3,
                     "uni_chiesti": 20, "errore": None, "bannato": False}
        def imp_ora():
            # ⛔ L'impronta si rilegge AL MOMENTO: alcuni guasti rigenerano
            #    `sessione.pem`, e un'impronta calcolata una volta sola darebbe
            #    «il certificato sul filo non e' sessione.pem» su un giro sano
            #    — cioe' un rosso del banco travestito da rosso del server.
            imp, _err = impronta_der(os.path.join(cert, "sessione.pem"))
            return imp

        def filo(**cambi):
            f = dict(FILO_SANO)
            f.update(cambi)
            return f

        # ── i guasti, uno per volta ─────────────────────────────────────────
        # (nome, cosa fa, quale proprieta', esito atteso, frase attesa)
        prove = []

        def copia_pagina_su_sessione():
            shutil.copy(os.path.join(cert, "sessione.pem"),
                        os.path.join(cert, "pagina.pem"))

        def rimetti_pagina():
            _cert(cert, "pagina", 3650, a.indirizzo)

        def pianta_parola():
            with open(os.path.join(prod, "b13-guasto.log"), "w") as f:
                f.write(f"utente=prova parola={a.parola}\n")

        def togli_parola():
            os.remove(os.path.join(prod, "b13-guasto.log"))

        def chiudi_registro():
            os.chmod(os.path.join(prod, "b13-finto.log"), 0o000)

        def riapri_registro():
            os.chmod(os.path.join(prod, "b13-finto.log"), 0o644)

        def permessi_larghi():
            os.chmod(os.path.join(cert, "sessione.key"), 0o644)

        def permessi_stretti():
            os.chmod(os.path.join(cert, "sessione.key"), 0o600)

        def san_storto():
            _cert(cert, "sessione", 7, "10.99.99.99")

        def san_dritto():
            _cert(cert, "sessione", 7, a.indirizzo)

        def ramo_nel_compilato():
            with open(comp_c, "w") as f:
                f.write(codice_ramo)

        def ramo_via():
            with open(comp_c, "w") as f:
                f.write(codice_sano)

        def compilato_via():
            os.rename(comp_c, comp_c + ".nascosto")

        def compilato_torna():
            os.rename(comp_c + ".nascosto", comp_c)

        def niente():
            return None

        prove = [
            ("⭐ il giro SANO non deve essere rosso (senza questo, ogni rosso "
             "qui sotto potrebbe esserci gia')",
             niente, niente, lambda: proprieta_1(arg()), PASSA, None),
            ("B13.1 ⛔ sessione.pem copiato su pagina.pem — il guasto GIUSTO "
             "per B13.1 (A2)",
             copia_pagina_su_sessione, rimetti_pagina,
             lambda: proprieta_1(arg()), NON_PASSA, "LE IMPRONTE COMBACIANO"),
            ("B13.2 ⛔ la parola d'ordine dentro un registro prodotto",
             pianta_parola, togli_parola, lambda: proprieta_2(arg()),
             NON_PASSA, "LA PAROLA E' DENTRO UN REGISTRO"),
            ("B13.2 ⛔ un registro che il `grep` NON puo' leggere (A13): non e' "
             "«pulito», e' «non ho potuto guardare»",
             chiudi_registro, riapri_registro, lambda: proprieta_2(arg()),
             NON_MISURATO, "NON ha coperto tutto"),
            ("B13.3 ⛔ la chiave di sessione a 0644",
             permessi_larghi, permessi_stretti,
             lambda: proprieta_3(arg(), imp_ora()), NON_PASSA,
             "§4.1 vuole 0600"),
            ("B13.3 ⛔ il subjectAltName che non e' l'indirizzo del server",
             san_storto, san_dritto,
             lambda: proprieta_3(arg(), None), NON_PASSA, "subjectAltName"),
            ("B13.3 ⛔ il certificato presentato sul filo NON e' sessione.pem",
             niente, niente,
             lambda: proprieta_3(arg(), "00" * 32), NON_PASSA,
             "PRESENTATO sul filo non e'"),
            ("B13.3 ⛔ una fonte che GENERA certificati (A12): piu' imputati "
             "c'erano, piu' la proprieta' era verde",
             niente, niente,
             lambda: proprieta_3(
                 arg(fonti_codice=[os.path.join(fonti, "con-generatore.py")]),
                 imp_ora()),
             SENZA_IMPUTATO, "C'E' UN IMPUTATO, E QUESTO BANCO NON LO INTERROGA"),
            ("B13.5 ⛔ il credito iniziale e' 8",
             niente, niente,
             lambda: proprieta_5(arg(), filo(credito_uni=8)), NON_PASSA,
             "8 < 16"),
            ("B13.5 ⛔ il trasporto concede TUTTI quelli chiesti (A15): lo "
             "strumento non sa dire *no*",
             niente, niente,
             lambda: proprieta_5(arg(), filo(uni_aperti=20)), NON_MISURATO,
             "non fa rispettare il limite"),
            ("B13.5 ⭐ e il controllo che dice il contrario: 3 di HTTP/3 + 13 "
             "nostri su un server CONFORME resta VERDE (A15: prima era rosso)",
             niente, niente, lambda: proprieta_5(arg(), filo()), PASSA,
             "16 aperti davvero"),
            ("B13.6 ⛔ `stato` vale 2 sul filo",
             niente, niente, lambda: proprieta_6(arg(), filo(stato=2)),
             NON_PASSA, "`stato` vale 2"),
            ("B13.6 ⛔ un ramo nella COPIA COMPILATA che non nomina RIPRESA "
             "(A17): `ripresa ? 2 : 1`",
             ramo_nel_compilato, ramo_via, lambda: proprieta_6(arg(), filo()),
             NON_PASSA, "NON COMBACIANO"),
            ("B13.6 ⛔ la copia compilata non si legge (R12.5): non si giudica "
             "sull'altra",
             compilato_via, compilato_torna, lambda: proprieta_6(arg(), filo()),
             SENZA_IMPUTATO, "COPIA COMPILATA"),
        ]

        falliti, eseguiti, approvati = 0, 0, 0
        for nome, rompi, rimetti, gira, atteso, frase in prove:
            if rompi is chiudi_registro and da_root:
                # ⛔ Da root i permessi non fermano nessuno: questo guasto NON
                #    e' stato provato, e un guasto saltato non e' un guasto
                #    passato (la stessa riga di `01-b8-prova-ban.c`).
                print(f"   {GIALLO}??{GRIGIO}  SALTATO da root: {nome}")
                print("        ⛔ rilancia da utente normale, o questa riga non "
                      "prova niente")
                falliti += 1
                continue
            rompi()
            try:
                esito = gira()
            finally:
                rimetti()
            eseguiti += 1
            testo = " ".join([esito.testo] + esito.righe)
            buono = esito.esito == atteso and (frase is None or frase in testo)
            if buono:
                approvati += 1
            else:
                falliti += 1
            segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
            print(f"   {segno}  {nome}")
            print(f"        atteso «{atteso}»"
                  + (f" con «{frase}»" if frase else "")
                  + f" · arrivato «{esito.esito}»")
            if not buono:
                print(f"        ⛔ {esito.testo}")
                for r in esito.righe[:4]:
                    print(f"           {r}")

        print()
        print(f"   == il denominatore: {len(prove)} guasti costruiti a mano, "
              f"{eseguiti} eseguiti, {approvati} approvati, {falliti} falliti")
        if eseguiti == 0:
            print(f"   {ROSSO}⛔ ZERO guasti eseguiti: non e' una "
                  f"certificazione{GRIGIO}")
            return 2
        if falliti:
            print(f"   {ROSSO}⛔ B13 NON E' CERTIFICATO: {falliti} guasti su "
                  f"{len(prove)} non lo fanno diventare rosso nel loro "
                  f"punto{GRIGIO}")
            return 1
        print(f"   {VERDE}⭐ B13 e' certificato: tutti e {approvati} i guasti "
              f"costruiti a mano lo fanno cambiare colore NEL LORO PUNTO"
              f"{GRIGIO}")
        print("   ⚠ e non e' «B13 e' giusto»: e' «B13 sa vedere questi "
              "quattordici difetti».  Quel che")
        print("     resta fuori: la pagina in TCP (B13.4), che oggi non ha "
              "imputato, e tutto")
        print("     quel che vive sul filo — li' il guasto va costruito sul "
              "server, non qui.")
        return 0
    finally:
        for radice, _d, files in os.walk(base):
            for f in files:
                try:
                    os.chmod(os.path.join(radice, f), 0o600)
                except OSError:
                    pass
        shutil.rmtree(base, ignore_errors=True)


# ===========================================================================
def principale(a):
    print("== ⭐ B13 — le sei cose che la fase produce e che nessun banco "
          "guardava")
    print("   fasi/01-filo-nudo.md B13, rilievo R3.24\n")

    if a.elenco:
        for n, t in ((1, "i due certificati sono DUE: impronte e scadenze diverse"),
                     (2, "la parola d'ordine in nessun registro del giro"),
                     (3, "chiave 0600 · SAN che combacia · CA usata senza rigenerare"),
                     (4, "la pagina in TCP, l'impronta corrente, l'endpoint"),
                     (5, "credito ≥ 16 stream unidirezionali"),
                     (6, "`stato` sempre NUOVA")):
            print(f"  B13.{n}  {t}")
        print("\n  ⛔ Quattro esiti, non due: OK · NO · ?? (non misurato) · "
              "[?] (manca l'imputato)")
        return 0

    # ── B0.1: lo stato iniziale ────────────────────────────────────────────
    print("== ⛔ Lo stato iniziale (B0.1)")
    print(f"    --  certificati in {a.certificati}")
    print(f"    --  file del giro sotto {a.prodotti}")
    print(f"    --  server atteso su {a.indirizzo}:{a.porta} (UDP per RCP, "
          f"TCP per la pagina)")
    filo = asyncio.run(sul_filo(a))
    if filo.get("bannato"):
        print(f"\n    {ROSSO}⛔ L'INDIRIZZO E' BANNATO (§4.4-bis) — B0.3"
              f"{GRIGIO}")
        print("       Un altro banco ha fallito tre autenticazioni da qui, e il")
        print("       ban dura DODICI ORE.  Le cure sono due (§4.4-bis):")
        print("         · il comando di sblocco — `01-b8-sblocca.py --socket")
        print("           <presa> <indirizzo>` — che vuole il server acceso con")
        print("           `--comando-socket`;")
        print("         · riaccendere il server, che azzera il conto in memoria.")
        print("       Nessuna delle sei proprieta' si misura: sarebbe un falso")
        print("       rosso, che e' quel che B0.3 esiste per impedire.")
        return 5
    if filo.get("errore") and filo.get("stato") is None:
        print(f"    {GIALLO}??{GRIGIO}  il filo non si e' aperto: "
              f"{filo['errore']}")
        print("        ⚠ le proprieta' 5 e 6 non si misureranno, e lo diranno.")
    else:
        print(f"    {VERDE}OK{GRIGIO}  la stretta di mano intera riesce: "
              f"stato={filo.get('stato')} desktop=«{filo.get('desktop')}»")
    print()

    esiti = [
        proprieta_1(a),
        proprieta_2(a),
        proprieta_3(a, filo.get("impronta")),
        proprieta_4(a),
        proprieta_5(a, filo),
        proprieta_6(a, filo),
    ]
    print("== Le sei proprieta'")
    for e in esiti:
        e.stampa()
        print()

    # ── IL DENOMINATORE ────────────────────────────────────────────────────
    print("    == quel che questo giro ha davvero guardato")
    for e in esiti:
        print(f"    {COLORE[e.esito]}{e.esito:3s}{GRIGIO}  B13.{e.numero}  "
              f"{e.guardate:4d} cose guardate")
    quante = sum(e.guardate for e in esiti)
    print(f"    --   in tutto: {quante} cose guardate su 6 proprieta'")

    # ⛔ UN VERDETTO SU ZERO COSE NON SI DA'.
    if quante == 0:
        print(f"\n    {ROSSO}⛔ B13 ha guardato ZERO cose: non e' un verde, e "
              f"non e' nemmeno un rosso{GRIGIO}")
        return 2

    rossi = [e for e in esiti if e.esito == NON_PASSA]
    gialli = [e for e in esiti if e.esito in (NON_MISURATO, SENZA_IMPUTATO)]
    print()
    if rossi:
        print(f"    {ROSSO}⛔ B13: {len(rossi)} proprieta' su 6 NON passano"
              f"{GRIGIO}")
        for e in rossi:
            print(f"       B13.{e.numero}  {e.testo}")
        if gialli:
            print(f"       ⚠ e {len(gialli)} restano aperte (vedi sotto)")
        return 1
    if gialli:
        print(f"    {GIALLO}[?] B13: {6 - len(gialli)} proprieta' su 6 passano, "
              f"{len(gialli)} non si possono giudicare{GRIGIO}")
        for e in gialli:
            print(f"       B13.{e.numero}  {e.esito}  {e.testo}")
        print("       ⛔ «Non misurato» non e' «passa»: una proprieta' senza")
        print("          imputato e' un buco DICHIARATO, e va portata nel")
        print("          documento di fase come `[?]`, non archiviata.")
        return 3
    print(f"    {VERDE}⭐ B13: sei proprieta' su sei, e i numeri qui sopra "
          f"dicono su che cosa{GRIGIO}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B13 — le sei cose che nessun banco guardava")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--certificati", default="/media/REMOTIX/b2-certificati")
    p.add_argument("--prodotti", default="/srv/src",
                   help="la cartella dei file prodotti dal giro, per B13.2")
    # ⛔ Le DUE copie di rcp.c, e vanno passate tutt'e due (R12.5): il server
    #    esegue quella dentro `examples/`, non quella in `banchi/rcp/`.
    p.add_argument("--codice", default=None,
                   help="il sorgente rcp.c (predefinito: rcp/rcp.c accanto a questo file)")
    p.add_argument("--codice-compilato", default=None,
                   help="⛔ la COPIA da cui il binario acceso e' stato compilato")
    p.add_argument("--fonti-codice", nargs="*", default=None,
                   help="le fonti in cui B13.3 cerca un generatore di certificati")
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--certifica", action="store_true",
                   help="⛔ costruisce i guasti a mano e pretende il rosso NEL "
                        "SUO PUNTO — non tocca niente di vero")
    a = p.parse_args()
    if a.certifica:
        sys.exit(certifica(a))
    sys.exit(principale(a))
