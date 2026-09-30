package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// R36 in piccolo: la stessa installazione chiesta dalla CLI (le opzioni) e da TUI/GUI (le voci
// raccolte nelle schermate, PianoDaScelte) dà LO STESSO piano, a parte identificativo e ora.
// E D4 (DECISIONI §4.7): le tre cinture ci sono sempre, dichiarate, mai fra i consensi.
func TestPianoDaScelteComeLaCLI(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	if err := os.WriteFile(filepath.Join(radice, "remotix.deb"), []byte("pacchetto finto"), 0o644); err != nil {
		t.Fatal(err)
	}
	amb := ambienteFinto(radice)
	prof := profiloFinto()
	cat := catalogoProva(t)
	rap := Valuta(cat, prof)

	cli, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.deb", ApriFirewall: true, Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	dom := DomandeDaFare(prof, rap, cat, amb, 7447, false, "")
	if dom.Firewall != "chiuso" {
		t.Errorf("firewall: %q, atteso «chiuso» (firewalld finto, porta non aperta)", dom.Firewall)
	}
	voci := dom.VociDiserie()
	if _, c := voci["consenso.cinture"]; c {
		t.Errorf("D4: le voci di serie chiedono ancora le cinture: %v", voci)
	}
	gui, err := PianoDaScelte(voci, prof, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.deb", Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	norm := func(p *Piano) string {
		c := *p
		c.ID, c.Creato = "", ""
		return string(JSONCanonico(c))
	}
	if norm(cli) != norm(gui) {
		t.Errorf("il piano della CLI e quello delle schermate sono diversi:\nCLI %s\nGUI %s", norm(cli), norm(gui))
	}
	if gui.Risposte != nil || gui.Approvazione != nil {
		t.Errorf("il piano delle schermate non porta file di risposte né approvazione: %+v %+v", gui.Risposte, gui.Approvazione)
	}
	n := 0
	for _, a := range gui.Azioni {
		if a.Tipo == "attiva-cintura" {
			n++
			if a.Consenso != "" {
				t.Errorf("D4: la cintura %s ha ancora un consenso: %q", a.ID, a.Consenso)
			}
		}
	}
	if n != 3 {
		t.Errorf("D4: %d cinture nel piano, attese 3", n)
	}
	for _, c := range gui.Consensi {
		if strings.Contains(strings.ToLower(c), "cintur") || strings.Contains(strings.ToLower(c), "belt") {
			t.Errorf("D4: le cinture fra i consensi: %q", c)
		}
	}
	dich := false
	for _, x := range gui.Dichiarate {
		dich = dich || x == T("az.cintura.dichiarata")
	}
	if !dich {
		t.Errorf("D4: la riga dichiarata delle cinture manca: %+v", gui.Dichiarate)
	}

	// un consenso che serve e che le schermate non danno è un errore, mai un «no» tacito
	delete(voci, "consenso.firewall")
	if _, err := PianoDaScelte(voci, prof, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.deb", Porta: 7447}); CodiceDi(err) != "RX-RISPOSTE-001" {
		t.Errorf("consenso mancante: %v, atteso RX-RISPOSTE-001", err)
	}
	// una voce sconosciuta non passa
	if _, err := PianoDaScelte(map[string]string{"consenso.firewal": "si"}, prof, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.deb"}); CodiceDi(err) != "RX-RISPOSTE-002" {
		t.Errorf("voce sconosciuta: %v, atteso RX-RISPOSTE-002", err)
	}
}

// Il testo delle risposte è sempre lo stesso per le stesse voci (si può rifare senza domande).
func TestTestoRisposte(t *testing.T) {
	a := TestoRisposte(map[string]string{"porta": "7447", "consenso.firewall": "si", "formato": FormatoRisposte})
	b := TestoRisposte(map[string]string{"consenso.firewall": "si", "porta": "7447"})
	if a != b || !strings.HasPrefix(a, "formato = "+FormatoRisposte+"\n") {
		t.Errorf("%q\n%q", a, b)
	}
}

// D5 (DECISIONI §10.20): senza l'archivio per la codifica H.264 REMOTIX NON si installa. Il piano
// fatto col «no» lo scrive (RX-H264-006, BLOCCANTE); applicarlo porta a BLOCCATA senza toccare.
func TestSenzaArchivioVideoNonSiInstalla(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	os.WriteFile(filepath.Join(radice, "remotix.deb"), []byte("pacchetto finto"), 0o644)
	amb := ambienteFinto(radice)
	cat := catalogoProva(t)
	for _, si := range []bool{false, true} {
		// «si»: RPM Fusion c'è già, col ramo nonfree che la scheda Intel chiede (sulla macchina finta
		// non si può aggiungere un deposito vero); OpenH264 di Cisco c'è in tutti e due i casi
		extra := map[string]string{"deposito.openh264": "presente"}
		if si {
			extra["deposito.rpmfusion"] = "presente"
			extra["deposito.rpmfusion-nonfree"] = "presente"
		}
		fed := profiloDi("fedora", "44", extra)
		fed.Verificato("h264.scheda", "no", "finto")
		rap := Valuta(cat, fed)
		o := OpzioniInstallazione{Pacchetto: "/remotix.deb", Porta: 7447}
		p, err := PianoInstallazione(fed, rap, cat, amb, o)
		if err != nil {
			t.Fatal(err)
		}
		bl := false
		for _, m := range p.NonFatto {
			bl = bl || (m.Codice == "RX-H264-006" && m.Gravita == BLOCCANTE)
		}
		if bl == si {
			t.Errorf("consenso %v: RX-H264-006 nel piano = %v", si, bl)
		}
	}

	// applicato: BLOCCATA prima di toccare
	b := nuovoBanco(t)
	m := b.motore(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.NonFatto = append(p.NonFatto, Msg("RX-H264-006", "RPM Fusion"))
	p.Approvazione = &Approvazione{Da: "prova", Modo: "a mano", DigestPiano: p.Digest()}
	ScriviJSON(b.piano, &p)
	op, err := m.Applica(b.piano, false, "prova")
	if op == nil || op.Stato != BLOCCATA || !strings.Contains(ultimoStato(op), "RX-H264-006") {
		t.Errorf("D5: %v %v", op, err)
	}
	if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Errorf("D5: la macchina è stata toccata: %v", d)
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
		t.Errorf("fermata: IN_ANNULLAMENTO con RX-AZIONE-006 non è nel registro")
	}
}

// La porta scelta finisce nel piano: un file in /etc/remotix/remotix.conf.d (remotix.service lo
// legge), PRIMA dell'accensione; con quella di serie nessun file (`[M]` 30 set, leap16-kde in
// scatola: il servizio partiva su 7447 e il motore lo verificava su 8532).
func TestPianoPortaScelta(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	os.WriteFile(filepath.Join(radice, "remotix.deb"), []byte("pacchetto finto"), 0o644)
	amb := ambienteFinto(radice)
	prof := profiloFinto()
	cat := catalogoProva(t)
	rap := Valuta(cat, prof)
	for _, porta := range []int{7447, 8531} {
		p, err := PianoInstallazione(prof, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.deb", Porta: porta})
		if err != nil {
			t.Fatal(err)
		}
		file, servizio := -1, -1
		for i, a := range p.Azioni {
			switch {
			case a.ID == "porta" && a.Tipo == "scrivi-file":
				file = i
				if a.Parametri["percorso"] != "/etc/remotix/remotix.conf.d/porta.conf" || a.Parametri["contenuto"] != "REMOTIX_PORTA=8531\n" {
					t.Errorf("porta %d: il file è %v", porta, a.Parametri)
				}
			case a.Tipo == "accendi-servizio":
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
