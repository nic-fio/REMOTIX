package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"
)

// Ogni codice e ogni chiave ha il suo testo, in inglese (DECISIONI §10.35); ogni chiave usata esiste.
func TestTesti(t *testing.T) {
	italiano := regexp.MustCompile(`[àèéìòù]|\b(non|della|perché|questa)\b`)
	for c, v := range Codici {
		if v.Testo == "" {
			t.Errorf("%s senza testo", c)
		}
		if italiano.MatchString(v.Testo + " " + v.Rimedio) {
			t.Errorf("%s: italiano rimasto: %q", c, v.Testo+" "+v.Rimedio)
		}
	}
	for k, v := range testi {
		if v == "" {
			t.Errorf("%s: testo vuoto", k)
		}
		if italiano.MatchString(v) {
			t.Errorf("%s: italiano rimasto: %q", k, v)
		}
	}
	usate := regexp.MustCompile(`\bT\("([^"]+)"\s*[,)]`)
	voci, _ := filepath.Glob("*.go")
	voci2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(voci, voci2...) {
		b, _ := os.ReadFile(f)
		for _, m := range usate.FindAllStringSubmatch(string(b), -1) {
			if _, ok := testi[m[1]]; !ok {
				t.Errorf("%s usa la chiave %q, che non c'è", f, m[1])
			}
		}
	}
	for _, s := range TuttiGliStati() {
		if _, ok := testi["state."+string(s)]; !ok {
			t.Errorf("manca il nome dello stato %s", s)
		}
	}
}
