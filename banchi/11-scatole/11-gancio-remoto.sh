#!/bin/bash
# ===========================================================================
# 11-gancio-remoto.sh — ⭐ IL PEZZO CHE GIRA **SULLA MACCHINA DI PROVA**
# ===========================================================================
#
#   bash 11-gancio-remoto.sh <file-esito> gira --famiglia rete …
#
# ⛔ Non lo lancia una persona: lo lancia `11-gancio.sh remoto` dal portatile,
#    dentro un'unita' `systemd-run`, perche' la famiglia veloce costa `[M]` 173 s
#    e un comando lungo in ssh diretto non si porta a casa.
#
# ---------------------------------------------------------------------------
# ⛔⛔ ESISTE PER UNA RAGIONE SOLA, e va detta: **un'unita' transitoria che
#     RIESCE sparisce.**
#
# `systemd-run --unit=X …`: quando il comando esce **0**, systemd raccoglie
# l'unita' e `systemctl is-active X` risponde `inactive`.  ⇒ ⛔ Da fuori
# «sparita perche' e' andata bene» e **«non e' mai partita»** hanno esattamente
# lo stesso aspetto — e `systemctl show -p ExecMainStatus` risponde **vuoto** in
# tutt'e due i casi.
# ⇒ ⚠ Chi ha lanciato leggerebbe un silenzio e dovrebbe indovinare.  E' la
#   forma d'errore di `LEZIONI.md` §1.46: un giro che non ha girato e che
#   somiglia a uno riuscito.
#
# ⭐ Quindi l'esito non si deduce da systemd: **si scrive in un file**, e chi ha
#   lanciato lo legge.  Il file e' anche il segnale di «ho finito»: finche' non
#   c'e', il giro sta ancora girando.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)

if [ $# -lt 1 ]; then
	printf 'uso: bash %s <file-esito> gira --famiglia <nome> …\n' "$0" >&2
	exit 2
fi

ESITO_FILE=$1
shift

# ⛔ Si cancella QUI, non solo da chi lancia: un file d'esito vecchio letto come
#    se fosse di questo giro e' un giro che riferisce l'esito di un altro.
rm -f "$ESITO_FILE"

bash "$QUI/11-gancio.sh" "$@"
E=$?

# ⚠ E si scrive **dopo**, mai prima: il file che compare vuol dire «finito».
printf '%s\n' "$E" > "$ESITO_FILE"
chmod 644 "$ESITO_FILE" 2>/dev/null

exit "$E"
