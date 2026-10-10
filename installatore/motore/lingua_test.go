package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"
)

// Every code and every key has its text, in English (DECISIONI §10.35); every key used exists.
func TestTesti(t *testing.T) {
	italiano := regexp.MustCompile(`[àèéìòù]|\b(non|della|perché|questa)\b`)
	for c, v := range Codici {
		if v.Testo == "" {
			t.Errorf("%s without text", c)
		}
		if italiano.MatchString(v.Testo + " " + v.Rimedio) {
			t.Errorf("%s: Italian left: %q", c, v.Testo+" "+v.Rimedio)
		}
	}
	for k, v := range testi {
		if v == "" {
			t.Errorf("%s: empty text", k)
		}
		if italiano.MatchString(v) {
			t.Errorf("%s: Italian left: %q", k, v)
		}
	}
	usate := regexp.MustCompile(`\bT\("([^"]+)"\s*[,)]`)
	voci, _ := filepath.Glob("*.go")
	voci2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(voci, voci2...) {
		b, _ := os.ReadFile(f)
		for _, m := range usate.FindAllStringSubmatch(string(b), -1) {
			if _, ok := testi[m[1]]; !ok {
				t.Errorf("%s uses the key %q, which does not exist", f, m[1])
			}
		}
	}
	for _, s := range TuttiGliStati() {
		if _, ok := testi["state."+string(s)]; !ok {
			t.Errorf("the name of state %s is missing", s)
		}
	}
}
