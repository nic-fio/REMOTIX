#!/usr/bin/env python3
"""Esegue ssh/scp verso il server di sviluppo fornendo la password da ~/SERVER.ssh.

Serve solo perche' il rootfs del server e' live in RAM: il riavvio ha cancellato
/home/nicfio/.ssh/authorized_keys, quindi l'autenticazione a chiave non e' piu'
disponibile finche' non la si reinstalla.  La password non compare mai sulla riga
di comando: viene scritta sul pty solo quando ssh la chiede.

  sshpw.py <comando remoto...>
  sshpw.py --put <locale> <remoto>
"""
import os
import pty
import re
import select
import sys

CRED = os.path.expanduser("~/SERVER.ssh")


def leggi_credenziali():
    dati = {}
    with open(CRED) as f:
        for riga in f:
            if ":" in riga:
                k, _, v = riga.partition(":")
                dati[k.strip().lower()] = v.strip()
    return dati["host"], dati["user"], dati["pass"]


def emetti(riga, password):
    """Stampa una riga, togliendo la password dove e' stata digitata.

    Si filtra riga per riga e non con una sostituzione globale: qui la password
    coincide con il nome utente, e una sostituzione globale mangerebbe anche i
    percorsi /home/<utente>.
    """
    # Si toglie l'intera richiesta, compreso il «utente@host's » che ssh mette
    # davanti: lasciarne un pezzo significa infilare spazzatura in testa a
    # qualunque file catturato da questo flusso.
    # ANCORATO ALL'INIZIO RIGA, e non e' un dettaglio: senza l'ancora questo
    # filtro cancella anche le occorrenze legittime dentro i file che si
    # leggono da remoto, e mostra un contenuto diverso da quello vero — cosa
    # che e' gia' costata una diagnosi sbagliata.
    pulita = re.sub(r"^\S*@\S+'s [Pp]assword:\s*", "", riga)
    pulita = re.sub(r"^[Pp]assword[^:\n]*:\s*", "", pulita)
    if pulita.strip() == password:
        return
    sys.stdout.write(pulita + "\n")
    sys.stdout.flush()


def esegui(argv, password, timeout=1800):
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(argv[0], argv)
    resto = ""
    # Quante richieste di password si e' disposti a soddisfare.
    #
    # Il tetto serve: senza, un flusso remoto che per caso contenga «password:»
    # si farebbe mandare la parola d'ordine dentro un file.  Ma era 8, ed e'
    # troppo poco per una prova lunga — ogni ingresso nel contenitore ne chiede
    # una, e il giorno in cui `fase5.sh` ha guadagnato una sezione in piu' il
    # nono prompt e' rimasto senza risposta: `sudo` fermo per 39 minuti su una
    # domanda che nessuno stava piu' ascoltando, e la prova apparentemente
    # «lenta» invece che bloccata.
    #
    # Il tetto alto e' sicuro solo grazie all'ancora qui sotto.
    RISPOSTE_MAX = 64
    risposte = 0
    while True:
        try:
            pronti, _, _ = select.select([fd], [], [], timeout)
        except InterruptedError:
            continue
        if not pronti:
            break
        try:
            blocco = os.read(fd, 65536)
        except OSError:
            break
        if not blocco:
            break
        testo = blocco.decode("utf-8", "replace")
        # ANCORATO ALLA FINE DEL BLOCCO: una richiesta vera e' l'ultima cosa
        # che il programma scrive prima di mettersi in attesa, e non ha l'a
        # capo.  Una riga di registro che nomina una password, invece, ha
        # sempre qualcosa dopo.  E' questa distinzione — non il tetto — che
        # impedisce di spedire la parola d'ordine a chi non l'ha chiesta.
        if risposte < RISPOSTE_MAX and re.search(r"[Pp]assword[^:\n]*:\s*\Z", testo):
            os.write(fd, (password + "\n").encode())
            risposte += 1
        resto += testo
        while "\n" in resto:
            riga, _, resto = resto.partition("\n")
            emetti(riga.rstrip("\r"), password)
    if resto.strip():
        emetti(resto.rstrip("\r"), password)
    _, stato = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(stato)


def main():
    host, utente, password = leggi_credenziali()
    comuni = [
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "ConnectTimeout=10",
    ]
    if sys.argv[1:2] == ["--put"]:
        locale, remoto = sys.argv[2], sys.argv[3]
        argv = ["scp"] + comuni + [locale, f"{utente}@{host}:{remoto}"]
    elif sys.argv[1:2] == ["--get"]:
        # I file si prendono con scp, MAI catturando lo stdout di un `cat`
        # remoto: li' dentro finisce anche la richiesta di password di ssh.
        remoto, locale = sys.argv[2], sys.argv[3]
        argv = ["scp"] + comuni + [f"{utente}@{host}:{remoto}", locale]
    else:
        argv = ["ssh"] + comuni + [f"{utente}@{host}"] + sys.argv[1:]
    sys.exit(esegui(argv, password))


if __name__ == "__main__":
    main()
