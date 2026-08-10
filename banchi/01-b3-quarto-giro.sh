#!/bin/bash
#
# 01-b3-quarto-giro.sh — ⚠ gira DENTRO il contenitore.
#
#   ⛔ la 2ª DOPO IL SILENZIO della 1ª — 35 secondi, con `max_idle_timeout`
#      alzato a 120.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' 35 SECONDI A TIMEOUT 120, E NON 30 A TIMEOUT PREDEFINITO
#
# E' il rilievo **R3.19**, ed e' la differenza fra una prova e una benedizione.
#
# Con il tetto d'inattivita' predefinito (30 s), a chiudere la prima connessione
# sarebbe **QUIC**: la struttura legata alla connessione si libererebbe da se',
# e un server **senza nessuna nozione di sessione staccata** resterebbe verde.
# ⛔ Il banco benedirebbe la violazione di **I4**.
#
# Alzando il tetto a 120 secondi, dopo 35 la connessione della prima e' ancora
# **viva** — e se il posto si libera lo stesso, e' perche' il server ha il suo
# **orologio del silenzio** (`SPECIFICHE.md` §5.3, `DECISIONI.md` §4.4).
#
# ---------------------------------------------------------------------------
# ⛔ E IL CONTROLLO CHE DICE NO, SENZA IL QUALE NON SI PROVA NIENTE
#
# «Dopo 35 secondi la seconda entra» e' compatibile con **«la seconda entra
# sempre»**, cioe' con un server che non guarda il registro affatto.  Per
# questo il giro ha due tempi:
#
#   a +6 s   la seconda DEVE essere rifiutata con GIA_ATTIVA_REMOTA
#   a +35 s  la terza  DEVE entrare
#
# ⭐ Sono lo stesso server, lo stesso utente e lo stesso silenzio: cambia solo
#    l'orologio.  Senza il primo tempo, il secondo non dimostra l'orologio.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/srv/src
IND=${1:-192.168.0.2}
PORTA=${2:-7447}
UTENTE=prova
PAROLA=parola-di-prova

ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

cliente() # $1 = etichetta, $2.. = opzioni
{
	local et=$1; shift
	python3 -u "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
		--utente "$UTENTE" --parola "$PAROLA" \
		--registra "$QUI/b3-$et.rcpreg" "$@" > "$QUI/b3-$et.log" 2>&1
}

rm -f "$QUI/b3-muta.log" "$QUI/b3-muta.attaccato" "$QUI/b3-presto.log" \
      "$QUI/b3-tardi.log"

# La prima si attacca e poi TACE per 45 secondi.  ⚠ Non manda niente: i
# riscontri di QUIC che partono nel frattempo sono del trasporto, e
# l'orologio del silenzio si misura sui byte di RCP.
cliente muta --resta 45 --segnale "$QUI/b3-muta.attaccato" &
MUTA=$!

ATTACCATA=no
for _ in $(seq 1 15); do
	[ -f "$QUI/b3-muta.attaccato" ] && { ATTACCATA=si; break; }
	sleep 1
done
if [ "$ATTACCATA" != si ]; then
	ko "la prima non si e' attaccata: il quarto giro non prova niente"
	sed 's/^/        /' "$QUI/b3-muta.log"
	kill "$MUTA" 2>/dev/null
	exit 3
fi
T0=$(date +%s)
ok "la prima e' attaccata, e da adesso tace"

ESITO=0

# ── a +6 s: il controllo che dice NO ────────────────────────────────────────
sleep 6
inf "+6 s — la seconda arriva PRIMA che l'orologio scatti"
cliente presto
if grep -q "GIA_ATTIVA_REMOTA" "$QUI/b3-presto.log"; then
	ok "⭐ rifiutata con GIA_ATTIVA_REMOTA: il posto e' ancora occupato"
else
	ko "⛔ NON rifiutata: il server non guarda il registro, e il secondo"
	ko "   tempo di questo giro non dimostrerebbe niente"
	tail -4 "$QUI/b3-presto.log" | sed 's/^/        /'
	ESITO=1
fi

# ── a +35 s: la terza deve ENTRARE ──────────────────────────────────────────
while [ $(( $(date +%s) - T0 )) -lt 35 ]; do
	sleep 1
done
inf "+$(( $(date +%s) - T0 )) s — la terza arriva DOPO i trenta secondi di silenzio"
cliente tardi
if grep -q "SESSIONE" "$QUI/b3-tardi.log"; then
	ok "⭐ ENTRATA: chi tace e' staccato, chi arriva entra (§5.3, §4.4)"
else
	ko "⛔ NON entrata: il server non ha l'orologio del silenzio, oppure"
	ko "   lo misura sui byte di QUIC invece che su quelli di RCP"
	tail -4 "$QUI/b3-tardi.log" | sed 's/^/        /'
	ESITO=1
fi

# ⛔ E la connessione della prima dev'essere ANCORA VIVA: se fosse caduta,
#    a liberare il posto sarebbe stato QUIC e non il server — che e'
#    esattamente quel che questo giro esiste per escludere.
if [ -d "/proc/$MUTA" ]; then
	ok "⭐ e la connessione della prima e' ancora viva: a liberare il posto"
	ok "   e' stato il SERVER, non il tetto d'inattivita' di QUIC"
else
	ko "⛔ la prima e' gia' morta: non si puo' dire chi ha liberato il posto"
	ESITO=1
fi

wait "$MUTA" 2>/dev/null
exit "$ESITO"
