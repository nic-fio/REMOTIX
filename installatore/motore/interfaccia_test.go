package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// pacchettoUnico: the packages/ folder of a fake .run, with the REMOTIX package for the Debian 13
// of the fake machine (the fake manager reads the JSON: it depends on libnuova and libcomune).
func pacchettoUnico(t *testing.T, radice string) string {
	d := filepath.Join(radice, "run/packages/debian13")
	os.MkdirAll(d, 0o755)
	if err := os.WriteFile(filepath.Join(d, "remotix_0.17.0-1_amd64.deb"),
		[]byte(`{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`), 0o644); err != nil {
		t.Fatal(err)
	}
	return "/run/packages"
}

// DECISIONI §10.36: the plan does not modify the system — no repositories, firewalls, belts or desktops;
// the exact packages from the manager's simulation, before the question; the card's groups
// declared; the running firewall is stated, not opened.
func TestPianoNonModificaIlSistema(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	amb := ambienteFinto(radice)
	prof := profiloFinto()
	cat := catalogoProva(t)
	rap := Valuta(cat, prof)
	p, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Pacchetti: pacchettoUnico(t, radice), Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	if Bloccato(p) {
		t.Fatalf("plan blocked: %+v", p.NonFatto)
	}
	for _, a := range p.Azioni {
		switch a.Tipo {
		case "install-packages", "add-user-to-group", "write-file", "start-service":
		default:
			t.Errorf("the plan modifies the system with %s (%s)", a.ID, a.Tipo)
		}
	}
	esiti := map[string]string{}
	for _, x := range p.Pacchetti {
		esiti[x.Nome] = x.Esito
	}
	if esiti["remotix"] != "new" || esiti["libnuova"] != "new" || esiti["libcomune"] != "upgraded" {
		t.Errorf("the manager's simulation: %+v", p.Pacchetti)
	}
	fw := false
	for _, m := range p.NonFatto {
		fw = fw || (m.Gravita == AVVISO && strings.Contains(m.Testo, "firewalld"))
	}
	if !fw {
		t.Errorf("the running firewall must be stated: %+v", p.NonFatto)
	}
	// without the .run: the package is missing, and the plan stops
	q, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Porta: 7447})
	if err != nil || !Bloccato(q) || !haCodice(q.NonFatto, "RX-MANCA-004") {
		t.Errorf("without packages: %v %+v", err, q)
	}
}

// What is missing is stated and stops everything (DECISIONI §10.36): without a desktop RX-MANCA-001, on Alma without
// EPEL RX-MANCA-002 — without packages or commands suggested. labwc, wlr-randr and the font on the other hand
// are not missing: they are REMOTIX dependencies, in the plan (the user, 10 Oct). And a BLOCKING plan
// applied leads to BLOCCATA without touching anything.
func TestMancaFermaTutto(t *testing.T) {
	cat := catalogoProva(t)
	casi := []struct {
		id, ver string
		extra   map[string]string
		codice  string
	}{
		{"debian", "13", map[string]string{"desktop.gnome": "absent"}, "RX-MANCA-001"},
		{"almalinux", "10.1", map[string]string{"repo.epel": "absent"}, "RX-MANCA-002"},
	}
	for _, c := range casi {
		rap := Valuta(cat, profiloDi(c.id, c.ver, c.extra))
		if !haCodice(rap.Mancano, c.codice) {
			t.Errorf("%s %v: missing %s, the report says %+v", c.id, c.extra, c.codice, rap.Mancano)
		}
		for _, m := range rap.Mancano {
			for _, x := range []string{"sudo", "dnf ", "apt ", "zypper", "pacman"} {
				if strings.Contains(m.Testo+m.Dettaglio+m.Rimedio, x) {
					t.Errorf("%s: the message suggests a command (%q): %+v", c.codice, x, m)
				}
			}
		}
	}

	// XFCE without labwc, wlr-randr and fonts: no «missing», three dependencies with the desktop requiring them
	rap := Valuta(cat, profiloDi("debian", "13", map[string]string{"desktop.gnome": "absent", "desktop.xfce": "4.20.1",
		"package.labwc": "absent", "package.wlr-randr": "absent", "fonts.scalable": "0", "distro.family": "debian"}))
	if len(rap.Mancano) > 0 {
		t.Errorf("XFCE without labwc: missing %+v", rap.Mancano)
	}
	if got := strings.Join(rap.NomiDipendenze(), ","); got != "labwc,wlr-randr,fonts-dejavu-core" || rap.Dipendenze[0].Perche != "XFCE" {
		t.Errorf("XFCE without labwc: dependencies %+v", rap.Dipendenze)
	}

	b := nuovoBanco(t)
	m := b.motore(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.NonFatto = append(p.NonFatto, Msg("RX-MANCA-003", "XFCE: labwc"))
	p.Approvazione = &Approvazione{Da: "prova", Modo: "a mano", DigestPiano: p.Digest()}
	ScriviJSON(b.piano, &p)
	op, err := m.Applica(b.piano, false, "prova")
	if op == nil || op.Stato != BLOCCATA || !strings.Contains(ultimoStato(op), "RX-MANCA-003") {
		t.Errorf("missing: %v %v", op, err)
	}
	if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Errorf("missing: the machine was touched: %v", d)
	}
}

// Stopping halfway (the «Cancel and put back as it was» button): between one step and the next, then everything is
// undone from the log (RX-AZIONE-006) and the machine goes back to how it was.
func TestFermataDaChiInstalla(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	n := 0
	m.Fermata = func() bool { n++; return n > 2 } // after two steps
	op, err := m.Applica(b.piano, true, "prova")
	if op == nil || op.Stato != ANNULLATA {
		t.Fatalf("fermata: %v %v", op, err)
	}
	if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Errorf("stopped: the machine did not go back to how it was: %v", d)
	}
	if err := op.apriRegistro(); err != nil {
		t.Fatal(err)
	}
	visto := false
	for _, e := range op.Reg.Eventi {
		visto = visto || (e.Tipo == EvStato && e.A == IN_ANNULLAMENTO && e.Codice == "RX-AZIONE-006")
	}
	if !visto {
		t.Errorf("stopped: ROLLING_BACK with RX-AZIONE-006 is not in the log")
	}
}

// The chosen port ends up in the plan: a file in /etc/remotix/remotix.conf.d (remotix.service
// reads it), BEFORE the switch-on; with the stock one no file (`[M]` 30 Sep, leap16-kde in a
// box: the service started on 7447 and the engine verified it on 8532).
func TestPianoPortaScelta(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	bundle := pacchettoUnico(t, radice)
	amb := ambienteFinto(radice)
	prof := profiloFinto()
	cat := catalogoProva(t)
	rap := Valuta(cat, prof)
	for _, porta := range []int{7447, 8531} {
		p, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Pacchetti: bundle, Porta: porta})
		if err != nil {
			t.Fatal(err)
		}
		file, servizio := -1, -1
		for i, a := range p.Azioni {
			switch {
			case a.ID == "port" && a.Tipo == "write-file":
				file = i
				if a.Parametri["path"] != "/etc/remotix/remotix.conf.d/porta.conf" || a.Parametri["content"] != "REMOTIX_PORTA=8531\n" {
					t.Errorf("port %d: the file is %v", porta, a.Parametri)
				}
			case a.Tipo == "start-service":
				servizio = i
			}
		}
		switch {
		case porta == 7447 && file != -1:
			t.Errorf("stock port: no file in /etc, but there is one")
		case porta != 7447 && file == -1:
			t.Errorf("port %d: the file in /etc/remotix/remotix.conf.d is missing", porta)
		case file != -1 && file > servizio:
			t.Errorf("port %d: the file must be written BEFORE the switch-on (%d > %d)", porta, file, servizio)
		}
	}
}
