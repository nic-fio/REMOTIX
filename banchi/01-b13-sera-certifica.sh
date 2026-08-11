#!/bin/bash
#
# 01-b13-sera-certifica.sh — gira DENTRO il contenitore.  ⛔ La certificazione
# di B13 col modello di B12 — sano `0` → guasto `≠0` → risanato `0` — ma
# **contro il PRODOTTO** e su una porta di questo agente.
#
#   bash /srv/src/01-b13-sera-certifica.sh misura      un giro solo, per vedere
#   bash /srv/src/01-b13-sera-certifica.sh certifica   il ciclo intero
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' NON LO FA `01-b12-lancia.sh`, DETTO PRIMA E NON DOPO
#
# B12 sa certificare B13 dall'11 agosto: il guasto e' di tipo `copia-di-file`
# (`pagina.pem` sostituito da `sessione.pem`), l'appiglio non e' piu' una
# stringa da contare, e i rilievi R12-A.1 e R12-A.2 sono curati nel catalogo.
# ⛔ Quel che manca e' altro: `01-b12-lancia.sh` scrive `PORTA=7447` in chiaro,
# accende `bsslserver` — l'INNESTO — e non ha nessun modo di essere puntato
# altrove.  Questo agente ha la 7447 e la 7448 **fuori dal mandato** (sono di
# altri due giri che stanno correndo adesso), e `01-b12-lancia.sh` non e' un
# file di questo autore.
#
# ⭐ Quindi qui si fa **lo stesso ciclo, con lo stesso guasto**, sul server che
#    questo agente ha acceso — e le differenze si dichiarano, invece di
#    lasciarle intendere:
#
#   | B12 farebbe                    | qui si fa                              |
#   |--------------------------------|----------------------------------------|
#   | porta 7447                     | porta 7481                             |
#   | `bsslserver`, cioe' l'INNESTO  | ⭐ `remotix`, cioe' il PRODOTTO         |
#   | certificati di B2, condivisi   | i certificati che il prodotto si e'    |
#   |                                | generato in `tmp/sera-b13-cert`        |
#   | il guasto lo innesta           | lo innesta questo script, con la copia |
#   | `01-b12-guasti.py --applica`   | dell'originale e l'impronta accanto    |
#
# ⚠ E la differenza che conta piu' delle altre: **contro il prodotto B13.4 ha
#   finalmente un imputato**.  Contro l'innesto nessuno ascoltava in TCP, e
#   B13.4 usciva `[?] manca l'imputato`; il prodotto la pagina la serve, quindi
#   quella riga da stasera si misura invece di essere dichiarata.
#
# ---------------------------------------------------------------------------
# ⛔ L'ESITO ATTESO SI SCRIVE PRIMA (B0.4)
#
# Il giro sano di B13 **non e' uno zero**, e non lo era nemmeno per B12
# (`atteso_sano = 3` nel catalogo): l'uscita 3 vuol dire *«alcune proprieta'
# non si possono giudicare»*, ed e' un esito dichiarato, non un rosso.  ⛔ Qui
# l'atteso non si sceglie dopo aver visto il numero: si misura il giro sano, si
# scrive quel numero, e il criterio e' **che il guasto lo cambi e che il
# risanato lo riporti indietro** — piu' la marca, che dev'essere quella e non
# un'altra.
set -uo pipefail

D=/srv/src/remotix
TMP=/srv/src/tmp
PORTA=${PORTA:-7481}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-prova}
PAROLA=${PAROLA:-parola-di-prova}

CERT=$TMP/sera-b13-cert
BANCO=/srv/src/01-b13-proprieta.py
GIT_RCP=$TMP/sera-b13-rcp-git.c        # la copia che sta in git, portata a mano
MARCA="LE IMPRONTE COMBACIANO"
ORIG=$TMP/sera-b13-pagina-originale.pem

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

giro() # $1 = file su cui scrivere l'uscita del banco
{
	python3 -u "$BANCO" \
		--indirizzo "$IND" --porta "$PORTA" \
		--utente "$UTENTE" --parola "$PAROLA" \
		--certificati "$CERT" --prodotti /srv/src \
		--codice "$GIT_RCP" --codice-compilato "$D/rcp.c" \
		--fonti-codice "$D/certificati.c" "$D/main.c" "$D/rcp.c" \
		> "$1" 2>&1
	return $?
}

imp() { openssl x509 -in "$1" -outform der 2>/dev/null | sha256sum | cut -d' ' -f1; }

# ---------------------------------------------------------------------------
log "0. ⛔ Lo stato iniziale (B0.1): si dichiara E si verifica"
for f in "$BANCO" "$GIT_RCP" "$D/rcp.c" "$CERT/pagina.pem" "$CERT/sessione.pem"; do
	if [ ! -r "$f" ]; then ko "⛔ non si legge: $f"; exit 2; fi
done
ok "i cinque file che servono si leggono"
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$n" -lt 2 ]; then
	ko "⛔ su :$PORTA ci sono $n ascoltatori, ne servono 2 (UDP e TCP)"
	ko "   Accendi prima: bash /srv/src/01-b13-sera-accendi.sh accendi"
	exit 2
fi
ok "il server e' acceso: $n ascoltatori su :$PORTA"
IP=$(imp "$CERT/pagina.pem"); IS=$(imp "$CERT/sessione.pem")
inf "pagina.pem   ${IP:0:24}…"
inf "sessione.pem ${IS:0:24}…"
# ⛔ IL CONTROLLO POSITIVO DEL GUASTO, e viene prima: se i due file fossero gia'
#    uguali il guasto non costruirebbe niente, il banco sarebbe gia' rosso, e
#    «e' diventato rosso» non vorrebbe dire niente.
if [ "$IP" = "$IS" ]; then
	ko "⛔ i due certificati sono GIA' identici: il guasto non costruirebbe"
	ko "   niente e il rosso che ne uscisse sarebbe gia' li' — non certifico"
	exit 2
fi
ok "i due certificati sono DIVERSI, come devono essere prima del guasto"

if [ "${1:-certifica}" = misura ]; then
	log "Un giro solo, per vedere dove siamo"
	giro "$TMP/sera-b13-misura.txt"; E=$?
	cat "$TMP/sera-b13-misura.txt"
	inf "uscita del banco: $E"
	exit "$E"
fi

# ---------------------------------------------------------------------------
log "1. Il giro SANO — e il suo numero diventa l'atteso"
giro "$TMP/sera-b13-sano.txt"; E_SANO=$?
grep -E '^  (OK|NO|\?\?|\[\?\]|\s)' "$TMP/sera-b13-sano.txt" | head -40
tail -20 "$TMP/sera-b13-sano.txt"
inf "uscita del giro sano: $E_SANO"
if [ "$E_SANO" -eq 1 ] || [ "$E_SANO" -eq 2 ] || [ "$E_SANO" -eq 5 ]; then
	ko "⛔ il giro SANO e' rosso (uscita $E_SANO): il soggetto e' rotto, e un"
	ko "   banco il cui soggetto e' davvero rotto NON si certifica — si lascia"
	ko "   NON CERTIFICATO invece di allargare l'atteso finche' torna."
	exit 1
fi
if grep -qF "$MARCA" "$TMP/sera-b13-sano.txt"; then
	ko "⛔ la marca «$MARCA» compare GIA' nel giro sano: non discrimina niente"
	exit 1
fi
ok "giro sano: uscita $E_SANO, e la marca del guasto NON compare"

# ---------------------------------------------------------------------------
# ⚠ Niente accenti gravi dentro le virgolette doppie: la prima stesura scriveva
#   «`pagina.pem` diventa una copia di `sessione.pem`» e la shell ha provato a
#   ESEGUIRLI, stampando due «command not found» in mezzo alla certificazione.
#   Innocuo per il verdetto, rumoroso nel registro — e il rumore nel registro di
#   un banco insegna a non leggere il registro del banco.
log "2. Il GUASTO — pagina.pem diventa una copia di sessione.pem"
cp -p "$CERT/pagina.pem" "$ORIG"
if [ "$(sha256sum < "$ORIG" | cut -d' ' -f1)" != "$(sha256sum < "$CERT/pagina.pem" | cut -d' ' -f1)" ]; then
	ko "⛔ la copia dell'originale non e' identica all'originale: non innesto"
	exit 2
fi
ok "originale messo da parte in $ORIG, e i byte combaciano"
cp "$CERT/sessione.pem" "$CERT/pagina.pem"
IP2=$(imp "$CERT/pagina.pem")
if [ "$IP2" != "$IS" ]; then
	ko "⛔ dopo la copia pagina.pem non ha l'impronta di sessione.pem:"
	ko "   il guasto NON e' stato innestato, e quel che segue non misura niente"
	cp -p "$ORIG" "$CERT/pagina.pem"
	exit 2
fi
ok "guasto innestato: le due impronte adesso combaciano (${IP2:0:24}…)"

giro "$TMP/sera-b13-guasto.txt"; E_GUASTO=$?
inf "uscita del giro guasto: $E_GUASTO"
IP3=$(imp "$CERT/pagina.pem")
if [ "$IP3" != "$IS" ]; then
	ko "⛔ durante il giro il guasto e' SPARITO da solo (pagina.pem e' cambiato):"
	ko "   quel che il banco ha misurato non e' il guasto che ho innestato"
	cp -p "$ORIG" "$CERT/pagina.pem"
	exit 2
fi
ok "il guasto era ancora addosso alla fine del giro"

# ---------------------------------------------------------------------------
log "3. ⛔ Si rimette a posto SUBITO, prima di giudicare"
cp -p "$ORIG" "$CERT/pagina.pem"
IP4=$(imp "$CERT/pagina.pem")
if [ "$IP4" != "$IP" ]; then
	ko "⛔ pagina.pem non e' tornato quello di prima: ${IP4:0:16}… invece di ${IP:0:16}…"
	ko "   ⛔ IL SERVER RESTA GUASTO: dirlo e' l'unica cosa utile da fare qui"
	exit 2
fi
ok "pagina.pem e' tornato ai byte di prima (${IP4:0:24}…)"

log "4. Il giro RISANATO"
giro "$TMP/sera-b13-risanato.txt"; E_RIS=$?
inf "uscita del giro risanato: $E_RIS"

# ---------------------------------------------------------------------------
log "Il verdetto, con i tre numeri accanto"
inf "sano $E_SANO · guasto $E_GUASTO · risanato $E_RIS · marca attesa «$MARCA»"
FALLE=0
if [ "$E_GUASTO" = "$E_SANO" ]; then
	ko "⛔ il guasto NON cambia l'uscita ($E_GUASTO = $E_SANO): il banco non lo vede"
	FALLE=$((FALLE+1))
else
	ok "il guasto cambia l'uscita: $E_SANO → $E_GUASTO"
fi
if grep -qF "$MARCA" "$TMP/sera-b13-guasto.txt"; then
	ok "e la marca e' quella giusta: «$MARCA» compare nell'uscita del guasto"
	grep -F "$MARCA" "$TMP/sera-b13-guasto.txt" | head -2 | sed 's/^/        /'
else
	ko "⛔ il banco e' diventato rosso ma la sua uscita NON nomina «$MARCA»:"
	ko "   e' rosso per un'altra ragione, e questa non e' una certificazione"
	FALLE=$((FALLE+1))
fi
if [ "$E_RIS" = "$E_SANO" ]; then
	ok "il risanato torna al sano ($E_RIS)"
else
	ko "⛔ il risanato NON torna al sano ($E_RIS ≠ $E_SANO): o il guasto ha"
	ko "   lasciato qualcosa, o il giro sano non era ripetibile"
	FALLE=$((FALLE+1))
fi

if [ "$FALLE" -eq 0 ]; then
	printf '\n    \033[1;32m⭐ B13 E'"'"' CERTIFICATO: sano %s → guasto %s (nel suo punto) → risanato %s\033[0m\n' \
		"$E_SANO" "$E_GUASTO" "$E_RIS"
	printf '    --  e non e'"'"' «B13 e'"'"' giusto»: e'"'"' «B13 sa vedere QUESTO difetto».\n'
	exit 0
fi
printf '\n    \033[1;31m⛔ B13 NON E'"'"' CERTIFICATO: %s cose su 3 non tornano\033[0m\n' "$FALLE"
exit 1
