#!/usr/bin/env python3
"""01-b8-sblocca.py — ⛔ IL COMANDO DI SBLOCCO di `RCP.md` §4.4-bis, dal lato di
chi comanda.

    python3 01-b8-sblocca.py --socket /srv/src/remotix-comando.sock 192.168.0.2
    python3 01-b8-sblocca.py --socket /srv/src/b8-comando.sock --ping
    python3 01-b8-sblocca.py --socket ... --pretendi TOLTO 127.0.0.1
    python3 01-b8-sblocca.py --socket ... --pretendi-chi remotix \\
                             --ban-file /srv/src/remotix-ban 192.168.0.2

===========================================================================
⛔ A CHE COSA SERVE, E PERCHE' NON E' SOLO DI B8

`RCP.md` §4.4-bis: «si esce in due modi, non uno — la scadenza naturale, oppure
un **comando di sblocco sul server**».  E `FASI.md` §01-filo-nudo regola **B0.3**
lo rende il **vincolo piu' duro del capitolo**: il conto dei tentativi e' per
indirizzo, tutti i banchi partono dallo stesso indirizzo, e ⛔ *«B7 fallisce un
tentativo, B8 ne fallisce tre, e da li' in poi ogni banco di quella macchina e'
fuori per dodici ore — compresi B10, B11 e chi sta sviluppando»*.

⭐ Quindi questo file e' **lo strumento di B0.3**, non un pezzo di B8: lo chiama
   chiunque debba rimettere in piedi la macchina fra un banco e l'altro.  ⛔ E
   chi lo chiama **lo dichiara**, o «il ban non e' scattato» e «qualcuno l'ha
   tolto» hanno lo stesso aspetto — che e' la ragione per cui questo programma
   stampa sempre **quale delle due** risposte ha ricevuto, e non un semplice
   «fatto».

===========================================================================
⛔ TRE ESITI, NON DUE

    TOLTO         il ban c'era, e adesso non c'e' piu'
    NON-BANNATO   non c'era niente da togliere
    (nessuna)     ⛔ non ho potuto parlare col comando

⛔ Il terzo e' quello che conta di piu', ed e' quello che un programma scritto in
   fretta confonde col secondo: un socket assente, un server spento, un percorso
   sbagliato **non sono** «non era bannato».  Chi li confondesse dichiarerebbe
   «la macchina e' pulita» dopo non aver parlato con nessuno — `LEZIONI.md` §1.9,
   e la faccia comune di vuoto e proibito.

⛔⭐ E IL TERZO ESITO HA UNA QUARTA FACCIA, TROVATA L'11 AGOSTO 2026 — la piu'
     insidiosa, perche' e' l'unica che risponde:

    **ho parlato con un server, ma non con QUELLO** — cioe' il ban e' ancora vivo
    nel processo che serve, e io ho appena ricevuto un «NON-BANNATO» da un altro.

⚠ Non e' un caso di scuola: su questa macchina i **due** server esistono insieme
  — l'innesto `bsslserver` sulla 7447 e il prodotto `remotix` sulla 7448 — e fino
  a oggi il predefinito di `--socket` era il socket **dell'innesto**.  Chi
  sbloccava «per il prodotto» senza scrivere il percorso parlava con l'altro,
  riceveva `PONG` e `NON-BANNATO`, e usciva **0** dichiarando pulita una macchina
  che era ancora fuori per dodici ore.  ⛔ Il `PING` non lo vede: dice *«qualcuno
  risponde»*, non *«risponde quello giusto»*.

Le tre cure, e sono indipendenti l'una dall'altra:

    1. ⛔ `--socket` NON HA PIU' UN PREDEFINITO.  Il percorso si scrive, sempre.
       Un predefinito che punta a uno dei due server e' una scelta presa da chi
       ha scritto lo strumento al posto di chi misura, e presa in silenzio.
    2. ⭐ CHI HA RISPOSTO SI CHIEDE AL NUCLEO, non al server: `SO_PEERCRED` su un
       socket di dominio Unix consegna **pid, uid e gid del processo dall'altro
       capo**, e da li' `/proc/<pid>/comm` dice se si chiama `remotix` o
       `bsslserver`.  ⛔ E' `CODER.md` §3.7 — *«non si deduce il mittente: lo si
       chiede al nucleo»* — e vale piu' di qualunque risposta che il server
       potesse mandare da se': una stringa nel protocollo la scrive il server,
       il pid lo scrive il kernel.  ⚠ Per questo NON si e' aggiunto nessun verbo
       nuovo al protocollo: `RCP.md` §4.4-bis e `FASI.md` §01-filo-nudo promettono
       che i due server parlino **lo stesso protocollo byte per byte**, e un
       verbo che uno solo dei due capisce sarebbe stata la forma **E2** di
       `REVIEWER.md` — due comportamenti sotto la stessa etichetta.  Il
       protocollo non e' cambiato di un byte.
    3. ⭐ `--ban-file` GUARDA L'ALTRA META' DI §4.4-bis: il ban vive in due posti
       — la memoria del processo che serve e il file che sopravvive al riavvio —
       e finora questo strumento ne interrogava **uno**.  Con `--ban-file` si
       legge il file **prima e dopo**, e le due letture si confrontano.

===========================================================================
⛔ CHE COSA SI PRETENDE, E CHE COSA DICE NO  (regola B0.4)

*«L'atteso lo confronta il banco, non chi legge»*: si stampa **e** si confronta.

    --pretendi TOLTO|NON-BANNATO   l'esito dello sblocco
    --pretendi-chi NOME            il nome del processo che ha risposto
                                   (`remotix` per il prodotto, `bsslserver` per
                                   l'innesto): sottostringa di `/proc/<pid>/comm`
                                   o della riga di comando
    --pretendi-pid N               il pid esatto — ⭐ e' la forma piu' dura, ed e'
                                   quella che si usa quando il server l'ha acceso
                                   lo script che chiama questo comando e il pid
                                   se l'e' segnato
    --ban-file PATH                il file dei ban da guardare prima e dopo

⭐ E il controllo che dice **no**, sul file dei ban: se prima dello sblocco la
   chiave nel file **non c'era**, allora «dopo non c'e'» non dimostra niente —
   il lettore non ha mai trovato niente, quindi non si sa se sappia trovare
   (`LEZIONI.md` §1.9 regola 2, il controllo positivo sullo stesso strumento).
   Questo programma lo dice invece di tacerlo, e non chiama verde quel giro.

===========================================================================
⛔ GLI STATI D'USCITA — ognuno e' un fatto diverso

    0   ho parlato, e l'esito e' quello atteso (o non ne pretendevo nessuno)
    2   uso sbagliato: manca `--socket`, oppure manca l'indirizzo
    3   ⛔ NON HO PARLATO CON NESSUNO — il terzo esito, quello che conta
    4   ho parlato, ma l'esito (o chi ha risposto) non e' quello preteso — B0.4
    5   ⛔ memoria e file dei ban si CONTRADDICONO: lo sblocco non e' durato, o il
        server che ho sbloccato non e' quello che scrive quel file
    6   ⚠ non ho potuto leggere il file dei ban: la verifica su file **non e'
        stata fatta**, e non e' un «pulito»

⚠ Quando piu' d'uno di questi fatti e' vero insieme, sullo schermo ci sono
  **tutte** le righe e lo stato d'uscita porta il piu' grave: il file dei ban
  (5, 6) vince sul confronto dell'atteso (4), perche' dice che il ban c'e'
  ancora e non solo che non era quel che aspettavo.

===========================================================================
⭐ CHE COSA DI QUESTO FILE E' STATO MISURATO, E CON CHE DENOMINATORE

`[M]` **11 agosto 2026, su CHUWI** — ⛔ **non** contro il prodotto acceso, che e'
il giro che resta da fare.  Il banco era `src/comando.c` **compilato per davvero**
(`gcc -std=gnu11 -D_GNU_SOURCE -Wall -Wextra`) e legato a un `rcp` finto di
quaranta righe, in cui `rcp_chiave_indirizzo()` e' la **copia esatta** di quella
di `src/rcp.c` e `rcp_sblocca()` toglie da una lista e riscrive un file nello
stesso formato.  ⚠ Quel che quel banco NON prova e' il ban vero: che a bannare
sia `segna_fallito()` e che la tabella sia quella del processo che serve.

Diciassette casi, e ciascuno con il suo esito atteso:

    PING → PONG · SBLOCCA → TOLTO · di nuovo → NON-BANNATO · `--pretendi` che
    dice NO (esce 4) · `--pretendi-chi` sul server giusto e sul server sbagliato
    (0 e 4) · `--pretendi-pid` (0 e 4) · socket assente · socket abbandonato
    (nessuno ascolta) · file che non e' un socket · ⭐ **cartella non
    attraversabile** · server che risponde in un'altra lingua · server che
    accetta e tace · riga vuota · `SBLOCCA` senza indirizzo · `SBLOCCA` con soli
    spazi · `\r\n` invece di `\n` · `[192.168.0.2]` invece di `192.168.0.2`

⭐ E i due controlli che dicono **no**, perche' un elenco di casi verdi non e' una
   prova: *(1)* lo sblocco dato al server **sbagliato** — due processi accesi
   insieme, il ban su uno e il comando all'altro — e' l'unico caso che senza
   `--ban-file` e senza `--pretendi-chi` esce **0** dicendo «non era bannato»;
   con l'uno esce **5**, con l'altro **4**.  *(2)* La chiave digitata in due
   forme (`192.168.0.2` e `[192.168.0.2]`) arriva alla **stessa** voce: il primo
   comando risponde `TOLTO`, il secondo `NON-BANNATO`.

===========================================================================
⚠ DA DOVE SI CHIAMA, E CHE CHIAVE CHIEDE

Il socket sta nel filesystem con permessi **0600** e appartiene a chi ha acceso
il server — che nei banchi e' **root dentro il contenitore**.  ⭐ E' voluto:
§4.4-bis dice che questo comando *«chiede l'unica chiave che quel caso ammette —
l'accesso alla macchina»*, e un socket leggibile da chiunque la renderebbe
«l'accesso a un utente qualunque della macchina», che e' una chiave diversa e
piu' facile.

In pratica:

    il prodotto, dal    bash /media/REMOTIX/enter.sh --root \\
    contenitore           "python3 /srv/src/01-b8-sblocca.py \\
                           --socket /srv/src/remotix-comando.sock \\
                           --pretendi-chi remotix \\
                           --ban-file /srv/src/remotix-ban 192.168.0.2"

    l'innesto           come sopra, ma --socket /srv/src/b8-comando.sock e
                        --pretendi-chi bsslserver

    dal server, fuori   gli stessi percorsi si vedono come
                        /media/REMOTIX/src/…, ⚠ ma serve sudo: da utente normale
                        il socket e' 0600 di root

⛔ E un «permesso negato» **non e' un «non era bannato»**: qui esce con 3 e lo
   dice, perche' e' esattamente la faccia comune di vuoto e proibito.

⚠ E l'indirizzo si digita **come lo digita una persona** (`192.168.0.2`): la
  chiave vera porta le parentesi quadre — `[192.168.0.2]`, perche' cosi' la
  scrive `util::straddr()` dell'ospite — e a metterle e' `rcp_chiave_indirizzo()`
  dentro il server.  Qui non si costruisce nessuna chiave: se la costruisse
  anche questo file, il giorno in cui le due forme divergessero il comando
  risponderebbe «non era bannato» a ogni indirizzo, in silenzio e per sempre.

⭐ E la chiave che serve a guardare il file dei ban **si prende dalla risposta**,
   non si costruisce: il server risponde `TOLTO [192.168.0.2]`, e quella e' la
   sua chiave, pronunciata da lui.  ⛔ Se un giorno rispondesse senza chiave,
   questo programma dice che la verifica su file non l'ha potuta fare (esce 6)
   invece di inventarsela.
"""
import argparse
import os
import socket
import stat as statmod
import struct
import sys

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# I due socket che esistono su questa macchina, e servono solo a scriverli nel
# messaggio d'errore di chi ha dimenticato `--socket`.  ⛔ Non sono predefiniti:
# vedi il riquadro «il terzo esito ha una quarta faccia».
SOCKET_NOTI = (
    ("il prodotto  (src/, porta 7448)", "/srv/src/remotix-comando.sock", "remotix"),
    ("l'innesto    (bsslserver, 7447)", "/srv/src/b8-comando.sock", "bsslserver"),
)


# ===========================================================================
# ⛔ Chi c'e' dall'altro capo — e lo dice il NUCLEO, non il server
# ===========================================================================
def chi_ascolta(s):
    """Le credenziali del processo dall'altro capo del socket, da `SO_PEERCRED`.

    ⭐ `CODER.md` §3.7: *«non si deduce il mittente: lo si chiede al nucleo»*.
       Un socket di dominio Unix porta con se' pid, uid e gid di chi ascolta, e
       il kernel non ha nessun motivo per mentire — mentre una stringa nel
       protocollo la sceglie il server, cioe' proprio il pezzo di cui si vuole
       sapere l'identita'.

    Restituisce un dizionario che dichiara sempre **perche'** un campo manca:
    ⛔ «non l'ho potuto leggere» e «non c'e'» sono due fatti diversi
    (`LEZIONI.md` §1.9 regola 1), e questo e' esattamente il punto in cui la
    versione precedente di questo file li confondeva."""
    chi = {"pid": None, "uid": None, "gid": None, "nome": None,
           "riga": None, "guasto": None}
    try:
        grezzo = s.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                              struct.calcsize("3i"))
        chi["pid"], chi["uid"], chi["gid"] = struct.unpack("3i", grezzo)
    except (OSError, AttributeError, struct.error) as e:
        chi["guasto"] = (f"non ho potuto chiedere al nucleo chi ascolta "
                         f"(SO_PEERCRED): {type(e).__name__}: {e}")
        return chi
    if not chi["pid"]:
        chi["guasto"] = ("il nucleo ha dato pid 0: il processo che ascoltava non "
                         "e' piu' raggiungibile da questo spazio dei pid")
        return chi
    proc = f"/proc/{chi['pid']}"
    if not os.path.isdir(proc):
        # ⛔ Il processo e' morto fra il `connect` e questa riga: e' un fatto, e
        #    non e' «non l'ho potuto leggere».
        chi["guasto"] = (f"{proc} non c'e': il processo {chi['pid']} che ha "
                         f"risposto e' gia' morto")
        return chi
    for campo, dove, ripulisci in (("nome", "comm", lambda t: t.strip()),
                                   ("riga", "cmdline",
                                    lambda t: " ".join(t.split("\0")).strip())):
        try:
            with open(f"{proc}/{dove}", "r", errors="replace") as f:
                chi[campo] = ripulisci(f.read()) or None
        except OSError as e:
            # ⛔ `/proc/<pid>/cmdline` di un binario con file capabilities e'
            #    illeggibile anche per chi l'ha avviato (`LEZIONI.md` §1.9): un
            #    campo vuoto qui NON vuol dire «processo senza nome».
            chi["guasto"] = (f"non ho potuto leggere {proc}/{dove}: "
                             f"{type(e).__name__}: {e}")
    return chi


def descrivi_chi(chi):
    """La riga che si stampa sempre, anche quando non si e' potuto sapere."""
    if chi is None:
        return "⚠ non ho chiesto chi ascolta"
    pezzi = []
    if chi["pid"]:
        pezzi.append(f"pid {chi['pid']}")
    if chi["nome"]:
        pezzi.append(f"«{chi['nome']}»")
    if chi["uid"] is not None:
        pezzi.append(f"uid {chi['uid']}")
    if not pezzi:
        return f"⚠ chi ha risposto: SCONOSCIUTO — {chi['guasto']}"
    coda = f" — ⚠ {chi['guasto']}" if chi["guasto"] else ""
    return "ha risposto " + " ".join(pezzi) + coda


def chi_combacia(chi, atteso):
    """`(vero, dettaglio)`.  ⛔ Un confronto che non ha potuto guardare NON e'
    un confronto riuscito: restituisce falso e dice perche'.

    ⛔ E SI CONFRONTA `comm`, PER INTERO, NON LA RIGA DI COMANDO.  Sembrava piu'
       generoso cercare la parola dentro tutt'e due, e invece era una trappola
       misurabile: la riga di comando dell'**innesto** nomina il prodotto —
       `bsslserver … --ban-file /srv/src/remotix-ban` contiene «remotix» — e
       `--pretendi-chi remotix` sarebbe stato **verde sul server sbagliato**,
       cioe' il controllo che esiste per trovare quel caso l'avrebbe coperto.
       ⚠ `/proc/<pid>/comm` e' il nome del programma, sta in 15 caratteri, e
       `remotix` e `bsslserver` ci stanno tutti e due.
    ⚠ La riga di comando resta come RIPIEGO DICHIARATO per il solo caso in cui
      `comm` non si sia potuto leggere, e allora si dice che il confronto e'
      piu' debole (`CODER.md` §4.2: il ripiego si dichiara)."""
    if chi is None:
        return False, "non ho chiesto chi ha risposto"
    if chi["nome"]:
        if chi["nome"] == atteso:
            return True, f"/proc/{chi['pid']}/comm dice esattamente «{atteso}»"
        return False, (f"/proc/{chi['pid']}/comm dice «{chi['nome']}», non "
                       f"«{atteso}»")
    if chi["riga"]:
        if atteso in chi["riga"]:
            return True, (f"⚠ confronto DEBOLE (comm illeggibile: "
                          f"{chi['guasto']}): «{atteso}» compare nella riga di "
                          f"comando «{chi['riga']}» — ma comparirebbe anche in "
                          f"un altro programma che nomina quel percorso")
        return False, f"«{atteso}» non e' nella riga di comando «{chi['riga']}»"
    return False, ("non so chi ha risposto, quindi non posso dire che sia "
                   f"«{atteso}»: {chi['guasto']}")


# ===========================================================================
# Il socket, la riga, la risposta
# ===========================================================================
def guarda_il_socket(percorso):
    """`(va_bene, dettaglio)` sul solo file del socket, prima di parlarci.

    ⛔⭐ QUI STAVA UN DIFETTO DI QUESTO STESSO FILE, ed e' quello che il file
         predica di non fare — trovato l'11 agosto 2026.  La riga era
         `if not os.path.exists(percorso)` con il messaggio *«il socket non
         esiste: o il server non e' acceso, o e' stato acceso senza
         --comando-socket»*.  ⚠ Ma `os.path.exists()` **inghiotte l'errore**: su
         `PermissionError` — cioe' quando la cartella che contiene il socket non
         e' attraversabile da chi chiama, che e' il caso NORMALE per un socket di
         root guardato da un utente qualunque — restituisce `False` esattamente
         come quando il file non c'e'.  ⛔ Vuoto e proibito con la stessa faccia,
         dentro il programma la cui intestazione dice che non devono averla:
         `LEZIONI.md` §1.9, prima regola.  Qui si guarda `errno`."""
    try:
        st = os.stat(percorso)
    except FileNotFoundError:
        if os.path.lexists(percorso):
            return False, (f"«{percorso}» e' un collegamento che punta al vuoto: "
                           f"il socket a cui rimanda non c'e'")
        return False, (f"il socket «{percorso}» non esiste: o il server non e' "
                       f"acceso, o e' stato acceso senza --comando-socket — e in "
                       f"tutt'e due i casi il ban NON si puo' togliere")
    except PermissionError as e:
        return False, (f"⛔ non ho il permesso di GUARDARE «{percorso}» ({e}): "
                       f"questo NON e' «il socket non c'e'».  Il socket e' 0600 "
                       f"di chi ha acceso il server (di solito root nel "
                       f"contenitore): si richiama con sudo, o da dentro il "
                       f"contenitore con --root")
    except OSError as e:
        return False, (f"non ho potuto guardare «{percorso}»: "
                       f"{type(e).__name__}: {e}")
    if not statmod.S_ISSOCK(st.st_mode):
        return False, (f"«{percorso}» c'e' ma NON e' un socket "
                       f"(modo {statmod.filemode(st.st_mode)}): sto guardando il "
                       f"file sbagliato")
    modo = st.st_mode & 0o777
    if modo != 0o600:
        # ⚠ Non e' un guasto: si parla lo stesso, ma §4.4-bis dice che la chiave
        #   di questo comando e' «l'accesso alla macchina», e con un socket piu'
        #   largo la chiave e' un'altra.  Si dichiara.
        return True, (f"⚠ il socket e' {modo:04o} e non 0600: §4.4-bis suppone "
                      f"«l'accesso alla macchina», e questo e' l'accesso di piu' "
                      f"gente di cosi'")
    return True, None


def scambia(percorso, riga, attesa=5.0):
    """Una riga al socket di controllo, e tutto quel che se ne sa.

    Restituisce un dizionario con `risposta` **oppure** `guasto` (mai tutt'e
    due), piu' `chi` — chi ha risposto secondo il nucleo — e `avviso`.
    ⛔ Un guasto NON e' una risposta: chi chiama non deve poterli confondere, e
       per questo non c'e' nessun valore di ripiego."""
    r = {"risposta": None, "guasto": None, "chi": None, "avviso": None}
    if not percorso:
        r["guasto"] = "nessun percorso di socket: non ho parlato con nessuno"
        return r
    va, dettaglio = guarda_il_socket(percorso)
    if not va:
        r["guasto"] = dettaglio
        return r
    r["avviso"] = dettaglio
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(attesa)
    try:
        s.connect(percorso)
        # ⭐ Si chiede chi ascolta PRIMA di mandare la riga: se poi il server
        #    muore, si sa comunque con chi si era parlato.
        r["chi"] = chi_ascolta(s)
        s.sendall((riga + "\n").encode())
        # ⚠ Una lettura sola basta: la risposta e' una riga corta e il server
        #   chiude subito.  Se un giorno diventasse piu' lunga, questo e' il
        #   punto che va cambiato — e si vedrebbe, perche' la risposta
        #   arriverebbe troncata invece che assente.
        dati = s.recv(4096)
    except OSError as e:
        r["guasto"] = f"non ho potuto parlare col comando: {type(e).__name__}: {e}"
        return r
    finally:
        s.close()
    if not dati:
        r["guasto"] = "il comando ha chiuso senza rispondere niente"
        return r
    r["risposta"] = dati.decode(errors="replace").strip()
    return r


def parla(percorso, riga, attesa=5.0):
    """⚠ La forma vecchia, `(risposta, guasto)` — uno dei due e' sempre `None`.
    Resta perche' `01-b8-cronometro.py` la importa; il resto usa `scambia()`."""
    r = scambia(percorso, riga, attesa)
    return r["risposta"], r["guasto"]


def ping_esteso(percorso, attesa=5.0):
    """⭐ «Il comando c'e' e risponde?» — e non tocca nessun ban.

    E' il denominatore di B0.3: un banco che sblocca fra una prova e l'altra
    deve poter dire che **ha parlato con qualcuno**, o il suo «tolto» e il suo
    silenzio hanno lo stesso valore.

    ⛔ E dice **con chi**: `PONG` da solo prova che qualcuno risponde, non che
       risponda il server di cui si sta misurando il ban."""
    r = scambia(percorso, "PING", attesa)
    r["vivo"] = (r["risposta"] == "PONG")
    return r


def ping(percorso, attesa=5.0):
    """⚠ La forma vecchia, `(vivo, che)`, per `01-b8-cronometro.py`."""
    r = ping_esteso(percorso, attesa)
    return r["vivo"], (r["risposta"] or r["guasto"])


def sblocca_esteso(percorso, indirizzo, attesa=5.0):
    """Aggiunge a `scambia()` l'`esito` in TOLTO · NON-BANNATO · None, e la
    `chiave` **come l'ha pronunciata il server**."""
    r = scambia(percorso, f"SBLOCCA {indirizzo}", attesa)
    r["esito"] = None
    r["chiave"] = None
    if r["risposta"] is None:
        return r
    pezzi = r["risposta"].split(" ", 1)
    if pezzi[0] not in ("TOLTO", "NON-BANNATO"):
        r["guasto"] = f"risposta che non conosco: «{r['risposta']}»"
        r["risposta"] = None
        return r
    r["esito"] = pezzi[0]
    if len(pezzi) > 1 and pezzi[1].strip():
        r["chiave"] = pezzi[1].strip()
    return r


def sblocca(percorso, indirizzo, attesa=5.0):
    """⚠ La forma vecchia, `(esito, dettaglio)`, per `01-b8-cronometro.py`."""
    r = sblocca_esteso(percorso, indirizzo, attesa)
    if r["esito"] is None:
        return None, r["guasto"]
    return r["esito"], (r["risposta"] or r["esito"])


# ===========================================================================
# ⛔ L'ALTRA META' DI §4.4-bis: il file, che sopravvive al riavvio
# ===========================================================================
def leggi_file_ban(percorso):
    """`(righe, guasto)` — uno dei due e' sempre `None`.

    ⛔ Si legge il file INTERO e non si cerca ancora niente: la chiave la
       pronuncia il server nella sua risposta, e la risposta arriva **dopo** lo
       sblocco.  Prendendo le due fotografie — prima e dopo — la ricerca si fa
       su tutt'e due quando la chiave e' nota, e allora il «prima» diventa il
       controllo positivo del lettore invece che un'altra domanda senza risposta.

    ⛔ «La chiave non c'e' nel file» e «non ho potuto leggere il file» sono due
       fatti diversi, e il secondo NON e' un «pulito» (`LEZIONI.md` §1.9).
    ⛔ E «il file non esiste» non e' «nessun ban»: vuol dire che il server e'
       acceso senza `--ban-file`, cioe' che NESSUN ban sopravvive al riavvio —
       invariante **I7**, e §4.4-bis lo vieta."""
    try:
        with open(percorso, "r", errors="replace") as f:
            return [r for r in f.read().splitlines() if r.strip()], None
    except FileNotFoundError:
        return None, (
            f"il file dei ban «{percorso}» non esiste: ⛔ non e' «nessun ban», e' "
            f"che il server e' acceso senza --ban-file e nessun ban sopravvive "
            f"al riavvio (§4.4-bis, invariante I7)")
    except PermissionError as e:
        return None, (f"⛔ non ho il permesso di leggere il file dei ban "
                      f"«{percorso}» ({e}): non e' «il ban non c'e'»")
    except OSError as e:
        return None, (f"non ho potuto leggere il file dei ban «{percorso}»: "
                      f"{type(e).__name__}: {e}")


def dentro(righe, chiave):
    """⚠ Si confronta il PRIMO campo della riga, non `chiave in riga`: il file
    porta «[192.168.0.2] 1786000000», e una sottostringa direbbe di si' anche
    per «[192.168.0.20]»."""
    return any(r.split(" ", 1)[0] == chiave for r in righe)


# ===========================================================================
def principale():
    p = argparse.ArgumentParser(
        description="Il comando di sblocco di RCP.md §4.4-bis (fasi/01-filo-nudo.md B0.3)")
    p.add_argument("indirizzo", nargs="?", default=None,
                   help="l'indirizzo da sbloccare, come lo digita una persona")
    # ⛔ NESSUN PREDEFINITO, e la ragione sta nel riquadro «il terzo esito ha una
    #    quarta faccia»: il predefinito di prima era il socket dell'innesto, e
    #    chi lo usava contro il prodotto riceveva PONG e NON-BANNATO dal server
    #    sbagliato, uscendo 0.
    p.add_argument("--socket", default=None,
                   help="⛔ obbligatorio: il socket Unix 0600 del comando")
    p.add_argument("--ping", action="store_true",
                   help="chiede solo se il comando esiste, e non tocca niente")
    p.add_argument("--pretendi", choices=("TOLTO", "NON-BANNATO"), default=None,
                   help="⛔ e il banco CONFRONTA (B0.4): esce 4 se l'esito e' un altro")
    p.add_argument("--pretendi-chi", default=None, metavar="NOME",
                   help="il nome del processo che DEVE rispondere "
                        "(«remotix» il prodotto, «bsslserver» l'innesto): esce 4")
    p.add_argument("--pretendi-pid", type=int, default=None, metavar="N",
                   help="il pid esatto che DEVE rispondere: esce 4")
    p.add_argument("--ban-file", default=None, metavar="PATH",
                   help="guarda anche il file dei ban, prima e dopo")
    p.add_argument("--attesa", type=float, default=5.0)
    a = p.parse_args()

    if not a.socket:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ manca --socket, e non c'e' piu' un "
              f"predefinito: su questa macchina i server sono DUE, e sbloccare "
              f"quello sbagliato esce 0 dicendo che la macchina e' pulita")
        for chi, dove, nome in SOCKET_NOTI:
            print(f"        {chi}  --socket {dove} --pretendi-chi {nome}")
        return 2

    if a.ping:
        r = ping_esteso(a.socket, a.attesa)
        if r["avviso"]:
            print(f"        {r['avviso']}")
        if not r["vivo"]:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il comando di sblocco NON risponde: "
                  f"{r['risposta'] or r['guasto']}")
            return 3
        print(f"    {VERDE}OK{GRIGIO}  il comando di sblocco risponde («PONG») su "
              f"«{a.socket}» — e non ha toccato nessun ban")
        print(f"        ⭐ {descrivi_chi(r['chi'])}")
        return giudica_chi(a, r["chi"])

    if not a.indirizzo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ manca l'indirizzo da sbloccare "
              f"(oppure --ping)")
        return 2

    # ── la fotografia del file dei ban PRIMA ──────────────────────────────
    # ⛔ Si legge prima, e non per curiosita': senza il «prima», la frase «dopo
    #    la chiave non c'e'» non ha nessun controllo positivo — un lettore che
    #    non sa trovare NIENTE direbbe esattamente la stessa cosa
    #    (`LEZIONI.md` §1.9 regola 2).
    prima, prima_guasto = (None, None)
    if a.ban_file:
        prima, prima_guasto = leggi_file_ban(a.ban_file)

    r = sblocca_esteso(a.socket, a.indirizzo, a.attesa)
    if r["avviso"]:
        print(f"        {r['avviso']}")
    if r["esito"] is None:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ non ho tolto niente, e non perche' non "
              f"c'era: {r['guasto']}")
        return 3

    print(f"        ⭐ {descrivi_chi(r['chi'])}")
    if r["esito"] == "TOLTO":
        print(f"    {VERDE}OK{GRIGIO}  ⛔ SBLOCCATO «{a.indirizzo}» — il ban c'era "
              f"ed e' stato tolto  ({r['risposta']})")
    else:
        print(f"    {GIALLO}--{GRIGIO}  «{a.indirizzo}» NON era bannato: non ho "
              f"tolto niente  ({r['risposta']})")
        # ⛔ Questa riga e' stata una CONVINZIONE fino all'11 agosto 2026
        #    (rilievo A22): nessuno la verificava, e su di lei poggia l'intera
        #    strategia dei campioni di B8 («sbloccare fra un blocco e l'altro»).
        #    Adesso e' misurata, e si dice DOVE — perche' un fatto senza
        #    provenienza e' una speranza con un numero davanti.
        print(f"        ⚠ e il conto dei tentativi di quell'indirizzo riparte "
              f"comunque da zero — `[M]` 11 agosto 2026, misurato da "
              f"`01-b8-prova-ban.c` sezione 5: due fallimenti, uno sblocco che "
              f"risponde «non era bannato», altri due fallimenti, e il ban NON "
              f"scatta")

    codice = giudica_chi(a, r["chi"])
    if a.pretendi and r["esito"] != a.pretendi:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ atteso «{a.pretendi}», arrivato "
              f"«{r['esito']}»: sono due fatti diversi e questo banco li distingue")
        codice = codice or 4

    if a.ban_file:
        # ⚠ E il file dei ban VINCE sul confronto dell'atteso: 4 dice «non e'
        #   l'esito che aspettavo», 5 dice «il ban c'e' ancora».  Le righe a
        #   schermo restano tutte; lo stato d'uscita porta il fatto piu' grave.
        codice = guarda_le_due_meta(a, r, prima, prima_guasto) or codice
    return codice


def giudica_chi(a, chi):
    """B0.4 applicata a *chi ha risposto*: si stampa e si confronta."""
    codice = 0
    if a.pretendi_pid is not None:
        if chi is None or chi["pid"] != a.pretendi_pid:
            vero = chi["pid"] if chi else None
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ atteso il pid {a.pretendi_pid}, ha "
                  f"risposto {vero}: ho parlato con un server, ma non con QUELLO "
                  f"— il ban che volevo togliere e' ancora dov'era")
            codice = 4
    if a.pretendi_chi:
        va, dettaglio = chi_combacia(chi, a.pretendi_chi)
        if not va:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ atteso «{a.pretendi_chi}» dall'altro "
                  f"capo: {dettaglio}.  Su questa macchina i server sono due, e "
                  f"uno sblocco dato a quello sbagliato risponde benissimo")
            codice = 4
        else:
            print(f"        {VERDE}OK{GRIGIO}  ed e' il server giusto: {dettaglio}")
    return codice


def guarda_le_due_meta(a, r, prima, prima_guasto):
    """⛔ §4.4-bis vive in DUE posti — la memoria del processo che serve e il
    file che sopravvive al riavvio — e uno sblocco che ne convince uno solo non
    e' uno sblocco: al riavvio il ban torna, e chi ha dato il comando l'ha visto
    uscire con zero (rilievo R12.1, ed e' il difetto che `src/comando.c` esiste
    per togliere).  Qui le due meta' si confrontano invece di darne per buona
    una."""
    if not r["chiave"]:
        print(f"    {GIALLO}??{GRIGIO}  ⚠ il server ha risposto senza la chiave "
              f"(«{r['risposta']}»): non posso guardare il file dei ban senza "
              f"costruirmi una chiave, e costruirmela e' precisamente quel che "
              f"§4.4-bis vieta a chi comanda")
        return 6
    chiave = r["chiave"]
    dopo, dopo_guasto = leggi_file_ban(a.ban_file)

    # ⛔ Il denominatore, sempre (`LEZIONI.md` §1.9 regola 4): «assente» non e'
    #    un dato finche' non si sa su quante righe si e' guardato.
    for etichetta, righe, guasto in (("prima", prima, prima_guasto),
                                     ("dopo ", dopo, dopo_guasto)):
        if guasto:
            print(f"        {GIALLO}??{GRIGIO}  file dei ban {etichetta}: {guasto}")
        else:
            print(f"        --  file dei ban {etichetta}: «{chiave}» "
                  f"{'PRESENTE' if dentro(righe, chiave) else 'assente'} "
                  f"({len(righe)} righe in «{a.ban_file}»)")

    if dopo_guasto:
        print(f"    {GIALLO}??{GRIGIO}  ⚠ la verifica su FILE non e' stata fatta: "
              f"so solo che la memoria del processo dice «{r['esito']}».  ⛔ Non "
              f"e' un «pulito»")
        return 6

    c_dopo = dentro(dopo, chiave)
    c_prima = dentro(prima, chiave) if prima is not None else None

    if r["esito"] == "TOLTO" and c_dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il processo dice TOLTO e il file dei ban "
              f"contiene ancora «{chiave}»: lo sblocco NON e' arrivato al disco, "
              f"e al primo riavvio il ban torna (§4.4-bis, invariante I7)")
        return 5
    if r["esito"] == "NON-BANNATO" and c_dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il processo dice NON-BANNATO e il file "
              f"dei ban contiene «{chiave}»: le due meta' di §4.4-bis non "
              f"concordano, e le letture possibili sono due — ⛔ o ho parlato con "
              f"un server DIVERSO da quello che scrive «{a.ban_file}» (e allora "
              f"il ban che volevo togliere e' ancora vivo), oppure quel server e' "
              f"partito senza rileggere il file")
        return 5
    if r["esito"] == "TOLTO":
        print(f"    {VERDE}OK{GRIGIO}  ⭐ memoria e file concordano: il processo "
              f"ha tolto «{chiave}», e nel file non c'e' piu'")
        # ⛔ E il controllo che dice NO si dichiara: se la chiave non c'era nel
        #    file nemmeno PRIMA, «adesso non c'e'» lo direbbe identico un lettore
        #    che non sa trovare niente.
        if c_prima:
            print(f"        {VERDE}OK{GRIGIO}  ⭐ e il controllo positivo del "
                  f"lettore c'e': prima «{chiave}» in quel file lo trovavo")
        elif prima_guasto:
            print(f"        ⚠ controllo positivo ASSENTE: il «prima» non l'ho "
                  f"potuto leggere, quindi non so se questo lettore sappia "
                  f"trovare una chiave che c'e' (`LEZIONI.md` §1.9 regola 2)")
        else:
            print(f"        ⚠ controllo positivo ASSENTE: «{chiave}» nel file non "
                  f"c'era NEMMENO PRIMA, mentre il processo dice che il ban in "
                  f"memoria c'era.  ⛔ Le due meta' di §4.4-bis non concordano "
                  f"nell'altro verso: quel ban non sarebbe sopravvissuto al "
                  f"riavvio")
            return 5
    return 0


if __name__ == "__main__":
    sys.exit(principale())
