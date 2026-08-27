# ===========================================================================
# adattatore.kde.sh — ⭐ COME SI AVVIA E SI GUARDA **PLASMA**
# ===========================================================================
#
# ⛔⛔ E QUESTA SCATOLA HA UNO SCOPO SOLO, oggi: dimostrare che la rete NON e'
#     fatta su misura di GNOME.
#
# ⚠ Il prodotto **non sa ancora accendere KDE**: in `src/` c'e' soltanto il
#   pezzo che parla con Mutter, e KDE e' la fase 12.  ⇒ Dentro questa scatola,
#   oggi, girano soltanto le verifiche dell'AMBIENTE (il passo 0), non le
#   maglie della rete che vogliono il prodotto.
#
# ⭐ E questo basta a rispondere alla domanda che conta: **il modo di provare
#   regge anche su un compositore che non e' Mutter?**  Se la risposta e' no,
#   e' molto meglio saperlo adesso che alla fase 12.
#
# ⛔ Il confine e' lo stesso dell'altro adattatore: qui ci va **come si avvia e
#    come si guarda**, MAI il comportamento del prodotto.
# ===========================================================================

adattatore_nome() { printf 'KDE (KWin)'; }

adattatore_pacchetto() { printf 'kwin-wayland'; }

# ⚠ KWin senza monitor fisico si accende con `--virtual`, e la misura si da'
#   sulla riga di avvio.  ⭐ E' una differenza VERA fra i due compositori — la
#   stessa che `PIANO.md` fase 12 dichiara: KWin ≤ 6.7.4 prende la misura da
#   qui e non la cambia piu'.
#   ⇒ E' esattamente il genere di cosa che deve stare in un adattatore invece
#     che in un `se il desktop e' KDE allora` dentro la lista delle prove.
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
