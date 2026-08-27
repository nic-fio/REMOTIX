# ===========================================================================
# adattatore.gnome.sh — ⭐ COME SI AVVIA E SI GUARDA **QUESTO** DESKTOP
# ===========================================================================
#
# ⛔⛔ QUESTO FILE E' LA RISPOSTA ALLA DOMANDA PIU' DIFFICILE DELLA FASE:
#     *«come si scrivono prove che valgano su quattro desktop diversi senza
#       riscriverle quattro volte?»*  (`fasi/11…` §3.7, e la Q3 su cui i due
#       revisori esterni hanno risposto la stessa cosa).
#
# ⭐ La lista delle prove (C1…C14) e' UNA e non sa niente di nessun desktop.
#    Ogni scatola porta un file come questo, allo STESSO percorso —
#    `/usr/local/lib/rete11/adattatore.sh` — che risponde a poche domande:
#
#       adattatore_nome            come si chiama questo desktop
#       adattatore_pacchetto       da che pacchetto viene, per l'impronta
#       adattatore_avvia RTD LOG   accendi il compositore, torna il suo pid
#
# ⛔ IL CONFINE, e va difeso: qui dentro ci va **come si avvia e come si
#    guarda**, MAI il comportamento del prodotto.  Il giorno in cui un
#    adattatore contiene una regola di REMOTIX, non e' piu' un adattatore:
#    e' un'eccezione per compositore travestita, e il prodotto non le ammette
#    (`DECISIONI.md` §5.1-bis).
# ===========================================================================

adattatore_nome() { printf 'GNOME (Mutter)'; }

adattatore_pacchetto() { printf 'gnome-shell'; }

# avvia il compositore in fondo, e stampa il suo pid.
#   $1 = la cartella privata della sessione
#   $2 = dove scrivere quel che dice
#
# ⚠⚠ `--virtual-monitor` c'e' APPOSTA, e NON e' come lo avvia il prodotto.
#    Il prodotto lo ha tolto il 14 agosto 2026 con una misura sotto
#    (`src/sessione.c:735`): la sessione nasce SENZA monitor propri, e l'unico
#    monitor lo monta la nostra cattura.
#    ⇒ Qui la domanda e' sull'AMBIENTE — *«un compositore Wayland riesce a
#      vivere in questa scatola e a servire un cliente?»* — non sul prodotto.
#      ⛔ Chiedere quella del prodotto senza il prodotto dentro vorrebbe dire
#      rispondere a una domanda diversa da quella scritta.
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
