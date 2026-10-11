package motore

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

// rpmFinto: an rpm database answering «rpm -q --qf» the way rpm does — it expands %{NAME},
// %{VERSION}, %{RELEASE}, %{ARCH} and the conditional %|EPOCH?{%{EPOCH}:}|, which prints nothing
// for a package without an epoch. The other commands (rpm -qa, zypper verify) answer «all fine».
func rpmFake(db map[string][3]string) func(time.Duration, string, ...string) (string, int, error) {
	return func(_ time.Duration, nome string, arg ...string) (string, int, error) {
		if nome != "rpm" || len(arg) < 3 || arg[0] != "-q" || arg[1] != "--qf" {
			return "", 0, nil
		}
		var b strings.Builder
		for _, n := range arg[3:] {
			p, ok := db[n]
			if !ok {
				b.WriteString("package " + n + " is not installed\n")
				continue
			}
			epoca := ""
			if p[0] != "" {
				epoca = p[0] + ":"
			}
			r := strings.NewReplacer("%|EPOCH?{%{EPOCH}:}|", epoca, "%{EPOCH}", p[0], "%{NAME}", n,
				"%{VERSION}", p[1], "%{RELEASE}", p[2], "%{ARCH}", "x86_64", `\n`, "\n")
			b.WriteString(r.Replace(arg[2]))
		}
		return b.String(), 0, nil
	}
}

// The RPM epoch (Fedora, Alma, openSUSE): dnf and zypper resolve «1:1.7.0-9.fc44»; the check must
// read the installed one with its epoch, or every package that has one stays «missing» —
// `[M]` installa-91, fedora44: «packages: HALF_DONE 104 of 112», the 8 being libglvnd ×4,
// libogg, libtheora, libvisual, libvorbis.
func TestEpochRpm(t *testing.T) {
	db := map[string][3]string{
		"libglvnd":     {"1", "1.7.0", "9.fc44"},
		"libglvnd-egl": {"1", "1.7.0", "9.fc44"},
		"libogg":       {"2", "1.3.6", "2.fc44"},
		"libvorbis":    {"1", "1.3.7", "14.fc44"},
		"nettle":       {"", "3.10.1", "1.fc44"},
		"zlib-ng":      {"0", "2.2.4", "3.fc44"},
	}
	insieme := []Artefatto{
		{Nome: "libglvnd", Ver: "1:1.7.0-9.fc44", Esito: "new"},
		{Nome: "libglvnd-egl", Ver: "1:1.7.0-9.fc44", Esito: "new"},
		{Nome: "libogg", Ver: "2:1.3.6-2.fc44", Esito: "new"},
		{Nome: "libvorbis", Ver: "1:1.3.7-14.fc44", Esito: "new"},
		{Nome: "nettle", Ver: "3.10.1-1.fc44", Esito: "new"},
		{Nome: "zlib-ng", Ver: "2.2.4-3.fc44", Esito: "new"},
	}
	for _, fam := range []string{"fedora", "suse"} {
		a := &Ambiente{Radice: t.TempDir(), Famiglia: fam, Esegui: rpmFake(db)}
		a.Pacchetti = ScegliGestore(a, fam)

		v, err := a.Pacchetti.Vers([]string{"libglvnd", "nettle", "zlib-ng", "absent"})
		if err != nil {
			t.Fatal(err)
		}
		for n, atteso := range map[string]string{"libglvnd": "1:1.7.0-9.fc44", "nettle": "3.10.1-1.fc44", "zlib-ng": "0:2.2.4-3.fc44", "absent": ""} {
			if v[n] != atteso {
				t.Errorf("%s: %s installed as %q, want %q", fam, n, v[n], atteso)
			}
		}

		prima, _ := json.Marshal(beforePackages{Origine: DIRETTA, Gestore: a.Pacchetti.Nome(), ResolvedSet: insieme})
		c := &Contesto{Amb: a, Cartella: t.TempDir() + "/ops/op1"}
		es, det, err := (&pacchetti{}).Controlla(c, prima)
		if err != nil || es != COMPLETO {
			t.Errorf("%s: every package at the resolved version: %s %q %v, want COMPLETE", fam, es, det, err)
		}

		// a different epoch is a different version: an older epoch is not complete
		vecchio := map[string][3]string{}
		for k, x := range db {
			vecchio[k] = x
		}
		vecchio["libogg"] = [3]string{"1", "1.3.6", "2.fc44"}
		a.Esegui = rpmFake(vecchio)
		if es, det, _ := (&pacchetti{}).Controlla(c, prima); es != A_META || det != "5 of 6" {
			t.Errorf("%s: libogg at an older epoch: %s %q, want HALF_DONE 5 of 6", fam, es, det)
		}
	}
}

func TestSameVersion(t *testing.T) {
	for _, c := range []struct {
		a, b string
		ok   bool
	}{
		{"1:1.7.0-9.fc44", "1:1.7.0-9.fc44", true},
		{"0:2.2.4-3", "2.2.4-3", true},
		{"1.7.0-9.fc44", "1:1.7.0-9.fc44", false},
		{"2:1.3.6-2", "1:1.3.6-2", false},
	} {
		if versioneUguale(c.a, c.b) != c.ok {
			t.Errorf("versioneUguale(%q, %q) = %v", c.a, c.b, !c.ok)
		}
	}
}
