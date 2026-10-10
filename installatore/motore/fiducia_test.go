package motore

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"remotix/installatore/catalogo"
)

// Phase 0 TRUST after simplified D11 (DECISIONI §10.21): the catalogue is the engine's, and the
// engine was delivered by the .run (the sha256) or by the remotix-install package the .run installed. The engine verifies no signatures of its own: the tests check that the catalogue can be read, that this
// engine understands it, and that fiducia.json says where it comes from.

// testSources: the embedded catalogue, a «downloaded» engine.
func testSources(t testing.TB) *TrustSources {
	return &TrustSources{Embedded: catalogo.Embedded, Engine: "/non/esiste/motore"}
}

// a catalogue with sequence and minimum engine changed (the text stays a valid catalogue)
func catalogWith(t testing.TB, seq, minimum string) []byte {
	s := string(catalogo.Embedded)
	c, err := ReadCatalog(catalogo.Embedded)
	if err != nil {
		t.Fatal(err)
	}
	s = strings.Replace(s, `"sequence": `+strconv.Itoa(c.Sequence)+`,`, `"sequence": `+seq+`,`, 1)
	if minimum != "" {
		s = strings.Replace(s, `"motore_minimo": "`+c.EngineMinimum+`"`, `"motore_minimo": "`+minimum+`"`, 1)
	}
	return []byte(s)
}

var today = time.Date(2026, 9, 30, 12, 0, 0, 0, time.UTC)

func code_v(err error) string { return CodeOf(err) }

// The engine's catalogue can be read and this engine understands it; the repository key (the only one,
// the one the package manager uses) is inside the engine.
func TestEmbeddedCatalog(t *testing.T) {
	cat, fid, err := testSources(t).Trusted(today)
	if err != nil {
		t.Fatalf("the embedded catalogue cannot be read: %v", err)
	}
	if cat.Digest == "" || fid.Catalog.Digest != cat.Digest || fid.Sequence != cat.Sequence {
		t.Errorf("attestation: %+v", fid)
	}
	if !strings.Contains(fid.Source, "/non/esiste/motore") || !strings.Contains(fid.Source, "sha256") {
		t.Errorf("the downloaded engine must say that the sha256 guarantees it: %q", fid.Source)
	}
	// the engine of the installed remotix-install package
	f := testSources(t)
	f.Engine = PackagedEngine
	if _, fid, err := f.Trusted(today); err != nil || !strings.Contains(fid.Source, "remotix-install") {
		t.Errorf("package's engine: %v %q", err, fid.Source)
	}
}

// The catalogue given by hand replaces the engine's, and the certificate says so; an unreadable one,
// or one asking for a newer engine, is BLOCKED with its code.
func TestTrust(t *testing.T) {
	d := t.TempDir()
	put_out := func(label_name string, b []byte) string {
		p := filepath.Join(d, label_name)
		if err := os.WriteFile(p, b, 0o644); err != nil {
			t.Fatal(err)
		}
		return p
	}
	f := testSources(t)
	f.Explicit = put_out("a-mano.json", catalogWith(t, "99", ""))
	cat, fid, err := f.Trusted(today)
	if err != nil || cat.Sequence != 99 || !strings.Contains(fid.Source, "a-mano.json") {
		t.Fatalf("by hand: %v %+v", err, fid)
	}
	prova := func(label_name, expected_val string, change func(f *TrustSources)) {
		t.Helper()
		f := testSources(t)
		change(f)
		_, fid, err := f.Trusted(today)
		if code_v(err) != expected_val || len(fid.Messages) == 0 || fid.Messages[len(fid.Messages)-1].Code != expected_val {
			t.Errorf("%s: %v (expected %s)", label_name, err, expected_val)
		}
	}
	prova("by hand, missing", "RX-TRUST-004", func(f *TrustSources) { f.Explicit = filepath.Join(d, "non-c-e.json") })
	prova("by hand, unreadable", "RX-TRUST-004", func(f *TrustSources) { f.Explicit = put_out("rotto.json", []byte("{")) })
	prova("unknown format", "RX-TRUST-004", func(f *TrustSources) {
		f.Embedded = []byte(strings.Replace(string(catalogo.Embedded), "remotix-catalogo/1", "remotix-catalogo/9", 1))
	})
	prova("engine too old", "RX-TRUST-003", func(f *TrustSources) { f.Embedded = catalogWith(t, "7", "99.0.0") })
}

// The operation: a trust that does not verify is BLOCKED before touching anything.
func TestTrustBlocked(t *testing.T) {
	b := newBench(t)
	m := b.motore(t)
	m.Sources.Embedded = catalogWith(t, "7", "99.0.0")
	if op, err := m.Apply(b.piano, false, "prova"); CodeOf(err) != "RX-TRUST-003" || op.State != BLOCKED {
		t.Fatalf("engine too old: %v %v", op.State, err)
	}
}

// Package versions, with the managers' algorithms.
func TestPackageVersions(t *testing.T) {
	cases := []struct {
		fam, a, b string
		r         int
	}{
		{"debian", "0.17.0-1+deb13", "0.17.0-2+deb13", -1},
		{"debian", "0.17.0-2+deb13", "0.18.0-1+deb13", -1},
		{"debian", "0.17.0~git20260929.5cbb97d-1+deb13", "0.17.0-1+deb13", -1},
		{"debian", "1:0.1-1", "0.9-1", 1},
		{"debian", "0.17.0-10+deb13", "0.17.0-9+deb13", 1},
		{"fedora", "0.17.0-1.fc44", "0.17.0-2.fc44", -1},
		{"fedora", "0.17.0-10.fc44", "0.17.0-9.fc44", 1},
		{"fedora", "0.17.0~rc1-1", "0.17.0-1", -1},
		{"arch", "0.17.0-4", "0.17.0-5", -1},
		{"arch", "0.17.0-5", "0.17.0-5", 0},
	}
	for _, c := range cases {
		if r := ComparePackages(c.fam, c.a, c.b); r != c.r {
			t.Errorf("%s %s ⋚ %s = %d, expected %d", c.fam, c.a, c.b, r, c.r)
		}
	}
}
