#!/bin/sh
# REMOTIX — lo script d'ingresso, in inglese (DECISIONI §10.35) (fasi/17-l-installatore.md §6.1, §6.5 punto 1).
#
#   curl -fsSL <archive>/install.sh | sudo sh -s -- --archive <archive> [options]
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
# accanto al motore (<archive>/engine/<name>.sha256), scaricato in HTTPS; il motore porta dentro di
# sé il catalogo.
#
#   --archive URL       l'archivio di REMOTIX (D10: un indirizzo pubblico non c'è ancora)
#   --channel C         stable (predefinito) · candidate
#   --check             solo il controllo della macchina: niente viene toccato (anche da utente)
#   --dry-run           il controllo e il PIANO che si applicherebbe: niente viene toccato (da root)
#   --answers FILE      installazione SENZA DOMANDE dal file di risposte (§6.6.12)
#   --tui               le schermate nel terminale (da root), per ssh e console
#   --insecure          (solo prove) accetta un archivio in http:// anche senza lo sha256 scritto qui
#
# ⚠ 10 ott 2026: opzioni, comandi del motore e cartelle dell'archivio in inglese (DECISIONI §10.35).
#   -- …                il resto va al motore così com'è
#
# Tutto il corpo sta in funzioni, e l'ultima riga chiama main: uno scaricamento interrotto a metà
# (curl | sh) non esegue un pezzo di script.
#
# La riga SHA256_MOTORE la scrive il comando di rilascio (TestScript controlla che qui siano vuote).
# ARCHIVIO_PREDEFINITO: l'indirizzo pubblico dell'archivio (D10 aperta: per ora non c'è).

SHA256_MOTORE=''
ARCHIVIO_PREDEFINITO=''

# ---------------------------------------------------------------- messaggi

dice() { printf '%s\n' "$1"; }
errore() {
	printf 'remotix install.sh: ERROR: %s\n' "$1" >&2
	exit 1
}

# ---------------------------------------------------------------- la distribuzione

riconosci() {
	[ "$(uname -s)" = Linux ] || errore "REMOTIX runs on Linux only."
	case $(uname -m) in
	x86_64 | amd64) ;;
	*) errore "architecture $(uname -m): the engine exists for x86_64 only." ;;
	esac
	[ -r /etc/os-release ] || errore "cannot tell the distribution (/etc/os-release is missing: RX-DISTRO-001)."
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
	[ -n "$FAMIGLIA" ] || errore "$PRETTY_NAME: unknown distribution family (REMOTIX knows Debian/Ubuntu, Fedora/Alma, openSUSE, Arch)."
	dice "Distribution: $PRETTY_NAME ($FAMIGLIA family). Whether it is supported is decided by the engine, with its catalogue."
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
		errore "curl or wget is needed: $(comando_installa curl)"
	fi
}

# ---------------------------------------------------------------- lo sha256 (§6.6.10, DECISIONI §10.21)

sha256_di() {
	if command -v sha256sum >/dev/null 2>&1; then
		sha256sum "$1" | cut -d' ' -f1
	elif command -v openssl >/dev/null 2>&1; then
		openssl dgst -sha256 -r "$1" | cut -d' ' -f1
	else
		errore "sha256sum (coreutils) or openssl is needed to verify the engine."
	fi
}

# verifica_sha256 FILE ATTESO — il motore scaricato è quello pubblicato
verifica_sha256() {
	a=$(printf '%s' "$2" | tr 'A-F' 'a-f')
	if [ ${#a} -ne 64 ] || [ -n "$(printf '%s' "$a" | tr -d '0-9a-f')" ]; then
		errore "the published engine sha256 cannot be read (RX-TRUST-017)."
	fi
	h=$(sha256_di "$1")
	[ "$h" = "$a" ] || errore "the downloaded engine is NOT the published one: sha256 $h, expected $a. Nothing proceeds (RX-TRUST-017)."
}

# ---------------------------------------------------------------- main

uso() {
	dice "usage: install.sh --archive URL [--channel stable|candidate] [--check | --dry-run | --tui] [--answers FILE] [--insecure] [-- engine options]"
}

main() {
	ARCHIVIO=${REMOTIX_ARCHIVE:-$ARCHIVIO_PREDEFINITO} CANALE=stable MODO=installa RISPOSTE='' INSICURO=''
	while [ $# -gt 0 ]; do
		case $1 in
		--archive) ARCHIVIO=${2:-}; shift ;;
		--archive=*) ARCHIVIO=${1#*=} ;;
		--channel) CANALE=${2:-}; shift ;;
		--channel=*) CANALE=${1#*=} ;;
		--check) MODO=verifica ;;
		--dry-run) MODO=prova ;;
		--tui) MODO=tui ;;
		--insecure) INSICURO=1 ;;
		--answers) RISPOSTE=${2:-}; shift ;;
		--answers=*) RISPOSTE=${1#*=} ;;
		-h | --help) uso; exit 0 ;;
		--) shift; break ;;
		*) uso >&2; exit 2 ;;
		esac
		shift
	done
	[ -n "$ARCHIVIO" ] || { uso >&2; errore "the archive address is missing (--archive URL)."; }
	ARCHIVIO=${ARCHIVIO%/}
	case $CANALE in stable | candidate) ;; *) errore "channel «$CANALE» (stable · candidate)" ;; esac
	if [ -n "$RISPOSTE" ]; then
		[ -r "$RISPOSTE" ] || errore "the answer file $RISPOSTE cannot be read."
		case $RISPOSTE in /*) ;; *) RISPOSTE=$(pwd)/$RISPOSTE ;; esac
	fi
	# --dry-run vuole root anche lui: il piano legge i file che toccherebbe (polkit, logind), e da
	# utente non si leggono (`[M]` 30 set, debian13-gnome: «lstat /etc/polkit-1/rules.d/…: permission denied»)
	if [ "$MODO" != verifica ] && [ "$(id -u)" -ne 0 ]; then
		errore "installation and --dry-run must be run as root (sudo sh install.sh …); --check need not."
	fi
	riconosci

	T=$(mktemp -d "${TMPDIR:-/tmp}/remotix-install.XXXXXX") || errore "mktemp"
	trap 'rm -rf "$T"' EXIT
	trap 'exit 130' INT TERM
	# una costruzione sola, statica: va ovunque (la finestra è stata tolta, DECISIONI §10.31)
	M=$T/remotix-install
	NOME=remotix-install ATTESO=$SHA256_MOTORE
	DA="this script"
	if [ -z "$ATTESO" ]; then
		# una copia di sviluppo: lo sha256 pubblicato accanto al motore, e SOLO in HTTPS (in http chi
		# sta in mezzo cambierebbe motore e sha256 insieme)
		case $ARCHIVIO in
		https://* | file://*) ;;
		*) [ -n "$INSICURO" ] || errore "the archive $ARCHIVIO is not HTTPS: the engine sha256 would protect nothing (RX-TRUST-017). For testing only: --insecure." ;;
		esac
		scarica "$ARCHIVIO/engine/$NOME.sha256" "$T/atteso" || errore "the engine sha256 cannot be downloaded from $ARCHIVIO (RX-TRUST-017)."
		ATTESO=$(cut -d' ' -f1 <"$T/atteso")
		DA="$ARCHIVIO/engine/$NOME.sha256"
	fi
	dice "Downloading the engine from $ARCHIVIO/engine/ …"
	scarica "$ARCHIVIO/engine/$NOME" "$M" || errore "the engine cannot be downloaded from $ARCHIVIO."
	verifica_sha256 "$M" "$ATTESO"
	chmod 0755 "$M"
	dice "Engine VERIFIED: sha256 equal to the published one ($DA). Handing over to the engine."

	# o dal file di risposte (DECISIONI §10.15: il file di risposte può fissarla)
	comuni="--archive $ARCHIVIO --channel $CANALE"
	case $MODO in
	tui)
		# curl | sh: lo standard input è lo script; le schermate vogliono il terminale
		"$M" tui --archive "$ARCHIVIO" --channel "$CANALE" "$@" </dev/tty
		exit $?
		;;
	verifica)
		# shellcheck disable=SC2086
		"$M" check $comuni "$@"
		exit $?
		;;
	prova)
		# shellcheck disable=SC2086
		"$M" check $comuni >/dev/null 2>&1
		dice "--dry-run: the plan that would be applied (nothing is touched):"
		if [ -n "$RISPOSTE" ]; then
			# shellcheck disable=SC2086
			"$M" plan --install --answers "$RISPOSTE" --output "$T/plan.json" $comuni "$@"
		else
			# shellcheck disable=SC2086
			"$M" plan --install --output "$T/plan.json" $comuni "$@"
		fi
		c=$?
		dice "--dry-run: done, nothing was touched (exit $c)."
		exit $c
		;;
	esac
	if [ -n "$RISPOSTE" ]; then
		# shellcheck disable=SC2086
		"$M" install --answers "$RISPOSTE" $comuni "$@"
	elif [ -r /dev/tty ] && ( : </dev/tty ) 2>/dev/null; then
		# curl | sh: lo standard input è lo script; la conferma si chiede al terminale
		# shellcheck disable=SC2086
		"$M" install $comuni "$@" </dev/tty
	else
		# shellcheck disable=SC2086
		"$M" install $comuni "$@"
	fi
	exit $?
}

main "$@"
