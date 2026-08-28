#!/usr/bin/env bash
# ===========================================================================
# 10-ambiente-sessione — ⛔ L'AMBIENTE DI UNA SESSIONE REMOTA, IN UN POSTO SOLO
# ===========================================================================
#
# Quando un banco accende un'applicazione **dentro** una sessione remota, deve
# comporle l'ambiente **da zero** (`CODER.md` §4.5): `env -i` e una variabile
# per volta, cosi' che quel che l'applicazione trova sia dichiarato invece che
# ereditato dalla shell di chi ha lanciato il banco.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ PERCHE' QUESTO FILE ESISTE — 25 agosto 2026
# ═══════════════════════════════════════════════════════════════════════════
#
# La stessa composizione era scritta **a mano in quattro posti**:
#
#   · `10-b92-dieci.py`, `giu()` dentro l'attrezzo `10-b92-scene.py`
#   · `10-b98-mista.py`, `_giu()`   — e una **seconda** copia in linea, quella
#     che accende le scene del risveglio
#   · `10-b89-scena.sh`, `giu()`
#
# ⛔ Ed erano **incomplete tutt'e quattro**: mancavano tre variabili, e senza
#    quelle le applicazioni GTK vere **si rifiutano di partire**.
#
# | manca                        | `[M]` che cosa si vede                       |
# |------------------------------|----------------------------------------------|
# | `XDG_SESSION_TYPE=wayland`   | ⛔ Nautilus: *«Failed to initialize display   |
# |                              | server connection: Unsupported or missing     |
# |                              | session type ''»* — e non parte affatto       |
# | `XDG_CURRENT_DESKTOP=GNOME`  | i portali e le scorciatoie del desktop non si |
# |                              | riconoscono                                   |
# | `GTK_A11Y=none`              | rumore di `org.a11y.Bus`, che nella sessione  |
# |                              | headless non c'e'                             |
#
# ⇒ ⛔⛔ E IL DANNO NON E' ESTETICO: un banco che accende un'applicazione con
#      quell'ambiente **misura il fallimento del proprio `env`, non il
#      prodotto**.  E' `LEZIONI.md` §1.30 — *la prova che non morde da' un
#      giudizio che sembra un risultato*: il desktop resta vuoto, il costo di
#      GPU e' quello di uno schermo fermo, e nessuno vede rosso.
#
# ⭐ E il fatto che fossero **quattro copie** e' la ragione per cui la lacuna e'
#    sopravvissuta: chi ne curava una non curava le altre, ed e' lo stesso
#    difetto della quinta copia a mano di `WT_RIPASSO_INSIEME`.  ⇒ Adesso e'
#    UNA, ed e' questo file.
#
# ═══════════════════════════════════════════════════════════════════════════
# COME SI USA
# ═══════════════════════════════════════════════════════════════════════════
#
#   1. da uno script di shell, come funzione:
#        . "$(dirname "$0")/10-ambiente-sessione.sh"
#        setsid nohup $(ambiente_di "$UID_B" "$UTENTE") nautilus >>"$LOG" 2>&1 &
#
#   2. da Python o da una riga di comando, come stampatore del frammento:
#        bash 10-ambiente-sessione.sh 1103 provadec4
#      ⇒ stampa il frammento `setpriv … env -i …` da mettere davanti al comando.
#
#   3. `bash 10-ambiente-sessione.sh --righe` stampa le variabili una per riga,
#      per guardarle senza doverle leggere dentro una riga di seicento
#      caratteri.
#
# ⚠ Il frammento **non** porta `setsid`, `nohup`, il redirect ne' la `&`: quelli
#   sono di chi lancia, e ogni banco li vuole a modo suo.  ⛔ Il redirect in
#   particolare deve vivere nella shell di ROOT — in una cartella di root la
#   shell di `nicfio` non potrebbe scrivere, e il processo morirebbe col
#   registro VUOTO (la ragione per cui `10-b89-scena.sh` esiste).
# ===========================================================================

# ⛔ Le variabili, una per riga e con la ragione accanto.  Chi ne aggiunge una
#    la aggiunge QUI, e la aggiunge per tutti.
ambiente_di() {
	local n=$1 u=$2
	printf '%s' "setpriv --reuid=$n --regid=$n --init-groups env -i "
	printf '%s' "HOME=/home/$u USER=$u LANG=C.UTF-8 "
	printf '%s' "PATH=/usr/local/bin:/usr/bin:/bin "
	# ⛔ `XDG_RUNTIME_DIR` — senza, PipeWire e il bus della sessione non si
	#    trovano.  ⚠ E vive solo se l'utente ha `enable-linger`.
	printf '%s' "XDG_RUNTIME_DIR=/run/user/$n "
	# ⛔ Il compositore: il socket lo pubblica `mutter` della sessione remota.
	printf '%s' "WAYLAND_DISPLAY=wayland-0 "
	# ⛔ GTK userebbe X11 se lo trovasse; qui non c'e', e senza questa riga
	#    ripiega su «nessun display» invece di dire perche'.
	printf '%s' "GDK_BACKEND=wayland "
	# ⛔⛔ 25 ago 2026 — SENZA QUESTA, NAUTILUS NON PARTE AFFATTO:
	#     «Failed to initialize display server connection: Unsupported or
	#     missing session type ''».  ⚠ Non e' una comodita': e' la differenza
	#     fra misurare un desktop vero e misurare uno schermo vuoto.
	printf '%s' "XDG_SESSION_TYPE=wayland "
	# ⛔ 25 ago 2026 — i portali e le scorciatoie del desktop si riconoscono da
	#    qui: senza, un'applicazione GTK gira in un desktop che non sa nominare.
	printf '%s' "XDG_CURRENT_DESKTOP=GNOME "
	# ⚠ 25 ago 2026 — `org.a11y.Bus` nella sessione headless non c'e', e senza
	#   questa riga ogni applicazione GTK riempie il registro di tentativi
	#   falliti.  ⛔ Rumore nel registro non e' innocuo: e' il registro di
	#   diagnosi di questo progetto che diventa meno leggibile.
	printf '%s' "GTK_A11Y=none "
	# ⛔ Il bus di sessione: senza, niente portali, niente `gnome-terminal`
	#    (che parla col suo server via D-Bus e senza bus non apre finestre).
	printf '%s' "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$n/bus"
}

# ⭐ Eseguito invece che incluso: stampa il frammento (o le righe).
# ⛔ E LA GUARDIA E' SU `$0`, NON SU `BASH_SOURCE` — `10-b89-scena.sh` e' un
#    `#!/bin/sh` e lo include: `${BASH_SOURCE[0]}` la' e' un errore di sintassi
#    di `dash`, e il banco morirebbe prima di misurare.  ⚠ Incluso, `$0` resta
#    il nome di chi include; eseguito, e' questo file.
case "$0" in
*10-ambiente-sessione.sh)
	if [ "${1:-}" = "--righe" ]; then
		ambiente_di "${2:-1000}" "${3:-utente}" | tr ' ' '\n'
		exit 0
	fi
	if [ $# -lt 2 ]; then
		echo "uso: sh $0 <uid> <utente>   |   sh $0 --righe [uid] [utente]" >&2
		exit 2
	fi
	ambiente_di "$1" "$2"
	printf '\n'
	;;
esac
