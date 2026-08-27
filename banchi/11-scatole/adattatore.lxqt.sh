# ===========================================================================
# adattatore.lxqt.sh — ⭐ COME SI AVVIA E SI GUARDA **LXQt**
# ===========================================================================
#
# ⚠⚠ E QUI VA DETTA SUBITO LA COSA SCOMODA, invece di lasciarla scoprire a
#    qualcuno fra sei mesi: ⛔ **questo adattatore e' quasi identico a quello di
#    XFCE**, e non per pigrizia.
#
#    LXQt, come XFCE, non porta un compositore suo su Wayland: porta una
#    SESSIONE e si appoggia a uno di famiglia `wlroots`.  `PIANO.md` fase 13 lo
#    dice in una riga — *«il terzo e il quarto desktop, che condividono wlroots
#    e quindi quasi tutto»* — e `DECISIONI.md` §… ha gia' MISURATO `labwc`
#    sotto l'etichetta **«labwc (XFCE, LXQt)»**: una misura sola, valida per
#    due desktop.
#
# ⇒ ⭐ LA CONSEGUENZA, dichiarata: **la quarta scatola non mette alla prova un
#     quarto compositore.**  Mette alla prova una quarta SESSIONE e una quarta
#     ricetta.  ⛔ Chi legge i risultati deve saperlo, o contera' quattro prove
#     indipendenti dove ce ne sono tre.
#
# ⚠ E resta comunque utile averla: fra la terza e la quarta scatola cambiano i
#   pacchetti, le dipendenze che si tirano dietro e il demone d'inattivita' —
#   e `DECISIONI.md` ha gia' un rilievo che riguarda LXQt e non XFCE
#   (`enableIdlenessWatcher` che il demone riscrive a `true` al primo avvio).
#
# ⛔ Il confine e' lo stesso di tutti: qui ci va **come si avvia e come si
#    guarda**, MAI il comportamento del prodotto.
# ===========================================================================

adattatore_nome() { printf 'LXQt (labwc, famiglia wlroots)'; }

adattatore_pacchetto() { printf 'labwc'; }

# ⚠ `WLR_BACKENDS=headless` e' il modo in cui un compositore wlroots nasce
#   SENZA schermo fisico — l equivalente di `--headless` di Mutter e di
#   `--virtual` di KWin.  ⭐ Tre parole diverse per la stessa cosa: e'
#   precisamente il genere di differenza che deve stare qui sotto e non dentro
#   la lista delle prove.
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
