#!/bin/bash
#
# 02-cattura-lancia.sh — runs ON THE SERVER (NIC-OS), outside the container.
# The bench of sub-phase F2.2: ONE frame taken from the GNOME session,
# with the buffer type declared and the PIXELS looked at.
#
#   bash /media/REMOTIX/src/02-cattura-lancia.sh compila     once (in the container)
#   bash /media/REMOTIX/src/02-cattura-lancia.sh scena       generates the declared scene
#   bash /media/REMOTIX/src/02-cattura-lancia.sh misura      one round
#   bash /media/REMOTIX/src/02-cattura-lancia.sh elenco      the expectations, without measuring
#
# ===========================================================================
# ⛔ WHY THIS BENCH EXISTS, GIVEN THAT PHASE 0 ALREADY MEASURES CAPTURE
#
# `fondamenta/banchi/banco-compositori/misura-cattura` is certified, reproduces Mutter's
# 36 ± 2 frames per second, and stays the historical positive control
# of the whole project (`FASI.md` §00-ambiente).  ⛔ But it never looks at the pixels:
# it reads type, fd, stride, damage and sequence, and puts the buffer back in the queue without
# touching `piano->data`.
#
# ⇒ **A completely BLACK frame would pass phase 0 with full
#   marks**: 36 per second, four recycled buffers, partial damage, zero skips.
#   All green, and on the screen nothing.
#
# ⛔ And black is exactly the fault this phase risks:
#
#   | where it is written     | what it says                                   |
#   |-------------------------|------------------------------------------------|
#   | `STUDI.md` §gnome §3.1         | in headless `needs_outputs=false`: without  |
#   |                         | `--virtual-monitor` the session starts **alive,|
#   |                         | complete and black**                           |
#   | `STUDI.md` §gnome §13, M9      | it is a test to be done **broken on purpose**,|
#   |                         | to learn what the fault looks like             |
#   | `PIANO.md`, phase 2     | *«a black and perfectly alive session is the   |
#   |                         | thing that gets mistaken for a capture defect, |
#   |                         | and you search for half a day on the wrong     |
#   |                         | side»*                                         |
#
# The wrong measurement this bench prevents, said in one line: **«capture
# delivers» written in a table next to an empty frame.**
#
# ===========================================================================
# ⛔ THE SCENE IS DECLARED, AND THIS ONE DIFFERS FROM PHASE 0'S — WITH A
#    REASON, NOT BY TASTE
#
# `CODER.md` §3.2: the scene is declared and always moves.  Phase 0 used
# `weston-simple-egl -f -o`, which moves very well — but **is not recognisable
# in the pixels**: a spinning triangle has no signature, and F2.6 (the comparison
# between the captured and the decoded frame) would have nothing to
# compare.  An F2.2 bench with that scene could say «frames
# arrive» and could not say «the DESKTOP arrives».
#
# ⭐ SCENE «bandiera»: the seven SMPTE bars full screen, STILL, plus a
#    white block that slides along the bottom at every frame.
#
#   the still part   is the signature: it lives in the pixels and not in time, so two
#                    different rounds can be compared — which is what
#                    a STILL IMAGE and F2.6 need
#   the moving part  Mutter delivers a frame **only if something changes**
#                    (`LEZIONI.md` §4 trap 8).  Without the sliding block,
#                    on a still desktop nothing would arrive: a legitimate
#                    zero, and a mute bench
#   the block sits   so the signature does not depend on the INSTANT at which the
#   in a corner      frame was taken
#
# ⚠ And the phase 0 scene stays available (`SCENA=tetto`), because it is the
#   link with the historical positive control: on it the pixel judgement
#   reduces to «it is not black and it is not uniform», and it says so.
#
# ===========================================================================
# ⛔ THE ORDER: FIRST THE VIRTUAL MONITOR, THEN THE SCENE — and with an EVENT
#
# Phase 0's `banco.sh` switches the scene on 2.5 seconds after the meter, with
# the reason written next to it: *«without a screen there is nowhere to open»*.  Here
# a timed wait is not enough, because the producer must then know WHICH
# frames arrived before the scene and which after — it is the separation
# between the start-up frame and the steady-state one (`CODER.md` §3.5, form E9).
#
# Therefore:  the producer writes `pronto` when the stream is ACTIVE
#          →  this script switches the scene on and checks it is alive
#          →  this script writes `scena-accesa`
#          →  only then does the producer start counting the steady state
#
# ⭐ It is not a wait: it is an event (`LEZIONI.md` §4 trap 9 — «you do not wait for
#    a silence, you wait for an event»).
#
# ⚠ And the same form bites phase 2 from another side, already measured: in a
#   GNOME session without input devices, a client opened BEFORE the
#   `libei` virtual pointer exists receives nothing — `PIANO.md`, box
#   «A question phase 1 found and that bites HERE», `[M]` 10 Aug 2026.
#   Here no device is created (it is not F2.2's area), but whoever mounts
#   input will have to slip it between `pronto` and the scene, not before.
#
# ===========================================================================
# ⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS — and here there are FOUR
#
#   0  ⭐ VERDE: a frame is there, it is of the requested size, and it contains the scene
#   1  ROSSO: there is a frame and something does not add up. The mark says what —
#      FOTOGRAMMA NERO · FOTOGRAMMA UNIFORME · SCENA NON RICONOSCIUTA ·
#      BYTE NON TORNANO · MISURA DIVERSA DA QUELLA CHIESTA · IL BUFFER NON E'
#      CAMBIATO
#   3  ⭐ ZERO FRAMES, or DMA-BUF road (pixels not readable from here): there is
#      nothing to judge, and it is NOT a red
#   2  ⛔ I FAILED: the scene does not start, the stream was never active or
#      dropped, the binary is older than the source, the judge does not pass
#      its own positive control
#
# ⛔ No `2>/dev/null` in this file, and no exit status thrown into
#    a chain of `|`.  Items 1, 3 and 8 of «What did NOT work»
#    of `FASI.md` §00-ambiente are three faces of this single rule, and all three were
#    paid for in one afternoon.
#
# ===========================================================================
# ⛔ WHAT THIS BENCH DOES **NOT** SAY
#
#   - **nothing about rate.** The producer copies two 8 MB frames inside
#     PipeWire's real-time callback: a frames-per-second number
#     that came out of here would be skewed by us. Rate belongs to phase 0
#     (36 ± 2 `[M]`) and phase 3
#   - **nothing about where Mutter renders.** ⛔ Form E1 of `REVIEWER.md` §2: «delivers
#     MemFd ⇒ it is in software» and «it opened a render node ⇒ it renders on the GPU» are
#     two errors already paid for (`LEZIONI.md` §1.11). Here memory is ASKED FOR —
#     readable pixels are needed — so MemFd is the answer to our own
#     question, not a discovery
#   - **nothing about encoding.** Out of here comes 32-bit BGRx, which is the only
#     format Mutter delivers (`STUDI.md` §gnome §8.3: «Only BGRx and BGRA»). The
#     conversion to 10 bits belongs to F2.3
#
# ⚠ And the machine has TWO GPUs (Intel `0000:00:02.0`, Radeon `0000:03:00.0`): a
#   buffer of the wrong card cannot be imported, and the symptom is
#   software composition **without an error anywhere**
#   (`LEZIONI.md` §4 trap 6). ⛔ This bench would NOT see it: on the memory road
#   the pixels arrive anyway. It is a declared `[?]`, not something
#   the green below acquits.
# ===========================================================================
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
# ⭐ THE PRODUCER IS DECLARED, AND THERE ARE TWO — added on 12 Aug 2026 with the
#    product (P2.2).  The bench was born before the product and certified the
#    producer written INSIDE itself: that green said nothing about the
#    product, because the product did not exist yet (`LEZIONI.md` §1.3).
#
#      PROG=$QUI/02-cattura-fotogramma  FONTE=$SRC/02-cattura-fotogramma.c
#          the bench's producer, the one certified on 12 Aug
#      PROG=$QUI/02-cattura-prodotto    FONTE=$SRC/02-cattura-prodotto.c
#          ⭐ THE PRODUCT: src/cattura.c + src/mutter.c, behind the same command
#          line and with the same manifest
#
# ⛔ And the judge does not change: it judges the PIXELS, and does not know who made them.  Two
#    independent producers under the same judge are a positive control
#    that neither of the two would be on its own.
PROG=${PROG:-$QUI/02-cattura-fotogramma}
FONTE=${FONTE:-$SRC/02-cattura-fotogramma.c}
GIUDICE=$SRC/02-cattura-giudica.py
ESITI=${ESITI:-$SRC/02-cattura-esiti.jsonl}

# ⛔ THIS AGENT'S PORT IS 7512, and no port is opened here.
#    The line exists anyway because the mandate assigns it and because a bench
#    that does not name its own port is a bench that one day takes someone
#    else's: on 7448 and on 7501 two wanted servers run (§4 of the mandate).
PORTA_DI_QUESTO_BANCO=7512

SCENA=${SCENA:-bandiera}
LARGHEZZA=${LARGHEZZA:-1920}
ALTEZZA=${ALTEZZA:-1080}
FPS=${FPS:-60}
DOPO_SCENA=${DOPO_SCENA:-3}
SCARTA=${SCARTA:-10}
DURATA=${DURATA:-12}
STRADA=${STRADA:-memoria}
ETICHETTA=${ETICHETTA:-F2.2-$SCENA-${LARGHEZZA}x${ALTEZZA}-$STRADA}

# The session environment, built from scratch: whoever inherits their own environment
# gives a graphical process also the variables that have nothing to do with it
# (`CODER.md` §4.5).
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=wayland
export LANG=C.UTF-8

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ THE EXPECTATIONS ARE WRITTEN BEFORE THE ROUND — B0.4, and the rule born on 11
#    Aug applies: whoever writes a bench certifies it in the same round.
# ---------------------------------------------------------------------------
elenco()
{
	cat <<'FINE'

  THE EXPECTATIONS OF THIS BENCH, written BEFORE measuring
  ────────────────────────────────────────────────────────────────────────
  scene «bandiera», 1920×1080, memory road:

    what                              expected                  where it comes from
    ─────────────────────────────────────────────────────────────────────────
    frames arrived                    > 0                       the scene moves at every
                                                                frame (trap 8)
    declared buffer type              MemFd                     [?] NEVER MEASURED on this
                                                                road: phase 0 measured
                                                                DMA-BUF. What comes out is
                                                                written, not what is hoped
    negotiated size                   1920×1080                 Mutter makes the monitor of the
                                                                requested size (cattura.h)
    negotiated format                 BGRx                      STUDI.md §gnome §8.3, R32 line by
                                                                line: only BGRx and BGRA
    stride                            ≥ 7680                    ⛔ READ from the chunk, never
                                                                computed (cattura.h)
    bytes of the .raw                  stride × 1080             [?] depends on the real stride
    damage on the «primo» frame       full                      it is the start-up redraw
    damage on the «regime» frame      partial                   phase 0: full 15, partial 929
    distinct recycled buffers         4                         R29, and phase 0 confirms it
    the scene shows in the «regime»   YES                       ⭐ it is F2.2's question
    «primo» different from «regime»   YES                       or the buffer is old

  ⭐ AND THE QUESTION NO DOCUMENT CAN ANSWER TODAY, and which this round
     decides with a measurement instead of a rereading:

     is a frame with PARTIAL damage nevertheless WHOLE?

       `fondamenta/remotix-c/src/cattura.h`  says NO: *«Mutter recycles its own
                                     buffers and repaints in them ONLY the part
                                     that changed; outside those regions are the
                                     pixels of the previous frame»*
       `STUDI.md` §gnome §8.1               says YES: *«⛔ false: blit of the whole
                                     framebuffer, clip stack emptied
                                     deliberately»*, after rereading Mutter

     ⚠ And the stakes are high: if `cattura.h` were right, phase 2 would deliver
       half a desktop and half an old screen, without an error anywhere.

  ⛔ And the opposite case, written beforehand (LEZIONI.md §1.11):
     what would the CONTRARY look like?

       black and valid frame      → average luma ≈ 0, mark FOTOGRAMMA NERO.
                                    It is what a session without a
                                    virtual monitor would give: alive, complete and black
       scene not started          → the producer exits 2 with «the scene was
                                    never declared on», not a zero
       still desktop              → exit 3, ZERO FOTOGRAMMI: legitimate
       buffer of another card     → ⚠ this bench would NOT see it: on the memory
                                    road the pixels arrive anyway
FINE
}

# ---------------------------------------------------------------------------
# ⛔ THE BINARY THAT RUNS MUST BE NEWER THAN THE SOURCE.
#
# It is not recompiled from here — compilation wants the container and `sudo`'s
# password — it refuses to measure, which is the only honest thing.
# On 9 Aug 2026 phase 0 found at home a `misura-cattura` from the day
# before, that is without the cures written the day after: whoever had launched it
# would have brought back defects the documents declare closed, without a line
# telling them.
# ---------------------------------------------------------------------------
controlla_binario()
{
	if [ ! -x "$PROG" ]; then
		ko "⛔ $PROG is missing"
		inf "compile it:  bash $0 compila"
		return 1
	fi
	if [ "$FONTE" -nt "$PROG" ]; then
		ko "⛔ $PROG is OLDER than its source $FONTE."
		inf "Measuring now would mean running code different from the code read."
		inf "Recompile:  bash $0 compila"
		return 1
	fi
	ok "the binary is newer than the source"
	return 0
}

compila()
{
	log "compiling inside the container"
	mkdir -p "$QUI" || return 1
	# ⛔ NEVER A REDIRECTION AROUND `enter.sh`: `sudo`'s password
	#    prompt goes to stderr, and a redirection swallows it — the
	#    command hangs forever, silently.  Inside the quotes
	#    yes, around no.  `FASI.md` §00-ambiente B3.3, paid for four times.
	bash /media/REMOTIX/enter.sh "cd /srv/remotix/tmp/02-cattura && \
	    gcc -O2 -Wall -o 02-cattura-fotogramma /srv/src/02-cattura-fotogramma.c \
	        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm)"
	local esito=$?
	if [ $esito -ne 0 ]; then
		ko "⛔ compilation failed (exit $esito)"
		return 1
	fi
	ok "compiled: $PROG"
	ls -la "$PROG"
	return 0
}

# ---------------------------------------------------------------------------
#  The declared scene
# ---------------------------------------------------------------------------
file_scena() { echo "$QUI/bandiera-${LARGHEZZA}x${ALTEZZA}.mp4"; }

genera_scena()
{
	local f
	f=$(file_scena)
	mkdir -p "$QUI" || return 1
	if [ -s "$f" ]; then
		ok "the scene is already there: $f"
		return 0
	fi
	log "generating the declared scene «bandiera» ${LARGHEZZA}x${ALTEZZA}"
	inf "seven still SMPTE bars (the signature) + a 256-level gradient (the real bits)"
	inf "+ a sliding white block (the movement, without which Mutter does not deliver)"
	# ⛔ `-qp 0`: the signature lives in the pixels, and a quantiser that dirties the bands
	#    would make a judge that is right fail.  ⚠ 4:2:0 stays — no
	#    Android decoder does 4:4:4 (`CODER.md` §1) — but the signature is chosen to
	#    survive it: the order and dominance of the channels are checked, not the
	#    absolute RGB values.
	# ⛔ TWO THINGS LEARNED HERE ON 12 AUG 2026, AND BOTH COST A ROUND:
	#
	#  1. the modulo is written WITHOUT `mod(a,b)`.  The comma is ffmpeg's
	#     filter separator and must be protected with a backslash — which however
	#     crosses `bash`, `ssh` and the remote shell, and gets lost in one of the three.
	#     Symptom: «Undefined constant or missing '('».
	#     `t*V - P*floor(t*V/P)` is the same number without any comma;
	#  2. ⛔ and the variable is `t`, NOT `n`: `drawbox` does not expose the frame
	#     number, only time.  With `n` it gives the very same error
	#     message as point 1 — two different causes under the same face, and it is
	#     the reason this comment names both.
	#
	# ⚠ The block runs at 720 px per second: at 60 frames per second that is 12
	#   px per frame, so two consecutive frames are ALWAYS different
	#   — which is what keeps Mutter's delivery alive (trap 8).
	#
	# ⛔ AND THE THIRD PART OF THE SCENE IS A GRADIENT, and it is there for a question
	#    that is not mine but is born here: the **F2.3 seam**.
	#
	#    F2.3 calls **F2.3-A** the fault in which *«capture delivers 8 bits,
	#    the whole chain stays green and the label keeps saying Main10»* — and
	#    nobody notices by looking at the image, because it comes out fine
	#    anyway.  The number that unmasks it is how many DISTINCT LEVELS a
	#    frame carries, and the fraction of multiples of 4.
	#
	#    ⛔ But seven flat bars have about twenty levels in all **by
	#      construction**: on that scene the level count does not tell a
	#      poor path from a rich one, and a red there would be a red on the
	#      scene.  A gradient from black to white as wide as the screen
	#      crosses all 256: it is the only part of the image on which that
	#      count means something.
	#
	#    ⭐ This way ONE single scene answers all three questions — the
	#       frame is there (the movement), it is the DESKTOP (the bars), how many bits are
	#       real (the gradient) — and F2.3 can redo the same count on the same
	#       frame instead of on another.
	local corsa=$((LARGHEZZA - 160))
	local y_sfumatura=$((ALTEZZA - 240))
	ffmpeg -nostdin -loglevel error -y \
	       -f lavfi -i "smptebars=size=${LARGHEZZA}x${ALTEZZA}:rate=60" \
	       -f lavfi -i "color=black:size=${LARGHEZZA}x100:rate=60,geq=r='floor(X*256/W)':g='floor(X*256/W)':b='floor(X*256/W)'" \
	       -filter_complex "[0][1]overlay=0:${y_sfumatura},drawbox=x='t*720-${corsa}*floor(t*720/${corsa})':y=$((ALTEZZA - 120)):w=160:h=100:color=white:t=fill" \
	       -t 30 -c:v libx264 -preset ultrafast -qp 0 -pix_fmt yuv420p "$f"
	local esito=$?
	if [ $esito -ne 0 ] || [ ! -s "$f" ]; then
		ko "⛔ ffmpeg did not produce the scene (exit $esito)"
		return 1
	fi
	ok "scene generated: $(ls -la "$f")"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ THE SCREEN IS DECLARED TO THE SCENE, AND THEN IT IS CHECKED THAT IT OBEYED
#
# Found on 12 Aug 2026, at the FIRST real round of this bench — and found
# because the bench came out **VERDE** while the defect was alive.
#
# The GNOME session already had a virtual monitor (`Meta-0`, from another round);
# our `RecordVirtual` added a second one (`Meta-1`); and `mpv --fs`
# went full screen on the FIRST.  The scene was alive — `ps` said `Sl`, the
# log counted the seconds, the decoded frames flowed — and our
# capture received **zero frames**.
#
# ⚠ Phase 0 had never met it because back then the session had
#   no other monitor: the monitor mounted by the bench was the only one, and any
#   full-screen window necessarily ended up on it.  ⛔ The defect was not
#   in the phase 0 bench: it was **in the assumption that bench could afford
#   and this one cannot**.
#
# ⇒ `CODER.md` §3.9: *«when a component can decide by itself, tell it what to
#   do — and check that it obeyed»*.  Here the component is mpv, and the thing
#   it decided by itself was which screen to open on.
#
# How one knows which is ours: the monitors are looked at BEFORE mounting and AFTER, and
# the new one is ours.  ⛔ And if not exactly one appears, there is no
# guessing: the failure is declared.
# ---------------------------------------------------------------------------
elenco_monitor()
{
	gdbus call --session --dest org.gnome.Mutter.DisplayConfig \
	           --object-path /org/gnome/Mutter/DisplayConfig \
	           --method org.gnome.Mutter.DisplayConfig.GetCurrentState \
	  > "$QUI/monitor-$1.txt"
	local esito=$?
	if [ $esito -ne 0 ]; then
		# ⛔ A DENIED read is not a read that says «no monitor».
		echo "GUASTO-DBUS"
		return 1
	fi
	grep -o "'Meta-[0-9]*'" "$QUI/monitor-$1.txt" | tr -d "'" | sort -u
	return 0
}

# ⛔ THE MONITOR IS DECLARED BY NAME, NEVER BY INDEX AND NEVER BY SIZE.
#
# Asked by F2.1 (the session) and already paid for in the field: on the server there are TWO
# virtual monitors — `Meta-0` / **MetaVirtualMonitor** (the session's one,
# put there by the F2.1 drop-in) and `Meta-1` / **Virtual remote monitor** (the one that
# `RecordVirtual` mounts, that is ours) — and ⛔ **both are 1920×1080@60**.
# Only the product name tells them apart.
#
# ⇒ Choosing «the first» or «the 1080p one» is error form **E2**: two different
#   things under the same label.  Here the name is taken from the before/after diff
#   AND it is checked that the product matches: two independent roads that
#   must say the same thing, or nothing is measured.
prodotto_di()
{
	python3 - "$QUI/monitor-dopo.txt" "$1" <<'FINE'
import re, sys
testo = open(sys.argv[1]).read()
# ('Meta-1', 'MetaVendor', 'Virtual remote monitor', '0x00')
for connettore, venditore, prodotto in re.findall(
        r"\('(Meta-\d+)', '([^']*)', '([^']*)'", testo):
    if connettore == sys.argv[2]:
        print(prodotto)
        break
else:
    print("SCONOSCIUTO")
FINE
}

SCHERMO=

PRODOTTO_SCHERMO=

trova_il_nostro_schermo()
{
	local prima=$1 dopo nuovi
	dopo=$(elenco_monitor dopo) || { ko "⛔ DisplayConfig does not answer: I do not know which screen we are on"; return 1; }
	nuovi=$(comm -13 <(echo "$prima") <(echo "$dopo"))
	local quanti
	quanti=$(echo "$nuovi" | grep -c '^Meta-')
	inf "monitors before: $(echo "$prima" | tr '\n' ' ')"
	inf "monitors after:  $(echo "$dopo" | tr '\n' ' ')"
	if [ "$quanti" != 1 ]; then
		ko "⛔ after mounting $quanti new monitors appeared, not 1."
		inf "I do not guess which one is ours: without knowing, the scene"
		inf "would go to a screen we are not capturing, and the bench"
		inf "would measure darkness while declaring the scene (12 Aug 2026)."
		return 1
	fi
	SCHERMO=$(echo "$nuovi" | grep '^Meta-')
	PRODOTTO_SCHERMO=$(prodotto_di "$SCHERMO")
	inf "the product name of $SCHERMO is: «$PRODOTTO_SCHERMO»"
	# ⛔ AND THE SECOND ROAD MUST CONFIRM THE FIRST.  Our monitor is
	#    mounted by `RecordVirtual`, and Mutter calls it «Virtual remote monitor»;
	#    the session's one is called «MetaVirtualMonitor».  If the diff
	#    said one and the product name the other, the more convenient one is not
	#    chosen: we stop.
	case "$PRODOTTO_SCHERMO" in
	*"remote"*|*"Remote"*)
		ok "the two roads agree: $SCHERMO is the monitor we mounted"
		;;
	*)
		ko "⛔ the monitor that appeared ($SCHERMO) is called «$PRODOTTO_SCHERMO», and it is not"
		inf "the name Mutter gives a RecordVirtual monitor («Virtual remote"
		inf "monitor»).  The two roads do not agree: I stop instead of choosing."
		inf "⚠ On this server there are two virtual monitors BOTH 1920×1080@60:"
		inf "  only the product name tells them apart (F2.1 seam)."
		return 1
		;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ THE SESSION STATE IS LOOKED AT BEFORE EVERY COUNT, AND IT ENDS UP IN THE OUTCOME
#
# Asked by F2.1, and the reason is that **without it, a zero of mine has no defendant**:
# the GNOME session on NIC-OS ran from 10 Aug with **ZERO MONITORS** —
# started `--headless --no-x11` without `--virtual-monitor`, with `IsSessionRunning`
# true, fifty names on the bus and the applications on.  ⇒ A capture
# pointed there would have measured zero frames, and the blame would have ended up on
# capture.
#
# ⚠ And if the F2.1 tool is not on the server yet, it is DECLARED: a
#   check skipped silently and a check passed look the same,
#   and it is form E8.
STATO_SESSIONE=
guarda_la_sessione()
{
	local s=$SRC/02-sessione-stato.py
	if [ ! -r "$s" ]; then
		STATO_SESSIONE="not available (missing $s, of F2.1)"
		inf "⚠ $STATO_SESSIONE — this round has no witness of the session"
		return 0
	fi
	python3 -u "$s" > "$QUI/sessione.txt" 2>&1
	local esito=$?
	STATO_SESSIONE="02-sessione-stato.py exit $esito"
	sed 's/^/       /' "$QUI/sessione.txt"
	if [ $esito -ne 0 ]; then
		ko "⛔ the session is not healthy ($STATO_SESSIONE)"
		inf "⚠ It is set right with: bash $SRC/02-sessione-lancia.sh sano — and nothing is measured before."
		return 1
	fi
	ok "the session is healthy ($STATO_SESSIONE)"
	return 0
}

avvia_scena()
{
	local f
	case $SCENA in
	bandiera)
		f=$(file_scena)
		if [ ! -s "$f" ]; then echo IGNOTA; return; fi
		# ⛔ `stdbuf -oL`: towards a file the output is block-buffered, and
		#    when the scene closes its log stays in the buffer.  The
		#    empty log looks like «the scene said nothing», and it is
		#    item 12 of `FASI.md` §00-ambiente.
		# ⛔ `--fs-screen-name` is NOT a detail: it is the difference between
		#    measuring the scene and measuring darkness (see the box above).
		stdbuf -oL mpv --no-config --fs --fs-screen-name="$SCHERMO" \
		    --loop=inf --no-audio --no-osc \
		    --no-input-default-bindings --profile=low-latency \
		    "$f" >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	tetto)
		# The phase 0 scene, kept for the link with the historical positive
		# control.  ⛔ And it is launched with `pgrep -f`, never `pgrep -x`: `comm` is
		# truncated to 15 characters and `weston-simple-egl` has 17 — a bench
		# defect already paid for, `FASI.md` §00-ambiente B3 point 1.
		#
		# ⚠ AND HERE THE SCREEN CANNOT BE DECLARED: `weston-simple-egl` has no
		#   option to choose the output.  ⇒ On a session that has more than
		#   one monitor this scene is unreliable, and it is not a defect of the
		#   bench: it is a limit of the client, declared here instead of discovered
		#   by looking at a zero.
		stdbuf -oL weston-simple-egl -f -o >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	fermo)
		# ⭐ The opposite case, as a scene: nobody paints.  The expectation is exit 3
		#    (ZERO FOTOGRAMMI), not a red and not a green.
		echo 0
		;;
	*)
		# ⛔ AND AN UNKNOWN SCENE NAME IS NOT «NO SCENE»: without this
		#    branch, a wrong letter would give a measurement on a screen nobody
		#    drew on, with exit 0.
		echo IGNOTA
		;;
	esac
}

# ---------------------------------------------------------------------------
#  The round
# ---------------------------------------------------------------------------
misura()
{
	local pronto=$QUI/pronto accesa=$QUI/scena-accesa
	local prefisso=$QUI/giro-$(date -u +%Y%m%d-%H%M%S)
	local pid_prod pid_scena stato uscita_prod uscita_giud i morta=

	mkdir -p "$QUI" || return 2
	rm -f "$pronto" "$accesa" "$QUI/scena.log"

	log "0. the initial state is declared AND checked"
	controlla_binario || return 2
	if [ ! -r "$GIUDICE" ]; then ko "⛔ the judge is missing: $GIUDICE"; return 2; fi
	ok "the judge can be read: $GIUDICE"
	if ! pgrep -f 'gnome-shell' >/dev/null; then
		ko "⛔ there is no live gnome-shell: there is nothing to capture"
		inf "⚠ and this is NOT a zero: it is the absence of the defendant. The session belongs to F2.1."
		return 2
	fi
	ok "gnome-shell is alive (pid $(pgrep -f 'gnome-shell' | head -1))"
	guarda_la_sessione || return 2
	if [ "$SCENA" = bandiera ]; then genera_scena || return 2; fi

	log "1. the expectations, written before the round"
	elenco

	log "2. the producer: mounts the virtual monitor and waits for the scene"
	# ⛔ The monitors are counted BEFORE: ours will be the one that appears after.
	local monitor_prima
	monitor_prima=$(elenco_monitor prima)
	if [ "$monitor_prima" = GUASTO-DBUS ]; then
		ko "⛔ DisplayConfig does not answer: the session cannot be queried"
		return 2
	fi
	# ⚠ The «fermo» scene declares it wants to measure the legitimate zero: there the
	#   required minimum is 0, and it is said instead of obtained by chance.
	local minimo=1
	[ "$SCENA" = fermo ] && minimo=0
	local opzioni=(--uscita "$prefisso" --pronto "$pronto" --segnale-scena "$accesa"
	               --larghezza "$LARGHEZZA" --altezza "$ALTEZZA" --fps "$FPS"
	               --dopo-scena "$DOPO_SCENA" --scarta "$SCARTA" --durata "$DURATA"
	               --minimo-dopo-scena "$minimo" --etichetta "$ETICHETTA")
	[ "$STRADA" = dmabuf ] && opzioni+=(--dmabuf)

	"$PROG" "${opzioni[@]}" >"$QUI/produttore.txt" 2>"$QUI/produttore.log" &
	pid_prod=$!

	# ⛔ The EVENT is waited for, not a time: the `pronto` file is written by the
	#    producer when the stream is really ACTIVE.
	for i in $(seq 1 300); do
		[ -f "$pronto" ] && break
		if ! kill -0 $pid_prod 2>/dev/null; then break; fi
		sleep 0.1
	done
	if [ ! -f "$pronto" ]; then
		wait $pid_prod; uscita_prod=$?
		ko "⛔ the producer never declared the stream active (exit $uscita_prod)"
		sed 's/^/       /' "$QUI/produttore.log"
		return 2
	fi
	ok "stream active: the virtual monitor is there and the scene can be switched on"

	log "2-bis. which screen we are on — looked at, not assumed"
	if ! trova_il_nostro_schermo "$monitor_prima"; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		return 2
	fi

	log "3. the scene «$SCENA», switched on AFTER the monitor and ON THE DECLARED SCREEN"
	pid_scena=$(avvia_scena)
	if [ "$pid_scena" = IGNOTA ]; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		ko "⛔ '$SCENA' is not a scene of this bench. They are: bandiera, tetto, fermo."
		return 2
	fi
	if [ "$pid_scena" != 0 ]; then
		sleep 1.5
		# ⛔ AND NOT with `kill -0`, which SUCCEEDS on zombies: a child that died at once
		#    stays in the process table until someone reaps it, and
		#    «the pid exists» is not «the process is alive».  The STATE is read in
		#    `ps`, which says `Z`.  A bench defect already paid for — item 8 of
		#    `FASI.md` §00-ambiente.
		stato=$(ps -o stat= -p "$pid_scena" | tr -d ' ')
		if [ -z "$stato" ] || [ "${stato#Z}" != "$stato" ]; then
			kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
			ko "⛔ the scene died at once (state '$stato'). The log says:"
			sed 's/^/       /' "$QUI/scena.log"
			inf "⚠ It is not a zero of the compositor: it is the absence of something to capture."
			return 2
		fi
		ok "the scene is alive (pid $pid_scena, state $stato)"
	else
		ok "«fermo» scene: nobody paints, and the expectation is exit 3"
	fi
	echo accesa > "$accesa"

	log "4. the take"
	# ⛔ AND THE SCENE IS WATCHED FOR THE WHOLE TAKE, not only for the first second.
	while kill -0 $pid_prod 2>/dev/null; do
		if [ "$pid_scena" != 0 ]; then
			stato=$(ps -o stat= -p "$pid_scena" | tr -d ' ')
			if [ -z "$stato" ] || [ "${stato#Z}" != "$stato" ]; then morta=si; break; fi
		fi
		sleep 0.5
	done
	if [ -n "$morta" ]; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		[ "$pid_scena" != 0 ] && kill "$pid_scena" 2>/dev/null
		ko "⛔ the scene died during the take. The log says:"
		sed 's/^/       /' "$QUI/scena.log"
		return 2
	fi
	wait $pid_prod; uscita_prod=$?
	[ "$pid_scena" != 0 ] && kill "$pid_scena" 2>/dev/null
	sleep 0.5

	sed 's/^/       /' "$QUI/produttore.log"
	cat "$QUI/produttore.txt"
	inf "the producer exited with $uscita_prod"
	if [ $uscita_prod -eq 2 ]; then
		ko "⛔ I FAILED: there is no frame to judge"
		registra "$prefisso" "$uscita_prod" 2 "SONO FALLITO" ""
		return 2
	fi
	if [ $uscita_prod -eq 1 ]; then
		ko "⛔ the environment: monitor not mounted or file not written"
		registra "$prefisso" "$uscita_prod" 2 "AMBIENTE" ""
		return 2
	fi

	log "5. the judgement of the pixels"
	python3 -u "$GIUDICE" --manifesto "$prefisso.json" --scena "$SCENA" \
	        --json "$prefisso-verdetto.json"
	uscita_giud=$?

	registra "$prefisso" "$uscita_prod" "$uscita_giud" \
	         "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("verdetto",""))' \
	            "$prefisso-verdetto.json")" "$prefisso-verdetto.json"

	log "6. the verdict"
	case $uscita_giud in
	0) ok  "⭐ VERDE: a frame is there, it is the one requested, and it contains the scene" ;;
	1) ko  "ROSSO: the frame is there and something does not add up (the marks above)" ;;
	3) inf "⚠ NOTHING TO JUDGE: zero frames, or DMA-BUF road. It is not a red." ;;
	2) ko  "⛔ I FAILED: the judge is not certified, or the files cannot be read" ;;
	esac
	inf "the outcomes are in $ESITI"
	return $uscita_giud
}

# ---------------------------------------------------------------------------
#  The outcomes — one line per round, with the time and the SCENE
# ---------------------------------------------------------------------------
registra()
{
	local prefisso=$1 up=$2 ug=$3 verdetto=$4 vfile=$5
	python3 - "$prefisso" "$up" "$ug" "$verdetto" "$vfile" "$SCENA" "$ETICHETTA" \
	         "$LARGHEZZA" "$ALTEZZA" "$STRADA" "$ESITI" \
	         "${SCHERMO:-ignoto}" "${PRODOTTO_SCHERMO:-ignoto}" "${STATO_SESSIONE:-non guardato}" <<'FINE'
import json, os, sys, time
(prefisso, up, ug, verdetto, vfile, scena, etichetta,
 larghezza, altezza, strada, esiti, schermo, prodotto, stato_sessione) = sys.argv[1:15]
riga = {
    "banco": "F2.2 — la cattura",
    "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "macchina": "NIC-OS (192.168.0.2), sessione GNOME headless",
    "scena": scena,
    "etichetta": etichetta,
    "chiesto": {"larghezza": int(larghezza), "altezza": int(altezza), "strada": strada},
    "uscita_produttore": int(up),
    "uscita_giudice": int(ug),
    "verdetto": verdetto,
    "prefisso": prefisso,
    # ⛔ The monitor is declared BY NAME and with the PRODUCT name: on the server there
    #    are two, both 1920×1080@60, and only that tells them apart.
    "schermo": {"connettore": schermo, "prodotto": prodotto},
    # ⛔ And the session state sits in the line: without it, a zero has no defendant.
    "stato_sessione": stato_sessione,
}
man = prefisso + ".json"
if os.path.exists(man):
    m = json.load(open(man))
    riga["negoziato"] = m.get("negoziato")
    riga["buffer"] = m.get("buffer")
    riga["fotogrammi"] = m.get("fotogrammi")
    riga["esito_produttore"] = m.get("esito")
    # ⛔ The three things F2.3 asks to be DECLARED travel in the outcome line,
    #    not only in the manifest: it is the line the coordinator will read.
    riga["consegna_a_F2_3"] = m.get("consegna_a_F2_3")
    for q in ("primo", "regime"):
        if m.get(q):
            riga[q] = {k: m[q][k] for k in ("byte", "stride", "danno", "seq",
                                            "tipo_dichiarato")}
if vfile and os.path.exists(vfile):
    v = json.load(open(vfile))
    riga["controllo_positivo_passato"] = v.get("controllo_positivo", {}).get("passato")
    riga["danno_parziale_ma_intero"] = v.get("danno_parziale_ma_intero")
    reg = v.get("fotogrammi", {}).get("regime", {}).get("misure", {})
    riga["profondita_misurata"] = reg.get("profondita")
    riga["profondita_sfumatura"] = reg.get("profondita_sfumatura")
    # ⛔ Reds and warnings in two different fields: putting them together would be two outcomes
    #    under the same label (form E2), and in the log one could no longer tell
    #    a bench that saw a defect from one that saw a background.
    riga["rilievi"] = [r["marca"] for f in v.get("fotogrammi", {}).values()
                       for r in f.get("rilievi", []) if r.get("rosso", True)]
    riga["avvisi"] = [r["marca"] for f in v.get("fotogrammi", {}).values()
                      for r in f.get("rilievi", []) if not r.get("rosso", True)]
    riga["rilievi"] += [r["marca"]
                        for r in v.get("confronto_primo_regime", {}).get("rilievi", [])]
with open(esiti, "a") as f:
    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
print("    --  recorded in", esiti)
FINE
}

# ---------------------------------------------------------------------------
case "${1:-misura}" in
compila) compila ;;
scena)   genera_scena ;;
elenco)  elenco ;;
misura)  misura ;;
*)
	echo "usage: $0 [compila|scena|misura|elenco]" >&2
	echo "     SCENA=bandiera|tetto|fermo  STRADA=memoria|dmabuf  LARGHEZZA= ALTEZZA=" >&2
	exit 2
	;;
esac
uscita=$?

# ===========================================================================
# ⛔ THE POSITIVE CONTROL AT THE END OF EVERY EXECUTION — like the diagnosis of
#    `lsquic` in B2.  «Can this tool find something that is surely there?»
#    (`LEZIONI.md` §1.9, second rule.)  A tool that has never found
#    anything is not clean: it is uncertified.
# ===========================================================================
printf '\n\033[1m== positive control at the end ==\033[0m\n'
if [ -r "$GIUDICE" ]; then
	python3 -u "$GIUDICE" --solo-controllo-positivo
	cp_esito=$?
	if [ $cp_esito -ne 0 ]; then
		ko "⛔ THE JUDGE IS NOT CERTIFIED (exit $cp_esito): the green above does not count."
		exit 2
	fi
	ok "the judge finds the flag, calls black the black, and does NOT call black the grey"
else
	ko "⛔ the judge cannot be read: the positive control could not be done"
	exit 2
fi

# And the positive control of the OTHER tool, the one this bench is not:
# does the phase 0 meter exist and is it executable?  If one day it disappeared,
# this bench would stay green and the project would lose its own historical
# positive control without anybody noticing.
STORICO=/media/REMOTIX/tmp/banco-compositori/misura-cattura
if [ -x "$STORICO" ]; then
	ok "the HISTORICAL positive control is in its place: $STORICO (36 ± 2 fps [M] 9 Aug)"
else
	ko "⚠ $STORICO is missing: the project's historical positive control is not executable"
fi

exit $uscita
