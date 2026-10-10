package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"
)

// Every code and every key has its text, in English (DECISIONI §10.35); every key used exists.
func TestTexts(t *testing.T) {
	italian := regexp.MustCompile(`[àèéìòù]|\b(non|della|perché|questa)\b`)
	for c, v := range Codes {
		if v.Text == "" {
			t.Errorf("%s without text", c)
		}
		if italian.MatchString(v.Text + " " + v.Remediation) {
			t.Errorf("%s: Italian left: %q", c, v.Text+" "+v.Remediation)
		}
	}
	for k, v := range texts {
		if v == "" {
			t.Errorf("%s: empty text", k)
		}
		if italian.MatchString(v) {
			t.Errorf("%s: Italian left: %q", k, v)
		}
	}
	used_count := regexp.MustCompile(`\bT\("([^"]+)"\s*[,)]`)
	entries, _ := filepath.Glob("*.go")
	entries2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(entries, entries2...) {
		b, _ := os.ReadFile(f)
		for _, m := range used_count.FindAllStringSubmatch(string(b), -1) {
			if _, ok := texts[m[1]]; !ok {
				t.Errorf("%s uses the key %q, which does not exist", f, m[1])
			}
		}
	}
	for _, s := range AllStates() {
		if _, ok := texts["state."+string(s)]; !ok {
			t.Errorf("the name of state %s is missing", s)
		}
	}
}
