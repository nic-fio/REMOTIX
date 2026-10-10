package interfaccia

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"remotix/installatore/motore"
)

// Every key used by the screens (view and TUI) is there, in both languages (DECISIONI §10.15, R42).
func TestTestiInterfaccia(t *testing.T) {
	re := regexp.MustCompile(`\bT\("([a-z0-9_.]+)"`)
	var file []string
	for _, g := range []string{"*.go", "tui/*.go"} {
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
			if strings.HasPrefix(k, "comp.") || strings.HasPrefix(k, "cli.") || strings.HasSuffix(k, ".") { // the engine's, or composed
				continue
			}
			usate++
			x, ok := testi[k]
			if !ok {
				t.Errorf("%s: the key %q is missing", f, k)
				continue
			}
			if x == "" {
				t.Errorf("%q: empty text", k)
			}
		}
	}
	if usate < 50 {
		t.Errorf("only %d keys found: does the expression not see them?", usate)
	}
}

// The check in plain words: no names of drivers or buses outside the technical details; the
// labels in English (DECISIONI §10.35).
func TestVistaControlloParoleComuni(t *testing.T) {
	prof := motore.NuovoProfilo(7447)
	for k, v := range map[string]string{"distro.id": "fedora", "distro.version": "44", "distro.name": "Fedora Linux 44 (Workstation Edition)",
		"distro.variant": "workstation", "gpu.nodes": "renderD128", "gpu.renderD128.vendor": "virtio",
		"gpu.renderD128.driver": "virtio-pci", "selinux": "enforcing"} {
		prof.Rilevato(k, v, "prova")
	}
	rap := &motore.Rapporto{Riconosciuta: motore.T("comp.nella_matrice", "Fedora 44"),
		Desktop: []motore.EsitoDesktop{{Desktop: "gnome", Installato: "50.5", Livello: motore.COMPATIBILE}}}
	dom := &motore.Domande{Porta: 7447, Firewall: "firewalld"}
	for _, l := range []string{"en"} {
		v := VistaDelControllo(&Controllo{Profilo: prof, Rapporto: rap, Domande: dom})
		if v.Esito != CONDIZIONI {
			t.Errorf("%s: outcome %v, expected conditional", l, v.Esito)
		}
		for _, r := range v.Righe {
			if strings.Contains(r.Testo, "virtio") || strings.Contains(r.Testo, "renderD") || strings.Contains(r.Testo, "RX-") {
				t.Errorf("%s: technical word outside the details: %q", l, r.Testo)
			}
		}
		if !strings.Contains(v.Dettagli, "virtio-pci") {
			t.Errorf("%s: the driver is not in the details: %q", l, v.Dettagli)
		}
		if v.Intestazione != "Fedora Linux 44 · Workstation · GNOME 50" {
			t.Errorf("%s: header %q", l, v.Intestazione)
		}
	}
	s := VistaDelleScelte(&Controllo{Profilo: prof, Rapporto: rap, Domande: dom})
	if s.Titolo != T("sc.titolo.1") || s.PortaVerde {
		t.Errorf("choices: %q, green port %v (with the firewall on, opening it is the administrator's job)", s.Titolo, s.PortaVerde)
	}
	// what is missing stops everything, and is stated without suggesting how to provide it (§10.36)
	rap.Mancano = []motore.Messaggio{motore.Msg("RX-MANCA-003", "XFCE: labwc")}
	v := VistaDelControllo(&Controllo{Profilo: prof, Rapporto: rap, Domande: dom})
	if v.Esito != BLOCCATA || v.Bloccata == nil || !strings.Contains(v.Bloccata.Perche, "labwc") {
		t.Errorf("missing: outcome %v, %+v", v.Esito, v.Bloccata)
	}
}
