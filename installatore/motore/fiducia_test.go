package motore

import (
	"crypto/ed25519"
	"crypto/sha256"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"remotix/installatore/catalogo"
	"remotix/installatore/chiavi"
)

// La catena A nelle prove: una radice e due sottochiavi fatte al volo (deterministiche), il catalogo
// incorporato rifirmato con loro. Il catalogo e le revoche VERI del motore si provano a parte, con la
// radice incorporata (TestCatalogoIncorporatoFirmato).

type catenaProva struct {
	radice      ed25519.PrivateKey
	sub, sub2   ed25519.PrivateKey
	cert, cert2 *Sottochiave
}

func chiaveDa(seme string) ed25519.PrivateKey {
	s := sha256.Sum256([]byte(seme))
	return ed25519.NewKeyFromSeed(s[:])
}

func nuovaCatena() *catenaProva {
	b := &catenaProva{radice: chiaveDa("radice di prova"), sub: chiaveDa("sottochiave 1"), sub2: chiaveDa("sottochiave 2")}
	b.cert = CertificaSottochiave(b.radice, "P-1", b.sub.Public().(ed25519.PublicKey), "2026-01-01", "2027-06-30")
	b.cert2 = CertificaSottochiave(b.radice, "P-2", b.sub2.Public().(ed25519.PublicKey), "2026-01-01", "2027-12-31")
	return b
}

func (b *catenaProva) radici() []ed25519.PublicKey {
	return []ed25519.PublicKey{b.radice.Public().(ed25519.PublicKey)}
}

// fontiProva: il catalogo incorporato firmato dalla catena di prova; memoria in una cartella (o "").
func fontiProva(t testing.TB, memoria string) *FontiFiducia {
	b := nuovaCatena()
	rev := []byte(`{"formato":"remotix-revoche/1","catena":"A","sequenza":1,"emesso":"2026-09-30","revocate":[]}`)
	return &FontiFiducia{Radici: b.radici(), Incorporato: catalogo.Incorporato,
		FirmaIncorporata:   Firma(b.sub, b.cert, "catalogo", catalogo.Incorporato, "2026-09-30"),
		RevocheIncorporate: rev, FirmaRevoche: Firma(b.radice, nil, "revoche", rev, "2026-09-30"),
		Memoria: memoria, Motore: "/non/esiste/motore"}
}

// un catalogo con sequenza e scadenza cambiate (il testo resta un catalogo valido)
func catalogoCon(t testing.TB, seq, scad, minimo string) []byte {
	s := string(catalogo.Incorporato)
	c, _ := LeggiCatalogo(catalogo.Incorporato)
	s = strings.Replace(s, `"sequenza": `+strconv.Itoa(c.Sequenza)+`,`, `"sequenza": `+seq+`,`, 1)
	if scad != "" {
		s = strings.Replace(s, `"scadenza": "`+c.Scadenza+`"`, `"scadenza": "`+scad+`"`, 1)
	}
	if minimo != "" {
		s = strings.Replace(s, `"motore_minimo": "`+c.MotoreMinimo+`"`, `"motore_minimo": "`+minimo+`"`, 1)
	}
	return []byte(s)
}

var oggi = time.Date(2026, 9, 30, 12, 0, 0, 0, time.UTC)

// il catalogo e le revoche DEL MOTORE si verificano con la radice DEL MOTORE (chiavi di prova di T8):
// chi cambia catalogo.json senza rifirmarlo lo scopre qui.
func TestCatalogoIncorporatoFirmato(t *testing.T) {
	radici, err := LeggiRadici(chiavi.RadiceA)
	if err != nil {
		t.Fatal(err)
	}
	f := &FontiFiducia{Radici: radici, Incorporato: catalogo.Incorporato, FirmaIncorporata: catalogo.Firma,
		RevocheIncorporate: chiavi.Revoche, FirmaRevoche: chiavi.FirmaRevoche, Motore: "/non/esiste"}
	cat, fid, err := f.Fidati(time.Now())
	if err != nil {
		t.Fatalf("il catalogo incorporato non si verifica: %v (%s)", err, jsonCompatto(fid.Guardati))
	}
	if !fid.FirmaVerificata || fid.Fonte != "incorporato" || cat.Provenienza != "incorporato" {
		t.Errorf("fiducia: %+v", fid)
	}
	if chiavi.ImprontaArchivio() == "" || !strings.Contains(chiavi.Archivio, "BEGIN PGP PUBLIC KEY BLOCK") {
		t.Errorf("la chiave della catena B incorporata non c'è")
	}
}

func codice(err error) string { return CodiceDi(err) }

// TRUST: ogni modo di non fidarsi ha il suo codice, e niente passa.
func TestFiducia(t *testing.T) {
	b := nuovaCatena()
	dir := t.TempDir()

	// incorporato valido
	f := fontiProva(t, "")
	cat, fid, err := f.Fidati(oggi)
	if err != nil || !fid.FirmaVerificata || cat == nil || fid.Sottochiave != "P-1" {
		t.Fatalf("incorporato: %v %+v", err, fid)
	}
	if fid.FirmaMotore != "assente" {
		t.Errorf("firma del motore: %q", fid.FirmaMotore)
	}

	prova := func(nome, atteso string, cambia func(f *FontiFiducia)) {
		t.Helper()
		f := fontiProva(t, "")
		cambia(f)
		_, fid, err := f.Fidati(oggi)
		if codice(err) != atteso {
			t.Errorf("%s: atteso %s, avuto %v (%s)", nome, atteso, err, jsonCompatto(fid.Guardati))
		}
	}
	prova("firma assente", "RX-TRUST-006", func(f *FontiFiducia) { f.FirmaIncorporata = nil })
	prova("un byte alterato", "RX-TRUST-007", func(f *FontiFiducia) {
		d := append([]byte{}, f.Incorporato...)
		d[len(d)/2] ^= 1
		f.Incorporato = d
	})
	prova("firmato da una radice sconosciuta", "RX-TRUST-008", func(f *FontiFiducia) {
		altra := chiaveDa("un'altra radice")
		c := CertificaSottochiave(altra, "X-1", b.sub.Public().(ed25519.PublicKey), "2026-01-01", "2027-01-01")
		f.FirmaIncorporata = Firma(b.sub, c, "catalogo", f.Incorporato, "2026-09-30")
	})
	prova("firma del motore usata per un catalogo", "RX-TRUST-007", func(f *FontiFiducia) {
		f.FirmaIncorporata = Firma(b.sub, b.cert, "motore", f.Incorporato, "2026-09-30")
	})
	prova("sottochiave scaduta", "RX-TRUST-009", func(f *FontiFiducia) {
		c := CertificaSottochiave(b.radice, "P-vecchia", b.sub.Public().(ed25519.PublicKey), "2025-01-01", "2025-12-31")
		f.FirmaIncorporata = Firma(b.sub, c, "catalogo", f.Incorporato, "2025-06-30")
	})
	prova("sottochiave revocata", "RX-TRUST-010", func(f *FontiFiducia) {
		rev := []byte(`{"formato":"remotix-revoche/1","catena":"A","sequenza":2,"emesso":"2026-09-30","revocate":[{"id":"P-1","motivo":"prova"}]}`)
		f.RevocheIncorporate, f.FirmaRevoche = rev, Firma(b.radice, nil, "revoche", rev, "2026-09-30")
	})
	prova("revoche firmate da una sottochiave", "RX-TRUST-012", func(f *FontiFiducia) {
		f.FirmaRevoche = Firma(b.sub, b.cert, "revoche", f.RevocheIncorporate, "2026-09-30")
	})
	prova("catalogo scaduto", "RX-TRUST-002", func(f *FontiFiducia) {
		d := catalogoCon(t, "9", "2026-01-01", "")
		f.Incorporato, f.FirmaIncorporata = d, Firma(b.sub, b.cert, "catalogo", d, "2026-09-30")
	})
	prova("motore troppo vecchio", "RX-TRUST-003", func(f *FontiFiducia) {
		d := catalogoCon(t, "9", "", "9.0.0")
		f.Incorporato, f.FirmaIncorporata = d, Firma(b.sub, b.cert, "catalogo", d, "2026-09-30")
	})

	// l'archivio: il più recente vince e si memorizza; uno alterato BLOCCA; uno irraggiungibile avvisa
	nuovo := catalogoCon(t, "50", "", "")
	web := map[string][]byte{}
	f = fontiProva(t, dir)
	f.Archivio, f.Canale, f.Scrivi = "http://archivio.prova", "stabile", true
	f.Scarica = func(u string) ([]byte, error) {
		if d, ok := web[u]; ok {
			return d, nil
		}
		return nil, errors.New("404")
	}
	uc, _ := URLCatalogo(f.Archivio, f.Canale)
	web[uc], web[uc+".firma"] = nuovo, Firma(b.sub2, b.cert2, "catalogo", nuovo, "2026-09-30")
	cat, fid, err = f.Fidati(oggi)
	if err != nil || cat.Sequenza != 50 || !strings.HasPrefix(fid.Fonte, "archivio") || fid.Sottochiave != "P-2" {
		t.Fatalf("archivio più recente: %v %+v", err, fid)
	}
	if _, err := os.Stat(filepath.Join(dir, "catalogo.json")); err != nil {
		t.Errorf("il catalogo nuovo non è stato memorizzato: %v", err)
	}
	// senza rete: resta il memorizzato (50), con l'avviso
	delete(web, uc)
	cat, fid, err = f.Fidati(oggi)
	if err != nil || cat.Sequenza != 50 || fid.Fonte != "memorizzato" || !haCodice(fid.Messaggi, "RX-TRUST-013") {
		t.Errorf("senza rete: %v %+v", err, fid)
	}
	// un catalogo più vecchio dall'archivio: si tiene il 50, con l'avviso
	vecchio := catalogoCon(t, "20", "", "")
	web[uc], web[uc+".firma"] = vecchio, Firma(b.sub2, b.cert2, "catalogo", vecchio, "2026-09-30")
	cat, fid, err = f.Fidati(oggi)
	if err != nil || cat.Sequenza != 50 || !haCodice(fid.Messaggi, "RX-TRUST-011") {
		t.Errorf("archivio vecchio: %v %+v", err, fid)
	}
	// alterato nell'archivio: BLOCCATA
	alt := append([]byte{}, nuovo...)
	alt[100] ^= 1
	web[uc], web[uc+".firma"] = alt, Firma(b.sub2, b.cert2, "catalogo", nuovo, "2026-09-30")
	if _, _, err = f.Fidati(oggi); codice(err) != "RX-TRUST-007" {
		t.Errorf("archivio alterato: %v", err)
	}
	// fuori linea, dato esplicitamente: è l'unico guardato; più vecchio del memorizzato (50) ⇒ BLOCCATA
	fl := filepath.Join(t.TempDir(), "catalogo.json")
	os.WriteFile(fl, vecchio, 0o644)
	os.WriteFile(fl+".firma", Firma(b.sub, b.cert, "catalogo", vecchio, "2026-09-30"), 0o644)
	g := fontiProva(t, dir)
	g.Esplicito = fl
	if _, _, err := g.Fidati(oggi); codice(err) != "RX-TRUST-016" {
		t.Errorf("fuori linea più vecchio: %v", err)
	}

	// revocata dall'archivio la sottochiave P-2 del catalogo memorizzato (50) e nessun catalogo nuovo:
	// il memorizzato si scarta, resta quello del motore (P-1), che prende il suo posto
	_, ur := URLCatalogo(f.Archivio, f.Canale)
	rev := []byte(`{"formato":"remotix-revoche/1","catena":"A","sequenza":3,"emesso":"2026-09-30","revocate":[{"id":"P-2","motivo":"chiave persa (prova)"}]}`)
	web[ur], web[ur+".firma"] = rev, Firma(b.radice, nil, "revoche", rev, "2026-09-30")
	delete(web, uc)
	if cat, fid, err := f.Fidati(oggi); err != nil || fid.Fonte != "incorporato" || cat.Sequenza == 50 {
		t.Errorf("revocata dall'archivio: %v %+v", err, fid)
	}
	g = fontiProva(t, "")
	g.Esplicito = fl
	if cat, fid, err := g.Fidati(oggi); err != nil || cat.Sequenza != 20 || !strings.HasPrefix(fid.Fonte, "fuori linea") {
		t.Errorf("fuori linea: %v %+v", err, fid)
	}
	os.Remove(fl + ".firma")
	if _, _, err := g.Fidati(oggi); codice(err) != "RX-TRUST-006" {
		t.Errorf("fuori linea senza firma: %v", err)
	}
}

// La rotazione dopo una revoca: il catalogo del motore (P-1) è revocato dall'archivio, ma l'archivio
// ne ha uno nuovo firmato con P-2 ⇒ si procede con quello; senza, BLOCCATA col codice della revoca.
func TestRotazione(t *testing.T) {
	b := nuovaCatena()
	f := fontiProva(t, t.TempDir())
	f.Archivio, f.Canale, f.Scrivi = "http://archivio.prova", "stabile", true
	web := map[string][]byte{}
	f.Scarica = func(u string) ([]byte, error) {
		if d, ok := web[u]; ok {
			return d, nil
		}
		return nil, errors.New("404")
	}
	uc, ur := URLCatalogo(f.Archivio, f.Canale)
	rev := []byte(`{"formato":"remotix-revoche/1","catena":"A","sequenza":2,"emesso":"2026-09-30","revocate":[{"id":"P-1","motivo":"rotazione"}]}`)
	web[ur], web[ur+".firma"] = rev, Firma(b.radice, nil, "revoche", rev, "2026-09-30")
	if _, _, err := f.Fidati(oggi); codice(err) != "RX-TRUST-010" {
		t.Fatalf("revocato senza sostituto: %v", err)
	}
	nuovo := catalogoCon(t, "60", "", "")
	web[uc], web[uc+".firma"] = nuovo, Firma(b.sub2, b.cert2, "catalogo", nuovo, "2026-09-30")
	cat, fid, err := f.Fidati(oggi)
	if err != nil || cat.Sequenza != 60 || fid.Sottochiave != "P-2" || fid.Revoche != 2 {
		t.Fatalf("rotazione: %v %+v", err, fid)
	}
	// e le revoche nuove si ricordano: senza rete il catalogo del motore resta scartato
	delete(web, uc)
	delete(web, ur)
	if cat, fid, err := f.Fidati(oggi); err != nil || cat.Sequenza != 60 || fid.Revoche != 2 {
		t.Fatalf("dopo la rotazione, senza rete: %v %+v", err, fid)
	}
}

func haCodice(m []Messaggio, c string) bool {
	for _, x := range m {
		if x.Codice == c {
			return true
		}
	}
	return false
}

// L'operazione: una fiducia che non si verifica è BLOCCATA prima di toccare niente.
func TestFiduciaBloccata(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	m.Fonti.FirmaIncorporata = nil
	if op, err := m.Applica(b.piano, false, "prova"); CodiceDi(err) != "RX-TRUST-006" || op.Stato != BLOCCATA {
		t.Fatalf("senza firma: %v %v", op.Stato, err)
	}
}

// Le versioni dei pacchetti, con gli algoritmi dei gestori; e la regola annuale/manutenzione (D14).
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
	if Annuale("0.17.0-1+deb13", "0.17.0-2+deb13") || Annuale("0.17.0-1.fc44", "0.17.3-1.fc44") || !Annuale("0.17.0-5", "0.18.0-1") {
		t.Errorf("regola annuale/manutenzione sbagliata")
	}
}
