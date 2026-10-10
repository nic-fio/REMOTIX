#!/bin/bash
# ===========================================================================
# 11-capacita-del-prodotto.sh — ⭐⭐ WHAT THE PRODUCT CAN DO, AND ON WHICH
#                                DESKTOP: the list, in one place only
# ===========================================================================
#
# ⛔ It is not executed: it is READ (`source`) by `11-gancio.sh` and by `11-accendi.sh`.
#
# ⛔⛔ WHY IT EXISTS — 21 September 2026, phase 13, increment 2.
#   Until today the «on which desktop does this mesh run» was written TWICE,
#   by hand, in two whitelists: `le_cinque_nuove` in `11-gancio.sh` (all the
#   product meshes) and the `c8b` branch of `11-accendi.sh` (C8b only).
#   ⇒ `fasi/13-xfce.md`, «The bench», points 1 and 2: two places to open, and
#     opening only one of them C8b(xfce) stayed silent at 3 without anything saying so
#     (`LEZIONI.md` §1.46 — two identical lists are two lists that the next
#     day are not any more).
#   ⚠ And the gate gave ONE reason for all: *«the product can only start
#     GNOME and KDE»*.  Since XFCE is born and shows (C1(xfce) green) that
#     sentence is FALSE, and the meshes that look at pixels can judge while
#     those that want input still cannot.  ⇒ The gate must be able to say
#     **for which capability** it skips.
#
# ⭐ THE SHAPE: two small tables.
#   1. what each DESKTOP has from the product  (`capacita_del_desktop`)
#   2. what each MESH wants                    (`capacita_della_maglia`)
#   A mesh runs if the desktop has EVERYTHING it wants; otherwise it skips
#   naming the FIRST missing capability, and why (`perche_manca`); the
#   question is asked with `prodotto_pronto`.
#
# ⛔⛔ AND NO YARDSTICK IS DECIDED HERE.  Opening a capability softens
#     nothing: it only means that the mesh LOOKS, with its usual yardstick.
#     ⇒ A capability is added here IN THE INCREMENT in which the product provides it
#       (`fasi/13-xfce.md`, «The increments»), not before: a 3 that repeats
#       because of a decision taken on purpose is the cousin of the perpetual red (§1.49).
#
# ⚠ A desktop that is NOT here has no capability: all the product
#   meshes skip, and the reason is the real one — the product does not
#   recognise it.  ⇒ The default is CLOSED: a new desktop (the
#   `desktop-nuovo` family) runs nothing until someone writes it here.
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. ⭐ THE DESKTOPS THE PRODUCT CAN START, and what it can do with them.
#
#   immagine   the capture reaches the client       (C1 green on that box)
#   forma      the real shape of the pointer         (C21 green; phase 14: on gnome
#              it was already there, kde/xfce/lxqt open when C21 is green there)
#   input      keyboard and mouse arrive             (C4 green)
#   appunti    the clipboard in both directions      (C17 green)
#
# ⚠ `[M]` gnome and kde: all three — the net of 20 Sep 2026 has them green with
#   their faults seen (`fasi/13-xfce.md`, the baseline).
# ⭐ xfce: ONLY the image — phase 13, increment 2 (21 Sep 2026, C1(xfce)
#   green).  Input is increment 3, the clipboard increment 5.
# ⭐⭐ AND SINCE 21 SEPTEMBER 2026, MORNING, INPUT AND CLIPBOARD TOO — opened
#     only AFTER the measurement, not before: `[M]` binary `0c0634dd`, xfce box
#     rebuilt from scratch, launched by hand with `11-accendi.sh`:
#       C4(xfce)  GREEN · faults `--senza-tasto` and `--scena-sorda` SEEN
#       C6(xfce)  GREEN · fault `--uccidi-la-sessione` SEEN
#       C17(xfce) GREEN (A · B · R, wl-clipboard arbiter) · `--senza-copia` SEEN
#     ⛔ A capability is opened here when the mesh that judges it has given GREEN
#        and has seen its fault — not when the code is there.
# ⭐ lxqt: ALL THREE since 24 September 2026 — phase 14 (`fasi/14-lxqt.md`).  Until
#   then NOTHING: the product said «NO DESKTOP RECOGNISED».  Opened
#   only AFTER the measurement, `[M]` on the development box `rete14-lxqt` (binaries
#   `404f9907` → `1a10a66e`), launched by hand with `11-accendi.sh`:
#     C1(lxqt)×3 GREEN · C2 C3 C4 C6 C8b C17 C20 GREEN · 16 faults out of 16 SEEN
#     (`--senza-tasto` `--scena-sorda` `--uccidi-la-sessione` `--senza-copia` …)
# ---------------------------------------------------------------------------
DESKTOP_COL_PRODOTTO="gnome kde xfce lxqt"

capacita_del_desktop() {
	case "$1" in
	gnome) printf 'immagine input appunti forma' ;;
	kde)   printf 'immagine input appunti forma' ;;
	xfce)  printf 'immagine input appunti forma' ;;
	lxqt)  printf 'immagine input appunti forma' ;;
	*)     printf '' ;;
	esac
}

# ---------------------------------------------------------------------------
# 2. ⭐ WHAT EACH MESH WANTS FROM THE PRODUCT.
#
# ⛔ Only the meshes the gate governs.  C1, C5, C7, C8, C9 and step 0
#   do not go through here: they have always run on every box, and they say by themselves
#   «I could not look» — ⛔ taking them out of the run would be another decision,
#   not this one.
#
#   C2   a window opens                 looks at the PIXEL       ⇒ immagine
#   C3   the frames change              looks at the PIXEL       ⇒ immagine
#   C8b  the page shows from the client looks at the PIXEL       ⇒ immagine
#   C4   the key reaches the screen     sends a KEY              ⇒ + input
#   C6   detaches and finds itself again ⚠ see below             ⇒ + input
#   C17  the clipboard both ways        focus with the client's CLICK
#                                       (`--clic`) and the clipboard ⇒ + input + appunti
#   C20  rebirth after «Log out»        looks at the PIXEL       ⇒ immagine
#
# ⚠⚠ C20 AND THE «LOG OUT» GESTURE — declared, because it is NOT a capability of the
#   product.  Logging out from the menu is a gesture of the DESKTOP (`org.kde.Shutdown`,
#   `org.gnome.SessionManager`, `xfce4-session-logout`), and the mesh looks for it
#   by itself with the same question `src/sessione.c` asks — if in that
#   box none of the three is there, it says **3** and explains which one is missing.
#   ⛔ No «logout» capability is put here: what goes here is what the PRODUCT
#     provides, and the product does not provide the menu.  What the product must provide is
#     noticing that the session has ended — and without the image the session
#     that is reborn could not be judged anyway.
#
# ⛔ C19 is NOT here: it asks nothing of the product.  It looks at the BOX (who
#   stayed inside), and the box exists on every desktop — like C1, C5, C7, C9,
#   C18.  ⇒ Putting a gate on it would mean not looking at the dirt precisely
#   on the desktops where the product does less, which is the opposite of what is needed.
#
# ⚠⚠ C6 AND INPUT — declared, because I did NOT read it in the code.
#   `[R]` 21 Sep 2026: the C6 client (`attacca`) sends neither keys nor
#   clicks, and the scene is started by the bench inside the session (`apri_la_scena`).
#   ⇒ The dependency written here is the PLAN's (`fasi/13-xfce.md`, table
#     of increments: *«3 · … C4(xfce), and C3 · C6 on xfce»*), not a reading
#     of the mesh.  ⛔ Before opening C6(xfce) we decide whether the plan has a
#     reason the code does not show; if it does not, C6 wants only
#     the image and it is moved to the line above.
# ---------------------------------------------------------------------------
capacita_della_maglia() {
	case "$1" in
	C2|C3|C8b|C20) printf 'immagine' ;;
	C4|C6|C22|C23) printf 'immagine input' ;;
	C17)       printf 'immagine input appunti' ;;
	C21)       printf 'immagine input forma' ;;
	# ⛔ A mesh I do not know is not «free»: it wants a capability that
	#   no desktop has, and so it skips saying so instead of running at random.
	*)         printf 'sconosciuta' ;;
	esac
}

# ---------------------------------------------------------------------------
# 3. ⭐ THE REASON, written for whoever reads the log.
# ---------------------------------------------------------------------------
perche_manca() {
	local desktop=$1 capacita=$2
	case " $DESKTOP_COL_PRODOTTO " in
	*" $desktop "*) : ;;
	*)
		printf 'the product does not recognise the desktop «%s» (src/sessione.c, sessione_desktop: «NO DESKTOP RECOGNISED»)' "$desktop"
		return
		;;
	esac
	case "$desktop:$capacita" in
	xfce:input)
		printf 'input on XFCE is increment 3 of phase 13 (virtual-keyboard, virtual-pointer: fasi/13-xfce.md)' ;;
	xfce:appunti)
		printf 'the clipboard on XFCE is increment 5 of phase 13 (fasi/13-xfce.md)' ;;
	*:forma)
		printf 'the real pointer shape does not reach the browser on %s (C21, phase 14)' "$desktop" ;;
	*:sconosciuta)
		printf 'the mesh is not declared in 11-capacita-del-prodotto.sh: I do not know what it wants' ;;
	*)
		printf 'the product does not provide «%s» on %s (11-capacita-del-prodotto.sh)' "$capacita" "$desktop" ;;
	esac
}

# ---------------------------------------------------------------------------
# ⭐ THE GATE'S QUESTION: `prodotto_pronto <maglia> <desktop>`
#
#   returns 0 silently             if everything is there ⇒ the mesh runs
#   returns 1 and PRINTS THE REASON if something is missing ⇒ the mesh skips
#
# ⛔⛔ AND THE DIRECTION IS NOT A MATTER OF TASTE.  The caller writes
#     `if ! perche=$(prodotto_pronto …); then salta …; else gira …`, and ⇒ ONLY
#     0 makes it run.  If this function were not there (file not read, wrong
#     name) the shell would exit 127, ⭐ and 127 SKIPS.  `[M]` 21 Sep 2026:
#     with the opposite direction («missing? 0 = yes») the first draft, without the list,
#     ran EVERYTHING silently — a gate that opens when it breaks.
# ---------------------------------------------------------------------------
prodotto_pronto() {
	local maglia=$1 desktop=$2 c ha detto=""
	ha=" $(capacita_del_desktop "$desktop") "
	# ⭐ We name ALL the missing capabilities, not the first: C17 on xfce
	#   waits for input AND the clipboard, and whoever reads the log must know it.
	#   ⚠ A desktop the product does not recognise has a single reason.
	for c in $(capacita_della_maglia "$maglia"); do
		case "$ha" in
		*" $c "*) : ;;
		*)
			case " $DESKTOP_COL_PRODOTTO " in
			*" $desktop "*) : ;;
			*) perche_manca "$desktop" "$c"; return 1 ;;
			esac
			[ -n "$detto" ] && detto="$detto · "
			detto="$detto$(perche_manca "$desktop" "$c")"
			;;
		esac
	done
	[ -z "$detto" ] && return 0
	printf '%s' "$detto"
	return 1
}
