#!/bin/sh
# Costruisce remotix-install (binario statico, niente cgo) e fa girare le prove, dentro il
# contenitore ufficiale di Go: sul portatile Go non c'è, e non serve installarlo.
#
#   ./costruisci.sh            costruisce uscita/remotix-install
#   ./costruisci.sh prove      go vet + go test (macchina a stati, registro, ripresa: R30 in piccolo)
#   ./costruisci.sh go ...     un comando go qualunque
#   ./costruisci.sh gui        la costruzione CON LA FINESTRA: uscita/remotix-install-gui (cgo, legata
#                              alle librerie grafiche del sistema, nel contenitore Contenitore.gui su
#                              glibc di Debian 12; DECISIONI §10.19). Stesso sorgente, etichetta «gui»
#   ./costruisci.sh anteprime DATI USCITA [it|en]   le schermate in PNG fuori schermo (dati: una
#                              cartella con verifica.json e piano.json di una macchina)
#
# ⚠ /tmp del portatile è quasi pieno: la cache di Go sta in .cache/ qui accanto (ignorata da git).
set -eu
qui=$(cd "$(dirname "$0")" && pwd)
immagine=docker.io/library/golang:1.25
mkdir -p "$qui/.cache/go-build" "$qui/.cache/tmp" "$qui/uscita"
go_() {
	podman run --rm -v "$qui:/src:Z" -w /src \
		-e GOCACHE=/src/.cache/go-build -e GOTMPDIR=/src/.cache/tmp -e GOFLAGS=-mod=vendor -e GOPROXY=off \
		-e CGO_ENABLED=0 -e GOTOOLCHAIN=local \
		"$immagine" "$@"
}
gui_() {
	podman image exists localhost/remotix-costruzione-gui || podman build -q -t remotix-costruzione-gui -f "$qui/Contenitore.gui" "$qui" >/dev/null
	podman run --rm -v "$qui:/src:Z" -w /src \
		-e GOCACHE=/src/.cache/go-build -e GOTMPDIR=/src/.cache/tmp -e GOFLAGS=-mod=vendor -e GOPROXY=off \
		-e CGO_ENABLED=1 -e GOTOOLCHAIN=local -e EGL_PLATFORM=surfaceless \
		localhost/remotix-costruzione-gui "$@"
}
case "${1:-}" in
gui)
	gui_ go build -tags gui -trimpath -ldflags "-s -w" -o uscita/remotix-install-gui ./cmd/remotix-install
	ls -l "$qui/uscita/remotix-install-gui"
	;;
anteprime)
	# i dati e l'uscita dentro questa cartella (il contenitore vede solo lei)
	gui_ go build -tags gui -trimpath -ldflags "-s -w" -o uscita/remotix-install-gui ./cmd/remotix-install
	gui_ ./uscita/remotix-install-gui gui --anteprima "$3" --dati "$2" --lingua "${4:-it}"
	;;
prove)
	go_ sh -c 'gofmt -l cmd motore interfaccia catalogo prove | sed "s/^/gofmt: /"; go vet ./... && go test -count=1 ./...'
	;;
go)
	shift
	go_ go "$@"
	;;
*)
	go_ go build -trimpath -ldflags "-s -w" -o uscita/remotix-install ./cmd/remotix-install
	ls -l "$qui/uscita/remotix-install"
	;;
esac
