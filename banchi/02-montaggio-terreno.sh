#!/bin/bash
#
# 02-montaggio-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), FUORI dal contenitore,
# e vuole `root`.  Prepara la scena in cui il prodotto della fase 2 si puo'
# misurare, e ⛔ **dichiara perche' quella scena e' fatta cosi'**.
#
#   sudo bash /media/REMOTIX/src/02-montaggio-terreno.sh guarda
#   sudo bash /media/REMOTIX/src/02-montaggio-terreno.sh prepara
#
# ===========================================================================
# ⛔⭐ IL FATTO CHE DECIDE TUTTO IL RESTO, MISURATO IL 12 AGOSTO 2026
#
#   `[M]` root NON puo' collegarsi al bus di sessione dell'utente.
#
#   sudo env XDG_RUNTIME_DIR=/run/user/1000 \
#            DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
#            gdbus call --session --dest org.gnome.Mutter.ScreenCast …
#   → ⛔ «Error connecting: The connection is closed», uscita 1.
#
# ⇒ E da qui esce una TENSIONE VERA del prodotto, che questa fase e' la prima
#   a mettere sul tavolo — e non e' un problema di banco:
#
#   | per fare questo                                   | serve essere      |
#   |---------------------------------------------------|-------------------|
#   | verificare con PAM la parola d'ordine di un utente | ⛔ **root**       |
#   |   qualunque (`pam_unix` fuori da root passa da     |                   |
#   |   `unix_chkpwd`, che verifica solo la parola di    |                   |
#   |   CHI LO INVOCA)                                   |                   |
#   | parlare col bus di sessione, con PipeWire e con    | ⛔ **quell'utente**|
#   |   `systemd --user` di quell'utente                 |   (uid 1000 qui)  |
#
#   ⛔ **Le due cose non stanno nello stesso processo**, e oggi il prodotto le
#      chiede tutt'e due allo stesso: `aiutante.c` interroga PAM e `cattura.c`
#      legge PipeWire, dallo stesso albero di processi.  ⇒ Il prodotto vero
#      avra' bisogno della forma che ha gia' usato una volta — un processo per
#      utente, come l'aiutante di `DECISIONI.md` §1.10, ma **al contrario**:
#      il padre root autentica, il figlio scende a uid dell'utente e prende il
#      palco.  E' una decisione del coordinatore, non una riga di codice.
#
# ⭐ Per la fase 2 la scena si sceglie dal lato che NON puo' cedere: il
#    processo gira come **uid 1000**, perche' senza bus non c'e' niente da
#    catturare e la fase non ha oggetto.  Il pezzo che manca — la verifica di
#    un utente diverso — si compra con una riga di configurazione **della
#    macchina di prova**, dichiarata qui sotto.
#
# ===========================================================================
# ⛔ LE DUE RIGHE DI SCENA, E IL LORO PREZZO
#
#  1. l'utente `prova` sull'HOST.  `[M]` sull'host non c'era: `prova` e
#     `prova2` vivono nel contenitore, dove gira il server di casa.  La parola
#     d'ordine e' quella **pubblica** dei banchi (`01-b3-lancia.sh` riga 45):
#     sta in chiaro nel deposito da giorni, quindi qui non si protegge niente
#     che non sia gia' pubblico.  ⚠ Ma passa lo stesso da un file `0600` e
#     mai da una riga di comando — difetto **D12**, e la regola non cambia per
#     una parola pubblica: la disciplina che si applica solo quando conviene
#     non e' una disciplina.
#
#  2. `nicfio` nel gruppo `shadow`, cosi' che `pam_unix` a uid 1000 possa
#     leggere `/etc/shadow` e verificare `prova`.
#     ⚠ **E non regala niente**: `nicfio` ha gia' `sudo`, cioe' root pieno.
#       Questa riga gli da' un sottoinsieme stretto di quel che ha gia'.
#     ⛔ E non sopravvive al riavvio: il rootfs di questa macchina e' live in
#       RAM (`v1/strumenti/sshpw.py`, riquadro in testa) — che e' anche il
#       motivo per cui questo file esiste invece di essere un comando battuto
#       a mano una volta.  Una cura a mano torna.
#
# ⛔ E QUEL CHE QUESTA SCENA **NON** DIMOSTRA, detto prima: che il prodotto
#    autentichi bene un utente qualunque nel suo regime vero.  Dimostra la
#    catena dal fotogramma al filo.  L'autenticazione l'ha gia' certificata la
#    fase 1, dentro il contenitore, da root.
#
set -uo pipefail

FUORI=${FUORI:-/media/REMOTIX/src}
LAV=${LAV:-/media/REMOTIX/tmp/02-montaggio}
UTENTE=${UTENTE:-prova}
UID_PROVA=${UID_PROVA:-1001}
# ⚠ La parola pubblica dei banchi, la stessa di `01-b3-lancia.sh`: se qui ne
#   comparisse un'altra i banchi della fase 1 e questo direbbero cose diverse
#   sullo stesso utente.
PAROLA=${PAROLA:-parola-di-prova}
PADRONE=${PADRONE:-nicfio}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GRUPPI DELLA SCHEDA SI DANNO IN UN POSTO SOLO — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Qui c'era `usermod -aG render,video` (o niente affatto), coi NOMI
#    INCHIODATI e senza rileggere: due difetti in una riga sola.  La ragione
#    per cui la cura sta in un file a parte, e i numeri che la giustificano,
#    stanno nel riquadro in testa a quel file — ⛔ non si ricopiano qui, o
#    diventano dieci posti da cui divergere (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ manca $GRUPPI_SCHEDA_SH: senza, l'inquilino nascerebbe CIECO"; exit 2; }
. "$GRUPPI_SCHEDA_SH"


AZIONE=${1:-guarda}
case "$AZIONE" in guarda|prepara) ;; *) echo "uso: $0 [guarda|prepara]"; exit 2 ;; esac

GUAI=0

log "1. Il servizio PAM sull'host"
if [ -f /etc/pam.d/remotix ]; then
	ok "/etc/pam.d/remotix c'e'"
elif [ "$AZIONE" = prepara ]; then
	if cp "$FUORI/remotix/remotix.pam" /etc/pam.d/remotix; then
		ok "installato /etc/pam.d/remotix"
	else
		ko "⛔ non l'ho potuto installare: senza, PAM ripiega su «other» = pam_deny"
		GUAI=$((GUAI+1))
	fi
else
	ko "⛔ manca: ogni parola d'ordine giusta verrebbe RIFIUTATA, e l'utente"
	ko "   leggerebbe «utente o parola d'ordine non corretti»"
	GUAI=$((GUAI+1))
fi

log "2. L'utente «$UTENTE» sull'host"
if id -u "$UTENTE" >/dev/null 2>&1; then
	ok "«$UTENTE» c'e' (uid $(id -u "$UTENTE"))"
elif [ "$AZIONE" = prepara ]; then
	if useradd -u "$UID_PROVA" -m -s /bin/bash "$UTENTE"; then
		ok "«$UTENTE» creato (uid $UID_PROVA)"
	else
		ko "⛔ non si crea"; GUAI=$((GUAI+1))
	fi
else
	ko "⛔ non c'e': il cliente di prova non avrebbe nessuno con cui entrare"
	GUAI=$((GUAI+1))
fi

if [ "$AZIONE" = prepara ] && id -u "$UTENTE" >/dev/null 2>&1; then
	# ⛔ D12: la riga «utente:parola» che `chpasswd` mangia si scrive in un
	#    file 0600, non in una riga di comando — `/proc/<pid>/cmdline` e'
	#    leggibile da chiunque, e un `ps` durante il giro la stamperebbe.
	# ⛔ `umask` IN UNA SOTTOSHELL: nudo resterebbe addosso a tutto il resto.
	F=$LAV/chpasswd-terreno
	mkdir -p "$LAV"
	ripulisci() { rm -f "$F"; }
	trap ripulisci EXIT
	( umask 077; printf '%s:%s\n' "$UTENTE" "$PAROLA" > "$F" ) || {
		ko "⛔ non si scrive $F"; GUAI=$((GUAI+1)); }
	if [ -f "$F" ]; then
		if chpasswd < "$F"; then ok "parola d'ordine di «$UTENTE» impostata (dalla pubblica dei banchi)"
		else ko "⛔ chpasswd e' fallito"; GUAI=$((GUAI+1)); fi
		rm -f "$F"
	fi
fi

# ⛔⛔ QUI NON C'ERA NIENTE: «$UTENTE» nasceva senza i gruppi dei nodi della
#    scheda, cioe' CIECO (fase 10 §7.4).  In `verifica` non si tocca niente e
#    si CONTA il guaio; in `prepara` si cura e si rilegge.
if id -u "$UTENTE" >/dev/null 2>&1; then
	if [ "$AZIONE" = prepara ]; then
		gruppi_scheda_dai_a "$UTENTE" || GUAI=$((GUAI+1))
	else
		M=$(gruppi_scheda_mancanti "$UTENTE")
		if [ -z "$M" ]; then
			ok "⭐ «$UTENTE» e' nei gruppi dei nodi della scheda: la sua sessione puo' vedere"
		else
			for g in $M; do
				ko "⛔⛔ «$UTENTE» NON e' nel gruppo «$(gruppi_scheda_nome "$g")» (gid $g,"
				ko "   il gruppo di $(gruppi_scheda_nodo "$g")): la sua sessione NASCE CIECA"
			done
			ko "   ⭐ cura: bash $0 prepara"
			GUAI=$((GUAI+1))
		fi
	fi
fi

log "3. «$PADRONE» nel gruppo «shadow» — e la ragione sta nel riquadro in testa"
if id -nG "$PADRONE" 2>/dev/null | tr ' ' '\n' | grep -qx shadow; then
	ok "«$PADRONE» e' gia' nel gruppo shadow"
elif [ "$AZIONE" = prepara ]; then
	if usermod -aG shadow "$PADRONE"; then
		ok "«$PADRONE» aggiunto al gruppo shadow"
		inf "⚠ vale dalla PROSSIMA sessione di login: un processo gia' acceso"
		inf "   tiene i gruppi che aveva quando e' nato"
	else
		ko "⛔ non si aggiunge"; GUAI=$((GUAI+1))
	fi
else
	ko "⛔ non c'e': pam_unix a uid 1000 non potra leggere /etc/shadow, e"
	ko "   ogni parola d'ordine di «$UTENTE» sara' rifiutata"
	GUAI=$((GUAI+1))
fi

log "4. ⛔ Il controllo positivo: la parola d'ordine si verifica davvero?"
# ⚠ Senza questo, «l'utente c'e'» e «l'utente entra» avrebbero lo stesso
#   aspetto, e il primo giro del cliente cadrebbe su una diagnosi che punta
#   sul server.
if command -v python3 >/dev/null 2>&1 && [ -f "$LAV/prova-pam.py" ]; then
	inf "(lo fa il cliente di prova: qui si guarda solo che i pezzi ci siano)"
fi
inf "la prova vera e un giro di 02-filo-cliente.py, che e il lato che RICEVE"

printf '\n'
if [ "$GUAI" -eq 0 ]; then
	printf '    \033[1;32m⭐ il terreno del montaggio c'"'"'e'"'"'\033[0m\n'
	exit 0
fi
printf '    \033[1;31m⛔ %s cose mancano: il giro non si fa\033[0m\n' "$GUAI"
exit 1
