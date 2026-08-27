#!/bin/bash
# Applica al contenitore VIVO il passo 5-bis di provision.sh (R12-A.44).
#
# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ QUI C'ERA `bash $E --root "printf '%s:%s\n' '$1' '$3' | chpasswd"`, e la
#    parola `$3` finiva **dentro la stringa** che `bash` riceve come argomento:
#    cioe' nell'`argv` di `bash`, in quello di `sudo` e in quello della shell
#    lanciata dentro il contenitore.  `/proc/<pid>/cmdline` su Linux e'
#    leggibile da chiunque, e un `ps` durante il giro la stampava per intero.
#
# ⛔⛔ E non era la parola pubblica dei banchi: la riga «crea prova2 …» passava
#    la parola **generata** di `prova2` — quella che `01-b10-lancia.sh` tratta
#    come non compromettibile, e che per questo motivo li' passa da un file
#    `0600`.  ⇒ Lo strumento che la CREA la mostrava a chiunque, mentre lo
#    strumento che la USA la proteggeva.  Delle due, quella che contava era
#    questa: una parola nata in `ps` e' gia' compromessa quando B10 la legge.
#
# ⭐ LA STRADA E' QUELLA GIA' IN CASA (`banchi/01-b10-lancia.sh`): un file
#    `0600` scritto con `printf`, che e' un **builtin** della shell — nemmeno
#    la scrittura passa per un processo con la parola in `argv` — letto da
#    `chpasswd` con una redirezione **dentro** le virgolette, e cancellato
#    subito, piu' una `trap` per il caso in cui il giro muoia a meta'.
#
# ⚠ Resta una copia in chiaro su disco per la durata di una `chpasswd`, ed e'
#   dichiarata: e' il prezzo per non averla in `ps`, dove la vede chiunque.
#   Il file e' `0600` e sta sotto `$FUORI/tmp`, non in `/tmp`.
#
# ⛔ E la redirezione sta DENTRO le virgolette, mai attorno a `enter.sh`: fuori
#    si porterebbe via la richiesta di parola d'ordine di `sudo`, e lo script
#    resterebbe appeso per sempre in silenzio (`FASI.md` §00-ambiente B3.3,
#    pagata quattro volte).
# ---------------------------------------------------------------------------
set -uo pipefail
E=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CRED=/media/REMOTIX/credenziali-banchi
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ⛔ Un nome tutto suo: `01-b10-lancia.sh` usa `sera-b10-parola`, e due
#    strumenti che scrivono lo stesso file si cancellerebbero la parola a
#    vicenda — la stessa forma che ha fatto nascere il `PREFISSO` di
#    `01-p5-accendi.sh`.
PAROLA_FUORI=$FUORI/tmp/attrezzi-utenti-chpasswd
PAROLA_DENTRO=$DENTRO/tmp/attrezzi-utenti-chpasswd

ripulisci() { rm -f "$PAROLA_FUORI"; }
trap ripulisci EXIT

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ QUESTO ATTREZZO CREAVA `prova` E `prova2` **CIECHI** — e non lo diceva
#
# ⛔ La `useradd` qui sotto non dava nessun gruppo, mentre `src/provisiona.sh`
#    li dava: due posti che creano la stessa cosa, e sono divergiti.  Chi
#    preparava la macchina con l'uno otteneva inquilini che vedono, con l'altro
#    inquilini che non vedranno mai niente — `[M]` 0 sessioni su 4, zero
#    fotogrammi in 90 s (fase 10 §7.4).
#
# ⭐ LA CURA STA IN UN FILE SOLO, `attrezzi-gruppi-scheda.sh`.  ⚠ Ma qui i
#    comandi girano DENTRO il chroot di `enter.sh`, dove quel file non c'e':
#    quindi il file **si stampa** (`--testo`) e il testo si infila nella
#    stringa.  ⇒ La logica resta UNA, e non ce n'e' una copia scritta a mano.
#
# ⚠ E il chroot ha `/dev` in rbind ma un `/etc/group` tutto suo: leggere il
#   **gid dal nodo** e chiedere il nome li' dentro e' proprio quel che serve —
#   un `render` inchiodato di fuori potrebbe non esistere di dentro.
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ manca $GRUPPI_SCHEDA_SH: gli inquilini nascerebbero CIECHI"; exit 2; }
# ⚠ Il testo entra in `"$GRUPPI_SCHEDA_TESTO"`, e la shell NON riespande il
#   risultato di un'espansione: i `$` di la' dentro arrivano intatti.
GRUPPI_SCHEDA_TESTO=$(bash "$GRUPPI_SCHEDA_SH" --testo)
[ -n "$GRUPPI_SCHEDA_TESTO" ] || { ko "⛔ $GRUPPI_SCHEDA_SH --testo non ha stampato niente"; exit 2; }

mkdir -p "$FUORI/tmp" || { ko "⛔ non si crea $FUORI/tmp"; exit 2; }

crea() # $1 nome  $2 uid  $3 parola
{
  local stato
  if bash $E --root "id -u $1 >/dev/null 2>&1"; then
    ok "utente '$1' gia' presente"
  else
    bash $E --root "useradd -u $2 -m -s /bin/bash $1" && ok "utente '$1' creato (uid $2)"
  fi
  # ⛔ D12: la riga «utente:parola» che `chpasswd` mangia si scrive in un file
  #    `0600`, non in una riga di comando.
  # ⛔ `umask` IN UNA SOTTOSHELL — la riga che B10 ha pagato con un giro
  #    intero: `umask 077` nudo resta addosso a tutto quel che viene dopo,
  #    compresi i comandi mandati dentro il contenitore.
  ( umask 077; : > "$PAROLA_FUORI" ) || { ko "⛔ non si scrive $PAROLA_FUORI"; return 2; }
  chmod 600 "$PAROLA_FUORI" || return 2
  # ⛔ `printf` e' un builtin: nessun processo con la parola in `argv`.
  printf '%s:%s\n' "$1" "$3" > "$PAROLA_FUORI"
  bash $E --root "chpasswd < $PAROLA_DENTRO; s=\$?; rm -f $PAROLA_DENTRO; exit \$s"
  stato=$?
  # ⛔ E si cancella SUBITO, non alla fine dello script: la finestra in cui il
  #    file esiste dev'essere quella della `chpasswd` e non tutto il giro.  La
  #    `trap` e' la rete per quando il giro muore, non la cancellazione normale.
  rm -f "$PAROLA_FUORI"
  if [ "$stato" -eq 0 ]; then
    ok "parola di '$1' impostata da un file 0600 — mai in una riga di comando"
  else
    ko "⛔ chpasswd per '$1' esce $stato: la parola NON e' stata impostata"
    return "$stato"
  fi
  # ⭐⭐ I GRUPPI DELLA SCHEDA, LETTI DAI NODI DENTRO IL CHROOT.
  # ⛔ E se non ci entra, questo attrezzo si FERMA: un `prova` cieco manda a
  #    zero fotogrammi ogni banco che parte da qui, e nessuno se ne accorge.
  bash $E --root "$GRUPPI_SCHEDA_TESTO
gruppi_scheda_dai_a $1"
  stato=$?
  [ "$stato" -eq 0 ] || ko "⛔⛔ '$1' NON e' nei gruppi della scheda (uscita $stato): NON usare questo utente per misurare"
  return "$stato"
}

# ⛔ E se 'prova' non nasce sano si esce: proseguire vorrebbe dire lasciare
#    in giro un inquilino che i banchi useranno credendolo buono.
crea prova 1001 parola-di-prova || exit 3

if [ -f "$CRED" ] && grep -q '^prova2:' "$CRED" 2>/dev/null; then
  P2=$(sed -n 's/^prova2:[[:space:]]*//p' "$CRED" | head -1)
  inf "parola di 'prova2' riletta da $CRED"
else
  # ⚠ `head -c 18 /dev/urandom | base64` — nessuno dei tre vede la parola in
  #   `argv`: `base64` la riceve sullo stdin, non come argomento.
  P2=$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 20)
  touch "$CRED"; chmod 600 "$CRED"
  printf 'prova2: %s\n' "$P2" >> "$CRED"
  ok "parola di 'prova2' generata e scritta in $CRED (0600)"
fi
# ⛔ `crea` e' una FUNZIONE, non un programma: questa chiamata non crea nessun
#    `argv`, e la parola non esce dalla shell.
crea prova2 1002 "$P2" || exit 3

echo
for u in prova prova2; do
  if bash $E --root "getent shadow $u | cut -d: -f2 | grep -q '^\\\$'"; then
    ok "$u: parola d'ordine cifrata presente in /etc/shadow"
  else
    ko "⛔ $u: NON ha una parola utilizzabile — PAM lo rifiutera'"
  fi
done
# ⭐ E si RILEGGE dal di dentro, che e' l'unico posto che conta (E1).
bash $E --root "$GRUPPI_SCHEDA_TESTO
for u in prova prova2; do
  m=\$(gruppi_scheda_mancanti \$u)
  if [ -z \"\$m\" ]; then echo \"    OK  ⭐ \$u e' nei gruppi dei nodi della scheda: \$(id -nG \$u)\"
  else echo \"    NO  ⛔⛔ \$u NON e' nei gruppi \$m: la sua sessione NASCE CIECA\"; fi
done"
bash $E --root "getent passwd prova prova2"
ls -l "$CRED"
