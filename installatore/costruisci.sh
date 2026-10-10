#!/bin/sh
# Builds remotix-install (static binary, no cgo) and runs the tests, inside the
# official Go container: Go is not on the laptop, and there is no need to install it.
#
#   ./costruisci.sh            builds uscita/remotix-install
#   ./costruisci.sh prove      go vet + go test (state machine, log, resume: R30 in small)
#   ./costruisci.sh go ...     any go command
#
# The build with the window (gui, previews) is gone: GUI removed on 10 Oct 2026 (DECISIONI §10.31).
#
# RX_VERSIONE (from the release command, packaging/rilascio.sh): the engine's version, the same as the
# release's packages (-ldflags -X motore.VersioneMotore); without it, the one written in formato.go.
#
# ⚠ The laptop's /tmp is almost full: the Go cache lives in .cache/ next to this file (ignored by git).
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
