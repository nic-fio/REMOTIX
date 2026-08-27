# ===========================================================================
# adattatore.xfce.sh — ⭐ COME SI AVVIA E SI GUARDA **XFCE**
# ===========================================================================
#
# ⚠⚠ XFCE NON HA UN COMPOSITORE SUO SU WAYLAND, e questa e' la differenza piu'
#    grossa fra questa famiglia e le prime due.  GNOME porta Mutter, KDE porta
#    KWin; ⛔ XFCE (4.20) porta una SESSIONE e si appoggia a un compositore di
#    famiglia `wlroots` — `labwc` oppure `wayfire`.
#
# ⇒ ⭐ Qui si sceglie **labwc**, ed e' una scelta DICHIARATA, non ovvia:
#     · e' il piu' leggero dei due, e questa fase misura l ambiente non il gusto;
#     · e' uno dei due che il progetto ha gia' clonato per studiarli
#       (`reference-xfce/labwc`, `reference-xfce/wayfire`).
#   ⛔ E va rimessa in discussione nella fase 13, dove il prodotto dovra' parlare
#     con quel compositore davvero: se la scelta cambia, cambia QUESTO file e
#     non la lista delle prove.  ⭐ Che e' esattamente il motivo per cui esiste
#     un adattatore.
#
# ⛔ Il confine e' lo stesso degli altri: qui ci va **come si avvia e come si
#    guarda**, MAI il comportamento del prodotto.
# ===========================================================================

adattatore_nome() { printf 'XFCE (labwc, famiglia wlroots)'; }

adattatore_pacchetto() { printf 'labwc'; }

# ⚠ `WLR_BACKENDS=headless` e' il modo in cui un compositore wlroots nasce
#   SENZA schermo fisico — l equivalente di `--headless` di Mutter e di
#   `--virtual` di KWin.  ⭐ Tre compositori, tre parole diverse per la stessa
#   cosa: e' precisamente il genere di differenza che deve stare qui sotto e non
#   dentro la lista delle prove.
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
