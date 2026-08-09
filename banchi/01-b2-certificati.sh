#!/bin/bash
#
# 01-b2-certificati.sh — i due certificati del banco B2, con i vincoli veri.
#
#   bash 01-b2-certificati.sh [indirizzo]     predefinito: 192.168.0.2
#
# ---------------------------------------------------------------------------
# PERCHE' DUE E NON UNO
#
# `RCP.md` §4.1-bis ne impone due, e tenerli distinti e' normativo:
#
#   - il LONGEVO serve la pagina.  E' quello su cui l'utente concede
#     l'eccezione, quindi NON deve cambiare piu' spesso del necessario;
#   - il BREVE (≤ 14 giorni) serve la sessione WebTransport, e ruota da se'.
#     La sua impronta viaggia dentro la pagina (`serverCertificateHashes`).
#
# ⚠ Confonderli fa ricomparire l'avviso ogni due settimane, e nessuno
#   collegherebbe le due cose.  Il banco li tiene separati fin da adesso,
#   perche' e' esattamente il difetto che B13.1 deve poter vedere.
#
# ---------------------------------------------------------------------------
# I VINCOLI, E DA DOVE VENGONO
#
#   chiave      ECDSA P-256  — `RCP.md` §4.1: mai RSA, e nemmeno Ed25519.
#                              E' l'unica che tiene aperta la strada di
#                              `serverCertificateHashes` [S].
#   durata      ≤ 14 giorni per la sessione [S].  Qui 13, per avere margine.
#   nome        subjectAltName = l'indirizzo su cui il server risponde.
#               ⚠ Un SAN che non combacia fa mostrare al browser un avviso
#                 DIVERSO, e alcuni non offrono nemmeno il clic per proseguire.
#   impronta    SHA-256 del certificato in forma DER — NON della chiave
#               pubblica.  ⛔ E' il rilievo R1.14 di `RCP.md`: chi pubblicava
#               quella della chiave otteneva un confronto che non combacia
#               mai, con il sintomo «WebTransport non si connette» e nessun
#               errore che nomini l'impronta.
#   permessi    0600 sulla chiave privata (§4.1).
# ---------------------------------------------------------------------------
set -uo pipefail

IND=${1:-192.168.0.2}
DIR=/media/REMOTIX/b2-certificati

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

mkdir -p "$DIR" || exit 2

# Il SAN va scelto per forma: un indirizzo IP non si mette come DNS.
if [[ "$IND" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	SAN="IP:$IND"
else
	SAN="DNS:$IND"
fi
inf "indirizzo $IND  ->  subjectAltName = $SAN"

genera()
{
	local nome=$1 giorni=$2
	openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
		-keyout "$DIR/$nome.key" -out "$DIR/$nome.pem" \
		-days "$giorni" -nodes -subj "/CN=$IND" \
		-addext "subjectAltName=$SAN" >/dev/null 2>&1 || return 1
	chmod 600 "$DIR/$nome.key"
}

log "Il certificato LONGEVO — la pagina"
if genera pagina 365; then
	ok "pagina.pem  (365 giorni)"
else
	ko "generazione fallita"; exit 3
fi

log "Il certificato BREVE — la sessione WebTransport"
if genera sessione 13; then
	ok "sessione.pem  (13 giorni, sotto il tetto di 14)"
else
	ko "generazione fallita"; exit 3
fi

# ---------------------------------------------------------------------------
# I CONTROLLI, e sono quattro.  Un certificato che «esiste» non e' un
# certificato che vale: ciascuno di questi ha un modo di fallire in silenzio.
# ---------------------------------------------------------------------------
log "I controlli"

ESITO=0

# 1. la curva.  Un `-newkey ec` senza la curva giusta produce comunque un file.
for n in pagina sessione; do
	CURVA=$(openssl pkey -in "$DIR/$n.key" -noout -text 2>/dev/null | grep -o 'prime256v1\|secp384r1\|secp521r1' | head -1)
	if [ "$CURVA" = prime256v1 ]; then
		ok "$n: curva $CURVA"
	else
		ko "$n: curva '$CURVA' — attesa prime256v1"; ESITO=1
	fi
done

# 2. il SAN.  ⛔ `-addext` viene ignorato in silenzio da certe versioni di
#    openssl se la richiesta e' costruita diversamente: si verifica, non si
#    spera.
for n in pagina sessione; do
	if openssl x509 -in "$DIR/$n.pem" -noout -text 2>/dev/null | grep -q "$IND"; then
		ok "$n: subjectAltName contiene $IND"
	else
		ko "$n: subjectAltName NON contiene $IND"; ESITO=1
	fi
done

# 3. la durata della sessione, in giorni veri.
FINE=$(openssl x509 -in "$DIR/sessione.pem" -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$FINE" ]; then
	SEC=$(( ($(date -d "$FINE" +%s) - $(date +%s)) / 86400 ))
	if [ "$SEC" -le 14 ] && [ "$SEC" -ge 1 ]; then
		ok "sessione: scade fra $SEC giorni (tetto 14)"
	else
		ko "sessione: scade fra $SEC giorni — fuori dal tetto di 14"; ESITO=1
	fi
fi

# 4. ⛔ i due certificati DEVONO essere diversi.  E' il difetto che B13.1
#    cerca, e qui si verifica alla nascita invece che due settimane dopo.
IMP_PAG=$(openssl x509 -in "$DIR/pagina.pem"   -outform der 2>/dev/null | openssl dgst -sha256 -binary | base64 -w0)
IMP_SES=$(openssl x509 -in "$DIR/sessione.pem" -outform der 2>/dev/null | openssl dgst -sha256 -binary | base64 -w0)
if [ "$IMP_PAG" != "$IMP_SES" ] && [ -n "$IMP_SES" ]; then
	ok "i due certificati sono due (impronte diverse)"
else
	ko "i due certificati sono LO STESSO — e' il difetto di B13.1"; ESITO=1
fi

# ---------------------------------------------------------------------------
log "L'impronta della SESSIONE — quella che va nella pagina"
inf "SHA-256 del DER, base64:"
printf '\n        %s\n\n' "$IMP_SES"
# Anche in esadecimale, perche' e' la forma che si legge nei registri e nei
# messaggi d'errore dei browser.
printf '    --  la stessa in esadecimale:\n'
openssl x509 -in "$DIR/sessione.pem" -outform der 2>/dev/null | openssl dgst -sha256 | sed 's/^/        /'

printf '\n'
if [ "$ESITO" -eq 0 ]; then
	ok "quattro controlli su quattro"
else
	ko "un controllo e' fallito: i certificati NON si usano"
fi
exit "$ESITO"
