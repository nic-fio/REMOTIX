# ===========================================================================
# adattatore.xfce.sh — ⭐ HOW **XFCE** IS STARTED AND WATCHED
# ===========================================================================
#
# ⚠⚠ XFCE HAS NO COMPOSITOR OF ITS OWN ON WAYLAND, and this is the biggest
#    difference between this family and the first two.  GNOME brings Mutter, KDE brings
#    KWin; ⛔ XFCE (4.20) brings a SESSION and leans on a compositor of the
#    `wlroots` family — `labwc` or `wayfire`.
#
# ⇒ ⭐ Here **labwc** is chosen, and it is a DECLARED choice, not an obvious one:
#     · it is the lighter of the two, and this phase measures the environment, not taste;
#     · it is one of the two the project has already cloned to study them
#       (`reference-xfce/labwc`, `reference-xfce/wayfire`).
#   ⛔ And it must be questioned again in phase 13, where the product will have to talk
#     to that compositor for real: if the choice changes, THIS file changes and
#     not the list of tests.  ⭐ Which is exactly the reason an
#     adapter exists.
#
# ⛔ The boundary is the same as the others: what goes in here is **how it is started and how
#    it is watched**, NEVER the product's behaviour.
# ===========================================================================

adattatore_nome() { printf 'XFCE (labwc, wlroots family)'; }

adattatore_pacchetto() { printf 'labwc'; }

# ⚠ `WLR_BACKENDS=headless` is the way a wlroots compositor is born
#   WITHOUT a physical screen — the equivalent of Mutter's `--headless` and of
#   KWin's `--virtual`.  ⭐ Three compositors, three different words for the same
#   thing: it is precisely the kind of difference that must live down here and not
#   inside the list of tests.
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
