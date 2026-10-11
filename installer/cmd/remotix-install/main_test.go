package main

import (
	"testing"

	"remotix/installer/engine"
)

// The plan states the port before «Proceed? [y/N]»: the chosen one, the stock one, none on an upgrade.
func TestPortLine(t *testing.T) {
	for _, c := range []struct {
		o    engine.InstallOptions
		want string
	}{
		{engine.InstallOptions{Porta: 7447}, "Port: 7447 (TCP+UDP) — use --port N to change it"},
		{engine.InstallOptions{}, "Port: 7447 (TCP+UDP) — use --port N to change it"},
		{engine.InstallOptions{Porta: 8443}, "Port: 8443 (TCP+UDP) — use --port N to change it"},
		{engine.InstallOptions{Porta: 8443, Update: true}, ""},
	} {
		if got := portLine(c.o); got != c.want {
			t.Errorf("portLine(%+v) = %q, want %q", c.o, got, c.want)
		}
	}
}
