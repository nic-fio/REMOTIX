package motore

import (
	"os"
	"regexp"
	"strings"
	"testing"
)

// L'intestazione del pacchetto unico (installatore/run.sh, DECISIONI §10.36): la riga
// PAYLOAD_SHA256 la scrive il comando di rilascio (packaging/rilascio.sh) nella copia pubblicata; nel
// deposito c'è, ed è VUOTA. Lo script non tocca il sistema da sé: estrae in una cartella temporanea e
// passa la mano al motore.
func TestScript(t *testing.T) {
	b, err := os.ReadFile("../run.sh")
	if err != nil {
		t.Fatal(err)
	}
	for _, v := range []string{"PAYLOAD_SHA256", "VERSIONE"} {
		if !regexp.MustCompile(`(?m)^` + v + `=''$`).Match(b) {
			t.Errorf("run.sh: manca la riga %s='' (la riempie il comando di rilascio)", v)
		}
	}
	// ⛔ lo script non copia file del prodotto né aggiunge archivi: niente install/cp verso le
	// cartelle del sistema
	if regexp.MustCompile(`(?m)^[^#]*\b(install|cp|mv)\b[^\n]*(/usr/|/etc/|/var/lib/)`).Match(b) {
		t.Error("run.sh copia un file nel sistema")
	}
	if !strings.HasSuffix(string(b), "\n__PAYLOAD__\n") {
		t.Error("run.sh: l'ultima riga deve essere __PAYLOAD__ (sotto c'è il tar.gz)")
	}
	if !strings.Contains(string(b), `--bundle "$dir/packages"`) {
		t.Error("run.sh: il motore deve ricevere la cartella dei pacchetti (--bundle)")
	}
}
