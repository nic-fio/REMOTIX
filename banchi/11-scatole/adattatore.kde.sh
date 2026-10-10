# ===========================================================================
# adattatore.kde.sh — ⭐ HOW **PLASMA** IS STARTED AND WATCHED
# ===========================================================================
#
# ⛔⛔ AND THIS BOX HAS ONE PURPOSE ONLY, today: to show that the net is NOT
#     tailored to GNOME.
#
# ⚠ The product **cannot start KDE yet**: in `src/` there is only the
#   piece that talks to Mutter, and KDE is phase 12.  ⇒ Inside this box,
#   today, only the ENVIRONMENT checks run (step 0), not the
#   meshes of the net that need the product.
#
# ⭐ And that is enough to answer the question that counts: **does the way of testing
#   hold on a compositor that is not Mutter too?**  If the answer is no,
#   it is much better to know it now than at phase 12.
#
# ⛔ The boundary is the same as the other adapter: what goes in here is **how it is started and
#    how it is watched**, NEVER the product's behaviour.
# ===========================================================================

adattatore_nome() { printf 'KDE (KWin)'; }

adattatore_pacchetto() { printf 'kwin-wayland'; }

# ⚠ KWin without a physical monitor is started with `--virtual`, and the size is given
#   on the command line.  ⭐ It is a REAL difference between the two compositors — the
#   same one that `PIANO.md` phase 12 declares: KWin ≤ 6.7.4 takes the size from
#   here and never changes it again.
#   ⇒ It is exactly the kind of thing that must live in an adapter instead
#     of in an `if the desktop is KDE then` inside the list of tests.
adattatore_avvia() {
	_rtd=$1; _log=$2
	runuser -u provanic -- env \
		XDG_RUNTIME_DIR="$_rtd" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$_rtd/bus" \
		XDG_SESSION_TYPE=wayland \
		kwin_wayland --virtual --width 1920 --height 1080 \
		>"$_log" 2>&1 &
	printf '%s' $!
}
