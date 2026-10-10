#!/bin/bash
# fumo.sh — smoke test of the server, INSIDE the container.
set -uo pipefail
D=/srv/src/remotix
IND=${1:-127.0.0.1}
PORTA=${2:-7447}
REG=/srv/src/remotix-fumo.log

ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

log "Who holds port $PORTA before starting"
ss -lunp 2>/dev/null | grep ":$PORTA" || echo "    (nobody on UDP)"
ss -ltnp 2>/dev/null | grep ":$PORTA" || echo "    (nobody on TCP)"

rm -f "$REG"
rm -rf /srv/src/remotix-cert
log "Starting"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban --parlantina >"$REG" 2>&1 &
PID=$!
sleep 2

if [ -d "/proc/$PID" ]; then ok "the server is running, pid $PID"; else ko "the server DIED at once"; cat "$REG"; exit 2; fi

log "The startup log"
cat "$REG"

log "The two certificates on disk"
ls -l /srv/src/remotix-cert
echo "    -- key permissions:"
stat -c '        %a %n' /srv/src/remotix-cert/*.key

log "The fingerprint computed by openssl, for an independent comparison"
IMP=$(openssl x509 -in /srv/src/remotix-cert/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0)
echo "        $IMP"

log "GET / over TLS"
curl -sk -D /srv/src/testa.txt "https://$IND:$PORTA/" -o /srv/src/corpo.html
E=$?
echo "    uscita curl: $E"
cat /srv/src/testa.txt

log "The two isolation headers (SPECIFICHE.md 11.5)"
for h in "Cross-Origin-Opener-Policy: same-origin" "Cross-Origin-Embedder-Policy: require-corp" "Cross-Origin-Resource-Policy: same-origin"; do
  if grep -a -i -F -q "$h" /srv/src/testa.txt; then ok "$h"; else ko "MISSING: $h"; fi
done

log "The fingerprint INSIDE the page"
if grep -a -F -q "$IMP" /srv/src/corpo.html; then ok "the page carries the fingerprint of the session certificate"; else ko "the page does NOT carry the fingerprint"; grep -a -o 'IMPRONTA_SERVITA = "[^"]*"' /srv/src/corpo.html; fi
if grep -a -F -q "__IMPRONTA__" /srv/src/corpo.html; then ko "the __IMPRONTA__ marker was left unreplaced"; else ok "no unreplaced marker"; fi

log "GET /impronta (the endpoint of RCP.md 4.1-bis)"
curl -sk -D /srv/src/testa2.txt "https://$IND:$PORTA/impronta" -o /srv/src/imp.json
cat /srv/src/imp.json
if grep -a -F -q "$IMP" /srv/src/imp.json; then ok "the endpoint serves the current fingerprint"; else ko "the endpoint does NOT serve the current fingerprint"; fi
if grep -a -i -F -q "Cross-Origin-Resource-Policy" /srv/src/testa2.txt; then ok "/impronta too goes out isolated"; else ko "/impronta does NOT go out isolated"; fi

log "GET /something-that-does-not-exist"
curl -sk -o /dev/null -w '    status: %{http_code}\n' "https://$IND:$PORTA/nulla"

log "The TWO listeners with the same port number (RCP.md 2.4)"
ss -lunp 2>/dev/null | grep ":$PORTA" && ok "UDP" || ko "no UDP"
ss -ltnp 2>/dev/null | grep ":$PORTA" && ok "TCP" || ko "no TCP"

log "Stopping"
kill -TERM "$PID"
sleep 1
if [ -d "/proc/$PID" ]; then kill -KILL "$PID"; ko "it did not stop with TERM"; else ok "stopped"; fi

log "The full log"
cat "$REG"
