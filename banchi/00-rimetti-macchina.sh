#!/bin/bash
#
# 00-rimetti-macchina.sh — rimette in piedi la macchina di prova dopo un riavvio,
# partendo da PRIMA del disco.
#
#   bash 00-rimetti-macchina.sh          rimette tutto
#   bash 00-rimetti-macchina.sh controlla dice solo che cosa manca
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE, E PERCHE' NON BASTAVA `provision-server.sh`
#
# Il rootfs del server vive in RAM e si azzera a ogni riavvio.  `provision-server.sh`
# lo sa e rimette tutto — ma **sta su `/media`**, e `/media` NON SI MONTA DA SOLA:
# `/etc/fstab` è vuoto.
#
# Cioè: lo script che rimette in piedi la macchina è irraggiungibile finché
# qualcuno non fa a mano il passo che nessuno script contiene.
#
# ⭐ Misurato il 9 agosto 2026, riavviando davvero il server invece di rileggere
#    lo script — che è precisamente quel che `LEZIONI.md` §2.5-bis prescrive.
#    Trovato, subito dopo l'avvio:
#
#      /media is not a mountpoint
#      /etc/fstab: 1 riga (vuota)
#      ls: cannot access '/media/REMOTIX/provision-server.sh': No such file or directory
#
#    La lezione era scritta dal 7 agosto e **la cura non era mai stata applicata**:
#    era rimasta una nota in un documento, cioè esattamente ciò che l'invariante
#    **I7** vieta — «la protezione di un difetto noto sta nel programma, non in una
#    riga che si può perdere».  Qui non stava nemmeno in una riga: stava in una
#    memoria.
#
# ⚠ E questo file NON risolve il problema alla radice: vive su `/media` anche lui.
#   La radice è una riga in `/etc/fstab` — che però il rootfs in RAM riazzera, per
#   cui va messa da chi costruisce l'immagine del rootfs, non da noi.  Finché non
#   c'è, il primo comando dopo ogni riavvio è il montaggio qui sotto, e questo file
#   serve a non doverselo ricordare **e a non doverlo indovinare**.
# ---------------------------------------------------------------------------
set -uo pipefail

# L'UUID, non il nome del nodo: `nvme0n1p2` è quel che è oggi, l'UUID è quel che
# resta.  È la stessa ragione per cui la GPU si sceglie per id PCI e non per
# numero di nodo (`DECISIONI.md` §4.6-ter).
UUID_MEDIA=53daf650-6732-4c2a-b7b6-ad0b868bf361
BASE=/media/REMOTIX

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

manca=0

log "1. Il disco — il passo che nessuno script conteneva"
if mountpoint -q /media; then
	ok "/media già montata"
else
	ko "/media NON montata: senza questo, $BASE/provision-server.sh non esiste come file"
	manca=1
	if [ "${1:-}" != controlla ]; then
		# ⛔ Niente redirezione dello stderr su un comando che contiene `sudo`:
		#    la richiesta di password va lì, e chi la deve fornire non la vedrebbe
		#    mai (`LEZIONI.md` §2.3-bis).
		sudo -S -p 'Password: ' mount "UUID=$UUID_MEDIA" /media
		if mountpoint -q /media; then
			ok "montata"
		else
			ko "montaggio fallito: mi fermo qui, il resto non ha senso"
			exit 1
		fi
	fi
fi

log "2. Lo script del ripristino"
if [ -f "$BASE/provision-server.sh" ]; then
	ok "$BASE/provision-server.sh raggiungibile"
else
	ko "non c'è nemmeno col disco montato: la macchina è in uno stato che non conosciamo"
	exit 1
fi

if [ "${1:-}" = controlla ]; then
	log "3. Che cosa manca, senza toccare niente"
	for p in gnome-shell vainfo libei1 kwin-wayland; do
		dpkg -s "$p" >/dev/null 2>&1 && ok "$p" || { ko "$p"; manca=1; }
	done
	id -nG "$(id -un)" | grep -qw render && ok "gruppo render" || { ko "gruppo render"; manca=1; }
	[ -d "$BASE/tmp/banco-compositori" ] && ok "i banchi" || { ko "i banchi"; manca=1; }
	exit $manca
fi

log "3. Il ripristino dichiarato"
bash "$BASE/provision-server.sh" || exit 1

log "Fatto"
echo "    ⚠ i gruppi supplementari valgono per i processi NUOVI: la sessione ssh"
echo "      da cui hai lanciato questo script ha ancora i gruppi di prima."
