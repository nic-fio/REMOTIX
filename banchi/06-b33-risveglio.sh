#!/bin/bash
#
# 06-b33-risveglio.sh — ⛔⛔ THE SECOND DOOR OF THE DYING CLICK, §7.1.
#
#   ⚠ RUNS ON THE SERVER (192.168.0.2), as user `nicfio`, NOT as root and NOT
#     inside the container.
#
#   bash 06-b33-risveglio.sh <file-parola-sudo> tutto
#   bash 06-b33-risveglio.sh <file-parola-sudo> strumento  ⭐ the ZERO check
#   bash 06-b33-risveglio.sh <file-parola-sudo> libero     3 wake-ups, hand raised
#   bash 06-b33-risveglio.sh <file-parola-sudo> tenuto     ⛔ THE BAD SCENE
#   bash 06-b33-risveglio.sh <file-parola-sudo> confronto  the ALREADY KNOWN door
#   bash 06-b33-risveglio.sh <file-parola-sudo> guarigione ⭐ cure "C"
#   bash 06-b33-risveglio.sh <file-parola-sudo> applicazione ⭐ a real GTK app
#
#   ⛔ And its positive control is `06-b33-risveglio-certifica.sh`, which
#      injects three faults and demands that EXACTLY the declared cases change.
#
# ===========================================================================
# ⛔ THE EXPECTATION, DECLARED BEFOREHAND — `CODER.md` §3.3
# ===========================================================================
#
# The thesis of §7.1 that this bench sets out to REFUTE:
#
#   *"every `cattura_risveglia()` (400 ms, still scene, key owed) recreates the
#     `libei` devices: 3 wake-ups, 3 replacements, with zero `ADATTA_TELA`"*
#
# S0 · strumento   the witness sees `BTN_LEFT` down AND up, with no
#                  replacement in between.  ⛔ If it does not see them, all the
#                  rest is THE BENCH and not the product
# S1 · libero      3 `risveglia`, **nothing pressed** ⇒ `ricambi_puntatore`
#                  expected **+3** (one per wake-up) and **zero** calls to
#                  `cattura_ridimensiona()`.  ⚠ If the delta were 0, §7.1 is
#                  FALSE and must be corrected — and that is the outcome this
#                  bench must be able to declare
# S2 · tenuto      `BTN_LEFT` down → **a single** `risveglia` → release.
#                  expected with today's world: ⛔ the release does **NOT reach**
#                  the witness, and the next FRESH click **does not reach it
#                  either** (the seat counts the button as still down,
#                  `meta-seat-impl.c:899-908`).  ⭐ The KEY, instead, arrives:
#                  the keyboard is not a viewport device
# S3 · confronto   the same scene with `ridimensiona` in place of `risveglia`:
#                  it is the door already measured by §4.6.  ⛔ It serves to
#                  tell "the wake-up replaces" from "everything always
#                  replaces": without this comparison the number of S2 means
#                  nothing
# S4 · guarigione  break it on purpose and detach ONLY the EIS client ⇒ clicks
#                  must come back, with the SAME `gnome-shell` (checked by
#                  pid: if the pid changes the green would only say "I
#                  restarted")
# S5 · applicazione ⭐ a REAL `gnome-terminal` must keep receiving Enters
#                  AFTER the healing.  ⛔ It is needed because the reattach
#                  takes the seat capability from 3 to 0 and back: a Wayland
#                  client that does not re-hook goes DEAF — and there was one,
#                  and it was our witness (cured on 21 Aug)
#
# ⛔⛔ AND SINCE 21 AUGUST THE EXPECTATIONS OF S2/S3 HAVE CHANGED, because the
#      world has changed: with cures "A" and "C" in, T3 and T4 are GREEN.  With
#      the defect alive they go back to `DIFETTO_VIVO`, and that is what
#      `06-b33-risveglio-certifica.sh` demands by removing the cures one at a
#      time.
#
# ===========================================================================
# ⛔⛔ THE LIMIT, AT THE TOP SO THAT NOBODY FALLS INTO IT IN GREEN
# ===========================================================================
#
# **The server is not here**: there is no QUIC, no `rcp.c`, no page.  There
# is `06-b33-risveglio`, which links `src/cattura.c` and `src/input.c` and
# calls them from the command line (`CODER.md` §3.6).
#
#   ⇒ ⛔ This bench CANNOT SAY whether the PRODUCT falls in this scene: it says
#     that **the function the product calls** falls in it.  The step from the
#     second to the first is made by `figlio.c:6365`, which calls
#     `cattura_risveglia()` when the capture is ZERO and a key is owed — that
#     is, **on a still desktop**, which is exactly the scene below.  ⚠ But the
#     round with the real server is another bench, and until it exists the mark
#     stays `[M] on the module`.
#
#   ⇒ And it SAYS NOTHING about the browser: no frame, no `requestAnimationFrame`.
#
# ⚠ Every time measurement carries the LOAD next to it: ten agents on the same
#   machine, and a number taken under load and not declared as such is a false
#   number.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?needs the 0600 file with the sudo password}
COSA=${2:-tutto}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
T=$SRC/banchi/06-b33-terreno.sh
G=$SRC/banchi/06-b33-risveglio-giudice.py
# ⛔ The results file can be REDIRECTED, and it is not a convenience: the judge
#    opens it in **append** and nobody truncates it.  ⇒ Whoever compares two
#    rounds — that is, `06-b33-risveglio-certifica.sh` — must be able to give
#    each round a file of its own, or risks reading YESTERDAY's line believing
#    it is from now.
#    *Finding R3 of the adversarial review, 22 August 2026.*
ESITI=${ESITI:-$LAV/06-b33-risveglio-esiti.jsonl}
TELA=${TELA:-1264x800}
TELA2=${TELA2:-1000x640}
TL=${TELA%x*}
TA=${TELA#*x}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { printf '⛔ %s cannot be read\n' "$PAROLA_SUDO"; exit 2; }
sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
terreno()  { sudo_mio bash "$T" "$@"; }
di()       { terreno iniettore-di "$@" >/dev/null; }
carico()   { terreno carico | sed 's/^/        /'; }

# ⛔ The scene is rebuilt from scratch at EVERY round, and the reason is
#    measured: once the seat has a button stuck down, the only thing that
#    unsticks it is the drop of the EIS channel (`meta-eis-client.c:1075`,
#    `drop_device`).  ⇒ A second round inside the same injector would measure
#    the DAMAGE OF THE FIRST.
rimonta() {
	terreno iniettore-spegni  > /dev/null 2>&1
	terreno testimone-via     > /dev/null 2>&1
	terreno spegni            > /dev/null 2>&1
	sleep 2
	terreno sessione > /dev/null 2>&1
	terreno iniettore-accendi "$TELA" || return 3
	# ⛔ The witness is opened AFTER the injector: it is the injector that
	#    mounts the virtual monitor, and the witness picks it BY SIZE.  Opening
	#    it first would mean looking for a screen that does not exist yet.
	terreno testimone "$TELA" || { ko "⛔ THE BENCH: the witness does not open"; return 3; }
	# ⛔⛔ THE WARM-UP, and it is not caution: it is a bench defect measured on
	#     21 August 2026 that gave me a false red on the first round.
	#
	#     `[M]` The VERY FIRST `punta` on a freshly opened window produces the
	#     `wl_pointer.enter`, and the click sent 0.4 s later **does not
	#     arrive** — while the very same click, repeated by hand a minute
	#     later, arrives.  ⇒ It is not the defect of §7.1: it is the window
	#     still settling in, and a bench that started right away would accuse
	#     the product of something it did not do (`CODER.md` §3.10).
	#
	# ⇒ It warms up BEFORE `segna`, so the settling-in lines stay **outside**
	#   the measurement window instead of having to be discarded afterwards.
	di "punta $((TL / 2)) $((TA / 2))"; sleep 1.5
	di "punta $((TL / 3)) $((TA / 3))"; sleep 1.0
	return 0
}

# how many lines the witness has seen so far — it is the judge's `--da`
segna() { terreno righe | awk '{print $2}'; }

giudica() { # $1 label · $2 scene(mode) · $3 from · $4 description
	sudo_mio python3 "$G" --visto "$LAV/visto.jsonl" \
		--iniettore "$LAV/06-b33-risveglio.log" --da "$3" \
		--modo "$2" --etichetta "$1" --tela "$TELA" --esiti "$ESITI" \
		--scena "$4"
	[ $? -eq 0 ] || ESITO=1
}

case "$COSA" in
strumento)
	log "S0 · THE ZERO CHECK — can the instrument see a click?"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))"; sleep 0.4
	di "pulsante 272 1";                sleep 0.4
	di "pulsante 272 0";                sleep 0.6
	di "stato";                         sleep 0.3
	giudica s0-strumento strumento "$DA" \
		"click with no replacement at all, witness opened first"
	carico
	exit $ESITO ;;

libero)
	log "S1 · THREE WAKE-UPS WITH HAND RAISED — §7.1 says 3 replacements, and zero ADATTA_TELA"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "stato";     sleep 0.3
	di "risveglia"; sleep 1.2
	di "risveglia"; sleep 1.2
	di "risveglia"; sleep 1.2
	di "stato";     sleep 0.3
	giudica s1-libero libero "$DA" \
		"three cattura_risveglia() on a still scene, nothing pressed"
	carico
	exit $ESITO ;;

tenuto)
	log "S2 · ⛔ THE BUTTON HELD DOWN WHILE THE CAPTURE WAKES UP"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "stato";                          sleep 0.3
	# ⛔ A SINGLE wake-up: two would make it impossible to say which one did
	#    the damage, and the damage is irreversible — it does not add up, it
	#    is used up.
	di "risveglia";                      sleep 1.5
	di "stato";                          sleep 0.3
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	# ⭐ AND NOW A FRESH CLICK: it is the measurement that really counts — "does
	#    the desktop still take clicks?" — and yesterday's bench did not have it.
	di "punta $((TL * 3 / 4)) $((TA * 3 / 4))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.6
	# ⚠ And a key, as a check INSIDE the scene: the keyboard is not a viewport
	#   device and does not get replaced, so it MUST arrive.  If it did not,
	#   the cause would be something else and the red would accuse the wrong
	#   thing.
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	di "stato";                          sleep 0.3
	giudica s2-tenuto tenuto "$DA" \
		"BTN_LEFT and Ctrl held down during ONE cattura_risveglia(), still scene"
	carico
	exit $ESITO ;;

confronto)
	log "S3 · THE ALREADY KNOWN DOOR — the same scene with a RESIZE"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "stato";                          sleep 0.3
	di "ridimensiona ${TELA2%x*} ${TELA2#*x}"; sleep 1.5
	di "ritela ${TELA2%x*} ${TELA2#*x}"; sleep 0.4
	di "stato";                          sleep 0.3
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	di "punta $(( ${TELA2%x*} * 3 / 4 )) $(( ${TELA2#*x} * 3 / 4 ))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.6
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	di "stato";                          sleep 0.3
	giudica s3-confronto tenuto "$DA" \
		"BTN_LEFT and Ctrl held down during a cattura_ridimensiona() (§4.6)"
	carico
	exit $ESITO ;;

guarigione)
	# ⭐⭐ CAN IT BE HEALED WITHOUT RESTARTING THE SESSION? — the test of cure "E".
	#
	# §4.6 says *"it heals only by restarting the server"*.  ⛔ But "the server"
	# is much more than what is needed: `[R]` the only place where Mutter
	# releases what was pressed is `drop_device()`, called by
	# `meta_eis_client_disconnect()` (`meta-eis-client.c:1075`) — that is, by
	# the **drop of the EIS channel**, which has nothing to do with the process.
	#
	# ⇒ Here the desktop is broken and then **only the EIS client** is
	#   detached, leaving gnome-shell, the monitor and the user's session
	#   standing.  If the click comes back, the recovery cure exists and costs
	#   a reattach.
	#
	# ⛔⛔ AND THE LIMIT MUST BE SAID: here the client shuts down ENTIRELY, so
	#      the `RemoteDesktop` session and the PipeWire stream drop too.  ⇒ This
	#      measurement proves that **a new EIS client heals the seat**; it does
	#      NOT yet prove that reopening **only** `ConnectToEIS` while keeping
	#      the stage up is enough.  That is `[R]`
	#      (`meta-remote-desktop-session.c:1943-1969`: `session->eis` is reused
	#      and every call adds a client) and to make it `[M]` a line is needed
	#      in `mutter.c` that closes the descriptor set aside and calls
	#      `ConnectToEIS` again — ⚠ without closing that one, the socket stays
	#      open and Mutter **sees no detach at all**.
	log "S4 · ⭐ CAN IT BE HEALED WITHOUT TOUCHING THE SESSION?"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "risveglia";                      sleep 1.5
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	di "punta $((TL * 3 / 4)) $((TA * 3 / 4))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	giudica s4-rotto tenuto "$DA" "the damage, redone on purpose to then heal it"

	log "And now I detach ONLY the EIS client — gnome-shell is NOT touched"
	PRIMA_SHELL=$(sudo_mio pgrep -u 1006 -x gnome-shell | head -1)
	terreno iniettore-spegni > /dev/null
	sleep 2
	terreno iniettore-accendi "$TELA" > /dev/null || { ko "⛔ it does not come back on"; exit 3; }
	terreno testimone "$TELA" > /dev/null || { ko "⛔ THE BENCH: witness"; exit 3; }
	di "punta $((TL / 2)) $((TA / 2))"; sleep 1.5
	di "punta $((TL / 3)) $((TA / 3))"; sleep 1.0
	DOPO_SHELL=$(sudo_mio pgrep -u 1006 -x gnome-shell | head -1)
	# ⛔ And it is CHECKED that the session is the same: if gnome-shell had
	#    restarted, the seat's count (`MetaSeatImpl`) would be brand new and
	#    the green would only say "I restarted everything".
	if [ -n "$PRIMA_SHELL" ] && [ "$PRIMA_SHELL" = "$DOPO_SHELL" ]; then
		ok "gnome-shell is the SAME process ($PRIMA_SHELL): the seat is not new"
	else
		ko "⛔ gnome-shell has changed ($PRIMA_SHELL → $DOPO_SHELL): the green that follows does not count"
	fi
	DA=$(segna)
	di "pulsante 272 1"; sleep 0.4
	di "pulsante 272 0"; sleep 0.8
	giudica s4-guarito strumento "$DA" \
		"the same desktop, after reattaching only the EIS client"
	carico
	exit $ESITO ;;

applicazione)
	# ⛔⛔ THE REAL PRICE OF CURE "C", ON A REAL APPLICATION — 21 Aug 2026.
	#
	# The healing drops the EIS channel, and on a session without monitors
	# our virtual devices are the ONLY ones on the seat: `[M]` the capability
	# of the `wl_seat` goes **3 → 1 → 0 → 1 → 3**.  ⇒ **Every Wayland client
	# must let go of `wl_pointer`/`wl_keyboard` and re-hook them.**
	#
	# ⛔ The witness did NOT do it, and stayed mute forever (cured today, see
	#    the box in `06-b33-testimone.c`).  ⚠ A badly written client goes deaf
	#    after a healing, and this bench must say so before the user finds out.
	#
	# ⇒ Here the application is a REAL `gnome-terminal`, with a shell inside
	#   that nobody will restart: if after the healing it receives the Enters,
	#   a GTK client withstands the capability change.  ⭐ It is an `[M]` on a
	#   toolkit we did not write, which is the kind of test worth the most.
	log "S5 · ⭐ DOES A REAL APPLICATION survive the healing?"
	carico
	terreno iniettore-spegni  > /dev/null 2>&1
	terreno testimone-via     > /dev/null 2>&1
	terreno spegni            > /dev/null 2>&1
	sleep 2
	terreno sessione > /dev/null 2>&1
	terreno iniettore-accendi "$TELA" || exit 3
	# ⛔ And the terminal is opened AFTER the injector, like the witness: it is
	#    the injector that mounts the monitor.  ⚠ And NOT together with the
	#    witness: the full-screen window takes the focus and the terminal would
	#    not receive a key.
	terreno terminale || { ko "⛔ THE BENCH: the terminal does not open"; exit 3; }
	di "punta $((TL / 2)) $((TA / 2))"; sleep 1.5
	PRIMA=$(terreno invii | awk '{print $2}')
	inf "Enters received BEFORE: $PRIMA"
	# ⛔ One Enter BEFORE the healing: if not even this one arrives, the scene
	#    does not hold and the red afterwards would accuse the wrong thing.
	di "posizione 28 1"; sleep 0.3
	di "posizione 28 0"; sleep 0.8
	MEZZO=$(terreno invii | awk '{print $2}')
	if [ "$((MEZZO - PRIMA))" -ge 1 ]; then
		ok "the terminal receives the Enters BEFORE the healing ($((MEZZO - PRIMA)))"
	else
		ko "⛔ THE BENCH: the terminal receives nothing even before, the scene does not hold"
		exit 3
	fi
	# the bad scene: button down + wake-up ⇒ cure "C" must kick in
	di "pulsante 272 1"; sleep 0.6
	di "risveglia";      sleep 2.0
	di "pulsante 272 0"; sleep 0.8
	di "stato";          sleep 0.3
	# ⛔ `iniettore-registro`, NOT `iniettore-dice`: the healing line is written
	#    by `registro_dice()` of the "input" area, and `iniettore-dice` filters
	#    only the injector's `B33R:` lines.  ⚠ Looking for it there gave a false
	#    red while the cure had really kicked in — bench defect, 21 Aug.
	# ⛔ And the LONG form, not the bare word: "HEALING" alone would also show
	#    up in a comment or in a future line of another module.  ⚠ It is the
	#    same discipline as the finding on `%s`: the complete form is searched.
	if terreno iniettore-registro 400 | grep -q 'HEALING (n\.'; then
		ok "⭐ cure \"C\" kicked in (the HEALING line is there)"
	else
		ko "⛔ cure \"C\" did NOT kick in: what follows does not measure the healing"
	fi
	di "posizione 28 1"; sleep 0.3
	di "posizione 28 0"; sleep 0.8
	di "posizione 28 1"; sleep 0.3
	di "posizione 28 0"; sleep 1.0
	DOPO=$(terreno invii | awk '{print $2}')
	inf "Enters received AFTER the healing: $DOPO (they were $MEZZO)"
	if [ "$((DOPO - MEZZO))" -ge 2 ]; then
		ok "⭐ the REAL application received $((DOPO - MEZZO)) Enters AFTER the healing"
	else
		ko "⛔ it received $((DOPO - MEZZO)) instead of 2: a GTK client does NOT withstand the"
		ko "   seat capability change ⇒ the price of cure \"C\" is much higher"
		ko "   than what was declared, and must be reported to the coordinator"
	fi
	terreno terminale-via > /dev/null 2>&1
	carico
	exit $ESITO ;;

spegni)
	terreno iniettore-spegni
	terreno testimone-via
	terreno terminale-via
	exit 0 ;;

tutto)
	# ⛔⛔ THE OUTCOMES OF THE SUB-ROUNDS ADD UP, and it is not pedantry:
	#      `06-b33-lancia.sh` had an `exit 0` here and came out green with all
	#      cases red (finding of the adversarial review, 21 August 2026).  It
	#      is not paid twice.
	for g in strumento libero tenuto confronto guarigione; do
		bash "$0" "$PAROLA_SUDO" "$g" || ESITO=1
	done
	bash "$0" "$PAROLA_SUDO" spegni > /dev/null
	if [ "$ESITO" -eq 0 ]; then
		ok "⭐ all scenes gave what the expectation declared"
	else
		ko "⛔ at least one scene is not green: look at the sub-rounds above"
	fi
	exit $ESITO ;;

*)
	echo "⛔ I do not know how to do \"$COSA\""; exit 2 ;;
esac
