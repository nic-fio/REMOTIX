#!/bin/bash
#
# provisiona.sh — la macchina che ospita REMOTIX_V2, messa nello stato che il
# prodotto si aspetta.  ⛔ E si VERIFICA alla fine, invece di crederci.
#
#   sudo bash src/provisiona.sh            tutto
#   sudo bash src/provisiona.sh verifica   solo i controlli, non tocca niente
#
# ---------------------------------------------------------------------------
# ⛔⛔ PERCHE' NON SI USA PIU' `v1/banco/provision-server.sh`
#
# `[M]` La notte del 15 agosto 2026 quello script, rieseguito dopo un riavvio,
# ha rimesso in piedi lo stato SBAGLIATO e ci e' costato una serata.  In tre
# punti lavora CONTRO v2:
#
#   1. ⛔ scrive `--virtual-monitor 1920x1080` nel drop-in della Shell.  Dal 14
#      agosto quel monitor e' il DIFETTO — «la sessione si prende un monitor suo,
#      la cattura ne monta un secondo, e l'utente guarda quello vuoto»
#      (`sessione.h`).  v2 scrive il proprio drop-in `zz-` per scavalcarlo;
#   2. ⛔ la regola polkit copre 3 azioni su 12 e **manca proprio quelle
#      `*-multiple-sessions`**, cioe' fallisce nel caso multi-utente per cui e'
#      stata scritta (`DECISIONI.md` §4.7);
#   3. ⛔ non ricrea gli utenti di prova ne' i loro gruppi — e il rootfs vive in
#      RAM, quindi ogni riavvio se li porta via.
#
# ---------------------------------------------------------------------------
# ⭐ QUEL CHE IL PRODOTTO NON PUO' FARE DA SE', ed e' l'unica cosa che sta qui
#
# `DECISIONI.md` §1.10-ter, §4.6-quinquies e §4.7: il prodotto mette da se' tutto
# quel che riguarda la SESSIONE (le impostazioni, il drop-in, l'inibizione) —
# invariante I7.  ⛔ Qui resta solo quel che vuole root e vale per la MACCHINA:
# i conti, i gruppi, polkit, logind, udev, PAM.
set -uo pipefail

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
tit() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

ESITO=0
QUI=$(cd "$(dirname "$0")" && pwd)
SOLO_VERIFICA=${1:-}

[ "$(id -u)" -eq 0 ] || { echo "⛔ vuole root"; exit 2; }

# ---------------------------------------------------------------------------
# 1. Gli utenti di prova, e ⛔ I LORO GRUPPI
#
# ⛔⛔ `video` e `render` NON sono una comodita' dell'ambiente di prova: sono un
#     REQUISITO del prodotto, e la ragione e' l'headless.  Su un desktop normale
#     l'accesso alla GPU lo da' logind con un'**ACL** (tag udev `uaccess`)
#     all'utente della sessione attiva **su un seat**; ⇒ la nostra sessione un
#     seat non ce l'ha di proposito, quindi quell'ACL non arriva mai e senza i
#     gruppi Mesa ripiega su llvmpipe **senza un errore**.
#
# `[M]` 15 agosto 2026: il sintomo e' «lento», non «rotto» — un comando nel
# terminale che risponde dopo un secondo, e il compositore che compone a mano un
# desktop di 2544x926.
# ---------------------------------------------------------------------------
if [ "$SOLO_VERIFICA" != "verifica" ]; then
	tit "Gli utenti di prova, coi gruppi che l'headless ci fa perdere"
	for u in prova:1001 prova2:1002; do
		n=${u%%:*}; i=${u##*:}
		id -u "$n" >/dev/null 2>&1 || useradd -u "$i" -m -s /bin/bash "$n"
		usermod -aG video,render "$n"
	done
	printf 'prova:prova2026\nprova2:prova2026\n' | chpasswd
	ok "prova e prova2, in video e render"

	# -------------------------------------------------------------------
	# ⛔⭐ IL LINGER, e non e' una comodita': e' 2,6 secondi per ogni login
	#
	# `[M]` 16 agosto 2026, misurato sul registro.  Senza linger, il gestore
	# d'utente (`user@UID.service`, cioe' `systemd --user` piu' il bus) MUORE a
	# ogni logout e RINASCE al login dopo.  ⇒ Il figlio, che come prima cosa si
	# collega al bus di sessione, restava dentro quella connessione:
	#
	#     senza linger   2,6 s (e 13,7 s al primo giro dopo un riavvio)
	#     con linger     ⭐ 18 ms
	#
	# ⛔ E c'era di peggio: `loginctl` mostrava l'utente in `State=closing` per
	#    decine di secondi, e due giri su dieci hanno aspettato 29 e 32 secondi
	#    un gestore che non finiva di spegnersi.
	#
	# ⚠ E NON contraddice §1.10-ter, che rifiutava il linger COME SOSTITUTO
	#   della sessione PAM: li' il problema era la classe (`manager` invece di
	#   `user`), e resta vero.  ⭐ Qui il linger sta SOTTO la sessione PAM, non
	#   al suo posto: la sessione di classe `user` la apre il prodotto lo
	#   stesso, e il linger tiene solo il gestore caldo fra un login e l'altro.
	# -------------------------------------------------------------------
	for u in prova prova2; do
		loginctl enable-linger "$u" >/dev/null 2>&1
	done
	ok "linger acceso: il gestore d'utente resta caldo fra un login e l'altro"
	inf "⚠ i gruppi arrivano al compositore solo quando RINASCE il gestore"
	inf "   d'utente: se cambi i gruppi a sessione viva, fermala prima"

	# -------------------------------------------------------------------
	# 2. ⛔ VIA il drop-in di v1 col monitor di troppo
	# -------------------------------------------------------------------
	tit "Il drop-in di v1 col monitor di troppo"
	if [ -e /etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf ]; then
		rm -rf /etc/systemd/user/org.gnome.Shell@wayland.service.d
		ok "tolto: v2 scrive il suo, senza --virtual-monitor"
	else
		ok "non c'era"
	fi

	# -------------------------------------------------------------------
	# 3. Le tre cinture di §4.7
	# -------------------------------------------------------------------
	tit "Nessuno spegne il server (DECISIONI.md §4.7)"
	install -D -m 644 "$QUI/remotix-niente-spegnimento.rules" \
		/etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
	rm -f /etc/polkit-1/rules.d/49-remotix-niente-spegnimento.rules
	install -D -m 644 "$QUI/remotix-tasti.conf" \
		/etc/systemd/logind.conf.d/remotix-tasti.conf
	mkdir -p /etc/systemd/sleep.conf.d
	cat > /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf <<'CONF'
# ⛔ La cintura piu' forte delle tre: qui rifiuta SYSTEMD, non polkit, e vale
#    anche per root — `[M]` 15 ago 2026, `CanSuspend="no"` anche da root.
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no
CONF
	systemctl restart polkit >/dev/null 2>&1
	systemctl reload systemd-logind >/dev/null 2>&1 || systemctl restart systemd-logind >/dev/null 2>&1
	ok "polkit (12 azioni), logind (tasti), sleep.conf"

	# -------------------------------------------------------------------
	# 4. Il servizio PAM
	# -------------------------------------------------------------------
	tit "Il servizio PAM"
	install -D -m 644 "$QUI/remotix.pam" /etc/pam.d/remotix
	ok "/etc/pam.d/remotix"

	# -------------------------------------------------------------------
	# 5. ⛔ LA SCHEDA: si misura sull'INTEGRATA — §4.6-quinquies
	#
	# «I test vanno fatti sulla GPU integrata, altrimenti trucchiamo il gioco»
	# — l'utente, 15 agosto 2026.  ⚠ Per indirizzo PCI e non per numero di
	# nodo: `renderD128` e `renderD129` si scambiano fra due avvii.
	# -------------------------------------------------------------------
	tit "La scheda: si esclude la discreta"
	DISCRETA=""
	for c in /sys/class/drm/card[0-9]; do
		[ -e "$c/device/driver" ] || continue
		drv=$(basename "$(readlink -f "$c/device/driver")")
		pci=$(basename "$(readlink -f "$c/device")")
		case "$drv" in
		amdgpu|nvidia|nouveau) DISCRETA="$pci"; inf "discreta: $drv a $pci" ;;
		*)                     inf "integrata: $drv a $pci" ;;
		esac
	done
	if [ -n "$DISCRETA" ] && [ -x /media/REMOTIX/gpu-udev.sh ]; then
		bash /media/REMOTIX/gpu-udev.sh "$DISCRETA" >/dev/null 2>&1 \
			&& ok "esclusa $DISCRETA: si misura sull'integrata" \
			|| ko "la regola udev non e' entrata"
	elif [ -z "$DISCRETA" ]; then
		ok "una scheda sola: niente da escludere"
	else
		ko "manca /media/REMOTIX/gpu-udev.sh"
	fi
fi

# ---------------------------------------------------------------------------
# ⭐ LA VERIFICA — e non e' una formalita': `REVIEWER.md` E1, «scritto non e' in
#    vigore».  ⚠ Quel che si puo' controllare da root si controlla qui; il resto
#    — le due Can* viste DALL'UTENTE — lo verifica il figlio a ogni sessione, e
#    la ragione e' che root si sente rispondere «yes» per via di `CAP_SYS_BOOT`.
# ---------------------------------------------------------------------------
tit "La verifica"

for n in prova prova2; do
	if id -nG "$n" 2>/dev/null | grep -qw render; then ok "$n e' in render"
	else ko "$n NON e' in render: il compositore disegnera' in SOFTWARE"; fi
	if [ "$(loginctl show-user "$n" -p Linger --value 2>/dev/null)" = "yes" ]; then
		ok "$n ha il linger: il gestore d'utente non rinasce a ogni login"
	else
		ko "$n NON ha il linger: ogni login paghera' 2,6 s di gestore d'utente che nasce"
	fi
done

[ -f /etc/pam.d/remotix ] && ok "/etc/pam.d/remotix c'e'" \
	|| ko "/etc/pam.d/remotix manca"
grep -q pam_systemd /etc/pam.d/remotix 2>/dev/null && ok "e chiama pam_systemd" \
	|| ko "⛔ NON chiama pam_systemd: senza, la sessione logind non nasce e il compositore non parte"

[ -f /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules ] && ok "la regola polkit c'e'" \
	|| ko "la regola polkit manca"
grep -q 'multiple-sessions' /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules 2>/dev/null \
	&& ok "e copre le *-multiple-sessions (il caso multi-utente)" \
	|| ko "⛔ NON copre le *-multiple-sessions: fallisce proprio col multi-utente"

VIG=$(systemd-analyze cat-config systemd/logind.conf 2>/dev/null | grep -c '^HandlePowerKey=ignore')
[ "$VIG" -ge 1 ] && ok "il tasto di accensione e' ignorato" \
	|| ko "il tasto di accensione spegne ancora la macchina"

[ -e /etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf ] \
	&& ko "⛔ c'e' ancora il drop-in di v1 col --virtual-monitor" \
	|| ok "nessun drop-in di v1"

echo
if [ "$ESITO" -eq 0 ]; then
	echo "⭐ la macchina e' nello stato che il prodotto si aspetta."
else
	echo "⛔ qualcosa non e' a posto: leggi i NO qui sopra."
fi
exit "$ESITO"
