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

// La fase 0 TRUST dopo D11 semplificata (DECISIONI §10.21): il catalogo è quello del motore, e il
// motore l'ha consegnato il .run (lo sha256) o il pacchetto remotix-install che il .run ha installato. Il motore non verifica firme sue: le prove guardano che il catalogo si legga, che questo
// motore lo capisca, e che fiducia.json dica da dove viene.

// fontiProva: il catalogo incorporato, un motore «scaricato».
func fontiProva(t testing.TB) *FontiFiducia {
	return &FontiFiducia{Incorporato: catalogo.Incorporato, Motore: "/non/esiste/motore"}
}

// un catalogo con sequenza e motore minimo cambiati (il testo resta un catalogo valido)
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

// Il catalogo del motore si legge e questo motore lo capisce; la chiave dell'archivio (l'unica,
// quella che il gestore di pacchetti usa) è dentro il motore.
func TestCatalogoIncorporato(t *testing.T) {
	cat, fid, err := fontiProva(t).Fidati(oggi)
	if err != nil {
		t.Fatalf("il catalogo incorporato non si legge: %v", err)
	}
	if cat.Digest == "" || fid.Catalogo.Digest != cat.Digest || fid.Sequenza != cat.Sequenza {
		t.Errorf("fiducia: %+v", fid)
	}
	if !strings.Contains(fid.Fonte, "/non/esiste/motore") || !strings.Contains(fid.Fonte, "sha256") {
		t.Errorf("il motore scaricato deve dire che lo garantisce lo sha256: %q", fid.Fonte)
	}
	// il motore del pacchetto remotix-install installato
	f := fontiProva(t)
	f.Motore = MotoreDelPacchetto
	if _, fid, err := f.Fidati(oggi); err != nil || !strings.Contains(fid.Fonte, "remotix-install") {
		t.Errorf("motore del pacchetto: %v %q", err, fid.Fonte)
	}
}

// Il catalogo dato a mano sostituisce quello del motore, e il certificato lo dice; uno illeggibile,
// o che chiede un motore più nuovo, BLOCCA col suo codice.
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
		t.Fatalf("a mano: %v %+v", err, fid)
	}
	prova := func(nome, atteso string, cambia func(f *FontiFiducia)) {
		t.Helper()
		f := fontiProva(t)
		cambia(f)
		_, fid, err := f.Fidati(oggi)
		if codice(err) != atteso || len(fid.Messaggi) == 0 || fid.Messaggi[len(fid.Messaggi)-1].Codice != atteso {
			t.Errorf("%s: %v (atteso %s)", nome, err, atteso)
		}
	}
	prova("a mano, manca", "RX-TRUST-004", func(f *FontiFiducia) { f.Esplicito = filepath.Join(d, "non-c-e.json") })
	prova("a mano, illeggibile", "RX-TRUST-004", func(f *FontiFiducia) { f.Esplicito = scrivi("rotto.json", []byte("{")) })
	prova("formato sconosciuto", "RX-TRUST-004", func(f *FontiFiducia) {
		f.Incorporato = []byte(strings.Replace(string(catalogo.Incorporato), "remotix-catalogo/1", "remotix-catalogo/9", 1))
	})
	prova("motore troppo vecchio", "RX-TRUST-003", func(f *FontiFiducia) { f.Incorporato = catalogoCon(t, "7", "99.0.0") })
}

// L'operazione: una fiducia che non si verifica è BLOCCATA prima di toccare niente.
func TestFiduciaBloccata(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	m.Fonti.Incorporato = catalogoCon(t, "7", "99.0.0")
	if op, err := m.Applica(b.piano, false, "prova"); CodiceDi(err) != "RX-TRUST-003" || op.Stato != BLOCCATA {
		t.Fatalf("motore troppo vecchio: %v %v", op.Stato, err)
	}
}

// Le versioni dei pacchetti, con gli algoritmi dei gestori.
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
			t.Errorf("%s %s ⋚ %s = %d, atteso %d", c.fam, c.a, c.b, r, c.r)
		}
	}
}
