#!/usr/bin/env bash
#
# 07-b63-terreno.sh — il terreno del banco A7 (il percorso VIDEO della pagina).
#
#   bash banchi/07-b63-terreno.sh utente     crea `provav7` sulla macchina di prova
#   bash banchi/07-b63-terreno.sh stato      chi c'e', che porte, che carico
#   bash banchi/07-b63-terreno.sh pulisci    toglie l'utente del banco
#
# ⛔ MODELLO: `banchi/04-b20-terreno.sh`, e le tre cose che ne vengono copiate
#    non sono stile — sono tre difetti gia' pagati:
#
#    1. ⛔ LA PAROLA D'ORDINE NON PASSA MAI DALLA RIGA DI COMANDO (difetto D12).
#       `chpasswd` legge da un file `0600`, che si cancella subito dopo.  Una
#       riga `printf 'utente:parola' | chpasswd` dentro un `ssh "…"` finisce
#       nella riga di comando di `ssh` sul portatile, in `ps` sulla macchina di
#       prova e nel registro di questa sessione.
#    2. ⛔ GRUPPO `render`, senza il quale il codificatore ripiega in software —
#       e la misura del ritardo diventa la misura di un'altra macchina.
#    3. ⛔ `loginctl enable-linger`, o il gestore d'utente muore appena l'ultima
#       sessione di logind se ne va, e con lui la sessione grafica.
#
# ⛔ E L'UTENTE `prova` NON SI TOCCA (ne' la 7700, ne' la 7730): sono dell'utente.
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
UTENTE=${UTENTE:-provav7}
UID_B=${UID_B:-1017}
PAROLA=${PAROLA:-provav7-2026}
PORTE_MIE="7771 7772 7773 7774 7775"
PORTE_ALTRUI="7700 7730 7448"
# ⭐ Da dove si prende il testo della cura dei gruppi (vedi il passo `utente`).
QUI_B63=${QUI_B63:-$(cd "$(dirname "$0")" && pwd)}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ⛔ Il copione remoto si spedisce come FILE e si esegue con `sudo -S` che legge
#    la parola d'ordine dallo stdin: e' la trappola gia' pagata in `07-b41`
#    (`printf … | sudo -S bash -s` da' a bash uno stdin gia' consumato).
remoto() {
	local f
	f=$(mktemp)
	cat > "$f"
	scp -q -o BatchMode=yes "$f" "$MACCHINA:/tmp/07-b63-remoto.sh"
	rm -f "$f"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /tmp/07-b63-remoto.sh; rc=\$?; rm -f /tmp/07-b63-remoto.sh; exit \$rc"
}

case "${1:-stato}" in
utente)
	log "L'utente del banco A7: $UTENTE (uid $UID_B)"
	remoto <<FINE
set -u
if id $UTENTE >/dev/null 2>&1; then
	echo "    --  c'e' gia' — non lo rifaccio (una sessione per utente, I2)"
else
	useradd -m -u $UID_B -s /bin/bash $UTENTE || { echo "    NO  useradd"; exit 2; }
	echo "    OK  creato"
fi
# ⛔ 0600, e la parola non compare in nessuna riga di comando.
P=\$(mktemp); chmod 600 "\$P"
printf '%s:%s\n' '$UTENTE' '$PAROLA' > "\$P"
chpasswd < "\$P"; rc=\$?
shred -u "\$P" 2>/dev/null || rm -f "\$P"
[ \$rc -eq 0 ] || { echo "    NO  chpasswd: PAM dira' sempre di no"; exit 2; }
echo "    OK  parola d'ordine posta (da file 0600, mai dalla riga di comando)"
# ⭐⭐ I GRUPPI DELLA SCHEDA — la cura sta in UN FILE SOLO, e qui si INFILA
#    il suo testo perche' il copione gira sulla macchina di prova, dove
#    `banchi/` non c'e'.  ⛔ Qui c'era il solo `render` INCHIODATO, e mancava
#    `video` (il gruppo di `cardN`): meta' della cura di fase 10 §7.4.
$(bash "$QUI_B63/attrezzi-gruppi-scheda.sh" --testo)
gruppi_scheda_dai_a $UTENTE || exit 3
loginctl enable-linger $UTENTE || { echo "    NO  enable-linger"; exit 2; }
echo "    OK  linger acceso: \$(ls -ld /run/user/$UID_B 2>&1)"
FINE
	# ⛔ E il copione remoto puo' essere USCITO ROSSO: senza questa riga il
	#    terreno diceva «fatto» anche quando l'inquilino era rimasto cieco.
	[ $? -eq 0 ] || { ko "⛔⛔ il terreno di $UTENTE NON e' sano: non misurare niente"; exit 3; }
	;;

stato)
	log "Lo stato della macchina di prova"
	ssh -o BatchMode=yes "$MACCHINA" \
		"echo carico: \$(uptime); echo utente: \$(id $UTENTE 2>&1 | head -1); \
		 echo 'porte MIE  :'; for p in $PORTE_MIE; do echo \"  \$p \$(ss -uln | grep -c \":\$p \")\"; done; \
		 echo 'porte ALTRUI (non si toccano):'; for p in $PORTE_ALTRUI; do echo \"  \$p \$(ss -uln | grep -c \":\$p \")\"; done" 2>/dev/null
	;;

pulisci)
	log "Tolgo l'utente del banco"
	remoto <<FINE
set -u
systemctl stop remotix-7771.service 2>/dev/null || true
loginctl disable-linger $UTENTE 2>/dev/null || true
loginctl terminate-user $UTENTE 2>/dev/null || true
sleep 2
userdel -r $UTENTE 2>/dev/null && echo "    OK  $UTENTE tolto" || echo "    --  $UTENTE non c'era"
FINE
	;;
*) ko "uso: $0 <utente|stato|pulisci>"; exit 2 ;;
esac
