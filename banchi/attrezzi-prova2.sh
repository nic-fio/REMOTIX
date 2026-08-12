#!/bin/bash
# ⛔ Il secondo utente si AUTENTICA davvero?  E la parola non si stampa mai.
#
# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ QUI C'ERANO DUE FALLE, e la seconda era piu' insidiosa della prima:
#
#   1. `--parola '$P2'` finiva dentro la stringa che `bash $E --root "…"`
#      riceve come argomento: nell'`argv` di `bash`, in quello di `sudo` e in
#      quello di `python3`.  `/proc/<pid>/cmdline` e' leggibile da chiunque.
#   2. ⛔ `sed "s/$P2/<NON SI STAMPA>/g"` — la riga che serviva a NON stampare
#      la parola la metteva nell'`argv` di `sed`.  ⚠ E' la forma peggiore: una
#      cura che si smentisce da sola nel processo accanto, come il
#      «la parola non compare in nessun registro» di `sonda-rcp.html`.
#
# ⛔⛔ E non e' la parola pubblica dei banchi: e' quella **generata** di
#    `prova2`, che `01-b10-lancia.sh` tratta come non compromettibile e che per
#    questo passa da un file `0600`.  ⇒ Questo attrezzo la mostrava a chiunque
#    mentre il banco che la usa la proteggeva.
#
# ⭐ La strada e' quella gia' in casa (`banchi/01-b10-lancia.sh`): file `0600`
#    scritto con `printf` — un **builtin**, quindi nemmeno la scrittura passa
#    per un processo con la parola in `argv` — passato come `--parola-file`, e
#    cancellato con una `trap`.  Anche lo script di `sed` sta in un file: `-f`
#    lo legge, e nell'`argv` finisce il percorso.
# ---------------------------------------------------------------------------
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
FUORI=/media/REMOTIX/src

# ⚠ `sed` legge il file: la parola non compare in nessun `argv`.
P2=$(sed -n 's/^prova2:[[:space:]]*//p' /media/REMOTIX/credenziali-banchi | head -1)
[ -n "$P2" ] || { echo "⛔ nessuna parola per prova2"; exit 2; }

PAROLA_FUORI=$FUORI/tmp/attrezzi-prova2-parola
PAROLA_DENTRO=$D/tmp/attrezzi-prova2-parola
MASCHERA=$FUORI/tmp/attrezzi-prova2-maschera.sed

ripulisci() { rm -f "$PAROLA_FUORI" "$MASCHERA"; }
trap ripulisci EXIT

# ⛔ `umask` in una SOTTOSHELL: nudo resterebbe addosso a tutto quel che segue,
#    compresi i comandi mandati dentro il contenitore — la riga che B10 ha
#    pagato con un giro intero.
mkdir -p "$FUORI/tmp" \
  && ( umask 077; : > "$PAROLA_FUORI"; : > "$MASCHERA" ) \
  && chmod 600 "$PAROLA_FUORI" "$MASCHERA" \
  || { echo "⛔ non si scrive in $FUORI/tmp"; exit 2; }
printf '%s\n' "$P2" > "$PAROLA_FUORI"
# ⭐ La maschera resta, e non e' ridondante: se un giorno il banco stampasse la
#    parola per un altro motivo, questa la fermerebbe lo stesso.  ⛔ Ma adesso
#    lo script di `sed` sta in un file, non in `argv`.
printf 's/%s/<NON SI STAMPA>/g\n' "$P2" > "$MASCHERA"

# ---------------------------------------------------------------------------
# ⛔⛔ E QUI C'ERA UNA SECONDA COSA, PEGGIORE DELLA PRIMA — `[M]` 12 agosto 2026,
#     misurata **lanciando questo attrezzo dopo averlo curato**.
#
# Le due chiamate qui sotto erano scritte
#
#     bash $E --root "…" 2>&1 | grep -E … | sed …
#
# cioe' con una redirezione **ATTORNO** a `enter.sh`.  ⛔ La richiesta di parola
# d'ordine di `sudo` esce su **stderr**, e `2>&1 |` se l'ha portata via dentro
# la pipe: `[M]` `ps` sul server, `sudo -v -S -p 'Password sudo: '` fermo in
# stato `S` dopo 2 minuti e 33 secondi, con `grep` e `sed` che aspettavano un
# flusso che non sarebbe mai arrivato.  ⚠ Nessun errore, nessun messaggio:
# l'attrezzo sembrava soltanto **lento**.
#
# ⛔ E' `fasi/00-ambiente.md` B3.3, gia' pagata **quattro volte** — due nella
#    sola notte dell'11 agosto.  ⭐ La cura e' quella di `01-b12-lancia.sh`: si
#    redirige **dentro** le virgolette e si legge il file dopo.
#
# ⚠ E cosi' si guadagna anche lo stato d'uscita vero: `echo "uscita=$?"` dopo
#   una pipe leggeva quello di `sed`, che e' 0 sempre — il cliente poteva
#   fallire e l'attrezzo stampava «uscita=0».
USCITA_FUORI=$FUORI/tmp/attrezzi-prova2-uscita.txt
USCITA_DENTRO=$D/tmp/attrezzi-prova2-uscita.txt

bash $E --root "nohup env LD_LIBRARY_PATH=$D/b2/ngtcp2/build/lib $D/b2/ngtcp2/build/examples/bsslserver --timeout=120s 192.168.0.2 7447 /media/REMOTIX/b2-certificati/sessione.key /media/REMOTIX/b2-certificati/sessione.pem < /dev/null > $D/p2.log 2>&1 & echo \$! > $D/p2.pid"
sleep 2
PID=$(cat /media/REMOTIX/src/p2.pid)

echo "== prova2 (parola generata, mai in una riga di comando)"
bash $E --root "python3 -u $D/01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7447 --utente prova2 --parola-file $PAROLA_DENTRO --registra $D/p2.rcpreg > $USCITA_DENTRO 2>&1"
STATO=$?
grep -E "AMMESSO|RESPINTO|SESSIONE|RuntimeError|ECCOMI" "$USCITA_FUORI" | sed -f "$MASCHERA"
echo "uscita=$STATO   ⛔ del CLIENTE, non di sed"

echo "== e il controllo che dice NO: parola sbagliata"
# ⚠ Questa SI' sulla riga di comando: non e' il segreto di nessuno, ed e' la
#   stessa scelta gia' dichiarata in `01-b10-secondo-utente.py`
#   (`--parola-sbagliata`).  ⭐ E senza di lei il «AMMESSO» qui sopra sarebbe
#   compatibile con un server che ammette chiunque.
bash $E --root "python3 -u $D/01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7447 --utente prova2 --parola questa-non-e-la-sua --registra $D/p2b.rcpreg > $USCITA_DENTRO 2>&1"
STATO_NO=$?
grep -E "AMMESSO|RESPINTO|RuntimeError" "$USCITA_FUORI" | head -3
echo "uscita=$STATO_NO   ⛔ e dev'essere DIVERSA da quella di sopra"
rm -f "$USCITA_FUORI"
# ⛔ E ANCHE QUI la redirezione va DENTRO le virgolette: `bash $E --root "kill
#    $PID" >/dev/null 2>&1` e' la stessa trappola di sopra, e ⚠ e' la piu'
#    velenosa delle due — sta nell'ULTIMA riga, quindi l'attrezzo ha gia'
#    stampato tutto quel che doveva e sembra finito, mentre il server di prova
#    resta acceso sulla 7447 per il prossimo che passa.  `[M]` 12 agosto 2026:
#    e' successo, e ha lasciato un `bsslserver` orfano da spegnere a mano.
bash $E --root "kill $PID >/dev/null 2>&1; true"
echo "== server di prova spento (pid $PID)"
