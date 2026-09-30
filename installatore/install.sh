#!/bin/sh
# REMOTIX — lo script d'ingresso / the entry script (fasi/17-l-installatore.md §6.1, §6.5 punto 1).
#
#   curl -fsSL <archivio>/install.sh | sudo sh -s -- --archivio <archivio> [opzioni]
#
# Che cosa fa, e basta: riconosce la distribuzione, scarica il MOTORE d'installazione
# (remotix-install, binario statico) dall'archivio di REMOTIX, ne VERIFICA la firma con la chiave
# madre della catena A scritta qui sotto (§6.6.10), e gli passa la mano. ⛔ Non copia mai file del
# prodotto: li mette il gestore di pacchetti della distribuzione, guidato dal motore (§6.0 regola 1).
# Il motore sta in una cartella temporanea, e la cartella se ne va con lo script.
#
#   --archivio URL      l'archivio di REMOTIX (D10: un indirizzo pubblico non c'è ancora)
#   --canale C          stabile (predefinito) · candidato
#   --verifica          solo il controllo della macchina: niente viene toccato (anche da utente)
#   --dry-run           il controllo e il PIANO che si applicherebbe: niente viene toccato (da root)
#   --risposte FILE     installazione SENZA DOMANDE dal file di risposte (§6.6.12)
#   --lingua it|en      altrimenti dalla lingua del sistema (DECISIONI §10.15)
#   --finestra          la FINESTRA (GUI), da utente nel desktop: scarica la costruzione con la
#                       finestra (motore/remotix-install-gui, stessa firma, DECISIONI §10.19); i
#                       permessi da amministratore li chiede lei a polkit quando servono
#   --tui               le schermate nel terminale (da root), per ssh e console
#   -- …                il resto va al motore così com'è
#
# Tutto il corpo sta in funzioni, e l'ultima riga chiama main: uno scaricamento interrotto a metà
# (curl | sh) non esegue un pezzo di script.
#
# ⚠ T9: la chiave madre qui sotto è quella DI PROVA della fase 17 (D11); quando ci sarà la vera si
# cambia questa riga insieme a installatore/chiavi/radice-A.pub (TestScriptRadice lo controlla).

RADICE_A='2dmXgOiOluzJJzQxbCZ4OfQiC+NZUDVKIQzuL3Z802M='
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
	dice "Distribuzione: $PRETTY_NAME (famiglia $FAMIGLIA). Se è supportata lo dice il motore, col suo catalogo firmato." \
		"Distribution: $PRETTY_NAME ($FAMIGLIA family). Whether it is supported is decided by the engine, with its signed catalogue."
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

# ---------------------------------------------------------------- la firma (catena A, §6.6.10)
# Il formato è quello di installatore/motore/firma.go: un file .firma JSON (scritto dallo strumento
# chiavi-a, una voce per riga), la sottochiave certificata dalla radice, ed25519. Si verifica con
# openssl (pkeyutl -rawin): nessun programma nostro.

campo() { sed -n "s/^ *\"$1\": *\"\([^\"]*\)\".*/\1/p" "$2" | head -n 1; }

sha256_di() {
	if command -v sha256sum >/dev/null 2>&1; then
		sha256sum "$1" | cut -d' ' -f1
	else
		openssl dgst -sha256 -r "$1" | cut -d' ' -f1
	fi
}

# verifica_ed25519 CHIAVE_BASE64 FILE_MESSAGGIO FIRMA_BASE64
verifica_ed25519() {
	[ "$(printf '%s' "$1" | base64 -d 2>/dev/null | wc -c)" -eq 32 ] || return 1
	{ printf 'MCowBQYDK2VwAyEA' | base64 -d && printf '%s' "$1" | base64 -d; } >"$T/chiave.der" 2>/dev/null || return 1
	printf '%s' "$3" | base64 -d >"$T/firma.bin" 2>/dev/null || return 1
	openssl pkeyutl -verify -pubin -keyform DER -inkey "$T/chiave.der" -rawin -in "$2" -sigfile "$T/firma.bin" >/dev/null 2>&1
}

# verifica_firma FILE FILE.firma OGGETTO — la firma di una sottochiave certificata dalla radice
verifica_firma() {
	f=$1 s=$2 ogg=$3
	command -v openssl >/dev/null 2>&1 || errore "serve openssl per verificare la firma del motore: $(comando_installa openssl). Senza verifica non si procede." \
		"openssl is needed to verify the engine signature: $(comando_installa openssl). Nothing proceeds without verification."
	[ "$(campo formato "$s")" = remotix-firma/1 ] && [ "$(campo catena "$s")" = A ] && [ "$(campo oggetto "$s")" = "$ogg" ] ||
		errore "$ogg: la firma non si legge o non è della catena A per «$ogg» (RX-TRUST-006/007)." "$ogg: the signature cannot be read or is not chain A for «$ogg» (RX-TRUST-006/007)."
	sha=$(campo sha256 "$s")
	[ "$(sha256_di "$f")" = "$sha" ] || errore "$ogg: il contenuto non è quello firmato: alterato (RX-TRUST-007)." "$ogg: the content is not what was signed: altered (RX-TRUST-007)."
	id=$(campo id "$s") pub=$(campo pubblica "$s") dal=$(campo dal "$s") al=$(campo al "$s") fr=$(campo firma_radice "$s")
	printf 'remotix-sottochiave/1\nA\n%s\n%s\n%s\n%s\n' "$id" "$pub" "$dal" "$al" >"$T/msg-sottochiave"
	verifica_ed25519 "$RADICE_A" "$T/msg-sottochiave" "$fr" ||
		errore "$ogg: la chiave che ha firmato non è certificata dalla chiave madre di REMOTIX (RX-TRUST-008)." "$ogg: the signing key is not certified by the REMOTIX root key (RX-TRUST-008)."
	oggi=$(date -u +%Y%m%d) n_dal=$(printf '%s' "$dal" | tr -cd 0-9) n_al=$(printf '%s' "$al" | tr -cd 0-9)
	{ [ -z "$n_dal" ] || [ -z "$n_al" ] || [ "$oggi" -lt "$n_dal" ] || [ "$oggi" -gt "$n_al" ]; } &&
		errore "$ogg: la sottochiave $id vale dal $dal al $al (RX-TRUST-009; controllare anche l'orologio)." "$ogg: subkey $id is valid from $dal to $al (RX-TRUST-009; also check the clock)."
	printf 'remotix-firma/1\nA\n%s\n%s\n' "$ogg" "$sha" >"$T/msg-oggetto"
	verifica_ed25519 "$pub" "$T/msg-oggetto" "$(campo firma "$s")" ||
		errore "$ogg: la firma non è della sottochiave $id (RX-TRUST-007)." "$ogg: the signature is not by subkey $id (RX-TRUST-007)."
	SOTTOCHIAVE=$id
}

# le revoche: firmate dalla RADICE; la sottochiave del motore non deve esserci
verifica_revoche() {
	r=$T/revoche.json
	scarica "$ARCHIVIO/catalogo/revoche.json" "$r" && scarica "$ARCHIVIO/catalogo/revoche.json.firma" "$r.firma" ||
		errore "l'elenco delle revoche non si scarica: senza non si procede (RX-TRUST-012)." "the revocation list cannot be downloaded: nothing proceeds without it (RX-TRUST-012)."
	[ "$(campo oggetto "$r.firma")" = revoche ] && [ "$(sha256_di "$r")" = "$(campo sha256 "$r.firma")" ] || errore "revoche alterate (RX-TRUST-012)." "revocations altered (RX-TRUST-012)."
	printf 'remotix-firma/1\nA\nrevoche\n%s\n' "$(campo sha256 "$r.firma")" >"$T/msg-revoche"
	verifica_ed25519 "$RADICE_A" "$T/msg-revoche" "$(campo firma "$r.firma")" ||
		errore "l'elenco delle revoche non è firmato dalla chiave madre (RX-TRUST-012)." "the revocation list is not signed by the root key (RX-TRUST-012)."
	if grep -q "\"id\": *\"$SOTTOCHIAVE\"" "$r"; then
		errore "la sottochiave $SOTTOCHIAVE che ha firmato il motore è REVOCATA (RX-TRUST-010)." "subkey $SOTTOCHIAVE that signed the engine is REVOKED (RX-TRUST-010)."
	fi
}

# ---------------------------------------------------------------- main

uso() {
	dice "uso: install.sh --archivio URL [--canale stabile|candidato] [--verifica | --dry-run | --finestra | --tui] [--risposte FILE] [--lingua it|en] [-- opzioni del motore]" \
		"usage: install.sh --archivio URL [--canale stabile|candidato] [--verifica | --dry-run | --finestra | --tui] [--risposte FILE] [--lingua it|en] [-- engine options]"
}

main() {
	scegli_lingua
	ARCHIVIO=${REMOTIX_ARCHIVIO:-$ARCHIVIO_PREDEFINITO} CANALE=stabile MODO=installa RISPOSTE='' LINGUA_DATA=''
	while [ $# -gt 0 ]; do
		case $1 in
		--archivio) ARCHIVIO=${2:-}; shift ;;
		--archivio=*) ARCHIVIO=${1#*=} ;;
		--canale) CANALE=${2:-}; shift ;;
		--canale=*) CANALE=${1#*=} ;;
		--verifica) MODO=verifica ;;
		--dry-run) MODO=prova ;;
		--finestra | --window) MODO=finestra ;;
		--tui) MODO=tui ;;
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
	# la finestra, al contrario, NON gira da root (R37): polkit dà i permessi alla sua parte da root
	if [ "$MODO" = finestra ]; then
		[ "$(id -u)" -ne 0 ] || errore "la finestra non si lancia da root: senza sudo (i permessi li chiede lei). RX-UI-003" "the window is not launched as root: without sudo (it asks for permissions itself). RX-UI-003"
		[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ] || errore "non c'è una sessione grafica: usa --tui (da root). RX-UI-002" "there is no graphical session: use --tui (as root). RX-UI-002"
	elif [ "$MODO" != verifica ] && [ "$(id -u)" -ne 0 ]; then
		errore "l'installazione e --dry-run vanno lanciati da root (sudo sh install.sh …); --verifica no." "installation and --dry-run must be run as root (sudo sh install.sh …); --verifica need not."
	fi
	riconosci

	T=$(mktemp -d "${TMPDIR:-/tmp}/remotix-install.XXXXXX") || errore "mktemp" "mktemp"
	trap 'rm -rf "$T"' EXIT
	trap 'exit 130' INT TERM
	# due costruzioni dello stesso sorgente (DECISIONI §10.19): la statica va ovunque; quella con la
	# finestra è legata alle librerie grafiche del sistema e si scarica solo per --finestra
	M=$T/remotix-install
	NOME=remotix-install
	[ "$MODO" = finestra ] && NOME=remotix-install-gui
	dice "Scarico il motore da $ARCHIVIO/motore/ …" "Downloading the engine from $ARCHIVIO/motore/ …"
	scarica "$ARCHIVIO/motore/$NOME" "$M" && scarica "$ARCHIVIO/motore/$NOME.firma" "$M.firma" ||
		errore "il motore non si scarica da $ARCHIVIO." "the engine cannot be downloaded from $ARCHIVIO."
	verifica_firma "$M" "$M.firma" motore
	verifica_revoche
	chmod 0755 "$M"
	dice "Firma del motore VERIFICATA (catena A, sottochiave $SOTTOCHIAVE, chiave madre scritta in questo script). Passo la mano al motore." \
		"Engine signature VERIFIED (chain A, subkey $SOTTOCHIAVE, root key written in this script). Handing over to the engine."

	# la lingua passa al motore solo se data qui: altrimenti il motore la legge da sé, dall'ambiente
	# o dal file di risposte (DECISIONI §10.15: il file di risposte può fissarla)
	comuni="--archivio $ARCHIVIO --canale $CANALE"
	[ -n "$LINGUA_DATA" ] && comuni="$comuni --lingua $L"
	case $MODO in
	finestra)
		# la lingua va passata sempre: polkit ripulisce l'ambiente della parte da root (§10.15)
		"$M" gui --archivio "$ARCHIVIO" --canale "$CANALE" --lingua "$L" "$@"
		exit $?
		;;
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
