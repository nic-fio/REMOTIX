package motore

import (
	"os"
	"regexp"
	"testing"
)

// Lo script d'ingresso verifica il motore con lo sha256 (DECISIONI §10.21): la riga SHA256_MOTORE la
// scrive il comando di rilascio (packaging/rilascio.sh) nella copia pubblicata; nel deposito c'è,
// ed è VUOTA (una copia di sviluppo prende lo sha256 pubblicato accanto al motore).
func TestScript(t *testing.T) {
	b, err := os.ReadFile("../install.sh")
	if err != nil {
		t.Fatal(err)
	}
	for _, v := range []string{"SHA256_MOTORE"} {
		if !regexp.MustCompile(`(?m)^` + v + `=''$`).Match(b) {
			t.Errorf("install.sh: manca la riga %s='' (la riempie il comando di rilascio)", v)
		}
	}
	// ⛔ lo script non copia file del prodotto: niente install/cp verso le cartelle di REMOTIX
	if regexp.MustCompile(`(?m)^[^#]*\b(install|cp|mv)\b[^\n]*(/usr/(lib|libexec|bin|share)|/etc/remotix|/var/lib/remotix)`).Match(b) {
		t.Error("install.sh copia un file del prodotto")
	}
	if !regexp.MustCompile(`(?m)^main "\$@"\n?$`).Match(b[len(b)-20:]) {
		t.Error("install.sh: l'ultima riga deve essere main \"$@\"")
	}
}
