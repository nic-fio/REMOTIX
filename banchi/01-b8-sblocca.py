#!/usr/bin/env python3
"""01-b8-sblocca.py — ⛔ IL COMANDO DI SBLOCCO di `RCP.md` §4.4-bis, dal lato di
chi comanda.

    python3 01-b8-sblocca.py --socket /srv/src/b8-comando.sock 192.168.0.2
    python3 01-b8-sblocca.py --socket /srv/src/b8-comando.sock --ping
    python3 01-b8-sblocca.py --socket ... --pretendi TOLTO 127.0.0.1

===========================================================================
⛔ A CHE COSA SERVE, E PERCHE' NON E' SOLO DI B8

`RCP.md` §4.4-bis: «si esce in due modi, non uno — la scadenza naturale, oppure
un **comando di sblocco sul server**».  E `fasi/01-filo-nudo.md` regola **B0.3**
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

===========================================================================
⚠ DA DOVE SI CHIAMA, E CHE CHIAVE CHIEDE

Il socket sta nel filesystem con permessi **0600** e appartiene a chi ha acceso
il server — che nei banchi e' **root dentro il contenitore**.  ⭐ E' voluto:
§4.4-bis dice che questo comando *«chiede l'unica chiave che quel caso ammette —
l'accesso alla macchina»*, e un socket leggibile da chiunque la renderebbe
«l'accesso a un utente qualunque della macchina», che e' una chiave diversa e
piu' facile.

In pratica:

    dentro il contenitore   bash enter.sh --root "python3 /srv/src/01-b8-sblocca.py \
                              --socket /srv/src/b8-comando.sock 192.168.0.2"
    dal server, fuori       lo stesso percorso si vede come
                            /media/REMOTIX/src/b8-comando.sock, ⚠ ma serve sudo:
                            da utente normale il socket e' 0600 di root

⛔ E un «permesso negato» **non e' un «non era bannato»**: qui esce con 3 e lo
   dice, perche' e' esattamente la faccia comune di vuoto e proibito.

⚠ E l'indirizzo si digita **come lo digita una persona** (`192.168.0.2`): la
  chiave vera porta le parentesi quadre — `[192.168.0.2]`, perche' cosi' la
  scrive `util::straddr()` dell'ospite — e a metterle e' `rcp_chiave_indirizzo()`
  dentro il server.  Qui non si costruisce nessuna chiave: se la costruisse
  anche questo file, il giorno in cui le due forme divergessero il comando
  risponderebbe «non era bannato» a ogni indirizzo, in silenzio e per sempre.
"""
import argparse
import os
import socket
import sys

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def parla(percorso, riga, attesa=5.0):
    """Una riga al socket di controllo, e la riga che torna.

    Restituisce `(risposta, guasto)`: uno dei due e' sempre `None`.
    ⛔ Un guasto NON e' una risposta: chi chiama non deve poterli confondere,
       e per questo non c'e' nessun valore di ripiego."""
    if not percorso:
        return None, "nessun percorso di socket: non ho parlato con nessuno"
    if not os.path.exists(percorso):
        return None, (f"il socket «{percorso}» non esiste: o il server non e' "
                      f"acceso, o e' stato acceso senza --comando-socket — e in "
                      f"tutt'e due i casi il ban NON si puo' togliere")
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(attesa)
    try:
        s.connect(percorso)
        s.sendall((riga + "\n").encode())
        # ⚠ Una lettura sola basta: la risposta e' una riga corta e il server
        #   chiude subito.  Se un giorno diventasse piu' lunga, questo e' il
        #   punto che va cambiato — e si vedrebbe, perche' la risposta
        #   arriverebbe troncata invece che assente.
        dati = s.recv(4096)
    except OSError as e:
        return None, f"non ho potuto parlare col comando: {type(e).__name__}: {e}"
    finally:
        s.close()
    if not dati:
        return None, "il comando ha chiuso senza rispondere niente"
    return dati.decode(errors="replace").strip(), None


def ping(percorso, attesa=5.0):
    """⭐ «Il comando c'e' e risponde?» — e non tocca nessun ban.

    E' il denominatore di B0.3: un banco che sblocca fra una prova e l'altra
    deve poter dire che **ha parlato con qualcuno**, o il suo «tolto» e il suo
    silenzio hanno lo stesso valore."""
    r, guasto = parla(percorso, "PING", attesa)
    return (r == "PONG"), (r or guasto)


def sblocca(percorso, indirizzo, attesa=5.0):
    """Restituisce `(esito, dettaglio)` con esito in TOLTO · NON-BANNATO · None."""
    r, guasto = parla(percorso, f"SBLOCCA {indirizzo}", attesa)
    if r is None:
        return None, guasto
    testa = r.split(" ", 1)[0]
    if testa not in ("TOLTO", "NON-BANNATO"):
        return None, f"risposta che non conosco: «{r}»"
    return testa, r


def principale():
    p = argparse.ArgumentParser(
        description="Il comando di sblocco di RCP.md §4.4-bis (fasi/01-filo-nudo.md B0.3)")
    p.add_argument("indirizzo", nargs="?", default=None,
                   help="l'indirizzo da sbloccare, come lo digita una persona")
    p.add_argument("--socket", default="/srv/src/b8-comando.sock")
    p.add_argument("--ping", action="store_true",
                   help="chiede solo se il comando esiste, e non tocca niente")
    p.add_argument("--pretendi", choices=("TOLTO", "NON-BANNATO"), default=None,
                   help="⛔ e il banco CONFRONTA (B0.4): esce 4 se l'esito e' un altro")
    p.add_argument("--attesa", type=float, default=5.0)
    a = p.parse_args()

    if a.ping:
        vivo, che = ping(a.socket, a.attesa)
        if vivo:
            print(f"    {VERDE}OK{GRIGIO}  il comando di sblocco risponde "
                  f"(«{che}») su «{a.socket}» — e non ha toccato nessun ban")
            return 0
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il comando di sblocco NON risponde: {che}")
        return 3

    if not a.indirizzo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ manca l'indirizzo da sbloccare "
              f"(oppure --ping)")
        return 2

    esito, dettaglio = sblocca(a.socket, a.indirizzo, a.attesa)
    if esito is None:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ non ho tolto niente, e non perche' non "
              f"c'era: {dettaglio}")
        return 3
    if esito == "TOLTO":
        print(f"    {VERDE}OK{GRIGIO}  ⛔ SBLOCCATO «{a.indirizzo}» — il ban c'era "
              f"ed e' stato tolto  ({dettaglio})")
    else:
        print(f"    {GIALLO}--{GRIGIO}  «{a.indirizzo}» NON era bannato: non ho "
              f"tolto niente  ({dettaglio})")
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
    if a.pretendi and esito != a.pretendi:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ atteso «{a.pretendi}», arrivato "
              f"«{esito}»: sono due fatti diversi e questo banco li distingue")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(principale())
