#!/bin/sh
# REMOTIX — lo script d'ingresso / the entry script (fasi/17-l-installatore.md §6.1, §6.5 punto 1).
#
#   curl -fsSL <archivio>/install.sh | sudo sh -s -- --archivio <archivio> [opzioni]
#
# Che cosa fa, e basta: riconosce la distribuzione, scarica il MOTORE d'installazione
# (remotix-install, binario statico) dall'archivio di REMOTIX, ne VERIFICA lo sha256 (§6.6.10,
# DECISIONI §10.21) e gli passa la mano. ⛔ Non copia mai file del prodotto: li mette il gestore di
# pacchetti della distribuzione, guidato dal motore (§6.0 regola 1), dall'archivio firmato con
# l'unica chiave di REMOTIX. Il motore sta in una cartella temporanea, e se ne va con lo script.
#
# La catena, dall'amministratore in giù: lui verifica QUESTO script con lo sha256 pubblicato sul sito
# (HTTPS); lo script verifica il motore con lo sha256 scritto qui sotto dal comando di rilascio
# (packaging/rilascio.sh) — o, in una copia di sviluppo dove la riga è vuota, con quello pubblicato
# accanto al motore (<archivio>/motore/<nome>.sha256), scaricato in HTTPS; il motore porta dentro di
# sé il catalogo.
#
#   --archivio URL      l'archivio di REMOTIX (D10: un indirizzo pubblico non c'è ancora)
#   --canale C          stabile (predefinito) · candidato
#   --verifica          solo il controllo della macchina: niente viene toccato (anche da utente)
#   --dry-run           il controllo e il PIANO che si applicherebbe: niente viene toccato (da root)
#   --risposte FILE     installazione SENZA DOMANDE dal file di risposte (§6.6.12)
#   --lingua it|en      altrimenti dalla lingua del sistema (DECISIONI §10.15)
#   --tui               le schermate nel terminale (da root), per ssh e console
#   --insicuro          (solo prove) accetta un archivio in http:// anche senza lo sha256 scritto qui
#   -- …                il resto va al motore così com'è
#
# Tutto il corpo sta in funzioni, e l'ultima riga chiama main: uno scaricamento interrotto a metà
# (curl | sh) non esegue un pezzo di script.
#
# La riga SHA256_MOTORE la scrive il comando di rilascio (TestScript controlla che qui siano vuote).
# ARCHIVIO_PREDEFINITO: l'indirizzo pubblico dell'archivio (D10 aperta: per ora non c'è).

SHA256_MOTORE=''
ARCHIVIO_PREDEFINITO=''

# ---------------------------------------------------------------- lingua e messaggi

scegli_lingua() {
	L=en
	for v in "${LANGUAGE:-}" "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
		[ -n "$v" ] || continue
		primo=${v%%:*}
		case $primo in it | it_* | it.* | it@*) L=it ;; esac
		break
	done
}

# dice «italiano» «english»
dice() { if [ "$L" = it ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }
errore() {
	if [ "$L" = it ]; then printf 'remotix install.sh: ERRORE: %s\n' "$1" >&2; else printf 'remotix install.sh: ERROR: %s\n' "$2" >&2; fi
	exit 1
}

# ---------------------------------------------------------------- la distribuzione

riconosci() {
	[ "$(uname -s)" = Linux ] || errore "REMOTIX gira solo su Linux." "REMOTIX runs on Linux only."
	case $(uname -m) in
	x86_64 | amd64) ;;
	*) errore "architettura $(uname -m): il motore c'è solo per x86_64." "architecture $(uname -m): the engine exists for x86_64 only." ;;
	esac
	[ -r /etc/os-release ] || errore "non si sa che distribuzione è (/etc/os-release manca: RX-DISTRO-001)." "cannot tell the distribution (/etc/os-release is missing: RX-DISTRO-001)."
	ID='' ID_LIKE='' VERSION_ID='' PRETTY_NAME=''
	# shellcheck disable=SC1091
	. /etc/os-release
	FAMIGLIA=''
	for x in $ID $ID_LIKE; do
		case $x in
		debian | ubuntu) FAMIGLIA=debian ;;
		fedora | rhel | centos | almalinux | rocky) FAMIGLIA=fedora ;;
		opensuse* | suse | sles) FAMIGLIA=suse ;;
		arch) FAMIGLIA=arch ;;
		esac
		[ -n "$FAMIGLIA" ] && break
	done
	[ -n "$FAMIGLIA" ] || errore "$PRETTY_NAME: famiglia di distribuzione sconosciuta (REMOTIX conosce Debian/Ubuntu, Fedora/Alma, openSUSE, Arch)." \
		"$PRETTY_NAME: unknown distribution family (REMOTIX knows Debian/Ubuntu, Fedora/Alma, openSUSE, Arch)."
	dice "Distribuzione: $PRETTY_NAME (famiglia $FAMIGLIA). Se è supportata lo dice il motore, col suo catalogo." \
		"Distribution: $PRETTY_NAME ($FAMIGLIA family). Whether it is supported is decided by the engine, with its catalogue."
}

# il comando che installa un programma mancante, per famiglia
comando_installa() {
	case $FAMIGLIA in
	debian) echo "apt-get install $1" ;;
	fedora) echo "dnf install $1" ;;
	suse) echo "zypper install $1" ;;
	arch) echo "pacman -S $1" ;;
	esac
}

# ---------------------------------------------------------------- scaricare

scarica() { # scarica URL FILE
	if command -v curl >/dev/null 2>&1; then
		curl -fsSL --proto '=https,http,file' -o "$2" "$1"
	elif command -v wget >/dev/null 2>&1; then
		wget -q -O "$2" "$1"
	else
		errore "servono curl o wget: $(comando_installa curl)" "curl or wget is needed: $(comando_installa curl)"
	fi
}

# ---------------------------------------------------------------- lo sha256 (§6.6.10, DECISIONI §10.21)

sha256_di() {
	if command -v sha256sum >/dev/null 2>&1; then
		sha256sum "$1" | cut -d' ' -f1
	elif command -v openssl >/dev/null 2>&1; then
		openssl dgst -sha256 -r "$1" | cut -d' ' -f1
	else
		errore "servono sha256sum (coreutils) o openssl per verificare il motore." "sha256sum (coreutils) or openssl is needed to verify the engine."
	fi
}

# verifica_sha256 FILE ATTESO — il motore scaricato è quello pubblicato
verifica_sha256() {
	a=$(printf '%s' "$2" | tr 'A-F' 'a-f')
	if [ ${#a} -ne 64 ] || [ -n "$(printf '%s' "$a" | tr -d '0-9a-f')" ]; then
		errore "lo sha256 pubblicato del motore non si legge (RX-TRUST-017)." "the published engine sha256 cannot be read (RX-TRUST-017)."
	fi
	h=$(sha256_di "$1")
	[ "$h" = "$a" ] || errore "il motore scaricato NON è quello pubblicato: sha256 $h, atteso $a. Non si procede (RX-TRUST-017)." \
		"the downloaded engine is NOT the published one: sha256 $h, expected $a. Nothing proceeds (RX-TRUST-017)."
}

# ---------------------------------------------------------------- main

uso() {
	dice "uso: install.sh --archivio URL [--canale stabile|candidato] [--verifica | --dry-run | --tui] [--risposte FILE] [--lingua it|en] [--insicuro] [-- opzioni del motore]" \
		"usage: install.sh --archivio URL [--canale stabile|candidato] [--verifica | --dry-run | --tui] [--risposte FILE] [--lingua it|en] [--insicuro] [-- engine options]"
}

main() {
	scegli_lingua
	ARCHIVIO=${REMOTIX_ARCHIVIO:-$ARCHIVIO_PREDEFINITO} CANALE=stabile MODO=installa RISPOSTE='' LINGUA_DATA='' INSICURO=''
	while [ $# -gt 0 ]; do
		case $1 in
		--archivio) ARCHIVIO=${2:-}; shift ;;
		--archivio=*) ARCHIVIO=${1#*=} ;;
		--canale) CANALE=${2:-}; shift ;;
		--canale=*) CANALE=${1#*=} ;;
		--verifica) MODO=verifica ;;
		--dry-run) MODO=prova ;;
		--tui) MODO=tui ;;
		--insicuro) INSICURO=1 ;;
		--risposte) RISPOSTE=${2:-}; shift ;;
		--risposte=*) RISPOSTE=${1#*=} ;;
		--lingua) L=${2:-}; LINGUA_DATA=1; shift ;;
		--lingua=*) L=${1#*=}; LINGUA_DATA=1 ;;
		-h | --help | --aiuto) uso; exit 0 ;;
		--) shift; break ;;
		*) uso >&2; exit 2 ;;
		esac
		shift
	done
	# il file di risposte può fissare la lingua (DECISIONI §10.15), anche per i messaggi di qui
	if [ -z "$LINGUA_DATA" ] && [ -n "$RISPOSTE" ] && [ -r "$RISPOSTE" ]; then
		l=$(sed -n 's/^[[:space:]]*lingua[[:space:]]*=[[:space:]]*\([a-z][a-z]\).*/\1/p' "$RISPOSTE" | head -n 1)
		[ -n "$l" ] && L=$l
	fi
	case $L in it*) L=it ;; *) L=en ;; esac
	[ -n "$ARCHIVIO" ] || { uso >&2; errore "manca l'indirizzo dell'archivio (--archivio URL)." "the archive address is missing (--archivio URL)."; }
	ARCHIVIO=${ARCHIVIO%/}
	case $CANALE in stabile | candidato) ;; *) errore "canale «$CANALE» (stabile · candidato)" "channel «$CANALE» (stabile · candidato)" ;; esac
	if [ -n "$RISPOSTE" ]; then
		[ -r "$RISPOSTE" ] || errore "il file di risposte $RISPOSTE non si legge." "the answer file $RISPOSTE cannot be read."
		case $RISPOSTE in /*) ;; *) RISPOSTE=$(pwd)/$RISPOSTE ;; esac
	fi
	# --dry-run vuole root anche lui: il piano legge i file che toccherebbe (polkit, logind), e da
	# utente non si leggono (`[M]` 30 set, debian13-gnome: «lstat /etc/polkit-1/rules.d/…: permission denied»)
	if [ "$MODO" != verifica ] && [ "$(id -u)" -ne 0 ]; then
		errore "l'installazione e --dry-run vanno lanciati da root (sudo sh install.sh …); --verifica no." "installation and --dry-run must be run as root (sudo sh install.sh …); --verifica need not."
	fi
	riconosci

	T=$(mktemp -d "${TMPDIR:-/tmp}/remotix-install.XXXXXX") || errore "mktemp" "mktemp"
	trap 'rm -rf "$T"' EXIT
	trap 'exit 130' INT TERM
	# una costruzione sola, statica: va ovunque (la finestra è stata tolta, DECISIONI §10.31)
	M=$T/remotix-install
	NOME=remotix-install ATTESO=$SHA256_MOTORE
	DA="questo script" DA_EN="this script"
	if [ -z "$ATTESO" ]; then
		# una copia di sviluppo: lo sha256 pubblicato accanto al motore, e SOLO in HTTPS (in http chi
		# sta in mezzo cambierebbe motore e sha256 insieme)
		case $ARCHIVIO in
		https://* | file://*) ;;
		*) [ -n "$INSICURO" ] || errore "l'archivio $ARCHIVIO non è in HTTPS: lo sha256 del motore non proteggerebbe niente (RX-TRUST-017). Solo per prova: --insicuro." \
			"the archive $ARCHIVIO is not HTTPS: the engine sha256 would protect nothing (RX-TRUST-017). For testing only: --insicuro." ;;
		esac
		scarica "$ARCHIVIO/motore/$NOME.sha256" "$T/atteso" || errore "lo sha256 del motore non si scarica da $ARCHIVIO (RX-TRUST-017)." "the engine sha256 cannot be downloaded from $ARCHIVIO (RX-TRUST-017)."
		ATTESO=$(cut -d' ' -f1 <"$T/atteso")
		DA="$ARCHIVIO/motore/$NOME.sha256" DA_EN=$DA
	fi
	dice "Scarico il motore da $ARCHIVIO/motore/ …" "Downloading the engine from $ARCHIVIO/motore/ …"
	scarica "$ARCHIVIO/motore/$NOME" "$M" || errore "il motore non si scarica da $ARCHIVIO." "the engine cannot be downloaded from $ARCHIVIO."
	verifica_sha256 "$M" "$ATTESO"
	chmod 0755 "$M"
	dice "Motore VERIFICATO: sha256 uguale a quello pubblicato ($DA). Passo la mano al motore." \
		"Engine VERIFIED: sha256 equal to the published one ($DA_EN). Handing over to the engine."

	# la lingua passa al motore solo se data qui: altrimenti il motore la legge da sé, dall'ambiente
	# o dal file di risposte (DECISIONI §10.15: il file di risposte può fissarla)
	comuni="--archivio $ARCHIVIO --canale $CANALE"
	[ -n "$LINGUA_DATA" ] && comuni="$comuni --lingua $L"
	case $MODO in
	tui)
		# curl | sh: lo standard input è lo script; le schermate vogliono il terminale
		"$M" tui --archivio "$ARCHIVIO" --canale "$CANALE" --lingua "$L" "$@" </dev/tty
		exit $?
		;;
	verifica)
		# shellcheck disable=SC2086
		"$M" verifica $comuni "$@"
		exit $?
		;;
	prova)
		# shellcheck disable=SC2086
		"$M" verifica $comuni >/dev/null 2>&1
		dice "--dry-run: il piano che si applicherebbe (niente viene toccato):" "--dry-run: the plan that would be applied (nothing is touched):"
		if [ -n "$RISPOSTE" ]; then
			# shellcheck disable=SC2086
			"$M" piano --installa --risposte "$RISPOSTE" --uscita "$T/piano.json" $comuni "$@"
		else
			# shellcheck disable=SC2086
			"$M" piano --installa --uscita "$T/piano.json" $comuni "$@"
		fi
		c=$?
		dice "--dry-run: fine, niente è stato toccato (uscita $c)." "--dry-run: done, nothing was touched (exit $c)."
		exit $c
		;;
	esac
	if [ -n "$RISPOSTE" ]; then
		# shellcheck disable=SC2086
		"$M" installa --risposte "$RISPOSTE" $comuni "$@"
	elif [ -r /dev/tty ] && ( : </dev/tty ) 2>/dev/null; then
		# curl | sh: lo standard input è lo script; la conferma si chiede al terminale
		# shellcheck disable=SC2086
		"$M" installa $comuni "$@" </dev/tty
	else
		# shellcheck disable=SC2086
		"$M" installa $comuni "$@"
	fi
	exit $?
}

main "$@"
