#!/bin/sh
# Costruisce remotix-install (binario statico, niente cgo) e fa girare le prove, dentro il
# contenitore ufficiale di Go: sul portatile Go non c'è, e non serve installarlo.
#
#   ./costruisci.sh            costruisce uscita/remotix-install
#   ./costruisci.sh prove      go vet + go test (macchina a stati, registro, ripresa: R30 in piccolo)
#   ./costruisci.sh go ...     un comando go qualunque
#
# La costruzione con la finestra (gui, anteprime) non c'è più: GUI tolta il 10 ott 2026 (DECISIONI §10.31).
#
# RX_VERSIONE (dal comando di rilascio, packaging/rilascio.sh): la versione del motore, la stessa dei
# pacchetti del rilascio (-ldflags -X motore.VersioneMotore); senza, quella scritta in formato.go.
#
# ⚠ /tmp del portatile è quasi pieno: la cache di Go sta in .cache/ qui accanto (ignorata da git).
set -eu
qui=$(cd "$(dirname "$0")" && pwd)
immagine=docker.io/library/golang:1.25
ldf="-s -w"
[ -n "${RX_VERSIONE:-}" ] && ldf="$ldf -X remotix/installatore/motore.VersioneMotore=$RX_VERSIONE"
mkdir -p "$qui/.cache/go-build" "$qui/.cache/tmp" "$qui/uscita"
go_() {
	podman run --rm -v "$qui:/src:Z" -w /src \
		-e GOCACHE=/src/.cache/go-build -e GOTMPDIR=/src/.cache/tmp -e GOFLAGS=-mod=vendor -e GOPROXY=off \
		-e CGO_ENABLED=0 -e GOTOOLCHAIN=local \
		"$immagine" "$@"
}
case "${1:-}" in
prove)
	go_ sh -c 'gofmt -l cmd motore interfaccia catalogo prove | sed "s/^/gofmt: /"; go vet ./... && go test -count=1 ./...'
	;;
go)
	shift
	go_ go "$@"
	;;
*)
	go_ go build -trimpath -ldflags "$ldf" -o uscita/remotix-install ./cmd/remotix-install
	ls -l "$qui/uscita/remotix-install"
	;;
esac
