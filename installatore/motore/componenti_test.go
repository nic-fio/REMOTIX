package motore

import (
	"strings"
	"testing"
)

// Se il motore installa il desktop, i pezzi che quel desktop chiede a REMOTIX entrano nel piano.
func TestComponentiDelDesktopInstallato(t *testing.T) {
	cat := catalogoProva(t)
	p := profiloDi("opensuse-leap", "16.0", map[string]string{"desktop.gnome": "assente"})
	rap := Valuta(cat, p)
	s := SceltaDesktop(rap)
	if s == nil {
		t.Fatal("nessuna scelta")
	}
	if got := s.Componenti["lxqt"]; got != "labwc,wlr-randr,google-droid-fonts" {
		t.Fatalf("componenti lxqt: %q", got)
	}
	if got := s.Componenti["kde"]; got != "" {
		t.Fatalf("componenti kde su Leap: %q", got)
	}
	pn := &Piano{Scelte: []Scelta{*s}}
	if err := pn.Rispondi("desktop", "lxqt"); err != nil {
		t.Fatal(err)
	}
	var ids []string
	for _, a := range pn.Azioni {
		ids = append(ids, a.ID+"="+a.Parametri["nomi"])
	}
	if got := strings.Join(ids, " "); got != "desktop=pattern:lxqt componenti-desktop=labwc,wlr-randr,google-droid-fonts" {
		t.Fatalf("passi: %s", got)
	}
	pn.Rispondi("desktop", "kde")
	if len(pn.Azioni) != 1 {
		t.Fatalf("cambiando risposta i componenti di prima restano: %+v", pn.Azioni)
	}
}
