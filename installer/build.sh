#!/bin/sh
# Builds remotix-install (static binary, no cgo) and runs the tests, inside the
# official Go container: Go is not on the laptop, and there is no need to install it.
#
#   ./build.sh            builds output/remotix-install
#   ./build.sh test      go vet + go test (state machine, log, resume: R30 in small)
#   ./build.sh go ...     any go command
#
# The build with the window (gui, previews) is gone: GUI removed on 10 Oct 2026 (DECISIONI §10.31).
#
# RX_VERSION (from the release command, packaging/release.sh): the engine's version, the same as the
# release's packages (-ldflags -X engine.EngineVersion); without it, the one written in format.go.
#
# ⚠ The laptop's /tmp is almost full: the Go cache lives in .cache/ next to this file (ignored by git).
set -eu
here=$(cd "$(dirname "$0")" && pwd)
bitmap=docker.io/library/golang:1.25
ldf="-s -w"
[ -n "${RX_VERSION:-}" ] && ldf="$ldf -X remotix/installer/engine.EngineVersion=$RX_VERSION"
mkdir -p "$here/.cache/go-build" "$here/.cache/tmp" "$here/uscita"
go_() {
	podman run --rm -v "$here:/src:Z" -w /src \
		-e GOCACHE=/src/.cache/go-build -e GOTMPDIR=/src/.cache/tmp -e GOFLAGS=-mod=vendor -e GOPROXY=off \
		-e CGO_ENABLED=0 -e GOTOOLCHAIN=local \
		"$bitmap" "$@"
}
case "${1:-}" in
test)
	go_ sh -c 'gofmt -l cmd engine ui catalog tests | sed "s/^/gofmt: /"; go vet ./... && go test -count=1 ./...'
	;;
go)
	shift
	go_ go "$@"
	;;
*)
	go_ go build -trimpath -ldflags "$ldf" -o uscita/remotix-install ./cmd/remotix-install
	ls -l "$here/uscita/remotix-install"
	;;
esac
