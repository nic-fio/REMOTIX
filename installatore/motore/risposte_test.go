package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func fileRisposte(t *testing.T, testo string) string {
	p := filepath.Join(t.TempDir(), "risposte.conf")
	if err := os.WriteFile(p, []byte(testo), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

// Il file di risposte: formato, voci conosciute, valori ammessi. Un errore di battitura in un
// consenso non passa mai in silenzio.
func TestLeggiRisposte(t *testing.T) {
	buono := "# prova\nformato = remotix-risposte/1\nlingua = it\nporta = 7500\nconsenso.cinture = sì\nconsenso.firewall = NO # commento\n"
	r, err := LeggiRisposte(fileRisposte(t, buono))
	if err != nil {
		t.Fatal(err)
	}
	if r.Voci["consenso.cinture"] != "si" || r.Voci["consenso.firewall"] != "no" || r.Porta() != 7500 || len(r.Sha256) != 64 {
		t.Errorf("voci: %+v", r.Voci)
	}
	for testo, codice := range map[string]string{
		"porta = 7447\n": "RX-RISPOSTE-002", // senza formato
		"formato = remotix-risposte/1\nconsenso.firewal = si\n":    "RX-RISPOSTE-002", // voce sconosciuta
		"formato = remotix-risposte/1\nconsenso.cinture = forse\n": "RX-RISPOSTE-003",
		"formato = remotix-risposte/1\nporta = 99999\n":            "RX-RISPOSTE-003",
		"formato = remotix-risposte/1\ndesktop = cinnamon\n":       "RX-RISPOSTE-003",
		"formato = remotix-risposte/1\nlingua = de\n":              "RX-RISPOSTE-003",
		"formato = remotix-risposte/1\nporta = 1\nporta = 2\n":     "RX-RISPOSTE-002", // due volte
		"formato = remotix-risposte/1\nsolo una parola\n":          "RX-RISPOSTE-002",
	} {
		if _, err := LeggiRisposte(fileRisposte(t, testo)); CodiceDi(err) != codice {
			t.Errorf("%q: %v, atteso %s", testo, err, codice)
		}
	}
}

// I consensi che servono dipendono dalla macchina: il firewall solo con firewalld acceso, l'archivio
// di terzi solo dove H.264 lo chiede, gli aggiornamenti solo dall'archivio; le cinture sempre.
func TestConsensiNecessari(t *testing.T) {
	cat := catalogoProva(t)
	amb := ambienteFinto(t.TempDir()) // firewalld
	deb := profiloFinto()
	fed := profiloDi("fedora", "44", nil)
	fed.Verificato("h264.scheda", "no", "finto")
	casi := []struct {
		nome     string
		prof     *Profilo
		archivio string
		testo    string
		mancanti string
		superflu string
	}{
		// D4 (DECISIONI §4.7): le cinture non si chiedono; «consenso.cinture» di un file vecchio si
		// annota fra le superflue e non conta, nemmeno «no»
		{"debian, niente", deb, "", "", "consenso.firewall", ""},
		{"debian, archivio", deb, "http://a", "", "consenso.firewall,consenso.aggiornamenti", ""},
		{"debian, tutto", deb, "http://a", "consenso.cinture = no\nconsenso.firewall = si\nconsenso.aggiornamenti = no\nconsenso.deposito.rpmfusion = si\n", "", "consenso.cinture,consenso.deposito.rpmfusion"},
		{"fedora senza RPM Fusion", fed, "", "consenso.cinture = si\nconsenso.firewall = si\n", "consenso.deposito.rpmfusion", "consenso.cinture"},
	}
	for _, c := range casi {
		r, err := LeggiRisposte(fileRisposte(t, "formato = remotix-risposte/1\n"+c.testo))
		if err != nil {
			t.Fatal(err)
		}
		rap := Valuta(cat, c.prof)
		o, rif, _, err := r.OpzioniDaRisposte(rap, c.prof, amb, OpzioniInstallazione{Archivio: c.archivio})
		if err != nil {
			t.Fatal(c.nome, err)
		}
		if got := strings.Join(rif.Mancanti, ","); got != c.mancanti {
			t.Errorf("%s: mancanti %q, attesi %q", c.nome, got, c.mancanti)
		}
		var sup []string
		for _, x := range rif.Superflue {
			x, _, _ = strings.Cut(x, " (")
			sup = append(sup, x)
		}
		if got := strings.Join(sup, ","); got != c.superflu {
			t.Errorf("%s: superflue %q, attese %q", c.nome, got, c.superflu)
		}
		// un consenso che manca vale «no», mai «sì»
		for _, k := range rif.Mancanti {
			si := map[string]bool{"consenso.firewall": o.ApriFirewall,
				"consenso.aggiornamenti": !o.SenzaTimer, "consenso.deposito.rpmfusion": strings.Contains(strings.Join(o.Depositi, ","), "rpmfusion")}
			if si[k] {
				t.Errorf("%s: il consenso mancante %s è diventato sì: %+v", c.nome, k, o)
			}
		}
	}
}

// Un deposito di terzi c'è solo se una sua sezione è ACCESA: i nonfree spenti che Fedora Workstation
// porta non fanno «RPM Fusion presente» (`[M]` 30 set, fedora44-gnome: niente consenso chiesto, e
// REMOTIX senza codifica).
func TestDepositiAccesi(t *testing.T) {
	steam := "[rpmfusion-nonfree-steam]\nname=steam\nbaseurl=https://x\nenabled=0\n\n[rpmfusion-nonfree-nvidia-driver]\nenabled=0\n"
	for _, c := range []struct {
		file   map[string]string
		atteso string
	}{
		{map[string]string{"etc/yum.repos.d/steam.repo": steam}, "assente"},
		{map[string]string{"etc/yum.repos.d/steam.repo": steam, "etc/yum.repos.d/rpmfusion-free.repo": "[rpmfusion-free]\nmetalink=x\nenabled=1\n[rpmfusion-free-debuginfo]\nenabled=0\n"}, "presente"},
		{map[string]string{"etc/yum.repos.d/rpmfusion-free.repo": "[rpmfusion-free]\nmetalink=x\n"}, "presente"}, // enabled che manca = acceso
		{map[string]string{"etc/yum.repos.d/rpmfusion-free.repo": "[rpmfusion-free]\nmetalink=x\nenabled = 0\n"}, "assente"},
	} {
		p := NuovoProfilo(7447)
		depositi(&Ambiente{Radice: radiceFinta(t, c.file, nil)}, p)
		if p.V("deposito.rpmfusion") != c.atteso {
			f, _ := p.F("deposito.rpmfusion")
			t.Errorf("%v: %+v, atteso %s", c.file, f, c.atteso)
		}
	}
}

// Senza domande non vuol dire senza consenso: un piano che viene da un file di risposte a cui manca
// un consenso è BLOCCATO (RX-RISPOSTE-001) e la macchina non si tocca; con tutti i consensi il
// piano approvato dal file si applica.
func TestRisposteBloccate(t *testing.T) {
	for _, mancanti := range [][]string{{"consenso.firewall"}, nil} {
		b := nuovoBanco(t)
		m := b.motore(t)
		var p Piano
		LeggiJSON(b.piano, &p)
		p.Risposte = &RifRisposte{Formato: FormatoRisposte, File: "/root/risposte.conf", Sha256: strings.Repeat("a", 64),
			Voci: map[string]string{"formato": FormatoRisposte}, Mancanti: mancanti}
		p.Approvazione = &Approvazione{Da: "file di risposte", Modo: "senza domande", DigestPiano: p.Digest()}
		ScriviJSON(b.piano, &p)
		op, err := m.Applica(b.piano, false, "prova")
		if mancanti != nil {
			if op.Stato != BLOCCATA || !strings.Contains(ultimoStato(op), "RX-RISPOSTE-001") {
				t.Errorf("consenso mancante: %s %v %q", op.Stato, err, ultimoStato(op))
			}
			if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Errorf("toccata: %v", d)
			}
		} else if op.Stato != CONFERMATA {
			t.Errorf("tutti i consensi: %s %v", op.Stato, err)
		}
	}
}
