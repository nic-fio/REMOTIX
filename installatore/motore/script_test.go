package motore

import (
	"os"
	"regexp"
	"strings"
	"testing"

	"remotix/installatore/chiavi"
)

// Lo script d'ingresso verifica il motore con la chiave madre della catena A scritta DENTRO di sé:
// deve essere la stessa del motore (installatore/chiavi/radice-A.pub), o install.sh rifiuterebbe
// ogni motore vero — o, peggio, ne accetterebbe uno firmato da un'altra radice.
func TestScriptRadice(t *testing.T) {
	b, err := os.ReadFile("../install.sh")
	if err != nil {
		t.Fatal(err)
	}
	m := regexp.MustCompile(`(?m)^RADICE_A='([^']+)'$`).FindStringSubmatch(string(b))
	if m == nil {
		t.Fatal("install.sh: RADICE_A non trovata")
	}
	radici, err := LeggiRadici(chiavi.RadiceA)
	if err != nil {
		t.Fatal(err)
	}
	var righe []string
	for _, r := range strings.Split(chiavi.RadiceA, "\n") {
		if r = strings.TrimSpace(r); r != "" && !strings.HasPrefix(r, "#") {
			righe = append(righe, r)
		}
	}
	if len(radici) != 1 || righe[0] != m[1] {
		t.Errorf("install.sh ha la radice %s, il motore %v", m[1], righe)
	}
	// ⛔ lo script non copia file del prodotto: niente install/cp verso le cartelle di REMOTIX
	if regexp.MustCompile(`(?m)^[^#]*\b(install|cp|mv)\b[^\n]*(/usr/(lib|libexec|bin|share)|/etc/remotix|/var/lib/remotix)`).Match(b) {
		t.Error("install.sh copia un file del prodotto")
	}
	if !regexp.MustCompile(`(?m)^main "\$@"\n?$`).Match(b[len(b)-20:]) {
		t.Error("install.sh: l'ultima riga deve essere main \"$@\"")
	}
}
