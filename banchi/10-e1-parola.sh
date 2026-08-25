#!/usr/bin/env bash
# ===========================================================================
# 10-e1-parola — ⛔⛔ QUALE DELLE DUE PAROLE E' QUELLA VERA, senza rifarla.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL PROBLEMA, che non e' del banco ma del COORDINAMENTO
# ═══════════════════════════════════════════════════════════════════════════
#
# `provadec4/5/6` sono **condivisi** fra due banchi della fase 10, e i due
# dichiarano parole DIVERSE:
#     `10-c3-terreno.sh`  → `dec-pieno-2026`
#     `10-b96-terreno.sh` → `mt-dieci-2026`
# Da quando `07-b64-terreno.sh` **non riscrive piu'** la parola di un utente che
# esiste gia' (la cura del 25 agosto 2026), sulla macchina ce n'e' **una sola**,
# ed e' quella dell'ultimo che l'ha scritta prima della cura.  ⛔ L'altra da'
# `CONGEDO 0x07 CREDENZIALI_ERRATE` su una macchina perfettamente sana.
#
# ⛔⛔ E OGNI RESPINTO CONSUMA UNO DEI **TRE** TENTATIVI di `RCP.md` §4.4-bis
#      (tre dentro cinque minuti ⇒ ban di dodici ore).  ⚠ Il ban e' per
#      indirizzo **dentro il server che lo conta**, e ogni banco ha il suo
#      `--ban-file`: qui si rischia **il proprio** server, non quello altrui.
#      ⇒ Un tentativo, non tre: si prova la prima candidata, e se e' sbagliata
#        si passa alla seconda.  Mai una terza.
#
# ⭐ E NON SI RIFA' LA PAROLA (l'incarico lo vieta, e rifarla la ruberebbe a chi
#    sta misurando adesso): si cambia solo **il file che il cliente legge**,
#    `$LAV/parola`.  Il sistema non si tocca.
#
# Uso:
#     LAV=… DENTRO_ALB=… DENTRO_LAV=… PORTA=… \
#       bash banchi/10-e1-parola.sh provadec4 dec-pieno-2026 mt-dieci-2026
#
# Esce 0 e stampa la parola buona; 1 se nessuna delle candidate ha funzionato.
# ===========================================================================
set -uo pipefail
MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-8310}
LAV=${LAV:-/media/REMOTIX/tmp/10e1}
DENTRO_ALB=${DENTRO_ALB:-/srv/src/10e1-src}
DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10e1}

U=${1:?serve l utente}
shift
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*" >&2; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*" >&2; }
inf() { printf '    --  %s\n' "$*" >&2; }

# ⛔⛔ IL COMANDO VIAGGIA IN base64, E NON E' UN VEZZO — `[M]` 25 agosto 2026.
#     La forma `ssh … "sudo bash -c '$1'"` si rompe appena `$1` contiene un
#     apice, e la riga del cliente ne e' piena: il comando **non e' partito** e
#     dall'uscita si vedeva solo l'avviso di `tput`.  ⚠ Il banco ha detto «non
#     ho capito l'esito» invece di indovinare — ed e' l'unica ragione per cui
#     non ha dichiarato sbagliata una parola che non aveva mai provato.
root() {
	local b64; b64=$(printf '%s' "$1" | base64 -w0)
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"echo $b64 | base64 -d | bash\""
}

for P in "$@"; do
	inf "provo «$P» per $U (⚠ un tentativo solo: §4.4-bis conta fino a tre)"
	root "printf '%s\n' '$P' > $LAV/parola; chmod 600 $LAV/parola" >/dev/null 2>&1
	# ⛔ Niente `timeout` qui dentro: `enter.sh` passa la riga a una shell che la
	#   rispezza, e `timeout` si e' ritrovato gli argomenti sbagliati — `[M]` 25
	#   agosto 2026, e il banco ha detto «non ho capito l'esito», che e' la cosa
	#   giusta da dire.  ⭐ Il cliente esce da solo: `--resta 2`.
	OUT=$(root "bash /media/REMOTIX/enter.sh --root \"python3 -u $DENTRO_ALB/banchi/01-b3-cliente.py --indirizzo $IND --porta $PORTA --utente $U --parola-file $DENTRO_LAV/parola --audio-codec pcm --video-codec h264 --resta 2\"" 2>&1)
	if printf '%s' "$OUT" | grep -q "AMMESSO dopo"; then
		ok "⭐ la parola vera di $U e' «$P» — e resta in $LAV/parola"
		# ⛔⛔ E SI SPEGNE IL PALCO CHE HO APPENA ACCESO — invariante I4: il palco
		#     appartiene alla SESSIONE, non alla connessione, quindi sopravvive
		#     al cliente e resta li' fino al logout o all'abbandono a 60 minuti.
		#     `[M]` 25 agosto 2026: senza questa riga il controllo del terreno
		#     del banco successivo ha dato rosso — [T7.1] «il posto di
		#     provadec4 NON e' libero» — ⭐ e ha fatto benissimo: un palco gia'
		#     montato falsa la scena di chi misura il RIEMPIMENTO.
		#  ⚠ Solo il MIO utente: mai un modello globale (§7.3, quinta trappola).
		root "pkill -u $U -f gnome-session-binary 2>/dev/null; true" >/dev/null 2>&1
		for _ in $(seq 1 40); do
			n=$(root "pgrep -u $U -c gnome-shell || true" 2>/dev/null | tr -dc 0-9)
			[ "${n:-0}" = 0 ] && break
			sleep 0.5
		done
		inf "palco di $U sgombrato (l'ho acceso io provando la parola)"
		printf '%s\n' "$P"
		exit 0
	fi
	if printf '%s' "$OUT" | grep -q "0x07"; then
		ko "⛔ «$P» e' sbagliata (CONGEDO 0x07): ho bruciato UN tentativo dei tre"
		continue
	fi
	ko "⛔ non ho capito l'esito con «$P»: $(printf '%s' "$OUT" | tail -4 | tr '\n' ' ')"
	exit 2
done
ko "⛔ nessuna delle candidate ha funzionato per $U"
exit 1
