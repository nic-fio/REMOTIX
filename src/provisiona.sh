#!/bin/bash
#
# provisiona.sh — la macchina che ospita REMOTIX, messa nello stato che il
# prodotto si aspetta.  ⛔ E si VERIFICA alla fine, invece di crederci.
#
#   sudo bash src/provisiona.sh            tutto
#   sudo bash src/provisiona.sh verifica   solo i controlli, non tocca niente
#
# ---------------------------------------------------------------------------
# ⛔⛔ PERCHE' NON SI USA PIU' `fondamenta/banco/provision-server.sh`
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
# ⭐⭐ I GRUPPI DELLA SCHEDA SI LEGGONO DAL NODO — 27 agosto 2026, fase 11.
#
# ⛔ Qui c'era `usermod -aG video,render`, cioe' DUE NOMI INCHIODATI.  Sono
#    giusti su questa distribuzione e falsi sulla prossima: il gruppo di
#    `/dev/dri/renderD128` e' quel che il nucleo e udev hanno deciso su QUESTA
#    macchina, e l'unico modo di saperlo e' **chiederglielo** — `stat -c %g`.
# ⛔ E si scorrono i nodi invece di inchiodare `renderD128`: `renderD128` e
#    `renderD129` si scambiano fra due avvii (vedi il passo 5), e `cardN` e
#    `renderDN` hanno gruppi DIVERSI (`video` e `render`) che servono tutt'e due.
# ⚠ Un gid non si passa a `usermod -aG`: si passa il NOME, che si ricava dal
#   numero con `getent group`.  Il numero resta quel che si VERIFICA, perche' un
#   nome puo' cambiare di significato e un gid no.
# ---------------------------------------------------------------------------
gid_della_scheda() {
	local n g
	for n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$n" ] || continue
		g=$(stat -c %g "$n" 2>/dev/null) || continue
		printf '%s\n' "$g"
	done | sort -un
}

nomi_della_scheda() {
	local g nome nomi=""
	for g in $(gid_della_scheda); do
		nome=$(getent group "$g" | cut -d: -f1)
		[ -n "$nome" ] || continue
		case ",$nomi," in *",$nome,"*) continue ;; esac
		nomi="${nomi:+$nomi,}$nome"
	done
	printf '%s' "$nomi"
}

GRUPPI_SCHEDA=$(nomi_della_scheda)

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
#
# ⛔⛔⭐ E IL 27 AGOSTO 2026 IL SINTOMO SI E' RIVELATO PEGGIO DI «LENTO»: e'
#      **CIECO**.  `[M]` Sulla macchina vera, un inquilino senza i due gruppi
#      non vede MAI — **0 sessioni su 4**, zero fotogrammi, mai in 90 secondi —
#      mentre gli inquilini coi gruppi vedono **17 su 17** in ~2,0 s.  ⭐ E la
#      controprova, sullo stesso utente: dati i due gruppi e fatto rinascere il
#      gestore d'utente ⇒ **2,04 s**.
# ⛔⛔ E' `fasi/10-multi-tenant-e-il-budget.md` §7.4, «la sessione che nasce
#      cieca»: `provanic4/5/6` mai riusciti in **98 · 55 · 50** tentativi, e
#      sono esattamente e soltanto i tre utenti che i due gruppi non li avevano.
#      ⇒ Ha bloccato cinque prove e rinviato una fase, e non ha mai dato un
#      errore.  ⭐ Da oggi il PRODOTTO se ne accorge e lo scrive nel registro
#      alla nascita di ogni sessione (`figlio.c`, `gruppi_della_scheda()`).
# ---------------------------------------------------------------------------
if [ "$SOLO_VERIFICA" != "verifica" ]; then
	tit "Gli utenti di prova, coi gruppi che l'headless ci fa perdere"
	if [ -z "$GRUPPI_SCHEDA" ]; then
		ko "⛔ nessun gruppo leggibile dai nodi /dev/dri: gli inquilini nasceranno CIECHI"
	fi
	for u in prova:1001 prova2:1002; do
		n=${u%%:*}; i=${u##*:}
		id -u "$n" >/dev/null 2>&1 || useradd -u "$i" -m -s /bin/bash "$n"
		[ -n "$GRUPPI_SCHEDA" ] && usermod -aG "$GRUPPI_SCHEDA" "$n"
	done
	printf 'prova:prova2026\nprova2:prova2026\n' | chpasswd
	ok "prova e prova2, nei gruppi LETTI DAI NODI: ${GRUPPI_SCHEDA:-nessuno}"

	# -------------------------------------------------------------------
	# ⛔⛔ `~/.cache` DEV'ESSERE UNA CARTELLA SUA, non un collegamento a /tmp
	#
	# `[M]` 25 agosto 2026, incarico F2 — ed e' il difetto per cui il regista
	# ha detto tre volte «Firefox non funziona».
	#
	# `/etc/skel/.cache` di questa macchina e' un COLLEGAMENTO a `/tmp`.
	# ⭐⭐ E NON E' UN GUASTO: e' una SCELTA VOLUTA dell'utente su come deve
	#    funzionare il suo sistema operativo — *«.cache che punta a /tmp e' una
	#    mia scelta voluta»*, 25 agosto 2026, `DECISIONI.md` §4.6-undecies.
	#    ⛔ Quindi qui NON si ripara niente del sistema: la sua scelta resta.
	# ⛔ Il difetto e' NOSTRO: `useradd -m` copia lo scheletro ⇒ i dieci utenti
	#    che creiamo noi nascono TUTTI a scrivere nello stesso posto.
	# Firefox tiene il profilo **locale** sotto `$HOME/.cache/mozilla`, cioe'
	# sotto `/tmp/mozilla`.  ⛔ Il PRIMO utente che apre il browser crea
	# `/tmp/mozilla` **a nome suo e a modo 0700**; da quel momento nessun altro
	# utente ci puo' scrivere, `profiles.ini` non nasce mai, e il browser apre
	# una finestra che dice *«Your Firefox profile cannot be loaded»* — cioe'
	# **e' inutilizzabile per tutti tranne il primo**.
	#
	# ⭐⭐ ED E' IL MULTI-TENANT A RENDERLO CERTO, non a renderlo raro: e' un
	#    difetto che su una macchina a un utente solo non si vede mai, e che su
	#    dieci utenti morde nove.  ⇒ Sta QUI e non nel prodotto: e' la macchina
	#    che dev'essere in ordine (`SPECIFICHE.md` §5.9, parte A).
	#
	# `[M]` La prova, senza browser di mezzo: da `provanic3`
	#     `mkdir -p ~/.cache/mozilla`
	#     → `Permission denied`, con `/tmp/mozilla` di `prova2`, modo 0700.
	# `[M]` E col rimedio, headless e senza REMOTIX: `profiles.ini` nasce.
	#
	# ⚠ Non si tocca `/tmp/mozilla` di chi ce l'ha gia': non e' nostro e non si
	#   sa chi lo usa.  ⛔ E non si tocca ne' `/etc/skel` ne' la home
	#   dell'utente: quella e' casa sua.  Si da' una `~/.cache` vera SOLTANTO
	#   agli utenti che creiamo noi.
	# -------------------------------------------------------------------
	for u in prova prova2; do
		c="/home/$u/.cache"
		if [ -L "$c" ]; then
			rm -f "$c"
			mkdir -p "$c"
			chown "$u:$u" "$c"
			chmod 700 "$c"
			inf "⚠ $u aveva ~/.cache come collegamento: rifatta cartella vera"
		elif [ ! -d "$c" ]; then
			mkdir -p "$c"
			chown "$u:$u" "$c"
			chmod 700 "$c"
		fi
	done
	ok "~/.cache e' una cartella di ciascun utente: il browser puo' fare il suo profilo"

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

	# -------------------------------------------------------------------
	# 6. ⛔⭐⭐ I TRE REQUISITI CHE IL MULTI-TENANT VUOLE E CHE NON ERANO
	#          SCRITTI DA NESSUNA PARTE — 27 agosto 2026, misurati sulla
	#          macchina vera FACENDO la cosa, non ispezionandola.
	#
	#   1. ⛔ IL SERVER DEVE GIRARE DA **ROOT**, o il multi-tenant non esiste.
	#      `[M]` Con `User=nicfio` il prodotto stesso scrive «questo processo
	#      e' uid 1000: NON e' root — PAM potra' verificare solo il suo
	#      utente», e ogni altro inquilino si prende `0x07
	#      CREDENZIALI_ERRATE`.  Da root: «uid 0: puo' verificare con PAM la
	#      parola di chiunque».
	#   2. ⛔ IL BINARIO DEVE STARE DOVE L'INQUILINO PUO' ESEGUIRLO.  `[M]`
	#      `/home/nicfio` e' `0700`: il figlio, che gira con l'uid
	#      dell'inquilino, **non attraversa** quella cartella ed esce con 37 —
	#      «non ha potuto eseguire il binario del server».
	#   3. ⛔ `LD_LIBRARY_PATH` NON ARRIVA AL FIGLIO.  `figlio.c` compone
	#      l'ambiente **da zero** e fa `execve` (CODER.md §4.5): una libreria
	#      fuori dai percorsi di sistema fa uscire il figlio con **127**, e la
	#      variabile del padre non lo raggiunge.  ⇒ La cura sta QUI, dove
	#      vuole root: `/etc/ld.so.conf.d/` piu' `ldconfig`.
	#
	# ⚠ Il punto 1 lo SISTEMA questo script (un drop-in), i punti 2 e 3 li
	#   VERIFICA facendoli — la consegna del binario non e' della provvista.
	# -------------------------------------------------------------------
	tit "I tre requisiti del multi-tenant (27 ago 2026)"
	if systemctl cat remotix.service >/dev/null 2>&1; then
		QUALE=$(systemctl show remotix.service -p User --value 2>/dev/null)
		if [ -n "$QUALE" ] && [ "$QUALE" != "root" ]; then
			install -d -m 755 /etc/systemd/system/remotix.service.d
			cat > /etc/systemd/system/remotix.service.d/zz-remotix-root.conf <<'CONF'
# ⛔⛔ IL SERVER GIRA DA ROOT, e non e' una comodita': e' la condizione del
#     multi-tenant.  `[M]` 27 ago 2026: con `User=` non root, PAM puo'
#     verificare la parola SOLO dell'utente del servizio, e ogni altro
#     inquilino si prende `0x07 CREDENZIALI_ERRATE`.
[Service]
User=root
Group=root
CONF
			systemctl daemon-reload >/dev/null 2>&1
			ok "drop-in zz-remotix-root.conf scritto (era User=$QUALE)"
			inf "⚠ il servizio NON e' stato riavviato: entra in vigore al prossimo riavvio del servizio"
		else
			ok "remotix.service gira gia' da root"
		fi
	else
		inf "remotix.service non e' installato su questa macchina: niente da correggere"
	fi

	# ⭐ Le librerie fuori dai percorsi di sistema si REGISTRANO, perche' la
	#   variabile d'ambiente non attraversa l'`execve` del figlio.
	LIBRERIE=""
	for c in /opt/remotix/lib /opt/remotix/solo "$QUI/lib-remotix"; do
		[ -d "$c" ] || continue
		LIBRERIE="$c"
		break
	done
	if [ -n "$LIBRERIE" ]; then
		printf '# ⛔ `LD_LIBRARY_PATH` non arriva al figlio (execve con ambiente da\n#    zero): le librerie del prodotto si registrano qui.\n%s\n' \
			"$LIBRERIE" > /etc/ld.so.conf.d/zz-remotix.conf
		ldconfig
		ok "librerie del prodotto registrate: $LIBRERIE (ldconfig fatto)"
	else
		inf "nessuna cartella di librerie del prodotto da registrare"
	fi
fi

# ---------------------------------------------------------------------------
# ⭐ LA VERIFICA — e non e' una formalita': `REVIEWER.md` E1, «scritto non e' in
#    vigore».  ⚠ Quel che si puo' controllare da root si controlla qui; il resto
#    — le due Can* viste DALL'UTENTE — lo verifica il figlio a ogni sessione, e
#    la ragione e' che root si sente rispondere «yes» per via di `CAP_SYS_BOOT`.
# ---------------------------------------------------------------------------
tit "La verifica"

# ⭐ Il binario si chiede al SERVIZIO, non si indovina: e' quello che girera'
#   davvero.  ⚠ Se il servizio non c'e', si guarda quello dell'albero.
BINARIO=$(systemctl show remotix.service -p ExecStart --value 2>/dev/null \
	| sed -n 's/.*path=\([^ ;]*\).*/\1/p' | head -1)
[ -n "$BINARIO" ] || BINARIO="$QUI/remotix"

# ⛔⭐⭐ REQUISITO 1 — il server deve girare da ROOT, o il multi-tenant non c'e'.
if systemctl cat remotix.service >/dev/null 2>&1; then
	QUALE=$(systemctl show remotix.service -p User --value 2>/dev/null)
	if [ -z "$QUALE" ] || [ "$QUALE" = "root" ]; then
		ok "remotix.service gira da root: PAM puo' verificare la parola di CHIUNQUE"
	else
		ko "⛔⛔ remotix.service gira come «$QUALE»: PAM potra' verificare SOLO quell'utente, e ogni altro inquilino prendera' 0x07 CREDENZIALI_ERRATE"
	fi
else
	inf "remotix.service non e' installato: il requisito «da root» resta a chi lo lancia a mano"
fi

for n in prova prova2; do
	# ⛔⭐ SI VERIFICA IL **GID DEL NODO**, non il nome «render».  Un `grep -qw
	#     render` su `id -nG` passa anche su una macchina dove il nodo
	#     appartiene a un altro gruppo — cioe' direbbe OK a un inquilino che
	#     nascera' cieco.  ⚠ E si guardano TUTTI i gid dei nodi: `cardN` e
	#     `renderDN` ne hanno due diversi, e servono tutt'e due.
	SUOI=" $(id -G "$n" 2>/dev/null) "
	MANCA=""
	for g in $(gid_della_scheda); do
		case "$SUOI" in *" $g "*) ;; *) MANCA="${MANCA:+$MANCA }$(getent group "$g" | cut -d: -f1) (gid $g)" ;; esac
	done
	if [ -z "$(gid_della_scheda)" ]; then
		ko "⛔ nessun nodo /dev/dri: non si puo' dire se $n vedra'"
	elif [ -z "$MANCA" ]; then
		ok "$n e' in TUTTI i gruppi dei nodi della scheda (${GRUPPI_SCHEDA})"
	else
		ko "⛔⛔ $n NON e' nei gruppi della scheda: $MANCA — la sua sessione NASCERA' CIECA (0 su 4 [M], 27 ago 2026, fase 10 §7.4)"
		inf "   cura: usermod -aG ${GRUPPI_SCHEDA} $n  &&  loginctl terminate-user $n"
	fi
	if [ "$(loginctl show-user "$n" -p Linger --value 2>/dev/null)" = "yes" ]; then
		ok "$n ha il linger: il gestore d'utente non rinasce a ogni login"
	else
		ko "$n NON ha il linger: ogni login paghera' 2,6 s di gestore d'utente che nasce"
	fi
	# ⛔ E si guarda che `~/.cache` sia SUA: se e' un collegamento a `/tmp`, il
	#    profilo del browser finisce in una cartella condivisa che il primo
	#    utente si prende a modo 0700, e da li' in poi il browser non parte
	#    piu' per nessun altro.  ⚠ Non basta guardare il collegamento: si prova
	#    a SCRIVERCI, perche' «scritto non e' in vigore» (E1).
	if [ -L "/home/$n/.cache" ]; then
		ko "⛔ $n ha ~/.cache come COLLEGAMENTO a $(readlink "/home/$n/.cache"): il browser non fara' il profilo"
	elif su -s /bin/sh -c "mkdir -p /home/$n/.cache/.prova-remotix && rmdir /home/$n/.cache/.prova-remotix" "$n" 2>/dev/null; then
		ok "$n puo' scrivere nella sua ~/.cache (il profilo del browser ci sta)"
	else
		ko "⛔ $n NON puo' scrivere nella sua ~/.cache: il browser dira' «Profile Missing»"
	fi

	# ⛔⭐⭐ REQUISITI 2 E 3 IN UNA PROVA SOLA, e si FANNO invece di guardarli.
	#
	#   Si chiede al caricatore di elencare le librerie del binario **con
	#   l'uid dell'inquilino e con l'ambiente A ZERO** — che e' esattamente la
	#   condizione del figlio dopo l'`execve` di `figlio.c`.  ⇒ Una sola riga
	#   risponde a tutt'e due le domande:
	#     · il binario non si attraversa (home `0700`) ⇒ «Permission denied»,
	#       ed e' l'uscita 37 del figlio;
	#     · una libreria non si trova ⇒ «not found», ed e' l'uscita 127.
	# ⚠ `LD_TRACE_LOADED_OBJECTS` fa elencare e NON eseguire: non parte nessun
	#   server, e non si tocca niente di quel che sta girando.
	if [ ! -e "$BINARIO" ]; then
		inf "⚠ $BINARIO non c'e': la prova del caricatore per $n non si puo' fare"
	else
		ESCE=$(su -s /bin/sh -c "env -i LD_TRACE_LOADED_OBJECTS=1 '$BINARIO'" "$n" 2>&1)
		if printf '%s' "$ESCE" | grep -q 'not found'; then
			ko "⛔⛔ a $n MANCANO delle librerie ($(printf '%s' "$ESCE" | grep -c 'not found')): il figlio uscira' con 127.  ⚠ LD_LIBRARY_PATH NON lo raggiunge: la cura e' /etc/ld.so.conf.d + ldconfig"
			printf '%s' "$ESCE" | grep 'not found' | sed 's/^/        /'
		elif printf '%s' "$ESCE" | grep -qi 'permission denied\|cannot execute\|No such file'; then
			ko "⛔⛔ $n NON puo' eseguire $BINARIO: il figlio uscira' con 37.  ⚠ Guarda i modi delle cartelle sul percorso — una home 0700 ferma tutto"
			printf '%s' "$ESCE" | head -2 | sed 's/^/        /'
		else
			ok "$n esegue $BINARIO e ne risolve le librerie con l'ambiente A ZERO (come il figlio)"
		fi
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
