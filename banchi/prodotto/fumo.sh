#!/bin/bash
# fumo.sh — prova di fumo del server, DENTRO il contenitore.
set -uo pipefail
D=/srv/src/remotix
IND=${1:-127.0.0.1}
PORTA=${2:-7447}
REG=/srv/src/remotix-fumo.log

ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

log "Chi occupa la porta $PORTA prima di cominciare"
ss -lunp 2>/dev/null | grep ":$PORTA" || echo "    (nessuno in UDP)"
ss -ltnp 2>/dev/null | grep ":$PORTA" || echo "    (nessuno in TCP)"

rm -f "$REG"
rm -rf /srv/src/remotix-cert
log "Si accende"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban --parlantina >"$REG" 2>&1 &
PID=$!
sleep 2

if [ -d "/proc/$PID" ]; then ok "il server gira, pid $PID"; else ko "il server e' MORTO subito"; cat "$REG"; exit 2; fi

log "Il registro d'avvio"
cat "$REG"

log "I due certificati sul disco"
ls -l /srv/src/remotix-cert
echo "    -- permessi delle chiavi:"
stat -c '        %a %n' /srv/src/remotix-cert/*.key

log "L'impronta calcolata da openssl, per confronto indipendente"
IMP=$(openssl x509 -in /srv/src/remotix-cert/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
echo "        $IMP"

log "GET / in TLS"
curl -sk -D /srv/src/testa.txt "https://$IND:$PORTA/" -o /srv/src/corpo.html
E=$?
echo "    uscita curl: $E"
cat /srv/src/testa.txt

log "Le due intestazioni di isolamento (SPECIFICHE.md 11.5)"
for h in "Cross-Origin-Opener-Policy: same-origin" "Cross-Origin-Embedder-Policy: require-corp" "Cross-Origin-Resource-Policy: same-origin"; do
  if grep -a -i -F -q "$h" /srv/src/testa.txt; then ok "$h"; else ko "MANCA: $h"; fi
done

log "L'impronta DENTRO la pagina"
if grep -a -F -q "$IMP" /srv/src/corpo.html; then ok "la pagina porta l'impronta del certificato di sessione"; else ko "la pagina NON porta l'impronta"; grep -a -o 'IMPRONTA_SERVITA = "[^"]*"' /srv/src/corpo.html; fi
if grep -a -F -q "__IMPRONTA__" /srv/src/corpo.html; then ko "il segno __IMPRONTA__ e' rimasto non sostituito"; else ok "nessun segno non sostituito"; fi

log "GET /impronta (l'endpoint di RCP.md 4.1-bis)"
curl -sk -D /srv/src/testa2.txt "https://$IND:$PORTA/impronta" -o /srv/src/imp.json
cat /srv/src/imp.json
if grep -a -F -q "$IMP" /srv/src/imp.json; then ok "l'endpoint serve l'impronta corrente"; else ko "l'endpoint NON serve l'impronta corrente"; fi
if grep -a -i -F -q "Cross-Origin-Resource-Policy" /srv/src/testa2.txt; then ok "anche /impronta esce isolato"; else ko "/impronta NON esce isolato"; fi

log "GET /qualcosa-che-non-esiste"
curl -sk -o /dev/null -w '    stato: %{http_code}\n' "https://$IND:$PORTA/nulla"

log "I DUE ascoltatori con lo stesso numero di porta (RCP.md 2.4)"
ss -lunp 2>/dev/null | grep ":$PORTA" && ok "UDP" || ko "niente UDP"
ss -ltnp 2>/dev/null | grep ":$PORTA" && ok "TCP" || ko "niente TCP"

log "Si spegne"
kill -TERM "$PID"
sleep 1
if [ -d "/proc/$PID" ]; then kill -KILL "$PID"; ko "non si e' fermato con TERM"; else ok "fermato"; fi

log "Il registro completo"
cat "$REG"
