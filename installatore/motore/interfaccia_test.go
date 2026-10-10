package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// pacchettoUnico: la cartella packages/ di un .run finto, col pacchetto di REMOTIX per la Debian 13
// della macchina finta (il gestore finto legge il JSON: dipende da libnuova e libcomune).
func pacchettoUnico(t *testing.T, radice string) string {
	d := filepath.Join(radice, "run/packages/debian13")
	os.MkdirAll(d, 0o755)
	if err := os.WriteFile(filepath.Join(d, "remotix_0.17.0-1_amd64.deb"),
		[]byte(`{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`), 0o644); err != nil {
		t.Fatal(err)
	}
	return "/run/packages"
}

// DECISIONI §10.36: il piano non modifica il sistema — niente archivi, firewall, cinture né desktop;
// i pacchetti esatti dalla simulazione del gestore, prima della domanda; i gruppi della scheda
// dichiarati; il firewall acceso si dice, non si apre.
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
		t.Fatalf("piano bloccato: %+v", p.NonFatto)
	}
	for _, a := range p.Azioni {
		switch a.Tipo {
		case "install-packages", "add-user-to-group", "write-file", "start-service":
		default:
			t.Errorf("il piano modifica il sistema con %s (%s)", a.ID, a.Tipo)
		}
	}
	esiti := map[string]string{}
	for _, x := range p.Pacchetti {
		esiti[x.Nome] = x.Esito
	}
	if esiti["remotix"] != "new" || esiti["libnuova"] != "new" || esiti["libcomune"] != "upgraded" {
		t.Errorf("la simulazione del gestore: %+v", p.Pacchetti)
	}
	fw := false
	for _, m := range p.NonFatto {
		fw = fw || (m.Gravita == AVVISO && strings.Contains(m.Testo, "firewalld"))
	}
	if !fw {
		t.Errorf("il firewall acceso va detto: %+v", p.NonFatto)
	}
	// senza il .run: manca il pacchetto, e il piano si ferma
	q, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Porta: 7447})
	if err != nil || !Bloccato(q) || !haCodice(q.NonFatto, "RX-MANCA-004") {
		t.Errorf("senza pacchetti: %v %+v", err, q)
	}
}

// Quel che manca si dice e ferma tutto (DECISIONI §10.36): senza desktop RX-MANCA-001, a XFCE senza
// labwc RX-MANCA-003, su Alma senza EPEL RX-MANCA-002 — senza pacchetti né comandi suggeriti. E un
// piano BLOCCANTE applicato porta a BLOCCATA senza toccare niente.
func TestMancaFermaTutto(t *testing.T) {
	cat := catalogoProva(t)
	casi := []struct {
		id, ver string
		extra   map[string]string
		codice  string
	}{
		{"debian", "13", map[string]string{"desktop.gnome": "absent"}, "RX-MANCA-001"},
		{"debian", "13", map[string]string{"desktop.gnome": "absent", "desktop.xfce": "4.20.1", "package.labwc": "absent"}, "RX-MANCA-003"},
		{"almalinux", "10.1", map[string]string{"repo.epel": "absent"}, "RX-MANCA-002"},
	}
	for _, c := range casi {
		rap := Valuta(cat, profiloDi(c.id, c.ver, c.extra))
		if !haCodice(rap.Mancano, c.codice) {
			t.Errorf("%s %v: manca %s, il rapporto dice %+v", c.id, c.extra, c.codice, rap.Mancano)
		}
		for _, m := range rap.Mancano {
			for _, x := range []string{"sudo", "dnf ", "apt ", "zypper", "pacman"} {
				if strings.Contains(m.Testo+m.Dettaglio+m.Rimedio, x) {
					t.Errorf("%s: il messaggio suggerisce un comando (%q): %+v", c.codice, x, m)
				}
			}
		}
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
		t.Errorf("manca: %v %v", op, err)
	}
	if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Errorf("manca: la macchina è stata toccata: %v", d)
	}
}

// Fermarsi a metà (il pulsante «Annulla e rimetti com'era»): fra un passo e l'altro, poi tutto si
// annulla dal registro (RX-AZIONE-006) e la macchina torna com'era.
func TestFermataDaChiInstalla(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	n := 0
	m.Fermata = func() bool { n++; return n > 2 } // dopo due passi
	op, err := m.Applica(b.piano, true, "prova")
	if op == nil || op.Stato != ANNULLATA {
		t.Fatalf("fermata: %v %v", op, err)
	}
	if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Errorf("fermata: la macchina non è tornata com'era: %v", d)
	}
	if err := op.apriRegistro(); err != nil {
		t.Fatal(err)
	}
	visto := false
	for _, e := range op.Reg.Eventi {
		visto = visto || (e.Tipo == EvStato && e.A == IN_ANNULLAMENTO && e.Codice == "RX-AZIONE-006")
	}
	if !visto {
		t.Errorf("fermata: ROLLING_BACK con RX-AZIONE-006 non è nel registro")
	}
}

// La porta scelta finisce nel piano: un file in /etc/remotix/remotix.conf.d (remotix.service lo
// legge), PRIMA dell'accensione; con quella di serie nessun file (`[M]` 30 set, leap16-kde in
// scatola: il servizio partiva su 7447 e il motore lo verificava su 8532).
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
					t.Errorf("porta %d: il file è %v", porta, a.Parametri)
				}
			case a.Tipo == "start-service":
				servizio = i
			}
		}
		switch {
		case porta == 7447 && file != -1:
			t.Errorf("porta di serie: nessun file in /etc, invece c'è")
		case porta != 7447 && file == -1:
			t.Errorf("porta %d: manca il file in /etc/remotix/remotix.conf.d", porta)
		case file != -1 && file > servizio:
			t.Errorf("porta %d: il file va scritto PRIMA dell'accensione (%d > %d)", porta, file, servizio)
		}
	}
}
