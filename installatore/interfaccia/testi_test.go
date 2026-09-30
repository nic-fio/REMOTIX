package interfaccia

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"remotix/installatore/motore"
)

// Ogni chiave usata dalle schermate (vista, TUI, GUI) c'è, nelle due lingue (DECISIONI §10.15, R42).
func TestTestiInterfaccia(t *testing.T) {
	re := regexp.MustCompile(`\bT\("([a-z0-9_.]+)"`)
	var file []string
	for _, g := range []string{"*.go", "tui/*.go", "gui/*.go"} {
		m, _ := filepath.Glob(g)
		file = append(file, m...)
	}
	usate := 0
	for _, f := range file {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		for _, m := range re.FindAllStringSubmatch(string(b), -1) {
			k := m[1]
			if strings.HasPrefix(k, "comp.") || strings.HasPrefix(k, "cli.") || strings.HasSuffix(k, ".") { // del motore, o composta
				continue
			}
			usate++
			x, ok := testi[k]
			if !ok {
				t.Errorf("%s: la chiave %q manca", f, k)
				continue
			}
			if x.it == "" || x.en == "" {
				t.Errorf("%q: manca una lingua: %+v", k, x)
			}
		}
	}
	if usate < 50 {
		t.Errorf("trovate solo %d chiavi: l'espressione non le vede?", usate)
	}
	for k, x := range testi {
		if strings.Count(x.it, "%") != strings.Count(x.en, "%") {
			t.Errorf("%q: argomenti diversi fra le lingue: %q / %q", k, x.it, x.en)
		}
	}
}

// Il controllo in parole comuni: niente nomi di driver o bus fuori dai dettagli tecnici; i
// cartellini nelle due lingue.
func TestVistaControlloParoleComuni(t *testing.T) {
	prof := motore.NuovoProfilo(7447)
	for k, v := range map[string]string{"distro.id": "fedora", "distro.versione": "44", "distro.nome": "Fedora Linux 44 (Workstation Edition)",
		"distro.variante": "workstation", "scheda.nodi": "renderD128", "scheda.renderD128.fornitore": "virtio",
		"scheda.renderD128.driver": "virtio-pci", "selinux": "enforcing"} {
		prof.Rilevato(k, v, "prova")
	}
	rap := &motore.Rapporto{Riconosciuta: motore.T("comp.nella_matrice", "Fedora 44"),
		Desktop: []motore.EsitoDesktop{{Desktop: "gnome", Installato: "50.5", Livello: motore.COMPATIBILE}}}
	dom := &motore.Domande{Porta: 7447, Firewall: "chiuso", Depositi: []motore.DomandaDeposito{{ID: "rpmfusion", Nome: "RPM Fusion", Per: "h264", Serve: true}}}
	for _, l := range []string{"it", "en"} {
		motore.ImpostaLingua(l)
		v := VistaDelControllo(&Controllo{Profilo: prof, Rapporto: rap, Domande: dom})
		if v.Esito != CONDIZIONI {
			t.Errorf("%s: esito %v, atteso a condizioni", l, v.Esito)
		}
		for _, r := range v.Righe {
			if strings.Contains(r.Testo, "virtio") || strings.Contains(r.Testo, "renderD") || strings.Contains(r.Testo, "RX-") {
				t.Errorf("%s: parola tecnica fuori dai dettagli: %q", l, r.Testo)
			}
		}
		if !strings.Contains(v.Dettagli, "virtio-pci") {
			t.Errorf("%s: il driver non è nei dettagli: %q", l, v.Dettagli)
		}
		if v.Intestazione != "Fedora Linux 44 · Workstation · GNOME 50" {
			t.Errorf("%s: intestazione %q", l, v.Intestazione)
		}
	}
	motore.ImpostaLingua("it")
	s := VistaDelleScelte(&Controllo{Profilo: prof, Rapporto: rap, Domande: dom})
	if s.Titolo != "Tre cose da decidere" || len(s.Domande) != 2 {
		t.Errorf("scelte: %q, %d domande", s.Titolo, len(s.Domande))
	}
}
