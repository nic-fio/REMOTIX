#!/bin/bash
# resto.sh — le cose che restano: rotazione, certificato dell'amministratore,
#            ban + pagina + sblocco.  Dentro il contenitore.
set -uo pipefail
D=/srv/src/remotix
IND=192.168.0.2
PORTA=${1:-7448}
ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.  `python3` e' un PROCESSO: la parola stava nel
#    suo `argv`, cioe' in `/proc/<pid>/cmdline`, leggibile da chiunque.
#
# ⭐ La strada e' quella gia' in casa (`banchi/01-b10-lancia.sh`): file `0600`
#    scritto con `printf` — un **builtin**, quindi nemmeno la scrittura passa
#    per un processo con la parola in `argv` — passato come `--parola-file`, e
#    cancellato con una `trap`.  Nel `cmdline` finisce il PERCORSO.
#
# ⚠ Le parole SBAGLIATE restano dove stanno: non sono il segreto di nessuno, e
#   due strade per la stessa cosa sarebbero la forma **E2**.  Qui pero' comprano
#   qualcosa — la scena e' «tre tentativi falliti» — quindi si dichiarano.
PAROLA=${PAROLA:-parola-di-prova}
PAROLA_FILE=/srv/src/tmp/prodotto-resto-parola

ripulisci_parola() { rm -f "$PAROLA_FILE"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN UNA SOTTOSHELL: nudo resterebbe addosso a tutto quel che segue.
mkdir -p /srv/src/tmp \
  && ( umask 077; : > "$PAROLA_FILE" ) \
  && chmod 600 "$PAROLA_FILE" \
  || { ko "⛔ non si scrive $PAROLA_FILE"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"

accendi() # $1 = dir certificati, $2 = file ban, $3 = registro
{
  nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
    --certificati "$1" --pagina "$D/pagina.html" --ban "$2" >"$3" 2>&1 &
  PID=$!
  sleep 2
  [ -d "/proc/$PID" ]
}
spegni() { kill -TERM "$PID" 2>/dev/null; sleep 1; [ -d "/proc/$PID" ] && kill -KILL "$PID"; return 0; }

# ---------------------------------------------------------------------------
log "1. LA ROTAZIONE — un certificato di sessione a cui restano meno di 2 giorni"
C=/srv/src/cert-rot
rm -rf $C; mkdir -p $C
# il longevo, nostro
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout $C/pagina.key -out $C/pagina.pem -days 365 -nodes -subj "/CN=$IND" \
  -addext "subjectAltName=IP:$IND" >/dev/null 2>&1 && echo "generato da REMOTIX_V2" > $C/pagina.nostro
# il breve, a UN giorno: sotto il margine di 2
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout $C/sessione.key -out $C/sessione.pem -days 1 -nodes -subj "/CN=$IND" \
  -addext "subjectAltName=IP:$IND" >/dev/null 2>&1 && echo "generato da REMOTIX_V2" > $C/sessione.nostro
chmod 600 $C/*.key
VECCHIA=$(openssl x509 -in $C/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
echo "    impronta PRIMA: $VECCHIA"

accendi $C /srv/src/ban-rot /srv/src/rot.log || { ko "morto"; cat /srv/src/rot.log; exit 2; }
NUOVA=$(openssl x509 -in $C/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
echo "    impronta DOPO:  $NUOVA"
[ "$VECCHIA" != "$NUOVA" ] && ok "il certificato di sessione E' stato ruotato all'avvio" || ko "NON ruotato"
GIORNI=$(( ( $(date -d "$(openssl x509 -in $C/sessione.pem -noout -enddate | cut -d= -f2)" +%s) - $(date +%s) ) / 86400 ))
[ "$GIORNI" -le 14 ] && [ "$GIORNI" -ge 10 ] && ok "il nuovo scade fra $GIORNI giorni (tetto 14)" || ko "scade fra $GIORNI giorni"
curl -sk "https://$IND:$PORTA/impronta" | grep -F -q "$NUOVA" && ok "/impronta serve la NUOVA" || ko "/impronta serve una impronta vecchia"
curl -sk "https://$IND:$PORTA/" | grep -F -q "$NUOVA" && ok "la pagina porta la NUOVA" || ko "la pagina porta una impronta vecchia"
grep -a -F -q "rotazione del certificato di SESSIONE" /srv/src/rot.log && ok "e lo dice nel registro" || ko "il registro tace sulla rotazione"
spegni

# ---------------------------------------------------------------------------
log "2. IL CERTIFICATO DELL'AMMINISTRATORE non si rigenera (RCP.md 4.1, B13.3)"
rm -f $C/pagina.nostro           # via la marca: adesso «non e' nostro»
IMP=$(openssl x509 -in $C/pagina.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
accendi $C /srv/src/ban-rot /srv/src/adm.log || { ko "morto"; cat /srv/src/adm.log; exit 2; }
DOPO=$(openssl x509 -in $C/pagina.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
[ "$IMP" = "$DOPO" ] && ok "il certificato della pagina NON e' stato toccato" || ko "e' stato RIGENERATO: viola §4.1"
grep -a -F -q "non e' nostro" /srv/src/adm.log && ok "e lo dichiara nel registro" || ko "il registro non lo dice"
spegni

# ---------------------------------------------------------------------------
log "3. IL BAN — tre autenticazioni fallite, poi la pagina lo DICE (SPECIFICHE 4.2)"
rm -rf /srv/src/cert-ban /srv/src/ban-prova; mkdir -p /srv/src/cert-ban
accendi /srv/src/cert-ban /srv/src/ban-prova /srv/src/ban.log || { ko "morto"; cat /srv/src/ban.log; exit 2; }
for i in 1 2 3; do
  timeout 30 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
    --utente prova --parola SBAGLIATA-$i >/dev/null 2>&1
  echo "    tentativo $i: uscita $?"
done
log "   il quarto, e la pagina"
timeout 30 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
  --utente prova --parola-file "$PAROLA_FILE" 2>&1 | tail -4
curl -sk "https://$IND:$PORTA/" -o /srv/src/pagina-ban.html
if grep -a -F -q "tentativi di accesso da questo indirizzo sono esauriti" /srv/src/pagina-ban.html; then
  ok "⭐ la pagina SI CARICA e dice che i tentativi sono esauriti"
else
  ko "la pagina non lo dice"
  grep -a -o 'AVVISO = "[^"]*"' /srv/src/pagina-ban.html | head -1
fi
echo "    -- il file dei ban:"
cat /srv/src/ban-prova 2>&1 | sed 's/^/        /'
spegni

log "   e lo SBLOCCO (SPECIFICHE 4.2: l'altra via d'uscita)"
"$D/remotix" --ban /srv/src/ban-prova --sblocca "$IND" --nome "$IND" 2>&1 | sed 's/^/    /'
echo "    uscita: $?"
echo "    -- il file dei ban dopo lo sblocco:"
cat /srv/src/ban-prova 2>&1 | sed 's/^/        /'

log "   e la pagina torna normale"
accendi /srv/src/cert-ban /srv/src/ban-prova /srv/src/ban2.log || { ko "morto"; exit 2; }
curl -sk "https://$IND:$PORTA/" -o /srv/src/pagina-dopo.html
grep -a -F -q "tentativi di accesso da questo indirizzo sono esauriti" /srv/src/pagina-dopo.html \
  && ko "l'avviso c'e' ancora" || ok "l'avviso e' sparito"
timeout 30 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
  --utente prova --parola-file "$PAROLA_FILE" 2>&1 | tail -3
spegni
