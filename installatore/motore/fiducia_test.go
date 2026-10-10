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

// fontiProva: the embedded catalogue, a «downloaded» engine.
func fontiProva(t testing.TB) *FontiFiducia {
	return &FontiFiducia{Incorporato: catalogo.Incorporato, Motore: "/non/esiste/motore"}
}

// a catalogue with sequence and minimum engine changed (the text stays a valid catalogue)
func catalogoCon(t testing.TB, seq, minimo string) []byte {
	s := string(catalogo.Incorporato)
	c, err := LeggiCatalogo(catalogo.Incorporato)
	if err != nil {
		t.Fatal(err)
	}
	s = strings.Replace(s, `"sequenza": `+strconv.Itoa(c.Sequenza)+`,`, `"sequenza": `+seq+`,`, 1)
	if minimo != "" {
		s = strings.Replace(s, `"motore_minimo": "`+c.MotoreMinimo+`"`, `"motore_minimo": "`+minimo+`"`, 1)
	}
	return []byte(s)
}

var oggi = time.Date(2026, 9, 30, 12, 0, 0, 0, time.UTC)

func codice(err error) string { return CodiceDi(err) }

// The engine's catalogue can be read and this engine understands it; the repository key (the only one,
// the one the package manager uses) is inside the engine.
func TestCatalogoIncorporato(t *testing.T) {
	cat, fid, err := fontiProva(t).Fidati(oggi)
	if err != nil {
		t.Fatalf("the embedded catalogue cannot be read: %v", err)
	}
	if cat.Digest == "" || fid.Catalogo.Digest != cat.Digest || fid.Sequenza != cat.Sequenza {
		t.Errorf("fiducia: %+v", fid)
	}
	if !strings.Contains(fid.Fonte, "/non/esiste/motore") || !strings.Contains(fid.Fonte, "sha256") {
		t.Errorf("the downloaded engine must say that the sha256 guarantees it: %q", fid.Fonte)
	}
	// the engine of the installed remotix-install package
	f := fontiProva(t)
	f.Motore = MotoreDelPacchetto
	if _, fid, err := f.Fidati(oggi); err != nil || !strings.Contains(fid.Fonte, "remotix-install") {
		t.Errorf("package's engine: %v %q", err, fid.Fonte)
	}
}

// The catalogue given by hand replaces the engine's, and the certificate says so; an unreadable one,
// or one asking for a newer engine, is BLOCKED with its code.
func TestFiducia(t *testing.T) {
	d := t.TempDir()
	scrivi := func(nome string, b []byte) string {
		p := filepath.Join(d, nome)
		if err := os.WriteFile(p, b, 0o644); err != nil {
			t.Fatal(err)
		}
		return p
	}
	f := fontiProva(t)
	f.Esplicito = scrivi("a-mano.json", catalogoCon(t, "99", ""))
	cat, fid, err := f.Fidati(oggi)
	if err != nil || cat.Sequenza != 99 || !strings.Contains(fid.Fonte, "a-mano.json") {
		t.Fatalf("by hand: %v %+v", err, fid)
	}
	prova := func(nome, atteso string, cambia func(f *FontiFiducia)) {
		t.Helper()
		f := fontiProva(t)
		cambia(f)
		_, fid, err := f.Fidati(oggi)
		if codice(err) != atteso || len(fid.Messaggi) == 0 || fid.Messaggi[len(fid.Messaggi)-1].Codice != atteso {
			t.Errorf("%s: %v (expected %s)", nome, err, atteso)
		}
	}
	prova("by hand, missing", "RX-TRUST-004", func(f *FontiFiducia) { f.Esplicito = filepath.Join(d, "non-c-e.json") })
	prova("by hand, unreadable", "RX-TRUST-004", func(f *FontiFiducia) { f.Esplicito = scrivi("rotto.json", []byte("{")) })
	prova("unknown format", "RX-TRUST-004", func(f *FontiFiducia) {
		f.Incorporato = []byte(strings.Replace(string(catalogo.Incorporato), "remotix-catalogo/1", "remotix-catalogo/9", 1))
	})
	prova("engine too old", "RX-TRUST-003", func(f *FontiFiducia) { f.Incorporato = catalogoCon(t, "7", "99.0.0") })
}

// The operation: a trust that does not verify is BLOCKED before touching anything.
func TestFiduciaBloccata(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	m.Fonti.Incorporato = catalogoCon(t, "7", "99.0.0")
	if op, err := m.Applica(b.piano, false, "prova"); CodiceDi(err) != "RX-TRUST-003" || op.Stato != BLOCCATA {
		t.Fatalf("engine too old: %v %v", op.Stato, err)
	}
}

// Package versions, with the managers' algorithms.
func TestVersioniPacchetti(t *testing.T) {
	casi := []struct {
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
	for _, c := range casi {
		if r := ConfrontaPacchetti(c.fam, c.a, c.b); r != c.r {
			t.Errorf("%s %s ⋚ %s = %d, expected %d", c.fam, c.a, c.b, r, c.r)
		}
	}
}
