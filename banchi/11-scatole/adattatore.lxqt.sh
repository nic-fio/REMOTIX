# ===========================================================================
# adattatore.lxqt.sh — ⭐ HOW **LXQt** IS STARTED AND WATCHED
# ===========================================================================
#
# ⚠⚠ AND HERE THE AWKWARD THING MUST BE SAID RIGHT AWAY, instead of letting
#    someone discover it six months from now: ⛔ **this adapter is almost identical to the
#    XFCE one**, and not out of laziness.
#
#    LXQt, like XFCE, does not bring a compositor of its own on Wayland: it brings a
#    SESSION and leans on one from the `wlroots` family.  `PIANO.md` phase 13
#    says it in one line — *«the third and fourth desktops, which share wlroots
#    and therefore almost everything»* — and `DECISIONI.md` §… has already MEASURED `labwc`
#    under the label **«labwc (XFCE, LXQt)»**: a single measurement, valid for
#    two desktops.
#
# ⇒ ⭐ THE CONSEQUENCE, declared: **the fourth box does not test a
#     fourth compositor.**  It tests a fourth SESSION and a fourth
#     recipe.  ⛔ Whoever reads the results must know it, or will count four independent
#     tests where there are three.
#
# ⚠ And it is still useful to have it: between the third and the fourth box the
#   packages change, the dependencies they drag along and the idle daemon —
#   and `DECISIONI.md` already has a finding that concerns LXQt and not XFCE
#   (`enableIdlenessWatcher`, which the daemon rewrites to `true` at first start).
#
# ⛔ The boundary is the same for all: what goes in here is **how it is started and how
#    it is watched**, NEVER the product's behaviour.
# ===========================================================================

adattatore_nome() { printf 'LXQt (labwc, wlroots family)'; }

adattatore_pacchetto() { printf 'labwc'; }

# ⚠ `WLR_BACKENDS=headless` is the way a wlroots compositor is born
#   WITHOUT a physical screen — the equivalent of Mutter's `--headless` and of
#   KWin's `--virtual`.  ⭐ Three different words for the same thing: it is
#   precisely the kind of difference that must live down here and not inside
#   the list of tests.
adattatore_avvia() {
	_rtd=$1; _log=$2
	runuser -u provanic -- env \
		XDG_RUNTIME_DIR="$_rtd" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$_rtd/bus" \
		XDG_SESSION_TYPE=wayland \
		WLR_BACKENDS=headless \
		WLR_LIBINPUT_NO_DEVICES=1 \
		labwc \
		>"$_log" 2>&1 &
	printf '%s' $!
}
