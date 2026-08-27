#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c14 — ⭐⭐ «LE SCATOLE NON SI DISTURBANO» — la maglia che guarda LA RETE
===========================================================================

    python3 11-c14-non-si-disturbano.py
    python3 11-c14-non-si-disturbano.py --solo-porte
    python3 11-c14-non-si-disturbano.py --certifica

⛔ Come C11, questa maglia **non prova il prodotto**: prova che la rete valga
   qualcosa.  ⭐ E prova una cosa che il documento di fase fin qui si limitava
   ad AFFERMARE.

`fasi/11…` §3.4 dice che le quattro scatole possono girare **insieme**, e ci
costruisce sopra il piano di lavoro (*«per fortuna stavolta lo sviluppo
dovrebbe essere veloce a causa del fatto che i container possono essere tutti
e 4 attivi contemporaneamente»*, parole dell'utente).
⇒ ⛔ **Un'affermazione su cui poggia un piano, e che nessuno aveva misurato.**
  §4.2: *«§3.4 lo AFFERMA; questo lo MISURA»*.

---------------------------------------------------------------------------
⭐ LA DOMANDA ESATTA, e le due parti in cui si spezza
---------------------------------------------------------------------------

    *le stesse prove, da sole e in parallelo, danno lo stesso esito?*

  PARTE 1 · LE PORTE      ⛔ il prezzo dichiarato di `--network=host`
  PARTE 2 · L'ESITO       ⭐ la stessa prova, sola contro in parallelo

### PARTE 1 — e perche' e' la prima

`11-accendi.sh` porta scritto un prezzo, con dentro un rimando a questa maglia:

    --network=host   ⚠ NON e' una scelta: `netavark` su questa macchina non
                     riesce ad applicare le regole di rete.  ⛔ E ha un PREZZO:
                     quattro scatole accese insieme CONDIVIDONO le porte
                     dell'ospite, quindi ciascuna dovra' avere la SUA porta —
                     o si pesteranno i piedi in un modo che somiglia a un
                     guasto del prodotto.  ⇒ Da rivedere quando si fa C14.

⇒ ⭐ **Eccoci.**  E il modo di misurarlo non e' leggere `11-accendi.sh` — quello
  e' *«scritto»*, non *«in vigore»* (E1).  Si accendono i quattro server
  **insieme** e si guarda chi ascolta davvero, e dove.

⛔ E si prova anche il ROVESCIO: due scatole sulla **stessa** porta.  Se
   quello NON fallisce, allora la separazione per porta non e' una separazione,
   e il prezzo era scritto male.

### PARTE 2 — la stessa prova, sola contro in parallelo

Si usa la **prova A di C8** (`--senza-sessione`), e la scelta ha tre ragioni:

  · ⭐ e' l'unica maglia del prodotto che oggi GIUDICA in tutte e quattro le
    scatole: non passa dal prodotto, quindi il difetto aperto della fase 10
    §7.4 (`[M]` dieci sessioni GNOME nuove su dieci nascono cieche) non la
    ferma;
  · ⭐⭐ col guasto innestato (`--senza-cura`) il suo esito porta dentro **un
    verde E un rosso** — `1 si' · 1 no` — cioe' e' un'impronta che si rompe
    in due modi diversi.  ⛔ Una prova che dice sempre e solo «verde» sarebbe
    un metro spuntato: se in parallelo si rompesse, come farebbe a dirlo?
  · fa lavorare **davvero** la scatola: crea due utenti, avvia due volte un
    browser, decodifica due immagini.  ⇒ Se le scatole si disturbano, e'
    esattamente sotto questo carico che deve venire fuori.

---------------------------------------------------------------------------
⛔⛔ LE DUE TRAPPOLE, dichiarate prima dei numeri
---------------------------------------------------------------------------

1. ⛔ **«?» uguale a «?» PASSA il confronto** (`LEZIONI.md` §1.47).  Se una
   scatola non risponde ne' da sola ne' in parallelo, le sue due impronte sono
   uguali — e un confronto ingenuo direbbe **verde** senza aver guardato
   niente.  ⇒ Qui una scatola senza impronta e' **«non giudicata»**, mai
   «uguale».

2. ⚠ **Il primo avvio di Firefox e' piu' lento degli altri.**  Se si misurasse
   «sole» per prime e «insieme» per seconde, il parallelo partirebbe con la
   memoria dell'ospite gia' calda ⇒ ⛔ un confronto truccato **a favore** del
   parallelo, cioe' proprio nel verso in cui questa maglia potrebbe sbagliare.
   ⇒ Si fa un **giro di riscaldamento** che si BUTTA, e lo si dichiara.

---------------------------------------------------------------------------
⚠ E IL TEMPO NON E' UN VERDETTO
---------------------------------------------------------------------------

Il parallelo **rallentera'**: quattro scatole su una macchina sola si dividono
la stessa scheda grafica e gli stessi processori.  ⛔ **Un rallentamento non e'
un disturbo**, e chiamarlo rosso renderebbe questa maglia rossa a vuoto — cioe'
la farebbe spegnere (§1.3).

⇒ ⭐ Il tempo si MISURA e si STAMPA lo stesso, perche' serve a chi scrive il
  gancio: §5.1 gli mette un tetto di **3 minuti** per la famiglia veloce, e
  quel tetto si rispetta **tagliando prove**, non alzandolo.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ sole e in parallelo danno lo stesso esito, e le porte non si pestano
  1  ⛔ almeno una scatola cambia esito, o due si pestano una porta ⇒ rosso
  3  ⛔ non ho potuto guardare (podman non c'e', meno di due scatole hanno
     dato un'impronta) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# ⛔ LE SOGLIE E I NUMERI DICHIARATI QUI, e stampati in ogni esito: «non si
#    disturbano» e' un verdetto, e un verdetto senza il suo metro e' un'opinione.
# ---------------------------------------------------------------------------
DESKTOP = ("gnome", "kde", "xfce", "lxqt")

# ⚠ Le porte NON si inventano qui: sono quelle che assegna `11-accendi.sh`, e
#   questa maglia le ricopia per poterle CONTROLLARE.  ⛔ Se un giorno divergono,
#   il controllo delle porte guarderebbe porte che nessuno usa — ed e' per questo
#   che la prova 1.1 verifica che il server abbia detto di ascoltare proprio li'.
PORTA = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}

# quanto si aspetta un giro della prova (uno solo, non tutti)
TETTO_PROVA_S = 600
# quanto si aspetta che un server dica di essere pronto
TETTO_SERVER_S = 40
# ⚠ il tetto del gancio, che questa maglia non fa rispettare: lo MISURA e basta
TETTO_GANCIO_S = 180
# ⚠ il tetto che C8 si da' per uno scatto: si ricopia qui SOLO per poter dire a
#   chi legge da dove viene l'attesa fissa nei tempi col guasto innestato.
#   ⛔ Non lo impone questa maglia: lo impone C8, ed e' la sua opzione
#   `--attesa-scatto`.
TETTO_SCATTO_C8_S = 120


# ═══════════════════════════════════════════════════════════════════════════
# GLI ATTREZZI — ⛔ e niente `sh -c` annidati (`LEZIONI.md` §1.46)
# ═══════════════════════════════════════════════════════════════════════════
def podman(*argomenti, tetto=120):
    """Chiama podman per percorso, e torna (codice, uscita).

    ⛔ Un comando annidato dentro tre livelli di virgolette puo' perdersi per
       strada, **non eseguire niente e restituire 0** — cioe' un verde senza
       nessuna misura sotto.  ⇒ Qui si chiama il programma, non una shell.
    """
    try:
        p = subprocess.run(["podman", *argomenti], capture_output=True,
                           text=True, timeout=tetto)
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def dentro(scatola, *comando, tetto=120):
    """Fa girare un programma DENTRO la scatola, per percorso assoluto."""
    return podman("exec", scatola, *comando, tetto=tetto)


def accesa(scatola):
    c, out = podman("inspect", "-f", "{{.State.Running}}", scatola, tetto=60)
    return c == 0 and out.strip() == "true"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ L'IMPRONTA DI UN GIRO — che cosa si confronta, esattamente
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ NON si confronta il testo che C8 stampa: cambierebbe l'impronta a ogni
#    ritocco di una frase, e la maglia diventerebbe rossa a vuoto.
# ⭐ Si confrontano i CONTI e il CODICE D'USCITA: sono il giudizio, e il
#    giudizio e' quel che deve restare uguale.
RIGA_A = re.compile(
    r"A · il browser rende la pagina\s*:\s*(\d+) si' · ⛔ (\d+) no · (\d+) non giudicati")


def impronta(testo, codice):
    """Dal registro di un giro di C8 tira fuori l'impronta del suo GIUDIZIO.

    ⛔ Torna **`None`** se il giro non ha prodotto nessuna riga di riepilogo —
       e `None` non e' un'impronta: e' *«non ho guardato»*.  ⚠ Un giro che non
       ha stampato niente NON e' un giro riuscito (`LEZIONI.md` §1.46).
    """
    if not testo:
        return None
    m = RIGA_A.search(testo)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), codice)


def dillo(imp):
    if imp is None:
        return "non lo so"
    return "%d si' %d no %d ign · uscita %s" % imp


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDICE — e le due trappole che deve schivare
# ═══════════════════════════════════════════════════════════════════════════
def giudica(sole, insieme, quante_in_parallelo=None):
    """Confronta le impronte «sola» e «in parallelo», scatola per scatola.

    Torna:
      `None`   ⛔ non ho potuto guardare
      lista    le scatole che hanno CAMBIATO esito (vuota = nessuna e' cambiata)

    ⛔⛔ `quante_in_parallelo` e' quante scatole hanno **PARTECIPATO** al giro
       insieme, non quante hanno risposto — e la differenza e' sostanziale.
       `[M]` La prima stesura contava quelle che avevano risposto, e la
       certificazione l'ha bocciata: ⚠ **una scatola che gira e non riesce a
       riferire sta comunque occupando la macchina.**  ⇒ Il carico c'e' lo
       stesso, e buttare via il giudizio delle altre sarebbe buttare via una
       misura vera.

    Le due condizioni per cui non si giudica:
      · **meno di due scatole nel parallelo** ⇒ con una sola la parola
        «parallelo» non vuol dire niente (stessa ragione per cui C11 rifiuta
        di chiamare «allineata» una scatola sola);
      · **nessuna scatola confrontabile** ⇒ non c'e' niente da confrontare.

    ⛔⛔ E la trappola di `LEZIONI.md` §1.47: una scatola che non ha risposto
       **ne' da sola ne' in parallelo** ha due `None` uguali — e un confronto
       ingenuo direbbe «uguale».  ⇒ Qui non e' uguale: e' **non giudicata**, e
       non entra ne' fra i verdi ne' fra i rossi.
    """
    nomi = sorted(set(sole) | set(insieme))
    if quante_in_parallelo is None:
        quante_in_parallelo = len(insieme)
    giudicabili = [n for n in nomi
                   if sole.get(n) is not None and insieme.get(n) is not None]
    if quante_in_parallelo < 2 or not giudicabili:
        return None
    return [n for n in giudicabili if sole[n] != insieme[n]]


def non_giudicate(sole, insieme):
    nomi = sorted(set(sole) | set(insieme))
    return [n for n in nomi
            if sole.get(n) is None or insieme.get(n) is None]


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — si dimostra che il giudice SA dare rosso
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ E si dichiara che cosa copre e che cosa no.

    COPRE: il confronto fra le impronte — che una differenza si veda, che
    l'uguaglianza sia verde, ⛔ che una scatola muta sia «non lo so» e non
    «uguale», e che una scatola sola non passi per un parallelo.
    ⛔ NON COPRE: che le scatole si disturbino davvero.  Quello lo dice il
    giro sul vero, e la prova delle porte in parte 1.
    """
    U = (2, 0, 0, 0)          # l'esito con la cura:      2 si', 0 no
    G = (1, 1, 0, 0)          # l'esito col guasto:       1 si', 1 no
    casi = [
        ("due scatole, stesso esito sole e insieme",
         {"a": G, "b": G}, {"a": G, "b": G}, 0),
        ("⭐ una scatola cambia esito in parallelo",
         {"a": G, "b": G}, {"a": G, "b": U}, 1),
        ("tutt'e due cambiano",
         {"a": G, "b": G}, {"a": U, "b": U}, 2),
        ("⛔ cambia solo il CODICE d'uscita: e' un giudizio diverso",
         {"a": G, "b": G}, {"a": G, "b": (1, 1, 0, 1)}, 1),
        ("una scatola non ha risposto DA SOLA ⇒ non giudicata, non uguale",
         {"a": G, "b": None}, {"a": G, "b": G}, 0),
        ("⭐ una sola confrontabile BASTA: l'altra faceva carico lo stesso",
         {"a": G, "b": None, "c": None}, {"a": G, "b": None, "c": None}, 0),
        ("⛔ e se quella confrontabile CAMBIA, e' rosso anche cosi'",
         {"a": G, "b": None}, {"a": U, "b": None}, 1),
        ("⛔ una scatola sola non e' un parallelo",
         {"a": G}, {"a": G}, None),
        ("⛔ nessuna scatola ha risposto ⇒ niente da confrontare",
         {"a": None, "b": None}, {"a": None, "b": None}, None),
        ("tre d'accordo e una muta: si giudicano le tre",
         {"a": G, "b": G, "c": G, "d": None},
         {"a": G, "b": G, "c": G, "d": None}, 0),
    ]
    print("== certificazione del giudice di C14 ==")
    print("   impronta = (quanti si', quanti no, quanti non giudicati, codice uscita)")
    print("   ⛔ e un giro senza riga di riepilogo NON e' un'impronta: e' «non lo so»\n")
    guai = 0
    for nome, sole, ins, atteso in casi:
        r = giudica(sole, ins)
        otten = None if r is None else len(r)
        ok = otten == atteso
        print("  %s  %-62s  cambiate=%s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if otten is None else otten,
                 "non lo so" if atteso is None else atteso))
        if not ok:
            guai += 1

    # ⛔ E il lettore dell'impronta si certifica a parte: e' lui che decide se
    #    un giro «ha parlato».  Un lettore che tornasse (0,0,0) invece di None
    #    su un registro muto trasformerebbe «non ho guardato» in «zero», che e'
    #    la ferita numero uno di questo progetto.
    print()
    letture = [
        ("un riepilogo vero",
         "  A · il browser rende la pagina    : 1 si' · ⛔ 1 no · 0 non giudicati\n",
         0, (1, 1, 0, 0)),
        ("un riepilogo con dei non giudicati",
         "  A · il browser rende la pagina    : 0 si' · ⛔ 0 no · 2 non giudicati\n",
         3, (0, 0, 2, 3)),
        ("⛔ registro MUTO ⇒ None, non (0,0,0)", "", 0, None),
        ("⛔ registro che parla d'altro ⇒ None",
         "podman: comando non trovato\n", 127, None),
        ("⚠ solo la riga B non basta: si guarda A",
         "  B · e la pagina si vede DAL CLIENTE: 0 si' · ⛔ 0 no · 2 non giudicati\n",
         0, None),
    ]
    for nome, testo, codice, atteso in letture:
        got = impronta(testo, codice)
        ok = got == atteso
        print("  %s  %-62s  letto=%s" % ("OK " if ok else "NO ", nome, dillo(got)))
        if not ok:
            guai += 1

    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede il cambio d'esito, dice verde quando non c'e',")
    print("   ⛔ e non scambia «non ho guardato» per «uguale»")
    print("⚠ e questa certificazione copre IL CONFRONTO, non le scatole (vedi sopra)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 1 — LE PORTE: il prezzo di `--network=host`, messo alla prova
# ═══════════════════════════════════════════════════════════════════════════
def spegni_server(scatola):
    dentro(scatola, "/usr/bin/systemctl", "stop", "rete11-server", tetto=90)
    dentro(scatola, "/usr/bin/systemctl", "reset-failed", "rete11-server", tetto=60)
    dentro(scatola, "/bin/rm", "-f", "/var/lib/rete11/registro.log", tetto=60)


def accendi_server(scatola, porta):
    """Accende il server dentro la scatola sulla porta data.

    ⛔ La riga e' quella di `11-accendi.sh server`, ricopiata pezzo per pezzo
       come ARGOMENTI: nessuna shell in mezzo.
    """
    spegni_server(scatola)
    dentro(scatola, "/bin/mkdir", "-p", "/var/lib/rete11/certificati",
           "/var/lib/rete11/rilievo", tetto=60)
    return dentro(
        scatola, "/usr/bin/systemd-run", "--unit=rete11-server",
        "--working-directory=/opt/remotix",
        "--property=StandardOutput=append:/var/lib/rete11/registro.log",
        "--property=StandardError=append:/var/lib/rete11/registro.log",
        "--property=KillMode=mixed",
        "/opt/remotix/remotix", "--indirizzo", "0.0.0.0", "--nome", "127.0.0.1",
        "--porta", str(porta),
        "--certificati", "/var/lib/rete11/certificati",
        "--pagina", "/opt/remotix/pagina.html",
        "--ban-file", "/var/lib/rete11/ban",
        "--comando-socket", "/var/lib/rete11/comando.sock",
        "--rilievo", "/var/lib/rete11/rilievo", "--parlantina", tetto=90)


def aspetta_pronto(scatola, tetto=TETTO_SERVER_S):
    """⛔ «Acceso» vuol dire QUALCUNO IN ASCOLTO, non «il processo esiste».

    Lezione della fase 10 §1.36: un server col processo vivo e nessuno in
    ascolto passava per acceso.  ⇒ Si aspetta la riga che lo dice, e se non
    arriva si torna il MOTIVO, non un silenzio.
    """
    scadenza = time.time() + tetto
    while time.time() < scadenza:
        c, out = dentro(scatola, "/bin/grep", "-c", "pronto: https",
                        "/var/lib/rete11/registro.log", tetto=60)
        if c == 0 and out.strip().isdigit() and int(out.strip()) > 0:
            return True, ""
        time.sleep(1.0)
    _c, coda = dentro(scatola, "/usr/bin/tail", "-4",
                      "/var/lib/rete11/registro.log", tetto=60)
    return False, (coda or "(registro vuoto)").strip().replace("\n", " ")[:200]


def rifiuto_di_legarsi(scatola, porta):
    """⛔ Il MOTIVO per cui il server non e' partito, non solo il fatto.

    ⚠⚠ E questa funzione e' nata da un rilievo su me stesso.  La prima stesura
       di 1.3 si accontentava di *«l'invasore non ha detto di essere pronto in
       20 secondi»* — ⛔ che e' **debole**: un server lento, o fermo per un
       altro motivo qualunque, avrebbe prodotto lo stesso silenzio, e il banco
       avrebbe scritto «⭐ la separazione funziona» **senza nessuna misura
       sotto**.  ⇒ E' la forma d'errore di `LEZIONI.md` §1.46, vista dal verso
       del verde.

    ⭐ Adesso si pretendono DUE cose insieme:
       · l'unita' del server dev'essere in `failed` — non «in avvio»;
       · nel registro dev'esserci la riga che dice **perche'**:
         `[M]` `⛔ non mi lego a 0.0.0.0:8511 in UDP: Address already in use`.

    Torna (stato, riga) dove `stato` e':
       "rifiutato"  ⭐ si e' fermato E ha detto che la porta era occupata
       "fermo"      ⚠ si e' fermato, ma per un motivo che non e' la porta
       "vivo"       ⛔ non si e' fermato affatto
    """
    _c, attivo = dentro(scatola, "/usr/bin/systemctl", "is-active",
                        "rete11-server", tetto=60)
    _c2, coda = dentro(scatola, "/bin/grep", "-F", "non mi lego",
                       "/var/lib/rete11/registro.log", tetto=60)
    riga = (coda or "").strip().splitlines()
    riga = riga[-1].strip() if riga else ""
    occupata = ("Address already in use" in riga) and (":%d" % porta in riga)
    if (attivo or "").strip() not in ("failed", "inactive"):
        return "vivo", riga
    return ("rifiutato" if occupata else "fermo"), riga


def chi_ascolta(scatola, porta):
    """Chi tiene la porta, visto DA DENTRO questa scatola.

    ⭐ Con `--network=host` le scatole condividono la rete dell'ospite, quindi
      `ss` dentro una scatola vede TUTTE le porte dell'ospite.  ⛔ Ma il nome
      del processo lo puo' risolvere solo per i processi del PROPRIO albero:
      per gli altri vede il socket e non il padrone.
    ⇒ E' esattamente il discriminante che serve: *«questa porta e' MIA?»*
    """
    c, out = dentro(scatola, "/usr/bin/ss", "-ltnp", "sport", "=", ":%d" % porta,
                    tetto=60)
    if c != 0:
        return None
    righe = [r for r in out.splitlines() if ":%d" % porta in r]
    if not righe:
        return "nessuno"
    return "mia" if "users:((" in righe[0] else "di un altro"


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 2 — LA PROVA, sola e in parallelo
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(scatola, a, guasto=None):
    """Un giro della prova A di C8 dentro una scatola. Torna (impronta, secondi)."""
    t0 = time.time()
    if guasto is None:
        guasto = a.guasto
    argomenti = ["python3", "-u", a.prova, "--senza-sessione",
                 "--pagina", a.pagina]
    if guasto:
        argomenti.append("--senza-cura")
    # ⭐ E si possono passare argomenti alla prova, ⛔ e serve per una cosa sola:
    #    per **provare a smentirsi**.  Vedi `--passa` piu' sotto.
    argomenti.extend(shlex.split(a.passa))
    c, out = dentro(scatola, *argomenti, tetto=a.tetto_prova)
    return impronta(out, c), time.time() - t0


def giro_sole(scatole, a, guasto=None):
    """Una scatola per volta. ⛔ E' la linea di partenza: se questa non parla,
       non c'e' niente da confrontare."""
    esiti, tempi = {}, {}
    for s in scatole:
        imp, sec = un_giro(s, a, guasto)
        esiti[s], tempi[s] = imp, sec
        print("     %-14s  %-34s  %6.1f s" % (s, dillo(imp), sec))
    return esiti, tempi


def giro_insieme(scatole, a, guasto=None):
    """Tutte insieme, davvero: si lanciano e poi si aspettano.

    ⚠ `ThreadPoolExecutor` con tanti posti quante sono le scatole: se ne avesse
      meno, le ultime partirebbero **dopo** le prime — e non sarebbe un
      parallelo, sarebbe una fila con un nome ambizioso.
    """
    esiti, tempi = {}, {}
    with ThreadPoolExecutor(max_workers=len(scatole)) as pool:
        futuri = {s: pool.submit(un_giro, s, a, guasto) for s in scatole}
        for s in scatole:
            imp, sec = futuri[s].result()
            esiti[s], tempi[s] = imp, sec
    for s in scatole:
        print("     %-14s  %-34s  %6.1f s" % (s, dillo(esiti[s]), tempi[s]))
    return esiti, tempi


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# PARTE 1-bis — LA SCHEDA GRAFICA, l'unica cosa che si dividono DAVVERO
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ E QUESTA E' LA PARTE CHE MANCAVA, e va detto perche' mancava.
#
# La parte 2 fa girare la prova A di C8, che accende un browser SENZA schermo:
# `[M]` il suo registro dice `RenderCompositorSWGL`, cioe' ⛔ **disegna in
# software e la scheda grafica non la tocca**.  ⇒ Un parallelo che non tocca la
# scheda non puo' dire niente su chi se la contende.
#
# ⚠ E la contesa vera — quattro codificatori insieme sullo stesso nodo — oggi
#   **non si puo' misurare**: ci vorrebbe una sessione viva per scatola, e
#   `[M]` dieci sessioni GNOME nuove su dieci nascono cieche (fase 10 §7.4).
#   ⇒ Quel che si puo' misurare adesso e' lo strato di sotto, che e' comunque
#     la domanda che verrebbe prima: **quattro scatole riescono ad APRIRE il
#     codificatore nello stesso istante?**  Se gia' questo non regge, la
#     contesa vera non ha nemmeno bisogno di essere provata.
def guarda_la_scheda(scatola):
    """Chiede al nodo quanti profili di codifica H.264 espone.

    ⛔ Torna `None` se non ha potuto guardare — e `None` non e' zero: *«non ho
       chiesto»* e *«ha risposto zero profili»* sono due guasti diversi, e il
       secondo e' molto peggio del primo.
    """
    c, out = dentro(scatola, "/usr/bin/vainfo", tetto=90)
    if c is None or not out:
        return None
    n = len([r for r in out.splitlines()
             if "VAProfileH264" in r and "EncSlice" in r])
    if "Driver version" not in out:
        return None
    return n


def parte_scheda(scatole):
    """Torna (guai, ignoti). ⭐ Sole e insieme, come tutto il resto."""
    guai, ignoti = [], []
    print("== PARTE 1-bis — la scheda grafica, sola e con tutte e %d insieme =="
          % len(scatole))
    print("   ⛔ e' l'UNICA cosa che le quattro scatole si dividono davvero:")
    print("      un nodo solo, `/dev/dri/renderD128`, passato dentro a tutte")
    print()
    sole = {}
    for s in scatole:
        sole[s] = guarda_la_scheda(s)
    with ThreadPoolExecutor(max_workers=len(scatole)) as pool:
        futuri = {s: pool.submit(guarda_la_scheda, s) for s in scatole}
        insieme = {s: futuri[s].result() for s in scatole}
    for s in scatole:
        q, i = sole[s], insieme[s]
        segno = "  "
        if q is None or i is None:
            segno = "⚠"
        elif q != i:
            segno = "⛔"
        print("   %s %-14s  sola: %-12s  insieme: %s"
              % (segno, s,
                 "non lo so" if q is None else "%d profili" % q,
                 "non lo so" if i is None else "%d profili" % i))
        if q is None or i is None:
            ignoti.append("%s non ha detto che cosa vede sulla scheda" % s)
        elif q != i:
            guai.append("%s vede %d profili da sola e %d con le altre accese: "
                        "⛔ la scheda non regge quattro scatole insieme"
                        % (s, q, i))
        elif i == 0:
            # ⛔ Zero profili in tutte e due non e' «uguale, quindi va bene»:
            #    e' una scheda che non codifica.  ⚠ Uguale a se stesso e
            #    sbagliato resta sbagliato (`LEZIONI.md` §1.47).
            guai.append("%s non vede NESSUN profilo di codifica, ne' sola ne' "
                        "insieme: il confronto e' «uguale» e il terreno e' "
                        "rotto" % s)
    return guai, ignoti


def parte_porte(scatole, a):
    """Torna (guai, ignoti) — due liste di frasi, vuote se tutto regge.

    ⛔ `ignoti` non e' `guai`: e' *«non ho potuto guardare»*, e per §4.5 non e'
       un rosso — ma **non e' nemmeno un verde**, ed e' per questo che sta in
       una lista sua invece di essere taciuto.
    """
    guai, ignoti = [], []
    print("== PARTE 1 — le porte: il prezzo di `--network=host` ==")
    print("   ⛔ non si legge `11-accendi.sh`: si accendono i server e si guarda")
    print("      chi ascolta davvero (E1: «scritto non e' in vigore»)\n")

    # ── 1.1 · i quattro server, insieme, ciascuno sulla sua porta ──────────
    print("   1.1 · i server accesi INSIEME, ognuno sulla sua porta")
    with ThreadPoolExecutor(max_workers=len(scatole)) as pool:
        list(pool.map(lambda s: accendi_server(s, PORTA[s.split("-")[-1]]),
                      scatole))
    pronti = {}
    for s in scatole:
        ok, perche = aspetta_pronto(s)
        pronti[s] = ok
        print("       %-14s porta %-5d  %s" % (
            s, PORTA[s.split("-")[-1]],
            "⭐ ascolta" if ok else "⛔ non ha detto di essere pronto: %s" % perche))
    if not all(pronti.values()):
        guai.append("almeno un server non e' riuscito ad ascoltare mentre gli "
                    "altri erano accesi")

    # ── 1.2 · e ogni porta e' di CHI DEVE ─────────────────────────────────
    # ⭐ Non basta che quattro porte siano occupate: bisogna che la 8512 sia di
    #   KDE e non di GNOME.  Altrimenti un cliente che crede di parlare con un
    #   desktop parlerebbe con un altro — ⛔ e sarebbe un guasto travestito da
    #   guasto del prodotto.
    print("\n   1.2 · e ogni porta e' della scatola giusta")
    for s in scatole:
        mia = chi_ascolta(s, PORTA[s.split("-")[-1]])
        altrui = [chi_ascolta(s, PORTA[t.split("-")[-1]])
                  for t in scatole if t != s]
        ok = (mia == "mia") and all(x in ("di un altro", "nessuno", None)
                                    for x in altrui)
        print("       %-14s la sua: %-12s  le altre: %s"
              % (s, mia, ", ".join(str(x) for x in altrui)))
        if mia != "mia":
            guai.append("%s non riconosce come propria la porta %d"
                        % (s, PORTA[s.split("-")[-1]]))

    # ── 1.3 · ⛔ IL ROVESCIO: due scatole sulla STESSA porta ───────────────
    # ⛔ E' la prova che vale piu' delle altre due: se mettere due server sulla
    #   stessa porta NON facesse male, allora «una porta per scatola» non
    #   separerebbe niente, e il prezzo scritto in `11-accendi.sh` sarebbe una
    #   rassicurazione senza misura sotto.
    print("\n   1.3 · ⛔ il rovescio: due scatole sulla STESSA porta")
    if len(scatole) < 2:
        print("       ⚠ meno di due scatole: non lo posso provare")
    else:
        vittima, invasore = scatole[0], scatole[1]
        porta_contesa = PORTA[vittima.split("-")[-1]]
        spegni_server(invasore)
        accendi_server(invasore, porta_contesa)
        ok, _perche = aspetta_pronto(invasore, tetto=20)
        stato, riga = rifiuto_di_legarsi(invasore, porta_contesa)
        if ok or stato == "vivo":
            print("       ⛔⛔ %s ha preso la %d, che era di %s"
                  % (invasore, porta_contesa, vittima))
            guai.append("due scatole possono prendersi la stessa porta senza "
                        "che nessuno se ne accorga: ⛔ la separazione per porta "
                        "NON separa")
        elif stato == "rifiutato":
            print("       ⭐ %s NON e' riuscito a prendere la %d (di %s), e ha"
                  % (invasore, porta_contesa, vittima))
            print("          detto PERCHE':")
            print("          %s" % riga[:150])
            print("       ⭐ ⇒ la separazione per porta e' una separazione VERA:")
            print("          il prezzo di `--network=host` e' scritto giusto")
        else:
            # ⛔ Si e' fermato, ma non per la porta.  ⚠ Chiamarlo verde sarebbe
            #    festeggiare un silenzio: non ho la prova che sia stata la porta.
            print("       ⚠ %s non e' partito, ⛔ ma NON ha detto che la porta era"
                  % invasore)
            print("          occupata ⇒ non so se e' stata la porta a fermarlo.")
            print("          registro: %s" % (riga[:150] or "(nessuna riga «non mi lego»)"))
            ignoti.append("non ho la prova che sia la porta a impedire "
                          "l'invasione: l'invasore si e' fermato senza dirlo")
        # ⚠ E si rimette a posto, o la parte 2 partirebbe da un terreno sporco.
        spegni_server(invasore)
        accendi_server(invasore, PORTA[invasore.split("-")[-1]])
        rimesso, _ = aspetta_pronto(invasore)
        if not rimesso:
            ignoti.append("dopo la prova dell'invasione %s non e' tornato ad "
                          "ascoltare la sua porta" % invasore)
        else:
            print("       ⭐ e %s e' tornato sulla sua porta %d"
                  % (invasore, PORTA[invasore.split("-")[-1]]))
    return guai, ignoti


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--desktop", default=",".join(DESKTOP))
    p.add_argument("--prefisso", default="rete11-")
    p.add_argument("--prova",
                   default="/rete11/11-c8-il-secondo-apre-il-browser.py",
                   help="la prova che si fa girare sola e in parallelo")
    p.add_argument("--pagina", default="/rete11/11-c8-pagina.html")
    p.add_argument("--guasto", action="store_true", default=True,
                   help="usa C8 col guasto innestato: ⭐ il suo esito porta "
                        "dentro un verde E un rosso, cioe' e' un'impronta che "
                        "si puo' rompere in due modi")
    p.add_argument("--senza-guasto", dest="guasto", action="store_false")
    p.add_argument("--tetto-prova", type=int, default=TETTO_PROVA_S)
    p.add_argument("--senza-riscaldamento", action="store_true",
                   help="⛔ salta il giro che si butta. ⚠ Solo per diagnosi: "
                        "senza, il parallelo parte con la memoria gia' calda")
    # ⚠ UNA STRINGA SOLA, e non `nargs="*"`: `[M]` con `nargs` argparse si
    #   ferma al primo argomento che comincia per `--` e lo rifiuta come
    #   proprio.  ⇒ Si passa fra virgolette e si spezza qui.
    p.add_argument("--passa", default="", metavar="\"--a 1 --b 2\"",
                   help="⭐ argomenti da girare alla prova, fra virgolette. "
                        "⛔ Non e' una comodita: serve a PROVARE A SMENTIRSI. "
                        "Con un tetto stretto (`--passa \"--attesa-scatto 3\"`) "
                        "la contesa diventa decisiva, e si vede se questo banco "
                        "sa accorgersene")
    p.add_argument("--smentisci", action="store_true",
                   help="⛔⛔ LA CONTRO-PROVA SU DATI VERI: fa girare il "
                        "parallelo con l'ALTRO modo di C8, cosi' le due "
                        "impronte devono essere diverse. ⭐ Questa maglia DEVE "
                        "diventare ROSSA; se resta verde non sa vedere un "
                        "cambio d'esito, e ogni suo verde non vale niente")
    p.add_argument("--solo-porte", action="store_true",
                   help="solo la scheda grafica e le porte, senza il giro lungo")
    p.add_argument("--solo-esito", action="store_true")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    try:
        subprocess.run(["podman", "--version"], capture_output=True, timeout=30)
    except OSError:
        print("⛔ podman non c'e': ⇒ non ho potuto guardare")
        sys.exit(3)

    nomi = [a.prefisso + d for d in a.desktop.split(",") if d]
    scatole = [n for n in nomi if accesa(n)]

    print("== C14 — le scatole si disturbano? ==")
    print("   ⭐ §3.4 lo AFFERMA; questa maglia lo MISURA (§4.2)")
    print("   prova: %s%s%s" % (
        a.prova.split("/")[-1],
        "  --senza-cura (guasto innestato)" if a.guasto else "",
        ("  " + a.passa) if a.passa else ""))
    print("   tetti dichiarati: un giro %d s · un server pronto %d s"
          % (a.tetto_prova, TETTO_SERVER_S))
    print("   ⚠ il tempo NON e' un verdetto: si misura e si stampa, e basta\n")
    for n in nomi:
        print("   %-14s %s" % (n, "accesa" if n in scatole else "⛔ spenta"))
    print()
    if len(scatole) < 2:
        print("⛔ scatole accese: %d — ⭐ e con UNA SOLA la parola «parallelo»"
              % len(scatole))
        print("   non vuol dire niente.  ⇒ non ho potuto guardare")
        sys.exit(3)

    guai_porte, ignoti_porte = [], []
    if not a.solo_esito:
        g1, i1 = parte_scheda(scatole)
        print()
        g2, i2 = parte_porte(scatole, a)
        guai_porte, ignoti_porte = g1 + g2, i1 + i2
        print()

    if a.solo_porte:
        if guai_porte:
            print("⛔⛔ ROSSO — le porte si pestano:")
            for g in guai_porte:
                print("   · %s" % g)
            return 1
        if ignoti_porte:
            print("⛔ non ho potuto guardare fino in fondo:")
            for g in ignoti_porte:
                print("   · %s" % g)
            return 3
        print("⭐ la scheda regge quattro scatole insieme, e le porte non si")
        print("   pestano: ognuna e' della sua scatola, e due non possono")
        print("   prendersi la stessa")
        return 0

    # ═══ PARTE 2 ═══════════════════════════════════════════════════════════
    print("== PARTE 2 — la stessa prova, sola e in parallelo ==")
    if not a.senza_riscaldamento:
        # ⛔ IL GIRO CHE SI BUTTA, e va dichiarato perche' si butta.
        #    Il primo avvio di Firefox e' piu' lento: senza questo giro, il
        #    parallelo partirebbe con la memoria dell ospite calda ⇒ ⛔ un
        #    confronto truccato **a favore** del parallelo, cioe' proprio nel
        #    verso in cui questa maglia potrebbe sbagliare.
        print("\n   0 · giro di RISCALDAMENTO, e si BUTTA")
        print("       (il primo avvio del browser e' piu' lento: senza, il")
        print("        parallelo partirebbe avvantaggiato)")
        t0 = time.time()
        giro_insieme(scatole, a)
        print("       buttato, %.1f s\n" % (time.time() - t0))

    print("   1 · SOLE, una per volta")
    t0 = time.time()
    sole, tempi_sole = giro_sole(scatole, a)
    tot_sole = time.time() - t0
    print("       totale: %.1f s\n" % tot_sole)

    print("   2 · INSIEME, tutte e %d%s"
          % (len(scatole),
             "   ⛔⛔ CON LA PROVA CAMBIATA APPOSTA (--smentisci)"
             if a.smentisci else ""))
    t0 = time.time()
    # ⛔⛔ `--smentisci` FA CAMBIARE LA PROVA fra i due arrangiamenti.
    #
    # ⭐ E' la contro-prova che `--certifica` NON puo' dare: la certificazione
    #    lavora su casi FINTI, e dimostra che il confronto sa vedere una
    #    differenza **quando gliela si mette in mano**.  ⛔ Non dimostra che la
    #    catena vera — `podman exec`, la lettura del registro, il confronto —
    #    sappia produrre un rosso su dati VERI.
    # ⇒ Con `--smentisci` l'arrangiamento «insieme» gira con l'altro modo di
    #   C8, quindi le due impronte DEVONO essere diverse e questa maglia DEVE
    #   diventare rossa.  ⚠ Se resta verde, non e' capace di vedere un cambio
    #   d'esito, e ogni suo verde precedente non vale niente.
    insieme, tempi_ins = giro_insieme(
        scatole, a, guasto=(not a.guasto) if a.smentisci else None)
    tot_ins = time.time() - t0
    print("       totale: %.1f s\n" % tot_ins)

    # ── il confronto ──────────────────────────────────────────────────────
    print("   ⭐ IL CONFRONTO — impronta = (si', no, non giudicati, uscita)")
    print("     %-14s  %-30s  %-30s" % ("scatola", "sola", "insieme"))
    for s in scatole:
        uguale = (sole.get(s) is not None and insieme.get(s) is not None
                  and sole[s] == insieme[s])
        muta = sole.get(s) is None or insieme.get(s) is None
        segno = "⚠" if muta else ("  " if uguale else "⛔")
        print("   %s %-14s  %-30s  %-30s" % (segno, s, dillo(sole.get(s)),
                                             dillo(insieme.get(s))))
    print()

    # ── il tempo, che NON e' un verdetto ──────────────────────────────────
    print("   ⚠ IL TEMPO (informazione, non verdetto)")
    if a.guasto:
        # ⛔⛔ E QUI IL NUMERO VA LETTO CON UNA RISERVA, o inganna.
        #
        # `[M]` 26 agosto 2026, giro di riscaldamento: quattro scatole insieme
        # hanno fatto **125,9 · 126,0 · 126,0 · 126,1 s**.  ⚠ Quattro numeri
        # uguali a un decimo non sono un caso: ⛔ col guasto innestato il
        # SECONDO inquilino non apre il browser, e C8 lo aspetta per il suo
        # tetto dichiarato — che oggi vale **120 s**.
        # ⇒ ⛔ **Il tempo di questo giro e' quasi tutto un'ATTESA FISSA**, non
        #   lavoro: sommarci sopra un «×quanto rallenta» vorrebbe dire misurare
        #   il nostro stesso tetto e chiamarlo contesa.
        # ⭐ Il tempo pulito si prende con `--senza-guasto`, dove tutt'e due gli
        #   inquilini riescono e nessuno aspetta un tetto.
        print("     ⛔ RISERVA: col guasto innestato il secondo inquilino NON apre")
        print("        il browser, e C8 lo aspetta per il suo tetto (%d s)."
              % TETTO_SCATTO_C8_S)
        print("        ⇒ questi tempi sono quasi tutti ATTESA FISSA, non lavoro.")
        print("        ⭐ Il tempo pulito si prende con `--senza-guasto`.")
    piu_lenta = max((tempi_ins[s] for s in scatole), default=0)
    piu_lenta_sola = max((tempi_sole[s] for s in scatole), default=0)
    for s in scatole:
        q = tempi_sole[s]
        i = tempi_ins[s]
        print("     %-14s  sola %6.1f s   insieme %6.1f s   %s"
              % (s, q, i, ("×%.2f" % (i / q)) if q > 0 else "?"))
    print("     %-14s  sola %6.1f s   insieme %6.1f s"
          % ("TUTTE", tot_sole, tot_ins))
    if tot_ins > 0:
        print("     ⭐ il parallelo fa risparmiare ×%.2f sul totale" % (tot_sole / tot_ins))
    print("     ⚠ la piu' lenta in parallelo: %.1f s (da sola la piu' lenta: %.1f s)"
          % (piu_lenta, piu_lenta_sola))
    # ⚠ E il rimando al gancio: e' l'unico posto dove questo numero serve.
    print("     ⇒ il gancio (§5.1) ha un tetto di %d s per la famiglia veloce: "
          "questo giro %s"
          % (TETTO_GANCIO_S,
             "ci sta dentro" if piu_lenta <= TETTO_GANCIO_S else
             "⛔ NON ci sta dentro ⇒ si tagliano prove, non si alza il tetto"))
    print()

    # ── il verdetto ───────────────────────────────────────────────────────
    r = giudica(sole, insieme, quante_in_parallelo=len(scatole))
    mute = non_giudicate(sole, insieme)
    if mute:
        print("⚠ ⛔ %d scatole non giudicate — e una scatola muta NON e' «uguale»"
              % len(mute))
        for s in mute:
            print("     · %-14s  sola: %-18s  insieme: %s"
                  % (s, dillo(sole.get(s)), dillo(insieme.get(s))))
        print("   ⇒ `LEZIONI.md` §1.47: «?» uguale a «?» passerebbe il confronto")
        print("     senza aver guardato niente.\n")

    if ignoti_porte:
        print("⚠ ⛔ e sulle porte non ho potuto guardare fino in fondo:")
        for g in ignoti_porte:
            print("     · %s" % g)
        print()
    if r is None:
        print("⛔ non c'e' abbastanza per confrontare: o il parallelo aveva meno")
        print("   di due scatole, o nessuna e' confrontabile.")
        print("   ⇒ non ho potuto guardare")
        return 3
    if a.smentisci:
        # ⛔ Con la prova cambiata apposta l'esito si LEGGE AL CONTRARIO: qui il
        #    verde e' un fallimento del banco.
        print()
        if r:
            print("⭐ LA CONTRO-PROVA E' RIUSCITA: con la prova cambiata apposta")
            print("   questa maglia e' diventata rossa su %d scatole su %d."
                  % (len(r), len(scatole)))
            print("   ⇒ sa vedere un cambio d'esito su dati VERI, non solo nei")
            print("     casi finti di `--certifica`")
            return 0
        print("⛔⛔ LA CONTRO-PROVA E' FALLITA: le due impronte dovevano essere")
        print("    diverse e questa maglia non se n'e' accorta.")
        print("    ⇒ ogni suo verde precedente non vale niente.")
        return 1
    if r or guai_porte:
        print("⛔⛔ ROSSO — le scatole si disturbano:")
        for s in r:
            print("   · %-14s sola %s   ⇒   insieme %s"
                  % (s, dillo(sole[s]), dillo(insieme[s])))
        for g in guai_porte:
            print("   · %s" % g)
        print()
        print("   ⇒ finche' e' cosi', ⛔ **far girare le quattro scatole insieme")
        print("     non e' un risparmio: e' un modo di prendere numeri falsi**")
        print("     (§3.4, che questa maglia esiste per mettere alla prova).")
        return 1
    confrontate = [s for s in scatole if s not in mute]
    print("⭐ le %d scatole confrontate danno LO STESSO esito sole e in parallelo,"
          % len(confrontate))
    print("   e le porte non si pestano.")
    if mute:
        # ⛔ E QUI NON SI DICE VERDE, e la ragione sta in §4.5: `3` vuol dire
        #    *«ho misurato, e qualche pezzo non ha potuto parlare»*.  ⚠ Dire
        #    `0` con tre scatole su quattro mute sarebbe far passare una
        #    risposta PARZIALE per una risposta piena.
        print("⛔ ma %d scatole su %d non hanno parlato: la risposta e' PARZIALE."
              % (len(mute), len(scatole)))
        print("   ⇒ non giudico (§4.5, esito 3)")
        return 3
    if ignoti_porte:
        print("⛔ ma sulle porte qualcosa non l'ho potuto guardare ⇒ non giudico")
        return 3
    print("⚠ ⇒ §3.4 non e' piu' un'affermazione: e' `[M]`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
