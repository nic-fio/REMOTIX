# ===========================================================================
# adattatore.gnome.sh — ⭐ HOW **THIS** DESKTOP IS STARTED AND WATCHED
# ===========================================================================
#
# ⛔⛔ THIS FILE IS THE ANSWER TO THE HARDEST QUESTION OF THE PHASE:
#     *«how do you write tests that hold on four different desktops without
#       rewriting them four times?»*  (`fasi/11…` §3.7, and Q3, on which the two
#       external reviewers answered the same thing).
#
# ⭐ The list of tests (C1…C14) is ONE and knows nothing about any desktop.
#    Every box carries a file like this one, at the SAME path —
#    `/usr/local/lib/rete11/adattatore.sh` — that answers a few questions:
#
#       adattatore_nome            what this desktop is called
#       adattatore_pacchetto       which package it comes from, for the fingerprint
#       adattatore_avvia RTD LOG   start the compositor, return its pid
#
# ⛔ THE BOUNDARY, and it must be defended: what goes in here is **how it is started and how
#    it is watched**, NEVER the product's behaviour.  The day an
#    adapter contains a REMOTIX rule, it is no longer an adapter:
#    it is a per-compositor exception in disguise, and the product does not allow them
#    (`DECISIONI.md` §5.1-bis).
# ===========================================================================

adattatore_nome() { printf 'GNOME (Mutter)'; }

adattatore_pacchetto() { printf 'gnome-shell'; }

# starts the compositor in the background, and prints its pid.
#   $1 = the session's private directory
#   $2 = where to write what it says
#
# ⚠⚠ `--virtual-monitor` is there ON PURPOSE, and it is NOT how the product starts it.
#    The product removed it on 14 August 2026 with a measurement behind it
#    (`src/sessione.c:735`): the session is born WITHOUT monitors of its own, and the only
#    monitor is mounted by our capture.
#    ⇒ Here the question is about the ENVIRONMENT — *«can a Wayland compositor
#      live in this box and serve a client?»* — not about the product.
#      ⛔ Asking the product's question without the product inside would mean
#      answering a question different from the one written.
adattatore_avvia() {
	_rtd=$1; _log=$2
	runuser -u provanic -- env \
		XDG_RUNTIME_DIR="$_rtd" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$_rtd/bus" \
		XDG_SESSION_TYPE=wayland \
		gnome-shell --headless --no-x11 --virtual-monitor 1920x1080 \
		>"$_log" 2>&1 &
	printf '%s' $!
}
