package motore

import (
	"os"
	"regexp"
	"strings"
	"testing"
)

// The single package's header (installatore/run.sh, DECISIONI §10.36): the line
// PAYLOAD_SHA256 is written by the release command (packaging/rilascio.sh) in the published copy; in the
// repository it is there, and EMPTY. The script does not touch the system by itself: it extracts into a temporary folder and
// hands over to the engine.
func TestScript(t *testing.T) {
	b, err := os.ReadFile("../run.sh")
	if err != nil {
		t.Fatal(err)
	}
	for _, v := range []string{"PAYLOAD_SHA256", "VERSIONE"} {
		if !regexp.MustCompile(`(?m)^` + v + `=''$`).Match(b) {
			t.Errorf("run.sh: the line %s='' is missing (the release command fills it)", v)
		}
	}
	// ⛔ the script copies no product files and adds no repositories: no install/cp towards the
	// system folders
	if regexp.MustCompile(`(?m)^[^#]*\b(install|cp|mv)\b[^\n]*(/usr/|/etc/|/var/lib/)`).Match(b) {
		t.Error("run.sh copies a file into the system")
	}
	if !strings.HasSuffix(string(b), "\n__PAYLOAD__\n") {
		t.Error("run.sh: the last line must be __PAYLOAD__ (the tar.gz is below it)")
	}
	if !strings.Contains(string(b), `--bundle "$dir/packages"`) {
		t.Error("run.sh: the engine must receive the packages folder (--bundle)")
	}
}
