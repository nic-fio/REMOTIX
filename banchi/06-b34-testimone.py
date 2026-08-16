#!/usr/bin/env python3
"""06-b34-testimone.py — ⛔ IL TESTIMONE, DENTRO LA SESSIONE GRAFICA.

Gira in un terminale del desktop remoto e scrive, per ogni carattere che gli
arriva, una riga «<nanosecondi> <byte UTF-8 in esadecimale>».

    gnome-terminal --title=banco-T6-testimone -- python3 06-b34-testimone.py FILE

===========================================================================
⛔⛔ PERCHE' NON E' PIU' UN CICLO `bash` — `[M]` 16 agosto 2026
===========================================================================

Il testimone era una riga di bash:

    stty -isig; while IFS= read -r -N 1 c; do ... done

⛔ E su `Ctrl+Z` **non scriveva niente**.  Non perche' il tasto non arrivasse:
   `Ctrl+A` arrivava benissimo come `01`, quindi il modificatore lo applicava
   eccome.  La causa e' che **`read -N` di bash rimette `ISIG` a ogni giro**:
   letto il `stty` sul pty vivo, `-isig` era tornato `isig`.  ⇒ `Ctrl+Z`
   diventava **SIGTSTP** — cioe' sospendeva il testimone — invece di arrivare
   come byte `1a`.

⚠ E il sintomo era il peggiore possibile: un file VUOTO, cioe' l'aspetto esatto
  di *«la scorciatoia non e' arrivata»*, sulla prova che l'intera sottofase
  esiste per fare (`DECISIONI.md` §5-bis.6: `Ctrl+Z` su disposizione diversa).
  ⛔ Avrei dichiarato rotto il prodotto per un difetto dello strumento.

⇒ Qui il terminale si mette in modo grezzo **una volta sola**, e nessuno lo
  rimette a posto sotto di noi: `os.read()` non tocca il termios.

===========================================================================
⛔ E I BYTE SI ACCUMULANO FINCHE' NON FANNO UN CARATTERE
===========================================================================

`os.read(fd, 1)` da' **byte**, non caratteri: una `è` sono due byte (`c3 a8`).
Scriverli su due righe farebbe leggere al banco due caratteri illeggibili al
posto di uno giusto.  ⇒ Si accumula finche' la sequenza e' UTF-8 valida, e
allora si scrive **una riga sola** con tutti i suoi byte — che e' esattamente
la forma che `06-b34-leggi.py` si aspetta.
"""
import os
import sys
import termios
import time

PERCORSO = sys.argv[1] if len(sys.argv) > 1 else "/tmp/testimone.txt"

fd = sys.stdin.fileno()

# ⛔ Il modo grezzo, posto UNA VOLTA e non piu' toccato.
#    · `ISIG`   spento: o `Ctrl+Z` diventa SIGTSTP e sospende il testimone;
#    · `ICANON` spento: o i caratteri arrivano solo a fine riga;
#    · `ECHO`   spento: quel che si misura sta nel file, non sullo schermo;
#    · `IXON`   spento: o `Ctrl+S` e `Ctrl+Q` se li mangia il driver.
a = termios.tcgetattr(fd)
a[0] &= ~termios.IXON
a[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
termios.tcsetattr(fd, termios.TCSANOW, a)

# ⛔ E SI RILEGGE, invece di fidarsi: «l'ho scritto» e «e' in vigore» sono due
#    fatti diversi, ed e' precisamente su questo che il banco ha sbagliato una
#    sera intera.
b = termios.tcgetattr(fd)
acceso = bool(b[3] & termios.ISIG)

with open(PERCORSO, "a", buffering=1) as f:
    f.write("STTY %s\n" % ("isig" if acceso else "-isig"))
    f.write("PRONTO %d\n" % time.time_ns())
    f.flush()

    pezzo = b""
    while True:
        try:
            c = os.read(fd, 1)
        except OSError:
            break
        if not c:
            break
        pezzo += c
        # ⚠ Si aspetta che i byte facciano un carattere: una `è` sono due byte,
        #   e due righe al posto di una sarebbero due caratteri sbagliati.
        try:
            pezzo.decode("utf-8")
        except UnicodeDecodeError:
            if len(pezzo) < 4:
                continue          # ne mancano ancora
            # ⛔ Quattro byte che non fanno un carattere non lo faranno mai: si
            #    scrive quel che c'e' invece di ingoiarlo in silenzio.
        f.write("%d %s\n" % (time.time_ns(), pezzo.hex()))
        pezzo = b""
